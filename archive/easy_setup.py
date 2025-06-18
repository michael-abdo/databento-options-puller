#!/usr/bin/env python3
"""
Easy Setup - Interactive setup for Databento Options Puller
Run this first: python3 easy_setup.py
"""

import os
import sys
import subprocess
import webbrowser
from pathlib import Path

def clear_screen():
    """Clear the terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')

def print_header():
    """Print welcome header"""
    print("╔══════════════════════════════════════════════════════════╗")
    print("║         Databento Options Puller - Easy Setup            ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

def check_existing_key():
    """Check if API key already exists"""
    env_file = Path('.env')
    if env_file.exists():
        content = env_file.read_text()
        if 'DATABENTO_API_KEY=' in content and 'your_api_key_here' not in content:
            # Extract the key to verify it's not empty
            for line in content.split('\n'):
                if line.startswith('DATABENTO_API_KEY='):
                    key = line.split('=', 1)[1].strip()
                    if key:
                        return True
    return False

def save_api_key(api_key):
    """Save API key to .env file"""
    env_content = f"""# Databento API Configuration
DATABENTO_API_KEY={api_key}

# Set to 'mock' for testing, 'live' for real data
DATA_MODE=live

# Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Output settings
DEFAULT_OUTPUT_DIR=output
DEFAULT_DATE_FORMAT=%-m/%-d/%y
"""
    with open('.env', 'w') as f:
        f.write(env_content)
    print("✅ API key saved successfully!")

def setup_demo_mode():
    """Setup demo mode configuration"""
    env_content = """# Databento API Configuration
DATABENTO_API_KEY=demo_mode

# Set to 'mock' for testing, 'live' for real data
DATA_MODE=mock

# Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Output settings
DEFAULT_OUTPUT_DIR=output
DEFAULT_DATE_FORMAT=%-m/%-d/%y
"""
    with open('.env', 'w') as f:
        f.write(env_content)
    print("✅ Demo mode configured!")

def get_api_key_interactive():
    """Interactive API key setup"""
    print("📋 API Key Setup")
    print("=" * 50)
    print()
    print("To download real market data, you'll need a Databento API key.")
    print()
    print("Options:")
    print("1) I have an API key")
    print("2) Get a free API key (opens browser)")
    print("3) Use demo mode (no API key needed)")
    print()
    
    while True:
        choice = input("Enter your choice (1-3): ").strip()
        
        if choice == '1':
            print()
            print("Please enter your Databento API key:")
            print("(Tip: You can paste it here)")
            api_key = input("API Key: ").strip()
            
            if api_key:
                save_api_key(api_key)
                return True
            else:
                print("❌ No API key entered.")
                continue
                
        elif choice == '2':
            print()
            print("Opening Databento signup page...")
            webbrowser.open('https://databento.com/signup')
            print()
            print("After signing up:")
            print("1. Go to your Databento dashboard")
            print("2. Copy your API key")
            print("3. Run this setup again and choose option 1")
            print()
            input("Press Enter to continue with demo mode...")
            setup_demo_mode()
            return False
            
        elif choice == '3':
            print()
            setup_demo_mode()
            return False
            
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

def check_python_packages():
    """Check and install required Python packages"""
    print()
    print("📦 Checking Python packages...")
    
    required_packages = ['pandas', 'numpy', 'requests']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Installing required packages: {', '.join(missing_packages)}")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
        print("✅ Packages installed!")
    else:
        print("✅ All required packages already installed!")

def create_directories():
    """Create necessary directories"""
    dirs = ['output', 'logs', 'demo_output']
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
    print("✅ Created output directories!")

def run_demo():
    """Run the demo script"""
    print()
    print("🚀 Running demo...")
    print("=" * 50)
    
    try:
        subprocess.run([sys.executable, 'simple_demo.py'], check=True)
    except subprocess.CalledProcessError:
        print("❌ Demo script not found. Creating a simple example...")
        # Create inline demo if script doesn't exist
        create_inline_demo()

def create_inline_demo():
    """Create a simple demo if demo script is missing"""
    import csv
    from datetime import datetime, timedelta
    
    print("Creating sample options data...")
    
    # Generate sample data
    output_file = "demo_output/sample_data.csv"
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'Futures_Price', 'OHF24 C27800', 'OHG24 C24500'])
        
        base_date = datetime.now() - timedelta(days=30)
        for i in range(10):
            date = base_date + timedelta(days=i*3)
            writer.writerow([
                date.strftime("%-m/%-d/%y"),
                f"{2.5 + i*0.1:.2f}",
                f"{0.15 - i*0.01:.2f}" if i % 2 == 0 else "",
                f"{0.12 - i*0.005:.2f}" if i % 3 == 0 else ""
            ])
    
    print(f"✅ Created sample data: {output_file}")
    print("📊 You can open this file in Excel to see the format!")

def main():
    """Main setup flow"""
    clear_screen()
    print_header()
    
    # Check if already configured
    if check_existing_key():
        print("✅ API key already configured!")
        print()
        choice = input("Run a demo? (y/n): ").strip().lower()
        if choice == 'y':
            run_demo()
    else:
        # First time setup
        print("Welcome! Let's get you set up in 2 minutes.")
        print()
        
        # Get API key
        has_real_key = get_api_key_interactive()
        
        # Check packages
        check_python_packages()
        
        # Create directories
        create_directories()
        
        # Run demo
        print()
        print("Setup complete! Let's run a quick demo.")
        input("Press Enter to continue...")
        run_demo()
        
        # Final instructions
        print()
        print("=" * 50)
        print("✅ All done! You're ready to use Databento Options Puller")
        print()
        if has_real_key:
            print("To download real data:")
            print("  python3 databento_options_puller.py")
        else:
            print("To download real data later:")
            print("  1. Get your API key from databento.com")
            print("  2. Run this setup again")
            print("  3. Choose option 1 and enter your key")
    
    print()
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()