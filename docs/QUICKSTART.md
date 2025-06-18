# Quick Start Guide

## Complete Setup in 3 Commands

### 1. Make START_HERE executable (one time only)
```bash
chmod +x START_HERE
```

### 2. Run setup (one time only)
```bash
./START_HERE --setup-only
```

### 3. Pull data
```bash
./START_HERE --start-date 2021-12-02 --end-date 2022-03-09
```

That's it! Your data will be saved as `HO_options_20211202_to_20220309.csv`

---

## Interactive Mode

If you prefer to be prompted for dates:

```bash
./START_HERE
```

You'll see:
```
📅 Date Range Selection
   Enter the date range for data collection.
   Format: YYYY-MM-DD

   Start date: 2021-12-02
   End date: 2022-03-09
```

---

## What You Get

A CSV file with real market data:

```csv
timestamp,Futures_Price,OHF2 C27800,OHG2 C24500,OHH2 C27000,OHJ2 C30200,OHK2 C35000
12/2/21,2.11,,,,,
12/3/21,2.1,,,,,
1/5/22,2.5,,0.07,0.03,,
1/10/22,2.6,,0.08,,,
```

**Columns:**
- `timestamp`: Trading date (M/D/YY format)
- `Futures_Price`: NY Harbor ULSD front-month futures ($/gallon)
- `OHX# C#####`: 15-delta call options for different months

---

## Help & Troubleshooting

```bash
./START_HERE --help    # Show all options
```

**Common Issues:**

1. **Permission denied**: Run `chmod +x START_HERE`
2. **Python not found**: Install Python 3.8+ from python.org
3. **No data**: Try different date ranges, some periods have limited options data

**Need help?** Check the logs in `logs/` directory for detailed error messages.

---

Ready to start? Just run: `./START_HERE` 🚀