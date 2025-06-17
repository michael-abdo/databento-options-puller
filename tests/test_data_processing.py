"""
Unit tests for data processing components.
Tests example analyzer, output validator, and parameter refiner.
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.example_analyzer import ExampleAnalyzer
from src.output_validator import OutputValidator
from src.parameter_refiner import ParameterRefiner


class TestExampleAnalyzer(unittest.TestCase):
    """Test suite for ExampleAnalyzer."""
    
    def setUp(self):
        """Create test data."""
        self.analyzer = ExampleAnalyzer()
        
        # Create sample CSV data
        self.sample_data = pd.DataFrame({
            'timestamp': ['12/1/21', '12/2/21', '12/3/21', '1/3/22', '1/4/22', '2/1/22'],
            'OHF2 C27800': [0.12, 0.11, 0.10, np.nan, np.nan, np.nan],
            'OHG2 C24500': [np.nan, np.nan, 2.6, 4.11, 5.65, np.nan],
            'OHH2 C27000': [np.nan, np.nan, np.nan, 1.80, 2.19, 11.62]
        })
        
        # Save to temporary file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        self.sample_data.to_csv(self.temp_file.name, index=False)
    
    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_analyze_example(self):
        """Test basic analysis functionality."""
        facts = self.analyzer.analyze_example(self.temp_file.name)
        
        # Check basic facts
        self.assertIn('date_range', facts)
        self.assertIn('option_contracts', facts)
        self.assertIn('roll_schedule', facts)
        
        # Verify date range
        self.assertEqual(facts['date_range']['start'], '12/1/21')
        self.assertEqual(facts['date_range']['end'], '2/1/22')
        
        # Verify contracts
        self.assertEqual(len(facts['option_contracts']), 3)
        self.assertIn('OHF2 C27800', [c['symbol'] for c in facts['option_contracts']])
    
    def test_contract_analysis(self):
        """Test individual contract analysis."""
        facts = self.analyzer.analyze_example(self.temp_file.name)
        
        # Check first contract
        ohf2 = next(c for c in facts['option_contracts'] if c['symbol'] == 'OHF2 C27800')
        self.assertEqual(ohf2['expiry_month'], 'F2')
        self.assertEqual(ohf2['strike'], 27800)
        self.assertEqual(ohf2['first_date'], '12/1/21')
        self.assertEqual(ohf2['last_date'], '12/3/21')
        self.assertEqual(ohf2['data_points'], 3)
    
    def test_roll_schedule_detection(self):
        """Test roll schedule inference."""
        facts = self.analyzer.analyze_example(self.temp_file.name)
        
        # Should detect roll patterns
        rolls = facts['roll_schedule']
        self.assertGreater(len(rolls), 0)
        
        # Check roll structure
        for roll in rolls:
            self.assertIn('date', roll)
            self.assertIn('from_contract', roll)
            self.assertIn('to_contract', roll)
    
    def test_empty_file_handling(self):
        """Test handling of empty CSV."""
        empty_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        empty_file.write("timestamp\n")
        empty_file.close()
        
        facts = self.analyzer.analyze_example(empty_file.name)
        
        self.assertEqual(len(facts['option_contracts']), 0)
        
        os.unlink(empty_file.name)
    
    def test_futures_price_handling(self):
        """Test handling of futures price column."""
        # Add futures price column
        data_with_futures = self.sample_data.copy()
        data_with_futures['Futures_Price'] = [2.45, 2.46, 2.47, 2.50, 2.51, 2.55]
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        data_with_futures.to_csv(temp_file.name, index=False)
        
        facts = self.analyzer.analyze_example(temp_file.name)
        
        # Should identify futures column
        self.assertTrue(facts.get('has_futures_prices', False))
        
        os.unlink(temp_file.name)


class TestOutputValidator(unittest.TestCase):
    """Test suite for OutputValidator."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = OutputValidator()
        
        # Create reference data
        self.reference = pd.DataFrame({
            'timestamp': ['12/1/21', '12/2/21', '12/3/21'],
            'Futures_Price': [2.45, 2.46, 2.47],
            'OHF2 C27800': [0.12, 0.11, 0.10]
        })
        
        # Create test output (matching)
        self.output = pd.DataFrame({
            'timestamp': ['12/1/21', '12/2/21', '12/3/21'],
            'Futures_Price': [2.45, 2.46, 2.47],
            'OHF2 C27800': [0.12, 0.11, 0.10]
        })
    
    def test_perfect_match_validation(self):
        """Test validation of perfectly matching data."""
        errors = self.validator.validate(self.output, self.reference)
        
        self.assertEqual(len(errors), 0)
    
    def test_missing_column_detection(self):
        """Test detection of missing columns."""
        # Remove a column
        incomplete = self.output.drop('OHF2 C27800', axis=1)
        
        errors = self.validator.validate(incomplete, self.reference)
        
        self.assertGreater(len(errors), 0)
        self.assertTrue(any('Missing column' in str(e) for e in errors))
    
    def test_value_mismatch_detection(self):
        """Test detection of value mismatches."""
        # Change a value
        wrong_output = self.output.copy()
        wrong_output.loc[0, 'Futures_Price'] = 2.50
        
        errors = self.validator.validate(wrong_output, self.reference)
        
        self.assertGreater(len(errors), 0)
        self.assertTrue(any('Value mismatch' in str(e) for e in errors))
    
    def test_date_format_validation(self):
        """Test date format checking."""
        # Wrong date format
        wrong_dates = self.output.copy()
        wrong_dates['timestamp'] = ['2021-12-01', '2021-12-02', '2021-12-03']
        
        errors = self.validator.validate(wrong_dates, self.reference)
        
        self.assertGreater(len(errors), 0)
    
    def test_tolerance_handling(self):
        """Test numerical tolerance in comparisons."""
        # Small numerical difference
        close_output = self.output.copy()
        close_output.loc[0, 'Futures_Price'] = 2.4501  # Very close
        
        errors = self.validator.validate(close_output, self.reference, tolerance=0.001)
        
        # Should pass with tolerance
        self.assertEqual(len(errors), 0)
        
        # Should fail with tight tolerance
        errors = self.validator.validate(close_output, self.reference, tolerance=0.00001)
        self.assertGreater(len(errors), 0)
    
    def test_extra_column_handling(self):
        """Test handling of extra columns in output."""
        # Add extra column
        extra_output = self.output.copy()
        extra_output['Extra_Column'] = [1, 2, 3]
        
        errors = self.validator.validate(extra_output, self.reference)
        
        # Should warn about extra column but not fail
        warnings = [e for e in errors if e['severity'] == 'warning']
        self.assertGreater(len(warnings), 0)


