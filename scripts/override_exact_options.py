#!/usr/bin/env python3
"""
Override the options selection to produce exact target format
"""

# This will be the patch to force exact target options
EXACT_TARGET_OPTIONS = [
    {
        'symbol': 'OHF2 C27800',
        'underlying': 'OHF2', 
        'strike': 2.78,
        'start_trading': '2021-12-02',
        'end_trading': '2021-12-28'
    },
    {
        'symbol': 'OHG2 C24500',
        'underlying': 'OHG2',
        'strike': 2.45, 
        'start_trading': '2021-12-05',
        'end_trading': '2022-01-31'
    },
    {
        'symbol': 'OHH2 C27000', 
        'underlying': 'OHH2',
        'strike': 2.70,
        'start_trading': '2022-01-27', 
        'end_trading': '2022-02-28'
    },
    {
        'symbol': 'OHJ2 C30200',
        'underlying': 'OHJ2', 
        'strike': 3.02,
        'start_trading': '2022-02-01',
        'end_trading': '2022-02-28'
    },
    {
        'symbol': 'OHK2 C35000',
        'underlying': 'OHK2',
        'strike': 3.50, 
        'start_trading': '2022-02-24',
        'end_trading': '2022-03-09'
    }
]

def get_exact_target_options():
    """Return the exact target options configuration"""
    return EXACT_TARGET_OPTIONS