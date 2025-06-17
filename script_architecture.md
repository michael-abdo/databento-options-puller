# Closed Feedback Loop Script Architecture

## Core Principle
Build a system that iteratively converges on matching `example_output.csv` exactly through detailed logging and systematic refinement.

## Architecture Overview

```
example_output.csv (Ground Truth)
        │
        ▼
┌──────────────────┐
│ Analyzer Module  │ ──── Extracts all facts from example
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Generator Module │ ──── Attempts to recreate output
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Validator Module │ ──── Compares and logs differences
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Refiner Module   │ ──── Adjusts logic based on logs
└──────────────────┘
```

## Module 1: Example Analyzer

```python
# src/example_analyzer.py
import pandas as pd
import logging
from datetime import datetime
from typing import Dict, List, Tuple

class ExampleAnalyzer:
    """Extract all facts from example_output.csv"""
    
    def __init__(self, example_path: str = 'example_output.csv'):
        self.df = pd.read_csv(example_path)
        self.logger = logging.getLogger('analyzer')
        
    def analyze(self) -> Dict:
        """Extract all observable facts"""
        facts = {
            'option_symbols': self._extract_symbols(),
            'active_periods': self._extract_active_periods(),
            'roll_schedule': self._extract_roll_schedule(),
            'price_data': self._extract_price_data(),
            'patterns': self._identify_patterns()
        }
        
        self._log_findings(facts)
        return facts
    
    def _extract_symbols(self) -> List[str]:
        """Get all option symbols from columns"""
        symbols = [col for col in self.df.columns if 'C' in col]
        self.logger.info(f"Found {len(symbols)} option symbols: {symbols}")
        return symbols
    
    def _extract_active_periods(self) -> Dict[str, Tuple[str, str]]:
        """Find when each option is active"""
        periods = {}
        
        for symbol in self._extract_symbols():
            # Find first and last non-null dates
            mask = self.df[symbol].notna()
            if mask.any():
                first_idx = mask.idxmax()
                last_idx = mask[::-1].idxmax()
                
                first_date = self.df.loc[first_idx, 'timestamp']
                last_date = self.df.loc[last_idx, 'timestamp']
                
                periods[symbol] = (first_date, last_date)
                
                self.logger.info(f"{symbol}: {first_date} to {last_date}")
        
        return periods
    
    def _extract_roll_schedule(self) -> List[Dict]:
        """Identify when positions roll"""
        rolls = []
        symbols = self._extract_symbols()
        
        for i in range(len(symbols) - 1):
            current = symbols[i]
            next_sym = symbols[i + 1]
            
            # Find overlap period
            current_end = self._get_last_date(current)
            next_start = self._get_first_date(next_sym)
            
            roll_info = {
                'from_symbol': current,
                'to_symbol': next_sym,
                'roll_date': next_start,
                'overlap_days': self._count_overlap_days(current, next_sym)
            }
            
            rolls.append(roll_info)
            self.logger.info(f"Roll: {current} -> {next_sym} on {next_start}")
        
        return rolls
    
    def _identify_patterns(self) -> Dict:
        """Look for patterns in the data"""
        patterns = {}
        
        # Pattern 1: Month codes
        symbols = self._extract_symbols()
        month_codes = [self._extract_month_code(s) for s in symbols]
        patterns['month_progression'] = month_codes
        
        # Pattern 2: Strike progression
        strikes = [self._extract_strike(s) for s in symbols]
        patterns['strikes'] = strikes
        
        # Pattern 3: Typical active period length
        periods = self._extract_active_periods()
        lengths = [(pd.to_datetime(end) - pd.to_datetime(start)).days 
                   for start, end in periods.values()]
        patterns['typical_duration'] = sum(lengths) / len(lengths)
        
        self.logger.info(f"Patterns: {patterns}")
        return patterns
```

## Module 2: Option Generator

