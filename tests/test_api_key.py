#!/usr/bin/env python3
"""
Test Databento API key and connection
"""

import os
import databento as db
from datetime import datetime, timedelta

# Load API key from .env
from pathlib import Path
env_path = Path('.env')
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if line.startswith('DATABENTO_API_KEY='):
                api_key = line.split('=', 1)[1].strip()
                break
else:
    api_key = os.getenv('DATABENTO_API_KEY')

print(f"Testing Databento API key: {api_key[:15]}...")
print("=" * 50)

try:
    # Create client
    client = db.Historical(api_key)
    print("✅ Client created successfully")
    
    # Test 1: List available datasets
    print("\n1. Testing dataset listing...")
    datasets = client.metadata.list_datasets()
    print(f"✅ Found {len(datasets)} datasets")
    
    # Test 2: Check if we can access CME data
    print("\n2. Checking CME Globex access...")
    glbx_found = any('GLBX' in str(ds) for ds in datasets)
    if glbx_found:
        print("✅ CME Globex (GLBX) dataset available")
    else:
        print("❌ CME Globex dataset not found in available datasets")
        print("Available datasets:", datasets[:5])
    
    # Test 3: Try to get some recent data (ES futures as a test)
    print("\n3. Testing data retrieval...")
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=5)
    
    try:
        # Try to get ES (E-mini S&P) data as a test
        data = client.timeseries.get_range(
            dataset='GLBX.MDP3',
            symbols=['ES'],
            schema='ohlcv-1d',
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d')
        )
        
        if data.empty:
            print("⚠️  No data returned (might be outside market hours or holiday)")
        else:
            print(f"✅ Successfully retrieved {len(data)} days of data")
            print(f"   Sample: {data.iloc[0]['symbol']} - Close: ${data.iloc[0]['close']:,.2f}")
    except Exception as e:
        print(f"❌ Data retrieval failed: {e}")
        print("   This might be due to subscription limits or data availability")
    
    print("\n" + "=" * 50)
    print("✅ API KEY IS VALID AND WORKING!")
    print("\nNote: The options puller might fail if:")
    print("- You don't have access to the specific HO (Heating Oil) data")
    print("- The requested date range has no options data")
    print("- Your subscription doesn't include options data")
    
except Exception as e:
    print(f"\n❌ API key test failed: {e}")
    print("\nPlease check:")
    print("1. Your API key is correct")
    print("2. You have an active Databento subscription")
    print("3. Your internet connection is working")