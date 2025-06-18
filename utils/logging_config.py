"""
Simplified logging configuration - one folder per run with clean organization.
"""

import logging
import os
from datetime import datetime
from typing import Optional

# Global to track current run's log directory
_current_log_dir = None

def setup_logging(log_dir: str = "logs", 
                  level: int = logging.INFO,
                  console_level: int = logging.INFO) -> None:
    """
    Set up logging system - creates one folder per run with all logs inside.
    
    Args:
        log_dir: Base directory for logs
        level: Logging level for file handlers
        console_level: Logging level for console output
    """
    global _current_log_dir
    
    # Create timestamp for this run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create run-specific directory
    run_dir = os.path.join(log_dir, f"run_{timestamp}")
    os.makedirs(run_dir, exist_ok=True)
    _current_log_dir = run_dir
    
    # Configure formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Add file handler for main log
    main_log_path = os.path.join(run_dir, 'main.log')
    file_handler = logging.FileHandler(main_log_path)
    file_handler.setLevel(level)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Log initialization
    logger = logging.getLogger('main')
    logger.info("="*60)
    logger.info("Databento Options Puller - Logging Initialized")
    logger.info(f"Log directory: {run_dir}")
    logger.info(f"Timestamp: {timestamp}")
    logger.info("="*60)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger by name.
    
    Args:
        name: Logger name (e.g., 'main', 'databento', 'options')
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    
    # If logging hasn't been set up yet, add basic console handler
    if not logger.handlers and not logger.parent.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger


def get_current_log_dir() -> Optional[str]:
    """Get the current run's log directory."""
    return _current_log_dir