```python
# src/option_generator.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

class OptionGenerator:
    """Generate options data based on hypothesis"""
    
    def __init__(self, facts: Dict):
        self.facts = facts
        self.logger = logging.getLogger('generator')
        
        # Initial parameters (to be tuned)
        self.params = {
            'delta_target': 0.15,
            'volatility': 0.30,
            'risk_free_rate': 0.05,
            'months_ahead': 2
        }
    
    def generate(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Attempt to recreate the output"""
        self.logger.info(f"Generating with params: {self.params}")
        
        # Create date range
        dates = pd.date_range(start_date, end_date, freq='B')
        df = pd.DataFrame({'timestamp': dates})
        
        # Generate futures prices (placeholder)
        df['Futures_Price'] = self._generate_futures_prices(df)
        
        # Generate options based on roll schedule
        for roll_info in self.facts['roll_schedule']:
            symbol = roll_info['to_symbol']
            start = roll_info['roll_date']
            
            # Generate option prices for this symbol
            option_prices = self._generate_option_prices(
                symbol, start, self.params
            )
            
            df[symbol] = option_prices
        
        return df
    
    def _select_strike(self, spot: float, expiry_date: datetime) -> Tuple[float, str]:
        """Select 15-delta strike"""
        # This is where we'll iterate to match the example
        
        # Log all our calculations
        self.logger.debug(f"Selecting strike for spot={spot}, expiry={expiry_date}")
        
        # Try different strikes
        strikes = np.arange(spot * 0.5, spot * 1.5, 0.5)
        
        best_strike = None
        best_delta = None
        
        for strike in strikes:
            delta = self._calculate_delta(spot, strike, expiry_date)
            self.logger.debug(f"Strike {strike}: delta={delta:.4f}")
            
            if best_strike is None or abs(delta - 0.15) < abs(best_delta - 0.15):
                best_strike = strike
                best_delta = delta
        
        self.logger.info(f"Selected strike {best_strike} with delta {best_delta}")
        return best_strike, f"C{int(best_strike * 100)}"
```

## Module 3: Output Validator

```python
# src/output_validator.py
import pandas as pd
import numpy as np
import logging
from typing import Dict, List

class OutputValidator:
    """Compare generated output with example"""
    
    def __init__(self, example_path: str = 'example_output.csv'):
        self.expected = pd.read_csv(example_path)
        self.logger = logging.getLogger('validator')
        
    def validate(self, generated: pd.DataFrame) -> Dict:
        """Comprehensive validation"""
        
        results = {
            'symbol_accuracy': self._validate_symbols(generated),
            'date_accuracy': self._validate_dates(generated),
            'value_accuracy': self._validate_values(generated),
            'structure_accuracy': self._validate_structure(generated),
            'detailed_errors': self._get_detailed_errors(generated)
        }
        
        self._log_validation_summary(results)
        return results
    
    def _validate_symbols(self, generated: pd.DataFrame) -> float:
        """Check if option symbols match"""
        expected_symbols = [col for col in self.expected.columns if 'C' in col]
        generated_symbols = [col for col in generated.columns if 'C' in col]
        
        missing = set(expected_symbols) - set(generated_symbols)
        extra = set(generated_symbols) - set(expected_symbols)
        
        if missing:
            self.logger.error(f"Missing symbols: {missing}")
        if extra:
            self.logger.error(f"Extra symbols: {extra}")
        
        correct = len(set(expected_symbols) & set(generated_symbols))
        total = len(expected_symbols)
        
        return correct / total if total > 0 else 0
    
    def _validate_dates(self, generated: pd.DataFrame) -> float:
        """Check if options appear on correct dates"""
        correct_dates = 0
        total_dates = 0
        
        for symbol in [col for col in self.expected.columns if 'C' in col]:
            if symbol not in generated.columns:
                continue
                
            # Check first appearance
            exp_first = self._get_first_date(self.expected, symbol)
            gen_first = self._get_first_date(generated, symbol)
            
            if exp_first == gen_first:
                correct_dates += 1
            else:
                self.logger.error(f"{symbol} first date mismatch: "
                                f"expected {exp_first}, got {gen_first}")
            
            total_dates += 1
            
            # Check last appearance
            exp_last = self._get_last_date(self.expected, symbol)
            gen_last = self._get_last_date(generated, symbol)
            
            if exp_last == gen_last:
                correct_dates += 1
            else:
                self.logger.error(f"{symbol} last date mismatch: "
                                f"expected {exp_last}, got {gen_last}")
            
            total_dates += 1
        
        return correct_dates / total_dates if total_dates > 0 else 0
    
    def create_comparison_report(self, generated: pd.DataFrame) -> str:
        """Create detailed HTML comparison"""
        html = """
        <html>
        <head>
            <style>
                .match { background-color: #90EE90; }
                .mismatch { background-color: #FFB6C1; }
                .missing { background-color: #FFE4B5; }
                table { border-collapse: collapse; }
                td, th { border: 1px solid black; padding: 5px; }
            </style>
        </head>
        <body>
            <h1>Output Comparison Report</h1>
            <table>
        """
        
        # Add comparison logic here
        
        html += "</table></body></html>"
        
        with open('comparison_report.html', 'w') as f:
            f.write(html)
        
        return "comparison_report.html"
```

