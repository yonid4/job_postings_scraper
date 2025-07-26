"""
Scrapers module for the Job Application Automation System.

This module contains web scrapers for various job sites.
Each scraper should implement the BaseScraper interface.
"""

# Import the comprehensive base scraper
try:
    from .base_scraper import (
        BaseScraper,
        ScrapingResult,
        ScrapingConfig,
        sanitize_text,
        extract_salary_range,
        is_valid_url
    )
except ImportError:
    # Fallback for direct imports
    from base_scraper import (
        BaseScraper,
        ScrapingResult,
        ScrapingConfig,
        sanitize_text,
        extract_salary_range,
        is_valid_url
    )

# Import specific scrapers here when they are implemented
from .example_scraper import ExampleScraper, create_example_scraper
from .linkedin_scraper import LinkedInScraper, create_linkedin_scraper
# from .indeed_scraper import IndeedScraper

__all__ = [
    'BaseScraper',
    'ScrapingResult',
    'ScrapingConfig',
    'ExampleScraper',
    'create_example_scraper',
    'LinkedInScraper',
    'create_linkedin_scraper',
    'sanitize_text',
    'extract_salary_range',
    'is_valid_url',
] 