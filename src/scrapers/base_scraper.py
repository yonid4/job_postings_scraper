"""
Abstract base scraper class for job site scrapers.

This module defines the BaseScraper abstract class that all job site scrapers
must implement. It provides a standardized interface for scraping job listings
with built-in error handling, rate limiting, and logging.
"""

import time
import random
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
import logging

try:
    from ..data.models import JobListing, ScrapingSession
    from ..utils.logger import JobAutomationLogger
except ImportError:
    # Fallback for direct imports
    from data.models import JobListing, ScrapingSession
    from utils.logger import JobAutomationLogger


@dataclass
class ScrapingResult:
    """
    Result of a scraping operation.
    
    This class encapsulates the results of a scraping operation,
    including success status, scraped jobs, session information,
    and any error messages or metadata.
    """
    success: bool
    jobs: List[JobListing]
    session: ScrapingSession
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    warnings: List[str] = field(default_factory=list)
    performance_metrics: Optional[Dict[str, float]] = None


@dataclass
class ScrapingConfig:
    """
    Configuration for a scraper instance.
    
    This class contains all the configuration parameters needed
    for a scraper to operate properly, including rate limiting,
    timeouts, and behavior settings.
    """
    # Rate limiting
    delay_min: float = 1.0
    delay_max: float = 3.0
    max_requests_per_minute: int = 20
    
    # Timeouts
    page_load_timeout: int = 30
    element_wait_timeout: int = 10
    request_timeout: int = 15
    
    # Behavior settings
    max_jobs_per_session: int = 100
    respect_robots_txt: bool = True
    follow_redirects: bool = True
    retry_failed_requests: bool = True
    max_retries: int = 3
    
    # Anti-detection
    use_random_delays: bool = True
    rotate_user_agents: bool = True
    use_proxy: bool = False
    proxy_list: List[str] = field(default_factory=list)
    
    # Logging
    log_level: str = "INFO"
    log_requests: bool = True
    log_performance: bool = True
    
    # Site-specific settings
    site_name: str = ""
    base_url: str = ""
    search_url_template: str = ""
    
    def validate(self) -> List[str]:
        """
        Validate the configuration and return any errors.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        if self.delay_min < 0:
            errors.append("delay_min cannot be negative")
        
        if self.delay_max < self.delay_min:
            errors.append("delay_max cannot be less than delay_min")
        
        if self.max_requests_per_minute <= 0:
            errors.append("max_requests_per_minute must be positive")
        
        if self.page_load_timeout <= 0:
            errors.append("page_load_timeout must be positive")
        
        if self.element_wait_timeout <= 0:
            errors.append("element_wait_timeout must be positive")
        
        if self.request_timeout <= 0:
            errors.append("request_timeout must be positive")
        
        if self.max_jobs_per_session <= 0:
            errors.append("max_jobs_per_session must be positive")
        
        if self.max_retries < 0:
            errors.append("max_retries cannot be negative")
        
        if not self.site_name:
            errors.append("site_name is required")
        
        if not self.base_url:
            errors.append("base_url is required")
        
        return errors


class BaseScraper(ABC):
    """
    Abstract base class for all job site scrapers.
    
    This class defines the interface that all job scrapers must implement.
    It provides common functionality for rate limiting, error handling,
    logging, and session management.
    """
    
    def __init__(self, config: ScrapingConfig) -> None:
        """
        Initialize the scraper with configuration.
        
        Args:
            config: Configuration for the scraper
        """
        self.config = config
        self.session: Optional[ScrapingSession] = None
        self.logger = JobAutomationLogger(
            name=f"{config.site_name}_scraper",
            log_level=config.log_level
        )
        
        # Performance tracking
        self.request_count = 0
        self.start_time: Optional[datetime] = None
        self.last_request_time: Optional[datetime] = None
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate the scraper configuration."""
        errors = self.config.validate()
        if errors:
            error_msg = f"Invalid configuration for {self.config.site_name} scraper: " + "; ".join(errors)
            self.logger.logger.error(error_msg)
            raise ValueError(error_msg)
        
        self.logger.logger.info(f"Configuration validated for {self.config.site_name} scraper")
    
    @abstractmethod
    def scrape_jobs(self, keywords: List[str], location: str, **kwargs) -> ScrapingResult:
        """
        Scrape jobs from the job site.
        
        This is the main method that scrapers must implement. It should:
        1. Create a search URL based on keywords and location
        2. Navigate to the search results page
        3. Extract job listings from the page
        4. Handle pagination if needed
        5. Return a ScrapingResult with the found jobs
        
        Args:
            keywords: List of job keywords to search for
            location: Location to search in
            **kwargs: Additional search parameters (experience_level, job_type, etc.)
            
        Returns:
            ScrapingResult containing the scraped jobs and session info
        """
        pass
    
    @abstractmethod
    def get_job_details(self, job_url: str) -> Optional[JobListing]:
        """
        Get detailed information about a specific job.
        
        This method should navigate to a job's detail page and extract
        comprehensive information about the position.
        
        Args:
            job_url: URL of the job to get details for
            
        Returns:
            JobListing with detailed information, or None if failed
        """
        pass
    
    @abstractmethod
    def build_search_url(self, keywords: List[str], location: str, **kwargs) -> str:
        """
        Build the search URL for the job site.
        
        Args:
            keywords: List of job keywords
            location: Location to search in
            **kwargs: Additional search parameters
            
        Returns:
            Complete search URL for the job site
        """
        pass
    
    @abstractmethod
    def extract_job_listings_from_page(self, page_content: Any) -> List[JobListing]:
        """
        Extract job listings from a search results page.
        
        Args:
            page_content: The page content (HTML, BeautifulSoup object, etc.)
            
        Returns:
            List of JobListing objects extracted from the page
        """
        pass
    
    @abstractmethod
    def extract_job_details_from_page(self, page_content: Any, job_url: str) -> Optional[JobListing]:
        """
        Extract detailed job information from a job detail page.
        
        Args:
            page_content: The page content (HTML, BeautifulSoup object, etc.)
            job_url: URL of the job being processed
            
        Returns:
            JobListing with detailed information, or None if failed
        """
        pass
    
    def start_session(self, keywords: List[str], location: str) -> ScrapingSession:
        """
        Start a new scraping session.
        
        Args:
            keywords: Search keywords for this session
            location: Search location for this session
            
        Returns:
            New ScrapingSession instance
        """
        self.session = ScrapingSession(
            job_site=self.config.site_name,
            search_keywords=keywords,
            location=location
        )
        self.start_time = datetime.now()
        self.request_count = 0
        
        self.logger.logger.info(
            f"Started scraping session for {self.config.site_name} - "
            f"Keywords: {keywords}, Location: {location}"
        )
        
        return self.session
    
    def finish_session(self) -> None:
        """Finish the current scraping session."""
        if self.session and not self.session.completed:
            self.session.finish()
            
            # Calculate performance metrics
            if self.start_time:
                total_duration = (datetime.now() - self.start_time).total_seconds()
                requests_per_minute = (self.request_count / total_duration) * 60 if total_duration > 0 else 0
                
                self.logger.logger.info(
                    f"Finished scraping session for {self.config.site_name} - "
                    f"Jobs found: {self.session.jobs_found}, "
                    f"Jobs processed: {self.session.jobs_processed}, "
                    f"Duration: {total_duration:.2f}s, "
                    f"Requests/min: {requests_per_minute:.1f}"
                )
    
    def rate_limit(self) -> None:
        """
        Apply rate limiting between requests.
        
        This method implements intelligent rate limiting based on the configuration,
        including random delays and request frequency monitoring.
        """
        if not self.config.use_random_delays:
            return
        
        # Calculate delay
        if self.config.use_random_delays:
            delay = random.uniform(self.config.delay_min, self.config.delay_max)
        else:
            delay = self.config.delay_min
        
        # Check if we're exceeding requests per minute
        if self.last_request_time:
            time_since_last = (datetime.now() - self.last_request_time).total_seconds()
            if time_since_last < (60 / self.config.max_requests_per_minute):
                additional_delay = (60 / self.config.max_requests_per_minute) - time_since_last
                delay = max(delay, additional_delay)
        
        if delay > 0:
            self.logger.logger.debug(f"Rate limiting: sleeping for {delay:.2f} seconds")
            time.sleep(delay)
        
        self.last_request_time = datetime.now()
        self.request_count += 1
    
    def handle_error(self, error: Exception, context: str, url: str = "") -> None:
        """
        Handle and log errors during scraping.
        
        Args:
            error: The exception that occurred
            context: Context where the error occurred
            url: URL being processed when error occurred
        """
        error_msg = f"Error in {context}"
        if url:
            error_msg += f" (URL: {url})"
        error_msg += f": {str(error)}"
        
        self.logger.log_scraping_error(self.config.site_name, error, url)
        
        if self.session:
            self.session.errors_encountered += 1
    
    def retry_operation(self, operation: callable, *args, **kwargs) -> Any:
        """
        Retry an operation with exponential backoff.
        
        Args:
            operation: Function to retry
            *args: Arguments for the operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            Result of the operation
            
        Raises:
            Exception: If all retries fail
        """
        if not self.config.retry_failed_requests:
            return operation(*args, **kwargs)
        
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.config.max_retries:
                    # Exponential backoff
                    delay = (2 ** attempt) * self.config.delay_min
                    self.logger.logger.warning(
                        f"Operation failed (attempt {attempt + 1}/{self.config.max_retries + 1}), "
                        f"retrying in {delay:.2f}s: {str(e)}"
                    )
                    time.sleep(delay)
                else:
                    self.logger.logger.error(
                        f"Operation failed after {self.config.max_retries + 1} attempts: {str(e)}"
                    )
        
        raise last_exception
    
    def cleanup(self) -> None:
        """
        Clean up resources used by the scraper.
        
        This method should be called when the scraper is no longer needed.
        It ensures proper cleanup of any resources (browser sessions, connections, etc.).
        """
        if self.session and not self.session.completed:
            self.finish_session()
        
        self.logger.logger.info(f"Cleanup completed for {self.config.site_name} scraper")
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """
        Get performance metrics for the current session.
        
        Returns:
            Dictionary of performance metrics
        """
        if not self.start_time:
            return {}
        
        total_duration = (datetime.now() - self.start_time).total_seconds()
        requests_per_minute = (self.request_count / total_duration) * 60 if total_duration > 0 else 0
        
        return {
            "total_duration": total_duration,
            "requests_count": self.request_count,
            "requests_per_minute": requests_per_minute,
            "jobs_found": self.session.jobs_found if self.session else 0,
            "jobs_processed": self.session.jobs_processed if self.session else 0,
            "errors_encountered": self.session.errors_encountered if self.session else 0
        }
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()


