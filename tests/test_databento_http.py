#!/usr/bin/env python3
"""
Test Databento HTTP API directly to find correct symbol format
"""

import requests
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
api_key = os.getenv('DATABENTO_API_KEY')

headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}

# Test with different datasets
datasets = ['GLBX.MDP3', 'XNAS.ITCH', 'OPRA.PILLAR']

for dataset in datasets:
    print(f"\n\nTesting dataset: {dataset}")
    
    # Try to get dataset info
    url = f"https://hist.databento.com/v0/metadata.get_dataset?dataset={dataset}"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"Dataset info: {data}")
        else:
            print(f"Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Request error: {e}")

# Try searching for HO symbols
print("\n\nSearching for HO symbols...")
url = "https://hist.databento.com/v0/symbology.resolve"
    
payload = {
    "dataset": "GLBX.MDP3",
    "symbols": ["HO", "HOZ1", "HOZ21", "HO_Z1", "HO Z1"],
    "stype_in": "raw_symbol",
    "stype_out": "raw_symbol",
    "start_date": "2021-12-01",
    "end_date": "2021-12-02"
}

try:
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"Symbol resolution: {data}")
    else:
        print(f"Error {response.status_code}: {response.text}")
except Exception as e:
    print(f"Request error: {e}")