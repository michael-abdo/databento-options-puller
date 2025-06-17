"""
Centralized logging configuration for the feedback loop system.
Each module gets its own log file for easy debugging.
"""

import logging
import os
from datetime import datetime
from typing import Dict, Optional

def setup_logging(log_dir: str = "logs", 
                  level: int = logging.DEBUG,
                  console_level: int = logging.INFO) -> Dict[str, logging.Logger]:
    """
    Set up multi-file logging system for the feedback loop.
    
    Args:
        log_dir: Directory to store log files
        level: Logging level for file handlers
        console_level: Logging level for console output
        
    Returns:
        Dictionary of configured loggers
    """
    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)
    
    # Create timestamp for this run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Define loggers and their files
    logger_configs = {
        'main': f'{log_dir}/main_{timestamp}.log',
        'analyzer': f'{log_dir}/analyzer_{timestamp}.log',
        'generator': f'{log_dir}/generator_{timestamp}.log',
        'validator': f'{log_dir}/validator_{timestamp}.log',
        'refiner': f'{log_dir}/refiner_{timestamp}.log',
        'utils': f'{log_dir}/utils_{timestamp}.log'
    }
    
    # Also create a combined log
    combined_log = f'{log_dir}/combined_{timestamp}.log'
    
    # Configure formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Configure root logger to capture everything
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Add combined file handler
    combined_handler = logging.FileHandler(combined_log)
    combined_handler.setLevel(logging.DEBUG)
    combined_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(combined_handler)
    
    # Add console handler to root
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Configure individual loggers
    loggers = {}
    for name, log_file in logger_configs.items():
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Remove any existing handlers
        logger.handlers.clear()
        
        # Add file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
        
        # Prevent propagation to avoid duplicate logs
        logger.propagate = False
        
        # But also add to combined log
        logger.addHandler(combined_handler)
        
        # Add console handler for important messages
        if name == 'main':
            logger.addHandler(console_handler)
        
        loggers[name] = logger
        
    # Log initialization
    main_logger = loggers['main']
    main_logger.info("="*60)
    main_logger.info("Logging system initialized")
    main_logger.info(f"Log directory: {log_dir}")
    main_logger.info(f"Timestamp: {timestamp}")
    main_logger.info("="*60)
    
    return loggers


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger by name. If logging isn't set up, returns a basic logger.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    
    # If no handlers, add a basic console handler
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger