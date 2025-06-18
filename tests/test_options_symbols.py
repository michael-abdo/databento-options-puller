#!/usr/bin/env python3
"""
Test Databento options symbols for heating oil
"""

import databento as db
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()
client = db.Historical(os.getenv('DATABENTO_API_KEY'))

print("Testing heating oil options symbols...")

# Test different options symbol formats
# Based on the pattern from the requirements: "OHG2 C00325"
# This might translate to different formats in Databento

options_symbols = [
    # Try standard CME options format
    'HOG2 C3.25',  # Feb 2022 $3.25 call
    'HOG2C3.25',   # Without space
    'HOG2 325C',   # Alternative format
    'HOG2C325',    # No decimal
    'OHG2 C00325', # Original format from requirements
    'OHG2C00325',  # Without space
    # Try with proper CME format
    'HO2G C3.25',
    'HO2G 325C',
    # Try OPRA-style
    'HO 220218C00325000',  # Feb 18, 2022 $3.25 call
]

for symbol in options_symbols:
    print(f"\nTesting option symbol: {symbol}")
    try:
        data = client.timeseries.get_range(
            dataset='GLBX.MDP3',
            schema='ohlcv-1d',
            symbols=symbol,
            start='2021-12-01',
            end='2021-12-02'
        )
        df = data.to_df()
        print(f"  Got {len(df)} rows")
        if len(df) > 0:
            print(f"  Data: {df}")
    except Exception as e:
        print(f"  Error: {e}")

# Let's also try to get all instruments for a specific date
print("\n\nTrying to get all HO instruments for a date...")
try:
    # Get definition for HO futures
    definitions = client.timeseries.get_range(
        dataset='GLBX.MDP3',
        schema='definition',
        symbols='HO',
        stype_in='parent',
        start='2021-12-01',
        end='2021-12-01'
    )
    df = definitions.to_df()
    print(f"Got {len(df)} instrument definitions")
    if len(df) > 0:
        # Filter for options
        if 'instrument_class' in df.columns:
            options_df = df[df['instrument_class'] == 'C']  # Call options
            print(f"Found {len(options_df)} call options")
            if len(options_df) > 0:
                print("Sample options:")
                print(options_df[['symbol', 'strike_price', 'expiration']].head())
except Exception as e:
    print(f"Definition error: {e}")