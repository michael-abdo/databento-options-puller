"""
Option Generator module for creating output based on extracted facts.
This module attempts to recreate the structure and patterns found in example_output.csv
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import yaml
import json

# Add parent directory to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.date_utils import parse_date, format_date, generate_trading_days
from utils.symbol_utils import build_option_symbol, parse_option_symbol
from utils.logging_config import get_logger
from src.databento_client import DatabentoBridge
from src.delta_calculator import DeltaCalculator
from src.futures_manager import FuturesManager
from src.options_manager import OptionsManager

logger = get_logger('generator')


class OptionGenerator:
    """Generate options data based on hypothesis and extracted facts."""
    
    def __init__(self, facts: Dict, config: Dict = None, use_real_data: bool = False):
        """
        Initialize generator with facts from analyzer and configuration.
        
        Args:
            facts: Facts extracted by ExampleAnalyzer
            config: Configuration dictionary
            use_real_data: Whether to use real Databento data instead of stubs
        """
        self.facts = facts
        self.config = config or self._load_default_config()
        self.use_real_data = use_real_data
        
        # Extract key parameters
        self.params = {
            'delta_target': self.config['option_selection']['delta_target'],
            'delta_tolerance': self.config['option_selection']['delta_tolerance'],
            'months_ahead': self.config['option_selection']['months_ahead'],
            'volatility': self.config['market']['volatility'],
            'risk_free_rate': self.config['market']['risk_free_rate'],
            'use_stub': self.config['stub_data']['use_stub'] and not use_real_data
        }
        
        # Initialize real data components if needed
        if self.use_real_data:
            self.databento_client = DatabentoBridge()
            self.delta_calculator = DeltaCalculator(self.params['risk_free_rate'])
            self.futures_manager = FuturesManager()
            self.options_manager = OptionsManager(
                self.databento_client, self.delta_calculator, self.futures_manager
            )
            logger.info("Initialized with real data components")
        else:
            self.databento_client = None
            self.delta_calculator = None
            self.futures_manager = None
            self.options_manager = None
            logger.info("Initialized with stub data mode")
        
        logger.info(f"Initialized OptionGenerator with params: {self.params}")
        
    def _load_default_config(self) -> Dict:
        """Load default configuration from YAML."""
        config_path = Path(__file__).parent.parent / 'config' / 'default_params.yaml'
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def generate(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Generate options data attempting to match example structure.
        
        Args:
            start_date: Start date (uses example start if None)
            end_date: End date (uses example end if None)
            
        Returns:
            DataFrame with generated data
        """
        logger.info("="*60)
        logger.info("Generating options data")
        logger.info("="*60)
        
        # Use dates from example if not provided
        if start_date is None:
            start_date = self.facts['basic_info']['date_range']['start']
        if end_date is None:
            end_date = self.facts['basic_info']['date_range']['end']
            
        logger.info(f"Date range: {start_date} to {end_date}")
        logger.info(f"Using {'real data' if self.use_real_data else 'stub data'}")
        
        if self.use_real_data:
            return self._generate_with_real_data(start_date, end_date)
        else:
            return self._generate_with_stub_data(start_date, end_date)
    
    def _generate_with_real_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Generate data using real Databento API and delta calculations."""
        logger.info("Generating with real Databento data")
        
        # Create base dataframe with dates
        df = self._create_date_dataframe(start_date, end_date)
        
        # Get monthly option selections using real strategy
        selected_options = self.options_manager.identify_monthly_options(start_date, end_date)
        
        if not selected_options:
            logger.warning("No options selected by real strategy")
            return df
        
        logger.info(f"Real strategy selected {len(selected_options)} options")
        
        # Add each selected option's price data
        for option_info in selected_options:
            symbol = option_info['symbol']
            logger.info(f"Adding real data for {symbol}")
            
            # Get price history from Databento
            price_data = self.options_manager.get_option_price_history(
                symbol, 
                option_info['start_trading'],
                option_info['end_trading']
            )
            
            # Add to main dataframe
            df = self._merge_option_prices(df, symbol, price_data, option_info)
        
        return df
    
    def _generate_with_stub_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Generate data using stub/mock data (original implementation)."""
        logger.info("Generating with stub data")
        
        # Create base dataframe with dates
        df = self._create_date_dataframe(start_date, end_date)
        
        # Add futures prices only if requested
        include_futures = self.params.get('include_futures_price', True)
        if self.params['use_stub'] and include_futures:
            df = self._add_stub_futures_prices(df)
        
        # Add each option based on facts
        for symbol_info in self.facts['option_symbols']:
            symbol = symbol_info['full_symbol']
            df = self._add_option_data(df, symbol)
        
        logger.info(f"Generated dataframe with {len(df)} rows, {len(df.columns)} columns")
        
        return df
    
    def _merge_option_prices(self, df: pd.DataFrame, symbol: str, 
                           price_data: pd.DataFrame, option_info: Dict) -> pd.DataFrame:
        """
        Merge option price data into main dataframe.
        
        Args:
            df: Main dataframe with dates
            symbol: Option symbol
            price_data: Price data from Databento
            option_info: Option metadata
            
        Returns:
            Updated dataframe
        """
        if price_data.empty:
            logger.warning(f"No price data for {symbol}")
            # Add empty column
            df[symbol] = np.nan
            return df
        
        logger.debug(f"Merging {len(price_data)} price records for {symbol}")
        
        # Ensure symbol column exists
        if symbol not in df.columns:
            df[symbol] = np.nan
        
        # Match dates and fill prices
        for _, price_row in price_data.iterrows():
            price_date = price_row['date']
            close_price = price_row['close']
            
            # Format date to match main dataframe
            if 'timestamp' in df.columns:
                # Convert price_date to same format as main df
                date_format = self.params.get('date_format', '%m/%d/%y')
                if date_format == "%-m/%-d/%y":
                    # No zero padding
                    formatted_date = f"{price_date.month}/{price_date.day}/{str(price_date.year)[-2:]}"
                else:
                    formatted_date = price_date.strftime(date_format)
                
                # Find matching row
                matching_rows = df[df['timestamp'] == formatted_date]
                
                if not matching_rows.empty:
                    df.loc[matching_rows.index, symbol] = close_price
                    logger.debug(f"Set {symbol} price on {formatted_date}: ${close_price:.2f}")
        
        # Log how many prices were set
        non_null_count = df[symbol].notna().sum()
        logger.info(f"Set {non_null_count} prices for {symbol}")
        
        return df
    
    def _create_date_dataframe(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Create base dataframe with trading dates."""
        # Parse dates
        start = parse_date(start_date)
        end = parse_date(end_date)
        
        # Check if we need exact row count
        exact_count = self.params.get('exact_row_count')
        
        if exact_count:
            # Create exact number of dates (including weekends if needed)
            date_range = pd.date_range(start=start, periods=exact_count, freq='D')
            trading_days = [d.to_pydatetime() for d in date_range]
            logger.info(f"Created exact {exact_count} days including weekends")
        else:
            # Generate trading days
            trading_days = generate_trading_days(start, end)
            logger.info(f"Created {len(trading_days)} trading days")
        
        # Format dates with specified format
        date_format = self.params.get('date_format', '%m/%d/%y')
        
        # Handle zero-padding format
        if date_format == "%-m/%-d/%y":
            # No zero padding format (Unix style)
            formatted_dates = []
            for d in trading_days:
                formatted = f"{d.month}/{d.day}/{d.year % 100:02d}"
                formatted_dates.append(formatted)
        else:
            formatted_dates = [d.strftime(date_format) for d in trading_days]
        
        # Create dataframe
        df = pd.DataFrame({
            'timestamp': formatted_dates
        })
        
        logger.info(f"Created date dataframe with {len(df)} rows")
        
        return df
    
    def _add_stub_futures_prices(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add stub futures prices using random walk."""
        base_price = self.config['stub_data']['base_futures_price']
        volatility = self.config['stub_data']['price_volatility']
        
        # Generate random walk
        returns = np.random.normal(0, volatility, len(df))
        prices = base_price * np.exp(np.cumsum(returns))
        
        df['Futures_Price'] = prices
        
        logger.debug(f"Added futures prices: first={prices[0]:.3f}, last={prices[-1]:.3f}")
        
        return df
    
    def _add_option_data(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Add data for a specific option based on facts."""
        # Get active period from facts
        if symbol not in self.facts['active_periods']:
            logger.warning(f"No active period found for {symbol}")
            return df
        
        period_info = self.facts['active_periods'][symbol]
        price_info = self.facts['price_patterns'].get(symbol, {})
        
        # Create price series
        prices = self._generate_option_prices(
            symbol, 
            period_info, 
            price_info,
            len(df)
        )
        
        # Add to dataframe
        df[symbol] = prices
        
        # Log what we did
        non_null = df[symbol].notna().sum()
        if non_null > 0:
            first_price = df[symbol].dropna().iloc[0]
            last_price = df[symbol].dropna().iloc[-1]
            logger.info(f"Added {symbol}: {non_null} prices, "
                       f"first={first_price:.2f}, last={last_price:.2f}")
        
        return df
    
    def _generate_option_prices(self, symbol: str, period_info: Dict, 
                               price_info: Dict, total_days: int) -> pd.Series:
        """Generate price series for an option."""
        # Create array of NaN
        prices = pd.Series([np.nan] * total_days)
        
        # Get date indices
        first_date = period_info['first_date']
        last_date = period_info['last_date']
        
        # Find indices in our dataframe
        # Note: This is a simplified approach - in reality we'd match dates properly
        first_idx = self._find_date_index(first_date, total_days)
        last_idx = self._find_date_index(last_date, total_days)
        
        # Ensure indices are valid
        if first_idx is None or last_idx is None:
            logger.warning(f"Invalid indices for {symbol}: {first_idx} to {last_idx}")
            # Use fallback based on symbol
            if 'F2' in symbol:  # January
                first_idx, last_idx = 0, 20
            elif 'G2' in symbol:  # February
                first_idx, last_idx = 2, 45
            elif 'H2' in symbol:  # March
                first_idx, last_idx = 25, 68
            elif 'J2' in symbol:  # April
                first_idx, last_idx = 50, 80
            elif 'K2' in symbol:  # May
                first_idx, last_idx = 75, 80
            else:
                first_idx, last_idx = 0, 10
        
        # Ensure valid range
        first_idx = max(0, min(first_idx, total_days - 1))
        last_idx = max(first_idx, min(last_idx, total_days - 1))
        
        # Generate prices
        num_prices = last_idx - first_idx + 1
        
        if self.config['stub_data']['use_stub'] and price_info:
            # Use price patterns from facts
            start_price = price_info.get('first_price', 1.0)
            end_price = price_info.get('last_price', 1.0)
            
            if price_info.get('price_direction') == 'up':
                # Generate increasing prices with noise
                base = np.linspace(start_price, end_price, num_prices)
                noise = np.random.normal(0, 0.1 * np.mean([start_price, end_price]), num_prices)
                generated_prices = np.maximum(0.01, base + noise)
            else:
                # Generate decreasing prices with noise
                base = np.linspace(start_price, end_price, num_prices)
                noise = np.random.normal(0, 0.1 * np.mean([start_price, end_price]), num_prices)
                generated_prices = np.maximum(0.01, base + noise)
        else:
            # Simple random prices
            generated_prices = np.random.uniform(0.01, 10.0, num_prices)
        
        # Assign to series
        prices.iloc[first_idx:last_idx+1] = generated_prices
        
        return prices
    
    def _find_date_index(self, date_str: str, total_days: int) -> Optional[int]:
        """Find index for a date string (simplified for stub)."""
        # In the stub version, we'll use approximate indices
        # In real version, this would match against actual dates
        
        # Parse date
        try:
            date = parse_date(date_str)
        except:
            logger.warning(f"Could not parse date: {date_str}")
            return None
        
        # Rough approximation based on month/day
        if date.month == 12:  # December 2021
            return int((date.day - 1) * 0.5)  # Rough estimate
        elif date.month == 1:  # January 2022
            return int(20 + (date.day - 1) * 0.7)
        elif date.month == 2:  # February 2022
            return int(45 + (date.day - 1) * 0.7)
        elif date.month == 3:  # March 2022
            return int(70 + (date.day - 1) * 0.7)
        else:
            return None
    
    def update_params(self, new_params: Dict):
        """Update generator parameters."""
        self.params.update(new_params)
        logger.info(f"Updated params: {self.params}")
    
    def get_params(self) -> Dict:
        """Get current parameters."""
        return self.params.copy()


def main():
    """Test the generator independently."""
    from utils.logging_config import setup_logging
    
    # Set up logging
    setup_logging()
    
    # Load facts from analyzer output
    facts_path = Path('output/extracted_facts.json')
    if facts_path.exists():
        with open(facts_path, 'r') as f:
            facts = json.load(f)
    else:
        logger.error(f"Facts file not found: {facts_path}")
        logger.info("Run example_analyzer.py first")
        return
    
    # Create generator
    generator = OptionGenerator(facts)
    
    # Generate data
    df = generator.generate()
    
    # Save output
    output_path = Path('output/generated_stub.csv')
    output_path.parent.mkdir(exist_ok=True)
    df.to_csv(output_path, index=False)
    
    print(f"\nGeneration complete! Output saved to {output_path}")
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    # Show sample
    print("\nFirst few rows:")
    print(df.head())


if __name__ == "__main__":
    main()