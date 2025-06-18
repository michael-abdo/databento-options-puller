#!/usr/bin/env python3
"""
Check if everything is set up correctly
"""

import os
import sys
from pathlib import Path

print("Databento Options Puller - Setup Check")
print("=" * 50)

# 1. Check Python version
print(f"✅ Python version: {sys.version.split()[0]}")

# 2. Check required packages
packages = ['pandas', 'numpy', 'databento', 'requests']
missing = []
for pkg in packages:
    try:
        __import__(pkg)
        print(f"✅ {pkg} installed")
    except ImportError:
        print(f"❌ {pkg} missing")
        missing.append(pkg)

# 3. Check API key
env_file = Path('.env')
api_key = None
if env_file.exists():
    with open(env_file) as f:
        content = f.read()
        if 'DATABENTO_API_KEY=' in content:
            for line in content.split('\n'):
                if line.startswith('DATABENTO_API_KEY='):
                    key = line.split('=', 1)[1].strip()
                    if key and key != 'your_api_key_here':
                        api_key = key
                        print(f"✅ API key configured: {key[:15]}...")
                    break

if not api_key:
    print("❌ No API key configured")
    print("   Run: python3 easy_setup.py")

# 4. Check directories
dirs = ['output', 'logs', 'demo_output']
for d in dirs:
    if Path(d).exists():
        print(f"✅ Directory '{d}' exists")
    else:
        print(f"⚠️  Directory '{d}' missing (will be created automatically)")

print("\n" + "=" * 50)
print("SUMMARY:")
print("=" * 50)

if missing:
    print(f"❌ Missing packages: {', '.join(missing)}")
    print("   Run: pip install " + " ".join(missing))
elif not api_key:
    print("⚠️  No API key configured")
    print("   You can still use demo mode!")
    print("   To add API key: python3 easy_setup.py")
else:
    print("✅ Everything is set up correctly!")
    print("\nYou can now run:")
    print("   python3 databento_options_puller.py --start-date 2024-01-01 --end-date 2024-01-31")
    print("\nOr use the interactive runner:")
    print("   python3 run_puller.py")

print("\nYour API key:", api_key[:20] + "..." if api_key else "Not configured")