class TestParameterRefiner(unittest.TestCase):
    """Test suite for ParameterRefiner."""
    
    def setUp(self):
        """Set up test environment."""
        self.refiner = ParameterRefiner()
        
        # Initial parameters
        self.initial_params = {
            'target_delta': 0.15,
            'volatility_adjustment': 1.0,
            'days_offset': 0
        }
        
        # Sample errors
        self.errors = [
            {
                'type': 'delta_mismatch',
                'expected': 0.15,
                'actual': 0.18,
                'contract': 'OHF2 C27800'
            },
            {
                'type': 'strike_selection',
                'message': 'Selected strike too high',
                'difference': 200
            }
        ]
    
    def test_basic_refinement(self):
        """Test basic parameter refinement."""
        refined = self.refiner.refine_parameters(self.initial_params, self.errors)
        
        # Should adjust parameters
        self.assertNotEqual(refined, self.initial_params)
        
        # Should track iterations
        self.assertEqual(self.refiner.iteration, 1)
    
    def test_delta_adjustment(self):
        """Test delta target adjustment."""
        # Error showing we're getting too high deltas
        high_delta_errors = [
            {'type': 'delta_mismatch', 'expected': 0.15, 'actual': 0.20},
            {'type': 'delta_mismatch', 'expected': 0.15, 'actual': 0.19}
        ]
        
        refined = self.refiner.refine_parameters(self.initial_params, high_delta_errors)
        
        # Should adjust target delta or volatility
        self.assertIn('volatility_adjustment', refined)
    
    def test_convergence_detection(self):
        """Test convergence detection."""
        # First refinement
        refined1 = self.refiner.refine_parameters(self.initial_params, self.errors)
        
        # Second refinement with smaller errors
        small_errors = [
            {'type': 'delta_mismatch', 'expected': 0.15, 'actual': 0.151}
        ]
        refined2 = self.refiner.refine_parameters(refined1, small_errors)
        
        # Should detect near convergence
        self.assertTrue(self.refiner.has_converged(small_errors))
    
    def test_parameter_bounds(self):
        """Test parameter boundary enforcement."""
        # Extreme errors that would push parameters out of bounds
        extreme_errors = [
            {'type': 'delta_mismatch', 'expected': 0.15, 'actual': 0.50}
        ] * 10
        
        # Apply multiple refinements
        params = self.initial_params.copy()
        for _ in range(10):
            params = self.refiner.refine_parameters(params, extreme_errors)
        
        # Check bounds
        self.assertGreater(params.get('volatility_adjustment', 1.0), 0.5)
        self.assertLess(params.get('volatility_adjustment', 1.0), 2.0)
    
    def test_history_tracking(self):
        """Test parameter history tracking."""
        # Multiple refinements
        params = self.initial_params.copy()
        for i in range(3):
            params = self.refiner.refine_parameters(params, self.errors)
        
        # Check history
        self.assertEqual(len(self.refiner.history), 3)
        
        # Each history entry should have parameters and errors
        for entry in self.refiner.history:
            self.assertIn('parameters', entry)
            self.assertIn('errors', entry)
            self.assertIn('timestamp', entry)


