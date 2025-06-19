#!/usr/bin/env python3
"""
Analyze strike coverage for options data to verify we have sufficient strikes for 15-delta selection.
"""

import json
from collections import defaultdict
from datetime import datetime
import os
import re

def analyze_strike_coverage():
    """Analyze the strike coverage in options data."""
    
    data_file = "/Users/Mike/Desktop/programming/2_proposals/other/databento-options-puller/data/glbx-mdp3-20100606-20250617.ohlcv-1d.json"
    
    print("Analyzing strike coverage for OH options...")
    print(f"Reading data file...")
    
    # Track strikes by expiration
    strikes_by_expiry = defaultdict(set)
    options_by_date_expiry = defaultdict(lambda: defaultdict(set))
    futures_prices_by_date = {}
    total_lines = 0
    
    # Read and process the file
    with open(data_file, 'r') as f:
        for line_num, line in enumerate(f):
            try:
                record = json.loads(line.strip())
                total_lines += 1
                
                # Get symbol and timestamp
                symbol = record.get('symbol', '')
                ts_event = record.get('hd', {}).get('ts_event')
                close_price = float(record.get('close', 0))
                
                if not ts_event:
                    continue
                
                # Parse timestamp to date
                try:
                    timestamp = datetime.fromisoformat(ts_event.replace('Z', '+00:00'))
                    date = timestamp.date()
                except:
                    continue
                
                # Track futures prices for reference
                if symbol.startswith('HO') and ' ' not in symbol and close_price > 0:
                    futures_prices_by_date[date] = float(close_price)
                
                # Analyze options
                if symbol.startswith('OH') and ' C' in symbol:
                    # Parse option symbol (e.g., "OHF2 C27800")
                    parts = symbol.split(' ')
                    if len(parts) == 2:
                        expiry_code = parts[0]  # e.g., "OHF2"
                        strike_part = parts[1]   # e.g., "C27800"
                        
                        if strike_part.startswith('C'):
                            try:
                                strike_value = int(strike_part[1:])
                                strike_price = strike_value / 10000.0  # Convert to dollars
                                
                                # Track by expiry
                                strikes_by_expiry[expiry_code].add(strike_price)
                                
                                # Track by date and expiry
                                options_by_date_expiry[date][expiry_code].add(strike_price)
                                
                            except ValueError:
                                continue
                
                # Progress indicator
                if line_num % 100000 == 0 and line_num > 0:
                    print(f"Processed {line_num:,} lines...")
                    
            except json.JSONDecodeError:
                continue
    
    print(f"\nTotal lines processed: {total_lines:,}")
    
    # Analyze strike coverage
    analyze_coverage(strikes_by_expiry, options_by_date_expiry, futures_prices_by_date)

