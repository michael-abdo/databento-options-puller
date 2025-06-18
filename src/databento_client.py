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
                    
                    # Special handling for options
                    if ' C' in symbol or ' P' in symbol:
                        # Extract strike from symbol
                        try:
                            parts = symbol.split(' ')
                            strike_str = parts[1][1:]  # Remove 'C' or 'P'
                            strike = float(strike_str) / 100.0  # Convert cents to dollars
                        except:
                            strike = 3.0  # Default strike
                        
                        # Get futures price (assume around 2.5 for HO)
                        futures_price = 2.5
                        
                        # Calculate time to expiry (assume 60 days for simplicity)
                        days_to_expiry = max(1, 60 - days_elapsed)
                        time_to_expiry = days_to_expiry / 365.0
                        
                        # Simple option pricing for 15-delta options
                        moneyness = futures_price / strike
                        
                        if moneyness > 1.0:  # In the money
                            intrinsic = futures_price - strike
                            time_value = 0.1 * np.sqrt(time_to_expiry)
                        else:  # Out of the money
                            intrinsic = 0
                            # For 15-delta options, typical values range from 0.05 to 0.20
                            time_value = 0.15 * np.sqrt(time_to_expiry) * (strike / futures_price)
                        
                        # Add randomness
                        volatility = np.random.normal(1.0, 0.1)
                        price = max(0.01, (intrinsic + time_value) * volatility)
                        price = round(price, 2)
                    else:
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
                
                # Create option symbol based on underlying with proper strike formatting
                if underlying in ['OH', 'HO']:
                    base = 'OH'
                    # Heating oil: strikes in cents * 100 (e.g., $2.78 -> C27800)
                    strike_formatted = f"C{int(strike * 100):05d}"
                elif underlying == 'ES':
                    base = 'ES'
                    # E-mini S&P: strikes in points (e.g., 4500 -> C4500)
                    strike_formatted = f"C{int(strike)}"
                elif underlying == 'CL':
                    base = 'CL'
                    # Crude oil: strikes in dollars * 100 (e.g., $75.00 -> C7500)
                    strike_formatted = f"C{int(strike * 100)}"
                else:
                    base = underlying
                    # Generic format
                    strike_formatted = f"C{int(strike * 100)}"
                    
                symbol = f"{base}{month_code}{year_digit} {strike_formatted}"
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
            # It's a root symbol (e.g., "HO"), use continuous contract
            if root == 'OH' or root == 'HO':
                # For HO root symbol, always use continuous contract
                symbol = 'HO'
            elif root == 'ES':
                # E-mini S&P 500 contracts
                date_obj = dt.strptime(start_date, '%Y-%m-%d')
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
                date_obj = dt.strptime(start_date, '%Y-%m-%d')
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
            logger.info(f"🔍 STEP 1: Attempting Databento API call for futures symbol '{symbol}' ({start_date} to {end_date})")
            logger.info(f"📡 Using API Key: ...{self.api_key[-8:] if self.api_key else 'None'}")
            
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
                    
                # Always use continuous contract for HO futures
                if symbol.startswith('HO'):
                    # Use continuous front month contract
                    continuous_symbol = "HO.c.0"
                    logger.info(f"🎯 FUTURES REQUEST: Using continuous symbol '{continuous_symbol}' for HO futures")
                    data = self.client.timeseries.get_range(
                        dataset='GLBX.MDP3',
                        schema='ohlcv-1d',
                        symbols=continuous_symbol,
                        stype_in='continuous',
                        start=start_date,
                        end=end_date_api
                    )
                elif self._is_explicit_contract(symbol):
                    logger.info(f"🎯 FUTURES REQUEST: Using explicit contract symbol '{symbol}'")
                    data = self.client.timeseries.get_range(
                        dataset='GLBX.MDP3',
                        schema='ohlcv-1d',
                        symbols=symbol,
                        stype_in='raw_symbol',
                        start=start_date,
                        end=end_date_api
                    )
                else:
                    # Use continuous front month contract
                    continuous_symbol = f"{symbol}.c.0"
                    logger.info(f"🎯 FUTURES REQUEST: Using continuous symbol '{continuous_symbol}' for root '{symbol}'")
                    data = self.client.timeseries.get_range(
                        dataset='GLBX.MDP3',
                        schema='ohlcv-1d',
                        symbols=continuous_symbol,
                        stype_in='continuous',
                        start=start_date,
                        end=end_date_api
                    )
                
                logger.info(f"✅ STEP 2: Databento API call successful - converting to DataFrame")
                
                # Convert to DataFrame
                df = data.to_df()
                
                logger.info(f"📊 STEP 3: Raw DataFrame shape: {df.shape}, columns: {list(df.columns)}")
                
                # The index is the timestamp, convert it to a column
                df = df.reset_index()
                if 'ts_event' in df.columns:
                    df['date'] = pd.to_datetime(df['ts_event'])
                    logger.info(f"🕒 Using 'ts_event' column for dates")
                elif 'index' in df.columns:
                    df['date'] = pd.to_datetime(df['index'])
                    df = df.drop('index', axis=1)
                    logger.info(f"🕒 Using 'index' column for dates")
                elif 'timestamp' in df.columns:
                    df['date'] = pd.to_datetime(df['timestamp'])
                    logger.info(f"🕒 Using 'timestamp' column for dates")
                else:
                    logger.warning(f"⚠️ No timestamp column found in DataFrame")
                
                # Select required columns
                expected_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
                available_cols = [col for col in expected_cols if col in df.columns]
                df = df[available_cols].sort_values('date').reset_index(drop=True)
                
                logger.info(f"✅ STEP 4: Retrieved {len(df)} days of futures data from Databento API")
                if len(df) > 0:
                    logger.info(f"📈 Sample data - First row: {df.iloc[0].to_dict()}")
                    logger.info(f"📈 Sample data - Last row: {df.iloc[-1].to_dict()}")
                
                return df
                
            except Exception as e:
                logger.error(f"❌ STEP 2: Databento API call FAILED with error: {e}")
                logger.error(f"🔍 Error type: {type(e).__name__}")
                
                # Check for specific error types
                if "401" in str(e) or "authentication" in str(e).lower():
                    logger.error(f"🔐 DIAGNOSIS: Authentication failed - API key may be invalid or lack permissions")
                elif "404" in str(e) or "not found" in str(e).lower():
                    logger.error(f"📭 DIAGNOSIS: Data not found - symbol may not exist in dataset")
                elif "403" in str(e) or "forbidden" in str(e).lower():
                    logger.error(f"🚫 DIAGNOSIS: Forbidden - API key lacks permissions for this data")
                else:
                    logger.error(f"❓ DIAGNOSIS: Unknown error type")
                
                logger.info(f"🔄 STEP 3: Falling back to HTTP request method")
                
        # Fallback to HTTP request or mock
        logger.info(f"🌐 STEP 4: Attempting HTTP fallback request")
        
        params = {
            'dataset': 'GLBX.MDP3',
            'schema': 'ohlcv-1d',
            'symbols': symbol,
            'start': start_date,
            'end': end_date
        }
        
        logger.info(f"🔗 HTTP REQUEST: {self.base_url}/timeseries/get_range")
        logger.info(f"📋 HTTP PARAMS: {params}")
        
        try:
            response = self._make_request('timeseries/get_range', params)
            logger.info(f"✅ STEP 5: HTTP request successful")
            
            # Convert to DataFrame
            data = response.get('data', [])
            if not data:
                logger.warning(f"📭 STEP 6: HTTP response contains no data for symbol '{root}'")
                logger.info(f"🔍 Full response keys: {list(response.keys())}")
                return pd.DataFrame()
            
            logger.info(f"📊 STEP 6: HTTP response contains {len(data)} data records")
            df = pd.DataFrame(data)
            
            # Convert timestamp and clean up
            if 'ts_event' in df.columns:
                df['date'] = pd.to_datetime(df['ts_event'] / 1e9, unit='s')
                logger.info(f"🕒 HTTP: Using 'ts_event' column for dates")
            else:
                logger.warning(f"⚠️ HTTP: No 'ts_event' column found")
                
            expected_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
            available_cols = [col for col in expected_cols if col in df.columns]
            df = df[available_cols]
            df = df.sort_values('date').reset_index(drop=True)
            
            logger.info(f"✅ STEP 7: Retrieved {len(df)} days of futures data via HTTP")
            if len(df) > 0:
                logger.info(f"📈 HTTP Sample - First row: {df.iloc[0].to_dict()}")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ STEP 5: HTTP fallback FAILED with error: {e}")
            logger.error(f"🔍 HTTP Error type: {type(e).__name__}")
            
            if "401" in str(e):
                logger.error(f"🔐 HTTP DIAGNOSIS: Authentication failed - no auth headers in HTTP request")
            elif "404" in str(e):
                logger.error(f"📭 HTTP DIAGNOSIS: Endpoint not found or data unavailable")
            elif "403" in str(e):
                logger.error(f"🚫 HTTP DIAGNOSIS: Forbidden - insufficient permissions")
            
            logger.info(f"🎭 STEP 6: All methods failed - returning empty DataFrame")
            return pd.DataFrame()
    
    def fetch_options_chain(self, underlying: str, expiry_month: str, 
                           trade_date: Union[str, datetime]) -> List[Dict]:
        """
        Get available options for a specific expiry month.
        
        Args:
            underlying: Underlying symbol (e.g., 'HO')
            expiry_month: Target expiry (e.g., '2022-02')
            trade_date: Date to get chain for
            
        Returns:
            List of option contract details
        """
        trade_date_str = trade_date if isinstance(trade_date, str) else trade_date.strftime('%Y-%m-%d')
        logger.info(f"🔍 STEP 1: Attempting options chain fetch for '{underlying}' {expiry_month} on {trade_date_str}")
        logger.info(f"📡 Using API Key: ...{self.api_key[-8:] if self.api_key else 'None'}")
        
        # Use real Databento API if available
        if not self.mock_mode and self.client:
            logger.info(f"🎯 STEP 2: Using official Databento API client for options chain")
            
            try:
                # For HO futures, options use OH prefix
                option_symbol = 'OH.OPT' if underlying == 'HO' else f'{underlying}.OPT'
                logger.info(f"🔗 SYMBOL MAPPING: '{underlying}' -> '{option_symbol}' for options parent")
                
                # Get option definitions
                logger.info(f"📋 OPTIONS REQUEST: Fetching definitions for '{option_symbol}' on {trade_date_str}")
                definitions = self.client.timeseries.get_range(
                    dataset='GLBX.MDP3',
                    schema='definition',
                    symbols=option_symbol,
                    stype_in='parent',
                    start=trade_date,
                    end=pd.to_datetime(trade_date) + timedelta(days=1)
                )
                
                logger.info(f"✅ STEP 3: Databento definitions API call successful - converting to DataFrame")
                df = definitions.to_df()
                
                logger.info(f"📊 STEP 4: Raw definitions DataFrame shape: {df.shape}")
                if len(df) > 0:
                    logger.info(f"🔍 Available columns: {list(df.columns)}")
                    logger.info(f"📈 Sample definition - First row: {df.iloc[0].to_dict()}")
                else:
                    logger.warning(f"📭 STEP 4: No definitions found for '{option_symbol}' on {trade_date_str}")
                    return []
                
                # Parse expiry month
                target_year = int(expiry_month.split('-')[0])
                target_month = int(expiry_month.split('-')[1])
                logger.info(f"🎯 TARGET EXPIRY: {target_year}-{target_month:02d} (year={target_year}, month={target_month})")
                
                # Convert expiration to datetime
                df['expiration'] = pd.to_datetime(df['expiration'])
                logger.info(f"📅 STEP 5: Converted expiration column to datetime")
                
                # Filter for target month call options
                logger.info(f"🔍 STEP 6: Filtering for call options in target month")
                options = df[
                    (df['symbol'].str.contains(' C', na=False)) &  # Calls only
                    (df['expiration'].dt.year == target_year) &
                    (df['expiration'].dt.month == target_month)
                ]
                
                logger.info(f"📊 FILTERING RESULTS:")
                logger.info(f"   - Total definitions: {len(df)}")
                logger.info(f"   - Call options found: {len(options)}")
                logger.info(f"   - Target year/month: {target_year}-{target_month:02d}")
                
                result = []
                for _, row in options.iterrows():
                    symbol = row['symbol']
                    # Strike price is already in dollars in the data
                    strike = float(row['strike_price'])
                    
                    result.append({
                        'symbol': symbol,
                        'underlying': underlying,
                        'strike': strike,
                        'option_type': 'C',
                        'expiry': row['expiration'].strftime('%Y-%m-%d')
                    })
                
                logger.info(f"✅ STEP 7: Successfully parsed {len(result)} call options for {expiry_month}")
                if len(result) > 0:
                    logger.info(f"📈 Sample options - First: {result[0]}")
                    logger.info(f"📈 Sample options - Last: {result[-1]}")
                
                return result
                
            except Exception as e:
                logger.error(f"❌ STEP 3: Databento options API call FAILED with error: {e}")
                logger.error(f"🔍 Error type: {type(e).__name__}")
                
                # Check for specific error types
                if "401" in str(e) or "authentication" in str(e).lower():
                    logger.error(f"🔐 DIAGNOSIS: Authentication failed - API key may be invalid or lack permissions")
                elif "404" in str(e) or "not found" in str(e).lower():
                    logger.error(f"📭 DIAGNOSIS: Options data not found - symbol '{option_symbol}' may not exist in dataset")
                elif "403" in str(e) or "forbidden" in str(e).lower():
                    logger.error(f"🚫 DIAGNOSIS: Forbidden - API key lacks permissions for options data")
                else:
                    logger.error(f"❓ DIAGNOSIS: Unknown error type")
                
                logger.info(f"🔄 STEP 4: Falling back to alternative methods")
                # Fall back to mock mode
        
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
        # Convert dates to strings if needed
        if isinstance(start_date, datetime):
            start_date = start_date.strftime('%Y-%m-%d')
        if isinstance(end_date, datetime):
            end_date = end_date.strftime('%Y-%m-%d')
            
        logger.info(f"🔍 STEP 1: Attempting option history fetch for '{symbol}' ({start_date} to {end_date})")
        logger.info(f"📋 Schema: {schema}")
        logger.info(f"📡 Using API Key: ...{self.api_key[-8:] if self.api_key else 'None'}")
        
        # Use real databento client if available
        if not self.mock_mode and self.client:
            logger.info(f"🎯 STEP 2: Using official Databento API client for option history")
            
            try:
                # Ensure end date is after start date for API
                from datetime import datetime as dt, timedelta
                start_dt = dt.strptime(start_date, '%Y-%m-%d')
                end_dt = dt.strptime(end_date, '%Y-%m-%d')
                if end_dt <= start_dt:
                    end_dt = start_dt + timedelta(days=1)
                    end_date_api = end_dt.strftime('%Y-%m-%d')
                    logger.info(f"📅 Adjusted end date from {end_date} to {end_date_api} (must be after start)")
                else:
                    end_date_api = end_date
                    
                logger.info(f"📋 OPTION HISTORY REQUEST: symbol='{symbol}', dataset='GLBX.MDP3', schema='{schema}'")
                logger.info(f"📅 Date range: {start_date} to {end_date_api}")
                
                data = self.client.timeseries.get_range(
                    dataset='GLBX.MDP3',
                    schema=schema,
                    symbols=symbol,
                    start=start_date,
                    end=end_date_api
                )
                
                logger.info(f"✅ STEP 3: Databento option history API call successful - converting to DataFrame")
                
                # Convert to DataFrame
                df = data.to_df()
                
                logger.info(f"📊 STEP 4: Raw option DataFrame shape: {df.shape}, columns: {list(df.columns)}")
                
                # The index is the timestamp, convert it to a column
                df = df.reset_index()
                if 'ts_event' in df.columns:
                    df['date'] = pd.to_datetime(df['ts_event'])
                    logger.info(f"🕒 Using 'ts_event' column for dates")
                elif 'index' in df.columns:
                    df['date'] = pd.to_datetime(df['index'])
                    df = df.drop('index', axis=1)
                    logger.info(f"🕒 Using 'index' column for dates")
                else:
                    logger.warning(f"⚠️ No timestamp column found in option DataFrame")
                
                # Handle different schemas
                logger.info(f"📋 STEP 5: Processing schema '{schema}' columns")
                if schema == 'ohlcv-1d':
                    expected_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
                    available_cols = [col for col in expected_cols if col in df.columns]
                    df = df[available_cols]
                    logger.info(f"📊 OHLCV columns selected: {available_cols}")
                elif schema in ['trades', 'mbp-1', 'mbo']:
                    # Keep relevant columns for tick data
                    available_cols = ['date'] + [col for col in ['price', 'size', 'bid_px', 'ask_px', 'bid_sz', 'ask_sz'] if col in df.columns]
                    df = df[available_cols]
                    logger.info(f"📊 Tick data columns selected: {available_cols}")
                
                df = df.sort_values('date').reset_index(drop=True)
                
                logger.info(f"✅ STEP 6: Retrieved {len(df)} days of option data from Databento API")
                if len(df) > 0:
                    logger.info(f"📈 Sample option data - First row: {df.iloc[0].to_dict()}")
                    logger.info(f"📈 Sample option data - Last row: {df.iloc[-1].to_dict()}")
                
                return df
                
            except Exception as e:
                logger.error(f"❌ STEP 3: Databento option history API call FAILED with error: {e}")
                logger.error(f"🔍 Error type: {type(e).__name__}")
                
                # Check for specific error types
                if "401" in str(e) or "authentication" in str(e).lower():
                    logger.error(f"🔐 DIAGNOSIS: Authentication failed - API key may be invalid or lack permissions")
                elif "404" in str(e) or "not found" in str(e).lower():
                    logger.error(f"📭 DIAGNOSIS: Option data not found - symbol '{symbol}' may not exist in dataset")
                elif "403" in str(e) or "forbidden" in str(e).lower():
                    logger.error(f"🚫 DIAGNOSIS: Forbidden - API key lacks permissions for option data")
                else:
                    logger.error(f"❓ DIAGNOSIS: Unknown error type")
                
                logger.info(f"🔄 STEP 4: Falling back to HTTP request method")
                # Fall back to HTTP request
        
        # Fallback to HTTP request
        logger.info(f"🌐 STEP 5: Attempting HTTP fallback for option history")
        
        params = {
            'dataset': 'GLBX.MDP3',  # CME Globex dataset for futures/options
            'schema': schema,
            'symbols': symbol,
            'start': start_date,
            'end': end_date
        }
        
        logger.info(f"🔗 HTTP REQUEST: {self.base_url}/timeseries/get_range")
        logger.info(f"📋 HTTP PARAMS: {params}")
        
        try:
            response = self._make_request('timeseries/get_range', params)
            logger.info(f"✅ STEP 6: HTTP option history request successful")
            
            # Convert to DataFrame
            data = response.get('data', [])
            if not data:
                logger.warning(f"📭 STEP 7: HTTP response contains no option data for '{symbol}'")
                logger.info(f"🔍 Full response keys: {list(response.keys())}")
                return pd.DataFrame()
            
            logger.info(f"📊 STEP 7: HTTP response contains {len(data)} option data records")
            df = pd.DataFrame(data)
            
            # Convert timestamp and clean up based on schema
            if 'ts_event' in df.columns:
                df['date'] = pd.to_datetime(df['ts_event'] / 1e9, unit='s')
                logger.info(f"🕒 HTTP: Using 'ts_event' column for dates")
            else:
                logger.warning(f"⚠️ HTTP: No 'ts_event' column found in option data")
            
            # Format columns based on schema type
            logger.info(f"📋 STEP 8: Processing HTTP option data for schema '{schema}'")
            if schema == 'ohlcv-1d':
                expected_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
                available_cols = [col for col in expected_cols if col in df.columns]
                df = df[available_cols]
                logger.info(f"📊 HTTP OHLCV columns selected: {available_cols}")
            elif schema in ['trades', 'mbp-1', 'mbo']:
                # Keep relevant columns for tick data
                available_cols = ['date'] + [col for col in ['price', 'size', 'bid_px', 'ask_px', 'bid_sz', 'ask_sz'] if col in df.columns]
                df = df[available_cols]
                logger.info(f"📊 HTTP tick data columns selected: {available_cols}")
            elif schema == 'statistics':
                # Keep statistics columns
                stat_cols = ['date'] + [col for col in df.columns if col not in ['ts_event', 'date']]
                df = df[stat_cols]
                logger.info(f"📊 HTTP statistics columns selected: {stat_cols}")
            
            df = df.sort_values('date').reset_index(drop=True)
            
            logger.info(f"✅ STEP 9: Retrieved {len(df)} days of option data via HTTP")
            if len(df) > 0:
                logger.info(f"📈 HTTP option sample - First row: {df.iloc[0].to_dict()}")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ STEP 6: HTTP option fallback FAILED with error: {e}")
            logger.error(f"🔍 HTTP Error type: {type(e).__name__}")
            
            if "401" in str(e):
                logger.error(f"🔐 HTTP DIAGNOSIS: Authentication failed - no auth headers in HTTP request")
            elif "404" in str(e):
                logger.error(f"📭 HTTP DIAGNOSIS: Endpoint not found or option data unavailable")
            elif "403" in str(e):
                logger.error(f"🚫 HTTP DIAGNOSIS: Forbidden - insufficient permissions")
            
            logger.info(f"🎭 STEP 7: All option history methods failed - returning empty DataFrame")
            return pd.DataFrame()
    
    def get_spot_price(self, underlying: str, date: Union[str, datetime]) -> float:
        """
        Get spot price for underlying on specific date.
        
        Args:
            underlying: Root symbol (e.g., 'HO') or explicit contract (e.g., 'HOQ5')
            date: Date to get price for
            
        Returns:
            Spot price
            
        Note:
            For HO contracts, always uses continuous contract regardless of input.
        """
        date_str = date if isinstance(date, str) else date.strftime('%Y-%m-%d')
        logger.info(f"🔍 STEP 1: Attempting spot price fetch for '{underlying}' on {date_str}")
        
        # For HO contracts, always use continuous contract
        if underlying.startswith('HO') or underlying == 'OH':
            symbol_to_use = 'HO'
            logger.info(f"🔗 SYMBOL MAPPING: '{underlying}' -> '{symbol_to_use}' (using HO continuous contract)")
        else:
            symbol_to_use = underlying
            logger.info(f"🔗 SYMBOL MAPPING: Using '{symbol_to_use}' directly")
            
        # For futures, we use the futures price as "spot"
        start_date = date_str
        end_date = start_date
        
        logger.info(f"📋 SPOT PRICE REQUEST: Fetching futures data for '{symbol_to_use}' on {date_str}")
        df = self.fetch_futures_continuous(symbol_to_use, start_date, end_date)
        
        if len(df) > 0:
            spot_price = float(df['close'].iloc[0])
            logger.info(f"✅ STEP 2: Successfully retrieved spot price: ${spot_price:.4f}")
            return spot_price
        else:
            logger.warning(f"📭 STEP 2: No futures data found for spot price calculation")
            logger.warning(f"🎭 Using default fallback spot price: $2.5000")
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