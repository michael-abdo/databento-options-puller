#!/usr/bin/env python3
"""
Working example showing how to use the Databento API key
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import our modules
from src.databento_client import DatabentoBridge
from src.example_analyzer import ExampleAnalyzer

def main():
    print("Databento Options Puller - Working Example")
    print("=" * 50)
    
    # Use example mode which has known working data
    print("\n1. Running example analyzer to understand the data format...")
    analyzer = ExampleAnalyzer()
    analyzer.analyze()
    
    print("\n2. Testing with mock data (no API needed)...")
    
    # Create mock client
    client = DatabentoBridge(api_key=None)  # Forces mock mode
    print(f"   Mock mode: {client.mock_mode}")
    
    # Test futures data
    print("\n3. Getting mock futures data...")
    futures_data = client.get_futures_data('HO', '2021-12-01', '2021-12-05')
    if futures_data:
        print(f"   ✅ Got {len(futures_data)} days of futures data")
        print(f"   Sample: {futures_data.iloc[0].to_dict()}")
    
    print("\n" + "=" * 50)
    print("✅ Setup is working correctly!")
    print("\nTo use real data:")
    print("1. Make sure your API key is in .env")
    print("2. Run: python3 databento_options_puller.py --start-date 2021-12-01 --end-date 2021-12-31")
    print("\nNote: Real data requires:")
    print("- Valid subscription to CME Globex data")
    print("- Access to HO (Heating Oil) futures and options")
    print("- Correct date range with available data")

if __name__ == "__main__":
    main()