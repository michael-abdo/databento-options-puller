#!/usr/bin/env python3
"""
Simple Demo - Works without any setup!
Just run: python simple_demo.py
"""

import csv
import random
from datetime import datetime, timedelta
import os

def create_mock_options_data():
    """Creates realistic-looking options data for demonstration"""
    
    print("🚀 Databento Options Puller - Demo Mode")
    print("=" * 50)
    print("Creating sample options data...")
    
    # Create output directory if it doesn't exist
    os.makedirs("demo_output", exist_ok=True)
    
    # Generate 30 days of data
    start_date = datetime.now() - timedelta(days=30)
    dates = []
    for i in range(30):
        dates.append(start_date + timedelta(days=i))
    
    # Sample option contracts
    contracts = ["OHF24 C27800", "OHG24 C24500", "OHH24 C27000"]
    
    # Generate data
    output_file = "demo_output/sample_options_data.csv"
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Write header
        header = ["timestamp", "Futures_Price"] + contracts
        writer.writerow(header)
        
        # Write data rows
        for date in dates:
            row = [date.strftime("%-m/%-d/%y")]
            
            # Futures price (trending upward with noise)
            base_price = 2.5 + (dates.index(date) * 0.01)
            futures_price = round(base_price + random.uniform(-0.05, 0.05), 2)
            row.append(futures_price)
            
            # Option prices (decreasing as we get further out)
            for i, contract in enumerate(contracts):
                if random.random() > 0.3:  # 70% chance of having data
                    option_price = round(futures_price * 0.05 * (1 - i*0.1) + random.uniform(-0.02, 0.02), 2)
                    row.append(max(0.01, option_price))  # Ensure positive
                else:
                    row.append("")  # Missing data
            
            writer.writerow(row)
    
    print(f"✅ Created sample data file: {output_file}")
    print(f"📊 Generated {len(dates)} days of options data")
    print(f"📋 Contracts included: {', '.join(contracts)}")
    print("\n" + "=" * 50)
    print("📁 Output Preview:")
    print("=" * 50)
    
    # Show first few lines
    with open(output_file, 'r') as f:
        for i, line in enumerate(f):
            if i < 5:
                print(line.strip())
            elif i == 5:
                print("... (25 more rows)")
                break
    
    print("\n✅ Demo complete!")
    print(f"📂 Open '{output_file}' in Excel to see the full data")
    print("\n💡 This is mock data. To use real Databento data:")
    print("   1. Run ./setup_mac.sh")
    print("   2. Add your API key to .env")
    print("   3. Run ./run.sh")

if __name__ == "__main__":
    create_mock_options_data()