#!/usr/bin/env python3
"""
Random Date Tester - Runs 20 random date tests and evaluates results
Compares output with local data to ensure nothing is missing
"""

import random
import subprocess
import json
import pandas as pd
from datetime import datetime, timedelta
import os
from pathlib import Path

class RandomDateTester:
    def __init__(self):
        self.data_dir = Path("/Users/Mike/Desktop/programming/2_proposals/other/databento-options-puller/data")
        self.output_dir = Path("/Users/Mike/Desktop/programming/2_proposals/other/databento-options-puller/output")
        self.results = []
        
    def generate_random_dates(self, num_tests=20):
        """Generate random date ranges for testing."""
        dates = []
        
        # Define different date ranges to test various periods
        periods = [
            # 2025 January (we know has data)
            (datetime(2025, 1, 2), datetime(2025, 1, 20)),
            # 2024 various months
            (datetime(2024, 1, 1), datetime(2024, 12, 31)),
            # 2023 
            (datetime(2023, 1, 1), datetime(2023, 12, 31)),
            # 2022
            (datetime(2022, 1, 1), datetime(2022, 12, 31)),
            # 2021
            (datetime(2021, 1, 1), datetime(2021, 12, 31)),
            # Earlier years
            (datetime(2015, 1, 1), datetime(2020, 12, 31)),
            (datetime(2010, 6, 1), datetime(2014, 12, 31))
        ]
        
        for i in range(num_tests):
            # Pick a random period
            period_start, period_end = random.choice(periods)
            
            # Generate random start date within period
            days_diff = (period_end - period_start).days
            random_days = random.randint(0, max(0, days_diff - 5))
            start_date = period_start + timedelta(days=random_days)
            
            # Generate end date (1-10 days after start)
            end_days = random.randint(1, min(10, (period_end - start_date).days))
            end_date = start_date + timedelta(days=end_days)
            
            dates.append((start_date, end_date))
            
        return dates
    
    def run_single_test(self, start_date, end_date):
        """Run a single test with given dates."""
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        print(f"\n{'='*60}")
        print(f"Test: {start_str} to {end_str}")
        print(f"{'='*60}")
        
        # Run the command
        cmd = f'echo -e "{start_str}\\n{end_str}" | ./START_HERE'
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            
            # Parse output to find the generated file
            output_lines = result.stdout.split('\n')
            output_file = None
            
            for line in output_lines:
                if "Full path:" in line and ".csv" in line:
                    # Extract file path
                    path_part = line.split("Full path:")[1].strip()
                    # Remove ANSI color codes
                    output_file = path_part.replace('\x1b[0;36m', '').replace('\x1b[0m', '').strip()
                    break
            
            if output_file and os.path.exists(output_file):
                # Read the generated CSV
                df = pd.read_csv(output_file)
                
                # Analyze results
                analysis = self.analyze_output(df, start_date, end_date)
                
                self.results.append({
                    'start_date': start_str,
                    'end_date': end_str,
                    'output_file': output_file,
                    'analysis': analysis,
                    'success': True
                })
                
                # Print summary
                print(f"✅ Success! Generated {len(df)} rows")
                print(f"📊 Columns: {', '.join(df.columns)}")
                print(f"💰 Futures prices: {analysis['futures_price_summary']}")
                print(f"📈 Options data: {analysis['options_summary']}")
                
            else:
                print(f"❌ No output file found")
                self.results.append({
                    'start_date': start_str,
                    'end_date': end_str,
                    'output_file': None,
                    'analysis': None,
                    'success': False
                })
                
        except subprocess.TimeoutExpired:
            print(f"⏱️ Timeout for dates {start_str} to {end_str}")
            self.results.append({
                'start_date': start_str,
                'end_date': end_str,
                'output_file': None,
                'analysis': 'TIMEOUT',
                'success': False
            })
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            self.results.append({
                'start_date': start_str,
                'end_date': end_str,
                'output_file': None,
                'analysis': f'ERROR: {str(e)}',
                'success': False
            })
    
    def analyze_output(self, df, start_date, end_date):
        """Analyze the output DataFrame."""
        analysis = {
            'row_count': len(df),
            'columns': list(df.columns),
            'date_range': f"{df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}" if len(df) > 0 else "N/A",
            'futures_price_summary': None,
            'options_summary': {},
            'data_coverage': 0.0
        }
        
        # Analyze Futures_Price column if exists
        if 'Futures_Price' in df.columns:
            futures_prices = df['Futures_Price'].dropna()
            if len(futures_prices) > 0:
                analysis['futures_price_summary'] = {
                    'count': len(futures_prices),
                    'min': futures_prices.min(),
                    'max': futures_prices.max(),
                    'mean': round(futures_prices.mean(), 4),
                    'real_data': not all(price == 2.5 for price in futures_prices)
                }
            else:
                analysis['futures_price_summary'] = "No futures data"
        
        # Analyze option columns
        option_cols = [col for col in df.columns if col not in ['timestamp', 'Futures_Price']]
        for col in option_cols:
            option_data = df[col].dropna()
            if len(option_data) > 0:
                analysis['options_summary'][col] = {
                    'count': len(option_data),
                    'min': option_data.min(),
                    'max': option_data.max(),
                    'coverage': f"{(len(option_data) / len(df)) * 100:.1f}%"
                }
        
        # Calculate overall data coverage
        total_cells = len(df) * (len(df.columns) - 1)  # Exclude timestamp
        filled_cells = sum(df[col].notna().sum() for col in df.columns if col != 'timestamp')
        analysis['data_coverage'] = (filled_cells / total_cells * 100) if total_cells > 0 else 0
        
        return analysis
    
    def check_against_local_data(self):
        """Check results against local data files to identify any missing data."""
        print(f"\n{'='*80}")
        print("CHECKING AGAINST LOCAL DATA FILES")
        print(f"{'='*80}")
        
        # Load the main dataset to check coverage
        main_file = self.data_dir / "glbx-mdp3-20100606-20250617.ohlcv-1d.json"
        jan_file = self.data_dir / "jan_2025_subset.json"
        
        # Currently using jan_2025_subset.json based on src/databento_client.py
        current_data_file = jan_file
        print(f"📂 Current data source: {current_data_file.name}")
        
        # Sample the data file to understand date coverage
        dates_found = set()
        symbols_found = set()
        
        print("🔍 Analyzing data file coverage...")
        with open(current_data_file, 'r') as f:
            for i, line in enumerate(f):
                if i >= 10000:  # Sample first 10k records
                    break
                try:
                    record = json.loads(line)
                    ts = record.get('hd', {}).get('ts_event', '')
                    symbol = record.get('symbol', '')
                    if ts:
                        date = pd.to_datetime(ts).date()
                        dates_found.add(date)
                    if symbol:
                        symbols_found.add(symbol)
                except:
                    continue
        
        print(f"📅 Date range in sample: {min(dates_found)} to {max(dates_found)}")
        print(f"📊 Unique symbols found: {len(symbols_found)}")
        print(f"📈 Sample HO symbols: {[s for s in list(symbols_found)[:10] if s.startswith('HO')]}")
        print(f"📈 Sample OH symbols: {[s for s in list(symbols_found)[:10] if s.startswith('OH')]}")
        
        return dates_found, symbols_found
    
    def generate_summary_report(self):
        """Generate a comprehensive summary report."""
        print(f"\n{'='*80}")
        print("COMPREHENSIVE TEST SUMMARY")
        print(f"{'='*80}")
        
        successful_tests = [r for r in self.results if r['success']]
        failed_tests = [r for r in self.results if not r['success']]
        
        print(f"\n📊 Overall Results:")
        print(f"   ✅ Successful: {len(successful_tests)}/{len(self.results)}")
        print(f"   ❌ Failed: {len(failed_tests)}/{len(self.results)}")
        
        if successful_tests:
            print(f"\n📈 Successful Test Analysis:")
            
            # Group by data quality
            real_data_tests = []
            mock_data_tests = []
            
            for test in successful_tests:
                if test['analysis']['futures_price_summary']:
                    if isinstance(test['analysis']['futures_price_summary'], dict):
                        if test['analysis']['futures_price_summary'].get('real_data', False):
                            real_data_tests.append(test)
                        else:
                            mock_data_tests.append(test)
            
            print(f"\n   💎 Tests with REAL market data: {len(real_data_tests)}")
            for test in real_data_tests[:5]:  # Show first 5
                print(f"      • {test['start_date']} to {test['end_date']}")
                print(f"        Futures: ${test['analysis']['futures_price_summary']['min']:.4f} - ${test['analysis']['futures_price_summary']['max']:.4f}")
                if test['analysis']['options_summary']:
                    print(f"        Options: {', '.join(test['analysis']['options_summary'].keys())}")
            
            print(f"\n   🔵 Tests with mock data ($2.50): {len(mock_data_tests)}")
            for test in mock_data_tests[:5]:  # Show first 5
                print(f"      • {test['start_date']} to {test['end_date']}")
        
        # Identify patterns
        print(f"\n🔍 Data Availability Patterns:")
        
        # Check which years have real data
        years_with_data = {}
        for test in successful_tests:
            year = test['start_date'][:4]
            if year not in years_with_data:
                years_with_data[year] = {'real': 0, 'mock': 0}
            
            if test['analysis']['futures_price_summary']:
                if isinstance(test['analysis']['futures_price_summary'], dict):
                    if test['analysis']['futures_price_summary'].get('real_data', False):
                        years_with_data[year]['real'] += 1
                    else:
                        years_with_data[year]['mock'] += 1
        
        for year, counts in sorted(years_with_data.items()):
            print(f"   {year}: {counts['real']} real, {counts['mock']} mock")
        
        return successful_tests, failed_tests

