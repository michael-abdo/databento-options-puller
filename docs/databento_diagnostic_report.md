# Databento HO Options Data Diagnostic Report

## Issue Summary
Unable to retrieve NY Harbor ULSD (HO) options data from Databento GLBX.MDP3 dataset, while futures data is successfully retrieved.

## Test Results

### ✅ Successful Tests
1. **Databento API Connection**: Connected successfully with API key
2. **Futures Data Retrieval**: Successfully retrieved OHLCV data for:
   - HOF2 (Jan 2022): Close price $2.0743
   - HOG2 (Feb 2022): Close price $2.0807  
   - HOH2 (Mar 2022): Close price $2.0825

### ❌ Failed Tests
1. **Options Symbol Formats Tested** (all returned no data):
   - `HOG2 2250C`, `HOG2 2500C`, `HOG2 3250C` (CME-style)
   - `HOG22250C`, `HOG22500C` (no spaces)
   - `HOG2-2250C`, `HOG2_2250C` (with separators)
   - `OHG2 C00325`, `OHG2C00325` (requirements format)
   - `HO 220218C00325000` (OPRA-style)

2. **Parent Symbol Resolution**:
   - `HO.OPT` returns error: "Could not resolve smart symbols"
   - `HO` as parent returns error: "expected format: '[ROOT].FUT' or '[ROOT].OPT'"

3. **Instrument Definitions**:
   - No HO-related instruments found in first 1000 definitions
   - No options with instrument_class 'C' or 'P' for HO

## Diagnosis
The GLBX.MDP3 dataset appears to contain NY Harbor ULSD **futures** data but not **options** data. This could be because:

1. CME HO options are not included in GLBX.MDP3
2. Options require a different dataset (e.g., separate options feed)
3. Options use a different symbology we haven't discovered

## Recommendations

### Immediate Actions
1. **Contact Databento Support** with this specific query:
   - "How to access NY Harbor ULSD (HO) options data from CME/NYMEX?"
   - "Which dataset contains CME energy options?"
   - "What is the correct symbol format for HO options?"

2. **Check Alternative Datasets**:
   - OPRA datasets for options
   - ICE datasets (if HO options trade on ICE)
   - Specific CME options feeds

### Workaround Options
If HO options data is truly unavailable:
1. Use a different data provider (e.g., CME DataMine, Refinitiv)
2. Calculate synthetic option prices using Black-Scholes
3. Source historical options data from another vendor

## Code References
- Futures data working: `test_nymex_dataset.py:50`
- Options tests failed: `test_direct_options.py:41`
- API connection verified: `src/databento_client.py:62`