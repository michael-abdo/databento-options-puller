# Closed Feedback Loop Implementation Plan

## Success Criteria
The implementation must exactly reproduce `example_output.csv` - this is our ground truth.

## 🔄 Feedback Loop Architecture

```
┌─────────────────┐
│ Initial Script  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│  Run & Generate │────▶│ Compare Output   │
│     Output      │     │ vs example_output│
└─────────────────┘     └────────┬─────────┘
         ▲                       │
         │                       ▼
         │              ┌──────────────────┐
         │              │ Analyze Deltas   │
         │              │ Log Discrepancies│
         │              └────────┬─────────┘
         │                       │
         │                       ▼
┌────────┴────────┐     ┌──────────────────┐
│ Update Logic    │◀────│ Identify Root    │
│ Based on Logs   │     │ Cause from Logs  │
└─────────────────┘     └──────────────────┘
```

## Phase 1: Validation Framework Setup

### 1.1 Create Output Validator
```python
class OutputValidator:
    def __init__(self, expected_path='example_output.csv'):
        self.expected = pd.read_csv(expected_path)
        self.logger = self._setup_detailed_logger()
        
    def validate_output(self, generated_df):
        """Core validation against example_output.csv"""
        results = {
            'columns_match': self._validate_columns(generated_df),
            'symbols_match': self._validate_symbols(generated_df),
            'dates_match': self._validate_dates(generated_df),
            'values_match': self._validate_values(generated_df),
            'roll_logic_match': self._validate_roll_logic(generated_df)
        }
        return results
```

### 1.2 Detailed Logging System
```python
# Multi-file logging for different aspects
loggers = {
    'main': 'logs/feedback_loop.log',
    'delta': 'logs/delta_calculations.log',
    'selection': 'logs/option_selection.log',
    'alignment': 'logs/data_alignment.log',
    'validation': 'logs/validation_results.log'
}
```

## Phase 2: Reverse Engineering from Example

### 2.1 Extract Known Facts
```python
def analyze_example_output():
    """Extract all facts from example_output.csv"""
    
    facts = {
        'option_symbols': [],  # All unique option symbols
        'roll_dates': [],      # When each option starts
        'expiry_dates': [],    # When each option ends
        'active_periods': {},  # Date ranges for each option
        'price_patterns': {}   # Price movements
    }
    
    # Log everything we learn
    logger.info("=== EXTRACTED FACTS FROM EXAMPLE ===")
    return facts
```

### 2.2 Reverse Engineer Parameters
```python
def reverse_engineer_selection_logic():
    """Work backwards from known selections"""
    
    # Known: OHF2 C27800 was selected in December
    # Find: What parameters would produce this?
    
    for symbol in known_symbols:
        strike = extract_strike(symbol)
        expiry = extract_expiry(symbol)
        selection_date = find_first_appearance(symbol)
        
        # What delta would this strike have had?
        implied_delta = calculate_implied_delta(
            selection_date, strike, expiry
        )
        
        logger.info(f"{symbol}: Implied delta = {implied_delta}")
```

## Phase 3: Iterative Development Loop

### Iteration 1: Symbol Generation Only
```python
def iteration_1_symbol_matching():
    """First goal: Generate correct option symbols"""
    
    expected_symbols = extract_symbols_from_example()
    
    for date in roll_dates:
        generated = generate_option_symbol(date)
        expected = expected_symbols[date]
        
        if generated != expected:
            logger.error(f"Symbol mismatch on {date}")
            logger.error(f"Expected: {expected}")
            logger.error(f"Generated: {generated}")
            logger.error(f"Debug info: {get_debug_info(date)}")
```

### Iteration 2: Date Alignment
```python
def iteration_2_date_alignment():
    """Ensure options appear/disappear on correct dates"""
    
    for symbol in option_symbols:
        expected_dates = get_active_dates_from_example(symbol)
        generated_dates = get_generated_active_dates(symbol)
        
        missing = expected_dates - generated_dates
        extra = generated_dates - expected_dates
        
        if missing or extra:
            logger.error(f"{symbol} date mismatch:")
            logger.error(f"Missing dates: {missing}")
            logger.error(f"Extra dates: {extra}")
```

### Iteration 3: Price Data
```python
def iteration_3_price_validation():
    """Validate price data matches"""
    
    tolerance = 0.01  # Allow small floating point differences
    
    for symbol in option_symbols:
        for date in active_dates[symbol]:
            expected_price = get_expected_price(symbol, date)
            generated_price = get_generated_price(symbol, date)
            
            if abs(expected_price - generated_price) > tolerance:
                logger.error(f"Price mismatch {symbol} on {date}")
                logger.error(f"Expected: {expected_price}")
                logger.error(f"Generated: {generated_price}")
```

