# 🚀 Getting Started with Databento Options Puller

This guide will have you pulling options data in under 5 minutes!

## 📋 Quick Overview

The Databento Options Puller automatically:
- Finds 15-delta call options for NY Harbor ULSD (OH) futures
- Rolls to new options monthly (M+2 expiration)
- Outputs clean CSV data matching your exact format

## 🎯 Prerequisites

- **Python 3.8+** installed
- **Databento API key** (for live data - optional for testing)
- **Basic command line knowledge**

## ⚡ 5-Minute Quick Start

### 1️⃣ Clone and Setup (1 minute)
```bash
# Clone the project
git clone <repository-url>
cd databento_options_project

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2️⃣ Install Dependencies (1 minute)
```bash
pip install -r requirements.txt
```

### 3️⃣ Run Your First Test (1 minute)
```bash
# Test with mock data (no API key needed!)
python databento_options_puller.py \
    --start-date "2021-12-01" \
    --end-date "2021-12-31" \
    --output "my_first_output.csv"
```

### 4️⃣ Check Your Output (30 seconds)
```bash
# View the generated CSV
head my_first_output.csv
```

You should see:
```csv
timestamp,OHF2 C27800,OHG2 C24500,...
12/1/21,0.12,,,
12/2/21,0.11,,,
...
```

### 5️⃣ Verify Everything Works (1.5 minutes)
```bash
# Run tests to ensure setup is correct
python run_tests.py
```

## 📊 Understanding the Output

Your CSV will contain:
- **timestamp**: Dates in MM/D/YY format
- **Option columns**: Like `OHF2 C27800` where:
  - `OH` = NY Harbor ULSD
  - `F2` = February 2022 expiry
  - `C27800` = Call option with $2.78 strike

## 🔧 Common Use Cases

### Case 1: Get Last Month's Data
```bash
python databento_options_puller.py \
    --start-date "2023-10-01" \
    --end-date "2023-10-31" \
    --output "october_2023.csv"
```

### Case 2: Get Quarterly Data
```bash
python databento_options_puller.py \
    --start-date "2023-07-01" \
    --end-date "2023-09-30" \
    --output "Q3_2023.csv"
```

### Case 3: Include Futures Prices
```bash
python databento_options_puller.py \
    --start-date "2023-10-01" \
    --end-date "2023-10-31" \
    --include-futures \
    --output "oct_with_futures.csv"
```

## 🔄 Switching to Live Data

Currently using mock data? Here's how to use real market data:

### Step 1: Get Databento API Key
Sign up at [databento.com](https://databento.com) for an API key.

### Step 2: Set Your API Key
```bash
export DATABENTO_API_KEY="your_actual_key_here"
```

### Step 3: Enable Live Data
```bash
# Edit config/config.yaml
databento:
  use_mock: false  # Change from true to false
```

### Step 4: Test with Small Date Range
```bash
python databento_options_puller.py \
    --start-date "2023-10-01" \
    --end-date "2023-10-07" \
    --output "test_live.csv"
```

## 🎯 What is 15-Delta?

**Delta** measures how much an option price changes when the underlying moves $1.
- **15-delta** = Option price increases ~$0.15 for each $1 increase in futures
- These are out-of-the-money options with ~15% chance of expiring in-the-money
- Popular for hedging and income strategies

## 📅 Understanding the Rolling Strategy

The system automatically:
1. **First trading day of month**: Identifies new options to buy
2. **Targets M+2 expiry**: In December, selects February options
3. **Finds 15-delta strike**: Calculates which strike has ~0.15 delta
4. **Tracks until next roll**: Continues pricing until next month's roll

Example Timeline:
- Dec 1: Buy `OHF2 C27800` (Feb expiry, $2.78 strike)
- Jan 1: Buy `OHG2 C24500` (Mar expiry, $2.45 strike)
- Feb 1: Buy `OHH2 C27000` (Apr expiry, $2.70 strike)

## 🛠️ Configuration Options

### Basic Config (`config/config.yaml`)
```yaml
strategy:
  target_delta: 0.15      # Change to 0.20 for 20-delta
  months_ahead: 2         # Change to 3 for M+3 expiry

output:
  include_futures: false  # Set true to add futures column
  date_format: "%-m/%-d/%y"  # US format
```

### Run with Custom Config
```bash
python databento_options_puller.py \
    --config my_config.yaml \
    --start-date "2023-10-01" \
    --end-date "2023-10-31"
```

## 🐛 Troubleshooting

### "No data available"
- Check your date range includes trading days
- Verify the contract was active during that period
- For live data, check API key is set correctly

### "Import error: databento"
```bash
pip install databento  # If using live data
```

### "Tests failing"
- Normal with mock data - some calculations need adjustment
- Core functionality still works

### Need More Details?
Check `logs/databento_options_*.log` for detailed debugging info.

## 📚 Next Steps

1. **Read the Docs**:
   - [Full Documentation](docs/guides/DOCUMENTATION.md) - Complete feature guide
   - [Deployment Guide](docs/guides/DEPLOYMENT_GUIDE.md) - Production setup

2. **Explore Examples**:
   - Check `examples/example_output.csv` to see expected format
   - Run `examples/live_data_demo.py` for more examples

3. **Customize**:
   - Modify `config/config.yaml` for different strategies
   - Adjust delta targets, date formats, etc.

## 💡 Pro Tips

1. **Start Small**: Test with 1-week date ranges first
2. **Check Logs**: Enable debug mode with `--log-level DEBUG`
3. **Validate Output**: Compare with `examples/example_output.csv`
4. **Monitor Costs**: Databento charges per API request

## 🆘 Getting Help

- **Issues?** Check [Troubleshooting](#-troubleshooting) above
- **Logs:** Look in `logs/` directory for detailed errors
- **Examples:** See `examples/` directory for working samples

---

**Ready to pull some options data? You're all set! 🎉**

Start with the [5-Minute Quick Start](#-5-minute-quick-start) above and you'll be generating options data in no time!