#!/usr/bin/env python3
"""
Focused analysis of strike coverage for the target period (Dec 2021 - Mar 2022).
"""

import json
from collections import defaultdict
from datetime import datetime
import os

def analyze_target_period_coverage():
    """Analyze strike coverage specifically for Dec 2021 - Mar 2022."""
    
    data_file = "/Users/Mike/Desktop/programming/2_proposals/other/databento-options-puller/data/glbx-mdp3-20100606-20250617.ohlcv-1d.json"
    
    print("Analyzing strike coverage for target period (Dec 2021 - Mar 2022)...")
    
    # Target period
    start_date = datetime(2021, 12, 1).date()
    end_date = datetime(2022, 3, 31).date()
    
    # Track data
    options_data = defaultdict(lambda: defaultdict(list))  # date -> expiry -> list of (strike, price)
    futures_prices = {}  # date -> price
    
    # Read and process the file
    with open(data_file, 'r') as f:
        for line in f:
            try:
                record = json.loads(line.strip())
                
                # Get symbol and timestamp
                symbol = record.get('symbol', '')
                ts_event = record.get('hd', {}).get('ts_event')
                close_price = record.get('close', 0)
                
                if not ts_event:
                    continue
                
                # Parse timestamp to date
                try:
                    timestamp = datetime.fromisoformat(ts_event.replace('Z', '+00:00'))
                    date = timestamp.date()
                except:
                    continue
                
                # Skip if outside target period
                if date < start_date or date > end_date:
                    continue
                
                # Track futures prices
                if symbol.startswith('HO') and ' ' not in symbol:
                    try:
                        price = float(close_price)
                        if price > 0:
                            futures_prices[date] = price
                    except:
                        pass
                
                # Track options
                if symbol.startswith('OH') and ' C' in symbol:
                    parts = symbol.split(' ')
                    if len(parts) == 2:
                        expiry_code = parts[0]
                        strike_part = parts[1]
                        
                        if strike_part.startswith('C'):
                            try:
                                strike_value = int(strike_part[1:])
                                strike_price = strike_value / 10000.0
                                option_price = float(close_price)
                                
                                options_data[date][expiry_code].append((strike_price, option_price))
                            except:
                                pass
                    
            except json.JSONDecodeError:
                continue
    
    # Analyze the data
    print(f"\nPeriod analyzed: {start_date} to {end_date}")
    print(f"Days with futures data: {len(futures_prices)}")
    print(f"Days with options data: {len(options_data)}")
    
    # Check first trading day of each month
    key_dates = [
        (datetime(2021, 12, 1).date(), "December 2021", "OHF2"),  # Target Feb 2022
        (datetime(2022, 1, 3).date(), "January 2022", "OHG2"),   # Target Mar 2022 (Jan 1 is holiday)
        (datetime(2022, 2, 1).date(), "February 2022", "OHH2"),  # Target Apr 2022
        (datetime(2022, 3, 1).date(), "March 2022", "OHJ2"),     # Target May 2022
    ]
    
    print("\n=== STRIKE COVERAGE ON KEY DATES ===")
    
    for check_date, month_name, target_expiry in key_dates:
        print(f"\n{month_name} - First Trading Day: {check_date}")
        
        # Get futures price
        futures_price = futures_prices.get(check_date, 0)
        if futures_price == 0:
            # Try nearby dates
            for i in range(1, 5):
                alt_date = datetime.combine(check_date, datetime.min.time())
                alt_date = (alt_date + datetime.timedelta(days=i)).date()
                if alt_date in futures_prices:
                    futures_price = futures_prices[alt_date]
                    print(f"  Using futures price from {alt_date}")
                    break
        
        if futures_price > 0:
            print(f"  Futures price: ${futures_price:.4f}")
        else:
            print(f"  Futures price: Not found - estimating $2.50")
            futures_price = 2.50
        
        # Get M+2 options
        if check_date in options_data and target_expiry in options_data[check_date]:
            strikes_data = sorted(options_data[check_date][target_expiry])
            strikes = [s[0] for s in strikes_data]
            
            print(f"\n  {target_expiry} Options Available:")
            print(f"    Number of strikes: {len(strikes)}")
            if strikes:
                print(f"    Strike range: ${min(strikes):.2f} - ${max(strikes):.2f}")
                
                # Find strikes in 15-delta range (typically 5-15% OTM)
                target_range_min = futures_price * 1.05
                target_range_max = futures_price * 1.15
                
                in_range_strikes = [(s, p) for s, p in strikes_data if target_range_min <= s <= target_range_max]
                
                print(f"    15-delta target range: ${target_range_min:.2f} - ${target_range_max:.2f}")
                print(f"    Strikes in target range: {len(in_range_strikes)}")
                
                if in_range_strikes:
                    print(f"    Available strikes in range:")
                    for strike, price in in_range_strikes[:5]:  # Show up to 5
                        print(f"      ${strike:.2f} (price: ${price:.4f})")
                
                # Show all strikes if few
                if len(strikes) <= 10:
                    print(f"    All strikes: {[f'${s:.2f}' for s in strikes]}")
        else:
            print(f"  No {target_expiry} options data found on {check_date}")
    
    # Check actual target options from final_output.csv
    print("\n\n=== TARGET OPTIONS FROM final_output.csv ===")
    target_options = [
        ("OHF2 C27800", 2.78),
        ("OHG2 C24500", 2.45),
        ("OHH2 C27000", 2.70),
        ("OHJ2 C30200", 3.02),
        ("OHK2 C35000", 3.50)
    ]
    
    for option_symbol, strike in target_options:
        expiry = option_symbol.split()[0]
        print(f"\n{option_symbol} (${strike:.2f}):")
        
        # Find dates where this option traded
        dates_found = []
        for date, expiries in options_data.items():
            if expiry in expiries:
                for s, p in expiries[expiry]:
                    if abs(s - strike) < 0.01:  # Match strike
                        dates_found.append((date, p))
        
        if dates_found:
            print(f"  Found on {len(dates_found)} days")
            print(f"  Date range: {min(dates_found)[0]} to {max(dates_found)[0]}")
            print(f"  Sample prices: {[f'${p:.4f}' for d, p in dates_found[:5]]}")
        else:
            print(f"  Not found in dataset")
    
    print("\n=== CONCLUSION ===")
    print("\nStrike coverage analysis complete. Key findings:")
    print("- Check if sufficient strikes exist in the 15-delta range (5-15% OTM)")
    print("- Verify that target options from final_output.csv are present in the data")

if __name__ == "__main__":
    analyze_target_period_coverage()