# Utility functions for scrapers
def sanitize_text(text: str) -> str:
    """
    Sanitize text extracted from web pages.
    
    Args:
        text: Raw text from web page
        
    Returns:
        Cleaned and normalized text
    """
    if not text:
        return ""
    
    # Remove extra whitespace and normalize
    text = " ".join(text.split())
    
    # Remove common unwanted characters
    text = text.replace('\xa0', ' ')  # Non-breaking space
    text = text.replace('\u200b', '')  # Zero-width space
    
    return text.strip()


def extract_salary_range(text: str) -> tuple[Optional[int], Optional[int]]:
    """
    Extract salary range from text.
    
    Args:
        text: Text that may contain salary information
        
    Returns:
        Tuple of (min_salary, max_salary) or (None, None) if not found
    """
    import re
    
    if not text:
        return None, None
    
    # Common salary patterns
    patterns = [
        r'\$(\d{1,3}(?:,\d{3})*)\s*-\s*\$(\d{1,3}(?:,\d{3})*)',  # $50,000 - $80,000
        r'\$(\d{1,3}(?:,\d{3})*)\s*to\s*\$(\d{1,3}(?:,\d{3})*)',  # $50,000 to $80,000
        r'(\d{1,3}(?:,\d{3})*)\s*-\s*(\d{1,3}(?:,\d{3})*)\s*k',   # 50k - 80k
        r'(\d{1,3}(?:,\d{3})*)\s*to\s*(\d{1,3}(?:,\d{3})*)\s*k',  # 50k to 80k
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            min_sal = int(match.group(1).replace(',', ''))
            max_sal = int(match.group(2).replace(',', ''))
            
            # Convert k to thousands
            if 'k' in pattern:
                min_sal *= 1000
                max_sal *= 1000
            
            return min_sal, max_sal
    
    return None, None


def is_valid_url(url: str) -> bool:
    """
    Check if a URL is valid.
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL is valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False 