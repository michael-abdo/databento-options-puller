#!/usr/bin/env python3
"""
Search for CME HO options using different approaches
"""

import databento as db
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()
client = db.Historical(os.getenv('DATABENTO_API_KEY'))

print("Searching for HO options data...\n")

# Test 1: Try getting all symbols for a date
print("Test 1: Getting all symbols on 2021-12-01...")
try:
    # Get all instruments
    all_data = client.timeseries.get_range(
        dataset='GLBX.MDP3',
        schema='definition',
        start='2021-12-01',
        end='2021-12-02',
        limit=1000  # Limit to first 1000 instruments
    )
    df = all_data.to_df()
    print(f"Got {len(df)} instrument definitions")
    
    # Filter for HO related
    if 'symbol' in df.columns:
        ho_instruments = df[df['symbol'].str.contains('HO', na=False)]
        print(f"Found {len(ho_instruments)} HO-related instruments")
        
        if len(ho_instruments) > 0:
            print("\nHO instrument types:")
            if 'instrument_class' in ho_instruments.columns:
                print(ho_instruments['instrument_class'].value_counts())
            
            # Show some HO instruments
            print("\nSample HO instruments:")
            cols = ['symbol', 'instrument_class', 'strike_price', 'expiration']
            available_cols = [c for c in cols if c in ho_instruments.columns]
            print(ho_instruments[available_cols].head(20))
            
            # Check for options
            if 'instrument_class' in ho_instruments.columns:
                ho_options = ho_instruments[ho_instruments['instrument_class'].isin(['C', 'P'])]
                print(f"\nFound {len(ho_options)} HO options (calls and puts)")
                
                if len(ho_options) > 0:
                    print("\nSample HO options:")
                    print(ho_options[available_cols].head(10))
                    
except Exception as e:
    print(f"Error in Test 1: {e}")

# Test 2: Try symbology resolution
print("\n\nTest 2: Trying symbology resolution...")
try:
    # Use symbology endpoint
    result = client.symbology.resolve(
        dataset='GLBX.MDP3',
        symbols=['HO'],
        stype_in='continuous',
        stype_out='raw_symbol',
        start='2021-12-01',
        end='2021-12-02'
    )
    print(f"Symbology result: {result}")
except Exception as e:
    print(f"Symbology error: {e}")

# Test 3: Check metadata
print("\n\nTest 3: Checking dataset metadata...")
try:
    # Get dataset fields
    fields = client.metadata.get_fields(
        dataset='GLBX.MDP3',
        schema='definition'
    )
    print(f"Definition schema fields: {fields}")
except Exception as e:
    print(f"Metadata error: {e}")