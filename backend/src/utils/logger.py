"""
Logging configuration and utilities for the Job Application Automation System.

This module provides a centralized logging system with support for:
- Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- File and console output
- Colored console output for better readability
- Log rotation to manage file sizes
- Structured logging for better debugging
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional
import colorlog
from datetime import datetime


class JobAutomationLogger:
    """
    Centralized logging system for the Job Application Automation System.
    
    This class provides a comprehensive logging solution with support for
    multiple output formats, log rotation, and structured logging.
    """
    
    def __init__(
        self,
        name: str = "job_automation",
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ) -> None:
        """
        Initialize the logging system.
        
        Args:
            name: Logger name
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Path to log file (optional)
            max_file_size: Maximum size of log file before rotation
            backup_count: Number of backup files to keep
        """
        self.name = name
        self.log_level = getattr(logging, log_level.upper())
        self.log_file = log_file
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.log_level)
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Add handlers
        self._setup_console_handler()
        if log_file:
            self._setup_file_handler()
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def _setup_console_handler(self) -> None:
        """Set up colored console logging handler."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        
        # Create colored formatter
        formatter = colorlog.ColoredFormatter(
            fmt='%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            },
            secondary_log_colors={},
            style='%'
        )
        
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def _setup_file_handler(self) -> None:
        """Set up file logging handler with rotation."""
        # Ensure log directory exists
        log_path = Path(self.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_file,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(self.log_level)
        
        # Create file formatter (no colors for file)
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance."""
        return self.logger
    
    def log_job_discovery(self, job_site: str, jobs_found: int, duration: float) -> None:
        """
        Log job discovery results.
        
        Args:
            job_site: Name of the job site scraped
            jobs_found: Number of jobs found
            duration: Time taken for scraping in seconds
        """
        self.logger.info(
            f"Job discovery completed - Site: {job_site}, "
            f"Jobs found: {jobs_found}, Duration: {duration:.2f}s"
        )
    
    def log_application_attempt(
        self,
        job_title: str,
        company: str,
        linkedin_url: str,
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        """
        Log application attempt results.
        
        Args:
            job_title: Title of the job applied to
            company: Company name
            linkedin_url: URL of the job posting
            status: Application status (success, failed, skipped)
            error_message: Error message if application failed
        """
        if status == "success":
            self.logger.info(
                f"Application successful - {job_title} at {company} ({linkedin_url})"
            )
        elif status == "failed":
            self.logger.error(
                f"Application failed - {job_title} at {company} ({linkedin_url}): {error_message}"
            )
        elif status == "skipped":
            self.logger.warning(
                f"Application skipped - {job_title} at {company} ({linkedin_url}): {error_message}"
            )
    
    def log_scraping_error(self, job_site: str, error: Exception, url: str) -> None:
        """
        Log scraping errors with context.
        
        Args:
            job_site: Name of the job site
            error: The exception that occurred
            url: URL that was being scraped
        """
        self.logger.error(
            f"Scraping error on {job_site} - URL: {url}, Error: {str(error)}",
            exc_info=True
        )
    
    def log_rate_limit_hit(self, job_site: str, delay: float) -> None:
        """
        Log when rate limiting is triggered.
        
        Args:
            job_site: Name of the job site
            delay: Delay time in seconds
        """
        self.logger.warning(
            f"Rate limit hit on {job_site}, waiting {delay:.2f} seconds"
        )
    
    def log_configuration_loaded(self, config_path: str) -> None:
        """
        Log when configuration is successfully loaded.
        
        Args:
            config_path: Path to the configuration file
        """
        self.logger.info(f"Configuration loaded from {config_path}")
    
    def log_api_error(self, api_name: str, error: Exception, operation: str) -> None:
        """
        Log API-related errors.
        
        Args:
            api_name: Name of the API (e.g., 'Google Sheets')
            error: The exception that occurred
            operation: Operation being performed
        """
        self.logger.error(
            f"API error in {api_name} during {operation}: {str(error)}",
            exc_info=True
        )
    
    def log_system_startup(self, version: str) -> None:
        """
        Log system startup information.
        
        Args:
            version: System version
        """
        self.logger.info(f"Job Application Automation System v{version} starting up")
    
    def log_system_shutdown(self) -> None:
        """Log system shutdown."""
        self.logger.info("Job Application Automation System shutting down")
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str = "") -> None:
        """
        Log performance metrics.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Unit of measurement
        """
        self.logger.info(f"Performance metric - {metric_name}: {value}{unit}")
    
    def log_security_event(self, event_type: str, details: str) -> None:
        """
        Log security-related events.
        
        Args:
            event_type: Type of security event
            details: Event details
        """
        self.logger.warning(f"Security event - {event_type}: {details}")
    
    def log_error(self, message: str) -> None:
        """Log an error message."""
        self.logger.error(message)
    
    def error(self, message: str) -> None:
        """Log an error message (alias for log_error)."""
        self.logger.error(message)
    
    def info(self, message: str) -> None:
        """Log an info message."""
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """Log a warning message."""
        self.logger.warning(message)
    
    def debug(self, message: str) -> None:
        """Log a debug message."""
        self.logger.debug(message)


def setup_logging(
    name: str = "job_automation",
    log_level: str = "INFO",
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Convenience function to set up logging for the application.
    
    Args:
        name: Logger name
        log_level: Logging level
        log_file: Path to log file (optional)
    
    Returns:
        Configured logger instance
    """
    logger_instance = JobAutomationLogger(name, log_level, log_file)
    return logger_instance.get_logger()


def get_logger(name: str = "job_automation") -> logging.Logger:
    """
    Get a logger instance by name.
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Create a default logger instance
default_logger = setup_logging() 