#!/usr/bin/env python3
"""
Test Databento API symbols for NY Harbor ULSD
"""

import databento as db
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()
client = db.Historical(os.getenv('DATABENTO_API_KEY'))

print("Testing Databento symbols for NY Harbor ULSD...")

# Test different symbol formats
test_symbols = [
    'HO',           # Parent symbol
    'HOZ1',         # December 2021
    'HOZ21',        # December 2021 (alternative)
    'HO.FUT',       # Futures designation
    'HO.OPT',       # Options designation
    '@HO',          # Alternative format
]

# Try each symbol
for symbol in test_symbols:
    print(f"\nTesting symbol: {symbol}")
    try:
        # Try to get data
        data = client.timeseries.get_range(
            dataset='GLBX.MDP3',
            schema='ohlcv-1d',
            symbols=symbol,
            start='2021-12-01',
            end='2021-12-02',
            stype_in='raw_symbol'
        )
        df = data.to_df()
        print(f"  Success! Got {len(df)} rows")
        if len(df) > 0:
            print(f"  Sample data: {df.head()}")
    except Exception as e:
        print(f"  Error: {e}")

# Also try getting the dataset schema
print("\n\nGetting dataset schema...")
try:
    schema = client.metadata.get_dataset_schema(dataset='GLBX.MDP3')
    print(f"Schema info: {schema}")
except Exception as e:
    print(f"Schema error: {e}")

# Try listing available symbols
print("\n\nTrying to list available symbols...")
try:
    # Get conditions for the dataset
    conditions = client.metadata.get_dataset_condition(dataset='GLBX.MDP3')
    print(f"Dataset conditions: {conditions}")
except Exception as e:
    print(f"Conditions error: {e}")