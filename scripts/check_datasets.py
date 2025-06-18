#!/usr/bin/env python3
"""
Check available datasets and their contents
"""

import databento as db

def check_datasets():
    """Check what datasets are available and test them"""
    api_key = "db-3gVxurfuD5jfS6uJB8Df36YUrg7pv"
    client = db.Historical(api_key)
    
    print("🔍 Checking available datasets...")
    print("=" * 60)
    
    try:
        # Get all available datasets
        datasets = client.metadata.list_datasets()
        print(f"📊 Found {len(datasets)} total datasets:")
        
        for i, dataset in enumerate(datasets):
            print(f"   {i+1}. {dataset}")
        
        print("\n🎯 Testing CME-related datasets...")
        
        # Filter for CME or energy-related datasets
        cme_datasets = [ds for ds in datasets if 'CME' in str(ds) or 'GLBX' in str(ds) or 'NYMEX' in str(ds)]
        
        if cme_datasets:
            print(f"✅ Found {len(cme_datasets)} CME-related datasets:")
            for dataset in cme_datasets:
                print(f"   - {dataset}")
        else:
            print("❌ No CME-related datasets found")
        
        # Try to get schema info for GLBX.MDP3
        print(f"\n📋 Checking schemas for GLBX.MDP3...")
        try:
            schemas = client.metadata.list_schemas('GLBX.MDP3')
            print(f"✅ Available schemas: {schemas}")
        except Exception as e:
            print(f"❌ Could not get schemas: {e}")
        
        # Try to get some symbols from GLBX.MDP3
        print(f"\n🔍 Checking available symbols in GLBX.MDP3...")
        try:
            # Try to list symbols (this might not work depending on API)
            symbols = client.metadata.list_symbols('GLBX.MDP3')
            print(f"✅ Found {len(symbols)} symbols")
            if len(symbols) > 0:
                print("📋 Sample symbols:")
                for symbol in symbols[:10]:  # Show first 10
                    print(f"   - {symbol}")
        except Exception as e:
            print(f"❌ Could not get symbols: {e}")
            print("   This is normal - some APIs don't allow symbol listing")
        
    except Exception as e:
        print(f"❌ Error checking datasets: {e}")

if __name__ == "__main__":
    check_datasets()