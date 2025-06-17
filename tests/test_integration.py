"""
Integration tests for the complete databento options system.
Tests the full pipeline from data fetching to output generation.
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.databento_client import DatabentoBridge
from src.futures_manager import FuturesManager
from src.options_manager import OptionsManager
from src.option_generator import OptionGenerator
from main import DatabentoOptionsPuller


class TestDatabentoBridge(unittest.TestCase):
    """Test Databento API bridge with mocked responses."""
    
    def setUp(self):
        """Set up test environment with mocked API."""
        self.bridge = DatabentoBridge(api_key="test_key")
        
        # Mock the databento client
        self.bridge.client = Mock()
    
    def test_fetch_futures_data(self):
        """Test futures data fetching."""
        # Mock response
        mock_data = pd.DataFrame({
            'ts_event': pd.date_range('2021-12-01', periods=10, freq='D'),
            'close': np.random.uniform(2.4, 2.6, 10),
            'open': np.random.uniform(2.4, 2.6, 10),
            'high': np.random.uniform(2.5, 2.7, 10),
            'low': np.random.uniform(2.3, 2.5, 10),
            'volume': np.random.randint(1000, 5000, 10)
        })
        
        self.bridge.client.timeseries.get_range.return_value = mock_data
        
        # Test fetch
        result = self.bridge.fetch_futures_data(
            'OH',
            datetime(2021, 12, 1),
            datetime(2021, 12, 10)
        )
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 10)
        self.assertIn('close', result.columns)
    
    def test_fetch_options_chain(self):
        """Test options chain fetching."""
        # Mock response with multiple strikes
        mock_chain = []
        for strike in [2.25, 2.50, 2.75, 3.00, 3.25]:
            mock_chain.append({
                'symbol': f'OHF2 C{int(strike*10000)}',
                'strike_price': strike,
                'expiration': '2022-01-21',
                'option_type': 'C',
                'close': np.random.uniform(0.05, 0.30)
            })
        
        mock_df = pd.DataFrame(mock_chain)
        self.bridge.client.timeseries.get_range.return_value = mock_df
        
        # Test fetch
        chain = self.bridge.fetch_options_chain('OH', 'F2', datetime(2021, 12, 1))
        
        self.assertIsInstance(chain, list)
        self.assertEqual(len(chain), 5)
        self.assertEqual(chain[0]['strike'], 2.25)
    
    def test_error_handling(self):
        """Test API error handling."""
        # Mock API error
        self.bridge.client.timeseries.get_range.side_effect = Exception("API Error")
        
        # Should handle gracefully
        result = self.bridge.fetch_futures_data(
            'OH',
            datetime(2021, 12, 1),
            datetime(2021, 12, 10)
        )
        
        self.assertIsNone(result)


class TestFuturesManager(unittest.TestCase):
    """Test futures contract management."""
    
    def setUp(self):
        """Set up test environment."""
        self.manager = FuturesManager()
        
        # Mock bridge
        self.manager.bridge = Mock()
    
    def test_get_front_month_code(self):
        """Test front month contract determination."""
        # Test various dates
        test_cases = [
            (datetime(2022, 1, 15), 'G2'),  # Jan -> Feb (G)
            (datetime(2022, 2, 20), 'H2'),  # Feb -> Mar (H)
            (datetime(2022, 11, 15), 'Z2'), # Nov -> Dec (Z)
            (datetime(2022, 12, 20), 'F3'), # Dec -> Jan (F)
        ]
        
        for date, expected in test_cases:
            result = self.manager.get_front_month_code(date)
            self.assertEqual(result, expected)
    
    def test_get_expiry_date(self):
        """Test expiry date calculation."""
        # Test known expiry
        expiry = self.manager.get_expiry_date('F2', 2022)
        
        self.assertEqual(expiry.month, 1)  # January
        self.assertEqual(expiry.year, 2022)
        self.assertLessEqual(expiry.day, 31)
    
    def test_continuous_contract_building(self):
        """Test building continuous contract series."""
        # Mock individual contract data
        mock_data = {
            'F2': pd.DataFrame({
                'date': pd.date_range('2022-01-01', '2022-01-20', freq='D'),
                'close': np.random.uniform(2.4, 2.5, 20)
            }),
            'G2': pd.DataFrame({
                'date': pd.date_range('2022-01-21', '2022-02-20', freq='D'),
                'close': np.random.uniform(2.5, 2.6, 31)
            })
        }
        
        def mock_fetch(symbol, start, end):
            for code, data in mock_data.items():
                if code in symbol:
                    mask = (data['date'] >= start) & (data['date'] <= end)
                    return data[mask]
            return pd.DataFrame()
        
        self.manager.bridge.fetch_futures_data = mock_fetch
        
        # Test continuous series
        result = self.manager.get_continuous_futures(
            datetime(2022, 1, 1),
            datetime(2022, 2, 20)
        )
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertGreater(len(result), 40)


class TestOptionsManager(unittest.TestCase):
    """Test options contract management."""
    
    def setUp(self):
        """Set up test environment."""
        self.manager = OptionsManager()
        self.manager.bridge = Mock()
        self.manager.delta_calc = Mock()
    
    def test_find_15_delta_option(self):
        """Test finding 15-delta option."""
        # Mock options chain
        mock_chain = [
            {'symbol': 'OHF2 C22500', 'strike': 2.25},
            {'symbol': 'OHF2 C25000', 'strike': 2.50},
            {'symbol': 'OHF2 C27500', 'strike': 2.75},
            {'symbol': 'OHF2 C30000', 'strike': 3.00},
        ]
        
        self.manager.bridge.fetch_options_chain.return_value = mock_chain
        
        # Mock delta calculations
        self.manager.delta_calc.find_target_delta_strike.return_value = (2.75, 0.148)
        
        # Test finding option
        result = self.manager.find_15_delta_option(
            'F2',
            datetime(2021, 12, 1),
            spot_price=2.50,
            volatility=0.30
        )
        
        self.assertEqual(result['symbol'], 'OHF2 C27500')
        self.assertEqual(result['strike'], 2.75)
        self.assertAlmostEqual(result['delta'], 0.148, places=3)
    
    def test_get_option_history(self):
        """Test fetching option price history."""
        # Mock price data
        mock_prices = pd.DataFrame({
            'date': pd.date_range('2021-12-01', periods=20, freq='D'),
            'close': np.random.uniform(0.10, 0.30, 20)
        })
        
        self.manager.bridge.fetch_option_data.return_value = mock_prices
        
        # Test fetch
        result = self.manager.get_option_history(
            'OHF2 C27500',
            datetime(2021, 12, 1),
            datetime(2021, 12, 20)
        )
        
        self.assertEqual(len(result), 20)
        self.assertIn('close', result.columns)


class TestOptionGenerator(unittest.TestCase):
    """Test option data generation logic."""
    
    def setUp(self):
        """Set up test environment."""
        self.generator = OptionGenerator()
        
        # Create mock example data
        self.example_data = pd.DataFrame({
            'timestamp': ['12/1/21', '12/2/21', '1/3/22', '2/1/22'],
            'OHF2 C27800': [0.12, 0.11, np.nan, np.nan],
            'OHG2 C24500': [np.nan, np.nan, 4.11, np.nan],
            'OHH2 C27000': [np.nan, np.nan, np.nan, 11.62]
        })
    
    def test_generate_matching_output(self):
        """Test generating output matching example format."""
        # Mock managers
        mock_futures_mgr = Mock()
        mock_options_mgr = Mock()
        
        # Mock futures data
        mock_futures_mgr.get_continuous_futures.return_value = pd.DataFrame({
            'date': pd.to_datetime(['2021-12-01', '2021-12-02', '2022-01-03', '2022-02-01']),
            'close': [2.45, 2.46, 2.50, 2.55]
        })
        
        # Mock options data
        def mock_find_option(month_code, date, **kwargs):
            option_map = {
                'F2': {'symbol': 'OHF2 C27800', 'strike': 2.78, 'delta': 0.15},
                'G2': {'symbol': 'OHG2 C24500', 'strike': 2.45, 'delta': 0.15},
                'H2': {'symbol': 'OHH2 C27000', 'strike': 2.70, 'delta': 0.15}
            }
            return option_map.get(month_code, None)
        
        mock_options_mgr.find_15_delta_option = mock_find_option
        
        # Mock option histories
        def mock_history(symbol, start, end):
            if 'F2' in symbol:
                return pd.DataFrame({
                    'date': pd.to_datetime(['2021-12-01', '2021-12-02']),
                    'close': [0.12, 0.11]
                })
            elif 'G2' in symbol:
                return pd.DataFrame({
                    'date': pd.to_datetime(['2022-01-03']),
                    'close': [4.11]
                })
            elif 'H2' in symbol:
                return pd.DataFrame({
                    'date': pd.to_datetime(['2022-02-01']),
                    'close': [11.62]
                })
            return pd.DataFrame()
        
        mock_options_mgr.get_option_history = mock_history
        
        # Generate output
        self.generator.futures_mgr = mock_futures_mgr
        self.generator.options_mgr = mock_options_mgr
        
        result = self.generator.generate(
            datetime(2021, 12, 1),
            datetime(2022, 2, 1)
        )
        
        # Verify structure matches example
        self.assertIn('timestamp', result.columns)
        self.assertIn('OHF2 C27800', result.columns)
        self.assertEqual(len(result), 4)


class TestMainPuller(unittest.TestCase):
    """Test the main DatabentoOptionsPuller class."""
    
    @patch('src.databento_client.databento')
    def test_full_pipeline(self, mock_databento):
        """Test complete pipeline execution."""
        # Create puller instance
        puller = DatabentoOptionsPuller(
            api_key="test_key",
            config={'target_delta': 0.15}
        )
        
        # Mock all external calls
        puller.generator = Mock()
        mock_output = pd.DataFrame({
            'timestamp': ['12/1/21', '12/2/21'],
            'Futures_Price': [2.45, 2.46],
            'OHF2 C27800': [0.12, 0.11]
        })
        puller.generator.generate.return_value = mock_output
        
        # Run pipeline
        result = puller.run(
            start_date=datetime(2021, 12, 1),
            end_date=datetime(2021, 12, 31)
        )
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        self.assertIn('Futures_Price', result.columns)
    
    def test_config_loading(self):
        """Test configuration handling."""
        config = {
            'target_delta': 0.20,
            'volatility_adjustment': 1.1,
            'risk_free_rate': 0.04
        }
        
        puller = DatabentoOptionsPuller(
            api_key="test_key",
            config=config
        )
        
        self.assertEqual(puller.config['target_delta'], 0.20)
        self.assertEqual(puller.delta_calc.risk_free_rate, 0.04)
    
    def test_save_output(self):
        """Test output saving functionality."""
        puller = DatabentoOptionsPuller(api_key="test_key")
        
        # Create sample output
        output = pd.DataFrame({
            'timestamp': ['12/1/21', '12/2/21'],
            'Futures_Price': [2.45, 2.46],
            'OHF2 C27800': [0.12, 0.11]
        })
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name
        
        puller.save_output(output, output_path)
        
        # Verify file was created
        self.assertTrue(os.path.exists(output_path))
        
        # Read back and verify
        loaded = pd.read_csv(output_path)
        self.assertEqual(len(loaded), 2)
        self.assertIn('timestamp', loaded.columns)
        
        # Clean up
        os.unlink(output_path)


class TestEndToEnd(unittest.TestCase):
    """End-to-end integration tests."""
    
    def test_realistic_scenario(self):
        """Test a realistic usage scenario."""
        # This would require actual API access or comprehensive mocking
        # For now, we'll test the integration of components
        
        # Create all components
        from src.delta_calculator import DeltaCalculator
        from src.example_analyzer import ExampleAnalyzer
        from src.output_validator import OutputValidator
        
        delta_calc = DeltaCalculator()
        analyzer = ExampleAnalyzer()
        validator = OutputValidator()
        
        # Test delta calculation
        delta = delta_calc.calculate_delta(
            spot_price=2.50,
            strike_price=2.75,
            time_to_expiry=60/252,
            volatility=0.30
        )
        
        self.assertGreater(delta, 0)
        self.assertLess(delta, 0.3)  # Should be OTM
        
        # Test validation on sample data
        sample = pd.DataFrame({
            'timestamp': ['12/1/21'],
            'Futures_Price': [2.45],
            'OHF2 C27800': [0.12]
        })
        
        errors = validator.validate(sample, sample)
        self.assertEqual(len(errors), 0)


if __name__ == '__main__':
    unittest.main()