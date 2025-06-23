#!/bin/bash

# One-click setup for Databento Options Puller
# Just double-click this file!

# Get script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Clear screen and show welcome
clear
echo "╔══════════════════════════════════════════════════════════╗"
echo "║     Welcome to Databento Options Puller! 🚀             ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Installing it now..."
    
    # Check for Homebrew
    if ! command -v brew &> /dev/null; then
        echo "Installing Homebrew first..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    # Install Python
    brew install python@3.11
fi

# Function to check API key
check_api_key() {
    if [ -f .env ]; then
        if grep -q "DATABENTO_API_KEY=your_api_key_here" .env || grep -q "DATABENTO_API_KEY=$" .env || grep -q "DATABENTO_API_KEY=demo_mode" .env; then
            return 1  # No valid key
        else
            return 0  # Key exists
        fi
    else
        return 1  # No .env file
    fi
}

# Function to get API key
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
                DATA_MODE="mock"
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
                DATA_MODE="live"
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
            DATA_MODE="mock"
            ;;
        3)
            echo ""
            echo "No problem! You can add your API key later."
            DATA_MODE="mock"
            ;;
        *)
            echo "Invalid choice. Using demo mode."
            DATA_MODE="mock"
            ;;
    esac
}

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

# Main flow
echo "Setting up Databento Options Puller..."
echo ""

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "🔧 First time setup detected. Installing dependencies..."
    echo ""
    
    # Make scripts executable
    chmod +x setup_mac.sh
    chmod +x databento_options_puller.py
    
    # Run setup
    ./setup_mac.sh
    echo ""
fi

# Check/get API key
if ! check_api_key; then
    get_api_key
else
    echo "✅ API key already configured!"
    DATA_MODE="live"
fi

# Get date range
get_date_range

# Activate virtual environment
echo ""
echo "🚀 Starting options data pull..."
source venv/bin/activate

# Run the puller with selected options
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
echo ""
echo "Press Enter to close this window..."
read