#!/bin/bash

# One-click setup for Databento Options Puller
# Just double-click this file!

# Get script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

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

# Run the easy setup
python3 easy_setup.py

# Keep window open
echo ""
echo "You can close this window now."
read -n 1 -s -r -p ""