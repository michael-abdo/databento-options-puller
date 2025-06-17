"""
Symbol parsing utilities for options contracts.
Handles symbols like "OHF2 C27800" from example_output.csv
"""

import re
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger('utils')

# Month codes mapping
MONTH_CODES = {
    'F': 1,   # January
    'G': 2,   # February  
    'H': 3,   # March
    'J': 4,   # April
    'K': 5,   # May
    'M': 6,   # June
    'N': 7,   # July
    'Q': 8,   # August
    'U': 9,   # September
    'V': 10,  # October
    'X': 11,  # November
    'Z': 12   # December
}

# Reverse mapping
MONTH_TO_CODE = {v: k for k, v in MONTH_CODES.items()}


def parse_option_symbol(symbol: str) -> Dict[str, any]:
    """
    Parse an option symbol like "OHF2 C27800" into components.
    
    Args:
        symbol: Option symbol string
        
    Returns:
        Dictionary with parsed components:
        - root: Underlying symbol (e.g., "OH")
        - month_code: Month code letter (e.g., "F")
        - month: Month number (e.g., 1)
        - year_code: Year code (e.g., "2")
        - year: Full year (e.g., 2022)
        - option_type: "C" for call, "P" for put
        - strike: Strike price (e.g., 278.00)
        - strike_raw: Raw strike value (e.g., 27800)
        
    Raises:
        ValueError: If symbol cannot be parsed
    """
    # Expected format: "OHF2 C27800"
    # Pattern: ROOT + MONTH_CODE + YEAR + SPACE + OPTION_TYPE + STRIKE
    pattern = r'^([A-Z]+)([FGHJKMNQUVXZ])(\d)\s+([CP])(\d+)$'
    
    match = re.match(pattern, symbol.strip())
    if not match:
        raise ValueError(f"Unable to parse option symbol: {symbol}")
    
    root, month_code, year_code, option_type, strike_raw = match.groups()
    
    # Parse month
    if month_code not in MONTH_CODES:
        raise ValueError(f"Invalid month code: {month_code}")
    month = MONTH_CODES[month_code]
    
    # Parse year (assuming 20XX for single digit)
    year = 2020 + int(year_code)
    
    # Parse strike (divide by 100 to get actual price)
    strike = float(strike_raw) / 100
    
    result = {
        'root': root,
        'month_code': month_code,
        'month': month,
        'year_code': year_code,
        'year': year,
        'option_type': option_type,
        'strike': strike,
        'strike_raw': int(strike_raw),
        'full_symbol': symbol
    }
    
    logger.debug(f"Parsed {symbol}: {result}")
    return result


def build_option_symbol(root: str, 
                       month: int, 
                       year: int, 
                       option_type: str, 
                       strike: float) -> str:
    """
    Build an option symbol from components.
    
    Args:
        root: Underlying symbol (e.g., "OH")
        month: Month number (1-12)
        year: Full year (e.g., 2022)
        option_type: "C" for call, "P" for put
        strike: Strike price (e.g., 278.00)
        
    Returns:
        Formatted option symbol (e.g., "OHF2 C27800")
    """
    # Get month code
    if month not in MONTH_TO_CODE:
        raise ValueError(f"Invalid month: {month}")
    month_code = MONTH_TO_CODE[month]
    
    # Get year code (last digit)
    year_code = str(year)[-1]
    
    # Format strike (multiply by 100, no decimals)
    strike_raw = int(strike * 100)
    
    # Build symbol
    symbol = f"{root}{month_code}{year_code} {option_type}{strike_raw}"
    
    logger.debug(f"Built symbol: {symbol}")
    return symbol


def extract_month_year(symbol: str) -> Tuple[int, int]:
    """
    Extract month and year from option symbol.
    
    Args:
        symbol: Option symbol
        
    Returns:
        Tuple of (month, year)
    """
    parsed = parse_option_symbol(symbol)
    return parsed['month'], parsed['year']


def extract_strike(symbol: str) -> float:
    """
    Extract strike price from option symbol.
    
    Args:
        symbol: Option symbol
        
    Returns:
        Strike price
    """
    parsed = parse_option_symbol(symbol)
    return parsed['strike']


def extract_expiry_code(symbol: str) -> str:
    """
    Extract expiry code (e.g., "F2") from option symbol.
    
    Args:
        symbol: Option symbol
        
    Returns:
        Expiry code
    """
    parsed = parse_option_symbol(symbol)
    return parsed['month_code'] + parsed['year_code']


def is_call_option(symbol: str) -> bool:
    """
    Check if option is a call.
    
    Args:
        symbol: Option symbol
        
    Returns:
        True if call option
    """
    parsed = parse_option_symbol(symbol)
    return parsed['option_type'] == 'C'


def is_put_option(symbol: str) -> bool:
    """
    Check if option is a put.
    
    Args:
        symbol: Option symbol
        
    Returns:
        True if put option
    """
    parsed = parse_option_symbol(symbol)
    return parsed['option_type'] == 'P'


def build_futures_symbol(root: str, month: int, year: int) -> str:
    """
    Build futures symbol from components.
    
    Args:
        root: Underlying symbol (e.g., "OH")
        month: Month number (1-12) 
        year: Full year (e.g., 2022)
        
    Returns:
        Futures symbol (e.g., "OHF2")
    """
    if month not in MONTH_TO_CODE:
        raise ValueError(f"Invalid month: {month}")
    
    month_code = MONTH_TO_CODE[month]
    year_code = str(year)[-1]
    
    return f"{root}{month_code}{year_code}"


def parse_futures_symbol(symbol: str) -> Tuple[str, str, str]:
    """
    Parse futures symbol into components.
    
    Args:
        symbol: Futures symbol (e.g., "OHF2")
        
    Returns:
        Tuple of (root, month_code, year_code)
    """
    # Pattern: ROOT + MONTH_CODE + YEAR_CODE
    pattern = r'^([A-Z]+)([FGHJKMNQUVXZ])(\d)$'
    
    match = re.match(pattern, symbol.strip())
    if not match:
        return None
    
    root, month_code, year_code = match.groups()
    return root, month_code, year_code


def get_futures_symbol(root: str, month: int, year: int) -> str:
    """
    Build futures symbol from components.
    
    Args:
        root: Underlying symbol (e.g., "OH")
        month: Month number (1-12) 
        year: Full year (e.g., 2022)
        
    Returns:
        Futures symbol (e.g., "OHF2")
    """
    if month not in MONTH_TO_CODE:
        raise ValueError(f"Invalid month: {month}")
    
    month_code = MONTH_TO_CODE[month]
    year_code = str(year)[-1]
    
    return f"{root}{month_code}{year_code}"


def compare_expiries(symbol1: str, symbol2: str) -> int:
    """
    Compare expiry dates of two option symbols.
    
    Args:
        symbol1: First option symbol
        symbol2: Second option symbol
        
    Returns:
        -1 if symbol1 expires before symbol2
        0 if same expiry
        1 if symbol1 expires after symbol2
    """
    month1, year1 = extract_month_year(symbol1)
    month2, year2 = extract_month_year(symbol2)
    
    date1 = year1 * 12 + month1
    date2 = year2 * 12 + month2
    
    if date1 < date2:
        return -1
    elif date1 > date2:
        return 1
    else:
        return 0