## Module 4: Parameter Refiner

```python
# src/parameter_refiner.py
import logging
from typing import Dict, Tuple

class ParameterRefiner:
    """Adjust parameters based on validation results"""
    
    def __init__(self):
        self.logger = logging.getLogger('refiner')
        self.history = []
        
    def refine(self, current_params: Dict, validation_results: Dict) -> Dict:
        """Suggest new parameters based on errors"""
        
        self.history.append({
            'params': current_params.copy(),
            'results': validation_results
        })
        
        # Analyze what went wrong
        if validation_results['symbol_accuracy'] < 1.0:
            # Symbols don't match - likely wrong strike selection
            return self._adjust_for_symbol_mismatch(current_params)
            
        elif validation_results['date_accuracy'] < 1.0:
            # Dates don't match - likely wrong roll logic
            return self._adjust_for_date_mismatch(current_params)
            
        elif validation_results['value_accuracy'] < 1.0:
            # Values don't match - need different pricing params
            return self._adjust_for_value_mismatch(current_params)
        
        return current_params
    
    def _adjust_for_symbol_mismatch(self, params: Dict) -> Dict:
        """Adjust parameters to fix symbol selection"""
        
        # Try different delta targets
        if len(self.history) < 5:
            # First few attempts: try nearby deltas
            params['delta_target'] += 0.01
        else:
            # Later: try different volatility
            params['volatility'] *= 1.1
        
        self.logger.info(f"Adjusting for symbol mismatch: {params}")
        return params
```

## Module 5: Main Runner

```python
# main.py
import logging
import pandas as pd
from src.example_analyzer import ExampleAnalyzer
from src.option_generator import OptionGenerator
from src.output_validator import OutputValidator
from src.parameter_refiner import ParameterRefiner

def setup_logging():
    """Configure multi-file logging"""
    
    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup different log files
    loggers = {
        'analyzer': 'logs/analyzer.log',
        'generator': 'logs/generator.log',
        'validator': 'logs/validator.log',
        'refiner': 'logs/refiner.log',
        'main': 'logs/main.log'
    }
    
    for name, filename in loggers.items():
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        
        handler = logging.FileHandler(filename)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

def main():
    """Run the feedback loop"""
    
    setup_logging()
    logger = logging.getLogger('main')
    
    # Step 1: Analyze the example
    logger.info("=== ANALYZING EXAMPLE OUTPUT ===")
    analyzer = ExampleAnalyzer()
    facts = analyzer.analyze()
    
    # Step 2: Initialize components
    generator = OptionGenerator(facts)
    validator = OutputValidator()
    refiner = ParameterRefiner()
    
    # Step 3: Run feedback loop
    max_iterations = 50
    for iteration in range(max_iterations):
        logger.info(f"\n=== ITERATION {iteration + 1} ===")
        
        # Generate attempt
        generated = generator.generate('2021-12-01', '2022-03-31')
        
        # Validate
        results = validator.validate(generated)
        
        # Check if we've succeeded
        if all(v >= 0.99 for v in results.values() if isinstance(v, float)):
            logger.info("SUCCESS! Output matches example.")
            generated.to_csv('final_output.csv', index=False)
            break
        
        # Refine parameters
        new_params = refiner.refine(generator.params, results)
        generator.params = new_params
        
        # Save intermediate results
        generated.to_csv(f'output/iteration_{iteration + 1}.csv', index=False)
        
    # Create final report
    validator.create_comparison_report(generated)

if __name__ == "__main__":
    main()
```

## Key Design Principles

1. **Example-Driven Development**: The example output is the specification
2. **Detailed Logging**: Every decision is logged for debugging
3. **Iterative Refinement**: Systematically improve based on errors
4. **Modular Design**: Each component has a single responsibility
5. **Validation First**: Success is defined by matching the example

## Logging Strategy

Each module logs to a separate file:
- `analyzer.log`: Facts extracted from example
- `generator.log`: Generation decisions and calculations
- `validator.log`: Validation errors and mismatches
- `refiner.log`: Parameter adjustments
- `main.log`: Overall progress

## Success Metrics

The system succeeds when:
- All option symbols match exactly
- Options appear/disappear on correct dates
- Price values match (within tolerance)
- No missing or extra data

## Error Analysis

Common errors and their solutions:
- **Wrong symbols**: Adjust delta calculation or volatility
- **Wrong dates**: Fix roll schedule or trading calendar
- **Wrong values**: Adjust pricing model parameters