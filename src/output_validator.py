"""
Output Validator module for comparing generated output with example.
Provides detailed analysis of discrepancies to guide parameter refinement.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set
import logging
from pathlib import Path
import json
from collections import defaultdict

# Add parent directory to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.date_utils import parse_date, format_date
from utils.symbol_utils import parse_option_symbol
from utils.logging_config import get_logger

logger = get_logger('validator')


class OutputValidator:
    """Compare generated output with example and identify discrepancies."""
    
    def __init__(self, example_path: str = 'example_output.csv'):
        """
        Initialize validator with path to example CSV.
        
        Args:
            example_path: Path to example_output.csv
        """
        self.example_path = example_path
        self.expected = pd.read_csv(example_path)
        self.validation_results = {}
        
        logger.info(f"Initialized OutputValidator with {example_path}")
        logger.info(f"Expected shape: {self.expected.shape}")
    
    def validate(self, generated: pd.DataFrame) -> Dict:
        """
        Comprehensive validation of generated output against example.
        
        Args:
            generated: Generated dataframe to validate
            
        Returns:
            Dictionary with validation results and metrics
        """
        logger.info("="*60)
        logger.info("Starting validation")
        logger.info("="*60)
        
        results = {
            'column_validation': self._validate_columns(generated),
            'date_validation': self._validate_dates(generated),
            'symbol_validation': self._validate_symbols(generated),
            'active_period_validation': self._validate_active_periods(generated),
            'value_validation': self._validate_values(generated),
            'structure_validation': self._validate_structure(generated),
            'accuracy_metrics': self._calculate_accuracy_metrics(generated),
            'detailed_errors': self._collect_detailed_errors(generated)
        }
        
        # Calculate overall score
        results['overall_score'] = self._calculate_overall_score(results)
        
        # Log summary
        self._log_validation_summary(results)
        
        # Save detailed results
        self._save_validation_results(results)
        
        self.validation_results = results
        return results
    
    def _validate_columns(self, generated: pd.DataFrame) -> Dict:
        """Validate column names and order."""
        expected_cols = list(self.expected.columns)
        generated_cols = list(generated.columns)
        
        # Find differences
        missing_cols = set(expected_cols) - set(generated_cols)
        extra_cols = set(generated_cols) - set(expected_cols)
        
        # Check order (excluding any extra columns)
        common_cols = [col for col in generated_cols if col in expected_cols]
        order_match = common_cols == [col for col in expected_cols if col in common_cols]
        
        validation = {
            'expected_columns': expected_cols,
            'generated_columns': generated_cols,
            'missing_columns': list(missing_cols),
            'extra_columns': list(extra_cols),
            'order_matches': order_match,
            'score': 1.0 if not missing_cols and not extra_cols and order_match else 0.0
        }
        
        # Log issues
        if missing_cols:
            logger.error(f"Missing columns: {missing_cols}")
        if extra_cols:
            logger.warning(f"Extra columns: {extra_cols}")
        if not order_match:
            logger.warning("Column order does not match")
            
        return validation
    
    def _validate_dates(self, generated: pd.DataFrame) -> Dict:
        """Validate date alignment and format."""
        if 'timestamp' not in generated.columns:
            logger.error("No timestamp column in generated data")
            return {'score': 0.0, 'error': 'No timestamp column'}
        
        expected_dates = self.expected['timestamp'].tolist()
        generated_dates = generated['timestamp'].tolist()
        
        # Compare lengths
        len_match = len(expected_dates) == len(generated_dates)
        
        # Compare actual dates
        dates_match = expected_dates == generated_dates[:len(expected_dates)]
        
        # Find mismatches
        mismatches = []
        for i, (exp, gen) in enumerate(zip(expected_dates, generated_dates[:len(expected_dates)])):
            if exp != gen:
                mismatches.append({
                    'index': i,
                    'expected': exp,
                    'generated': gen
                })
        
        validation = {
            'expected_count': len(expected_dates),
            'generated_count': len(generated_dates),
            'length_matches': len_match,
            'dates_match': dates_match,
            'mismatches': mismatches[:10],  # First 10 mismatches
            'score': 1.0 if dates_match and len_match else len([m for m in mismatches if m == []]) / len(expected_dates)
        }
        
        if not len_match:
            logger.error(f"Date count mismatch: expected {len(expected_dates)}, got {len(generated_dates)}")
        if mismatches:
            logger.error(f"Found {len(mismatches)} date mismatches")
            
        return validation
    
    def _validate_symbols(self, generated: pd.DataFrame) -> Dict:
        """Validate option symbols match."""
        # Get option columns (exclude timestamp and Futures_Price)
        expected_symbols = [col for col in self.expected.columns 
                          if col not in ['timestamp', 'Futures_Price']]
        generated_symbols = [col for col in generated.columns 
                           if col not in ['timestamp', 'Futures_Price']]
        
        # Find differences
        missing_symbols = set(expected_symbols) - set(generated_symbols)
        extra_symbols = set(generated_symbols) - set(expected_symbols)
        matching_symbols = set(expected_symbols) & set(generated_symbols)
        
        validation = {
            'expected_symbols': expected_symbols,
            'generated_symbols': generated_symbols,
            'missing_symbols': list(missing_symbols),
            'extra_symbols': list(extra_symbols),
            'matching_symbols': list(matching_symbols),
            'score': len(matching_symbols) / len(expected_symbols) if expected_symbols else 0.0
        }
        
        if missing_symbols:
            logger.error(f"Missing symbols: {missing_symbols}")
        if extra_symbols:
            logger.warning(f"Extra symbols: {extra_symbols}")
            
        logger.info(f"Symbol match score: {validation['score']:.2%}")
        
        return validation
    
    def _validate_active_periods(self, generated: pd.DataFrame) -> Dict:
        """Validate when each option is active (non-null)."""
        period_validations = {}
        
        # Get option symbols
        symbols = [col for col in self.expected.columns 
                  if col not in ['timestamp', 'Futures_Price']]
        
        for symbol in symbols:
            if symbol not in generated.columns:
                period_validations[symbol] = {
                    'status': 'missing',
                    'score': 0.0
                }
                continue
            
            # Find active periods in both dataframes
            exp_active = self.expected[symbol].notna()
            gen_active = generated[symbol].notna()
            
            # Align lengths
            min_len = min(len(exp_active), len(gen_active))
            exp_active = exp_active[:min_len]
            gen_active = gen_active[:min_len]
            
            # Find first and last active dates
            if exp_active.any():
                exp_first = exp_active.idxmax()
                exp_last = len(exp_active) - 1 - exp_active[::-1].idxmax()
            else:
                exp_first = exp_last = None
                
            if gen_active.any():
                gen_first = gen_active.idxmax()
                gen_last = len(gen_active) - 1 - gen_active[::-1].idxmax()
            else:
                gen_first = gen_last = None
            
            # Calculate overlap
            if exp_first is not None and gen_first is not None:
                overlap_start = max(exp_first, gen_first)
                overlap_end = min(exp_last, gen_last)
                
                if overlap_start <= overlap_end:
                    overlap_days = overlap_end - overlap_start + 1
                    total_days = max(exp_last - exp_first + 1, gen_last - gen_first + 1)
                    overlap_score = overlap_days / total_days if total_days > 0 else 0
                else:
                    overlap_score = 0.0
            else:
                overlap_score = 0.0
            
            period_validations[symbol] = {
                'expected_first': exp_first,
                'expected_last': exp_last,
                'generated_first': gen_first,
                'generated_last': gen_last,
                'first_match': exp_first == gen_first,
                'last_match': exp_last == gen_last,
                'overlap_score': overlap_score,
                'score': overlap_score
            }
            
            if not period_validations[symbol]['first_match']:
                logger.warning(f"{symbol} first date mismatch: "
                             f"expected idx {exp_first}, got idx {gen_first}")
            if not period_validations[symbol]['last_match']:
                logger.warning(f"{symbol} last date mismatch: "
                             f"expected idx {exp_last}, got idx {gen_last}")
        
        # Overall score
        scores = [v['score'] for v in period_validations.values()]
        overall_score = sum(scores) / len(scores) if scores else 0.0
        
        return {
            'period_validations': period_validations,
            'score': overall_score
        }
    
    def _validate_values(self, generated: pd.DataFrame) -> Dict:
        """Validate actual price values."""
        value_validations = {}
        tolerance = 0.01  # Price tolerance
        
        # Get option symbols
        symbols = [col for col in self.expected.columns 
                  if col not in ['timestamp', 'Futures_Price']]
        
        for symbol in symbols:
            if symbol not in generated.columns:
                value_validations[symbol] = {
                    'status': 'missing',
                    'score': 0.0
                }
                continue
            
            # Get non-null values
            exp_values = self.expected[symbol].dropna()
            gen_values = generated[symbol].dropna()
            
            if len(exp_values) == 0:
                value_validations[symbol] = {
                    'status': 'no_expected_values',
                    'score': 0.0
                }
                continue
            
            # Compare counts
            count_ratio = len(gen_values) / len(exp_values) if len(exp_values) > 0 else 0
            
            # Compare actual values (for overlapping indices)
            value_matches = 0
            total_comparisons = 0
            
            for idx in exp_values.index:
                if idx < len(generated) and pd.notna(generated.loc[idx, symbol]):
                    exp_val = exp_values.loc[idx]
                    gen_val = generated.loc[idx, symbol]
                    
                    if abs(exp_val - gen_val) <= tolerance:
                        value_matches += 1
                    total_comparisons += 1
            
            value_score = value_matches / total_comparisons if total_comparisons > 0 else 0
            
            value_validations[symbol] = {
                'expected_count': len(exp_values),
                'generated_count': len(gen_values),
                'count_ratio': count_ratio,
                'value_matches': value_matches,
                'total_comparisons': total_comparisons,
                'value_score': value_score,
                'score': value_score * min(count_ratio, 1.0)  # Penalize wrong count
            }
            
            logger.debug(f"{symbol} value validation: "
                        f"{value_matches}/{total_comparisons} matches "
                        f"(score: {value_validations[symbol]['score']:.2%})")
        
        # Overall score
        scores = [v['score'] for v in value_validations.values() if v.get('status') != 'missing']
        overall_score = sum(scores) / len(scores) if scores else 0.0
        
        return {
            'value_validations': value_validations,
            'score': overall_score
        }
    
    def _validate_structure(self, generated: pd.DataFrame) -> Dict:
        """Validate overall structure and patterns."""
        structure_checks = {
            'shape_matches': self.expected.shape == generated.shape,
            'has_timestamp': 'timestamp' in generated.columns,
            'no_duplicate_columns': len(generated.columns) == len(set(generated.columns)),
            'no_duplicate_rows': len(generated) == len(generated.drop_duplicates())
        }
        
        # Calculate score
        score = sum(1 for check in structure_checks.values() if check) / len(structure_checks)
        
        return {
            'checks': structure_checks,
            'score': score
        }
    
    def _calculate_accuracy_metrics(self, generated: pd.DataFrame) -> Dict:
        """Calculate overall accuracy metrics."""
        metrics = {}
        
        # Get individual scores
        column_score = self.validation_results.get('column_validation', {}).get('score', 0)
        date_score = self.validation_results.get('date_validation', {}).get('score', 0)
        symbol_score = self.validation_results.get('symbol_validation', {}).get('score', 0)
        period_score = self.validation_results.get('active_period_validation', {}).get('score', 0)
        value_score = self.validation_results.get('value_validation', {}).get('score', 0)
        structure_score = self.validation_results.get('structure_validation', {}).get('score', 0)
        
        metrics = {
            'column_accuracy': column_score,
            'date_accuracy': date_score,
            'symbol_accuracy': symbol_score,
            'period_accuracy': period_score,
            'value_accuracy': value_score,
            'structure_accuracy': structure_score,
            'overall_accuracy': np.mean([
                column_score, date_score, symbol_score, 
                period_score, value_score, structure_score
            ])
        }
        
        return metrics
    
    def _collect_detailed_errors(self, generated: pd.DataFrame) -> List[Dict]:
        """Collect detailed error information for debugging."""
        errors = []
        
        # Column errors
        col_validation = self.validation_results.get('column_validation', {})
        for col in col_validation.get('missing_columns', []):
            errors.append({
                'type': 'missing_column',
                'severity': 'error',
                'details': f"Missing column: {col}"
            })
        
        # Symbol errors
        sym_validation = self.validation_results.get('symbol_validation', {})
        for sym in sym_validation.get('missing_symbols', []):
            errors.append({
                'type': 'missing_symbol',
                'severity': 'error',
                'details': f"Missing option symbol: {sym}"
            })
        
        # Period errors
        period_validation = self.validation_results.get('active_period_validation', {})
        for symbol, validation in period_validation.get('period_validations', {}).items():
            if not validation.get('first_match', True):
                errors.append({
                    'type': 'period_mismatch',
                    'severity': 'warning',
                    'symbol': symbol,
                    'details': f"{symbol} starts at wrong date"
                })
            if not validation.get('last_match', True):
                errors.append({
                    'type': 'period_mismatch',
                    'severity': 'warning',
                    'symbol': symbol,
                    'details': f"{symbol} ends at wrong date"
                })
        
        return errors[:20]  # Return first 20 errors
    
    def _calculate_overall_score(self, results: Dict) -> float:
        """Calculate weighted overall score."""
        # Define weights for different aspects
        weights = {
            'column_validation': 0.15,
            'date_validation': 0.15,
            'symbol_validation': 0.20,
            'active_period_validation': 0.25,
            'value_validation': 0.20,
            'structure_validation': 0.05
        }
        
        total_score = 0.0
        for key, weight in weights.items():
            score = results.get(key, {}).get('score', 0.0)
            total_score += score * weight
            
        return total_score
    
    def _log_validation_summary(self, results: Dict):
        """Log a summary of validation results."""
        logger.info("="*60)
        logger.info("VALIDATION SUMMARY")
        logger.info("="*60)
        
        metrics = results.get('accuracy_metrics', {})
        for metric, value in metrics.items():
            logger.info(f"{metric}: {value:.2%}")
        
        logger.info(f"Overall Score: {results['overall_score']:.2%}")
        
        # Log major issues
        errors = results.get('detailed_errors', [])
        if errors:
            logger.info(f"\nFound {len(errors)} errors:")
            for error in errors[:5]:  # First 5 errors
                logger.error(f"  - {error['details']}")
                
        logger.info("="*60)
    
    def _save_validation_results(self, results: Dict):
        """Save validation results to file."""
        output_path = Path('output') / 'validation_results.json'
        output_path.parent.mkdir(exist_ok=True)
        
        # Convert to JSON-serializable format
        results_json = json.dumps(results, indent=2, default=str)
        
        with open(output_path, 'w') as f:
            f.write(results_json)
            
        logger.info(f"Saved validation results to {output_path}")
    
    def is_success(self, results: Dict = None, threshold: float = 0.99) -> bool:
        """
        Check if validation was successful.
        
        Args:
            results: Validation results (uses last if None)
            threshold: Success threshold
            
        Returns:
            True if overall score >= threshold
        """
        if results is None:
            results = self.validation_results
            
        score = results.get('overall_score', 0.0)
        return score >= threshold
    
    def create_comparison_report(self, generated: pd.DataFrame = None, 
                               output_path: str = 'output/comparison_report.html') -> str:
        """
        Create an HTML report showing differences.
        
        Args:
            generated: Generated dataframe (uses last validated if None)
            output_path: Where to save the report
            
        Returns:
            Path to generated report
        """
        logger.info("Creating comparison report...")
        
        # Simple HTML report
        html = """
        <html>
        <head>
            <title>Output Comparison Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .match { background-color: #90EE90; }
                .mismatch { background-color: #FFB6C1; }
                .missing { background-color: #FFE4B5; }
                table { border-collapse: collapse; margin: 20px 0; }
                td, th { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                .summary { background-color: #f0f0f0; padding: 15px; margin: 20px 0; }
                .error { color: red; }
                .warning { color: orange; }
                .success { color: green; }
            </style>
        </head>
        <body>
            <h1>Output Comparison Report</h1>
        """
        
        # Add summary
        if self.validation_results:
            score = self.validation_results.get('overall_score', 0.0)
            status_class = 'success' if score >= 0.99 else 'warning' if score >= 0.80 else 'error'
            
            html += f"""
            <div class="summary">
                <h2>Summary</h2>
                <p>Overall Score: <span class="{status_class}">{score:.2%}</span></p>
                <ul>
            """
            
            metrics = self.validation_results.get('accuracy_metrics', {})
            for metric, value in metrics.items():
                status = 'success' if value >= 0.99 else 'warning' if value >= 0.80 else 'error'
                html += f'<li>{metric}: <span class="{status}">{value:.2%}</span></li>'
            
            html += """
                </ul>
            </div>
            """
            
            # Add error details
            errors = self.validation_results.get('detailed_errors', [])
            if errors:
                html += """
                <div class="errors">
                    <h2>Errors Found</h2>
                    <ul>
                """
                for error in errors:
                    html += f'<li class="{error["severity"]}">{error["details"]}</li>'
                html += """
                    </ul>
                </div>
                """
        
        html += """
        </body>
        </html>
        """
        
        # Save report
        output_path = Path(output_path)
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(html)
            
        logger.info(f"Saved comparison report to {output_path}")
        
        return str(output_path)


def main():
    """Test the validator independently."""
    from utils.logging_config import setup_logging
    
    # Set up logging  
    setup_logging()
    
    # Create validator
    validator = OutputValidator()
    
    # Load generated data
    generated_path = Path('output/generated_stub.csv')
    if generated_path.exists():
        generated = pd.read_csv(generated_path)
        
        # Run validation
        results = validator.validate(generated)
        
        # Create report
        report_path = validator.create_comparison_report(generated)
        
        print(f"\nValidation complete!")
        print(f"Overall score: {results['overall_score']:.2%}")
        print(f"Report saved to: {report_path}")
        
        # Show if success
        if validator.is_success(results):
            print("\n✅ SUCCESS! Output matches example.")
        else:
            print("\n❌ Output does not match example yet.")
            print("Check logs/validator_*.log for details")
    else:
        print(f"Generated file not found: {generated_path}")
        print("Run option_generator.py first")


if __name__ == "__main__":
    main()