#!/bin/bash

# This file can be double-clicked in Finder to start the setup
# It opens Terminal and runs everything automatically

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Clear screen and show welcome
clear
echo "╔══════════════════════════════════════════════════════════╗"
echo "║     Welcome to Databento Options Puller! 🚀             ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "This tool downloads historical options data from Databento."
echo "Setup takes about 3-5 minutes."
echo ""

# Check if .env exists and has a real API key
check_api_key() {
    if [ -f .env ]; then
        # Check if API key is set and not the default
        if grep -q "DATABENTO_API_KEY=your_api_key_here" .env || grep -q "DATABENTO_API_KEY=$" .env; then
            return 1  # No valid key
        else
            return 0  # Key exists
        fi
    else
        return 1  # No .env file
    fi
}

# Function to get API key from user
get_api_key() {
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║                  API Key Setup                           ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
    echo "You'll need a Databento API key to download real data."
    echo ""
    echo "Choose an option:"
    echo "1) I have a Databento API key"
    echo "2) I need to get an API key (opens databento.com)"
    echo "3) Skip for now (use demo mode)"
    echo ""
    echo -n "Enter your choice (1-3): "
    read choice
    
    case $choice in
        1)
            echo ""
            echo "Please paste your Databento API key:"
            echo "(It will be hidden as you type for security)"
            echo ""
            read -s -p "API Key: " api_key
            echo ""
            
            if [ -z "$api_key" ]; then
                echo "❌ No API key entered. Using demo mode."
                setup_demo_env
            else
                # Save the API key
                cat > .env << EOF
# Databento API Configuration
DATABENTO_API_KEY=$api_key

# Set to 'mock' for testing, 'live' for real data
DATA_MODE=live

# Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
EOF
                echo "✅ API key saved successfully!"
            fi
            ;;
        2)
            echo ""
            echo "Opening Databento website..."
            open "https://databento.com/signup"
            echo ""
            echo "After you sign up and get your API key, run this setup again."
            echo "For now, we'll use demo mode."
            echo ""
            setup_demo_env
            ;;
        3)
            echo ""
            echo "No problem! You can add your API key later."
            setup_demo_env
            ;;
        *)
            echo "Invalid choice. Using demo mode."
            setup_demo_env
            ;;
    esac
}

# Function to setup demo environment
setup_demo_env() {
    cat > .env << 'EOF'
# Databento API Configuration
DATABENTO_API_KEY=your_api_key_here

# Set to 'mock' for testing, 'live' for real data
DATA_MODE=mock

# Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
EOF
}

# First time check
if ! check_api_key; then
    get_api_key
    echo ""
fi

echo "Press Enter to continue..."
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