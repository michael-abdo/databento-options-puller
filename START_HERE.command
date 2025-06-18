#!/bin/bash

# Databento Options Puller - Production Ready Entry Point
# This is THE way to run the application

# Get script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Function to check if Python 3 is installed
check_python() {
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 is required but not installed."
        echo "Installing Python via Homebrew..."
        
        # Install Homebrew if needed
        if ! command -v brew &> /dev/null; then
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        
        # Install Python
        brew install python@3.11
    fi
}

# Function to setup virtual environment
setup_venv() {
    if [ ! -d "venv" ]; then
        echo "📦 Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip silently
    pip install --upgrade pip &>/dev/null
    
    # Install requirements if needed
    if [ -f "requirements.txt" ]; then
        echo "📚 Checking dependencies..."
        pip install -q -r requirements.txt
    fi
}

# Function to check API key
check_api_key() {
    if [ -f .env ]; then
        if grep -q "DATABENTO_API_KEY=your_api_key_here" .env || ! grep -q "DATABENTO_API_KEY=" .env; then
            return 1
        else
            # Extract key for validation
            API_KEY=$(grep "DATABENTO_API_KEY=" .env | cut -d'=' -f2)
            if [ -z "$API_KEY" ] || [ "$API_KEY" = "your_api_key_here" ] || [ "$API_KEY" = "demo_mode" ]; then
                return 1
            fi
            return 0
        fi
    else
        return 1
    fi
}

# Function to get API key from user
get_api_key() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "                  API Key Required"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "This application requires a Databento API key."
    echo ""
    echo "1) Enter API key now"
    echo "2) Get a free API key (opens browser)"
    echo "3) Exit"
    echo ""
    read -p "Choose (1-3): " choice
    
    case $choice in
        1)
            echo ""
            read -p "Enter your Databento API key: " api_key
            
            if [ ! -z "$api_key" ]; then
                cat > .env << EOF
# Databento API Configuration
DATABENTO_API_KEY=$api_key
DATA_MODE=live
LOG_LEVEL=INFO
EOF
                echo "✅ API key saved!"
                return 0
            else
                echo "❌ No API key entered"
                return 1
            fi
            ;;
        2)
            echo "Opening Databento signup page..."
            open "https://databento.com/signup"
            echo ""
            echo "After getting your API key, run this again."
            exit 0
            ;;
        *)
            echo "Exiting..."
            exit 0
            ;;
    esac
}

# Main execution starts here
clear
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║          Databento Options Puller - Production Mode           ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Check Python
check_python

# Step 2: Setup environment
setup_venv

# Step 3: Check API key
if ! check_api_key; then
    echo "⚠️  No valid API key found."
    if ! get_api_key; then
        echo "Cannot proceed without API key."
        exit 1
    fi
fi

# Step 4: Create necessary directories
mkdir -p output logs

# Step 5: Get date range
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "                  Select Date Range"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Calculate default dates
END_DATE=$(date +%Y-%m-%d)
START_DATE=$(date -v-30d +%Y-%m-%d 2>/dev/null || date -d "30 days ago" +%Y-%m-%d)

echo "1) Last 30 days ($START_DATE to $END_DATE)"
echo "2) Last 90 days"
echo "3) Year to date"
echo "4) Custom range"
echo ""
read -p "Choose (1-4): " date_choice

case $date_choice in
    1)
        # Already set above
        ;;
    2)
        START_DATE=$(date -v-90d +%Y-%m-%d 2>/dev/null || date -d "90 days ago" +%Y-%m-%d)
        ;;
    3)
        START_DATE=$(date +%Y-01-01)
        ;;
    4)
        echo ""
        read -p "Enter start date (YYYY-MM-DD): " START_DATE
        read -p "Enter end date (YYYY-MM-DD): " END_DATE
        ;;
    *)
        # Default to last 30 days
        ;;
esac

# Step 6: Set output filename
OUTPUT_FILE="output/databento_options_${START_DATE}_${END_DATE}.csv"

# Step 7: Run the application
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "                  Running Data Pull"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📅 Date Range: $START_DATE to $END_DATE"
echo "📄 Output File: $OUTPUT_FILE"
echo ""
echo "Fetching data..."
echo ""

# Run the main application
python3 databento_options_puller.py \
    --start-date "$START_DATE" \
    --end-date "$END_DATE" \
    --output "$OUTPUT_FILE"

# Check if successful
if [ $? -eq 0 ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "                    ✅ SUCCESS!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📊 Data saved to: $OUTPUT_FILE"
    echo ""
    echo "Would you like to:"
    echo "1) Open in Excel/Numbers"
    echo "2) Run another date range"
    echo "3) Exit"
    echo ""
    read -p "Choose (1-3): " final_choice
    
    case $final_choice in
        1)
            open "$OUTPUT_FILE"
            ;;
        2)
            # Re-run this script
            exec "$0"
            ;;
        *)
            ;;
    esac
else
    echo ""
    echo "❌ Error occurred. Check the logs folder for details"
    echo "   Logs are organized by run date/time in logs/run_*/"
fi

echo ""
echo "Press any key to exit..."
read -n 1 -s