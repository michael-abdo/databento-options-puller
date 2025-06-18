#!/usr/bin/env python3
"""
Test HO symbols instead of OH - HO is the correct NYMEX heating oil symbol
"""

import databento as db

def test_ho_symbols():
    """Test HO symbols (correct NYMEX heating oil)"""
    api_key = "db-3gVxurfuD5jfS6uJB8Df36YUrg7pv"
    client = db.Historical(api_key)
    
    print("🎯 Testing HO symbols (correct NYMEX heating oil)...")
    print("=" * 60)
    
    # Try HO instead of OH
    ho_symbols = ['HOF2', 'HOG2', 'HOH2', 'HOJ2', 'HOK2']
    
    # Also try other date ranges in case 2021 data doesn't exist
    date_ranges = [
        ('2021-12-15', '2021-12-16'),  # Original target
        ('2022-01-15', '2022-01-16'),  # January 2022 
        ('2022-02-15', '2022-02-16'),  # February 2022
        ('2023-12-15', '2023-12-16'),  # Recent data
        ('2024-01-15', '2024-01-16'),  # Very recent
    ]
    
    working_combinations = []
    
    for start_date, end_date in date_ranges:
        print(f"\n📅 Testing date range: {start_date} to {end_date}")
        
        for symbol in ho_symbols:
            try:
                print(f"   📊 Testing {symbol}...", end=" ")
                data = client.timeseries.get_range(
                    dataset='GLBX.MDP3',
                    symbols=[symbol],
                    schema='ohlcv-1d',
                    start=start_date,
                    end=end_date
                )
                
                df = data.to_df()
                if len(df) > 0:
                    print(f"✅ SUCCESS! Found {len(df)} days")
                    sample_row = df.iloc[0]
                    print(f"      Price=${sample_row['close']:.2f}, Volume={sample_row.get('volume', 'N/A')}")
                    working_combinations.append((symbol, start_date, end_date))
                    break  # Found working symbol for this date range
                else:
                    print("❌ No data")
                    
            except Exception as e:
                if "did not resolve" in str(e):
                    print("❌ No symbol")
                else:
                    print(f"❌ Error: {e}")
        
        if working_combinations and working_combinations[-1][1] == start_date:
            print(f"   ✅ Found working symbol for {start_date}")
        else:
            print(f"   ❌ No working symbols for {start_date}")
    
    print("\n" + "=" * 60)
    print("📋 WORKING COMBINATIONS:")
    for symbol, start, end in working_combinations:
        print(f"   {symbol}: {start} to {end}")
    
    return working_combinations

if __name__ == "__main__":
    working = test_ho_symbols()