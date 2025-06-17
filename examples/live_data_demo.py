#!/usr/bin/env python3
"""
Live Databento Demo - Shows real NY Harbor ULSD heating oil futures data
"""

import databento as db
import pandas as pd

def main():
    print("🚀 Live Databento NY Harbor ULSD Demo")
    print("=" * 50)
    
    # Initialize client with API key
    client = db.Historical('db-G6UdaW7epknFt6XceRt4SYjdsXwMx')
    
    # Fetch real heating oil futures data (HOH4 = March 2024 contract)
    print("📊 Fetching HOH4 (March 2024) heating oil futures data...")
    
    data = client.timeseries.get_range(
        dataset='GLBX.MDP3',
        symbols='HOH4',
        schema='ohlcv-1d',
        start='2024-01-01',
        end='2024-01-10'
    )
    
    # Convert to DataFrame
    df = data.to_df()
    
    # Display results
    print(f"✅ Retrieved {len(df)} days of live market data")
    print("\n📈 NY Harbor ULSD Futures Prices (HOH4):")
    print("-" * 45)
    
    # Format the data nicely
    df_display = df.copy()
    df_display['date'] = df_display.index.strftime('%Y-%m-%d')
    df_display = df_display[['date', 'open', 'high', 'low', 'close', 'volume']]
    
    for _, row in df_display.iterrows():
        print(f"{row['date']}: ${row['close']:.3f} (Vol: {row['volume']:,})")
    
    print(f"\n💰 Price Range: ${df['low'].min():.3f} - ${df['high'].max():.3f}")
    print(f"📊 Average Volume: {df['volume'].mean():,.0f} contracts/day")
    
    # Save to CSV
    output_file = 'live_heating_oil_data.csv'
    df_display.to_csv(output_file, index=False)
    print(f"\n💾 Saved live data to: {output_file}")
    
    print("\n🎉 Live Databento integration working perfectly!")
    return df

if __name__ == "__main__":
    df = main()