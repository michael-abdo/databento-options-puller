#!/usr/bin/env python3
"""
Test different option symbol formats for HO
"""

import databento as db

def test_option_formats():
    """Test different option symbol formats"""
    api_key = "db-3gVxurfuD5jfS6uJB8Df36YUrg7pv"
    client = db.Historical(api_key)
    
    print("🎯 Testing DIFFERENT option symbol formats...")
    print("=" * 60)
    
    # Use working HO contract
    underlying = "HOF2"
    test_date_start = "2021-12-15"
    test_date_end = "2021-12-16"
    
    print(f"📊 Testing options on {underlying} ({test_date_start})")
    
    # Try different option symbol formats
    # Strike price: trying 275 (which could be $2.75)
    
    format_tests = [
        # Format 1: Standard CME format
        "HOF2   C00275",  # CME standard with padding
        "HOF2   P00275",  # Put version
        
        # Format 2: Compact format  
        "HOF2C275",
        "HOF2P275",
        
        # Format 3: With decimal
        "HOF2 C2.75",
        "HOF2 P2.75",
        
        # Format 4: Different strike representations
        "HOF2 C275",
        "HOF2 C02750",
        "HOF2 C027500",
        
        # Format 5: Try the original target format anyway
        "HOF2 C27800",
        "HOF2 C24500",
        
        # Format 6: Different underlying formats
        "HO   F2C00275",
        "HO F2 C275",
        
        # Format 7: Root symbol approach
        "HO C275F2",
        "HO C275-F2",
    ]
    
    print(f"   Testing {len(format_tests)} different formats...")
    
    working_formats = []
    
    for i, symbol in enumerate(format_tests):
        try:
            print(f"   {i+1:2d}. Testing '{symbol}'...", end=" ")
            data = client.timeseries.get_range(
                dataset='GLBX.MDP3',
                symbols=[symbol],
                schema='ohlcv-1d',
                start=test_date_start,
                end=test_date_end
            )
            
            df = data.to_df()
            if len(df) > 0:
                print(f"✅ SUCCESS! Found {len(df)} days")
                sample_row = df.iloc[0]
                print(f"        Price=${sample_row['close']:.4f}")
                working_formats.append(symbol)
            else:
                print("❌ No data")
                
        except Exception as e:
            if "did not resolve" in str(e):
                print("❌ No symbol")
            else:
                print(f"❌ Error: {e}")
    
    print(f"\n📋 WORKING OPTION FORMATS: {len(working_formats)}")
    for fmt in working_formats:
        print(f"   ✅ '{fmt}'")
    
    if not working_formats:
        print("\n🔍 Let's try to find ANY option symbols...")
        print("Testing if ANY options exist in the dataset...")
        
        # Try some common option formats for different underlyings
        common_options = [
            "ES   C04500",  # S&P 500 
            "ES00 C04500",
            "SPY  C00400", # SPY ETF
            "QQQ  C00300", # QQQ ETF
        ]
        
        for symbol in common_options:
            try:
                print(f"   Testing {symbol}...", end=" ")
                data = client.timeseries.get_range(
                    dataset='GLBX.MDP3',
                    symbols=[symbol],
                    schema='ohlcv-1d',
                    start=test_date_start,
                    end=test_date_end
                )
                df = data.to_df()
                if len(df) > 0:
                    print("✅ OPTIONS EXIST!")
                    break
                else:
                    print("❌")
            except:
                print("❌")
    
    return working_formats

if __name__ == "__main__":
    working = test_option_formats()