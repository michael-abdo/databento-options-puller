#!/usr/bin/env python3
"""
Main entry point for the Databento Options Feedback Loop system.
This script orchestrates the iterative process of matching example_output.csv
"""

import argparse
import os
import sys
from pathlib import Path
import yaml
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.logging_config import setup_logging, get_logger

# These imports will work once we create the modules
# from src.example_analyzer import ExampleAnalyzer
# from src.option_generator import OptionGenerator
# from src.output_validator import OutputValidator
# from src.parameter_refiner import ParameterRefiner


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def main():
    """Run the feedback loop to match example_output.csv"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Generate options data matching example_output.csv"
    )
    parser.add_argument(
        '--config',
        default='config/default_params.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--example',
        default='example_output.csv',
        help='Path to example output CSV'
    )
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=50,
        help='Maximum number of iterations'
    )
    parser.add_argument(
        '--output-dir',
        default='output',
        help='Directory for output files'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Set up logging
    loggers = setup_logging(
        log_dir='logs',
        level=getattr(logging, config['logging']['level']),
        console_level=getattr(logging, config['logging']['console_level'])
    )
    
    logger = loggers['main']
    logger.info("Starting Databento Options Feedback Loop")
    logger.info(f"Configuration: {args.config}")
    logger.info(f"Example file: {args.example}")
    logger.info(f"Max iterations: {args.max_iterations}")
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    try:
        # Step 1: Analyze the example
        logger.info("="*60)
        logger.info("STEP 1: Analyzing example output")
        logger.info("="*60)
        
        from src.example_analyzer import ExampleAnalyzer
        analyzer = ExampleAnalyzer(args.example)
        facts = analyzer.analyze()
        
        # Step 2: Initialize components
        logger.info("="*60)
        logger.info("STEP 2: Initializing components")
        logger.info("="*60)
        
        from src.option_generator import OptionGenerator
        from src.output_validator import OutputValidator
        from src.parameter_refiner import ParameterRefiner
        
        generator = OptionGenerator(facts, config)
        validator = OutputValidator(args.example)
        refiner = ParameterRefiner(config)
        
        # Track best result
        best_score = 0.0
        best_iteration = 0
        success_threshold = config['feedback_loop']['convergence_threshold']
        
        # Step 3: Run feedback loop
        logger.info("="*60)
        logger.info("STEP 3: Running feedback loop")
        logger.info("="*60)
        
        for iteration in range(1, args.max_iterations + 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"ITERATION {iteration}")
            logger.info(f"{'='*60}")
            
            # Generate attempt
            generated = generator.generate()
            
            # Validate
            results = validator.validate(generated)
            current_score = results.get('overall_score', 0.0)
            
            # Save iteration output
            output_path = f"{args.output_dir}/iteration_{iteration:03d}.csv"
            generated.to_csv(output_path, index=False)
            logger.info(f"Saved iteration {iteration} to {output_path}")
            
            # Track best
            if current_score > best_score:
                best_score = current_score
                best_iteration = iteration
                # Save best result
                best_path = f"{args.output_dir}/best_result.csv"
                generated.to_csv(best_path, index=False)
            
            logger.info(f"Iteration {iteration} score: {current_score:.2%}")
            logger.info(f"Best score so far: {best_score:.2%} (iteration {best_iteration})")
            
            # Check success
            if validator.is_success(results, success_threshold):
                logger.info("SUCCESS! Output matches example.")
                # Save final result
                final_path = f"{args.output_dir}/final_result.csv"
                generated.to_csv(final_path, index=False)
                break
            
            # Refine parameters
            new_params = refiner.refine(generator.get_params(), results)
            generator.update_params(new_params)
            
            # Early stopping if no improvement
            convergence_info = refiner.get_convergence_info()
            if convergence_info['stuck_count'] > 10:
                logger.warning("No improvement for 10 iterations, stopping early")
                break
        
        # Generate final report
        logger.info("="*60)
        logger.info("Generating final report")
        logger.info("="*60)
        
        # Create comparison report with best result
        best_result_path = f"{args.output_dir}/best_result.csv"
        if Path(best_result_path).exists():
            import pandas as pd
            best_df = pd.read_csv(best_result_path)
            report_path = validator.create_comparison_report(best_df)
            logger.info(f"Comparison report saved to: {report_path}")
        
        # Save refinement history
        refiner.save_history()
        
        # Summary
        logger.info(f"Process completed after {iteration} iterations")
        logger.info(f"Best score achieved: {best_score:.2%}")
        
        if best_score >= success_threshold:
            logger.info("✅ SUCCESS: Achieved target match!")
        else:
            logger.warning(f"❌ Did not reach target ({success_threshold:.1%})")
            logger.info("Check logs and validation results for improvements needed")
        
    except KeyboardInterrupt:
        logger.warning("Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()