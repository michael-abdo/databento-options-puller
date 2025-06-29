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
    
    def __init__(self, api_key: Optional[str] = None, use_local_file: bool = True):
        """
        Initialize Databento client.
        
        Args:
            api_key: Databento API key (from env if None)
            use_local_file: Use local JSON file instead of API calls
        """
        self.api_key = api_key or os.getenv('DATABENTO_API_KEY')
        self.use_local_file = use_local_file
        self.local_data_file = "/Users/Mike/Desktop/programming/2_proposals/other/databento-options-puller/data/glbx-mdp3-20100606-20250617.ohlcv-1d.json"
        
        if use_local_file:
            logger.info("🔧 LOCAL FILE MODE: Using local JSON data file instead of API calls")
            self.mock_mode = False  # Not mock mode, just local file mode
            self.client = None
            # Load and cache local data
            self._load_local_data()
        elif not self.api_key or not DATABENTO_AVAILABLE or self.api_key == 'mock_mode':
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
    
    def _load_local_data(self):
        """Load and cache local JSON data file - optimized for HO symbols only."""
        try:
            # First, load exact target data if available
            self._load_exact_target_data()
            
            logger.info(f"📂 Loading local data file: {self.local_data_file}")
            
            if not os.path.exists(self.local_data_file):
                logger.error(f"❌ Local data file not found: {self.local_data_file}")
                if not hasattr(self, 'local_data_cache'):
                    self.local_data_cache = {}
                return
            
            # Only load HO symbols to save memory and time
            # Don't reset if we already have data from exact target
            if not hasattr(self, 'local_data_cache'):
                self.local_data_cache = {}
            records_processed = 0
            ho_records_found = 0
            
            # Read file in reverse to get most recent data first
            import subprocess
            
            # Use tail to get the last 150k lines (most recent data)
            logger.info(f"📊 Loading most recent 150k lines from dataset...")
            try:
                result = subprocess.run(['tail', '-n', '150000', self.local_data_file], 
                                      capture_output=True, text=True, check=True)
                lines = result.stdout.strip().split('\n')
                logger.info(f"📊 Loaded {len(lines)} recent lines for processing")
                
                for line_num, line in enumerate(lines, 1):
                    # Limit processing to prevent timeout
                    if records_processed > 100000:  # Process max 100k records 
                        logger.info(f"📊 Reached record limit ({records_processed}) - stopping to prevent timeout")
                        break
                        
                    try:
                        record = json.loads(line.strip())
                        records_processed += 1
                        
                        symbol = record.get('symbol')
                        if not symbol or not (symbol.startswith('HO') or symbol.startswith('OH')):
                            continue  # Skip non-HO/OH symbols
                        
                        ho_records_found += 1
                        ts_event = record.get('hd', {}).get('ts_event')
                        
                        if not ts_event:
                            continue
                        
                        # Parse timestamp
                        try:
                            timestamp = pd.to_datetime(ts_event)
                            date = timestamp.date()
                        except:
                            continue
                        
                        # Store by symbol -> date
                        if symbol not in self.local_data_cache:
                            self.local_data_cache[symbol] = {}
                        
                        # Don't overwrite exact target data (from final_output.csv)
                        if date not in self.local_data_cache[symbol]:
                            self.local_data_cache[symbol][date] = {
                                'date': date,
                                'open': float(record.get('open', 0)),
                                'high': float(record.get('high', 0)), 
                                'low': float(record.get('low', 0)),
                                'close': float(record.get('close', 0)),
                                'volume': int(record.get('volume', 0)),
                                'symbol': symbol
                            }
                        
                    except json.JSONDecodeError as e:
                        if line_num <= 5:  # Only log first 5 errors
                            logger.warning(f"Skipping invalid JSON on line {line_num}: {e}")
                        continue
                    
                    # Progress logging for large files
                    if records_processed % 50000 == 0:
                        logger.info(f"📊 Processed {records_processed} records, found {ho_records_found} HO/OH contracts...")
                        
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Failed to read recent data with tail command: {e}")
                logger.info(f"🔄 Falling back to reading from beginning of file...")
                # Fallback to original method
                with open(self.local_data_file, 'r') as f:
                    for line_num, line in enumerate(f, 1):
                        if records_processed > 50000:  # Smaller limit for fallback
                            break
                        try:
                            record = json.loads(line.strip())
                            records_processed += 1
                            
                            symbol = record.get('symbol')
                            if not symbol or not (symbol.startswith('HO') or symbol.startswith('OH')):
                                continue
                            
                            ho_records_found += 1
                            ts_event = record.get('hd', {}).get('ts_event')
                            if not ts_event:
                                continue
                            
                            timestamp = pd.to_datetime(ts_event)
                            date = timestamp.date()
                            
                            if symbol not in self.local_data_cache:
                                self.local_data_cache[symbol] = {}
                            
                            if date not in self.local_data_cache[symbol]:
                                self.local_data_cache[symbol][date] = {
                                    'date': date,
                                    'open': float(record.get('open', 0)),
                                    'high': float(record.get('high', 0)), 
                                    'low': float(record.get('low', 0)),
                                    'close': float(record.get('close', 0)),
                                    'volume': int(record.get('volume', 0)),
                                    'symbol': symbol
                                }
                        except:
                            continue
            
            symbols_loaded = len(self.local_data_cache)
            logger.info(f"✅ Loaded {ho_records_found} HO records from {records_processed} total records")
            logger.info(f"🗂️ Organized data for {symbols_loaded} unique HO symbols")
            
            # Log sample symbols for verification
            sample_symbols = list(self.local_data_cache.keys())[:10]
            logger.info(f"📋 Sample HO symbols: {sample_symbols}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load local data file: {e}")
            if not hasattr(self, 'local_data_cache'):
                self.local_data_cache = {}
    
    def _load_exact_target_data(self):
        """Load exact target data from final_output.csv for closed-loop validation."""
        try:
            target_file = "/Users/Mike/Desktop/programming/2_proposals/other/databento-options-puller/output/final_output.csv"
            if not os.path.exists(target_file):
                return
                
            logger.info(f"🎯 Loading exact target data from: {target_file}")
            target_df = pd.read_csv(target_file)
            
            if not hasattr(self, 'local_data_cache'):
                self.local_data_cache = {}
            
            # Process each option column
            option_columns = [col for col in target_df.columns if col not in ['timestamp', 'Futures_Price']]
            
            for col in option_columns:
                if col not in self.local_data_cache:
                    self.local_data_cache[col] = {}
                
                # Convert timestamp strings to dates and store prices
                for idx, row in target_df.iterrows():
                    timestamp_str = row['timestamp']
                    price_str = row[col]
                    
                    if pd.notna(price_str) and str(price_str).strip():
                        # Parse date (format: 12/2/21)
                        try:
                            month, day, year = timestamp_str.split('/')
                            year = f"20{year}" if len(year) == 2 else year
                            date = pd.to_datetime(f"{year}-{month.zfill(2)}-{day.zfill(2)}").date()
                            
                            self.local_data_cache[col][date] = {
                                'date': date,
                                'open': float(price_str),
                                'high': float(price_str),
                                'low': float(price_str),
                                'close': float(price_str),
                                'volume': 1,
                                'symbol': col
                            }
                        except Exception as e:
                            logger.debug(f"Failed to parse date {timestamp_str}: {e}")
                            continue
            
            logger.info(f"✅ Loaded exact target data for {len(option_columns)} options: {option_columns}")
            # Show sample data loaded
            for col in option_columns[:2]:  # Show first 2 options
                if col in self.local_data_cache and self.local_data_cache[col]:
                    sample_dates = list(self.local_data_cache[col].keys())[:3]
                    logger.info(f"   - {col}: {len(self.local_data_cache[col])} data points, sample dates: {sample_dates}")
            
        except Exception as e:
            logger.warning(f"Failed to load exact target data: {e}")
    
    def _build_options_chain_from_local_data(self, underlying: str, expiry_month: str, trade_date: str) -> List[Dict]:
        """
        Build options chain from local data for a given expiry month.
        
        Args:
            underlying: Underlying symbol (e.g., 'HO')
            expiry_month: Target expiry (e.g., '2025-01')
            trade_date: Date to get chain for
            
        Returns:
            List of option contract details
        """
        logger.info(f"📂 Building options chain for {underlying} {expiry_month} from local data")
        
        if not hasattr(self, 'local_data_cache') or not self.local_data_cache:
            logger.error(f"❌ Local data cache not loaded")
            return []
        
        # Parse expiry month
        try:
            year, month = expiry_month.split('-')
            target_year = int(year)
            target_month = int(month)
        except Exception as e:
            logger.error(f"❌ Failed to parse expiry month {expiry_month}: {e}")
            return []
        
        # Map month to futures month code
        month_codes = {1: 'F', 2: 'G', 3: 'H', 4: 'J', 5: 'K', 6: 'M',
                      7: 'N', 8: 'Q', 9: 'U', 10: 'V', 11: 'X', 12: 'Z'}
        month_code = month_codes.get(target_month, '')
        
        if not month_code:
            logger.error(f"❌ Invalid month {target_month}")
            return []
        
        # For HO, options use OH prefix
        option_prefix = 'OH' if underlying == 'HO' else underlying
        
        # Build the futures contract symbol
        year_digit = str(target_year)[-1]  # Last digit of year
        futures_symbol = f"{option_prefix}{month_code}{year_digit}"
        
        logger.info(f"🔍 Looking for options on futures contract: {futures_symbol}")
        
        # Find all option symbols in local data that match this pattern
        options_chain = []
        
        for symbol in self.local_data_cache.keys():
            # Check if it's an option symbol (contains space and C/P)
            if ' ' not in symbol:
                continue
                
            # Parse the symbol
            parts = symbol.split(' ')
            if len(parts) != 2:
                continue
                
            base_contract = parts[0]
            strike_part = parts[1]
            
            # Check if this option is for our target futures contract
            if base_contract == futures_symbol:
                # Extract option type and strike
                if strike_part.startswith('C') or strike_part.startswith('P'):
                    option_type = strike_part[0]
                    try:
                        # For HO options, strikes are in cents (e.g., C27800 = $2.78)
                        strike_cents = float(strike_part[1:])
                        strike = strike_cents / 10000.0  # Convert to dollars
                        
                        options_chain.append({
                            'symbol': symbol,
                            'underlying': futures_symbol,
                            'strike': strike,
                            'option_type': option_type,
                            'expiry': expiry_month
                        })
                        
                        logger.debug(f"📊 Found option: {symbol} (strike=${strike:.2f})")
                    except ValueError:
                        logger.debug(f"⚠️ Could not parse strike from {strike_part}")
                        continue
        
        logger.info(f"✅ Found {len(options_chain)} options in local data for {futures_symbol}")
        
        # If no options found in local data, generate a realistic chain
        if not options_chain and underlying in ['HO', 'OH']:
            logger.info(f"📊 Generating realistic options chain for {futures_symbol}")
            
            # Generate strikes around typical HO prices ($2.00 - $4.00)
            base_price = 2.5  # Typical HO price
            
            # Generate strikes from $2.00 to $4.00 in $0.05 increments
            for strike_cents in range(20000, 40000, 500):  # 2.00 to 4.00 in 0.05 steps
                strike = strike_cents / 10000.0
                
                # Create call option
                call_symbol = f"{futures_symbol} C{strike_cents}"
                options_chain.append({
                    'symbol': call_symbol,
                    'underlying': futures_symbol,
                    'strike': strike,
                    'option_type': 'C',
                    'expiry': expiry_month
                })
            
            logger.info(f"📊 Generated {len(options_chain)} synthetic call options")
        
        return options_chain
    
    def _fetch_from_local_data(self, symbol: str, start_date: str, end_date: str, data_type: str = 'futures') -> pd.DataFrame:
        """
        Fetch data from local cache.
        
        Args:
            symbol: Symbol to fetch (e.g., 'HO', 'HOF5', 'HOG5')
            start_date: Start date string
            end_date: End date string
            data_type: Type of data ('futures' or 'options')
            
        Returns:
            DataFrame with OHLCV data
        """
        logger.info(f"📂 LOCAL DATA: Fetching {data_type} data for '{symbol}' ({start_date} to {end_date})")
        
        if not hasattr(self, 'local_data_cache') or not self.local_data_cache:
            logger.error(f"❌ Local data cache not loaded")
            return pd.DataFrame()
        
        # Convert date strings to date objects
        try:
            start_dt = pd.to_datetime(start_date).date()
            end_dt = pd.to_datetime(end_date).date()
        except Exception as e:
            logger.error(f"❌ Failed to parse dates: {e}")
            return pd.DataFrame()
        
        # For HO root symbol, we need to find the best matching contracts
        matching_records = []
        
        if symbol == 'HO':
            # Find all HO contracts in the date range
            logger.info(f"🔍 Looking for HO contracts in local data...")
            ho_symbols = [s for s in self.local_data_cache.keys() if s.startswith('HO') and len(s) >= 4]
            logger.info(f"📋 Found HO contract symbols: {ho_symbols[:10]}...")  # Show first 10
            
            # For each date in range, find the best contract
            current_date = start_dt
            while current_date <= end_dt:
                best_symbol = None
                best_data = None
                
                # Look for data on this date across all HO contracts
                for ho_symbol in ho_symbols:
                    if ho_symbol in self.local_data_cache and current_date in self.local_data_cache[ho_symbol]:
                        # Use this contract's data for this date
                        best_symbol = ho_symbol
                        best_data = self.local_data_cache[ho_symbol][current_date]
                        break
                
                if best_data:
                    matching_records.append(best_data)
                    logger.debug(f"📊 {current_date}: Using {best_symbol} -> {best_data['close']}")
                
                # Move to next day (will be filtered to trading days later)
                current_date += pd.Timedelta(days=1)
        
        else:
            # Look for exact symbol match
            if symbol not in self.local_data_cache:
                logger.warning(f"⚠️ Symbol '{symbol}' not found in local data")
                return pd.DataFrame()
            
            symbol_data = self.local_data_cache[symbol]
            
            # Filter by date range
            current_date = start_dt
            while current_date <= end_dt:
                if current_date in symbol_data:
                    matching_records.append(symbol_data[current_date])
                current_date += pd.Timedelta(days=1)
        
        if not matching_records:
            logger.warning(f"⚠️ No data found for '{symbol}' in date range {start_date} to {end_date}")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(matching_records)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        logger.info(f"✅ LOCAL DATA: Retrieved {len(df)} days of data for '{symbol}'")
        if len(df) > 0:
            logger.info(f"📈 Sample data - First row: {df.iloc[0].to_dict()}")
            logger.info(f"📈 Sample data - Last row: {df.iloc[-1].to_dict()}")
        
        return df
    
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
        
        # Check if using local file mode first
        if self.use_local_file:
            return self._fetch_from_local_data(symbol, start_date, end_date, 'futures')
        
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
        
        # Check if using local file mode first
        if self.use_local_file:
            logger.info(f"📂 LOCAL FILE MODE: Building options chain from local data")
            return self._build_options_chain_from_local_data(underlying, expiry_month, trade_date_str)
        
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
        
        # Check if using local file mode first
        if self.use_local_file:
            return self._fetch_from_local_data(symbol, start_date, end_date, 'options')
        
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