# Databento Options Puller - Simple Setup Guide 🚀

## What This Does
This tool automatically downloads options trading data from Databento and saves it as a spreadsheet you can open in Excel.

## Super Quick Setup (5 minutes)

### Step 1: Open Terminal
1. Press `Command + Space` on your keyboard
2. Type "Terminal" and press Enter
3. A black window will open

### Step 2: Go to the Project Folder
Copy and paste this command into Terminal:
```bash
cd ~/Desktop/programming/2_proposals/other/databento-options-puller
```
Press Enter.

### Step 3: Run the Setup
Copy and paste this command:
```bash
./setup_mac.sh
```
Press Enter. The setup will run automatically (takes about 2-3 minutes).

### Step 4: Get Your API Key (Optional for Testing)
1. Go to https://databento.com
2. Click "Sign Up" (it's free to start)
3. After signing in, find your API key on the dashboard
4. Copy it

### Step 5: Add Your API Key
1. In Finder, go to the databento-options-puller folder
2. Find the file named `.env` (if you can't see it, press `Command + Shift + .`)
3. Open it with TextEdit
4. Replace `your_api_key_here` with your actual API key
5. Save and close

## Running the Program

### Easy Way:
Double-click the `run.sh` file in Finder

### Terminal Way:
```bash
./run.sh
```

## What You Get
- A CSV file in the `output` folder
- You can open this with Excel, Numbers, or any spreadsheet app
- The file contains options prices and related data

## Common Issues

**"Permission denied" error:**
```bash
chmod +x setup_mac.sh
chmod +x run.sh
```

**"Python not found" error:**
Run the setup script again - it will install Python for you.

**No data appearing:**
- Make sure you added your API key to the `.env` file
- Check that your API key is valid on databento.com

## Need Help?
- The full documentation is in README.md
- Check the `examples` folder for sample data
- Error messages usually tell you what's wrong

## Testing Without API Key
The system works in "mock mode" by default, so you can test everything without an API key first!