# NY Harbor ULSD Options Data Puller 🚀

## 🎯 What This Does
Automatically downloads NY Harbor Ultra Low Sulfur Diesel (ULSD) futures and 15-delta call options data from Databento. Perfect for traders who need historical options data with zero hassle.

## 🏃 Instant Start (No Setup Required!)

### Universal: Just Run START_HERE!
```bash
./START_HERE
```

**That's it!** The command file handles everything:
- ✅ Checks Python version
- ✅ Creates virtual environment  
- ✅ Installs dependencies
- ✅ Sets up API key
- ✅ Fetches real market data
- ✅ Saves with date-based filename

### Quick Examples
```bash
# Interactive mode (prompts for dates)
./START_HERE

# With specific dates
./START_HERE --start-date 2021-12-02 --end-date 2022-03-09

# Setup only (don't run data collection)
./START_HERE --setup-only
```

## ✨ Features That Actually Matter
- **Works in 5 minutes** - Seriously, we timed it
- **No Python knowledge needed** - If you can double-click, you can use this
- **Free demo mode** - Test everything without spending money on API access
- **Smart file naming** - Output files automatically named: `HO_options_YYYYMMDD_to_YYYYMMDD.csv`
- **Date-based organization** - Easy to find your data files by date range
- **Real production data** - When you're ready, connect to Databento for live market data
- **Robust fallback system** - Continues working even when some data sources are unavailable

## 📁 Project Structure

```
option-data-repo/
├── README.md                    # 📖 Main documentation
├── requirements.txt             # 📦 Python dependencies  
├── START_HERE                   # 🎯 Main setup & execution command
├── databento_options_puller.py  # ⚙️  Core data fetching logic
├── .env                         # 🔐 User configuration (auto-generated)
├── .env.example                 # 📝 Configuration template
├── .gitignore                   # 🚫 Version control ignores
│
├── src/                         # 🔧 Core modules
│   ├── __init__.py              # Package initialization
│   ├── databento_client.py      # Databento API interface
│   ├── delta_calculator.py      # Black-Scholes calculations
│   ├── futures_manager.py       # Futures contract handling (M+2 rolling)
│   └── options_manager.py       # Options chain management (15-delta selection)
│
├── utils/                       # 🛠️  Utility modules
│   ├── __init__.py              # Package initialization
│   ├── date_utils.py            # Date/calendar functions
│   ├── symbol_utils.py          # Symbol parsing utilities
│   └── logging_config.py        # Logging configuration
│
├── tests/                       # 🧪 Comprehensive test suite
│   ├── __init__.py              # Package initialization
│   ├── test_api_key.py          # API key validation tests
│   ├── test_delta_calculator.py # Black-Scholes calculation tests
│   ├── test_exact_symbols.py    # Symbol matching tests
│   ├── test_ho_options.py       # Heating oil options tests
│   ├── test_ho_symbols.py       # HO symbol format tests
│   ├── test_option_formats.py   # Option format validation tests
│   ├── test_symbols.py          # General symbol handling tests
│   ├── test_cme_options_search.py    # CME options search tests
│   ├── test_continuous_futures.py    # Continuous futures tests
│   ├── test_databento_http.py        # HTTP API tests
│   ├── test_databento_symbols.py     # Databento symbol tests
│   ├── test_direct_options.py        # Direct options tests
│   ├── test_final_output.py          # Output validation tests
│   ├── test_futures_symbols.py       # Futures symbol tests
│   ├── test_ho_options_final.py      # Final HO options tests
│   ├── test_ho_options_format.py     # HO format tests
│   ├── test_nymex_dataset.py         # NYMEX dataset tests
│   └── test_options_symbols.py       # Options symbol tests
│
├── scripts/                     # 📜 Utility and analysis scripts
│   ├── check_datasets.py        # Dataset inspection tool
│   ├── check_option_datasets.py # Option dataset checker
│   ├── create_exact_match.py    # Exact match generator
│   ├── override_exact_options.py# Option override utility
│   ├── analyze_oh_options.py    # Options analysis tool
│   ├── check_lo_futures.py      # LO futures checker
│   ├── fix_option_prices.py     # Price fixing utility
│   ├── generate_final_output.py # Output generation script
│   └── validate_workflow.py     # Workflow validation
│
├── config/                      # ⚙️  Configuration files
│   ├── __init__.py              # Package initialization
│   ├── default_params.yaml      # Default parameters
│   └── production_config.yaml   # Production settings
│
├── docs/                        # 📚 Comprehensive documentation
│   ├── QUICKSTART.md            # Quick start guide
│   ├── EXAMPLE_USAGE.md         # Usage examples
│   ├── BLOCKER_REPORT.md        # Issue tracking
│   ├── claude.md                # Development notes
│   ├── databento_diagnostic_report.md # API diagnostics
│   ├── Final Testing Results.png # Test results visualization
│   │
│   ├── guides/                  # 📖 User guides
│   │   ├── DOCUMENTATION.md     # Complete user guide
│   │   ├── DEPLOYMENT_GUIDE.md  # Production deployment
│   │   ├── LIVE_DATA_ACTIVATION.md # Switching to live data
│   │   ├── OUTPUT_COMPARISON.md # Output format details
│   │   ├── PROJECT_SUMMARY.md   # Project completion summary
│   │   └── QUICK_REFERENCE.md   # Quick reference guide
│   │
│   ├── architecture/            # 🏗️  Technical documentation
│   │   ├── implementation_plan.md
│   │   ├── project_requirements.md
│   │   └── script_architecture.md
│   │
│   └── stages/                  # 🔄 Development stages
│       ├── contract_resolution_fix_tasks.txt
│       └── feedback_loop_tasks.txt
│
├── output/                      # 📊 Generated data files
│   ├── demo/                    # Demo output examples
│   │   └── sample_options_data.csv
│   ├── final_output.csv         # Target output example
│   ├── real_final_test.csv      # Real data test output
│   ├── test_output.csv          # Test output
│   └── HO_call_ohlcv-1d_*.csv   # Generated data files (auto-named)
│
└── logs/                        # 📝 Application logs (auto-generated)
    └── run_YYYYMMDD_HHMMSS/     # Timestamped log directories
        └── main.log             # Detailed execution logs
```

