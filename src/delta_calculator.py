"""
Delta Calculator for options using Black-Scholes model.
Handles delta calculation, strike selection, and options mathematics.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import logging
from pathlib import Path
from scipy.stats import norm
from scipy.optimize import minimize_scalar
import warnings

# Add parent directory to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.date_utils import parse_date, count_trading_days
from utils.symbol_utils import parse_option_symbol, extract_strike
from utils.logging_config import get_logger

logger = get_logger('delta')

# Suppress scipy warnings for cleaner output
warnings.filterwarnings('ignore', category=RuntimeWarning)


class DeltaCalculator:
    """
    Black-Scholes options calculator with delta targeting.
    
    Handles:
    - Delta calculation for option pricing
    - Strike selection based on target delta
    - Volatility estimation
    - Greeks calculation
    """
    
    def __init__(self, risk_free_rate: float = 0.05):
        """
        Initialize delta calculator.
        
        Args:
            risk_free_rate: Risk-free interest rate (default 5%)
        """
        self.risk_free_rate = risk_free_rate
        self.cache = {}  # Cache for expensive calculations
        
        logger.info(f"Initialized DeltaCalculator with r={risk_free_rate:.2%}")
    
    def calculate_delta(self, spot_price: float, strike_price: float, 
                       time_to_expiry: float, volatility: float,
                       option_type: str = 'call') -> float:
        """
        Calculate option delta using Black-Scholes formula.
        
        Args:
            spot_price: Current price of underlying
            strike_price: Option strike price
            time_to_expiry: Time to expiry in years
            volatility: Implied volatility (annualized)
            option_type: 'call' or 'put'
            
        Returns:
            Delta value
        """
        # Input validation
        if spot_price <= 0:
            logger.warning(f"Invalid spot price: {spot_price}")
            return 0.0
        
        if time_to_expiry <= 0:
            logger.warning(f"Invalid time to expiry: {time_to_expiry}")
            return 1.0 if option_type == 'call' and spot_price > strike_price else 0.0
        
        if volatility <= 0:
            logger.warning(f"Invalid volatility: {volatility}")
            volatility = 0.01  # Minimum volatility
        
        try:
            # Black-Scholes d1 calculation
            d1 = (np.log(spot_price / strike_price) + 
                  (self.risk_free_rate + 0.5 * volatility ** 2) * time_to_expiry) / \
                 (volatility * np.sqrt(time_to_expiry))
            
            # Delta calculation
            if option_type.lower() == 'call':
                delta = norm.cdf(d1)
            elif option_type.lower() == 'put':
                delta = -norm.cdf(-d1)
            else:
                raise ValueError(f"Invalid option type: {option_type}")
            
            logger.debug(f"Delta calculation: S={spot_price:.2f}, K={strike_price:.2f}, "
                        f"T={time_to_expiry:.3f}, σ={volatility:.2%}, Δ={delta:.4f}")
            
            return float(delta)
            
        except Exception as e:
            logger.error(f"Delta calculation error: {e}")
            return 0.0
    
    def calculate_option_price(self, spot_price: float, strike_price: float,
                              time_to_expiry: float, volatility: float,
                              option_type: str = 'call') -> float:
        """
        Calculate option price using Black-Scholes formula.
        
        Args:
            spot_price: Current price of underlying
            strike_price: Option strike price
            time_to_expiry: Time to expiry in years
            volatility: Implied volatility
            option_type: 'call' or 'put'
            
        Returns:
            Option price
        """
        if time_to_expiry <= 0:
            # Intrinsic value at expiry
            if option_type.lower() == 'call':
                return max(0, spot_price - strike_price)
            else:
                return max(0, strike_price - spot_price)
        
        if volatility <= 0:
            volatility = 0.01
        
        try:
            # Black-Scholes calculation
            d1 = (np.log(spot_price / strike_price) + 
                  (self.risk_free_rate + 0.5 * volatility ** 2) * time_to_expiry) / \
                 (volatility * np.sqrt(time_to_expiry))
            
            d2 = d1 - volatility * np.sqrt(time_to_expiry)
            
            if option_type.lower() == 'call':
                price = (spot_price * norm.cdf(d1) - 
                        strike_price * np.exp(-self.risk_free_rate * time_to_expiry) * norm.cdf(d2))
            elif option_type.lower() == 'put':
                price = (strike_price * np.exp(-self.risk_free_rate * time_to_expiry) * norm.cdf(-d2) - 
                        spot_price * norm.cdf(-d1))
            else:
                raise ValueError(f"Invalid option type: {option_type}")
            
            return max(0.0, float(price))
            
        except Exception as e:
            logger.error(f"Option price calculation error: {e}")
            return 0.0
    
    def find_target_delta_strike(self, spot_price: float, available_strikes: List[float],
                                time_to_expiry: float, volatility: float,
                                target_delta: float = 0.15, option_type: str = 'call') -> Tuple[float, float]:
        """
        Find the strike price closest to target delta.
        
        Args:
            spot_price: Current underlying price
            available_strikes: List of available strike prices
            time_to_expiry: Time to expiry in years
            volatility: Implied volatility
            target_delta: Target delta value (default 0.15)
            option_type: 'call' or 'put'
            
        Returns:
            Tuple of (best_strike, actual_delta)
        """
        if not available_strikes:
            logger.error("No strikes provided")
            return spot_price, 0.0
        
        logger.info(f"Finding {target_delta:.2f} delta strike from {len(available_strikes)} options")
        logger.debug(f"Spot: ${spot_price:.2f}, T: {time_to_expiry:.3f}y, σ: {volatility:.2%}")
        
        best_strike = available_strikes[0]
        best_delta = 0.0
        best_distance = float('inf')
        
        # Calculate delta for each strike
        delta_results = []
        
        for strike in available_strikes:
            delta = self.calculate_delta(
                spot_price, strike, time_to_expiry, volatility, option_type
            )
            
            distance = abs(delta - target_delta)
            delta_results.append((strike, delta, distance))
            
            if distance < best_distance:
                best_distance = distance
                best_strike = strike
                best_delta = delta
        
        # Log all results for debugging
        logger.debug("Delta calculation results:")
        for strike, delta, distance in sorted(delta_results, key=lambda x: x[2]):
            marker = "*** SELECTED ***" if strike == best_strike else ""
            logger.debug(f"  Strike ${strike:.2f}: Δ={delta:.4f}, distance={distance:.4f} {marker}")
        
        logger.info(f"Selected strike ${best_strike:.2f} with delta {best_delta:.4f} "
                   f"(target: {target_delta:.2f}, distance: {best_distance:.4f})")
        
        return best_strike, best_delta
    
    def estimate_implied_volatility(self, option_price: float, spot_price: float,
                                   strike_price: float, time_to_expiry: float,
                                   option_type: str = 'call') -> float:
        """
        Estimate implied volatility from option price using Newton-Raphson.
        
        Args:
            option_price: Observed option price
            spot_price: Current underlying price
            strike_price: Option strike price
            time_to_expiry: Time to expiry in years
            option_type: 'call' or 'put'
            
        Returns:
            Implied volatility
        """
        if time_to_expiry <= 0 or option_price <= 0:
            return 0.30  # Default volatility
        
        def objective(vol):
            """Objective function: difference between calculated and market price."""
            if vol <= 0:
                return float('inf')
            
            calc_price = self.calculate_option_price(
                spot_price, strike_price, time_to_expiry, vol, option_type
            )
            return abs(calc_price - option_price)
        
        try:
            # Use scipy to find optimal volatility
            result = minimize_scalar(
                objective,
                bounds=(0.01, 5.0),  # 1% to 500% volatility
                method='bounded'
            )
            
            implied_vol = result.x
            
            # Sanity check
            if implied_vol < 0.01 or implied_vol > 2.0:
                logger.warning(f"Unusual implied volatility: {implied_vol:.2%}")
                implied_vol = np.clip(implied_vol, 0.01, 2.0)
            
            logger.debug(f"Implied volatility: {implied_vol:.2%} for price ${option_price:.2f}")
            
            return float(implied_vol)
            
        except Exception as e:
            logger.warning(f"IV calculation failed: {e}, using default 30%")
            return 0.30
    
    def calculate_time_to_expiry(self, current_date: Union[str, datetime], 
                                expiry_date: Union[str, datetime]) -> float:
        """
        Calculate time to expiry in years.
        
        Args:
            current_date: Current date
            expiry_date: Option expiry date
            
        Returns:
            Time to expiry in years
        """
        if isinstance(current_date, str):
            current_date = parse_date(current_date)
        if isinstance(expiry_date, str):
            expiry_date = parse_date(expiry_date)
        
        # Calculate trading days to expiry
        trading_days = count_trading_days(current_date, expiry_date)
        
        # Convert to years (assuming 252 trading days per year)
        time_to_expiry = trading_days / 252.0
        
        # Ensure minimum time
        time_to_expiry = max(time_to_expiry, 1/252)  # At least 1 trading day
        
        logger.debug(f"Time to expiry: {trading_days} trading days = {time_to_expiry:.4f} years")
        
        return time_to_expiry
    
    def estimate_volatility_from_history(self, price_history: pd.DataFrame,
                                        window_days: int = 30) -> float:
        """
        Estimate volatility from historical price data.
        
        Args:
            price_history: DataFrame with 'close' prices
            window_days: Number of days for volatility calculation
            
        Returns:
            Annualized volatility
        """
        if len(price_history) < 2:
            logger.warning("Insufficient price history for volatility calculation")
            return 0.30
        
        # Calculate returns
        prices = price_history['close'].tail(window_days)
        returns = np.log(prices / prices.shift(1)).dropna()
        
        if len(returns) < 2:
            return 0.30
        
        # Calculate volatility
        daily_vol = returns.std()
        annualized_vol = daily_vol * np.sqrt(252)  # Annualize
        
        # Sanity check
        annualized_vol = np.clip(annualized_vol, 0.05, 2.0)  # 5% to 200%
        
        logger.debug(f"Historical volatility ({len(returns)} days): {annualized_vol:.2%}")
        
        return float(annualized_vol)
    
    def validate_delta_calculation(self, spot_price: float, strike_price: float,
                                  calculated_delta: float, time_to_expiry: float) -> bool:
        """
        Validate that delta calculation makes sense.
        
        Args:
            spot_price: Underlying price
            strike_price: Option strike
            calculated_delta: Calculated delta
            time_to_expiry: Time to expiry
            
        Returns:
            True if delta is reasonable
        """
        # Basic sanity checks
        if not (0 <= calculated_delta <= 1):
            logger.warning(f"Delta {calculated_delta:.4f} outside valid range [0,1]")
            return False
        
        # ATM options should have delta around 0.5
        if abs(spot_price - strike_price) / spot_price < 0.01:  # Within 1%
            if abs(calculated_delta - 0.5) > 0.2:
                logger.warning(f"ATM delta {calculated_delta:.4f} far from 0.5")
                return False
        
        # Deep ITM calls should have high delta
        if strike_price < spot_price * 0.8:  # Deep ITM
            if calculated_delta < 0.7:
                logger.warning(f"Deep ITM delta {calculated_delta:.4f} too low")
                return False
        
        # Deep OTM calls should have low delta
        if strike_price > spot_price * 1.2:  # Deep OTM
            if calculated_delta > 0.3:
                logger.warning(f"Deep OTM delta {calculated_delta:.4f} too high")
                return False
        
        return True


def main():
    """Test the delta calculator."""
    from utils.logging_config import setup_logging
    
    # Set up logging
    setup_logging()
    
    # Create calculator
    calc = DeltaCalculator()
    
    # Test parameters
    spot = 2.50
    strikes = [2.00, 2.25, 2.50, 2.75, 3.00, 3.25, 3.50]
    time_to_expiry = 60 / 252  # 60 trading days
    volatility = 0.30  # 30%
    
    logger.info("Testing delta calculation")
    logger.info(f"Spot: ${spot:.2f}, Time: {time_to_expiry:.3f}y, Vol: {volatility:.1%}")
    
    # Calculate deltas for all strikes
    logger.info("Strike   Delta    Price")
    logger.info("-" * 25)
    for strike in strikes:
        delta = calc.calculate_delta(spot, strike, time_to_expiry, volatility)
        price = calc.calculate_option_price(spot, strike, time_to_expiry, volatility)
        logger.info(f"${strike:.2f}   {delta:.4f}   ${price:.3f}")
    
    # Test target delta selection
    target_delta = 0.15
    best_strike, actual_delta = calc.find_target_delta_strike(
        spot, strikes, time_to_expiry, volatility, target_delta
    )
    
    logger.info(f"Target delta: {target_delta:.2f}")
    logger.info(f"Selected strike: ${best_strike:.2f} (delta: {actual_delta:.4f})")
    
    # Test implied volatility
    option_price = 0.10
    strike = 2.75
    implied_vol = calc.estimate_implied_volatility(
        option_price, spot, strike, time_to_expiry
    )
    
    logger.info("Implied volatility test:")
    logger.info(f"Option price: ${option_price:.2f}, Strike: ${strike:.2f}")
    logger.info(f"Implied vol: {implied_vol:.2%}")


if __name__ == "__main__":
    main()