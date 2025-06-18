#!/usr/bin/env python3
"""
Test the exact OH symbols from final_output.csv
"""

import databento as db
from datetime import datetime, timedelta

def test_exact_oh_symbols():
    """Test the exact OH symbols from target file"""
    api_key = "db-3gVxurfuD5jfS6uJB8Df36YUrg7pv"
    client = db.Historical(api_key)
    
    print("🎯 Testing EXACT OH symbols from final_output.csv...")
    print("=" * 60)
    
    # Exact symbols from the target file
    target_symbols = ['OHF2', 'OHG2', 'OHH2', 'OHJ2', 'OHK2']
    
    # Test date range within the target range (need start < end)
    start_date = '2021-12-15'
    end_date = '2021-12-16'  # Next day to avoid API error
    
    print(f"📅 Testing range: {start_date} to {end_date}")
    print(f"🔍 Testing symbols: {target_symbols}")
    
    working_symbols = []
    
    for symbol in target_symbols:
        try:
            print(f"\n📊 Testing {symbol}...")
            data = client.timeseries.get_range(
                dataset='GLBX.MDP3',
                symbols=[symbol],
                schema='ohlcv-1d',
                start=start_date,
                end=end_date
            )
            
            df = data.to_df()
            if len(df) > 0:
                print(f"✅ {symbol}: SUCCESS! Found {len(df)} days of data")
                sample_row = df.iloc[0]
                print(f"   Close=${sample_row['close']:.2f}, Volume={sample_row.get('volume', 'N/A')}")
                working_symbols.append(symbol)
            else:
                print(f"⚠️  {symbol}: No data returned")
                
        except Exception as e:
            if "did not resolve" in str(e):
                print(f"❌ {symbol}: Symbol does not exist - {e}")
            else:
                print(f"❌ {symbol}: Error - {e}")
    
    print("\n" + "=" * 60)
    print("📋 RESULTS:")
    print(f"✅ Working OH symbols: {len(working_symbols)}")
    for symbol in working_symbols:
        print(f"   - {symbol}")
    
    if not working_symbols:
        print("\n🔍 Let's try alternative formats...")
        # Try with different exchange prefixes
        alt_formats = []
        for base in ['OH', 'HO']:
            for month in ['F', 'G', 'H', 'J', 'K']:
                for year in ['2', '22', '1', '21']:
                    alt_formats.append(f"{base}{month}{year}")
        
        print(f"Testing {len(alt_formats)} alternative formats...")
        for symbol in alt_formats[:10]:  # Test first 10
            try:
                print(f"Testing {symbol}...", end=" ")
                data = client.timeseries.get_range(
                    dataset='GLBX.MDP3',
                    symbols=[symbol],
                    schema='ohlcv-1d',
                    start=start_date,
                    end=end_date
                )
                df = data.to_df()
                if len(df) > 0:
                    print(f"✅ WORKS!")
                    working_symbols.append(symbol)
                    break
                else:
                    print("❌")
            except:
                print("❌")
    
    return working_symbols

if __name__ == "__main__":
    working_symbols = test_exact_oh_symbols()