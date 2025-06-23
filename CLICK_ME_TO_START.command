#!/bin/bash

# This file can be double-clicked in Finder to start the setup
# It opens Terminal and runs everything automatically

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Function to check for updates
check_for_updates() {
    if [ -d ".git" ]; then
        echo "🔄 Checking for updates..."
        
        # Check if we can reach GitHub
        if git ls-remote --exit-code --heads origin &>/dev/null; then
            # Fetch latest changes
            git fetch origin api-working-version &>/dev/null
            
            # Check if we're behind
            LOCAL=$(git rev-parse HEAD)
            REMOTE=$(git rev-parse origin/api-working-version)
            
            if [ "$LOCAL" != "$REMOTE" ]; then
                echo ""
                echo "📦 Updates available! Would you like to download them?"
                echo "This will get the latest bug fixes and improvements."
                echo ""
                echo -n "Download updates? (y/n): "
                read update_choice
                
                if [ "$update_choice" = "y" ] || [ "$update_choice" = "Y" ]; then
                    echo "Downloading updates..."
                    git pull origin api-working-version
                    echo "✅ Updated successfully!"
                    echo ""
                    echo "Restarting with new version..."
                    exec "$0"
                else
                    echo "Skipping updates for now."
                fi
            else
                echo "✅ You're running the latest version!"
            fi
        else
            echo "⚠️  Cannot check for updates (no internet connection?)"
        fi
        echo ""
    fi
}

# Clear screen and show welcome
clear
echo "╔══════════════════════════════════════════════════════════╗"
echo "║     Welcome to Databento Options Puller! 🚀             ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "This tool downloads historical options data from Databento."
echo ""

# Check for updates first
check_for_updates

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

# Function to get date range
get_date_range() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║                  Date Range Selection                    ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
    echo "Choose a date range for your data:"
    echo "1) Last 30 days"
    echo "2) Last 60 days"
    echo "3) Last 90 days"
    echo "4) Custom date range"
    echo ""
    echo -n "Enter your choice (1-4): "
    read date_choice
    
    # Calculate dates
    END_DATE=$(date +%Y-%m-%d)
    
    case $date_choice in
        1)
            START_DATE=$(date -v-30d +%Y-%m-%d 2>/dev/null || date -d '30 days ago' +%Y-%m-%d)
            echo "Selected: Last 30 days ($START_DATE to $END_DATE)"
            ;;
        2)
            START_DATE=$(date -v-60d +%Y-%m-%d 2>/dev/null || date -d '60 days ago' +%Y-%m-%d)
            echo "Selected: Last 60 days ($START_DATE to $END_DATE)"
            ;;
        3)
            START_DATE=$(date -v-90d +%Y-%m-%d 2>/dev/null || date -d '90 days ago' +%Y-%m-%d)
            echo "Selected: Last 90 days ($START_DATE to $END_DATE)"
            ;;
        4)
            echo ""
            echo "Enter custom date range:"
            echo -n "Start date (YYYY-MM-DD): "
            read START_DATE
            echo -n "End date (YYYY-MM-DD): "
            read END_DATE
            echo "Selected: $START_DATE to $END_DATE"
            ;;
        *)
            # Default to last 30 days
            START_DATE=$(date -v-30d +%Y-%m-%d 2>/dev/null || date -d '30 days ago' +%Y-%m-%d)
            echo "Invalid choice. Using last 30 days ($START_DATE to $END_DATE)"
            ;;
    esac
    
    # Create output filename with dates
    OUTPUT_FILE="output/options_data_${START_DATE}_to_${END_DATE}.csv"
}

# Check if already set up
if [ -d "venv" ] && [ -f ".env" ]; then
    echo "✅ Already set up!"
    
    # Determine if API key is valid
    if check_api_key; then
        DATA_MODE="live"
    else
        DATA_MODE="mock"
    fi
    
    # Get date range
    get_date_range
    
    # Activate virtual environment
    echo ""
    echo "🚀 Starting options data pull..."
    source venv/bin/activate
    
    # Run the puller
    if [ "$DATA_MODE" = "mock" ]; then
        echo "Running in demo mode (no API key)..."
        python3 databento_options_puller.py \
            --start-date "$START_DATE" \
            --end-date "$END_DATE" \
            --output "$OUTPUT_FILE" \
            --mock-mode
    else
        echo "Running with real Databento data..."
        python3 databento_options_puller.py \
            --start-date "$START_DATE" \
            --end-date "$END_DATE" \
            --output "$OUTPUT_FILE"
    fi
    
    # Show results
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║                    Complete! ✅                          ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
    echo "📊 Output saved to: $OUTPUT_FILE"
    echo "📂 Open this file in Excel or Numbers to view your data"
    
else
    # First time setup
    echo "🔧 First time setup detected. Installing everything..."
    echo ""
    
    # Make scripts executable
    chmod +x setup_mac.sh
    chmod +x databento_options_puller.py
    chmod +x START_HERE.command
    
    # Run setup
    ./setup_mac.sh
    
    echo ""
    echo "Setup complete!"
    echo "Press Enter to continue..."
    read
    
    # Now run the START_HERE.command which has all the interactive features
    echo ""
    echo "Launching interactive setup..."
    ./START_HERE.command
    exit 0
fi

echo ""
echo "Press Enter to close this window..."
read