#!/bin/bash

# This file can be double-clicked in Finder to start the setup
# It opens Terminal and runs everything automatically

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Clear screen and show welcome
clear
echo "╔══════════════════════════════════════════════════════════╗"
echo "║     Welcome to Databento Options Puller Setup! 🚀       ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "This will set up everything automatically for you."
echo "No technical knowledge required!"
echo ""
echo "Press Enter to continue (or Ctrl+C to cancel)..."
read

# Check if already set up
if [ -d "venv" ] && [ -f ".env" ]; then
    echo "✅ Already set up! What would you like to do?"
    echo ""
    echo "1) Run the demo (no API key needed)"
    echo "2) Run with real data (requires API key)"
    echo "3) Re-run setup"
    echo "4) Exit"
    echo ""
    echo -n "Enter your choice (1-4): "
    read choice
    
    case $choice in
        1)
            echo "Running demo..."
            python3 simple_demo.py
            ;;
        2)
            echo "Running with real data..."
            source venv/bin/activate
            python databento_options_puller.py --output "output/options_data.csv"
            ;;
        3)
            echo "Re-running setup..."
            ./setup_mac.sh
            ;;
        4)
            echo "Goodbye!"
            exit 0
            ;;
        *)
            echo "Invalid choice. Running demo..."
            python3 simple_demo.py
            ;;
    esac
else
    # First time setup
    echo "🔧 First time setup detected. Installing everything..."
    echo ""
    
    # Make scripts executable
    chmod +x setup_mac.sh
    chmod +x simple_demo.py
    
    # Run setup
    ./setup_mac.sh
    
    echo ""
    echo "Setup complete! Now let's run a demo..."
    echo "Press Enter to continue..."
    read
    
    # Run demo
    python3 simple_demo.py
fi

echo ""
echo "Press Enter to close this window..."
read