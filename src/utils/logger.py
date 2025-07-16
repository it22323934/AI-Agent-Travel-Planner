"""
Logging configuration for the Travel Planning System
"""

import logging
import logging.config
import os
from pathlib import Path
from datetime import datetime

from config.settings import settings


def setup_logging():
    """Setup logging configuration for the application"""
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d")
    log_filename = logs_dir / f"travel_planner_{timestamp}.log"
    
    # Logging configuration
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)8s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": "%(asctime)s [%(levelname)8s] %(name)s - %(funcName)s:%(lineno)d: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "simple": {
                "format": "[%(levelname)s] %(name)s: %(message)s"
            }
        },
        "handlers": {
            "console": {
                "level": "INFO",
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "stream": "ext://sys.stdout"
            },
            "file": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "formatter": "detailed",
                "filename": str(log_filename),
                "mode": "a",
                "encoding": "utf-8"
            },
            "error_file": {
                "level": "ERROR",
                "class": "logging.FileHandler",
                "formatter": "detailed",
                "filename": str(logs_dir / f"travel_planner_errors_{timestamp}.log"),
                "mode": "a",
                "encoding": "utf-8"
            }
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console", "file"],
                "level": settings.log_level,
                "propagate": False
            },
            "travel_planner_app": {
                "handlers": ["console", "file", "error_file"],
                "level": "INFO",
                "propagate": False
            },
            "agent": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False
            },
            "mcp": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False
            },
            "graph_nodes": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False
            },
            "workflow": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False
            }
        }
    }
    
    # Apply configuration
    logging.config.dictConfig(logging_config)
    
    # Log initialization
    logger = logging.getLogger("travel_planner_app")
    logger.info("Logging system initialized")
    logger.info(f"Log files: {log_filename}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    return logging.getLogger(name)


def log_function_call(func_name: str, args: dict = None, logger_name: str = "function_calls"):
    """Decorator to log function calls"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(logger_name)
            logger.debug(f"Calling {func_name} with args: {args}, kwargs: {kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func_name} completed successfully")
                return result
            except Exception as e:
                logger.error(f"{func_name} failed with error: {e}")
                raise
        return wrapper
    return decorator


def log_performance(func_name: str, logger_name: str = "performance"):
    """Decorator to log function performance"""
    def decorator(func):
        import time
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(logger_name)
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                end_time = time.time()
                execution_time = end_time - start_time
                logger.info(f"{func_name} executed in {execution_time:.3f} seconds")
                return result
            except Exception as e:
                end_time = time.time()
                execution_time = end_time - start_time
                logger.error(f"{func_name} failed after {execution_time:.3f} seconds: {e}")
                raise
        return wrapper
    return decorator