## Phase 4: Debug Tools

### 4.1 Delta Calculator Debugger
```python
class DeltaDebugger:
    def debug_selection(self, date, selected_strike, all_strikes):
        """Log everything about delta calculation"""
        
        logger.debug("=== DELTA SELECTION DEBUG ===")
        logger.debug(f"Date: {date}")
        logger.debug(f"Target delta: 0.15")
        
        # Calculate delta for ALL strikes
        for strike in all_strikes:
            delta = calculate_delta(date, strike)
            distance = abs(delta - 0.15)
            selected = "***" if strike == selected_strike else ""
            
            logger.debug(f"Strike {strike}: delta={delta:.4f}, "
                        f"distance={distance:.4f} {selected}")
```

### 4.2 Comparison Visualizer
```python
def create_visual_diff():
    """Generate HTML report showing differences"""
    
    diff_html = """
    <html>
    <style>
        .match { background-color: #90EE90; }
        .mismatch { background-color: #FFB6C1; }
        .missing { background-color: #FFE4B5; }
    </style>
    <body>
        <h1>Output Comparison Report</h1>
        <table>
            <!-- Side by side comparison -->
        </table>
    </body>
    </html>
    """
```

## Phase 5: Success Metrics

### 5.1 Accuracy Tracking
```python
class AccuracyTracker:
    def __init__(self):
        self.metrics_history = []
    
    def record_iteration(self, iteration_num, results):
        metrics = {
            'iteration': iteration_num,
            'symbol_accuracy': calculate_symbol_accuracy(results),
            'date_accuracy': calculate_date_accuracy(results),
            'value_accuracy': calculate_value_accuracy(results),
            'overall_match': calculate_overall_match(results)
        }
        
        self.metrics_history.append(metrics)
        self.log_progress(metrics)
    
    def log_progress(self, metrics):
        logger.info(f"=== ITERATION {metrics['iteration']} ===")
        logger.info(f"Symbol Accuracy: {metrics['symbol_accuracy']:.1%}")
        logger.info(f"Date Accuracy: {metrics['date_accuracy']:.1%}")
        logger.info(f"Value Accuracy: {metrics['value_accuracy']:.1%}")
        logger.info(f"Overall Match: {metrics['overall_match']:.1%}")
```

### 5.2 Convergence Monitoring
```python
def monitor_convergence():
    """Track if we're getting closer to solution"""
    
    if len(metrics_history) > 1:
        current = metrics_history[-1]['overall_match']
        previous = metrics_history[-2]['overall_match']
        
        if current > previous:
            logger.info("✅ Improving! Keep current approach")
        elif current == previous:
            logger.warning("⚠️ No improvement - try different approach")
        else:
            logger.error("❌ Getting worse - revert changes")
```

## Phase 6: Parameter Tuning

### 6.1 Parameter Search
```python
class ParameterTuner:
    def __init__(self):
        self.parameter_grid = {
            'volatility': np.arange(0.1, 0.5, 0.05),
            'risk_free_rate': np.arange(0.01, 0.10, 0.01),
            'delta_target': np.arange(0.13, 0.17, 0.01)
        }
    
    def grid_search(self):
        """Try different parameter combinations"""
        best_score = 0
        best_params = {}
        
        for params in self.generate_combinations():
            score = self.evaluate_parameters(params)
            
            if score > best_score:
                best_score = score
                best_params = params
                logger.info(f"New best: {params} (score: {score:.2%})")
        
        return best_params
```

## Execution Timeline

### Day 1-2: Setup & Analysis
- Implement validation framework
- Analyze example_output.csv
- Extract all known facts

### Day 3-4: Reverse Engineering
- Work backwards from known selections
- Identify implicit parameters
- Build initial hypothesis

### Day 5-7: Iterative Refinement
- Run feedback loop
- Adjust based on logs
- Converge on solution

### Day 8: Final Validation
- Verify 100% match
- Document findings
- Package solution

## Success Criteria Checklist

- [ ] All option symbols match exactly
- [ ] Options appear on correct dates
- [ ] Options disappear on correct dates  
- [ ] All price values match (within tolerance)
- [ ] No extra columns
- [ ] No missing data where expected
- [ ] Logs clearly show reasoning

## Key Insight

The example_output.csv is our test case. We don't need to guess the business logic - we need to reverse engineer it from the data. Every discrepancy is a clue about the true underlying logic.