#!/usr/bin/env python3
"""
Test HO options with CME format based on ES example
"""

import databento as db
from dotenv import load_dotenv
import os

load_dotenv()
client = db.Historical(os.getenv('DATABENTO_API_KEY'))

print("Testing HO options with CME format...")
print("Based on format: ROOT+MONTH+YEAR OPTIONTYPE+STRIKE")
print("Example: ESM4 C2950 = ES June 2024 Call $2950\n")

# For HO Feb 2022 options, following the same format
# Strike prices in cents per gallon (multiply by 100)
test_symbols = [
    # Format: HOG2 C+strike_in_cents
    'HOG2 C225',   # $2.25 call
    'HOG2 C250',   # $2.50 call  
    'HOG2 C275',   # $2.75 call
    'HOG2 C300',   # $3.00 call
    'HOG2 C325',   # $3.25 call
    # Try with leading zeros
    'HOG2 C0225',
    'HOG2 C0250',
    'HOG2 C0275',
    'HOG2 C0300',
    'HOG2 C0325',
    # Try put options too
    'HOG2 P225',
    'HOG2 P250',
]

for symbol in test_symbols:
    print(f"Testing: {symbol}")
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
            print(f"  Close price: ${df.iloc[0]['close']}")
            print(f"  Symbol: {df.iloc[0]['symbol']}")
        else:
            print(f"  ✗ No data")
    except Exception as e:
        if "No data found" not in str(e):
            print(f"  ✗ Error: {e}")

# Also try getting all HO instruments using definition schema
print("\n\nTrying to get HO option definitions...")
try:
    # Get definitions for a specific date
    definitions = client.timeseries.get_range(
        dataset='GLBX.MDP3',
        schema='definition',
        symbols='HO',  # Root symbol
        stype_in='continuous',
        start='2021-12-01T00:00:00',
        end='2021-12-01T00:01:00',  # Just 1 minute to get snapshot
        limit=1000
    )
    df = definitions.to_df()
    print(f"Got {len(df)} definitions")
    
    if len(df) > 0 and 'symbol' in df.columns:
        # Filter for options (containing C or P)
        options = df[df['symbol'].str.contains(' C| P', na=False)]
        print(f"Found {len(options)} option contracts")
        
        if len(options) > 0:
            print("\nSample options:")
            cols = ['symbol', 'instrument_class', 'strike_price', 'expiration']
            available_cols = [c for c in cols if c in options.columns]
            print(options[available_cols].head(10))
            
except Exception as e:
    print(f"Definition error: {e}")