#!/usr/bin/env python3
"""
Test NYMEX dataset for heating oil futures
"""

import databento as db
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()
client = db.Historical(os.getenv('DATABENTO_API_KEY'))

print("Testing NYMEX heating oil data...")

# Common NYMEX datasets
datasets_to_try = [
    'GLBX.MDP3',  # CME Globex (includes NYMEX)
    'XNYS.TRADES',  # NYSE trades
    'IFEU.IMPACT',  # ICE Europe
]

# Test each dataset
for dataset in datasets_to_try:
    print(f"\n\nTesting dataset: {dataset}")
    try:
        # Get dataset info
        print("Getting dataset range...")
        dataset_range = client.metadata.get_dataset_range(dataset=dataset)
        print(f"  Dataset range: {dataset_range}")
    except Exception as e:
        print(f"  Dataset range error: {e}")

# Try with specific symbology
print("\n\nTrying different symbology approaches...")

# Test 1: Try raw symbols
symbols_to_test = [
    'HO',  # Root
    'HOZ1',  # Dec 2021
    'HOG2',  # Feb 2022 
    'HO*',  # Wildcard
    'HO:BF',  # Back month
    'HO_continuous',  # Continuous
]

for symbol in symbols_to_test:
    print(f"\nTesting symbol: {symbol}")
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
            print(f"  Columns: {df.columns.tolist()}")
            print(f"  First row:\n{df.iloc[0]}")
    except Exception as e:
        print(f"  Error: {e}")