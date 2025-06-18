#!/usr/bin/env python3
"""
Test getting HO options using correct parent symbol format
"""

import databento as db
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()
client = db.Historical(os.getenv('DATABENTO_API_KEY'))

print("Getting HO options definitions...")

try:
    # Get all HO options definitions
    definitions = client.timeseries.get_range(
        dataset='GLBX.MDP3',
        schema='definition',
        symbols='HO.OPT',  # Correct parent symbol for options
        stype_in='parent',
        start='2021-12-01',
        end='2021-12-02'
    )
    df = definitions.to_df()
    print(f"Got {len(df)} option definitions")
    
    if len(df) > 0:
        # Show available columns
        print(f"\nColumns: {df.columns.tolist()}")
        
        # Filter for call options expiring in Feb 2022
        if 'instrument_class' in df.columns and 'expiration' in df.columns:
            # Convert expiration to datetime for filtering
            df['expiration'] = pd.to_datetime(df['expiration'])
            
            # Filter for Feb 2022 expiry calls
            feb_2022_calls = df[
                (df['instrument_class'] == 'C') &  # Calls
                (df['expiration'].dt.year == 2022) &
                (df['expiration'].dt.month == 2)
            ]
            
            print(f"\nFound {len(feb_2022_calls)} Feb 2022 call options")
            
            if len(feb_2022_calls) > 0:
                # Sort by strike price
                feb_2022_calls = feb_2022_calls.sort_values('strike_price')
                
                # Show some options
                print("\nFeb 2022 call options (sorted by strike):")
                cols_to_show = ['symbol', 'strike_price', 'expiration']
                print(feb_2022_calls[cols_to_show].head(10))
                
                # Now try to get price data for one of these options
                test_symbol = feb_2022_calls.iloc[0]['symbol']
                print(f"\n\nTesting price data for: {test_symbol}")
                
                price_data = client.timeseries.get_range(
                    dataset='GLBX.MDP3',
                    schema='ohlcv-1d',
                    symbols=test_symbol,
                    start='2021-12-01',
                    end='2021-12-02'
                )
                price_df = price_data.to_df()
                print(f"Got {len(price_df)} price records")
                if len(price_df) > 0:
                    print(price_df)
                    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()