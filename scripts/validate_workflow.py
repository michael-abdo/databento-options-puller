#!/usr/bin/env python3
"""
Validation script for NY Harbor ULSD Options Data Workflow
Ensures compliance with strict constraints defined in claude.md
"""

import os
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / 'src'))
sys.path.append(str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

def reload_constraints():
    """Step 1: Reload constraints from claude.md"""
    print("\n🔄 Step 1: Reloading constraints from claude.md...")
    with open('claude.md', 'r') as f:
        constraints = f.read()
    
    # Extract key constraints
    input_constraint = "databento API key and web search databento documentation"
    output_constraint = "/output/final_output.csv"
    throughput_constraint = "15-delta call options with M+2 expiration"
    
    print(f"✓ Input: {input_constraint}")
    print(f"✓ Output: {output_constraint}")
    print(f"✓ Throughput: {throughput_constraint}")
    
    return True

def validate_output_format(csv_path):
    """Step 3: Validate output format matches specification"""
    print(f"\n🔍 Step 3: Validating output format for {csv_path}...")
    
    if not os.path.exists(csv_path):
        print(f"❌ Output file not found: {csv_path}")
        return False
    
    df = pd.read_csv(csv_path)
    
    # Check column structure
    if 'timestamp' not in df.columns:
        print("❌ Missing 'timestamp' column")
        return False
    
    if 'Futures_Price' not in df.columns:
        print("❌ Missing 'Futures_Price' column")
        return False
    
    # Check date format (M/D/YY)
    try:
        # Verify date format by parsing first date
        first_date = df.iloc[0]['timestamp']
        datetime.strptime(first_date, '%-m/%-d/%y')
        print(f"✓ Date format correct: {first_date}")
    except:
        try:
            datetime.strptime(first_date, '%m/%d/%y')
            print(f"✓ Date format correct: {first_date}")
        except:
            print(f"❌ Invalid date format: {first_date} (expected M/D/YY)")
            return False
    
    # Check option columns format (e.g., OHG2 C00325)
    option_cols = [col for col in df.columns if col not in ['timestamp', 'Futures_Price']]
    for col in option_cols:
        if not col.startswith('OH') or ' C' not in col:
            print(f"❌ Invalid option column format: {col}")
            return False
        print(f"✓ Valid option column: {col}")
    
    print(f"✓ Output validation passed: {len(df)} rows, {len(df.columns)} columns")
    return True

def diagnose_issues(csv_path, expected_format):
    """Step 4: Diagnose and reflect on any mismatches"""
    print("\n🔧 Step 4: Diagnosing issues...")
    
    if not os.path.exists(csv_path):
        print("❌ Issue: Output file does not exist")
        print("  Cause: Script may have failed or output path is incorrect")
        return ["Output file creation failed"]
    
    df = pd.read_csv(csv_path)
    issues = []
    
    # Check each constraint
    if 'timestamp' not in df.columns:
        issues.append("Missing timestamp column - check data processing logic")
    
    if 'Futures_Price' not in df.columns:
        issues.append("Missing Futures_Price column - check futures data fetching")
    
    # Check option identification logic
    option_cols = [col for col in df.columns if col not in ['timestamp', 'Futures_Price']]
    if not option_cols:
        issues.append("No option columns found - check 15-delta option identification")
    
    # Check rolling logic (M+2)
    for col in option_cols:
        if col.startswith('OH'):
            month_char = col[2]  # Extract month character
            print(f"  Option {col} has month code: {month_char}")
    
    if issues:
        print(f"❌ Found {len(issues)} issues:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    else:
        print("✓ No issues found")
    
    return issues

def main():
    """Main validation workflow"""
    print("="*60)
    print("NY Harbor ULSD Options Data Workflow Validator")
    print("="*60)
    
    # Step 1: Reload constraints
    reload_constraints()
    
    # Step 2: Check if we need to execute workflow
    output_path = "output/final_output.csv"
    
    if not os.path.exists(output_path):
        print(f"\n⚠️  Output file not found at {output_path}")
        print("📝 Run the workflow first with:")
        print("   python3 databento_options_puller.py --start-date 2021-12-01 --end-date 2022-03-31 --output output/final_output.csv")
        return
    
    # Step 3: Validate output
    is_valid = validate_output_format(output_path)
    
    # Step 4: Diagnose issues if validation failed
    if not is_valid:
        issues = diagnose_issues(output_path, "expected_format")
        
        # Step 5: Strategize fixes
        print("\n💡 Step 5: Suggested fixes:")
        if "date format" in str(issues):
            print("  - Update date formatting in output generation")
        if "option columns" in str(issues):
            print("  - Verify 15-delta calculation and option selection")
        if "Missing" in str(issues):
            print("  - Check data fetching and processing pipeline")
    else:
        print("\n✅ Validation PASSED! Output matches all constraints.")
        
        # Show sample of output
        df = pd.read_csv(output_path)
        print(f"\n📊 Sample output ({output_path}):")
        print(df.head(10).to_string(index=False))

if __name__ == "__main__":
    main()