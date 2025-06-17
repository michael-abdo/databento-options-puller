"""
Unit tests for the DeltaCalculator class.
Tests Black-Scholes calculations, delta targeting, and volatility estimation.
"""

import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.delta_calculator import DeltaCalculator


class TestDeltaCalculator(unittest.TestCase):
    """Test suite for DeltaCalculator functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calc = DeltaCalculator(risk_free_rate=0.05)
        
        # Common test parameters
        self.spot_price = 100.0
        self.strike_price = 100.0
        self.time_to_expiry = 0.25  # 3 months
        self.volatility = 0.30  # 30%
        
    def test_initialization(self):
        """Test calculator initialization."""
        calc = DeltaCalculator(risk_free_rate=0.03)
        self.assertEqual(calc.risk_free_rate, 0.03)
        self.assertEqual(len(calc.cache), 0)
    
    def test_delta_calculation_basic(self):
        """Test basic delta calculation."""
        # ATM call should have delta around 0.5
        delta = self.calc.calculate_delta(
            self.spot_price, self.strike_price, 
            self.time_to_expiry, self.volatility
        )
        self.assertAlmostEqual(delta, 0.5, delta=0.1)
        
        # ITM call should have higher delta
        itm_delta = self.calc.calculate_delta(
            self.spot_price, 90.0, 
            self.time_to_expiry, self.volatility
        )
        self.assertGreater(itm_delta, 0.7)
        
        # OTM call should have lower delta
        otm_delta = self.calc.calculate_delta(
            self.spot_price, 110.0, 
            self.time_to_expiry, self.volatility
        )
        self.assertLess(otm_delta, 0.3)
    
    def test_delta_edge_cases(self):
        """Test delta calculation edge cases."""
        # Zero spot price
        delta = self.calc.calculate_delta(0, 100, 0.25, 0.30)
        self.assertEqual(delta, 0.0)
        
        # Zero time to expiry
        delta = self.calc.calculate_delta(110, 100, 0, 0.30)
        self.assertEqual(delta, 1.0)  # ITM at expiry
        
        delta = self.calc.calculate_delta(90, 100, 0, 0.30)
        self.assertEqual(delta, 0.0)  # OTM at expiry
        
        # Zero volatility
        delta = self.calc.calculate_delta(100, 100, 0.25, 0)
        self.assertIsInstance(delta, float)
        
    def test_option_price_calculation(self):
        """Test Black-Scholes option pricing."""
        # ATM option
        price = self.calc.calculate_option_price(
            self.spot_price, self.strike_price,
            self.time_to_expiry, self.volatility
        )
        self.assertGreater(price, 0)
        self.assertLess(price, self.spot_price)
        
        # Deep ITM should be close to intrinsic value
        itm_price = self.calc.calculate_option_price(
            self.spot_price, 80.0,
            self.time_to_expiry, self.volatility
        )
        intrinsic = self.spot_price - 80.0
        self.assertGreater(itm_price, intrinsic)
        
        # OTM should have only time value
        otm_price = self.calc.calculate_option_price(
            self.spot_price, 120.0,
            self.time_to_expiry, self.volatility
        )
        self.assertGreater(otm_price, 0)
        self.assertLess(otm_price, 5.0)
    
    def test_put_option_calculations(self):
        """Test put option calculations."""
        # ATM put delta should be around -0.5
        put_delta = self.calc.calculate_delta(
            self.spot_price, self.strike_price,
            self.time_to_expiry, self.volatility,
            option_type='put'
        )
        self.assertAlmostEqual(put_delta, -0.5, delta=0.1)
        
        # ITM put (strike > spot) should have more negative delta
        itm_put_delta = self.calc.calculate_delta(
            self.spot_price, 110.0,
            self.time_to_expiry, self.volatility,
            option_type='put'
        )
        self.assertLess(itm_put_delta, -0.7)
    
    def test_find_target_delta_strike(self):
        """Test finding strike with target delta."""
        strikes = [80, 85, 90, 95, 100, 105, 110, 115, 120]
        target_delta = 0.15
        
        best_strike, actual_delta = self.calc.find_target_delta_strike(
            self.spot_price, strikes,
            self.time_to_expiry, self.volatility,
            target_delta
        )
        
        # Should find a strike with delta close to target
        self.assertIn(best_strike, strikes)
        self.assertAlmostEqual(actual_delta, target_delta, delta=0.05)
        
        # For 15-delta, strike should be OTM
        self.assertGreater(best_strike, self.spot_price)
    
    def test_find_target_delta_edge_cases(self):
        """Test edge cases in strike selection."""
        # Empty strikes list
        strike, delta = self.calc.find_target_delta_strike(
            100, [], 0.25, 0.30, 0.15
        )
        self.assertEqual(strike, 100)
        self.assertEqual(delta, 0.0)
        
        # Single strike
        strike, delta = self.calc.find_target_delta_strike(
            100, [110], 0.25, 0.30, 0.15
        )
        self.assertEqual(strike, 110)
    
    def test_implied_volatility_estimation(self):
        """Test implied volatility calculation."""
        # Generate a known option price
        known_vol = 0.25
        option_price = self.calc.calculate_option_price(
            self.spot_price, self.strike_price,
            self.time_to_expiry, known_vol
        )
        
        # Estimate IV from the price
        estimated_vol = self.calc.estimate_implied_volatility(
            option_price, self.spot_price, self.strike_price,
            self.time_to_expiry
        )
        
        # Should recover the original volatility
        self.assertAlmostEqual(estimated_vol, known_vol, delta=0.01)
    
    def test_time_to_expiry_calculation(self):
        """Test time to expiry calculations."""
        current_date = datetime(2023, 1, 1)
        expiry_date = datetime(2023, 4, 1)  # ~3 months
        
        tte = self.calc.calculate_time_to_expiry(current_date, expiry_date)
        
        # Should be approximately 0.25 years
        self.assertGreater(tte, 0.2)
        self.assertLess(tte, 0.3)
        
        # String dates
        tte_str = self.calc.calculate_time_to_expiry("2023-01-01", "2023-04-01")
        self.assertAlmostEqual(tte, tte_str, delta=0.01)
    
    def test_historical_volatility_estimation(self):
        """Test volatility estimation from price history."""
        # Create synthetic price data with known volatility
        dates = pd.date_range(start='2023-01-01', periods=60, freq='D')
        np.random.seed(42)
        
        # Generate returns with 30% annual volatility
        daily_vol = 0.30 / np.sqrt(252)
        returns = np.random.normal(0, daily_vol, len(dates))
        prices = 100 * np.exp(np.cumsum(returns))
        
        price_df = pd.DataFrame({
            'date': dates,
            'close': prices
        })
        
        estimated_vol = self.calc.estimate_volatility_from_history(price_df)
        
        # Should be roughly 30%
        self.assertGreater(estimated_vol, 0.20)
        self.assertLess(estimated_vol, 0.40)
    
    def test_delta_validation(self):
        """Test delta validation logic."""
        # Valid ATM delta
        is_valid = self.calc.validate_delta_calculation(
            100, 100, 0.52, 0.25
        )
        self.assertTrue(is_valid)
        
        # Invalid delta (out of range)
        is_valid = self.calc.validate_delta_calculation(
            100, 100, 1.5, 0.25
        )
        self.assertFalse(is_valid)
        
        # Deep ITM with low delta (suspicious)
        is_valid = self.calc.validate_delta_calculation(
            100, 70, 0.2, 0.25
        )
        self.assertFalse(is_valid)
        
        # Deep OTM with high delta (suspicious)
        is_valid = self.calc.validate_delta_calculation(
            100, 130, 0.8, 0.25
        )
        self.assertFalse(is_valid)
    
    def test_realistic_oh_futures_scenario(self):
        """Test with realistic OH futures parameters."""
        # OH futures scenario
        spot = 2.50  # $2.50/gallon
        strikes = [2.00, 2.25, 2.50, 2.75, 3.00, 3.25, 3.50]
        time_to_expiry = 60 / 252  # 60 trading days
        volatility = 0.35  # 35% vol typical for energy
        
        # Find 15-delta strike
        target_strike, actual_delta = self.calc.find_target_delta_strike(
            spot, strikes, time_to_expiry, volatility, 0.15
        )
        
        # Should select an OTM strike
        self.assertGreater(target_strike, spot)
        self.assertAlmostEqual(actual_delta, 0.15, delta=0.05)
        
        # Calculate option price
        option_price = self.calc.calculate_option_price(
            spot, target_strike, time_to_expiry, volatility
        )
        
        # Should be reasonably priced
        self.assertGreater(option_price, 0.01)
        self.assertLess(option_price, 0.50)  # Less than 50 cents
    
    def test_greeks_consistency(self):
        """Test that Greeks calculations are consistent."""
        # Small bump in spot price
        bump = 0.01
        
        # Calculate delta using definition
        price_up = self.calc.calculate_option_price(
            self.spot_price + bump, self.strike_price,
            self.time_to_expiry, self.volatility
        )
        price_down = self.calc.calculate_option_price(
            self.spot_price - bump, self.strike_price,
            self.time_to_expiry, self.volatility
        )
        
        numerical_delta = (price_up - price_down) / (2 * bump)
        
        # Calculate analytical delta
        analytical_delta = self.calc.calculate_delta(
            self.spot_price, self.strike_price,
            self.time_to_expiry, self.volatility
        )
        
        # Should be very close
        self.assertAlmostEqual(numerical_delta, analytical_delta, places=3)


class TestDeltaCalculatorIntegration(unittest.TestCase):
    """Integration tests for DeltaCalculator with realistic scenarios."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.calc = DeltaCalculator(risk_free_rate=0.05)
    
    def test_monthly_roll_scenario(self):
        """Test a complete monthly roll scenario."""
        # Simulate finding 15-delta options for multiple months
        spot_prices = [2.45, 2.50, 2.55, 2.48]  # Varying spot prices
        volatilities = [0.30, 0.32, 0.35, 0.28]  # Varying vols
        
        results = []
        
        for i, (spot, vol) in enumerate(zip(spot_prices, volatilities)):
            # Generate realistic strikes
            strikes = [spot + 0.25 * j for j in range(-4, 8)]
            time_to_expiry = (60 - i * 30) / 252  # Decreasing time
            
            strike, delta = self.calc.find_target_delta_strike(
                spot, strikes, time_to_expiry, vol, 0.15
            )
            
            price = self.calc.calculate_option_price(
                spot, strike, time_to_expiry, vol
            )
            
            results.append({
                'month': i + 1,
                'spot': spot,
                'strike': strike,
                'delta': delta,
                'price': price,
                'volatility': vol
            })
        
        # Verify results make sense
        for result in results:
            self.assertAlmostEqual(result['delta'], 0.15, delta=0.05)
            self.assertGreater(result['strike'], result['spot'])
            self.assertGreater(result['price'], 0)
    
    def test_volatility_smile_effect(self):
        """Test handling of volatility smile."""
        spot = 100
        strikes = range(80, 125, 5)
        time_to_expiry = 0.25
        
        # Simulate volatility smile (higher vol for OTM options)
        vols = []
        for strike in strikes:
            moneyness = strike / spot
            smile_vol = 0.20 + 0.1 * abs(np.log(moneyness))
            vols.append(smile_vol)
        
        # Calculate deltas with smile
        deltas = []
        for strike, vol in zip(strikes, vols):
            delta = self.calc.calculate_delta(
                spot, strike, time_to_expiry, vol
            )
            deltas.append(delta)
        
        # Verify monotonicity (deltas should decrease with strike)
        for i in range(1, len(deltas)):
            self.assertLess(deltas[i], deltas[i-1])


if __name__ == '__main__':
    unittest.main()