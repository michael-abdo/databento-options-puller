#!/bin/bash

# Databento Options Puller - Quick Download Script
# Just double-click to download and open the project!

echo "🚀 Downloading Databento Options Puller..."
echo ""

# Navigate to Desktop
cd ~/Desktop

# Clone the repository
if git clone https://github.com/michael-abdo/databento-options-puller.git; then
    echo ""
    echo "✅ Download complete!"
    echo ""
    
    # Open the folder in Finder
    open databento-options-puller
    
    # Also open in Terminal for convenience
    cd databento-options-puller
    
    echo "📁 Project folder opened in Finder"
    echo "📍 Current directory: $(pwd)"
    echo ""
    echo "To get started:"
    echo "1. Double-click START_HERE.command in the project folder"
    echo "2. Follow the prompts to set up your API key"
    echo ""
    echo "Press any key to close this window..."
    read -n 1
else
    echo ""
    echo "❌ Download failed. Please check your internet connection."
    echo "Press any key to close..."
    read -n 1
fi