"""
Databento API Client for fetching NY Harbor ULSD futures and options data.
Handles authentication, rate limiting, and data retrieval.
"""

import os
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import logging
from pathlib import Path
import requests
import json

try:
    import databento as db
    DATABENTO_AVAILABLE = True
except ImportError:
    DATABENTO_AVAILABLE = False
    db = None

# Add parent directory to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.date_utils import parse_date, format_date, is_trading_day
from utils.symbol_utils import parse_option_symbol, build_option_symbol
from utils.logging_config import get_logger

logger = get_logger('databento')

# For now, we'll create a mock client that behaves like Databento
# In production, you'd replace this with the real databento library

class DatabentoBridge:
    """
    Databento API client for options and futures data.
    
    Note: This is currently a mock implementation that simulates
    the Databento API behavior. Replace with real databento client.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Databento client.
        
        Args:
            api_key: Databento API key (from env if None)
        """
        self.api_key = api_key or os.getenv('DATABENTO_API_KEY')
        
        if not self.api_key or not DATABENTO_AVAILABLE or self.api_key == 'mock_mode':
            logger.warning("No API key provided or databento library not available - using mock mode")
            self.mock_mode = True
            self.client = None
        else:
            self.mock_mode = False
            try:
                if DATABENTO_AVAILABLE:
                    self.client = db.Historical(self.api_key)
                    logger.info("Initialized real Databento client")
                else:
                    self.client = None
                    logger.warning("Databento library not available, using HTTP fallback")
            except Exception as e:
                logger.error(f"Failed to initialize Databento client: {e}")
                self.mock_mode = True
                self.client = None
        
        # Legacy HTTP session for fallback
        self.base_url = "https://hist.databento.com/v0"
        self.session = requests.Session()
        self.rate_limit_delay = 0.1  # Seconds between requests
        self.last_request_time = 0
        
        if self.api_key and self.mock_mode:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })
        
        logger.info(f"Initialized DatabentoBridge (mock_mode={self.mock_mode})")
    
    def _is_explicit_contract(self, symbol: str) -> bool:
        """
        Detect if symbol is an explicit contract (e.g., 'HOQ5') vs root symbol (e.g., 'HO').
        
        Args:
            symbol: Symbol to check
            
        Returns:
            True if symbol appears to be an explicit contract
        """
        if len(symbol) < 4:
            return False
        
        # Check if ends with futures month code + year digit
        month_codes = ['F','G','H','J','K','M','N','Q','U','V','X','Z']
        if len(symbol) >= 4 and symbol[-2] in month_codes and symbol[-1].isdigit():
            return True
        
        return False
    
    def _rate_limit(self):
        """Enforce rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict) -> Dict:
        """Make authenticated request to Databento API."""
        if self.mock_mode:
            return self._mock_request(endpoint, params)
        
        self._rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Databento API request failed: {e}")
            raise
    
    def _mock_request(self, endpoint: str, params: Dict) -> Dict:
        """Mock Databento API responses for development."""
        logger.debug(f"Mock request to {endpoint} with params: {params}")
        
        # Simulate realistic responses based on endpoint
        if 'timeseries' in endpoint:
            return self._mock_timeseries_response(params)
        elif 'symbology' in endpoint:
            return self._mock_symbology_response(params)
        else:
            return {'data': [], 'metadata': {}}
    
    def _mock_timeseries_response(self, params: Dict) -> Dict:
        """Generate mock time series data."""
        start_date = parse_date(params.get('start', '2021-12-01'))
        end_date = parse_date(params.get('end', '2022-03-31'))
        symbols = params.get('symbols', ['OH']).split(',')
        
        # Generate realistic mock data
        data = []
        current_date = start_date
        
        # Base prices for different symbols
        base_prices = {
            'OH': 2.50,  # Heating oil futures base price
            'HO': 2.50,  # Heating oil futures base price
            'ES': 4500.00,  # E-mini S&P 500
            'CL': 75.00,  # Crude oil
            'GC': 2000.00,  # Gold
            'ZC': 500.00,  # Corn
        }
        
        # Default base prices for options
        for symbol_str in symbols:
            if ' C' in symbol_str or ' P' in symbol_str:
                base_prices.setdefault(symbol_str, 0.50)
        
        while current_date <= end_date:
            if is_trading_day(current_date):
                for symbol in symbols:
                    # Get base price and add realistic movement
                    # For futures, use the root symbol price
                    if ' ' in symbol:  # Option symbol
                        base_price = base_prices.get(symbol, 0.50)
                    else:  # Futures symbol
                        # Extract root from futures symbol (e.g., ESH4 -> ES)
                        root = ''.join([c for c in symbol if not c.isdigit()])[:-1]
                        base_price = base_prices.get(root, base_prices.get(symbol, 100.0))
                    
                    # Add some realistic price movement
                    days_elapsed = (current_date - start_date).days
                    trend = 1 + (days_elapsed * 0.001)  # Small upward trend
                    noise = np.random.normal(1, 0.02)   # 2% daily volatility
                    
                    price = base_price * trend * noise
                    
                    # Ensure positive prices
                    price = max(0.01, price)
                    
                    data.append({
                        'symbol': symbol,
                        'ts_event': int(current_date.timestamp() * 1e9),  # Nanoseconds
                        'open': price * 0.99,
                        'high': price * 1.02,
                        'low': price * 0.98,
                        'close': price,
                        'volume': np.random.randint(100, 10000)
                    })
            
            current_date += timedelta(days=1)
        
        return {
            'data': data,
            'metadata': {
                'dataset': 'OPRA',
                'schema': 'ohlcv-1d',
                'symbols': symbols
            }
        }
    
    def _mock_symbology_response(self, params: Dict) -> Dict:
        """Generate mock symbology data for options chains."""
        # Mock options chain for OH contracts
        underlying = params.get('underlying', 'OH')
        expiry = params.get('expiry', '2022-01')
        
        # Generate realistic strike range based on underlying
        strikes = []
        if underlying in ['OH', 'HO']:
            # Heating oil: $2.00 to $4.00 in $0.25 increments
            for strike in range(200, 400, 25):
                strikes.append(strike / 100.0)
        elif underlying == 'ES':
            # E-mini S&P: 4200 to 4800 in 50 point increments
            for strike in range(4200, 4800, 50):
                strikes.append(float(strike))
        elif underlying == 'CL':
            # Crude oil: $60 to $90 in $2 increments
            for strike in range(60, 90, 2):
                strikes.append(float(strike))
        else:
            # Generic range
            for strike in range(90, 110, 5):
                strikes.append(float(strike))
        
        # Map month to futures month code
        month_codes = {1: 'F', 2: 'G', 3: 'H', 4: 'J', 5: 'K', 6: 'M',
                      7: 'N', 8: 'Q', 9: 'U', 10: 'V', 11: 'X', 12: 'Z'}
        
        symbols = []
        for strike in strikes:
            # Parse expiry to get month and year
            try:
                year, month = expiry.split('-')
                month_num = int(month)
                year_digit = year[-1]  # Last digit of year
                month_code = month_codes.get(month_num, 'X')
                
                # Create option symbol based on underlying
                if underlying in ['OH', 'HO']:
                    base = 'OH'
                elif underlying == 'ES':
                    base = 'ES'
                elif underlying == 'CL':
                    base = 'CL'
                else:
                    base = underlying
                    
                symbol = f"{base}{month_code}{year_digit} C{int(strike * 100):05d}"
            except:
                continue
                
            symbols.append({
                'symbol': symbol,
                'underlying': underlying,
                'strike': strike,
                'option_type': 'C',
                'expiry': expiry
            })
        
        return {
            'data': symbols,
            'metadata': {
                'underlying': underlying,
                'expiry': expiry
            }
        }
    
    def fetch_futures_continuous(self, root: str, start_date: Union[str, datetime], 
                                end_date: Union[str, datetime]) -> pd.DataFrame:
        """
        Fetch continuous front-month futures data.
        
        Args:
            root: Futures root symbol (e.g., 'HO') or explicit contract (e.g., 'HOQ5')
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with OHLCV data
            
        Note:
            If 'root' is an explicit contract (e.g., 'HOQ5'), it will be used directly.
            If 'root' is a root symbol (e.g., 'HO'), it will be mapped to a specific 
            contract using hardcoded logic (currently only supports 2024 dates).
        """
        logger.info(f"Fetching futures data for {root}: {start_date} to {end_date}")
        
        # Convert dates to strings if needed
        if isinstance(start_date, datetime):
            start_date = start_date.strftime('%Y-%m-%d')
        if isinstance(end_date, datetime):
            end_date = end_date.strftime('%Y-%m-%d')
        
        # Import datetime for use in both contract paths
        from datetime import datetime as dt
        
        # Determine symbol to use - explicit contract or map from root symbol
        if self._is_explicit_contract(root):
            # It's already a specific contract (e.g., "HOQ5"), use it directly
            symbol = root
            logger.debug(f"Using explicit contract: {symbol}")
        else:
            # It's a root symbol (e.g., "HO"), map to specific contract using hardcoded logic
            date_obj = dt.strptime(start_date, '%Y-%m-%d')
            
            if root == 'OH' or root == 'HO':
                # Get front month heating oil contract for the date
                # Use March 2024 contract for early 2024 dates as example
                if date_obj.year == 2024 and date_obj.month <= 3:
                    symbol = 'HOH4'  # March 2024
                elif date_obj.year == 2024 and date_obj.month <= 6:
                    symbol = 'HOM4'  # June 2024
                else:
                    symbol = 'HOZ4'  # December 2024
            elif root == 'ES':
                # E-mini S&P 500 contracts
                if date_obj.year == 2024 and date_obj.month <= 3:
                    symbol = 'ESH4'  # March 2024
                elif date_obj.year == 2024 and date_obj.month <= 6:
                    symbol = 'ESM4'  # June 2024
                elif date_obj.year == 2024 and date_obj.month <= 9:
                    symbol = 'ESU4'  # September 2024
                else:
                    symbol = 'ESZ4'  # December 2024
            elif root == 'CL':
                # Crude oil contracts
                if date_obj.year == 2024 and date_obj.month <= 2:
                    symbol = 'CLG4'  # February 2024
                elif date_obj.year == 2024 and date_obj.month <= 5:
                    symbol = 'CLK4'  # May 2024
                else:
                    symbol = 'CLN4'  # July 2024
            else:
                # For other symbols, try to use the root directly
                # This might need specific contract mapping
                symbol = root
            
            logger.debug(f"Mapped root symbol '{root}' to contract '{symbol}' for date {start_date}")
        
        if not self.mock_mode and self.client:
            try:
                # Use official Databento client
                # Ensure end date is after start date for API
                start_dt = dt.strptime(start_date, '%Y-%m-%d')
                end_dt = dt.strptime(end_date, '%Y-%m-%d')
                if end_dt <= start_dt:
                    end_dt = start_dt + timedelta(days=1)
                    end_date_api = end_dt.strftime('%Y-%m-%d')
                else:
                    end_date_api = end_date
                    
                data = self.client.timeseries.get_range(
                    dataset='GLBX.MDP3',
                    schema='ohlcv-1d',
                    symbols=symbol,
                    start=start_date,
                    end=end_date_api
                )
                
                # Convert to DataFrame
                df = data.to_df()
                
                # The index is the timestamp, convert it to a column
                df = df.reset_index()
                if 'ts_event' in df.columns:
                    df['date'] = pd.to_datetime(df['ts_event'])
                elif 'index' in df.columns:
                    df['date'] = pd.to_datetime(df['index'])
                    df = df.drop('index', axis=1)
                elif 'timestamp' in df.columns:
                    df['date'] = pd.to_datetime(df['timestamp'])
                
                # Select required columns
                expected_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
                available_cols = [col for col in expected_cols if col in df.columns]
                df = df[available_cols].sort_values('date').reset_index(drop=True)
                
                logger.info(f"Retrieved {len(df)} days of futures data from Databento")
                return df
                
            except Exception as e:
                logger.error(f"Databento API error: {e}")
                # Fall back to mock mode for this request
                
        # Fallback to HTTP request or mock
        params = {
            'dataset': 'GLBX.MDP3',
            'schema': 'ohlcv-1d',
            'symbols': symbol,
            'start': start_date,
            'end': end_date
        }
        
        response = self._make_request('timeseries/get_range', params)
        
        # Convert to DataFrame
        data = response.get('data', [])
        if not data:
            logger.warning(f"No futures data returned for {root}")
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        
        # Convert timestamp and clean up
        if 'ts_event' in df.columns:
            df['date'] = pd.to_datetime(df['ts_event'] / 1e9, unit='s')
        df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
        df = df.sort_values('date').reset_index(drop=True)
        
        logger.info(f"Retrieved {len(df)} days of futures data")
        return df
    
    def fetch_options_chain(self, underlying: str, expiry_month: str, 
                           trade_date: Union[str, datetime]) -> List[Dict]:
        """
        Get available options for a specific expiry month.
        
        Args:
            underlying: Underlying symbol (e.g., 'ES')
            expiry_month: Target expiry (e.g., '2024-03')
            trade_date: Date to get chain for
            
        Returns:
            List of option contract details
        """
        logger.info(f"Fetching options chain for {underlying} {expiry_month} on {trade_date}")
        
        if self.mock_mode:
            # Use mock response
            params = {
                'underlying': underlying,
                'expiry': expiry_month,
                'date': trade_date if isinstance(trade_date, str) else trade_date.strftime('%Y-%m-%d')
            }
            response = self._mock_symbology_response(params)
            return response.get('data', [])
        
        # For real API, we need to get definitions and filter
        if isinstance(trade_date, str):
            trade_date_str = trade_date
        else:
            trade_date_str = trade_date.strftime('%Y-%m-%d')
        
        try:
            # Get the futures contract for this expiry
            year, month = expiry_month.split('-')
            month_num = int(month)
            year_digit = year[-1]
            
            # Map to futures month code
            month_codes = {1: 'F', 2: 'G', 3: 'H', 4: 'J', 5: 'K', 6: 'M',
                          7: 'N', 8: 'Q', 9: 'U', 10: 'V', 11: 'X', 12: 'Z'}
            month_code = month_codes.get(month_num, 'X')
            
            # Build futures contract symbol
            futures_symbol = f"{underlying}{month_code}{year_digit}"
            
            # Get definitions for a short time window to find options
            data = self.client.timeseries.get_range(
                dataset='GLBX.MDP3',
                schema='definition',
                symbols='ALL_SYMBOLS',
                stype_in='raw_symbol',
                start=f'{trade_date_str}T00:00',
                end=f'{trade_date_str}T01:00'  # Just 1 hour of definitions
            )
            
            df = data.to_df()
            
            # Filter for options on our futures contract
            options_mask = (
                df['raw_symbol'].str.startswith(futures_symbol + ' ', na=False) &
                df['instrument_class'].isin(['C', 'P'])  # Call and Put options
            )
            options_df = df[options_mask].copy()
            
            # Parse option details
            options_data = []
            for _, row in options_df.iterrows():
                raw_symbol = row['raw_symbol']
                parts = raw_symbol.split(' ')
                if len(parts) >= 2:
                    option_type = parts[1][0]  # 'C' or 'P'
                    strike_str = parts[1][1:]  # Strike price
                    try:
                        strike = float(strike_str)
                        options_data.append({
                            'symbol': raw_symbol,
                            'underlying': futures_symbol,
                            'strike': strike,
                            'option_type': option_type,
                            'expiry': expiry_month
                        })
                    except ValueError:
                        continue
            
            logger.info(f"Found {len(options_data)} options in chain")
            return options_data
            
        except Exception as e:
            logger.error(f"Failed to fetch options chain: {e}")
            return []
    
    def fetch_option_history(self, symbol: str, start_date: Union[str, datetime], 
                            end_date: Union[str, datetime], schema: str = 'ohlcv-1d') -> pd.DataFrame:
        """
        Get historical data for specific option contract.
        
        Args:
            symbol: Option symbol (e.g., 'OHF2 C27800')
            start_date: Start date
            end_date: End date
            schema: Data schema type (default: 'ohlcv-1d')
            
        Returns:
            DataFrame with option data
        """
        logger.info(f"Fetching option history for {symbol}: {start_date} to {end_date} (schema: {schema})")
        
        # Convert dates to strings if needed
        if isinstance(start_date, datetime):
            start_date = start_date.strftime('%Y-%m-%d')
        if isinstance(end_date, datetime):
            end_date = end_date.strftime('%Y-%m-%d')
        
        # Use real databento client if available
        if not self.mock_mode and self.client:
            try:
                # Ensure end date is after start date for API
                from datetime import datetime as dt, timedelta
                start_dt = dt.strptime(start_date, '%Y-%m-%d')
                end_dt = dt.strptime(end_date, '%Y-%m-%d')
                if end_dt <= start_dt:
                    end_dt = start_dt + timedelta(days=1)
                    end_date_api = end_dt.strftime('%Y-%m-%d')
                else:
                    end_date_api = end_date
                    
                data = self.client.timeseries.get_range(
                    dataset='GLBX.MDP3',
                    schema=schema,
                    symbols=symbol,
                    start=start_date,
                    end=end_date_api
                )
                
                # Convert to DataFrame
                df = data.to_df()
                
                # The index is the timestamp, convert it to a column
                df = df.reset_index()
                if 'ts_event' in df.columns:
                    df['date'] = pd.to_datetime(df['ts_event'])
                elif 'index' in df.columns:
                    df['date'] = pd.to_datetime(df['index'])
                    df = df.drop('index', axis=1)
                
                # Handle different schemas
                if schema == 'ohlcv-1d':
                    expected_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
                    available_cols = [col for col in expected_cols if col in df.columns]
                    df = df[available_cols]
                elif schema in ['trades', 'mbp-1', 'mbo']:
                    # Keep relevant columns for tick data
                    available_cols = ['date'] + [col for col in ['price', 'size', 'bid_px', 'ask_px', 'bid_sz', 'ask_sz'] if col in df.columns]
                    df = df[available_cols]
                
                df = df.sort_values('date').reset_index(drop=True)
                logger.info(f"Retrieved {len(df)} days of option data from Databento")
                return df
                
            except Exception as e:
                logger.error(f"Databento API error: {e}")
                # Fall back to HTTP request
        
        # Fallback to HTTP request
        params = {
            'dataset': 'GLBX.MDP3',  # CME Globex dataset for futures/options
            'schema': schema,
            'symbols': symbol,
            'start': start_date,
            'end': end_date
        }
        
        response = self._make_request('timeseries/get_range', params)
        
        # Convert to DataFrame
        data = response.get('data', [])
        if not data:
            logger.warning(f"No option data returned for {symbol}")
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        
        # Convert timestamp and clean up based on schema
        df['date'] = pd.to_datetime(df['ts_event'] / 1e9, unit='s')
        
        # Format columns based on schema type
        if schema == 'ohlcv-1d':
            df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
        elif schema in ['trades', 'mbp-1', 'mbo']:
            # Keep relevant columns for tick data
            available_cols = ['date'] + [col for col in ['price', 'size', 'bid_px', 'ask_px', 'bid_sz', 'ask_sz'] if col in df.columns]
            df = df[available_cols]
        elif schema == 'statistics':
            # Keep statistics columns
            stat_cols = ['date'] + [col for col in df.columns if col not in ['ts_event', 'date']]
            df = df[stat_cols]
        
        df = df.sort_values('date').reset_index(drop=True)
        
        logger.info(f"Retrieved {len(df)} days of option data")
        return df
    
    def get_spot_price(self, underlying: str, date: Union[str, datetime]) -> float:
        """
        Get spot price for underlying on specific date.
        
        Args:
            underlying: Root symbol (e.g., 'HO') or explicit contract (e.g., 'HOQ5')
            date: Date to get price for
            
        Returns:
            Spot price
            
        Note:
            If 'underlying' is an explicit contract, it will be used directly.
            If 'underlying' is a root symbol, it will be mapped to a specific contract.
        """
        # For futures, we use the futures price as "spot"
        start_date = date if isinstance(date, str) else date.strftime('%Y-%m-%d')
        end_date = start_date
        
        df = self.fetch_futures_continuous(underlying, start_date, end_date)
        
        if len(df) > 0:
            return float(df['close'].iloc[0])
        else:
            logger.warning(f"No spot price found for {underlying} on {date}")
            return 2.5  # Default fallback


def main():
    """Test the Databento client."""
    from utils.logging_config import setup_logging
    
    # Set up logging
    setup_logging()
    
    # Create client
    client = DatabentoBridge()
    
    # Test futures data
    logger.info("Testing futures data fetch...")
    futures_df = client.fetch_futures_continuous('OH', '2021-12-01', '2021-12-10')
    logger.info(f"Fetched {len(futures_df)} rows of futures data")
    logger.debug(f"Sample data: {futures_df.head()}")
    
    # Test options chain
    logger.info("Testing options chain fetch...")
    chain = client.fetch_options_chain('OH', '2022-01', '2021-12-01')
    logger.info(f"Found {len(chain)} options in chain")
    if chain:
        logger.debug(f"Sample options: {chain[:3]}")
    
    # Test option history
    logger.info("Testing option history fetch...")
    option_df = client.fetch_option_history('OHF2 C27800', '2021-12-01', '2021-12-10')
    logger.info(f"Fetched {len(option_df)} rows of option data")
    logger.debug(f"Sample option data: {option_df.head()}")


if __name__ == "__main__":
    main()