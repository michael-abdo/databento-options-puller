#!/usr/bin/env python3
"""
Test runner for the Databento Options project.
Runs all unit and integration tests with coverage reporting.
"""

import sys
import unittest
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent  # Go up one level from scripts
sys.path.insert(0, str(project_root))

def run_all_tests():
    """Run all tests in the tests directory."""
    print("=" * 70)
    print("Running Databento Options Tests")
    print("=" * 70)
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = str(project_root / 'tests')  # Convert to string
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run tests with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
        
    print("=" * 70)
    
    return result.wasSuccessful()

def run_specific_test(test_module=None):
    """Run a specific test module."""
    if test_module:
        print(f"Running tests from: {test_module}")
        suite = unittest.TestLoader().loadTestsFromName(f'tests.{test_module}')
    else:
        suite = unittest.TestLoader().discover('tests', pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)

def run_with_coverage():
    """Run tests with coverage reporting."""
    try:
        import coverage
    except ImportError:
        print("Coverage module not installed. Install with: pip install coverage")
        return False
    
    print("Running tests with coverage...")
    
    # Start coverage
    cov = coverage.Coverage(source=['src'])
    cov.start()
    
    # Run tests
    success = run_all_tests()
    
    # Stop coverage and generate report
    cov.stop()
    cov.save()
    
    print("\n" + "=" * 70)
    print("Coverage Report")
    print("=" * 70)
    cov.report()
    
    # Generate HTML report
    html_dir = project_root / 'htmlcov'
    cov.html_report(directory=str(html_dir))
    print(f"\nDetailed HTML coverage report generated in: {html_dir}")
    
    return success

def main():
    """Main entry point for test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run tests for Databento Options project')
    parser.add_argument('--coverage', action='store_true', help='Run with coverage reporting')
    parser.add_argument('--module', type=str, help='Run specific test module (e.g., test_delta_calculator)')
    parser.add_argument('--failfast', action='store_true', help='Stop on first failure')
    
    args = parser.parse_args()
    
    # Set failfast if requested
    if args.failfast:
        unittest.TestProgram.failfast = True
    
    # Run appropriate test suite
    if args.module:
        success = run_specific_test(args.module)
    elif args.coverage:
        success = run_with_coverage()
    else:
        success = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()