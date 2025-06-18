#!/usr/bin/env python3
"""
Test final output generation with real data
"""

import databento as db
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()
client = db.Historical(os.getenv('DATABENTO_API_KEY'))

print("Testing final output data...")

# Get futures data for Dec 2021
try:
    futures_data = client.timeseries.get_range(
        dataset='GLBX.MDP3',
        schema='ohlcv-1d',
        symbols='HO.c.0',
        stype_in='continuous',
        start='2021-12-01',
        end='2021-12-10'
    )
    futures_df = futures_data.to_df()
    print(f"\nFutures data (HO.c.0):")
    print(futures_df[['close']].head())
    
    # Get option data for OHG2 C24500
    option_data = client.timeseries.get_range(
        dataset='GLBX.MDP3',
        schema='ohlcv-1d',
        symbols='OHG2 C24500',
        start='2022-01-05',
        end='2022-01-15'
    )
    option_df = option_data.to_df()
    print(f"\nOption data (OHG2 C24500):")
    print(option_df[['symbol', 'close']].head())
    
except Exception as e:
    print(f"Error: {e}")