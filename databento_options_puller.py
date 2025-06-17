#!/usr/bin/env python3
"""
Databento Options Data Puller

Production script to pull NY Harbor ULSD (OH) futures and 15-delta call options data
from Databento API and generate a single CSV output.

Usage:
    python databento_options_puller.py --start-date 2021-12-01 --end-date 2022-03-31 --output output.csv
    python databento_options_puller.py --example-mode  # Use example data for testing
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / 'src'))
sys.path.append(str(Path(__file__).parent))

from src.example_analyzer import ExampleAnalyzer
from src.option_generator import OptionGenerator
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
    
    # Date range (required unless using example mode)
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
        '--example-mode',
        action='store_true',
        help='Use example data structure for testing (ignores date parameters)'
    )
    
    parser.add_argument(
        '--mock-mode',
        action='store_true',
        help='Use mock data instead of real Databento API calls'
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
        help='Suppress console output (only log to file)'
    )
    
    return parser.parse_args()


def validate_arguments(args):
    """Validate command line arguments."""
    if not args.example_mode:
        if not args.start_date or not args.end_date:
            raise ValueError("--start-date and --end-date are required unless using --example-mode")
        
        # Validate date formats
        try:
            datetime.strptime(args.start_date, '%Y-%m-%d')
            datetime.strptime(args.end_date, '%Y-%m-%d')
        except ValueError as e:
            raise ValueError(f"Invalid date format. Use YYYY-MM-DD: {e}")
    
    # Check API key
    api_key = args.api_key or os.getenv('DATABENTO_API_KEY')
    if not api_key and not args.mock_mode and not args.example_mode:
        raise ValueError("Databento API key required. Set DATABENTO_API_KEY environment variable or use --api-key")
    
    return True


def setup_components(args):
    """Initialize all components based on arguments."""
    logger = get_logger('main')
    
    # Initialize Databento client
    if args.example_mode or args.mock_mode:
        logger.info("Using mock Databento client")
        databento_client = DatabentoBridge()  # Will use mock mode
    else:
        api_key = args.api_key or os.getenv('DATABENTO_API_KEY')
        logger.info("Initializing real Databento client")
        databento_client = DatabentoBridge(api_key=api_key)
    
    # Initialize calculation components
    delta_calculator = DeltaCalculator(risk_free_rate=args.risk_free_rate)
    futures_manager = FuturesManager()
    options_manager = OptionsManager(
        databento_client=databento_client,
        delta_calculator=delta_calculator,
        futures_manager=futures_manager
    )
    
    # Set target delta
    options_manager.target_delta = args.target_delta
    
    logger.info(f"Initialized components (target_delta={args.target_delta:.2f}, "
               f"risk_free_rate={args.risk_free_rate:.2%})")
    
    return {
        'databento_client': databento_client,
        'delta_calculator': delta_calculator,
        'futures_manager': futures_manager,
        'options_manager': options_manager
    }


def run_example_mode(args, output_path):
    """Run in example mode using existing example data."""
    logger = get_logger('main')
    logger.info("Running in example mode")
    
    # Analyze example to get facts
    example_path = Path(__file__).parent / 'example_output.csv'
    analyzer = ExampleAnalyzer(str(example_path))
    facts = analyzer.analyze()
    
    logger.info(f"Analyzed example: {facts['basic_info']['num_rows']} rows, "
               f"{facts['basic_info']['num_columns']} columns")
    
    # Generate using stub data
    generator = OptionGenerator(facts, use_real_data=False)
    df = generator.generate()
    
    # Save output
    df.to_csv(output_path, index=False)
    logger.info(f"Saved example-based output to {output_path}")
    
    return df


def run_real_mode(args, components, output_path):
    """Run with real Databento data."""
    logger = get_logger('main')
    logger.info(f"Running real mode: {args.start_date} to {args.end_date}")
    
    # Get monthly option selections
    options_manager = components['options_manager']
    selected_options = options_manager.identify_monthly_options(
        args.start_date, args.end_date
    )
    
    if not selected_options:
        raise RuntimeError("No options identified by strategy")
    
    logger.info(f"Strategy identified {len(selected_options)} options:")
    for opt in selected_options:
        logger.info(f"  {opt['selection_date'].strftime('%Y-%m-%d')}: {opt['symbol']} "
                   f"(Δ={opt['actual_delta']:.4f}, K=${opt['strike']:.2f})")
    
    # Create output dataframe
    start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
    
    # Generate trading days
    from utils.date_utils import generate_trading_days
    trading_days = generate_trading_days(start_date, end_date)
    
    # Format dates
    formatted_dates = []
    for date in trading_days:
        # Use no-padding format to match example
        formatted_date = f"{date.month}/{date.day}/{str(date.year)[-2:]}"
        formatted_dates.append(formatted_date)
    
    # Create base dataframe
    import pandas as pd
    df = pd.DataFrame({'timestamp': formatted_dates})
    
    # Add each option's data
    for option_info in selected_options:
        symbol = option_info['symbol']
        logger.info(f"Fetching price data for {symbol}")
        
        # Get price history
        price_data = options_manager.get_option_price_history(
            symbol,
            option_info['start_trading'],
            option_info['end_trading']
        )
        
        # Add column for this option
        df[symbol] = None
        
        # Fill in the prices for active dates
        for _, price_row in price_data.iterrows():
            price_date = price_row['date']
            close_price = price_row['close']
            
            # Format date to match
            formatted_date = f"{price_date.month}/{price_date.day}/{str(price_date.year)[-2:]}"
            
            # Set price in dataframe
            matching_rows = df[df['timestamp'] == formatted_date]
            if not matching_rows.empty:
                df.loc[matching_rows.index, symbol] = close_price
    
    # Save output
    df.to_csv(output_path, index=False)
    logger.info(f"Saved real data output to {output_path}")
    
    return df


def main():
    """Main entry point."""
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Setup logging
        setup_logging(
            level=getattr(logging, args.log_level),
            console_level=logging.ERROR if args.quiet else logging.INFO
        )
        
        logger = get_logger('main')
        logger.info("Starting Databento Options Data Puller")
        logger.info(f"Arguments: {vars(args)}")
        
        # Validate arguments
        validate_arguments(args)
        
        # Determine output path
        output_path = Path(args.output)
        if output_path.exists():
            logger.warning(f"Output file {output_path} already exists and will be overwritten")
        
        # Run in appropriate mode
        if args.example_mode:
            df = run_example_mode(args, output_path)
        else:
            components = setup_components(args)
            df = run_real_mode(args, components, output_path)
        
        # Print summary
        print(f"\n✅ Successfully generated options data!")
        print(f"📊 Output: {len(df)} rows, {len(df.columns)} columns")
        print(f"💾 Saved to: {output_path}")
        
        if not args.quiet:
            print(f"\n📋 Column summary:")
            for col in df.columns:
                non_null = df[col].notna().sum()
                print(f"  {col}: {non_null} non-null values")
        
        logger.info("✅ Databento Options Data Puller completed successfully")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if hasattr(e, '__traceback__'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()