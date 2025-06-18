#!/usr/bin/env python3
"""
Test HO options chains to see if we can get option data
"""

import databento as db

def test_ho_options():
    """Test HO options chains"""
    api_key = "db-3gVxurfuD5jfS6uJB8Df36YUrg7pv"
    client = db.Historical(api_key)
    
    print("🎯 Testing HO OPTIONS chains...")
    print("=" * 60)
    
    # Working HO contracts from previous test
    working_contracts = [
        ('HOF2', '2021-12-15', '2021-12-16'),  # January delivery
        ('HOH2', '2022-02-15', '2022-02-16'),  # March delivery
    ]
    
    for contract, start_date, end_date in working_contracts:
        print(f"\n📊 Testing options on {contract} ({start_date})...")
        
        # Try to find option symbols based on the contract
        option_symbols_to_test = []
        
        # Generate potential option symbols based on target strikes
        # Target file has: C27800, C24500, C27000, C30200, C35000
        strikes = [27800, 24500, 27000, 30200, 35000]
        
        for strike in strikes:
            # Format: HOF2 C27800 (matches target format but with HO instead of OH)
            option_symbol = f"{contract} C{strike}"
            option_symbols_to_test.append(option_symbol)
        
        print(f"   Testing {len(option_symbols_to_test)} option symbols...")
        
        working_options = []
        
        for option_symbol in option_symbols_to_test:
            try:
                print(f"   📈 Testing {option_symbol}...", end=" ")
                data = client.timeseries.get_range(
                    dataset='GLBX.MDP3',
                    symbols=[option_symbol],
                    schema='ohlcv-1d',
                    start=start_date,
                    end=end_date
                )
                
                df = data.to_df()
                if len(df) > 0:
                    print(f"✅ SUCCESS! Found {len(df)} days")
                    sample_row = df.iloc[0]
                    print(f"      Option Price=${sample_row['close']:.3f}")
                    working_options.append(option_symbol)
                else:
                    print("❌ No data")
                    
            except Exception as e:
                if "did not resolve" in str(e):
                    print("❌ No symbol")
                else:
                    print(f"❌ Error: {e}")
        
        print(f"   📋 Working options for {contract}: {len(working_options)}")
        for opt in working_options:
            print(f"      - {opt}")
        
        if working_options:
            print(f"   ✅ {contract} has working options!")
        else:
            print(f"   ❌ {contract} has no working options")
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY:")
    print("HO futures data exists ✅")
    print("HO options data - testing results above")

if __name__ == "__main__":
    test_ho_options()