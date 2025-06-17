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
        
        if not self.api_key or not DATABENTO_AVAILABLE:
            logger.warning("No API key provided or databento library not available - using mock mode")
            self.mock_mode = True
            self.client = None
        else:
            self.mock_mode = False
            try:
                self.client = db.Historical(self.api_key)
                logger.info("Initialized real Databento client")
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
            'OH': 2.50,  # Futures base price
            'OHF2 C27800': 0.10,
            'OHG2 C24500': 2.00,
            'OHH2 C27000': 1.50,
            'OHJ2 C30200': 4.00,
            'OHK2 C35000': 25.00
        }
        
        while current_date <= end_date:
            if is_trading_day(current_date):
                for symbol in symbols:
                    # Get base price and add realistic movement
                    base_price = base_prices.get(symbol, 1.0)
                    
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
        
        # Generate realistic strike range
        strikes = []
        for strike in range(200, 400, 25):  # $2.00 to $4.00 in $0.25 increments
            strikes.append(strike / 100.0)
        
        symbols = []
        for strike in strikes:
            # Create option symbol
            if expiry == '2022-01':
                symbol = f"OHF2 C{int(strike * 100):05d}"
            elif expiry == '2022-02':
                symbol = f"OHG2 C{int(strike * 100):05d}"
            elif expiry == '2022-03':
                symbol = f"OHH2 C{int(strike * 100):05d}"
            elif expiry == '2022-04':
                symbol = f"OHJ2 C{int(strike * 100):05d}"
            elif expiry == '2022-05':
                symbol = f"OHK2 C{int(strike * 100):05d}"
            else:
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
            root: Futures root symbol (e.g., 'HO')
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with OHLCV data
        """
        logger.info(f"Fetching futures data for {root}: {start_date} to {end_date}")
        
        # Convert dates to strings if needed
        if isinstance(start_date, datetime):
            start_date = start_date.strftime('%Y-%m-%d')
        if isinstance(end_date, datetime):
            end_date = end_date.strftime('%Y-%m-%d')
        
        # Map symbols - use front month contract instead of root
        if root == 'OH' or root == 'HO':
            # Get front month heating oil contract for the date
            from datetime import datetime as dt
            date_obj = dt.strptime(start_date, '%Y-%m-%d')
            # Use March 2024 contract for early 2024 dates as example
            if date_obj.year == 2024 and date_obj.month <= 3:
                symbol = 'HOH4'  # March 2024
            elif date_obj.year == 2024 and date_obj.month <= 6:
                symbol = 'HOM4'  # June 2024
            else:
                symbol = 'HOZ4'  # December 2024
        else:
            symbol = root
        
        if not self.mock_mode and self.client:
            try:
                # Use official Databento client
                data = self.client.timeseries.get_range(
                    dataset='GLBX.MDP3',
                    schema='ohlcv-1d',
                    symbols=symbol,
                    start=start_date,
                    end=end_date
                )
                
                # Convert to DataFrame
                df = data.to_df()
                
                # Rename columns to match expected format
                if 'ts_event' in df.columns:
                    df['date'] = pd.to_datetime(df['ts_event'])
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
            underlying: Underlying symbol (e.g., 'OH')
            expiry_month: Target expiry (e.g., '2022-01')
            trade_date: Date to get chain for
            
        Returns:
            List of option contract details
        """
        logger.info(f"Fetching options chain for {underlying} {expiry_month} on {trade_date}")
        
        # Make symbology request
        params = {
            'underlying': underlying,
            'expiry': expiry_month,
            'date': trade_date if isinstance(trade_date, str) else trade_date.strftime('%Y-%m-%d')
        }
        
        response = self._make_request('symbology/get_range', params)
        
        options_data = response.get('data', [])
        
        logger.info(f"Found {len(options_data)} options in chain")
        return options_data
    
    def fetch_option_history(self, symbol: str, start_date: Union[str, datetime], 
                            end_date: Union[str, datetime]) -> pd.DataFrame:
        """
        Get historical OHLCV data for specific option contract.
        
        Args:
            symbol: Option symbol (e.g., 'OHF2 C27800')
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with OHLCV data
        """
        logger.info(f"Fetching option history for {symbol}: {start_date} to {end_date}")
        
        # Convert dates to strings if needed
        if isinstance(start_date, datetime):
            start_date = start_date.strftime('%Y-%m-%d')
        if isinstance(end_date, datetime):
            end_date = end_date.strftime('%Y-%m-%d')
        
        # Make API request  
        params = {
            'dataset': 'GLBX.MDP3',  # CME Globex dataset for futures/options
            'schema': 'ohlcv-1d',
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
        
        # Convert timestamp and clean up
        df['date'] = pd.to_datetime(df['ts_event'] / 1e9, unit='s')
        df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
        df = df.sort_values('date').reset_index(drop=True)
        
        logger.info(f"Retrieved {len(df)} days of option data")
        return df
    
    def get_spot_price(self, underlying: str, date: Union[str, datetime]) -> float:
        """
        Get spot price for underlying on specific date.
        
        Args:
            underlying: Underlying symbol
            date: Date to get price for
            
        Returns:
            Spot price
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
    print("Testing futures data fetch...")
    futures_df = client.fetch_futures_continuous('OH', '2021-12-01', '2021-12-10')
    print(f"Fetched {len(futures_df)} rows of futures data")
    print(futures_df.head())
    
    # Test options chain
    print("\nTesting options chain fetch...")
    chain = client.fetch_options_chain('OH', '2022-01', '2021-12-01')
    print(f"Found {len(chain)} options in chain")
    if chain:
        print("Sample options:", chain[:3])
    
    # Test option history
    print("\nTesting option history fetch...")
    option_df = client.fetch_option_history('OHF2 C27800', '2021-12-01', '2021-12-10')
    print(f"Fetched {len(option_df)} rows of option data")
    print(option_df.head())


if __name__ == "__main__":
    main()