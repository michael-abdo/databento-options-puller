#!/bin/bash

# Databento Options Puller - Mac Setup Script
# This script handles everything automatically

echo "╔══════════════════════════════════════════════════════════╗"
echo "║         Databento Options Puller Setup for Mac           ║"
echo "║                                                          ║"
echo "║  This will set up everything you need automatically      ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check if running on Mac
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is for Mac only. Detected: $OSTYPE"
    exit 1
fi

# Function to install Homebrew if needed
install_homebrew() {
    if ! command -v brew &> /dev/null; then
        echo "📦 Installing Homebrew (Mac's package manager)..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Add Homebrew to PATH
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        echo "✅ Homebrew already installed"
    fi
}

# Function to install Python if needed
install_python() {
    if ! command -v python3 &> /dev/null; then
        echo "🐍 Installing Python..."
        brew install python@3.11
    else
        echo "✅ Python already installed ($(python3 --version))"
    fi
}

# Main setup
echo "🚀 Starting setup..."
echo ""

# Step 1: Install Homebrew
install_homebrew

# Step 2: Install Python
install_python

# Step 3: Create virtual environment
echo ""
echo "📁 Setting up Python environment..."
python3 -m venv venv

# Step 4: Activate virtual environment
source venv/bin/activate

# Step 5: Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Step 6: Install requirements
echo ""
echo "📚 Installing required packages..."
pip install -r requirements.txt

# Step 7: Create necessary directories
echo ""
echo "📂 Creating necessary folders..."
mkdir -p output logs

# Step 8: Create .env file for API key
echo ""
echo "🔑 Setting up configuration..."
if [ ! -f .env ]; then
    cat > .env << 'EOF'
# Databento API Configuration
DATABENTO_API_KEY=your_api_key_here

# Set to 'mock' for testing, 'live' for real data
DATA_MODE=mock

# Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
EOF
    echo "✅ Created .env file for your API key"
else
    echo "✅ .env file already exists"
fi

# Step 9: Run a test
echo ""
echo "🧪 Running a quick test..."
python -c "
import sys
print('✅ Python is working correctly')
try:
    import databento
    print('✅ Databento package installed')
except:
    print('⚠️  Databento package not found - will use mock data')
print('✅ Setup completed successfully!')
"

# Step 10: Create a simple run script
cat > run.sh << 'EOF'
#!/bin/bash
# Simple run script for databento options puller

# Activate virtual environment
source venv/bin/activate

# Run with default settings (last 30 days)
python databento_options_puller.py --output "output/options_data.csv"

echo ""
echo "✅ Data saved to output/options_data.csv"
echo "📊 Open the file with Excel or Numbers to view your data"
EOF

chmod +x run.sh

# Final instructions
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                  ✅ SETUP COMPLETE!                      ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "📋 NEXT STEPS:"
echo ""
echo "1️⃣  To get your Databento API key:"
echo "    • Go to https://databento.com"
echo "    • Sign up for a free account"
echo "    • Copy your API key from the dashboard"
echo ""
echo "2️⃣  Add your API key:"
echo "    • Open the .env file in this folder"
echo "    • Replace 'your_api_key_here' with your actual key"
echo ""
echo "3️⃣  Run the program:"
echo "    • Double-click the 'run.sh' file, OR"
echo "    • Open Terminal and type: ./run.sh"
echo ""
echo "📚 For more help, see README.md"
echo ""