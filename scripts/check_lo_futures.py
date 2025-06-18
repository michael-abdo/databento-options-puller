#!/usr/bin/env python3
"""
Check LO futures symbols (alternative heating oil symbol)
"""

import databento as db
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()
client = db.Historical(os.getenv('DATABENTO_API_KEY'))

print("Checking LO futures definitions...")

# Get LO futures definitions
try:
    definitions = client.timeseries.get_range(
        dataset='GLBX.MDP3',
        schema='definition',
        symbols='LO.FUT',
        stype_in='parent',
        start='2021-12-01',
        end='2021-12-02'
    )
    df = definitions.to_df()
    print(f"Got {len(df)} LO futures definitions")
    
    if len(df) > 0:
        # Show Dec 2021 - Mar 2022 contracts
        df['expiration'] = pd.to_datetime(df['expiration'])
        target_contracts = df[
            (df['expiration'] >= '2021-12-01') & 
            (df['expiration'] <= '2022-03-31')
        ]
        
        print("\nLO futures contracts (Dec 2021 - Mar 2022):")
        print(target_contracts[['symbol', 'expiration']].sort_values('expiration'))
        
        # Test fetching data for these contracts
        for symbol in target_contracts['symbol'].head(5):
            print(f"\nTesting {symbol}:")
            try:
                data = client.timeseries.get_range(
                    dataset='GLBX.MDP3',
                    schema='ohlcv-1d',
                    symbols=symbol,
                    start='2021-12-01',
                    end='2021-12-02'
                )
                price_df = data.to_df()
                if len(price_df) > 0:
                    print(f"  ✓ Close: ${price_df.iloc[0]['close']:.4f}")
                else:
                    print(f"  ✗ No price data")
            except:
                print(f"  ✗ Error")
                
except Exception as e:
    print(f"Error: {e}")

# Also check if there's a continuous contract
print("\n\nChecking continuous contracts...")
continuous_symbols = ['LO.c.0', 'LO.C.0', 'HO.c.0', 'HO.C.0']
for symbol in continuous_symbols:
    print(f"\nTrying: {symbol}")
    try:
        data = client.timeseries.get_range(
            dataset='GLBX.MDP3',
            schema='ohlcv-1d',
            symbols=symbol,
            stype_in='continuous',
            start='2021-12-01',
            end='2021-12-02'
        )
        df = data.to_df()
        if len(df) > 0:
            print(f"  ✓ SUCCESS! Close: ${df.iloc[0]['close']:.4f}")
            print(f"  Symbol: {df.iloc[0]['symbol']}")
    except Exception as e:
        print(f"  ✗ Error: {e}")