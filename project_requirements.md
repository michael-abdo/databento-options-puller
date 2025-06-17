# Databento Options Data Project Requirements

## Project Overview
Create a Python script to pull and format NY Harbor ULSD (OH) futures and 15-delta call options data from Databento into a single CSV file.

## Key Features
- 📊 Pull daily OHLCV data from Databento API
- 🎯 Automatic 15-delta strike identification
- 🔄 Rolling monthly strategy logic
- 🚀 Single CSV output with clean formatting

## Project Goal
Create a single CSV file containing:
1. Daily prices for NY Harbor ULSD (OH) futures (front-month contract)
2. Specific 15-delta call options used in a rolling monthly strategy

## Required Logic

For each month in the date range (start_date to end_date):

### 1. Identify Target Option
- On the first trading day of Month M, target options for Month M+2 expiration
- Example: On July 1, 2025, target September 2025 (OHU5) contracts

### 2. Find Specific Strike
- Calculate delta for all available call strikes
- Select the strike closest to 0.15 delta

### 3. Pull Price History
- Retrieve complete daily price history (ohlcv-1d)
- Data range: From identification day until option expiry

## Output Format

### CSV Structure
- **Column A**: `timestamp` (Date)
- **Column B**: `Futures_Price` (Front-month futures daily price)
- **Columns C+**: One column per identified 15-delta option
  - Header: Full instrument symbol (e.g., `OHU5 C31500`)
  - Data: Prices only for dates when option was active

### Example Output Structure
```
timestamp,Futures_Price,OHF2 C27800,OHG2 C24500,OHH2 C27000,OHJ2 C30200
2021-12-02,2.458,0.12,,,,
2021-12-03,2.471,0.11,,,,
2021-12-05,2.485,0.11,2.6,,,
...
```

## Technical Requirements

### Databento API Integration
- Use Databento Python client
- Handle API rate limits
- Implement error handling and retries

### Delta Calculation
- Use appropriate pricing model (likely Black-Scholes)
- Account for:
  - Underlying price
  - Strike price
  - Time to expiration
  - Volatility
  - Risk-free rate

### Data Processing
- Handle missing data gracefully
- Ensure proper date alignment
- Validate data integrity

## Deliverables

1. **Python Script** (`databento_options_puller.py`)
   - Modular, well-documented code
   - Command-line interface with start/end date parameters
   - Progress tracking and logging

2. **Output CSV File**
   - Single file with all data
   - Properly formatted dates
   - No missing values where data should exist

3. **Documentation**
   - Setup instructions
   - Usage examples
   - Data validation notes

## Strategy Details

### Rolling Logic
- Monthly rolls on first trading day
- Always target M+2 expiration
- Hold position until next roll date

### Option Selection Criteria
- Call options only
- Target delta: 0.15 (±0.02 tolerance)
- If exact 0.15 unavailable, choose closest

## Data Validation Requirements
- Ensure futures prices exist for all trading days
- Verify option prices during active periods
- Flag any data anomalies or gaps