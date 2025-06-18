#!/usr/bin/env python3
"""
Test continuous contract for HO futures
"""

import databento as db
from dotenv import load_dotenv
import os

load_dotenv()
client = db.Historical(os.getenv('DATABENTO_API_KEY'))

print("Testing HO continuous contract...")

try:
    data = client.timeseries.get_range(
        dataset='GLBX.MDP3',
        schema='ohlcv-1d',
        symbols='HO.c.0',
        stype_in='continuous',
        start='2021-12-01',
        end='2021-12-10'
    )
    df = data.to_df()
    print(f"Got {len(df)} rows")
    print("\nFirst few rows:")
    print(df[['symbol', 'close']].head())
    
    # Check what specific contract it maps to
    print("\nActual contracts mapped:")
    print(df['symbol'].unique())
    
except Exception as e:
    print(f"Error: {e}")