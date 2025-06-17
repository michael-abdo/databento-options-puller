# 📋 Quick Reference Card

## 🚀 Essential Commands

### Basic Run
```bash
python databento_options_puller.py \
    --start-date "YYYY-MM-DD" \
    --end-date "YYYY-MM-DD" \
    --output "filename.csv"
```

### Common Examples
```bash
# Last month
python databento_options_puller.py \
    --start-date "2023-10-01" \
    --end-date "2023-10-31" \
    --output "oct_2023.csv"

# With futures prices
python databento_options_puller.py \
    --start-date "2023-10-01" \
    --end-date "2023-10-31" \
    --include-futures \
    --output "oct_with_futures.csv"

# Custom config
python databento_options_puller.py \
    --config config/production.yaml \
    --start-date "2023-10-01" \
    --end-date "2023-10-31"

# Debug mode
python databento_options_puller.py \
    --start-date "2023-10-01" \
    --end-date "2023-10-31" \
    --log-level DEBUG
```

## 📊 Output Format

```csv
timestamp,OHF2 C27800,OHG2 C24500,OHH2 C27000
12/1/21,0.12,,,
12/2/21,0.11,,,
12/5/21,0.11,2.6,,
```

## 🔧 Key Options

| Option | Description | Example |
|--------|-------------|---------|
| `--start-date` | Start date (YYYY-MM-DD) | `2023-10-01` |
| `--end-date` | End date (YYYY-MM-DD) | `2023-10-31` |
| `--output` | Output CSV filename | `results.csv` |
| `--config` | Config file path | `config/custom.yaml` |
| `--include-futures` | Add futures price column | (flag only) |
| `--log-level` | Logging verbosity | `DEBUG`, `INFO`, `WARNING` |

## 🎯 Symbol Decoder

`OHF2 C27800` means:
- `OH` = NY Harbor ULSD
- `F` = February
- `2` = 2022
- `C` = Call option
- `27800` = $2.78 strike price

### Month Codes
| Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| F   | G   | H   | J   | K   | M   | N   | Q   | U   | V   | X   | Z   |

## ⚡ Environment Setup

```bash
# One-time setup
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# For live data
export DATABENTO_API_KEY="your_key_here"
```

## 🧪 Testing

```bash
# Run all tests
python run_tests.py

# Specific test
python run_tests.py --module test_delta_calculator

# With coverage
python run_tests.py --coverage
```

## 📁 Key Files

- `databento_options_puller.py` - Main script
- `config/config.yaml` - Default settings
- `examples/example_output.csv` - Expected format
- `logs/` - Debug information
- `output/` - Your generated files

## 🔄 Mock vs Live Data

### Currently Using Mock Data?
```yaml
# In config/config.yaml
databento:
  use_mock: true  # Change to false for live
```

### Switch to Live
1. Get API key from databento.com
2. `export DATABENTO_API_KEY="your_key"`
3. Set `use_mock: false` in config
4. Test with small date range first!

## 🆘 Quick Fixes

| Problem | Solution |
|---------|----------|
| "No data" | Check date is trading day |
| "Import error" | `pip install databento` |
| "API error" | Check DATABENTO_API_KEY |
| "Wrong format" | Check date_format in config |

---
**Need more?** See [GETTING_STARTED.md](GETTING_STARTED.md) or [docs/guides/DOCUMENTATION.md](docs/guides/DOCUMENTATION.md)