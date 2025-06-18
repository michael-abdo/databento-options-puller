#!/usr/bin/env python3
"""
Test to find available symbols in Databento GLBX.MDP3 dataset
"""

import databento as db
from datetime import datetime, timedelta

def test_available_symbols():
    """Find available symbols and test some energy futures"""
    api_key = "db-3gVxurfuD5jfS6uJB8Df36YUrg7pv"
    client = db.Historical(api_key)
    
    print("🔍 Testing available symbols in GLBX.MDP3...")
    print("=" * 60)
    
    # Test specific contract formats commonly used
    test_symbols = [
        # Crude Oil contracts (different formats)
        'CLN24',  # July 2024
        'CLU24',  # September 2024  
        'CLZ24',  # December 2024
        'CLF25',  # January 2025
        
        # Heating Oil contracts
        'HON24',  # July 2024
        'HOU24',  # September 2024
        'HOZ24',  # December 2024
        
        # Natural Gas contracts
        'NGN24',  # July 2024
        'NGU24',  # September 2024
        'NGZ24',  # December 2024
        
        # E-mini S&P contracts
        'ESU24',  # September 2024
        'ESZ24',  # December 2024
        'ESH25',  # March 2025
    ]
    
    # Test recent date range
    end_date = datetime(2024, 12, 1)  # December 1, 2024
    start_date = end_date - timedelta(days=7)  # Week of data
    
    working_symbols = []
    
    for symbol in test_symbols:
        try:
            print(f"\n📊 Testing {symbol}...")
            data = client.timeseries.get_range(
                dataset='GLBX.MDP3',
                symbols=[symbol],
                schema='ohlcv-1d',
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d')
            )
            
            df = data.to_df()
            if len(df) > 0:
                print(f"✅ {symbol}: Found {len(df)} days of data")
                sample_row = df.iloc[0]
                print(f"   Sample: Close=${sample_row['close']:.2f}, Volume={sample_row.get('volume', 'N/A')}")
                working_symbols.append(symbol)
            else:
                print(f"⚠️  {symbol}: No data returned")
                
        except Exception as e:
            if "did not resolve" in str(e):
                print(f"❌ {symbol}: Symbol does not exist")
            else:
                print(f"❌ {symbol}: Error - {e}")
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY:")
    print(f"✅ Working symbols found: {len(working_symbols)}")
    for symbol in working_symbols:
        print(f"   - {symbol}")
    
    if working_symbols:
        print(f"\n🎯 RECOMMENDATION: Use {working_symbols[0]} for testing")
        return working_symbols[0]
    else:
        print("\n❌ No working symbols found - need to investigate further")
        return None

if __name__ == "__main__":
    working_symbol = test_available_symbols()