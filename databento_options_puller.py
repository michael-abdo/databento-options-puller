#!/usr/bin/env python3
"""
Databento Options Data Puller

Production script to pull NY Harbor ULSD (OH) futures and 15-delta call options data
from Databento API and generate a single CSV output.

Usage:
    python databento_options_puller.py --start-date 2021-12-01 --end-date 2022-03-31 --output output.csv
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / 'src'))
sys.path.append(str(Path(__file__).parent))

from src.databento_client import DatabentoBridge
from src.delta_calculator import DeltaCalculator
from src.futures_manager import FuturesManager
from src.options_manager import OptionsManager
from utils.logging_config import setup_logging, get_logger


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Pull NY Harbor ULSD (OH) futures and 15-delta call options data from Databento"
    )
    
    # Date range (required unless --demo)
    parser.add_argument(
        '--start-date', 
        type=str,
        help='Start date in YYYY-MM-DD format (e.g., 2021-12-01)'
    )
    parser.add_argument(
        '--end-date', 
        type=str,
        help='End date in YYYY-MM-DD format (e.g., 2022-03-31)'
    )
    
    # Output file
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='databento_options_output.csv',
        help='Output CSV file path (default: databento_options_output.csv)'
    )
    
    # API configuration
    parser.add_argument(
        '--api-key',
        type=str,
        help='Databento API key (or set DATABENTO_API_KEY environment variable)'
    )
    
    # Mode selection
    parser.add_argument(
        '--mock-mode',
        action='store_true',
        help='Use mock data instead of real Databento API calls'
    )
    
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run quick demo showing sample output format'
    )
    
    # Strategy parameters
    parser.add_argument(
        '--target-delta',
        type=float,
        default=0.15,
        help='Target delta for option selection (default: 0.15)'
    )
    
    parser.add_argument(
        '--risk-free-rate',
        type=float,
        default=0.05,
        help='Risk-free rate for delta calculations (default: 0.05)'
    )
    
    # Logging
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress console output except errors'
    )
    
    return parser.parse_args()


def validate_arguments(args):
    """Validate command line arguments."""
    # Skip validation for demo mode
    if args.demo:
        return True
        
    # Check required arguments
    if not args.start_date or not args.end_date:
        raise ValueError("--start-date and --end-date are required")
    
    # Validate date formats
    try:
        datetime.strptime(args.start_date, '%Y-%m-%d')
        datetime.strptime(args.end_date, '%Y-%m-%d')
    except ValueError as e:
        raise ValueError(f"Invalid date format. Use YYYY-MM-DD: {e}")
    
    # Check API key
    api_key = args.api_key or os.getenv('DATABENTO_API_KEY')
    if not api_key and not args.mock_mode:
        raise ValueError("Databento API key required. Set DATABENTO_API_KEY environment variable or use --api-key")
    
    return True


def setup_components(args):
    """Initialize all components based on arguments."""
    logger = get_logger('main')
    
    # Initialize Databento client
    if args.mock_mode:
        logger.info("Using mock Databento client")
        databento_client = DatabentoBridge(api_key=None)  # Force mock mode
    else:
        api_key = args.api_key or os.getenv('DATABENTO_API_KEY')
        logger.info("Initializing real Databento client")
        databento_client = DatabentoBridge(api_key)
    
    # Initialize calculators
    delta_calculator = DeltaCalculator(risk_free_rate=args.risk_free_rate)
    
    # Initialize managers
    futures_manager = FuturesManager()
    
    options_manager = OptionsManager(
        databento_client=databento_client,
        futures_manager=futures_manager,
        delta_calculator=delta_calculator
    )
    
    # Set target delta on options manager
    options_manager.target_delta = args.target_delta
    
    logger.info(f"Initialized components (target_delta={args.target_delta:.2f}, risk_free_rate={args.risk_free_rate:.2%})")
    
    return {
        'databento_client': databento_client,
        'delta_calculator': delta_calculator,
        'futures_manager': futures_manager,
        'options_manager': options_manager
    }


def run_data_pull(args, components, output_path):
    """Run the data pull with Databento."""
    logger = get_logger('main')
    logger.info(f"Running data pull: {args.start_date} to {args.end_date}")
    
    # Get monthly option selections
    options_manager = components['options_manager']
    selected_options = options_manager.identify_monthly_options(
        start_date=args.start_date,
        end_date=args.end_date
    )
    
    if not selected_options:
        raise RuntimeError("No options identified by strategy")
    
    logger.info(f"Identified {len(selected_options)} options for the period")
    
    # Create dataframe structure
    import pandas as pd
    from utils.date_utils import generate_trading_days
    
    # Generate date range
    dates = generate_trading_days(args.start_date, args.end_date)
    
    # Create base dataframe
    df = pd.DataFrame()
    df['timestamp'] = [d.strftime('%-m/%-d/%y') for d in dates]
    
    # Add columns for each option
    option_symbols = [opt['symbol'] for opt in selected_options]
    for symbol in option_symbols:
        df[symbol] = ''
    
    # Fetch and fill prices
    databento_client = components['databento_client']
    
    for option in selected_options:
        symbol = option['symbol']
        start = option['start_date']
        end = option['end_date']
        
        logger.info(f"Fetching data for {symbol}: {start} to {end}")
        
        # Get option prices
        price_data = databento_client.get_options_data(
            symbol=symbol,
            start_date=start,
            end_date=end
        )
        
        if price_data is None or price_data.empty:
            logger.warning(f"No data returned for {symbol}")
            continue
        
        # Fill in the dataframe
        for _, row in price_data.iterrows():
            price_date = pd.to_datetime(row['date'])
            close_price = row['close']
            
            # Format date to match
            formatted_date = f"{price_date.month}/{price_date.day}/{str(price_date.year)[-2:]}"
            
            # Set price in dataframe
            matching_rows = df[df['timestamp'] == formatted_date]
            if not matching_rows.empty:
                df.loc[matching_rows.index, symbol] = close_price
    
    # Save output
    df.to_csv(output_path, index=False)
    logger.info(f"Saved data to {output_path}")
    
    return df


def run_demo():
    """Run a quick demo showing sample output."""
    import csv
    import random
    
    print("🚀 Databento Options Puller - Demo Mode")
    print("=" * 50)
    print("Creating sample options data...")
    
    # Create output directory
    os.makedirs("demo_output", exist_ok=True)
    
    # Generate sample data
    output_file = "demo_output/sample_options_data.csv"
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        contracts = ["OHF24 C27800", "OHG24 C24500", "OHH24 C27000"]
        writer.writerow(["timestamp", "Futures_Price"] + contracts)
        
        # Generate 10 days of sample data
        start_date = datetime.now() - timedelta(days=10)
        for i in range(10):
            date = start_date + timedelta(days=i)
            row = [date.strftime("%-m/%-d/%y")]
            row.append(f"{2.5 + random.uniform(-0.1, 0.1):.2f}")  # Futures price
            
            # Option prices
            for _ in contracts:
                if random.random() > 0.3:  # 70% chance of data
                    row.append(f"{random.uniform(0.10, 0.20):.2f}")
                else:
                    row.append("")  # Missing data
            
            writer.writerow(row)
    
    print(f"✅ Created sample data: {output_file}")
    print("\n📊 Sample output:")
    print("-" * 50)
    
    # Show first few lines
    with open(output_file, 'r') as f:
        for i, line in enumerate(f):
            if i < 5:
                print(line.strip())
    
    print("-" * 50)
    print("\n💡 This is what your output will look like.")
    print("To pull real data, run without --demo flag.")
    

def main():
    """Main entry point."""
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Handle demo mode
        if args.demo:
            run_demo()
            return 0
        
        # Setup logging
        setup_logging(
            level=getattr(logging, args.log_level),
            console_level=logging.ERROR if args.quiet else logging.INFO
        )
        
        logger = get_logger('main')
        logger.info("Starting Databento Options Data Puller")
        logger.debug(f"Arguments: {vars(args)}")
        
        # Validate arguments
        validate_arguments(args)
        
        # Determine output path
        output_path = Path(args.output)
        if output_path.exists():
            logger.warning(f"Output file {output_path} already exists and will be overwritten")
        
        # Run the data pull
        components = setup_components(args)
        df = run_data_pull(args, components, output_path)
        
        # Print summary
        print(f"\n✅ Successfully generated options data!")
        print(f"📊 Output: {len(df)} rows, {len(df.columns)} columns")
        print(f"💾 Saved to: {output_path}")
        
        # Show log location
        from utils.logging_config import get_current_log_dir
        log_dir = get_current_log_dir()
        if log_dir:
            print(f"📋 Logs saved to: {log_dir}/")
        
        return 0
        
    except Exception as e:
        logger = get_logger('main')
        logger.error(f"Fatal error: {e}", exc_info=True)
        
        # Get log directory for error message
        from utils.logging_config import get_current_log_dir
        log_dir = get_current_log_dir()
        
        print(f"\n❌ Error: {e}")
        if log_dir:
            print(f"📋 Check logs at: {log_dir}/main.log")
        return 1


if __name__ == "__main__":
    sys.exit(main())