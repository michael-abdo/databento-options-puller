# Databento Options Puller - Complete Documentation

## Table of Contents
1. [Overview](#overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Architecture](#architecture)
5. [Core Components](#core-components)
6. [Configuration](#configuration)
7. [Usage Examples](#usage-examples)
8. [API Reference](#api-reference)
9. [Testing](#testing)
10. [Troubleshooting](#troubleshooting)
11. [Performance Optimization](#performance-optimization)

## Overview

The Databento Options Puller is a sophisticated Python application that automatically fetches and formats NY Harbor ULSD (OH) futures and options data, implementing a rolling 15-delta call option strategy.

### Key Features
- **Automated Delta Targeting**: Finds options with delta closest to 0.15
- **Rolling Monthly Strategy**: Automatically rolls to M+2 expiration
- **Black-Scholes Calculations**: Accurate options pricing and Greeks
- **Intelligent Data Alignment**: Handles sparse options trading data
- **Comprehensive Error Handling**: Robust against API failures and data issues

## Installation

### Prerequisites
```bash
# Python 3.8 or higher required
python --version

# Virtual environment recommended
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Required Packages
- `databento`: Official API client
- `pandas>=1.3.0`: Data manipulation
- `numpy>=1.21.0`: Numerical calculations
- `scipy>=1.7.0`: Black-Scholes calculations
- `click>=8.0.0`: CLI interface
- `pyyaml>=5.4.0`: Configuration handling

## Quick Start

### 1. Set Up API Credentials
```bash
export DATABENTO_API_KEY="your_api_key_here"
```

### 2. Run Basic Example
```bash
python databento_options_puller.py \
    --start-date "2021-12-01" \
    --end-date "2022-03-31" \
    --output "output/oh_options_data.csv"
```

### 3. Check Output
```python
import pandas as pd
df = pd.read_csv('output/oh_options_data.csv')
print(df.head())
```

## Architecture

### System Design
```
┌─────────────────────┐
│ databento_options_  │  ← Main entry point
│    puller.py        │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   OptionGenerator   │  ← Orchestrates data generation
└──────────┬──────────┘
           │
     ┌─────┴─────┬──────────┬─────────┐
     │           │          │         │
┌────▼───┐ ┌────▼───┐ ┌────▼───┐ ┌───▼────┐
│Futures │ │Options │ │ Delta  │ │Databento│
│Manager │ │Manager │ │ Calc   │ │ Bridge  │
└────────┘ └────────┘ └────────┘ └────────┘
```

### Data Flow
1. **Input**: Start/end dates, configuration
2. **Futures Fetch**: Get continuous front-month contract
3. **Option Discovery**: Find available strikes for M+2 expiry
4. **Delta Calculation**: Identify 15-delta strikes
5. **Price History**: Fetch full history for selected options
6. **Output Generation**: Combine into single CSV

## Core Components

### 1. DeltaCalculator (`src/delta_calculator.py`)
Handles all options mathematics using Black-Scholes model.

```python
from src.delta_calculator import DeltaCalculator

calc = DeltaCalculator(risk_free_rate=0.05)

# Calculate delta
delta = calc.calculate_delta(
    spot_price=2.50,
    strike_price=2.75,
    time_to_expiry=0.25,  # years
    volatility=0.30
)

# Find 15-delta strike
strikes = [2.00, 2.25, 2.50, 2.75, 3.00]
best_strike, actual_delta = calc.find_target_delta_strike(
    spot_price=2.50,
    available_strikes=strikes,
    time_to_expiry=0.25,
    volatility=0.30,
    target_delta=0.15
)
```

### 2. DatabentoBridge (`src/databento_client.py`)
Interfaces with Databento API for all data fetching.

```python
from src.databento_client import DatabentoBridge

bridge = DatabentoBridge(api_key="your_key")

# Fetch futures data
futures_df = bridge.fetch_futures_data(
    symbol='OH',
    start_date=datetime(2021, 12, 1),
    end_date=datetime(2021, 12, 31)
)

# Get options chain
chain = bridge.fetch_options_chain(
    root='OH',
    expiry_month='F2',
    trade_date=datetime(2021, 12, 1)
)
```

### 3. FuturesManager (`src/futures_manager.py`)
Manages futures contract logic and continuous series building.

```python
from src.futures_manager import FuturesManager

mgr = FuturesManager()

# Get front month code
code = mgr.get_front_month_code(datetime(2022, 1, 15))  # Returns 'G2'

# Build continuous series
continuous_df = mgr.get_continuous_futures(
    start_date=datetime(2021, 12, 1),
    end_date=datetime(2022, 3, 31)
)
```

### 4. OptionsManager (`src/options_manager.py`)
Handles option selection and data retrieval.

```python
from src.options_manager import OptionsManager

mgr = OptionsManager()

# Find 15-delta option
option = mgr.find_15_delta_option(
    expiry_month='F2',
    trade_date=datetime(2021, 12, 1),
    spot_price=2.50,
    volatility=0.30
)

# Get price history
history = mgr.get_option_history(
    symbol='OHF2 C27500',
    start_date=datetime(2021, 12, 1),
    end_date=datetime(2022, 1, 20)
)
```

## Configuration

### Config File Format (`config/config.yaml`)
```yaml
# API Configuration
databento:
  api_key: ${DATABENTO_API_KEY}  # From environment
  dataset: "GLBX.MDP3"           # CME Globex
  schema: "ohlcv-1d"             # Daily bars

# Strategy Parameters
strategy:
  target_delta: 0.15             # Target option delta
  delta_tolerance: 0.02          # Accept 0.13-0.17
  months_ahead: 2                # M+2 expiration
  roll_day: 1                    # First trading day

# Risk Parameters
risk:
  risk_free_rate: 0.05           # 5% annual
  volatility_method: "historical" # or "implied"
  volatility_window: 30          # days for historical vol

# Output Configuration
output:
  date_format: "%-m/%-d/%y"      # Match example format
  include_futures: true          # Add futures price column
  precision: 2                   # Decimal places
```

### Environment Variables
```bash
# Required
export DATABENTO_API_KEY="your_key"

# Optional
export DATABENTO_DATASET="GLBX.MDP3"
export LOG_LEVEL="INFO"
export OUTPUT_DIR="./output"
```

## Usage Examples

### Example 1: Basic Usage
```python
from databento_options_puller import DatabentoOptionsPuller

# Initialize
puller = DatabentoOptionsPuller(
    api_key="your_key",
    config_path="config/config.yaml"
)

# Run for date range
df = puller.run(
    start_date=datetime(2021, 12, 1),
    end_date=datetime(2022, 3, 31)
)

# Save output
puller.save_output(df, "output/results.csv")
```

### Example 2: Custom Parameters
```python
# Override configuration
custom_config = {
    'target_delta': 0.20,  # 20-delta instead of 15
    'volatility_adjustment': 1.1,  # Increase vol by 10%
}

puller = DatabentoOptionsPuller(
    api_key="your_key",
    config=custom_config
)
```

### Example 3: Command Line Usage
```bash
# Basic run
python databento_options_puller.py \
    --start-date "2021-12-01" \
    --end-date "2022-03-31"

# With custom config
python databento_options_puller.py \
    --start-date "2021-12-01" \
    --end-date "2022-03-31" \
    --config "custom_config.yaml" \
    --output "custom_output.csv"

# Verbose logging
python databento_options_puller.py \
    --start-date "2021-12-01" \
    --end-date "2022-03-31" \
    --log-level DEBUG
```

### Example 4: Programmatic Integration
```python
# Use in larger system
class TradingSystem:
    def __init__(self):
        self.options_puller = DatabentoOptionsPuller(
            api_key=os.getenv('DATABENTO_API_KEY')
        )
    
    def update_positions(self, date):
        # Get latest option for rolling
        df = self.options_puller.run(
            start_date=date,
            end_date=date
        )
        
        # Extract today's 15-delta option
        option_cols = [c for c in df.columns if 'C' in c]
        today_option = df[option_cols].iloc[0].dropna()
        
        return today_option.index[0]  # Symbol
```

## API Reference

### Main Classes

#### DatabentoOptionsPuller
```python
class DatabentoOptionsPuller:
    def __init__(self, api_key: str, config: dict = None, config_path: str = None):
        """Initialize puller with API key and configuration."""
    
    def run(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Run full pipeline and return formatted data."""
    
    def save_output(self, df: pd.DataFrame, output_path: str):
        """Save dataframe to CSV with proper formatting."""
```

#### DeltaCalculator
```python
class DeltaCalculator:
    def calculate_delta(self, spot_price: float, strike_price: float, 
                       time_to_expiry: float, volatility: float,
                       option_type: str = 'call') -> float:
        """Calculate option delta using Black-Scholes."""
    
    def find_target_delta_strike(self, spot_price: float, 
                                available_strikes: List[float],
                                time_to_expiry: float, volatility: float,
                                target_delta: float = 0.15) -> Tuple[float, float]:
        """Find strike closest to target delta."""
```

## Testing

### Running Tests
```bash
# Run all tests
python run_tests.py

# Run with coverage
python run_tests.py --coverage

# Run specific test module
python run_tests.py --module test_delta_calculator

# Stop on first failure
python run_tests.py --failfast
```

### Test Structure
```
tests/
├── test_delta_calculator.py    # Unit tests for delta calculations
├── test_data_processing.py     # Tests for data handling
├── test_integration.py         # Integration tests
└── __init__.py
```

### Writing New Tests
```python
import unittest
from src.your_module import YourClass

class TestYourClass(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.instance = YourClass()
    
    def test_basic_functionality(self):
        """Test basic functionality."""
        result = self.instance.method()
        self.assertEqual(result, expected)
```

## Troubleshooting

### Common Issues

#### 1. API Connection Errors
```
Error: databento.common.error.BentoError: Unauthorized
```
**Solution**: Check API key is set correctly:
```bash
echo $DATABENTO_API_KEY
```

#### 2. Missing Data
```
Warning: No options data found for OHG2
```
**Solution**: Some contracts may have limited liquidity. The system will skip and continue.

#### 3. Delta Calculation Issues
```
Warning: Could not find option with delta near 0.15
```
**Solution**: Adjust `delta_tolerance` in config or check volatility estimates.

#### 4. Memory Issues with Large Date Ranges
```
MemoryError: Unable to allocate array
```
**Solution**: Process in smaller chunks:
```python
# Process monthly
for month in pd.date_range(start, end, freq='MS'):
    month_end = month + pd.offsets.MonthEnd(0)
    df = puller.run(month, month_end)
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python databento_options_puller.py --start-date "2021-12-01" --end-date "2021-12-31"

# Check log files
tail -f logs/databento_options_*.log
```

## Performance Optimization

### 1. Caching
The system automatically caches:
- Options chains (5-minute TTL)
- Delta calculations (per session)
- Volatility estimates (per day)

### 2. Batch Processing
```python
# Process multiple months efficiently
puller.batch_process(
    start_date=datetime(2021, 1, 1),
    end_date=datetime(2022, 12, 31),
    chunk_size='1M'  # Monthly chunks
)
```

### 3. Parallel Processing
```python
# Enable parallel option fetching
config = {
    'performance': {
        'parallel_options': True,
        'max_workers': 4
    }
}
```

### 4. Memory Management
- Data is processed in chunks
- Unused DataFrames are explicitly deleted
- Large date ranges are automatically chunked

### 5. API Rate Limiting
- Automatic exponential backoff
- Request queuing
- Configurable rate limits

## Best Practices

1. **Always validate output** against known good data
2. **Monitor API usage** to avoid hitting limits
3. **Use appropriate date ranges** (1-3 months recommended)
4. **Check log files** for warnings about data quality
5. **Test configuration changes** on small date ranges first
6. **Keep volatility estimates updated** for accurate deltas
7. **Version control your configuration** files

## Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review log files in `logs/` directory
3. Run tests to verify installation
4. Contact support with:
   - Full error message
   - Log files
   - Configuration used
   - Date range attempted