def analyze_coverage(strikes_by_expiry, options_by_date_expiry, futures_prices_by_date):
    """Analyze and report on strike coverage."""
    
    print("\n=== STRIKE COVERAGE ANALYSIS ===\n")
    
    # Overall statistics
    print(f"Total unique expiries with options: {len(strikes_by_expiry)}")
    
    # Sample some expiries to show strike coverage
    sample_expiries = sorted(strikes_by_expiry.keys())[:10]  # First 10 expiries
    
    print("\nSample strike coverage by expiry:")
    for expiry in sample_expiries:
        strikes = sorted(strikes_by_expiry[expiry])
        print(f"\n{expiry}:")
        print(f"  Number of strikes: {len(strikes)}")
        if strikes:
            print(f"  Strike range: ${min(strikes):.2f} - ${max(strikes):.2f}")
            print(f"  Strike spacing: ${(strikes[1] - strikes[0]):.2f}" if len(strikes) > 1 else "  N/A")
            # Show first few strikes
            print(f"  Sample strikes: {[f'${s:.2f}' for s in strikes[:5]]}...")
    
    # Analyze daily coverage
    print("\n\n=== DAILY STRIKE COVERAGE ===\n")
    
    # Sample some recent dates
    recent_dates = sorted(options_by_date_expiry.keys())[-30:]  # Last 30 days with data
    
    coverage_stats = []
    for date in recent_dates:
        expiries = options_by_date_expiry[date]
        futures_price = futures_prices_by_date.get(date, 2.5)  # Default to $2.50
        
        for expiry, strikes in expiries.items():
            if len(strikes) >= 3:  # Need at least 3 strikes for good coverage
                strikes_list = sorted(strikes)
                
                # Find strikes around the money (within 20% of futures price)
                atm_strikes = [s for s in strikes_list if 0.8 * futures_price <= s <= 1.2 * futures_price]
                
                # For 15-delta, we typically need strikes 5-15% OTM
                otm_15delta_range = [s for s in strikes_list if 1.05 * futures_price <= s <= 1.15 * futures_price]
                
                coverage_stats.append({
                    'date': date,
                    'expiry': expiry,
                    'futures_price': futures_price,
                    'total_strikes': len(strikes_list),
                    'atm_strikes': len(atm_strikes),
                    'otm_15delta_strikes': len(otm_15delta_range),
                    'min_strike': min(strikes_list),
                    'max_strike': max(strikes_list)
                })
    
    # Report coverage statistics
    if coverage_stats:
        avg_total_strikes = sum(s['total_strikes'] for s in coverage_stats) / len(coverage_stats)
        avg_atm_strikes = sum(s['atm_strikes'] for s in coverage_stats) / len(coverage_stats)
        avg_otm_strikes = sum(s['otm_15delta_strikes'] for s in coverage_stats) / len(coverage_stats)
        
        print(f"Average strikes per expiry: {avg_total_strikes:.1f}")
        print(f"Average ATM strikes (±20%): {avg_atm_strikes:.1f}")
        print(f"Average 15-delta range strikes (5-15% OTM): {avg_otm_strikes:.1f}")
        
        # Show some examples
        print("\nRecent examples of strike coverage:")
        for stat in coverage_stats[-5:]:  # Last 5 examples
            print(f"\n{stat['date']} - {stat['expiry']}:")
            print(f"  Futures: ${stat['futures_price']:.2f}")
            print(f"  Total strikes: {stat['total_strikes']}")
            print(f"  ATM strikes: {stat['atm_strikes']}")
            print(f"  15-delta range strikes: {stat['otm_15delta_strikes']}")
            print(f"  Strike range: ${stat['min_strike']:.2f} - ${stat['max_strike']:.2f}")
    
    # Check specific dates from target output
    print("\n\n=== TARGET DATE ANALYSIS (Dec 2021 - Mar 2022) ===\n")
    
    target_dates = [
        datetime(2021, 12, 1).date(),
        datetime(2022, 1, 3).date(),
        datetime(2022, 2, 1).date(),
        datetime(2022, 3, 1).date()
    ]
    
    for target_date in target_dates:
        if target_date in options_by_date_expiry:
            print(f"\n{target_date}:")
            expiries = options_by_date_expiry[target_date]
            futures_price = futures_prices_by_date.get(target_date, 2.5)
            print(f"  Futures price: ${futures_price:.2f}")
            
            for expiry, strikes in sorted(expiries.items()):
                strikes_list = sorted(strikes)
                print(f"  {expiry}: {len(strikes_list)} strikes")
                if len(strikes_list) <= 10:
                    print(f"    Strikes: {[f'${s:.2f}' for s in strikes_list]}")
                else:
                    print(f"    Range: ${min(strikes_list):.2f} - ${max(strikes_list):.2f}")
                    # Show strikes around 15-delta level (5-15% OTM)
                    otm_strikes = [s for s in strikes_list if 1.05 * futures_price <= s <= 1.15 * futures_price]
                    if otm_strikes:
                        print(f"    15-delta range: {[f'${s:.2f}' for s in otm_strikes]}")
    
    print("\n=== CONCLUSION ===")
    print("\nBased on the analysis, we can determine if there's sufficient strike coverage")
    print("for 15-delta option selection (typically 5-15% out-of-the-money).")

if __name__ == "__main__":
    analyze_strike_coverage()