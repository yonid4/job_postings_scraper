"""
Example scraper implementation.

This module demonstrates how to implement a proper scraper
using the BaseScraper interface. This is for educational purposes
and shows the correct patterns to follow.
"""

import time
import random
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse

from .base_scraper import BaseScraper, ScrapingResult, ScrapingConfig
try:
    from ..data.models import JobListing, ScrapingSession
    from ..utils.logger import JobAutomationLogger
except ImportError:
    # Fallback for direct imports
    from data.models import JobListing, ScrapingSession
    from utils.logger import JobAutomationLogger


class ExampleScraper(BaseScraper):
    """
    Example scraper implementation.
    
    This class demonstrates the proper way to implement a scraper
    using the BaseScraper interface. It includes:
    - Proper error handling
    - Rate limiting
    - Logging
    - Configuration validation
    - Resource cleanup
    """
    
    def __init__(self, config: ScrapingConfig) -> None:
        """
        Initialize the example scraper.
        
        Args:
            config: Configuration for the scraper
        """
        super().__init__(config)
        self.base_url = "https://example-jobs.com"
    
    def scrape_jobs(self, keywords: List[str], location: str, **kwargs) -> ScrapingResult:
        """
        Scrape jobs from the example job site.
        
        Args:
            keywords: List of job keywords to search for
            location: Location to search in
            **kwargs: Additional search parameters
            
        Returns:
            ScrapingResult containing the scraped jobs and session info
        """
        # Start scraping session
        self.session = self.start_session(keywords, location)
        
        try:
            self.logger.logger.info(f"Starting job scrape for keywords: {keywords} in {location}")
            
            # Build search URL
            search_url = self.build_search_url(keywords, location, **kwargs)
            self.logger.logger.info(f"Search URL: {search_url}")
            
            # Simulate scraping process
            jobs = self._scrape_job_listings(keywords, location, **kwargs)
            
            # Update session with results
            self.session.jobs_found = len(jobs)
            self.session.jobs_processed = len(jobs)
            
            self.logger.logger.info(f"Successfully scraped {len(jobs)} jobs")
            
            # Get performance metrics
            performance_metrics = self.get_performance_metrics()
            
            return ScrapingResult(
                success=True,
                jobs=jobs,
                session=self.session,
                metadata={"keywords": keywords, "location": location, "search_url": search_url},
                performance_metrics=performance_metrics
            )
            
        except Exception as e:
            self.handle_error(e, "job scraping", search_url if 'search_url' in locals() else "")
            return ScrapingResult(
                success=False,
                jobs=[],
                session=self.session,
                error_message=str(e)
            )
        finally:
            self.finish_session()
    
    def get_job_details(self, job_url: str) -> Optional[JobListing]:
        """
        Get detailed information about a specific job.
        
        Args:
            job_url: URL of the job to get details for
            
        Returns:
            JobListing with detailed information, or None if failed
        """
        try:
            self.logger.logger.info(f"Getting details for job: {job_url}")
            
            # Apply rate limiting
            self.rate_limit()
            
            # Simulate job details extraction
            job_details = self._extract_job_details(job_url)
            
            if job_details:
                self.logger.logger.info(f"Successfully extracted details for job: {job_details.title}")
                return job_details
            else:
                self.logger.logger.warning(f"Failed to extract details for job: {job_url}")
                return None
                
        except Exception as e:
            self.handle_error(e, "job details extraction", job_url)
            return None
    
    def build_search_url(self, keywords: List[str], location: str, **kwargs) -> str:
        """
        Build the search URL for the example job site.
        
        Args:
            keywords: List of job keywords
            location: Location to search in
            **kwargs: Additional search parameters
            
        Returns:
            Complete search URL for the job site
        """
        # Simulate building a search URL
        keyword_param = "+".join(keywords)
        location_param = location.replace(" ", "+")
        
        url = f"{self.base_url}/search?keywords={keyword_param}&location={location_param}"
        
        # Add additional parameters
        if kwargs.get("experience_level"):
            url += f"&experience={kwargs['experience_level']}"
        
        if kwargs.get("job_type"):
            url += f"&type={kwargs['job_type']}"
        
        return url
    
    def extract_job_listings_from_page(self, page_content: Any) -> List[JobListing]:
        """
        Extract job listings from a search results page.
        
        Args:
            page_content: The page content (HTML, BeautifulSoup object, etc.)
            
        Returns:
            List of JobListing objects extracted from the page
        """
        # This is a simulation - in a real scraper, you would parse the actual page content
        jobs = []
        max_jobs = self.config.max_jobs_per_session
        
        # Simulate finding job listings
        for i in range(min(max_jobs, 5)):  # Simulate finding 5 jobs
            # Apply rate limiting
            self.rate_limit()
            
            # Create a sample job listing
            job = JobListing(
                title=f"Sample Developer Position {i+1}",
                company=f"Example Company {i+1}",
                location="Remote",
                job_url=f"{self.base_url}/jobs/{i+1}",
                job_site=self.config.site_name,
                description=f"This is a sample job description for developer position {i+1}.",
                salary_min=60000 + (i * 10000),
                salary_max=80000 + (i * 10000)
            )
            
            jobs.append(job)
            
            self.logger.logger.debug(f"Found job: {job.title} at {job.company}")
        
        return jobs
    
    def extract_job_details_from_page(self, page_content: Any, job_url: str) -> Optional[JobListing]:
        """
        Extract detailed job information from a job detail page.
        
        Args:
            page_content: The page content (HTML, BeautifulSoup object, etc.)
            job_url: URL of the job being processed
            
        Returns:
            JobListing with detailed information, or None if failed
        """
        try:
            # Simulate parsing job details
            job_id = job_url.split("/")[-1]
            
            return JobListing(
                title=f"Detailed Developer Position {job_id}",
                company="Example Company",
                location="Remote",
                job_url=job_url,
                job_site=self.config.site_name,
                description="This is a detailed job description with full requirements and responsibilities.",
                salary_min=70000,
                salary_max=90000,
                requirements=["Python", "JavaScript", "SQL"],
                responsibilities=["Develop web applications", "Collaborate with team", "Write clean code"],
                benefits=["Health insurance", "401k", "Remote work"]
            )
            
        except Exception as e:
            self.logger.logger.error(f"Error extracting job details: {e}")
            return None
    
    def _scrape_job_listings(self, keywords: List[str], location: str, **kwargs) -> List[JobListing]:
        """
        Scrape job listings from the search results.
        
        Args:
            keywords: Search keywords
            location: Search location
            **kwargs: Additional parameters
            
        Returns:
            List of JobListing objects
        """
        # Simulate page content (in real implementation, this would be actual HTML)
        page_content = f"<html>Search results for {keywords} in {location}</html>"
        
        # Use the abstract method to extract jobs
        return self.extract_job_listings_from_page(page_content)
    
    def _extract_job_details(self, job_url: str) -> Optional[JobListing]:
        """
        Extract detailed job information from a job page.
        
        Args:
            job_url: URL of the job page
            
        Returns:
            JobListing with detailed information, or None if failed
        """
        # Simulate page content (in real implementation, this would be actual HTML)
        page_content = f"<html>Job details for {job_url}</html>"
        
        # Use the abstract method to extract job details
        return self.extract_job_details_from_page(page_content, job_url)


def create_example_scraper() -> ExampleScraper:
    """
    Create an example scraper with default configuration.
    
    Returns:
        Configured ExampleScraper instance
    """
    config = ScrapingConfig(
        site_name="example",
        base_url="https://example-jobs.com",
        delay_min=1.0,
        delay_max=3.0,
        max_requests_per_minute=20,
        max_jobs_per_session=10,
        respect_robots_txt=True,
        use_random_delays=True,
        log_level="INFO"
    )
    
    return ExampleScraper(config) 