#!/usr/bin/env python3
"""
Quick Example - Databento Options Puller

This script demonstrates the simplest way to use the options puller.
Just run: python quick_example.py
"""

from databento_options_puller import DatabentoOptionsPuller
from datetime import datetime
import pandas as pd
import os

def main():
    """Run a simple example of the options puller."""
    
    print("🚀 Databento Options Puller - Quick Example")
    print("=" * 50)
    
    # Create puller instance (uses mock data by default)
    print("\n1️⃣ Creating options puller...")
    puller = DatabentoOptionsPuller(
        api_key="mock_key",  # No real key needed for mock data
        config={'use_mock': True}
    )
    
    # Set date range (1 month for quick demo)
    start_date = datetime(2021, 12, 1)
    end_date = datetime(2021, 12, 31)
    
    print(f"\n2️⃣ Fetching options data...")
    print(f"   Date range: {start_date.date()} to {end_date.date()}")
    
    # Run the puller
    try:
        df = puller.run(start_date, end_date)
        
        print(f"\n3️⃣ Success! Generated {len(df)} rows of data")
        
        # Show sample of the data
        print("\n4️⃣ Sample output (first 5 rows):")
        print("-" * 70)
        print(df.head().to_string(index=False))
        
        # Save to file
        output_file = "quick_example_output.csv"
        df.to_csv(output_file, index=False)
        
        print(f"\n5️⃣ Full output saved to: {output_file}")
        
        # Show summary statistics
        print("\n6️⃣ Summary:")
        print(f"   - Total days: {len(df)}")
        print(f"   - Columns: {', '.join(df.columns)}")
        
        # Find option columns
        option_cols = [col for col in df.columns if 'C' in col and col != 'timestamp']
        if option_cols:
            print(f"   - Options found: {', '.join(option_cols)}")
            
            # Show active periods for each option
            print("\n7️⃣ Option active periods:")
            for col in option_cols:
                active_days = df[col].notna().sum()
                first_day = df[df[col].notna()]['timestamp'].iloc[0] if active_days > 0 else 'N/A'
                last_day = df[df[col].notna()]['timestamp'].iloc[-1] if active_days > 0 else 'N/A'
                print(f"   - {col}: {active_days} days ({first_day} to {last_day})")
        
        print("\n✅ Example completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you're in the project directory")
        print("2. Ensure virtual environment is activated")
        print("3. Check that requirements are installed: pip install -r requirements.txt")
        return 1
    
    # Show next steps
    print("\n📚 Next steps:")
    print("1. View the generated file: quick_example_output.csv")
    print("2. Try different date ranges by editing this script")
    print("3. Switch to live data by setting DATABENTO_API_KEY")
    print("4. Read GETTING_STARTED.md for more options")
    
    return 0


if __name__ == "__main__":
    exit(main())