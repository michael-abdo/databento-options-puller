"""
Futures Manager for NY Harbor ULSD (OH) contracts.
Handles contract specifications, roll dates, and front-month identification.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import logging
from pathlib import Path
import calendar

# Add parent directory to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.date_utils import parse_date, is_trading_day, get_first_trading_day
from utils.symbol_utils import build_futures_symbol, parse_futures_symbol
from utils.logging_config import get_logger

logger = get_logger('futures')


class FuturesManager:
    """
    Manager for NY Harbor ULSD (OH) futures contracts.
    
    Handles:
    - Contract specifications and naming
    - Roll date identification
    - Front-month contract determination
    - Expiry date calculations
    """
    
    def __init__(self, root_symbol: str = "HO"):
        """Initialize futures manager with contract specifications.
        
        Args:
            root_symbol: Root symbol for futures (default: HO for heating oil)
        """
        self.root_symbol = root_symbol
        self.contract_months = {
            1: 'F',   # January
            2: 'G',   # February  
            3: 'H',   # March
            4: 'J',   # April
            5: 'K',   # May
            6: 'M',   # June
            7: 'N',   # July
            8: 'Q',   # August
            9: 'U',   # September
            10: 'V',  # October
            11: 'X',  # November
            12: 'Z'   # December
        }
        
        # OH contracts typically expire on last business day of month prior to delivery
        # For example, January contract (OHF) expires end of December
        self.expiry_offset_days = -1  # Day before delivery month
        
        logger.info(f"Initialized FuturesManager for {self.root_symbol} contracts")
    
    def get_contract_symbol(self, expiry_date: Union[str, datetime]) -> str:
        """
        Get the futures contract symbol for a given expiry date.
        
        Args:
            expiry_date: Contract expiry date
            
        Returns:
            Contract symbol (e.g., 'OHF2', 'OHG2')
        """
        if isinstance(expiry_date, str):
            expiry_date = parse_date(expiry_date)
        
        month_code = self.contract_months[expiry_date.month]
        year_code = str(expiry_date.year)[-1]  # Last digit of year
        
        symbol = f"{self.root_symbol}{month_code}{year_code}"
        
        logger.debug(f"Contract for {expiry_date.strftime('%Y-%m')}: {symbol}")
        
        return symbol
    
    def get_front_month_contract(self, trade_date: Union[str, datetime]) -> str:
        """
        Determine the front-month contract for a given trade date.
        
        Args:
            trade_date: Date to determine front month for
            
        Returns:
            Front-month contract symbol
        """
        if isinstance(trade_date, str):
            trade_date = parse_date(trade_date)
        
        # For OH contracts, we typically roll on the first trading day of the month
        # The front month is usually the next month's contract
        current_month = trade_date.month
        current_year = trade_date.year
        
        # If we're at the beginning of the month (first 5 trading days), 
        # we might still be in the previous month's contract
        roll_date = self.get_roll_date(current_year, current_month)
        
        if trade_date < roll_date:
            # Still in previous month's contract
            if current_month == 1:
                contract_month = 12
                contract_year = current_year - 1
            else:
                contract_month = current_month - 1
                contract_year = current_year
        else:
            # In current month's contract
            contract_month = current_month
            contract_year = current_year
        
        # Create contract expiry date
        contract_date = datetime(contract_year, contract_month, 1)
        contract_symbol = self.get_contract_symbol(contract_date)
        
        logger.debug(f"Front month for {trade_date.strftime('%Y-%m-%d')}: {contract_symbol}")
        
        return contract_symbol
    
    def get_roll_date(self, year: int, month: int) -> datetime:
        """
        Get the roll date for a specific month.
        
        Args:
            year: Year
            month: Month
            
        Returns:
            Roll date (first trading day of month)
        """
        # OH contracts typically roll on first trading day of the month
        first_day = datetime(year, month, 1)
        roll_date = get_first_trading_day(first_day)
        
        logger.debug(f"Roll date for {year}-{month:02d}: {roll_date.strftime('%Y-%m-%d')}")
        
        return roll_date
    
    def get_roll_schedule(self, start_date: Union[str, datetime], 
                         end_date: Union[str, datetime]) -> List[Dict]:
        """
        Generate complete roll schedule for date range.
        
        Args:
            start_date: Start of period
            end_date: End of period
            
        Returns:
            List of roll events with dates and contracts
        """
        if isinstance(start_date, str):
            start_date = parse_date(start_date)
        if isinstance(end_date, str):
            end_date = parse_date(end_date)
        
        roll_schedule = []
        
        # IMPORTANT: Start from 2 months BEFORE start_date to catch options 
        # that were selected before our period but are still active during it
        # (M+2 means options selected 2 months ago are still trading)
        roll_start = start_date - timedelta(days=62)  # ~2 months back
        current_year = roll_start.year
        current_month = roll_start.month
        
        while True:
            roll_date = self.get_roll_date(current_year, current_month)
            
            # Stop if roll date is beyond our end date
            if roll_date > end_date:
                break
            
            # Include if the roll date is before end date
            # This catches options selected before start_date that are still active
            # Determine contracts involved
            if current_month == 1:
                prev_month = 12
                prev_year = current_year - 1
            else:
                prev_month = current_month - 1
                prev_year = current_year
            
            prev_contract = self.get_contract_symbol(datetime(prev_year, prev_month, 1))
            new_contract = self.get_contract_symbol(datetime(current_year, current_month, 1))
            
            roll_event = {
                'roll_date': roll_date,
                'from_contract': prev_contract,
                'to_contract': new_contract,
                'month': current_month,
                'year': current_year
            }
            
            roll_schedule.append(roll_event)
            
            logger.debug(f"Roll event: {roll_date.strftime('%Y-%m-%d')} "
                       f"{prev_contract} → {new_contract}")
            
            # Move to next month
            if current_month == 12:
                current_month = 1
                current_year += 1
            else:
                current_month += 1
        
        logger.info(f"Generated {len(roll_schedule)} roll events from "
                   f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        return roll_schedule
    
    def get_expiry_date(self, contract_symbol: str) -> datetime:
        """
        Calculate expiry date for a futures contract.
        
        Args:
            contract_symbol: Contract symbol (e.g., 'OHF2')
            
        Returns:
            Contract expiry date
        """
        # Parse the contract symbol
        parts = parse_futures_symbol(contract_symbol)
        if not parts:
            raise ValueError(f"Invalid contract symbol: {contract_symbol}")
        
        root, month_code, year_code = parts
        
        # Find month number from code
        month_num = None
        for num, code in self.contract_months.items():
            if code == month_code:
                month_num = num
                break
        
        if month_num is None:
            raise ValueError(f"Invalid month code: {month_code}")
        
        # Determine full year (assuming 20xx for now)
        if year_code.isdigit():
            if len(year_code) == 1:
                year = 2020 + int(year_code)  # 2020s decade
            else:
                year = int(year_code)
        else:
            raise ValueError(f"Invalid year code: {year_code}")
        
        # Calculate expiry date (last business day of month prior to delivery)
        delivery_month = datetime(year, month_num, 1)
        
        # Go to last day of previous month
        if month_num == 1:
            expiry_month = 12
            expiry_year = year - 1
        else:
            expiry_month = month_num - 1
            expiry_year = year
        
        # Last day of the month
        last_day = calendar.monthrange(expiry_year, expiry_month)[1]
        expiry_date = datetime(expiry_year, expiry_month, last_day)
        
        # Adjust to last trading day
        while not is_trading_day(expiry_date):
            expiry_date -= timedelta(days=1)
        
        logger.debug(f"Expiry for {contract_symbol}: {expiry_date.strftime('%Y-%m-%d')}")
        
        return expiry_date
    
    def get_m_plus_n_contract(self, base_date: Union[str, datetime], n: int = 2) -> str:
        """
        Get contract that expires N months after the base date.
        
        Args:
            base_date: Reference date
            n: Number of months to add (default 2 for M+2)
            
        Returns:
            Contract symbol for M+n expiry
        """
        if isinstance(base_date, str):
            base_date = parse_date(base_date)
        
        # Add N months to base date
        target_month = base_date.month + n
        target_year = base_date.year
        
        # Handle year rollover
        while target_month > 12:
            target_month -= 12
            target_year += 1
        
        # Create target date
        target_date = datetime(target_year, target_month, 1)
        contract_symbol = self.get_contract_symbol(target_date)
        
        logger.debug(f"M+{n} contract for {base_date.strftime('%Y-%m-%d')}: {contract_symbol}")
        
        return contract_symbol
    
    def is_contract_active(self, contract_symbol: str, 
                          trade_date: Union[str, datetime]) -> bool:
        """
        Check if a contract is active (not expired) on a given date.
        
        Args:
            contract_symbol: Contract to check
            trade_date: Date to check
            
        Returns:
            True if contract is active
        """
        if isinstance(trade_date, str):
            trade_date = parse_date(trade_date)
        
        try:
            expiry_date = self.get_expiry_date(contract_symbol)
            is_active = trade_date <= expiry_date
            
            logger.debug(f"{contract_symbol} on {trade_date.strftime('%Y-%m-%d')}: "
                        f"{'active' if is_active else 'expired'} "
                        f"(expires {expiry_date.strftime('%Y-%m-%d')})")
            
            return is_active
            
        except ValueError as e:
            logger.error(f"Cannot check if {contract_symbol} is active: {e}")
            return False
    
    def get_contracts_for_period(self, start_date: Union[str, datetime], 
                                end_date: Union[str, datetime]) -> List[str]:
        """
        Get all contracts that were front-month during the given period.
        
        Args:
            start_date: Start of period
            end_date: End of period
            
        Returns:
            List of unique contract symbols
        """
        if isinstance(start_date, str):
            start_date = parse_date(start_date)
        if isinstance(end_date, str):
            end_date = parse_date(end_date)
        
        contracts = set()
        current_date = start_date
        
        while current_date <= end_date:
            if is_trading_day(current_date):
                front_month = self.get_front_month_contract(current_date)
                contracts.add(front_month)
            
            current_date += timedelta(days=1)
        
        contract_list = sorted(list(contracts))
        
        logger.info(f"Contracts for {start_date.strftime('%Y-%m-%d')} to "
                   f"{end_date.strftime('%Y-%m-%d')}: {contract_list}")
        
        return contract_list


def main():
    """Test the futures manager."""
    from utils.logging_config import setup_logging
    
    # Set up logging
    setup_logging()
    
    # Create manager
    manager = FuturesManager()
    
    # Test contract symbol generation
    logger.info("Testing contract symbol generation:")
    test_dates = ['2022-01-01', '2022-02-01', '2022-03-01']
    for date_str in test_dates:
        symbol = manager.get_contract_symbol(date_str)
        logger.info(f"  {date_str} → {symbol}")
    
    # Test front month identification
    logger.info("Testing front month identification:")
    test_dates = ['2021-12-01', '2021-12-15', '2022-01-01', '2022-01-15']
    for date_str in test_dates:
        front_month = manager.get_front_month_contract(date_str)
        logger.info(f"  {date_str} → {front_month}")
    
    # Test roll schedule
    logger.info("Testing roll schedule:")
    rolls = manager.get_roll_schedule('2021-12-01', '2022-04-01')
    for roll in rolls:
        logger.info(f"  {roll['roll_date'].strftime('%Y-%m-%d')}: "
              f"{roll['from_contract']} → {roll['to_contract']}")
    
    # Test M+2 contracts
    logger.info("Testing M+2 contract identification:")
    test_dates = ['2021-12-01', '2022-01-01', '2022-02-01']
    for date_str in test_dates:
        m_plus_2 = manager.get_m_plus_n_contract(date_str, 2)
        logger.info(f"  {date_str} + 2 months → {m_plus_2}")
    
    # Test expiry dates
    logger.info("Testing expiry date calculation:")
    test_contracts = ['OHF2', 'OHG2', 'OHH2', 'OHJ2']
    for contract in test_contracts:
        expiry = manager.get_expiry_date(contract)
        logger.info(f"  {contract} expires: {expiry.strftime('%Y-%m-%d')}")


if __name__ == "__main__":
    main()