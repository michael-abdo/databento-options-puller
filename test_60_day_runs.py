#!/usr/bin/env python3
"""
Test script to run 20 different 60+ day periods and analyze results.
Each test should produce multiple option columns (3+) if the strategy is working correctly.
"""

import subprocess
import pandas as pd
import os
from datetime import datetime, timedelta
import json

def run_test(test_id, start_date, end_date, output_file):
    """Run a single test and return results."""
    print(f"\n{'='*60}")
    print(f"Test {test_id:2d}: {start_date} to {end_date}")
    print(f"Expected period: {(pd.to_datetime(end_date) - pd.to_datetime(start_date)).days} days")
    
    cmd = [
        'python3', 'databento_options_puller.py',
        '--start-date', start_date,
        '--end-date', end_date,
        '--output', output_file,
        '--mock-mode',
        '--quiet'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            # Check if file exists and analyze
            if os.path.exists(output_file):
                df = pd.read_csv(output_file)
                num_rows = len(df)
                num_cols = len(df.columns)
                option_cols = [col for col in df.columns if col != 'timestamp']
                
                print(f"✅ SUCCESS: {num_rows} rows, {num_cols} columns")
                print(f"   Option columns: {option_cols}")
                
                # Check for expected multiple options
                if len(option_cols) >= 3:
                    print(f"   ✅ Expected 3+ option columns: {len(option_cols)}")
                else:
                    print(f"   ⚠️  Only {len(option_cols)} option columns (expected 3+)")
                
                return {
                    'test_id': test_id,
                    'start_date': start_date,
                    'end_date': end_date,
                    'period_days': (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days,
                    'success': True,
                    'rows': num_rows,
                    'total_columns': num_cols,
                    'option_columns': len(option_cols),
                    'option_names': option_cols,
                    'file_size': os.path.getsize(output_file),
                    'stdout': result.stdout.strip(),
                    'stderr': result.stderr.strip()
                }
            else:
                print(f"❌ FAILED: Output file not created")
                return {
                    'test_id': test_id,
                    'start_date': start_date,
                    'end_date': end_date,
                    'success': False,
                    'error': 'Output file not created',
                    'stdout': result.stdout.strip(),
                    'stderr': result.stderr.strip()
                }
        else:
            print(f"❌ FAILED: Exit code {result.returncode}")
            print(f"   Error: {result.stderr.strip()}")
            return {
                'test_id': test_id,
                'start_date': start_date,
                'end_date': end_date,
                'success': False,
                'error': f"Exit code {result.returncode}",
                'stdout': result.stdout.strip(),
                'stderr': result.stderr.strip()
            }
            
    except subprocess.TimeoutExpired:
        print(f"❌ FAILED: Timeout after 60 seconds")
        return {
            'test_id': test_id,
            'start_date': start_date,
            'end_date': end_date,
            'success': False,
            'error': 'Timeout after 60 seconds'
        }
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return {
            'test_id': test_id,
            'start_date': start_date,
            'end_date': end_date,
            'success': False,
            'error': str(e)
        }

def main():
    """Run all 20 tests and analyze results."""
    print("🧪 Running 20 tests with 60+ day periods")
    print("📋 Each test should produce 3+ option columns if strategy is working correctly")
    
    # Define 20 test periods (60+ days each, covering different market periods)
    test_periods = [
        # Q4 2021 - Q1 2022 (various 60+ day windows)
        ('2021-12-01', '2022-02-15'),  # 76 days
        ('2021-11-15', '2022-01-31'),  # 77 days
        ('2021-10-01', '2021-12-15'),  # 75 days
        
        # Q2 2022 periods
        ('2022-03-01', '2022-05-15'),  # 75 days
        ('2022-04-15', '2022-07-01'),  # 77 days
        ('2022-02-15', '2022-04-30'),  # 74 days
        
        # Q3 2022 periods  
        ('2022-06-01', '2022-08-15'),  # 75 days
        ('2022-07-15', '2022-10-01'),  # 78 days
        ('2022-05-01', '2022-07-15'),  # 75 days
        
        # Q4 2022 periods
        ('2022-09-01', '2022-11-15'),  # 75 days
        ('2022-10-15', '2023-01-01'),  # 78 days
        ('2022-08-15', '2022-11-01'),  # 78 days
        
        # 2023 periods
        ('2023-01-15', '2023-04-01'),  # 76 days
        ('2023-03-01', '2023-05-15'),  # 75 days
        ('2023-05-01', '2023-07-15'),  # 75 days
        ('2023-07-01', '2023-09-15'),  # 76 days
        ('2023-09-01', '2023-11-15'),  # 75 days
        
        # Longer periods (90+ days)
        ('2022-01-01', '2022-04-15'),  # 104 days
        ('2022-06-15', '2022-10-01'),  # 108 days
        ('2023-02-01', '2023-06-01'),  # 120 days
    ]
    
    results = []
    
    # Run each test
    for i, (start_date, end_date) in enumerate(test_periods, 1):
        output_file = f"test_60day_{i:02d}.csv"
        result = run_test(i, start_date, end_date, output_file)
        results.append(result)
    
    # Analyze overall results
    print(f"\n{'='*80}")
    print("📊 ANALYSIS SUMMARY")
    print(f"{'='*80}")
    
    successful_tests = [r for r in results if r['success']]
    failed_tests = [r for r in results if not r['success']]
    
    print(f"✅ Successful tests: {len(successful_tests)}/{len(results)}")
    print(f"❌ Failed tests: {len(failed_tests)}/{len(results)}")
    
    if successful_tests:
        print(f"\n📈 SUCCESS ANALYSIS:")
        option_column_counts = [r['option_columns'] for r in successful_tests]
        print(f"   Option columns range: {min(option_column_counts)} - {max(option_column_counts)}")
        print(f"   Average option columns: {sum(option_column_counts)/len(option_column_counts):.1f}")
        
        # Count how many have 3+ columns
        multi_column_tests = [r for r in successful_tests if r['option_columns'] >= 3]
        print(f"   Tests with 3+ option columns: {len(multi_column_tests)}/{len(successful_tests)}")
        
        if len(multi_column_tests) < len(successful_tests):
            print(f"\n⚠️  WARNING: {len(successful_tests) - len(multi_column_tests)} tests have < 3 option columns!")
            single_column_tests = [r for r in successful_tests if r['option_columns'] < 3]
            for test in single_column_tests:
                print(f"      Test {test['test_id']}: {test['start_date']} to {test['end_date']} -> {test['option_columns']} columns")
    
    if failed_tests:
        print(f"\n❌ FAILURE ANALYSIS:")
        for test in failed_tests:
            print(f"   Test {test['test_id']}: {test.get('error', 'Unknown error')}")
    
    # Save detailed results
    with open('test_60day_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: test_60day_results.json")
    
    # Sample a few output files for manual inspection
    print(f"\n🔍 SAMPLE OUTPUT INSPECTION:")
    sample_files = [f"test_60day_{i:02d}.csv" for i in [1, 5, 10, 15, 20] if os.path.exists(f"test_60day_{i:02d}.csv")]
    
    for file in sample_files[:3]:  # Show first 3 samples
        if os.path.exists(file):
            print(f"\n📄 {file}:")
            df = pd.read_csv(file)
            print(f"   Shape: {df.shape}")
            print(f"   Columns: {list(df.columns)}")
            print(f"   First few rows:")
            print(df.head(3).to_string(index=False))

if __name__ == "__main__":
    main()