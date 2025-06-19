#!/usr/bin/env python3
"""
Analyze Long Range Test Results
"""

import pandas as pd
from pathlib import Path

class LongRangeAnalyzer:
    def __init__(self):
        self.output_dir = Path("/Users/Mike/Desktop/programming/2_proposals/other/databento-options-puller/output")
        
    def analyze_test_files(self):
        """Analyze the long range test outputs."""
        
        # Define the test files from the long range tests
        test_files = [
            ("2021-12-02", "2022-03-09", "HO_call_ohlcv-1d_20211202_to_20220309.csv", "Target validation (97 days)"),
            ("2025-01-02", "2025-01-31", "HO_call_ohlcv-1d_20250102_to_20250131.csv", "Full January 2025"),
            ("2024-11-01", "2025-01-31", "HO_call_ohlcv-1d_20241101_to_20250131.csv", "Q4 2024 - Q1 2025"),
            ("2024-01-01", "2024-03-31", "HO_call_ohlcv-1d_20240101_to_20240331.csv", "Q1 2024"),
            ("2023-07-01", "2023-09-30", "HO_call_ohlcv-1d_20230701_to_20230930.csv", "Q3 2023"),
            ("2022-04-01", "2022-06-30", "HO_call_ohlcv-1d_20220401_to_20220630.csv", "Q2 2022"),
            ("2021-10-01", "2021-12-31", "HO_call_ohlcv-1d_20211001_to_20211231.csv", "Q4 2021"),
            ("2020-11-01", "2021-02-28", "HO_call_ohlcv-1d_20201101_to_20210228.csv", "Winter 2020-2021"),
            ("2019-12-01", "2020-03-15", "HO_call_ohlcv-1d_20191201_to_20200315.csv", "Winter 2019-2020"),
            ("2018-06-01", "2018-08-31", "HO_call_ohlcv-1d_20180601_to_20180831.csv", "Summer 2018"),
            ("2017-05-15", "2017-08-15", "HO_call_ohlcv-1d_20170515_to_20170815.csv", "Summer 2017"),
            ("2015-01-01", "2015-04-30", "HO_call_ohlcv-1d_20150101_to_20150430.csv", "Q1-Q2 2015"),
            ("2013-09-01", "2013-12-31", "HO_call_ohlcv-1d_20130901_to_20131231.csv", "Fall 2013"),
            ("2011-06-01", "2011-09-30", "HO_call_ohlcv-1d_20110601_to_20110930.csv", "Summer-Fall 2011"),
            ("2016-01-01", "2016-06-30", "HO_call_ohlcv-1d_20160101_to_20160630.csv", "H1 2016"),
        ]
        
        # Also analyze final_output.csv for comparison
        final_output_path = self.output_dir / "final_output.csv"
        final_df = pd.read_csv(final_output_path)
        
        print("📊 LONG RANGE TEST RESULTS ANALYSIS")
        print("=" * 80)
        
        print(f"\n🎯 TARGET REFERENCE (final_output.csv):")
        print(f"   • Rows: {len(final_df)}")
        print(f"   • Columns: {len(final_df.columns)} - {', '.join(final_df.columns)}")
        print(f"   • Date range: {final_df['timestamp'].iloc[0]} to {final_df['timestamp'].iloc[-1]}")
        
        # Count data points in final_output
        total_cells = 0
        for col in final_df.columns[1:]:  # Skip timestamp
            non_empty = final_df[col].notna().sum()
            if non_empty > 0:
                total_cells += non_empty
                print(f"   • {col}: {non_empty} values")
        print(f"   • Total data points: {total_cells}")
        
        print(f"\n📈 LONG RANGE TEST RESULTS:")
        print("-" * 80)
        
        real_data_tests = []
        mock_data_tests = []
        
        for start_date, end_date, filename, description in test_files:
            filepath = self.output_dir / filename
            
            if filepath.exists():
                df = pd.read_csv(filepath)
                
                print(f"\n📅 {description}")
                print(f"   Range: {start_date} to {end_date}")
                print(f"   File: {filename}")
                print(f"   Rows: {len(df)}")
                print(f"   Columns: {len(df.columns)}")
                
                # Check if it has real data
                has_real_data = False
                if 'Futures_Price' in df.columns:
                    futures = df['Futures_Price'].dropna()
                    if len(futures) > 0:
                        unique_prices = futures.unique()
                        has_real_data = not (len(unique_prices) == 1 and unique_prices[0] == 2.5)
                        
                        print(f"   Futures: ${futures.min():.4f} - ${futures.max():.4f} ({'REAL' if has_real_data else 'MOCK'})")
                
                # Count options data
                option_cols = [col for col in df.columns if col not in ['timestamp', 'Futures_Price']]
                if option_cols:
                    print(f"   Options: {len(option_cols)} columns")
                    total_option_values = 0
                    for col in option_cols:
                        values = df[col].notna().sum()
                        if values > 0:
                            total_option_values += values
                            print(f"     • {col}: {values} values ({(values/len(df)*100):.1f}% coverage)")
                    print(f"   Total option data points: {total_option_values}")
                
                # Categorize
                if has_real_data:
                    real_data_tests.append((description, len(df), len(option_cols)))
                else:
                    mock_data_tests.append((description, len(df), len(option_cols)))
            else:
                print(f"\n❌ {description}: File not found")
        
        # Summary
        print(f"\n" + "="*80)
        print("SUMMARY ANALYSIS")
        print("="*80)
        
        print(f"\n✅ Tests with REAL market data: {len(real_data_tests)}")
        for desc, rows, opt_cols in real_data_tests:
            print(f"   • {desc}: {rows} rows, {opt_cols} option columns")
        
        print(f"\n🔵 Tests with MOCK data ($2.50): {len(mock_data_tests)}")
        print(f"   Total: {len(mock_data_tests)} tests")
        
        # Compare with target
        target_test = next((t for t in test_files if "Target validation" in t[3]), None)
        if target_test:
            _, _, filename, _ = target_test
            filepath = self.output_dir / filename
            if filepath.exists():
                df = pd.read_csv(filepath)
                print(f"\n🎯 TARGET COMPARISON:")
                print(f"   final_output.csv: 72 rows, 5 option columns")
                print(f"   Our test result: {len(df)} rows, {len([c for c in df.columns if c not in ['timestamp', 'Futures_Price']])} option columns")
                
                # Check if columns match
                our_options = set([c for c in df.columns if c not in ['timestamp', 'Futures_Price']])
                target_options = set(final_df.columns[1:])
                
                print(f"\n   Column comparison:")
                print(f"   Matching: {our_options & target_options}")
                print(f"   Missing: {target_options - our_options}")
                print(f"   Extra: {our_options - target_options}")

def main():
    analyzer = LongRangeAnalyzer()
    analyzer.analyze_test_files()

if __name__ == "__main__":
    main()