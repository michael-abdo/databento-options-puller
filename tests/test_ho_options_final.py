#!/usr/bin/env python3
"""
Test HO options using parent symbology and definition schema
"""

import databento as db
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()
client = db.Historical(os.getenv('DATABENTO_API_KEY'))

print("Testing HO options using various approaches...\n")

# Test 1: Try parent symbols for HO options
print("Test 1: Parent symbols for HO options")
parent_symbols = [
    'HO.OPT',    # Standard format
    'OHO.OPT',   # With O prefix like Gold (OG.OPT)
    'OH.OPT',    # Alternative
    'LO.OPT',    # Alternative ticker sometimes used
]

for symbol in parent_symbols:
    print(f"\nTrying parent symbol: {symbol}")
    try:
        data = client.timeseries.get_range(
            dataset='GLBX.MDP3',
            schema='definition',
            symbols=symbol,
            stype_in='parent',
            start='2021-12-01',
            end='2021-12-02'
        )
        df = data.to_df()
        print(f"  ✓ Got {len(df)} definitions")
        if len(df) > 0:
            print(f"  Sample symbols: {df['symbol'].head().tolist()}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

# Test 2: Get ALL definitions and search for HO options
print("\n\nTest 2: Get ALL symbols and filter for HO options")
try:
    # Get all definitions for the date
    print("Fetching all instrument definitions...")
    definitions = client.timeseries.get_range(
        dataset='GLBX.MDP3',
        schema='definition',
        symbols='ALL_SYMBOLS',
        start='2021-12-01',
        end='2021-12-01T01:00:00',  # Just 1 hour of definitions
        limit=50000  # Get more definitions
    )
    df = definitions.to_df()
    print(f"Got {len(df)} total definitions")
    
    if len(df) > 0 and 'symbol' in df.columns:
        # Search for HO-related options
        ho_symbols = df[df['symbol'].str.contains('HO', na=False)]
        print(f"\nFound {len(ho_symbols)} HO-related symbols")
        
        if len(ho_symbols) > 0:
            # Filter for options (space followed by C or P)
            ho_options = ho_symbols[ho_symbols['symbol'].str.contains(' C| P', regex=True, na=False)]
            print(f"Found {len(ho_options)} HO option contracts")
            
            if len(ho_options) > 0:
                print("\nSample HO options:")
                cols = ['symbol', 'instrument_class', 'strike_price']
                available_cols = [c for c in cols if c in ho_options.columns]
                print(ho_options[available_cols].head(20))
                
                # Test fetching price for first option
                first_option = ho_options.iloc[0]['symbol']
                print(f"\n\nTesting price fetch for: {first_option}")
                
                price_data = client.timeseries.get_range(
                    dataset='GLBX.MDP3',
                    schema='ohlcv-1d',
                    symbols=first_option,
                    start='2021-12-01',
                    end='2021-12-02'
                )
                price_df = price_data.to_df()
                if len(price_df) > 0:
                    print(f"✓ Got price data!")
                    print(price_df)
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Try statistics schema to find traded options
print("\n\nTest 3: Using statistics schema to find traded options")
try:
    stats = client.timeseries.get_range(
        dataset='GLBX.MDP3',
        schema='statistics',
        symbols='ALL_SYMBOLS',
        start='2021-12-01',
        end='2021-12-01T01:00:00',
        limit=10000
    )
    stats_df = stats.to_df()
    print(f"Got {len(stats_df)} statistics records")
    
    if len(stats_df) > 0 and 'symbol' in stats_df.columns:
        ho_stats = stats_df[stats_df['symbol'].str.contains('HO', na=False)]
        print(f"Found {len(ho_stats)} HO-related statistics")
        
        if len(ho_stats) > 0:
            ho_option_stats = ho_stats[ho_stats['symbol'].str.contains(' C| P', regex=True, na=False)]
            print(f"Found {len(ho_option_stats)} HO option statistics")
            
            if len(ho_option_stats) > 0:
                print("\nHO options with statistics:")
                print(ho_option_stats[['symbol', 'stat_type', 'value']].head(20))
                
except Exception as e:
    print(f"Statistics error: {e}")