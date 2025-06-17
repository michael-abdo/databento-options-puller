"""
Date utilities for handling various date formats and trading calendar logic.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Union
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar, Holiday
from pandas.tseries.offsets import Day
import logging

logger = logging.getLogger('utils')


def parse_date(date_str: str) -> datetime:
    """
    Parse date string in various formats.
    Primary format expected: MM/DD/YY (from example_output.csv)
    
    Args:
        date_str: Date string to parse
        
    Returns:
        datetime object
        
    Raises:
        ValueError: If date cannot be parsed
    """
    # Try common formats in order of likelihood
    formats = [
        "%m/%d/%y",     # 12/31/21 (example format)
        "%m/%d/%Y",     # 12/31/2021
        "%Y-%m-%d",     # 2021-12-31 (ISO)
        "%Y/%m/%d",     # 2021/12/31
        "%d/%m/%y",     # 31/12/21 (European)
        "%d/%m/%Y",     # 31/12/2021 (European)
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    
    # If none work, try pandas
    try:
        return pd.to_datetime(date_str).to_pydatetime()
    except:
        raise ValueError(f"Unable to parse date: {date_str}")


def format_date(date: Union[datetime, pd.Timestamp], 
                format_str: str = "%m/%d/%y") -> str:
    """
    Format date to string. Default format matches example_output.csv
    
    Args:
        date: Date to format
        format_str: Output format (default: MM/DD/YY)
        
    Returns:
        Formatted date string
    """
    if isinstance(date, pd.Timestamp):
        date = date.to_pydatetime()
    return date.strftime(format_str)


def is_trading_day(date: datetime) -> bool:
    """
    Check if a given date is a trading day (not weekend or US holiday).
    
    Args:
        date: Date to check
        
    Returns:
        True if trading day, False otherwise
    """
    # Check weekend
    if date.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False
    
    # Check holidays
    cal = USFederalHolidayCalendar()
    holidays = cal.holidays(start=date, end=date + timedelta(days=1))
    
    return date not in holidays.to_pydatetime()


def get_next_trading_day(date: datetime) -> datetime:
    """
    Get the next trading day from given date.
    
    Args:
        date: Starting date
        
    Returns:
        Next trading day
    """
    next_day = date + timedelta(days=1)
    while not is_trading_day(next_day):
        next_day += timedelta(days=1)
    return next_day


def get_previous_trading_day(date: datetime) -> datetime:
    """
    Get the previous trading day from given date.
    
    Args:
        date: Starting date
        
    Returns:
        Previous trading day
    """
    prev_day = date - timedelta(days=1)
    while not is_trading_day(prev_day):
        prev_day -= timedelta(days=1)
    return prev_day


def get_first_trading_day_of_month(year: int, month: int) -> datetime:
    """
    Get the first trading day of a given month.
    
    Args:
        year: Year
        month: Month (1-12)
        
    Returns:
        First trading day of the month
    """
    first_day = datetime(year, month, 1)
    
    if is_trading_day(first_day):
        return first_day
    else:
        return get_next_trading_day(first_day)


def get_last_trading_day_of_month(year: int, month: int) -> datetime:
    """
    Get the last trading day of a given month.
    
    Args:
        year: Year
        month: Month (1-12)
        
    Returns:
        Last trading day of the month
    """
    # Get first day of next month
    if month == 12:
        next_month_first = datetime(year + 1, 1, 1)
    else:
        next_month_first = datetime(year, month + 1, 1)
    
    # Go back one day
    last_day = next_month_first - timedelta(days=1)
    
    if is_trading_day(last_day):
        return last_day
    else:
        return get_previous_trading_day(last_day)


def generate_trading_days(start_date: Union[str, datetime], 
                         end_date: Union[str, datetime]) -> List[datetime]:
    """
    Generate list of trading days between start and end dates.
    
    Args:
        start_date: Start date (string or datetime)
        end_date: End date (string or datetime)
        
    Returns:
        List of trading days
    """
    # Convert strings to datetime if needed
    if isinstance(start_date, str):
        start_date = parse_date(start_date)
    if isinstance(end_date, str):
        end_date = parse_date(end_date)
    
    # Use pandas for efficiency
    date_range = pd.bdate_range(start=start_date, end=end_date, freq='B')
    
    # Filter out holidays
    cal = USFederalHolidayCalendar()
    holidays = cal.holidays(start=start_date, end=end_date)
    
    trading_days = [d.to_pydatetime() for d in date_range if d not in holidays]
    
    return trading_days


def count_trading_days(start_date: Union[str, datetime], 
                      end_date: Union[str, datetime]) -> int:
    """
    Count trading days between two dates (inclusive).
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        Number of trading days
    """
    trading_days = generate_trading_days(start_date, end_date)
    return len(trading_days)


def add_trading_days(date: Union[str, datetime], days: int) -> datetime:
    """
    Add a number of trading days to a date.
    
    Args:
        date: Starting date
        days: Number of trading days to add (can be negative)
        
    Returns:
        Resulting date
    """
    if isinstance(date, str):
        date = parse_date(date)
    
    if days == 0:
        return date
    
    current = date
    days_added = 0
    step = 1 if days > 0 else -1
    
    while days_added != days:
        current += timedelta(days=step)
        if is_trading_day(current):
            days_added += step
    
    return current