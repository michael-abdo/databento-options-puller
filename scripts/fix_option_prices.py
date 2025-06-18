#!/usr/bin/env python3
"""
Fix option price generation in mock mode to match expected output format
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_realistic_option_prices(symbol, start_date, end_date, futures_price=2.5):
    """
    Generate realistic option prices based on Black-Scholes-like behavior
    """
    # Parse dates
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Extract strike from symbol (e.g., "OHG2 C00325" -> 3.25)
    try:
        parts = symbol.split(' ')
        strike_str = parts[1][1:]  # Remove 'C' or 'P'
        strike = float(strike_str) / 100.0  # Convert cents to dollars
    except:
        strike = 3.0  # Default strike
    
    # Calculate time to expiry (assume 2 months for simplicity)
    days_to_expiry = 60
    
    # Generate daily prices
    prices = []
    current_date = start_date
    
    while current_date <= end_date:
        # Skip weekends
        if current_date.weekday() < 5:
            # Calculate days remaining
            days_remaining = max(1, days_to_expiry - (current_date - start_date).days)
            time_to_expiry = days_remaining / 365.0
            
            # Simple option pricing approximation
            # For 15-delta options, they should be out-of-the-money
            moneyness = futures_price / strike
            
            # Base option value calculation
            if moneyness > 1.0:  # In the money
                intrinsic = futures_price - strike
                time_value = 0.1 * np.sqrt(time_to_expiry)
            else:  # Out of the money
                intrinsic = 0
                # Time value decreases as we approach expiry
                # For 15-delta options, typical values range from 0.05 to 0.20
                time_value = 0.15 * np.sqrt(time_to_expiry) * (strike / futures_price)
            
            # Add some randomness
            volatility = np.random.normal(1.0, 0.1)
            option_price = max(0.01, (intrinsic + time_value) * volatility)
            
            # Round to 2 decimal places
            option_price = round(option_price, 2)
            
            prices.append({
                'date': current_date,
                'close': option_price,
                'open': option_price * 0.98,
                'high': option_price * 1.02,
                'low': option_price * 0.97,
                'volume': np.random.randint(10, 1000)
            })
        
        current_date += timedelta(days=1)
    
    return pd.DataFrame(prices)

# Test the function
if __name__ == "__main__":
    # Test with example option
    df = generate_realistic_option_prices(
        "OHG2 C00325",
        "2021-12-01",
        "2022-01-31",
        futures_price=2.5
    )
    
    print("Sample option prices:")
    print(df.head(10))
    print(f"\nGenerated {len(df)} price points")
    print(f"Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")