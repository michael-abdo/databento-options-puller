#!/usr/bin/env python3
"""
User-friendly runner for Databento Options Puller
Checks for API key and guides users through setup if needed
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

def check_api_key():
    """Check if API key is properly configured"""
    env_file = Path('.env')
    
    if not env_file.exists():
        return False
        
    content = env_file.read_text()
    if 'DATABENTO_API_KEY=' not in content:
        return False
        
    # Check if it's not the placeholder
    if 'your_api_key_here' in content or 'demo_mode' in content:
        return False
        
    # Extract and verify key exists
    for line in content.split('\n'):
        if line.startswith('DATABENTO_API_KEY='):
            key = line.split('=', 1)[1].strip()
            if key and key != 'your_api_key_here':
                return True
    
    return False

def run_setup():
    """Run the easy setup script"""
    print("No API key found. Let's set one up!")
    print()
    subprocess.run([sys.executable, 'easy_setup.py'])
    sys.exit(0)

def main():
    """Main runner logic"""
    print("╔══════════════════════════════════════════════════════════╗")
    print("║            Databento Options Puller                      ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    
    # Check for API key
    if not check_api_key():
        print("⚠️  No API key configured.")
        print()
        print("Options:")
        print("1) Set up API key now")
        print("2) Run in demo mode")
        print("3) Exit")
        print()
        
        choice = input("Enter your choice (1-3): ").strip()
        
        if choice == '1':
            run_setup()
        elif choice == '2':
            print("\nRunning in demo mode...")
            # Set environment variable for this session
            os.environ['DATA_MODE'] = 'mock'
        else:
            print("Exiting...")
            sys.exit(0)
    
    # Default date range (last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Ask user for date range
    print("Date range for data pull:")
    print(f"1) Last 30 days ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})")
    print("2) Custom date range")
    print()
    
    date_choice = input("Enter your choice (1-2): ").strip()
    
    if date_choice == '2':
        print()
        start_input = input("Enter start date (YYYY-MM-DD): ").strip()
        end_input = input("Enter end date (YYYY-MM-DD): ").strip()
        
        try:
            start_date = datetime.strptime(start_input, '%Y-%m-%d')
            end_date = datetime.strptime(end_input, '%Y-%m-%d')
        except ValueError:
            print("Invalid date format. Using default range.")
    
    # Output filename
    output_file = f"output/options_data_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
    
    print()
    print(f"Pulling data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
    print(f"Output will be saved to: {output_file}")
    print()
    
    # Run the main script
    cmd = [
        sys.executable,
        'databento_options_puller.py',
        '--start-date', start_date.strftime('%Y-%m-%d'),
        '--end-date', end_date.strftime('%Y-%m-%d'),
        '--output', output_file
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print()
        print(f"✅ Success! Data saved to: {output_file}")
        print("📊 You can open this file in Excel or any spreadsheet application.")
    except subprocess.CalledProcessError as e:
        print()
        print(f"❌ Error running the puller: {e}")
        print("Check the logs directory for more details.")
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")

if __name__ == "__main__":
    main()