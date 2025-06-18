#!/usr/bin/env python3
"""
Test direct options data access
"""

import databento as db
from dotenv import load_dotenv
import os

load_dotenv()
client = db.Historical(os.getenv('DATABENTO_API_KEY'))

print("Testing direct access to options data...\n")

# Based on CME options format, let's try some potential symbols
# CME options on futures typically use format like: HOG2 2250C (Feb 2022 $2.25 Call)

potential_symbols = [
    # Try CME-style options symbols
    'HOG2 2250C',  # Feb 2022 $2.25 Call
    'HOG2 2500C',  # Feb 2022 $2.50 Call
    'HOG2 2750C',  # Feb 2022 $2.75 Call
    'HOG2 3000C',  # Feb 2022 $3.00 Call
    'HOG2 3250C',  # Feb 2022 $3.25 Call
    # Try without spaces
    'HOG22250C',
    'HOG22500C',
    'HOG22750C',
    # Try with different separators
    'HOG2-2250C',
    'HOG2_2250C',
    # Try futures to confirm format
    'HOF2',  # Jan 2022
    'HOG2',  # Feb 2022
    'HOH2',  # Mar 2022
]

for symbol in potential_symbols:
    print(f"Testing symbol: {symbol}")
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
            print(f"  Data: {df}")
        else:
            print(f"  ✗ No data")
    except Exception as e:
        print(f"  ✗ Error: {e}")

# Also test getting trades to see actual symbols
print("\n\nTrying to get actual traded symbols...")
try:
    # Get trades for HOG2 to see related symbols
    trades = client.timeseries.get_range(
        dataset='GLBX.MDP3',
        schema='trades',
        symbols='HOG2',
        start='2021-12-01T12:00:00',
        end='2021-12-01T12:05:00',
        limit=100
    )
    trades_df = trades.to_df()
    print(f"Got {len(trades_df)} trades")
    if len(trades_df) > 0:
        print("Unique symbols in trades:")
        print(trades_df['symbol'].unique())
except Exception as e:
    print(f"Trades error: {e}")