class TestIntegration(unittest.TestCase):
    """Integration tests for data processing pipeline."""
    
    def test_full_analysis_pipeline(self):
        """Test complete analysis pipeline."""
        # Create sample data
        sample_data = pd.DataFrame({
            'timestamp': pd.date_range('2021-12-01', periods=30, freq='D').strftime('%-m/%-d/%y'),
            'OHF2 C27800': np.random.uniform(0.05, 0.20, 30),
            'OHG2 C24500': [np.nan] * 15 + list(np.random.uniform(2.0, 5.0, 15))
        })
        
        # Save to file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        sample_data.to_csv(temp_file.name, index=False)
        
        # Analyze
        analyzer = ExampleAnalyzer()
        facts = analyzer.analyze_example(temp_file.name)
        
        # Validate structure
        validator = OutputValidator()
        errors = validator.validate(sample_data, sample_data)  # Self-validation
        
        # Should pass
        self.assertEqual(len(errors), 0)
        
        # Clean up
        os.unlink(temp_file.name)
    
    def test_iterative_refinement(self):
        """Test iterative parameter refinement process."""
        refiner = ParameterRefiner()
        
        # Initial parameters
        params = {'target_delta': 0.15, 'volatility_adjustment': 1.0}
        
        # Simulate decreasing errors over iterations
        error_sequences = [
            [{'type': 'delta_mismatch', 'expected': 0.15, 'actual': 0.25}],
            [{'type': 'delta_mismatch', 'expected': 0.15, 'actual': 0.20}],
            [{'type': 'delta_mismatch', 'expected': 0.15, 'actual': 0.17}],
            [{'type': 'delta_mismatch', 'expected': 0.15, 'actual': 0.155}],
        ]
        
        # Run refinement
        for errors in error_sequences:
            if refiner.has_converged(errors):
                break
            params = refiner.refine_parameters(params, errors)
        
        # Should converge
        self.assertTrue(refiner.iteration >= 3)
        self.assertLess(refiner.iteration, 5)


if __name__ == '__main__':
    unittest.main()