"""
Parameter Refiner module for adjusting generation parameters based on validation errors.
This module analyzes validation results and suggests parameter changes to improve match.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import yaml

# Add parent directory to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.logging_config import get_logger

logger = get_logger('refiner')


class ParameterRefiner:
    """Adjust parameters based on validation results to improve output match."""
    
    def __init__(self, config: Dict = None):
        """
        Initialize refiner with optional configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or self._load_default_config()
        self.history = []
        self.iteration_count = 0
        self.best_score = 0.0
        self.best_params = {}
        
        # Learning parameters
        self.learning_rate = self.config['refiner']['learning_rate']
        self.patience = self.config['refiner']['patience']
        self.stuck_count = 0
        
        logger.info("Initialized ParameterRefiner")
    
    def _load_default_config(self) -> Dict:
        """Load default configuration from YAML."""
        config_path = Path(__file__).parent.parent / 'config' / 'default_params.yaml'
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def refine(self, current_params: Dict, validation_results: Dict) -> Dict:
        """
        Suggest new parameters based on validation results.
        
        Args:
            current_params: Current generation parameters
            validation_results: Results from validator
            
        Returns:
            Updated parameters dictionary
        """
        self.iteration_count += 1
        
        logger.info("="*60)
        logger.info(f"Parameter Refinement - Iteration {self.iteration_count}")
        logger.info("="*60)
        
        # Record history
        self.history.append({
            'iteration': self.iteration_count,
            'params': current_params.copy(),
            'results': validation_results,
            'score': validation_results.get('overall_score', 0.0),
            'timestamp': datetime.now()
        })
        
        # Update best score
        current_score = validation_results.get('overall_score', 0.0)
        if current_score > self.best_score:
            self.best_score = current_score
            self.best_params = current_params.copy()
            self.stuck_count = 0
            logger.info(f"New best score: {self.best_score:.2%}")
        else:
            self.stuck_count += 1
            logger.info(f"No improvement for {self.stuck_count} iterations")
        
        # Analyze specific issues and adjust
        new_params = current_params.copy()
        
        # Priority 1: Fix structural issues (columns, dates)
        if validation_results.get('column_validation', {}).get('score', 0) < 1.0:
            new_params = self._fix_column_issues(new_params, validation_results)
        
        # Priority 2: Fix date issues
        elif validation_results.get('date_validation', {}).get('score', 0) < 1.0:
            new_params = self._fix_date_issues(new_params, validation_results)
        
        # Priority 3: Fix symbol issues
        elif validation_results.get('symbol_validation', {}).get('score', 0) < 1.0:
            new_params = self._fix_symbol_issues(new_params, validation_results)
        
        # Priority 4: Fix active period issues
        elif validation_results.get('active_period_validation', {}).get('score', 0) < 1.0:
            new_params = self._fix_period_issues(new_params, validation_results)
        
        # Priority 5: Fix value issues
        elif validation_results.get('value_validation', {}).get('score', 0) < 1.0:
            new_params = self._fix_value_issues(new_params, validation_results)
        
        # If stuck, try larger changes
        if self.stuck_count >= self.patience:
            logger.warning(f"Stuck for {self.stuck_count} iterations, trying larger changes")
            new_params = self._apply_larger_changes(new_params)
            self.stuck_count = 0
        
        # Log changes
        self._log_parameter_changes(current_params, new_params)
        
        return new_params
    
    def _fix_column_issues(self, params: Dict, results: Dict) -> Dict:
        """Fix column-related issues."""
        col_validation = results.get('column_validation', {})
        
        # Check for extra columns
        extra_cols = col_validation.get('extra_columns', [])
        if 'Futures_Price' in extra_cols:
            logger.info("Fixing: Remove Futures_Price column")
            params['include_futures_price'] = False
        
        # Check for missing columns
        missing_cols = col_validation.get('missing_columns', [])
        if missing_cols:
            logger.error(f"Missing columns that should exist: {missing_cols}")
            # This shouldn't happen if generator is correct
        
        return params
    
    def _fix_date_issues(self, params: Dict, results: Dict) -> Dict:
        """Fix date-related issues."""
        date_validation = results.get('date_validation', {})
        
        # Check date format
        mismatches = date_validation.get('mismatches', [])
        if mismatches:
            # Look at first mismatch to understand format issue
            first_mismatch = mismatches[0]
            expected = first_mismatch.get('expected', '')
            generated = first_mismatch.get('generated', '')
            
            # Check if it's a zero-padding issue
            if expected.replace('/', '') == generated.replace('/', '').lstrip('0'):
                logger.info("Fixing: Date format zero-padding issue")
                params['date_format'] = "%-m/%-d/%y"  # No zero padding
            else:
                logger.warning(f"Date format mismatch: '{expected}' vs '{generated}'")
        
        # Check row count
        expected_count = date_validation.get('expected_count', 0)
        generated_count = date_validation.get('generated_count', 0)
        
        if expected_count != generated_count:
            logger.info(f"Fixing: Row count mismatch ({generated_count} vs {expected_count})")
            params['exact_row_count'] = expected_count
            # Might need to handle weekends/holidays differently
            params['include_weekends'] = True  # Try including weekends
        
        return params
    
    def _fix_symbol_issues(self, params: Dict, results: Dict) -> Dict:
        """Fix symbol-related issues."""
        sym_validation = results.get('symbol_validation', {})
        
        missing_symbols = sym_validation.get('missing_symbols', [])
        if missing_symbols:
            logger.error(f"Missing symbols: {missing_symbols}")
            # This is a generator logic issue, not parameter issue
            
        extra_symbols = sym_validation.get('extra_symbols', [])
        if extra_symbols:
            logger.warning(f"Extra symbols: {extra_symbols}")
            # Remove extra symbols
            params['symbols_to_exclude'] = extra_symbols
        
        return params
    
    def _fix_period_issues(self, params: Dict, results: Dict) -> Dict:
        """Fix active period issues."""
        period_validation = results.get('active_period_validation', {})
        period_details = period_validation.get('period_validations', {})
        
        # Analyze period mismatches
        for symbol, details in period_details.items():
            if not details.get('first_match', True):
                exp_first = details.get('expected_first')
                gen_first = details.get('generated_first')
                logger.info(f"{symbol}: Adjusting first date (exp:{exp_first} gen:{gen_first})")
                
                # Store adjustment needed
                if 'period_adjustments' not in params:
                    params['period_adjustments'] = {}
                params['period_adjustments'][symbol] = {
                    'first_idx_offset': (exp_first or 0) - (gen_first or 0)
                }
            
            if not details.get('last_match', True):
                exp_last = details.get('expected_last')
                gen_last = details.get('generated_last')
                logger.info(f"{symbol}: Adjusting last date (exp:{exp_last} gen:{gen_last})")
                
                if 'period_adjustments' not in params:
                    params['period_adjustments'] = {}
                if symbol not in params['period_adjustments']:
                    params['period_adjustments'][symbol] = {}
                params['period_adjustments'][symbol]['last_idx_offset'] = (exp_last or 0) - (gen_last or 0)
        
        return params
    
    def _fix_value_issues(self, params: Dict, results: Dict) -> Dict:
        """Fix value-related issues."""
        value_validation = results.get('value_validation', {})
        
        # For stub data, we can't match exact values
        # But we can ensure counts match
        value_details = value_validation.get('value_validations', {})
        
        for symbol, details in value_details.items():
            if details.get('status') == 'missing':
                continue
                
            exp_count = details.get('expected_count', 0)
            gen_count = details.get('generated_count', 0)
            
            if exp_count != gen_count:
                logger.info(f"{symbol}: Value count mismatch ({gen_count} vs {exp_count})")
                # This is related to period issues
        
        # For real implementation, would adjust volatility, pricing model, etc.
        logger.info("Value matching requires real data fetching (not stub)")
        params['use_stub'] = False  # Signal to use real data
        
        return params
    
    def _apply_larger_changes(self, params: Dict) -> Dict:
        """Apply larger parameter changes when stuck."""
        # Try different approaches based on iteration
        approach = (self.iteration_count // self.patience) % 4
        
        if approach == 0:
            logger.info("Trying: Reset to defaults")
            # Reset certain parameters
            params['date_format'] = "%m/%d/%y"
            params.pop('period_adjustments', None)
            
        elif approach == 1:
            logger.info("Trying: Adjust all periods by fixed amount")
            params['global_period_shift'] = 5  # Shift all periods
            
        elif approach == 2:
            logger.info("Trying: Different date handling")
            params['skip_weekends'] = True
            
        else:
            logger.info("Trying: Revert to best known params")
            return self.best_params.copy()
        
        return params
    
    def _log_parameter_changes(self, old_params: Dict, new_params: Dict):
        """Log what parameters changed."""
        changes = []
        
        # Find changed parameters
        all_keys = set(old_params.keys()) | set(new_params.keys())
        
        for key in all_keys:
            old_val = old_params.get(key)
            new_val = new_params.get(key)
            
            if old_val != new_val:
                changes.append(f"{key}: {old_val} -> {new_val}")
        
        if changes:
            logger.info("Parameter changes:")
            for change in changes:
                logger.info(f"  - {change}")
        else:
            logger.info("No parameter changes")
    
    def get_history(self) -> List[Dict]:
        """Get refinement history."""
        return self.history
    
    def get_best_params(self) -> Dict:
        """Get best parameters found so far."""
        return self.best_params
    
    def get_convergence_info(self) -> Dict:
        """Get information about convergence progress."""
        scores = [h['score'] for h in self.history]
        
        info = {
            'iterations': self.iteration_count,
            'best_score': self.best_score,
            'current_score': scores[-1] if scores else 0.0,
            'stuck_count': self.stuck_count,
            'score_history': scores,
            'improving': scores[-1] > scores[-2] if len(scores) >= 2 else False
        }
        
        return info
    
    def save_history(self, output_path: str = 'output/refinement_history.json'):
        """Save refinement history to file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(exist_ok=True)
        
        # Convert history to JSON-serializable format
        history_data = {
            'total_iterations': self.iteration_count,
            'best_score': self.best_score,
            'best_params': self.best_params,
            'history': [
                {
                    'iteration': h['iteration'],
                    'score': h['score'],
                    'timestamp': h['timestamp'].isoformat(),
                    'params': h['params']
                }
                for h in self.history
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(history_data, f, indent=2)
        
        logger.info(f"Saved refinement history to {output_path}")


def main():
    """Test the refiner independently."""
    from utils.logging_config import setup_logging
    
    # Set up logging
    setup_logging()
    
    # Create refiner
    refiner = ParameterRefiner()
    
    # Load sample validation results
    validation_path = Path('output/validation_results.json')
    if validation_path.exists():
        with open(validation_path, 'r') as f:
            validation_results = json.load(f)
    else:
        logger.error("No validation results found")
        return
    
    # Test refinement
    current_params = {
        'use_stub': True,
        'date_format': '%m/%d/%y',
        'include_futures_price': True
    }
    
    new_params = refiner.refine(current_params, validation_results)
    
    print("\nRefinement complete!")
    print(f"Current score: {validation_results.get('overall_score', 0):.2%}")
    print("\nSuggested changes:")
    for key, value in new_params.items():
        if key not in current_params or current_params[key] != value:
            print(f"  {key}: {current_params.get(key)} -> {value}")


if __name__ == "__main__":
    main()