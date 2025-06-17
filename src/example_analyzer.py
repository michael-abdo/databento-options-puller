"""
Example Analyzer module for extracting facts from example_output.csv
This is the first step in the feedback loop - understanding what we need to replicate.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging
from pathlib import Path
import json

# Add parent directory to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.date_utils import parse_date, format_date, count_trading_days
from utils.symbol_utils import parse_option_symbol, extract_month_year, extract_strike
from utils.logging_config import get_logger

logger = get_logger('analyzer')


class ExampleAnalyzer:
    """Extract all observable facts from example_output.csv"""
    
    def __init__(self, example_path: str = 'example_output.csv'):
        """
        Initialize analyzer with path to example CSV.
        
        Args:
            example_path: Path to example_output.csv
        """
        self.example_path = example_path
        self.df = None
        self.facts = {}
        
        logger.info(f"Initialized ExampleAnalyzer with {example_path}")
    
    def analyze(self) -> Dict:
        """
        Main analysis method - extracts all facts from example.
        
        Returns:
            Dictionary containing all discovered facts
        """
        logger.info("="*60)
        logger.info("Starting analysis of example output")
        logger.info("="*60)
        
        # Load the CSV
        self._load_data()
        
        # Extract various facts
        self.facts = {
            'basic_info': self._extract_basic_info(),
            'option_symbols': self._extract_option_symbols(),
            'active_periods': self._extract_active_periods(),
            'roll_schedule': self._extract_roll_schedule(),
            'price_patterns': self._extract_price_patterns(),
            'timing_patterns': self._extract_timing_patterns(),
            'data_statistics': self._extract_data_statistics()
        }
        
        # Log summary
        self._log_summary()
        
        # Save facts to file for reference
        self._save_facts()
        
        return self.facts
    
    def _load_data(self):
        """Load and perform initial inspection of the CSV."""
        logger.info(f"Loading {self.example_path}")
        
        self.df = pd.read_csv(self.example_path)
        
        logger.info(f"Loaded {len(self.df)} rows, {len(self.df.columns)} columns")
        logger.info(f"Columns: {list(self.df.columns)}")
        logger.info(f"Date range: {self.df['timestamp'].iloc[0]} to {self.df['timestamp'].iloc[-1]}")
    
    def _extract_basic_info(self) -> Dict:
        """Extract basic information about the dataset."""
        info = {
            'num_rows': len(self.df),
            'num_columns': len(self.df.columns),
            'date_range': {
                'start': self.df['timestamp'].iloc[0],
                'end': self.df['timestamp'].iloc[-1],
                'num_days': len(self.df)
            },
            'has_futures_column': 'Futures_Price' in self.df.columns
        }
        
        logger.info(f"Basic info: {info}")
        return info
    
    def _extract_option_symbols(self) -> List[Dict]:
        """Extract and parse all option symbols."""
        symbols = []
        
        # Get all columns that contain option symbols (have 'C' or 'P')
        option_cols = [col for col in self.df.columns 
                      if col not in ['timestamp', 'Futures_Price'] and ('C' in col or 'P' in col)]
        
        logger.info(f"Found {len(option_cols)} option symbols")
        
        for symbol in option_cols:
            try:
                parsed = parse_option_symbol(symbol)
                symbols.append(parsed)
                
                logger.info(f"Parsed {symbol}: {parsed['root']}{parsed['month_code']}{parsed['year_code']} "
                          f"{parsed['option_type']} Strike={parsed['strike']}")
            except Exception as e:
                logger.error(f"Failed to parse symbol {symbol}: {e}")
        
        return symbols
    
    def _extract_active_periods(self) -> Dict[str, Dict]:
        """Find when each option is active (non-null values)."""
        periods = {}
        
        option_cols = [col for col in self.df.columns 
                      if col not in ['timestamp', 'Futures_Price']]
        
        for symbol in option_cols:
            # Find first and last non-null indices
            non_null_mask = self.df[symbol].notna()
            
            if non_null_mask.any():
                first_idx = non_null_mask.idxmax()
                # Find last True value
                last_idx = len(self.df) - 1 - non_null_mask.iloc[::-1].idxmax()
                
                first_date = self.df.loc[first_idx, 'timestamp']
                last_date = self.df.loc[last_idx, 'timestamp']
                
                # Count trading days
                trading_days = non_null_mask.sum()
                
                periods[symbol] = {
                    'first_date': first_date,
                    'last_date': last_date,
                    'first_idx': int(first_idx),
                    'last_idx': int(last_idx),
                    'trading_days': int(trading_days),
                    'calendar_days': int(last_idx - first_idx + 1)
                }
                
                logger.info(f"{symbol}: {first_date} to {last_date} "
                          f"({trading_days} trading days)")
        
        return periods
    
    def _extract_roll_schedule(self) -> List[Dict]:
        """Identify when positions roll from one option to another."""
        rolls = []
        
        # Get symbols ordered by first appearance
        periods = self._extract_active_periods()
        symbols_by_start = sorted(periods.items(), 
                                 key=lambda x: x[1]['first_idx'])
        
        for i in range(len(symbols_by_start) - 1):
            curr_symbol, curr_period = symbols_by_start[i]
            next_symbol, next_period = symbols_by_start[i + 1]
            
            # Check for overlap
            overlap_start = max(curr_period['first_idx'], next_period['first_idx'])
            overlap_end = min(curr_period['last_idx'], next_period['last_idx'])
            
            if overlap_start <= overlap_end:
                overlap_days = overlap_end - overlap_start + 1
            else:
                overlap_days = 0
            
            roll_info = {
                'from_symbol': curr_symbol,
                'to_symbol': next_symbol,
                'roll_date': next_period['first_date'],
                'roll_idx': next_period['first_idx'],
                'overlap_days': overlap_days,
                'from_expiry': extract_month_year(curr_symbol),
                'to_expiry': extract_month_year(next_symbol)
            }
            
            rolls.append(roll_info)
            
            logger.info(f"Roll: {curr_symbol} -> {next_symbol} on {next_period['first_date']} "
                      f"(overlap: {overlap_days} days)")
        
        return rolls
    
    def _extract_price_patterns(self) -> Dict:
        """Analyze price patterns in the data."""
        patterns = {}
        
        option_cols = [col for col in self.df.columns 
                      if col not in ['timestamp', 'Futures_Price']]
        
        for symbol in option_cols:
            prices = self.df[symbol].dropna()
            
            if len(prices) > 0:
                patterns[symbol] = {
                    'first_price': float(prices.iloc[0]),
                    'last_price': float(prices.iloc[-1]),
                    'min_price': float(prices.min()),
                    'max_price': float(prices.max()),
                    'mean_price': float(prices.mean()),
                    'std_price': float(prices.std()),
                    'price_direction': 'up' if prices.iloc[-1] > prices.iloc[0] else 'down'
                }
                
                logger.debug(f"{symbol} prices: first={prices.iloc[0]:.2f}, "
                           f"last={prices.iloc[-1]:.2f}, range=[{prices.min():.2f}, {prices.max():.2f}]")
        
        return patterns
    
    def _extract_timing_patterns(self) -> Dict:
        """Extract patterns related to timing and scheduling."""
        patterns = {
            'month_progression': [],
            'strikes': [],
            'typical_duration': 0,
            'roll_frequency': []
        }
        
        symbols = self._extract_option_symbols()
        
        # Extract month progression
        for sym in symbols:
            month_year = (sym['month'], sym['year'])
            patterns['month_progression'].append(month_year)
            patterns['strikes'].append(sym['strike'])
        
        # Calculate typical duration
        periods = self._extract_active_periods()
        if periods:
            durations = [p['trading_days'] for p in periods.values()]
            patterns['typical_duration'] = sum(durations) / len(durations)
        
        # Analyze roll frequency
        rolls = self._extract_roll_schedule()
        for i in range(1, len(rolls)):
            days_between = rolls[i]['roll_idx'] - rolls[i-1]['roll_idx']
            patterns['roll_frequency'].append(days_between)
        
        logger.info(f"Month progression: {patterns['month_progression']}")
        logger.info(f"Strikes: {patterns['strikes']}")
        logger.info(f"Typical duration: {patterns['typical_duration']:.1f} days")
        
        return patterns
    
    def _extract_data_statistics(self) -> Dict:
        """Calculate various statistics about the data."""
        stats = {
            'total_data_points': 0,
            'non_null_counts': {},
            'null_patterns': {},
            'date_gaps': []
        }
        
        # Count non-null values per column
        for col in self.df.columns:
            if col != 'timestamp':
                non_null = self.df[col].notna().sum()
                stats['non_null_counts'][col] = int(non_null)
                stats['total_data_points'] += non_null
        
        # Check for date gaps (non-trading days)
        dates = pd.to_datetime(self.df['timestamp'], format='%m/%d/%y')
        for i in range(1, len(dates)):
            gap = (dates.iloc[i] - dates.iloc[i-1]).days
            if gap > 1:
                stats['date_gaps'].append({
                    'from': format_date(dates.iloc[i-1]),
                    'to': format_date(dates.iloc[i]),
                    'gap_days': int(gap)
                })
        
        logger.info(f"Total data points: {stats['total_data_points']}")
        logger.info(f"Date gaps found: {len(stats['date_gaps'])}")
        
        return stats
    
    def _log_summary(self):
        """Log a comprehensive summary of findings."""
        logger.info("="*60)
        logger.info("ANALYSIS SUMMARY")
        logger.info("="*60)
        
        logger.info(f"Options found: {len(self.facts['option_symbols'])}")
        
        for symbol in self.facts['option_symbols']:
            logger.info(f"  - {symbol['full_symbol']}")
        
        logger.info(f"Roll events: {len(self.facts['roll_schedule'])}")
        logger.info(f"Date range: {self.facts['basic_info']['date_range']['start']} to "
                   f"{self.facts['basic_info']['date_range']['end']}")
        
        logger.info("="*60)
    
    def _save_facts(self):
        """Save extracted facts to JSON file for reference."""
        output_path = Path('output') / 'extracted_facts.json'
        output_path.parent.mkdir(exist_ok=True)
        
        # Convert facts to JSON-serializable format
        facts_json = json.dumps(self.facts, indent=2, default=str)
        
        with open(output_path, 'w') as f:
            f.write(facts_json)
        
        logger.info(f"Saved extracted facts to {output_path}")


def main():
    """Test the analyzer independently."""
    import sys
    sys.path.append('..')
    
    from utils.logging_config import setup_logging
    
    # Set up logging
    setup_logging()
    
    # Create analyzer
    analyzer = ExampleAnalyzer()
    
    # Run analysis
    facts = analyzer.analyze()
    
    print("\nAnalysis complete! Check logs/analyzer_*.log for details.")
    print(f"Found {len(facts['option_symbols'])} options")
    print(f"Found {len(facts['roll_schedule'])} roll events")


if __name__ == "__main__":
    main()