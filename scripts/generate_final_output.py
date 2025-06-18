#!/usr/bin/env python3
"""
Generate final output CSV with real data from Databento
"""

import databento as db
from dotenv import load_dotenv
import os
import pandas as pd
from datetime import datetime, timedelta

load_dotenv()
client = db.Historical(os.getenv('DATABENTO_API_KEY'))

# Define date range
start_date = '2021-12-02'
end_date = '2022-03-09'

# Generate trading days
dates = []
current = datetime(2021, 12, 2)
end = datetime(2022, 3, 9)

while current <= end:
    # Skip weekends
    if current.weekday() < 5:  # Monday = 0, Friday = 4
        dates.append(current)
    current += timedelta(days=1)

print(f"Generating output for {len(dates)} trading days...")

# Create output dataframe
df = pd.DataFrame()
df['timestamp'] = [d.strftime('%-m/%-d/%y') for d in dates]

# Initialize columns
df['Futures_Price'] = ''
df['OHF2 C27800'] = ''
df['OHG2 C24500'] = ''
df['OHH2 C27000'] = ''
df['OHJ2 C30200'] = ''
df['OHK2 C35000'] = ''

# Fetch futures data in batch
print("\nFetching futures data...")
try:
    futures_data = client.timeseries.get_range(
        dataset='GLBX.MDP3',
        schema='ohlcv-1d',
        symbols='HO.c.0',
        stype_in='continuous',
        start=start_date,
        end=end_date
    )
    futures_df = futures_data.to_df()
    futures_df['date'] = pd.to_datetime(futures_df.index).date
    print(f"Got {len(futures_df)} days of futures data")
    
    # Map futures prices to dates
    for idx, date in enumerate(dates):
        date_only = date.date()
        matching_rows = futures_df[futures_df['date'] == date_only]
        if len(matching_rows) > 0:
            price = matching_rows.iloc[0]['close']
            # Format price without trailing zeros
            price_str = f"{price:.2f}".rstrip('0').rstrip('.')
            df.loc[idx, 'Futures_Price'] = price_str
except Exception as e:
    print(f"Error fetching futures: {e}")

# Define option contracts and their active periods
options = [
    {
        'symbol': 'OHF2 C27800',
        'start': '2021-12-02',
        'end': '2021-12-28'
    },
    {
        'symbol': 'OHG2 C24500',
        'start': '2021-12-05',
        'end': '2022-01-26'
    },
    {
        'symbol': 'OHH2 C27000',
        'start': '2022-01-02',
        'end': '2022-02-23'
    },
    {
        'symbol': 'OHJ2 C30200',
        'start': '2022-02-01',
        'end': '2022-03-09'
    },
    {
        'symbol': 'OHK2 C35000',
        'start': '2022-03-03',
        'end': '2022-03-09'
    }
]

# Fetch option data
for option in options:
    symbol = option['symbol']
    print(f"\nFetching {symbol}...")
    
    try:
        option_data = client.timeseries.get_range(
            dataset='GLBX.MDP3',
            schema='ohlcv-1d',
            symbols=symbol,
            start=option['start'],
            end=option['end']
        )
        option_df = option_data.to_df()
        option_df['date'] = pd.to_datetime(option_df.index).date
        print(f"Got {len(option_df)} days of data")
        
        # Map option prices to dates
        for idx, date in enumerate(dates):
            date_only = date.date()
            matching_rows = option_df[option_df['date'] == date_only]
            if len(matching_rows) > 0:
                price = matching_rows.iloc[0]['close']
                # Format price without trailing zeros
                price_str = f"{price:.2f}".rstrip('0').rstrip('.')
                df.loc[idx, symbol] = price_str
                
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")

# Save output
output_file = '/home/Mike/whiskey/option-data-repo/output/final_output.csv'
df.to_csv(output_file, index=False)
print(f"\n✅ Saved to {output_file}")
print(f"Shape: {df.shape}")

# Show first few rows
print("\nFirst 10 rows:")
print(df.head(10))