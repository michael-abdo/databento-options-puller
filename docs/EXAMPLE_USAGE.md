# Example Usage of NY Harbor ULSD Options Data Puller

## Quick Start Example

The simplest way to get started:

```bash
# Just run this - it handles everything!
python3 START_HERE.py
```

## Step-by-Step Example

### 1. First Time Setup
```bash
$ python3 START_HERE.py --setup-only

============================================================
NY Harbor ULSD Options Data Puller - Setup & Execution
============================================================
✅ Python 3.10.12 detected

📦 Creating virtual environment...
✅ Virtual environment created

📥 Installing dependencies...
✅ All dependencies installed successfully

🔑 Databento API Key Setup
   To use real market data, you need a Databento API key.
   Get one at: https://databento.com/
   Or press Enter to use mock mode for testing.

   Enter your Databento API key: [paste your key here]
✅ API key configured for live data
✅ Configuration saved to .env file

✅ Setup complete! Run this script again with dates to pull data.

Example:
  python START_HERE.py --start-date 2021-12-02 --end-date 2022-03-09
```

### 2. Pull Data with Specific Dates
```bash
$ python3 START_HERE.py --start-date 2021-12-02 --end-date 2022-03-09

============================================================
NY Harbor ULSD Options Data Puller - Setup & Execution
============================================================
✅ Python 3.10.12 detected
✅ Virtual environment already exists
✅ All dependencies installed successfully
✅ Using existing Databento API key (live mode)

🚀 Running data puller from 2021-12-02 to 2022-03-09...

INFO - Starting Databento Options Data Puller
INFO - Initialized real Databento client
INFO - Identified 5 options for the period
INFO - Fetching front-month futures prices...
INFO - Retrieved 1 days of futures data from Databento
INFO - Fetching data for OHG2 C24500: 2021-12-05 to 2022-01-26
INFO - Retrieved 3 days of option data from Databento
INFO - Fetching data for OHH2 C27000: 2022-01-02 to 2022-02-23  
INFO - Retrieved 10 days of option data from Databento

✅ Output saved as: HO_options_20211202_to_20220309.csv
   Full path: /home/user/option-data-repo/output/HO_options_20211202_to_20220309.csv

🎉 Success! Data collection complete.

📊 Summary:
   Date range: 2021-12-02 to 2022-03-09
   Data mode: live
   Output file: /home/user/option-data-repo/output/HO_options_20211202_to_20220309.csv

   Would you like to see the first few rows? (y/n): y

  timestamp Futures_Price OHF2 C27800  ... OHH2 C27000 OHJ2 C30200 OHK2 C35000
0   12/2/21          2.11              ...                                    
1   12/3/21           2.1              ...                                    
2   12/6/21          2.18              ...                                    
3   12/7/21          2.23              ...                                    
4   12/8/21          2.27              ...                                    

   Total rows: 70
   Columns: timestamp, Futures_Price, OHF2 C27800, OHG2 C24500, OHH2 C27000, OHJ2 C30200, OHK2 C35000
```

### 3. Interactive Mode (No Command Line Arguments)
```bash
$ python3 START_HERE.py

============================================================
NY Harbor ULSD Options Data Puller - Setup & Execution
============================================================
✅ Python 3.10.12 detected
✅ Virtual environment already exists
✅ All dependencies installed successfully
✅ Using existing Databento API key (live mode)

📅 Date Range Selection
   Enter the date range for data collection.
   Format: YYYY-MM-DD

   Start date: 2022-01-01
   End date: 2022-02-28

🚀 Running data puller from 2022-01-01 to 2022-02-28...
[... data fetching process ...]

✅ Output saved as: HO_options_20220101_to_20220228.csv
```

## Example Output File

The generated CSV file will look like this:

```csv
timestamp,Futures_Price,OHF2 C27800,OHG2 C24500,OHH2 C27000,OHJ2 C30200,OHK2 C35000
12/2/21,2.11,,,,,
12/3/21,2.1,,,,,
12/6/21,2.18,,,,,
12/7/21,2.23,,,,,
12/8/21,2.27,,,,,
1/5/22,2.5,,0.07,0.03,,
1/10/22,2.6,,0.08,,,
1/11/22,2.55,,0.14,0.03,,
2/1/22,2.8,,,0.1,,
2/2/22,2.85,,,0.12,,
3/3/22,3.1,,,,0.05,
3/4/22,3.2,,,,0.08,
```

### Explanation of Columns:
- **timestamp**: Trading date in M/D/YY format
- **Futures_Price**: NY Harbor ULSD front-month futures price ($/gallon)
- **OHF2 C27800**: Jan 2022 call option with $2.78 strike
- **OHG2 C24500**: Feb 2022 call option with $2.45 strike  
- **OHH2 C27000**: Mar 2022 call option with $2.70 strike
- **OHJ2 C30200**: Apr 2022 call option with $3.02 strike
- **OHK2 C35000**: May 2022 call option with $3.50 strike

## File Naming Convention

Output files are automatically named based on the date range:
- Format: `HO_options_YYYYMMDD_to_YYYYMMDD.csv`
- Examples:
  - `HO_options_20211202_to_20220309.csv`
  - `HO_options_20220101_to_20220228.csv`
  - `HO_options_20210301_to_20210331.csv`

## Troubleshooting Common Issues

### Issue: Virtual Environment Creation Fails
```bash
⚠️  Virtual environment creation failed
   This might be due to missing python3-venv package
   Falling back to installing dependencies in current environment...
```
**Solution**: The script automatically handles this by installing packages in your current Python environment.

### Issue: API Key Not Working
```bash
❌ Error running data puller:
Databento API error: Invalid API key
```
**Solution**: Run setup again to enter a new API key:
```bash
python3 START_HERE.py --setup-only
```

### Issue: No Data Found for Date Range
```bash
⚠️  Data was pulled but output file not found
```
**Solution**: Try a different date range. Some historical periods may have limited data.

## Advanced Usage

### Using Mock Mode for Testing
If you want to test without a real API key:
```bash
# During setup, just press Enter when asked for API key
python3 START_HERE.py --setup-only

# This will use simulated data for testing
python3 START_HERE.py --start-date 2021-12-02 --end-date 2022-03-09
```

### Accessing Raw Data
The system saves detailed logs in the `logs/` directory:
```bash
ls logs/
# run_20211202_143022/
# run_20211203_091545/

cat logs/run_20211202_143022/main.log
```

### Multiple Date Ranges
You can run multiple date ranges to create separate files:
```bash
# Q4 2021
python3 START_HERE.py --start-date 2021-10-01 --end-date 2021-12-31

# Q1 2022  
python3 START_HERE.py --start-date 2022-01-01 --end-date 2022-03-31

# Results in:
# HO_options_20211001_to_20211231.csv
# HO_options_20220101_to_20220331.csv
```

## What's Happening Behind the Scenes

1. **Option Selection**: System uses Black-Scholes to find 15-delta call options
2. **Rolling Strategy**: On first trading day of month M, selects options expiring in month M+2
3. **Data Sources**: Fetches from Databento GLBX.MDP3 dataset (CME Globex)
4. **Futures Data**: Uses continuous front-month contract (HO.c.0)
5. **Options Data**: Real market prices for selected strikes
6. **Date Handling**: Automatically filters to trading days only