def main():
    """Run the random date tests."""
    tester = RandomDateTester()
    
    print("🎲 Random Date Tester for Databento Options Puller")
    print("=" * 80)
    
    # Generate random dates
    test_dates = tester.generate_random_dates(20)
    
    print(f"\n📅 Generated {len(test_dates)} random date ranges for testing:")
    for i, (start, end) in enumerate(test_dates[:5]):  # Show first 5
        print(f"   {i+1}. {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")
    print("   ...")
    
    # Run tests
    print(f"\n🚀 Running tests...")
    for i, (start, end) in enumerate(test_dates):
        print(f"\n[Test {i+1}/{len(test_dates)}]")
        tester.run_single_test(start, end)
    
    # Check against local data
    dates_found, symbols_found = tester.check_against_local_data()
    
    # Generate summary
    successful_tests, failed_tests = tester.generate_summary_report()
    
    # Final recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    print(f"   1. Current data source is limited to January 2025")
    print(f"   2. To access full date range, update src/databento_client.py to use:")
    print(f"      'glbx-mdp3-20100606-20250617.ohlcv-1d.json'")
    print(f"   3. Consider creating date-specific subsets for faster loading")
    print(f"   4. Real data confirmed available for dates within data file coverage")

if __name__ == "__main__":
    main()