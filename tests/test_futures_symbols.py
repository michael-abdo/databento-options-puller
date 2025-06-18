#!/usr/bin/env python3
"""
Test different futures symbol formats
"""

import databento as db
from dotenv import load_dotenv
import os

load_dotenv()
client = db.Historical(os.getenv('DATABENTO_API_KEY'))

print("Testing futures symbols for Dec 2021...")

futures_symbols = [
    'HOZ1',   # Dec 2021 (1 digit year)
    'HOZ21',  # Dec 2021 (2 digit year)
    'HOZ2021', # Dec 2021 (4 digit year)
    'HOZ11',  # Alternative for 2021
    'HOZ12',  # Alternative for 2022
    'OHZ1',   # With OH prefix
    'OHZ21',  # With OH prefix
]

for symbol in futures_symbols:
    print(f"\nTesting: {symbol}")
    try:
        data = client.timeseries.get_range(
            dataset='GLBX.MDP3',
            schema='ohlcv-1d',
            symbols=symbol,
            start='2021-12-01',
            end='2021-12-02'
        )
        df = data.to_df()
        if len(df) > 0:
            print(f"  ✓ SUCCESS! Got {len(df)} rows")
            print(f"  Close price: ${df.iloc[0]['close']:.4f}")
            print(f"  Symbol in data: {df.iloc[0]['symbol']}")
        else:
            print(f"  ✗ No data")
    except Exception as e:
        if "No data found" not in str(e):
            print(f"  ✗ Error: {e}")