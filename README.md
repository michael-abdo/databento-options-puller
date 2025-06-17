# Databento Options Puller - Zero Setup Required! 🚀

## 🎯 What This Does
Automatically downloads options trading data and saves it as a spreadsheet. Perfect for traders who need historical options data without the hassle.

## 🏃 Instant Start (No Setup!)

### For Mac Users - Just Double-Click!
1. Find the file `CLICK_ME_TO_START.command` in this folder
2. Double-click it
3. That's it! Everything installs automatically

### Alternative: Run the Demo First
```bash
python3 simple_demo.py
```
This works immediately without any setup and shows you what the tool does.

## ✨ Features That Actually Matter
- **Works in 5 minutes** - Seriously, we timed it
- **No Python knowledge needed** - If you can double-click, you can use this
- **Free demo mode** - Test everything without spending money on API access
- **Excel-ready output** - Opens directly in Excel/Numbers
- **Real production data** - When you're ready, connect to Databento for live market data

## 📁 Project Structure

```
databento_options_project/
├── databento_options_puller.py  # Main executable
├── requirements.txt             # Python dependencies
├── setup.py                     # Package installation
├── run_tests.py                 # Test runner
├── README.md                    # This file
│
├── src/                         # Core modules
│   ├── databento_client.py      # Databento API interface
│   ├── delta_calculator.py      # Black-Scholes calculations
│   ├── futures_manager.py       # Futures contract handling
│   ├── options_manager.py       # Options chain management
│   ├── option_generator.py      # Output generation logic
│   ├── example_analyzer.py      # Example data analysis
│   ├── output_validator.py      # Output validation
│   └── parameter_refiner.py     # Parameter optimization
│
├── tests/                       # Test suite
│   ├── test_delta_calculator.py # Unit tests for delta calc
│   ├── test_data_processing.py  # Data handling tests
│   └── test_integration.py      # Integration tests
│
├── config/                      # Configuration files
│   ├── config.yaml              # Default configuration
│   └── production_config.yaml   # Production settings
│
├── utils/                       # Utility modules
│   ├── date_utils.py            # Date/calendar functions
│   ├── symbol_utils.py          # Symbol parsing
│   └── logging_config.py        # Logging setup
│
├── docs/                        # Documentation
│   ├── guides/                  # User guides
│   │   ├── DOCUMENTATION.md     # Complete user guide
│   │   ├── DEPLOYMENT_GUIDE.md  # Production deployment
│   │   ├── LIVE_DATA_ACTIVATION.md # Switching to live data
│   │   ├── OUTPUT_COMPARISON.md # Output format details
│   │   └── PROJECT_SUMMARY.md   # Project completion summary
│   ├── architecture/            # Technical docs
│   │   ├── implementation_plan.md
│   │   ├── project_requirements.md
│   │   └── script_architecture.md
│   └── stages/                  # Development stages
│
├── examples/                    # Example files
│   ├── example_output.csv       # Target output format
│   ├── live_heating_oil_data.csv# Sample market data
│   ├── test_output.csv          # Test results
│   └── live_data_demo.py        # Demo script
│
├── output/                      # Generated outputs
│   └── [generated files]
│
├── logs/                        # Application logs
└── archive/                     # Archived files
```

## 🚀 Three Ways to Start

### Option 1: The "I Don't Know Terminal" Method
1. Double-click `CLICK_ME_TO_START.command`
2. Follow the prompts
3. Done!

### Option 2: The "Show Me First" Method
1. Open Terminal (Command+Space, type "Terminal")
2. Drag this folder onto the Terminal window
3. Type: `python3 simple_demo.py`
4. See sample output immediately

### Option 3: The "I Know What I'm Doing" Method
```bash
./setup_mac.sh
./run.sh
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

Run the comprehensive test suite:
```bash
# All tests
python run_tests.py

# With coverage
python run_tests.py --coverage

# Specific module
python run_tests.py --module test_delta_calculator
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