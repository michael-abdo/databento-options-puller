#!/usr/bin/env python3
"""
Analyze OH options to understand the format and find Feb 2022 15-delta calls
"""

import databento as db
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()
client = db.Historical(os.getenv('DATABENTO_API_KEY'))

print("Analyzing OH options (NY Harbor ULSD)...\n")

# Get OH options definitions
print("Fetching OH options definitions...")
definitions = client.timeseries.get_range(
    dataset='GLBX.MDP3',
    schema='definition',
    symbols='OH.OPT',
    stype_in='parent',
    start='2021-12-01',
    end='2021-12-02'
)
df = definitions.to_df()
print(f"Got {len(df)} OH option definitions")

# Convert expiration to datetime
df['expiration'] = pd.to_datetime(df['expiration'])

# Filter for Feb 2022 call options
feb_2022_calls = df[
    (df['symbol'].str.contains(' C', na=False)) &  # Calls
    (df['expiration'].dt.year == 2022) &
    (df['expiration'].dt.month == 2)
]

print(f"\nFound {len(feb_2022_calls)} Feb 2022 call options")

if len(feb_2022_calls) > 0:
    # Extract strike prices
    feb_2022_calls['strike_value'] = feb_2022_calls['strike_price']
    feb_2022_calls = feb_2022_calls.sort_values('strike_value')
    
    print("\nFeb 2022 call options (sorted by strike):")
    print(feb_2022_calls[['symbol', 'strike_price', 'expiration']].head(20))
    
    # Show strike price range
    print(f"\nStrike price range: ${feb_2022_calls['strike_price'].min():.2f} - ${feb_2022_calls['strike_price'].max():.2f}")
    
    # Test fetching prices for a few options
    print("\n\nTesting price data for Feb 2022 calls around $2.50-$3.50 strikes...")
    
    # Filter for strikes in reasonable range (around futures price)
    target_strikes = feb_2022_calls[
        (feb_2022_calls['strike_price'] >= 2.25) & 
        (feb_2022_calls['strike_price'] <= 3.50)
    ]
    
    print(f"\nOptions in target strike range:")
    for idx, row in target_strikes.head(10).iterrows():
        symbol = row['symbol']
        strike = row['strike_price']
        print(f"\n{symbol} (Strike: ${strike:.2f})")
        
        try:
            # Get price data
            price_data = client.timeseries.get_range(
                dataset='GLBX.MDP3',
                schema='ohlcv-1d',
                symbols=symbol,
                start='2021-12-01',
                end='2021-12-03'
            )
            price_df = price_data.to_df()
            
            if len(price_df) > 0:
                print(f"  ✓ Got {len(price_df)} days of price data")
                for _, price_row in price_df.iterrows():
                    print(f"    {price_row.name.date()}: Close=${price_row['close']:.4f}, Volume={price_row['volume']}")
            else:
                print(f"  ✗ No price data")
                
        except Exception as e:
            if "No data found" not in str(e):
                print(f"  ✗ Error: {e}")

# Also check the futures symbol
print("\n\nChecking OH futures symbols...")
futures_symbols = ['OHG2', 'HOG2']
for symbol in futures_symbols:
    print(f"\nTesting futures symbol: {symbol}")
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
            print(f"  ✓ SUCCESS! Close price: ${df.iloc[0]['close']}")
    except:
        print(f"  ✗ No data")