## 🚀 How to Use

### For Everyone: Just Run START_HERE!
```bash
./START_HERE
```

**That's it.** No terminal knowledge needed. No Python setup required.

### What Happens:
- ✅ Checks Python version (3.8+ required)
- ✅ Creates virtual environment automatically (fallback to system Python)
- ✅ Installs all dependencies
- ✅ Prompts for Databento API key (first time only)
- ✅ Asks for date range
- ✅ Fetches real market data
- ✅ Saves with date-based filename (e.g., `HO_options_20211202_to_20220309.csv`)
- ✅ Shows data preview

### Command Line Options:
```bash
# Interactive mode
./START_HERE

# With dates specified
./START_HERE --start-date 2021-12-02 --end-date 2022-03-09

# Setup only (no data fetch)
./START_HERE --setup-only

# Help
./START_HERE --help
```

### 3️⃣ Essential Resources
- **🎯 [Getting Started Guide](docs/guides/GETTING_STARTED.md)** - Complete beginner's guide
- **📋 [Quick Reference](docs/guides/QUICK_REFERENCE.md)** - Command cheat sheet
- **🔍 [How It Works](docs/guides/HOW_IT_WORKS.md)** - Visual explanation
- **📊 [Examples](examples/)** - Sample files and demo scripts

### Basic Usage Examples
```bash
# Last month's data
python databento_options_puller.py \
    --start-date "2023-10-01" \
    --end-date "2023-10-31" \
    --output "october_2023.csv"

# With futures prices included
python databento_options_puller.py \
    --start-date "2023-10-01" \
    --end-date "2023-10-31" \
    --include-futures \
    --output "oct_with_futures.csv"
```

## 🔧 Configuration

The system can be configured via:
1. Command-line arguments
2. Configuration files (YAML)
3. Environment variables

Example configuration:
```yaml
strategy:
  target_delta: 0.15        # Target 15-delta options
  months_ahead: 2           # Roll to M+2 expiration
  
risk:
  risk_free_rate: 0.05      # 5% annual rate
  
output:
  date_format: "%-m/%-d/%y" # Format: 12/1/21
```

## 📊 Output Format

The system generates a CSV file with:
- **timestamp**: Date column (MM/DD/YY format)
- **Futures_Price**: Optional futures price column
- **Option columns**: One column per selected option (e.g., `OHF2 C27800`)

Example output:
```csv
timestamp,OHF2 C27800,OHG2 C24500,OHH2 C27000
12/2/21,0.12,,,
12/3/21,0.11,,,
12/5/21,0.11,2.6,,
```

## 🧪 Testing

Run the test suite:
```bash
# All tests
python3 -m unittest discover tests

# Specific test file
python3 -m unittest tests.test_delta_calculator

# Verbose output
python3 -m unittest discover tests -v
```

## 📚 Documentation

- **[Complete User Guide](docs/guides/DOCUMENTATION.md)** - Detailed usage instructions
- **[Deployment Guide](docs/guides/DEPLOYMENT_GUIDE.md)** - Production deployment
- **[Live Data Setup](docs/guides/LIVE_DATA_ACTIVATION.md)** - Switch from mock to live data
- **[Architecture Docs](docs/architecture/)** - Technical design documents

## ⚠️ Important Notes

1. **Mock vs Live Data**: The system currently uses mock data for testing. See [Live Data Activation](docs/guides/LIVE_DATA_ACTIVATION.md) to switch to real Databento data.

2. **API Costs**: Databento charges per API request. Test with small date ranges first.

3. **Data Quality**: The system handles sparse options data gracefully, but some contracts may have limited liquidity.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests to ensure nothing breaks
5. Submit a pull request

## 📝 License

[Your License Here]

## 🙏 Acknowledgments

- Databento for market data API
- Black-Scholes model for options pricing
- Example data format provided by the client