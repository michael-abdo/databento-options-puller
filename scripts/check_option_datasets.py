#!/usr/bin/env python3
"""
Check which datasets have options data
"""

import databento as db

def check_option_datasets():
    """Check which datasets might have options"""
    api_key = "db-3gVxurfuD5jfS6uJB8Df36YUrg7pv"
    client = db.Historical(api_key)
    
    print("🎯 Checking which datasets have OPTIONS...")
    print("=" * 60)
    
    # Get all available datasets
    datasets = client.metadata.list_datasets()
    print(f"📊 Found {len(datasets)} total datasets")
    
    # Look for options-related datasets
    options_likely = []
    for dataset in datasets:
        dataset_str = str(dataset)
        if any(keyword in dataset_str.upper() for keyword in ['OPRA', 'OPTION', 'OPT']):
            options_likely.append(dataset)
    
    print(f"\n🔍 Datasets likely to have options:")
    for dataset in options_likely:
        print(f"   - {dataset}")
    
    if not options_likely:
        print("❌ No obvious options datasets found")
        print("\n📋 All available datasets:")
        for i, dataset in enumerate(datasets):
            print(f"   {i+1:2d}. {dataset}")
        
        print("\n🔍 Let's check if any datasets mention futures/commodities...")
        futures_likely = []
        for dataset in datasets:
            dataset_str = str(dataset)
            if any(keyword in dataset_str.upper() for keyword in ['CME', 'NYMEX', 'COMEX', 'GLOBEX', 'FUTURES', 'COMMODITY']):
                futures_likely.append(dataset)
        
        print(f"📊 Datasets likely to have futures:")
        for dataset in futures_likely:
            print(f"   - {dataset}")
    
    # Test if any dataset has options by trying a known symbol
    print(f"\n🧪 Testing datasets for options support...")
    
    test_datasets = options_likely if options_likely else [d for d in datasets if 'OPRA' in str(d) or 'CME' in str(d) or 'GLBX' in str(d)]
    
    if not test_datasets:
        test_datasets = datasets[:5]  # Test first 5 if no obvious candidates
    
    for dataset in test_datasets:
        print(f"\n📊 Testing {dataset}...")
        try:
            # Try a simple ES futures option (common format)
            data = client.timeseries.get_range(
                dataset=str(dataset),
                symbols=['ES C4500'],  # Simple format
                schema='ohlcv-1d',
                start='2021-12-15',
                end='2021-12-16'
            )
            df = data.to_df()
            if len(df) > 0:
                print(f"   ✅ {dataset} HAS OPTIONS! Found data.")
            else:
                print(f"   ⚠️ {dataset} - No data returned")
        except Exception as e:
            if "did not resolve" in str(e):
                print(f"   ❌ {dataset} - Symbol doesn't exist")
            elif "schema" in str(e).lower():
                print(f"   ⚠️ {dataset} - Schema issue: {e}")
            else:
                print(f"   ❌ {dataset} - Error: {e}")

if __name__ == "__main__":
    check_option_datasets()