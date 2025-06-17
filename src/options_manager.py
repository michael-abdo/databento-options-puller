"""
Options Manager for NY Harbor ULSD (OH) call options.
Handles option chain management, strike selection, and contract lifecycle.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import logging
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.date_utils import parse_date, is_trading_day, get_first_trading_day
from utils.symbol_utils import parse_option_symbol, build_option_symbol, extract_strike
from utils.logging_config import get_logger
from src.databento_client import DatabentoBridge
from src.delta_calculator import DeltaCalculator
from src.futures_manager import FuturesManager

logger = get_logger('options')


class OptionsManager:
    """
    Manager for NY Harbor ULSD (OH) call options.
    
    Handles:
    - Options chain retrieval and filtering
    - 15-delta strike selection using rolling M+2 strategy
    - Option contract lifecycle tracking
    - Integration with Databento API and delta calculator
    """
    
    def __init__(self, databento_client: Optional[DatabentoBridge] = None,
                 delta_calculator: Optional[DeltaCalculator] = None,
                 futures_manager: Optional[FuturesManager] = None):
        """
        Initialize options manager.
        
        Args:
            databento_client: Databento API client
            delta_calculator: Delta calculation engine
            futures_manager: Futures contract manager
        """
        self.client = databento_client or DatabentoBridge()
        self.delta_calc = delta_calculator or DeltaCalculator()
        self.futures_mgr = futures_manager or FuturesManager()
        
        # Strategy parameters
        self.target_delta = 0.15
        self.delta_tolerance = 0.02
        self.underlying_root = "HO"  # CME/NYMEX symbol for ULSD heating oil futures
        self.option_type = "call"
        
        # Caches for performance
        self.options_cache = {}
        self.spot_price_cache = {}
        
        logger.info(f"Initialized OptionsManager (target_delta={self.target_delta:.2f})")
    
    def identify_monthly_options(self, start_date: Union[str, datetime], 
                                end_date: Union[str, datetime]) -> List[Dict]:
        """
        Identify 15-delta call options using rolling M+2 strategy.
        
        On first trading day of month M, select 15-delta call for month M+2.
        
        Args:
            start_date: Start of analysis period
            end_date: End of analysis period
            
        Returns:
            List of selected option contracts with metadata
        """
        if isinstance(start_date, str):
            start_date = parse_date(start_date)
        if isinstance(end_date, str):
            end_date = parse_date(end_date)
        
        logger.info(f"Identifying monthly options from {start_date.strftime('%Y-%m-%d')} "
                   f"to {end_date.strftime('%Y-%m-%d')}")
        
        selected_options = []
        
        # Get roll schedule for the period
        roll_schedule = self.futures_mgr.get_roll_schedule(start_date, end_date)
        
        for roll_event in roll_schedule:
            roll_date = roll_event['roll_date']
            
            # Skip if roll date is before our start
            if roll_date < start_date:
                continue
            
            logger.info(f"Processing roll date: {roll_date.strftime('%Y-%m-%d')}")
            
            try:
                # Get M+2 target contract
                target_contract = self.futures_mgr.get_m_plus_n_contract(roll_date, 2)
                logger.debug(f"M+2 target contract: {target_contract}")
                
                # Get spot price for delta calculation
                spot_price = self._get_spot_price(roll_date)
                logger.debug(f"Spot price on {roll_date.strftime('%Y-%m-%d')}: ${spot_price:.2f}")
                
                # Find 15-delta option
                selected_option = self._find_target_delta_option(
                    target_contract, roll_date, spot_price
                )
                
                if selected_option:
                    # Calculate active period
                    start_trading = roll_date
                    end_trading = self._get_option_last_trading_day(
                        selected_option['symbol'], target_contract
                    )
                    
                    option_info = {
                        'symbol': selected_option['symbol'],
                        'underlying_contract': target_contract,
                        'strike': selected_option['strike'],
                        'selection_date': roll_date,
                        'start_trading': start_trading,
                        'end_trading': end_trading,
                        'target_delta': self.target_delta,
                        'actual_delta': selected_option['delta'],
                        'spot_price_at_selection': spot_price,
                        'roll_month': roll_date.month,
                        'roll_year': roll_date.year
                    }
                    
                    selected_options.append(option_info)
                    
                    logger.info(f"Selected option: {selected_option['symbol']} "
                               f"(Δ={selected_option['delta']:.4f}, K=${selected_option['strike']:.2f})")
                else:
                    logger.warning(f"No suitable option found for {roll_date.strftime('%Y-%m-%d')}")
            
            except Exception as e:
                logger.error(f"Error processing roll date {roll_date.strftime('%Y-%m-%d')}: {e}")
                continue
        
        logger.info(f"Identified {len(selected_options)} options for the period")
        return selected_options
    
    def _find_target_delta_option(self, target_contract: str, trade_date: datetime, 
                                 spot_price: float) -> Optional[Dict]:
        """
        Find the call option closest to target delta.
        
        Args:
            target_contract: Underlying futures contract
            trade_date: Date for option selection
            spot_price: Current underlying price
            
        Returns:
            Selected option details or None
        """
        # Get options chain
        expiry_month = self._contract_to_expiry_month(target_contract)
        options_chain = self._get_options_chain(target_contract, expiry_month, trade_date)
        
        if not options_chain:
            logger.warning(f"No options chain found for {target_contract}")
            return None
        
        # Filter for call options only
        call_options = [opt for opt in options_chain if opt.get('option_type', 'C') == 'C']
        
        if not call_options:
            logger.warning(f"No call options found in chain for {target_contract}")
            return None
        
        # Extract strikes
        strikes = [opt['strike'] for opt in call_options]
        
        # Calculate expiry date
        expiry_date = self.futures_mgr.get_expiry_date(target_contract)
        time_to_expiry = self.delta_calc.calculate_time_to_expiry(trade_date, expiry_date)
        
        # Estimate volatility (in production, use market data)
        volatility = self._estimate_volatility(spot_price, trade_date)
        
        # Find target delta strike
        best_strike, actual_delta = self.delta_calc.find_target_delta_strike(
            spot_price, strikes, time_to_expiry, volatility, self.target_delta, 'call'
        )
        
        # Find the option with this strike
        selected_option = None
        for opt in call_options:
            if abs(opt['strike'] - best_strike) < 0.01:  # Match within $0.01
                selected_option = opt
                break
        
        if selected_option:
            # Build full symbol
            symbol = self._build_option_symbol(target_contract, best_strike, 'C')
            
            return {
                'symbol': symbol,
                'strike': best_strike,
                'delta': actual_delta,
                'underlying': target_contract,
                'option_type': 'C',
                'expiry_date': expiry_date,
                'time_to_expiry': time_to_expiry,
                'volatility': volatility
            }
        
        return None
    
    def _get_options_chain(self, underlying_contract: str, expiry_month: str, 
                          trade_date: datetime) -> List[Dict]:
        """
        Get options chain for a contract and expiry month.
        
        Args:
            underlying_contract: Futures contract symbol
            expiry_month: Expiry month string (e.g., '2022-01')
            trade_date: Date to get chain for
            
        Returns:
            List of option contracts
        """
        cache_key = f"{underlying_contract}_{expiry_month}_{trade_date.strftime('%Y-%m-%d')}"
        
        if cache_key in self.options_cache:
            logger.debug(f"Using cached options chain for {cache_key}")
            return self.options_cache[cache_key]
        
        try:
            # Use underlying root for chain fetch
            chain = self.client.fetch_options_chain(
                self.underlying_root, expiry_month, trade_date
            )
            
            self.options_cache[cache_key] = chain
            logger.debug(f"Fetched options chain: {len(chain)} contracts")
            
            return chain
            
        except Exception as e:
            logger.error(f"Failed to fetch options chain: {e}")
            return []
    
    def _get_spot_price(self, date: datetime) -> float:
        """
        Get spot price (futures price) for underlying.
        
        Args:
            date: Date to get price for
            
        Returns:
            Spot price
        """
        date_str = date.strftime('%Y-%m-%d')
        
        if date_str in self.spot_price_cache:
            return self.spot_price_cache[date_str]
        
        try:
            spot_price = self.client.get_spot_price(self.underlying_root, date)
            self.spot_price_cache[date_str] = spot_price
            return spot_price
            
        except Exception as e:
            logger.error(f"Failed to get spot price for {date_str}: {e}")
            return 2.5  # Fallback price
    
    def _estimate_volatility(self, spot_price: float, date: datetime, 
                           window_days: int = 30) -> float:
        """
        Estimate volatility from historical data.
        
        Args:
            spot_price: Current price
            date: Current date
            window_days: Lookback window
            
        Returns:
            Estimated volatility
        """
        try:
            # Get historical data
            start_date = date - timedelta(days=window_days + 10)  # Extra buffer
            end_date = date
            
            price_history = self.client.fetch_futures_continuous(
                self.underlying_root, start_date, end_date
            )
            
            if len(price_history) > 5:
                volatility = self.delta_calc.estimate_volatility_from_history(
                    price_history, window_days
                )
                logger.debug(f"Estimated volatility: {volatility:.2%}")
                return volatility
            else:
                logger.warning("Insufficient price history for volatility estimation")
                return 0.30  # Default 30%
                
        except Exception as e:
            logger.warning(f"Volatility estimation failed: {e}, using default")
            return 0.30
    
    def _contract_to_expiry_month(self, contract_symbol: str) -> str:
        """
        Convert futures contract symbol to expiry month string.
        
        Args:
            contract_symbol: Contract symbol (e.g., 'OHF2')
            
        Returns:
            Expiry month string (e.g., '2022-01')
        """
        # Parse contract to get month and year
        parts = self.futures_mgr.root_symbol
        if not contract_symbol.startswith(parts):
            raise ValueError(f"Invalid contract symbol: {contract_symbol}")
        
        month_year = contract_symbol[len(parts):]
        if len(month_year) != 2:
            raise ValueError(f"Invalid contract format: {contract_symbol}")
        
        month_code = month_year[0]
        year_code = month_year[1]
        
        # Find month number
        month_num = None
        for num, code in self.futures_mgr.contract_months.items():
            if code == month_code:
                month_num = num
                break
        
        if month_num is None:
            raise ValueError(f"Invalid month code: {month_code}")
        
        # Convert year code
        year = 2020 + int(year_code)  # Assuming 2020s
        
        return f"{year}-{month_num:02d}"
    
    def _build_option_symbol(self, underlying_contract: str, strike: float, 
                           option_type: str) -> str:
        """
        Build option symbol from components.
        
        Args:
            underlying_contract: Underlying futures contract
            strike: Strike price
            option_type: 'C' or 'P'
            
        Returns:
            Full option symbol (e.g., 'OHF2 C27800')
        """
        # Convert strike to integer representation (cents)
        strike_int = int(round(strike * 100))
        
        # Format: "OHF2 C27800"
        symbol = f"{underlying_contract} {option_type}{strike_int:05d}"
        
        return symbol
    
    def _get_option_last_trading_day(self, option_symbol: str, 
                                   underlying_contract: str) -> datetime:
        """
        Get last trading day for an option.
        
        Args:
            option_symbol: Option symbol
            underlying_contract: Underlying contract
            
        Returns:
            Last trading day
        """
        # For OH options, typically expire with the underlying futures
        try:
            expiry_date = self.futures_mgr.get_expiry_date(underlying_contract)
            return expiry_date
        except Exception as e:
            logger.error(f"Cannot determine expiry for {option_symbol}: {e}")
            # Fallback: assume end of month
            parsed = parse_option_symbol(option_symbol)
            if parsed:
                year = 2020 + int(parsed['year_code'])
                month_code = parsed['month_code']
                
                # Find month
                for num, code in self.futures_mgr.contract_months.items():
                    if code == month_code:
                        return datetime(year, num, 28)  # Conservative estimate
            
            return datetime.now() + timedelta(days=30)  # Very conservative fallback
    
    def get_option_price_history(self, option_symbol: str, start_date: datetime,
                               end_date: datetime) -> pd.DataFrame:
        """
        Get historical price data for an option.
        
        Args:
            option_symbol: Option symbol
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with price history
        """
        try:
            price_data = self.client.fetch_option_history(
                option_symbol, start_date, end_date
            )
            
            logger.debug(f"Retrieved {len(price_data)} days of price data for {option_symbol}")
            return price_data
            
        except Exception as e:
            logger.error(f"Failed to get price history for {option_symbol}: {e}")
            return pd.DataFrame()
    
    def validate_option_selection(self, option_info: Dict) -> bool:
        """
        Validate that an option selection meets criteria.
        
        Args:
            option_info: Option selection details
            
        Returns:
            True if valid
        """
        actual_delta = option_info.get('actual_delta', 0)
        target_delta = option_info.get('target_delta', self.target_delta)
        
        # Check delta tolerance
        delta_diff = abs(actual_delta - target_delta)
        if delta_diff > self.delta_tolerance:
            logger.warning(f"Delta {actual_delta:.4f} outside tolerance "
                          f"(target: {target_delta:.2f} ± {self.delta_tolerance:.2f})")
            return False
        
        # Check symbol format
        symbol = option_info.get('symbol', '')
        if not symbol or not parse_option_symbol(symbol):
            logger.warning(f"Invalid option symbol: {symbol}")
            return False
        
        # Check dates
        start_date = option_info.get('start_trading')
        end_date = option_info.get('end_trading')
        if not start_date or not end_date or start_date >= end_date:
            logger.warning("Invalid trading date range")
            return False
        
        return True


def main():
    """Test the options manager."""
    from utils.logging_config import setup_logging
    
    # Set up logging
    setup_logging()
    
    # Create manager
    manager = OptionsManager()
    
    # Test monthly option identification
    print("Testing monthly option identification:")
    start_date = "2021-12-01"
    end_date = "2022-03-31"
    
    options = manager.identify_monthly_options(start_date, end_date)
    
    print(f"\nFound {len(options)} options:")
    for opt in options:
        print(f"  {opt['selection_date'].strftime('%Y-%m-%d')}: {opt['symbol']} "
              f"(Δ={opt['actual_delta']:.4f}, K=${opt['strike']:.2f})")
        print(f"    Active: {opt['start_trading'].strftime('%Y-%m-%d')} to "
              f"{opt['end_trading'].strftime('%Y-%m-%d')}")
    
    # Test validation
    print("\nTesting option validation:")
    for opt in options:
        is_valid = manager.validate_option_selection(opt)
        print(f"  {opt['symbol']}: {'✓' if is_valid else '✗'}")


if __name__ == "__main__":
    main()