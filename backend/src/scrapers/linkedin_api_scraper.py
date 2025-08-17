#!/usr/bin/env python3
"""
LinkedIn API-Only Scraper

This module provides a fast, API-only approach for LinkedIn job searches
that don't require advanced filtering. It uses direct URL construction
and basic HTTP requests to extract job information without WebDriver overhead.

This scraper is optimized for:
- Basic searches (keywords + location)
- Fast execution (2-5 seconds)
- No browser automation
- Reduced resource usage
- Lower detection risk
"""

import time
import logging
import requests
from typing import List, Optional, Dict, Any
from urllib.parse import quote, urlencode
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re

try:
    from backend.src.scrapers.base_scraper import BaseScraper, ScrapingResult, ScrapingConfig
    from backend.src.data.models import JobListing
except ImportError:
    # Fallback for local development
    from .base_scraper import BaseScraper, ScrapingResult, ScrapingConfig
    from ..data.models import JobListing


class LinkedInAPIScraper(BaseScraper):
    """
    Fast API-only LinkedIn scraper for basic searches.
    
    This scraper provides rapid job search functionality for basic queries
    (keywords + location) without the overhead of WebDriver automation.
    It's designed for scenarios where advanced filtering is not required.
    """
    
    def __init__(self, config: ScrapingConfig):
        """Initialize the API-only LinkedIn scraper."""
        super().__init__(config)
        
        self.base_url = "https://www.linkedin.com"
        self.jobs_url = f"{self.base_url}/jobs"
        
        # Session for HTTP requests
        self.http_session = requests.Session()
        self.http_session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Rate limiting
        self.request_delay = 2.0
        self.last_request_time = 0
    
    def scrape_jobs(self, keywords: List[str], location: str, **kwargs) -> ScrapingResult:
        """
        Scrape jobs using API-only approach.
        
        Args:
            keywords: List of job keywords
            location: Location to search in
            **kwargs: Additional parameters (ignored for API-only approach)
            
        Returns:
            ScrapingResult with found jobs
        """
        try:
            self.logger.logger.info(f"Starting API-only LinkedIn search for: {keywords} in {location}")
            
            # Build search URL
            search_url = self.build_search_url(keywords, location, **kwargs)
            self.logger.logger.info(f"Search URL: {search_url}")
            
            # Perform the search
            jobs = self._perform_api_search(search_url, keywords, location)
            
            if jobs:
                self.logger.logger.info(f"Successfully found {len(jobs)} jobs via API")
                return ScrapingResult(
                    success=True,
                    jobs=jobs,
                    session=None,
                    error_message=None
                )
            else:
                self.logger.logger.warning("No jobs found via API search")
                return ScrapingResult(
                    success=False,
                    jobs=[],
                    session=None,
                    error_message="No jobs found"
                )
                
        except Exception as e:
            self.logger.logger.error(f"API-only search failed: {e}")
            return ScrapingResult(
                success=False,
                jobs=[],
                session=None,
                error_message=f"API search failed: {str(e)}"
            )
    
    def build_search_url(self, keywords: List[str], location: str, **kwargs) -> str:
        """
        Build LinkedIn search URL for API-only approach.
        
        Args:
            keywords: List of job keywords
            location: Location to search in
            **kwargs: Additional parameters including:
                - distance: Search radius in miles
                - experience_level: Experience level filter
                - job_type: Job type filter
                - work_arrangement: Remote/on-site/hybrid filter
                - date_posted: Date posted filter
            
        Returns:
            Complete search URL with proper LinkedIn parameters
        """
        # Base URL with trailing slash
        url = f"{self.jobs_url}/search/"
        
        # Build query parameters
        params = []
        
        # Keywords
        if keywords:
            keywords_str = ' '.join(keywords)
            # Use quote to properly encode spaces as %20
            params.append(f"keywords={quote(keywords_str)}")
        
        # Location
        if location:
            # Use quote to properly encode spaces as %20 and commas as %2C
            params.append(f"location={quote(location)}")
        
        # Distance (default to 25 miles if not specified)
        distance = kwargs.get('distance', '25')
        if distance and distance != 'exact':
            params.append(f"distance={distance}")
        
        # Experience Level (f_E parameter)
        experience_level = kwargs.get('experience_level')
        if experience_level:
            experience_mapping = {
                'entry': '1',
                'associate': '2', 
                'mid-senior': '3',
                'director': '4',
                'executive': '5'
            }
            exp_value = experience_mapping.get(experience_level.lower())
            if exp_value:
                params.append(f"f_E={exp_value}")
        
        # Job Type (f_JT parameter)
        job_type = kwargs.get('job_type')
        if job_type:
            job_type_mapping = {
                'full-time': 'F',
                'part-time': 'P',
                'contract': 'C',
                'temporary': 'T',
                'internship': 'I',
                'volunteer': 'V'
            }
            job_value = job_type_mapping.get(job_type.lower())
            if job_value:
                params.append(f"f_JT={job_value}")
        
        # Work Arrangement (f_WT parameter)
        work_arrangement = kwargs.get('work_arrangement')
        if work_arrangement and work_arrangement.lower() != 'any':
            work_mapping = {
                'on-site': '1',
                'remote': '2',
                'hybrid': '3'
            }
            work_value = work_mapping.get(work_arrangement.lower())
            if work_value:
                params.append(f"f_WT={work_value}")
        
        # Date Posted (f_TPR parameter)
        date_posted = kwargs.get('date_posted')
        if date_posted and date_posted.lower() != 'any':
            date_mapping = {
                'past_24_hours': 'r86400',
                'past_week': 'r604800',
                'past_month': 'r2592000'
            }
            date_value = date_mapping.get(date_posted.lower())
            if date_value:
                params.append(f"f_TPR={date_value}")
        
        # Add parameters to URL
        if params:
            url += '?' + '&'.join(params)
        
        return url
    
    def _perform_api_search(self, search_url: str, keywords: List[str], location: str) -> List[JobListing]:
        """
        Perform the actual API search and extract job listings.
        
        Args:
            search_url: URL to search
            keywords: Original keywords for context
            location: Original location for context
            
        Returns:
            List of JobListing objects
        """
        try:
            # Rate limiting
            self._respect_rate_limit()
            
            # Fetch the search page
            response = self.http_session.get(search_url, timeout=30)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract job listings
            jobs = self._extract_jobs_from_html(soup, search_url)
            
            # Limit results if specified
            max_jobs = getattr(self.config, 'max_jobs_per_search', 50)
            if len(jobs) > max_jobs:
                jobs = jobs[:max_jobs]
                self.logger.logger.info(f"Limited results to {max_jobs} jobs")
            
            return jobs
            
        except requests.RequestException as e:
            self.logger.logger.error(f"HTTP request failed: {e}")
            raise
        except Exception as e:
            self.logger.logger.error(f"Error parsing search results: {e}")
            raise
    
    def _extract_jobs_from_html(self, soup: BeautifulSoup, base_url: str) -> List[JobListing]:
        """
        Extract job listings from HTML content.
        
        Args:
            soup: BeautifulSoup object of the page
            base_url: Base URL for constructing job URLs
            
        Returns:
            List of JobListing objects
        """
        jobs = []
        
        # LinkedIn job card selectors (multiple patterns for robustness)
        job_selectors = [
            '[data-job-id]',
            '.job-search-card',
            '.job-card-container',
            '.job-card',
            '.artdeco-list__item',
            '[data-testid*="job-card"]'
        ]
        
        for selector in job_selectors:
            job_elements = soup.select(selector)
            if job_elements:
                self.logger.logger.info(f"Found {len(job_elements)} job elements with selector: {selector}")
                break
        
        if not job_elements:
            self.logger.logger.warning("No job elements found with any selector")
            return jobs
        
        for job_element in job_elements:
            try:
                job = self._extract_single_job(job_element, base_url)
                if job:
                    jobs.append(job)
            except Exception as e:
                self.logger.logger.warning(f"Error extracting job: {e}")
                continue
        
        return jobs
    
    def _extract_single_job(self, job_element, base_url: str) -> Optional[JobListing]:
        """
        Extract a single job from a job element.
        
        Args:
            job_element: BeautifulSoup element containing job data
            base_url: Base URL for constructing job URLs
            
        Returns:
            JobListing object or None if extraction fails
        """
        try:
            # Extract job title
            title = self._extract_text(job_element, [
                '.job-search-card__title',
                '.job-card__title',
                'h3',
                'h4',
                '[data-testid*="job-title"]'
            ])
            
            if not title:
                return None
            
            # Extract company name
            self.logger.logger.info(f"🏢 Extracting company name for job: '{title}'")
            company = self._extract_text(job_element, [
                '.job-search-card__subtitle',
                '.job-card__company-name',
                '.company-name',
                '[data-testid*="company-name"]',
                '.job-search-card__company-name',
                '.job-card__subtitle',
                'span[class*="company"]',
                'div[class*="company"]',
                'a[class*="company"]',
                '.job-search-card__company',
                '.job-card__company'
            ])
            
            # If standard extraction failed, try extracting from job URL
            if company is None:
                self.logger.logger.info("🔗 Trying to extract company from job URL...")
                linkedin_url = self._extract_job_url(job_element, base_url)
                company = self._extract_company_from_url(linkedin_url)
                if company:
                    self.logger.logger.info(f"✅ Extracted company from URL: '{company}' for job: '{title}'")
                else:
                    company = "Unknown"
                    self.logger.logger.warning(f"❌ Could not extract company name for job: '{title}' - setting to 'Unknown'")
            else:
                self.logger.logger.info(f"✅ Extracted company: '{company}' for job: '{title}'")
            
            # Extract location
            location = self._extract_text(job_element, [
                '.job-search-card__location',
                '.job-card__location',
                '.location',
                '[data-testid*="location"]'
            ])
            
            # Extract job URL
            linkedin_url = self._extract_job_url(job_element, base_url)
            
            # Extract job description (preview)
            description = self._extract_text(job_element, [
                '.job-search-card__description',
                '.job-card__description',
                '.description',
                '[data-testid*="description"]',
                '.job-search-card__snippet',
                '.job-card__snippet',
                'div[class*="description"]',
                'span[class*="description"]',
                '.job-search-card__job-description',
                '.job-card__job-description'
            ])
            
            # Debug logging
            self.logger.logger.info(f"Extracted description: '{description[:100] if description else 'None'}...' for job: '{title}'")
            
            # Extract posted date
            posted_date = self._extract_posted_date(job_element)
            
            # Extract job type and other metadata
            job_type = self._extract_job_type(job_element)
            experience_level = self._extract_experience_level(job_element)
            remote_type = self._extract_remote_type(job_element)
            
            # Create JobListing object
            job_listing = JobListing(
                title=title,
                company=company or "Unknown Company",
                location=location or "Unknown Location",
                description=description or "No description available",
                linkedin_url=linkedin_url,
                posted_date=posted_date,
                job_type=job_type,
                experience_level=experience_level,
                remote_type=remote_type,
                salary_min=None,
                salary_max=None,
                requirements=[],
                benefits=[]
            )
            
            return job_listing
            
        except Exception as e:
            self.logger.logger.warning(f"Error extracting job data: {e}")
            return None
    
    def _extract_text(self, element, selectors: List[str]) -> Optional[str]:
        """Extract text from element using multiple selectors."""
        self.logger.logger.info(f"🔍 Trying to extract text with selectors: {selectors}")
        
        for i, selector in enumerate(selectors):
            try:
                found_element = element.select_one(selector)
                if found_element:
                    # Try multiple text extraction methods
                    text = found_element.get_text(strip=True)
                    if text:
                        self.logger.logger.info(f"✅ Selector {i+1}/{len(selectors)} '{selector}' found text: '{text}'")
                        return text
                    else:
                        # Try alternative text extraction for elements with HTML comments
                        raw_text = str(found_element)
                        if '<!--' in raw_text and '-->' in raw_text:
                            # Extract text from HTML comments format like <!---->Company<!----> 
                            import re
                            # Remove HTML tags and comments
                            cleaned = re.sub(r'<[^>]*>', '', raw_text)
                            cleaned = re.sub(r'<!--.*?-->', '', cleaned)
                            cleaned = cleaned.strip()
                            if cleaned:
                                self.logger.logger.info(f"✅ Selector {i+1}/{len(selectors)} '{selector}' found text via HTML parsing: '{cleaned}'")
                                return cleaned
                        
                        self.logger.logger.info(f"❌ Selector {i+1}/{len(selectors)} '{selector}' found element but no text")
                else:
                    self.logger.logger.info(f"❌ Selector {i+1}/{len(selectors)} '{selector}' found no element")
            except Exception as e:
                self.logger.logger.info(f"❌ Selector {i+1}/{len(selectors)} '{selector}' failed: {e}")
                continue
        
        # Enhanced debug: Log the HTML structure if no text found
        self.logger.logger.info(f"🔍 NO TEXT FOUND with any selector. Element HTML structure:")
        self.logger.logger.info(f"Element HTML: {element.prettify()[:1000]}...")
        
        return None
    
    def _extract_company_from_url(self, url: str) -> Optional[str]:
        """
        Extract company name from LinkedIn job URL.
        
        LinkedIn URLs often follow the pattern:
        /jobs/view/job-title-at-COMPANY-jobid
        
        Args:
            url: LinkedIn job URL
            
        Returns:
            Company name or None if not found
        """
        if not url:
            return None
            
        try:
            import re
            
            # Pattern for LinkedIn job URLs: /jobs/view/job-title-at-COMPANY-jobid
            pattern = r'/jobs/view/[^/]+-at-([^-]+)-\d+' 
            match = re.search(pattern, url)
            
            if match:
                company = match.group(1)
                # Clean up company name
                company = company.replace('-', ' ').title()
                self.logger.logger.info(f"🎯 Extracted company from URL pattern: '{company}'")
                return company
            
            # Alternative pattern: look for company parameter
            pattern2 = r'[?&]company=([^&]+)'
            match2 = re.search(pattern2, url)
            if match2:
                company = match2.group(1)
                company = company.replace('%20', ' ').replace('+', ' ')
                self.logger.logger.info(f"🎯 Extracted company from URL parameter: '{company}'")
                return company
                
            self.logger.logger.info(f"❌ No company pattern found in URL: {url[:100]}...")
            return None
            
        except Exception as e:
            self.logger.logger.info(f"❌ Error extracting company from URL: {e}")
            return None
    
    def _extract_job_url(self, element, base_url: str) -> str:
        """Extract job URL from element."""
        # Try to find a link
        link_selectors = [
            'a[href*="/jobs/view"]',
            'a[href*="/jobs/"]',
            'a[data-job-id]',
            'a'
        ]
        
        for selector in link_selectors:
            try:
                link = element.select_one(selector)
                if link and link.get('href'):
                    href = link.get('href')
                    if href.startswith('/'):
                        return f"{self.base_url}{href}"
                    elif href.startswith('http'):
                        return href
                    else:
                        return f"{base_url}{href}"
            except Exception:
                continue
        
        # Fallback: construct URL from job ID
        job_id = element.get('data-job-id')
        if job_id:
            return f"{self.base_url}/jobs/view/{job_id}"
        
        return f"{self.base_url}/jobs"
    
    def _extract_posted_date(self, element) -> Optional[datetime]:
        """Extract posted date from job element."""
        date_selectors = [
            '.job-search-card__listdate',
            '.job-card__listdate',
            '.posted-date',
            '[data-testid*="posted-date"]'
        ]
        
        date_text = self._extract_text(element, date_selectors)
        if not date_text:
            return None
        
        # Parse common date formats
        try:
            # Handle "X days ago", "X hours ago", etc.
            if 'ago' in date_text.lower():
                return self._parse_relative_date(date_text)
            
            # Handle specific date formats
            date_formats = [
                '%Y-%m-%d',
                '%m/%d/%Y',
                '%B %d, %Y',
                '%d %B %Y'
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(date_text, fmt)
                except ValueError:
                    continue
            
            # If no format matches, return current date
            return datetime.now()
            
        except Exception:
            return datetime.now()
    
    def _parse_relative_date(self, date_text: str) -> datetime:
        """Parse relative date strings like '2 days ago'."""
        date_text = date_text.lower().strip()
        
        # Extract number and unit
        import re
        match = re.search(r'(\d+)\s+(day|hour|minute|week|month)s?\s+ago', date_text)
        
        if match:
            number = int(match.group(1))
            unit = match.group(2)
            
            now = datetime.now()
            
            if unit == 'day':
                return now - timedelta(days=number)
            elif unit == 'hour':
                return now - timedelta(hours=number)
            elif unit == 'minute':
                return now - timedelta(minutes=number)
            elif unit == 'week':
                return now - timedelta(weeks=number)
            elif unit == 'month':
                return now - timedelta(days=number * 30)
        
        return datetime.now()
    
    def _extract_job_type(self, element) -> Optional[str]:
        """Extract job type from element."""
        type_selectors = [
            '.job-search-card__job-type',
            '.job-card__job-type',
            '.job-type',
            '[data-testid*="job-type"]'
        ]
        
        type_text = self._extract_text(element, type_selectors)
        if not type_text:
            return None
        
        # Normalize job type
        type_text = type_text.lower()
        if 'full-time' in type_text or 'full time' in type_text:
            return 'Full-time'
        elif 'part-time' in type_text or 'part time' in type_text:
            return 'Part-time'
        elif 'contract' in type_text:
            return 'Contract'
        elif 'internship' in type_text:
            return 'Internship'
        else:
            return type_text.title()
    
    def _extract_experience_level(self, element) -> Optional[str]:
        """Extract experience level from element."""
        level_selectors = [
            '.job-search-card__experience-level',
            '.job-card__experience-level',
            '.experience-level',
            '[data-testid*="experience-level"]'
        ]
        
        level_text = self._extract_text(element, level_selectors)
        if not level_text:
            return None
        
        # Normalize experience level
        level_text = level_text.lower()
        if 'entry' in level_text or 'junior' in level_text:
            return 'Entry level'
        elif 'senior' in level_text:
            return 'Senior level'
        elif 'mid' in level_text or 'intermediate' in level_text:
            return 'Mid level'
        elif 'executive' in level_text or 'lead' in level_text:
            return 'Executive level'
        else:
            return level_text.title()
    
    def _extract_remote_type(self, element) -> Optional[str]:
        """Extract remote work type from element."""
        remote_selectors = [
            '.job-search-card__remote-type',
            '.job-card__remote-type',
            '.remote-type',
            '[data-testid*="remote-type"]'
        ]
        
        remote_text = self._extract_text(element, remote_selectors)
        if not remote_text:
            return None
        
        # Normalize remote type
        remote_text = remote_text.lower()
        if 'remote' in remote_text:
            return 'Remote'
        elif 'hybrid' in remote_text:
            return 'Hybrid'
        elif 'on-site' in remote_text or 'onsite' in remote_text:
            return 'On-site'
        else:
            return remote_text.title()
    
    def _respect_rate_limit(self):
        """Ensure we don't exceed rate limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get_job_details(self, job_url: str) -> Optional[JobListing]:
        """
        Get detailed job information (not supported in API-only mode).
        
        Args:
            job_url: URL of the job
            
        Returns:
            None (not supported in API-only mode)
        """
        self.logger.logger.warning("Detailed job extraction not supported in API-only mode")
        return None
    
    def extract_job_listings_from_page(self, page_content: Any) -> List[JobListing]:
        """
        Extract job listings from page content.
        
        Args:
            page_content: Page content (BeautifulSoup object)
            
        Returns:
            List of JobListing objects
        """
        if isinstance(page_content, BeautifulSoup):
            return self._extract_jobs_from_html(page_content, self.jobs_url)
        else:
            self.logger.logger.warning("Invalid page content type for API-only scraper")
            return []
    
    def extract_job_details_from_page(self, page_content: Any, job_url: str) -> Optional[JobListing]:
        """
        Extract detailed job information from page content.
        
        Args:
            page_content: Page content (BeautifulSoup object)
            job_url: URL of the job
            
        Returns:
            JobListing object or None if extraction fails
        """
        try:
            if isinstance(page_content, BeautifulSoup):
                # For API-only mode, we'll extract basic details from the page
                # This is a simplified version since we don't have full page access
                job_listings = self._extract_jobs_from_html(page_content, job_url)
                if job_listings:
                    return job_listings[0]  # Return the first job found
                else:
                    self.logger.logger.warning(f"No job details found for URL: {job_url}")
                    return None
            else:
                self.logger.logger.warning("Invalid page content type for API-only scraper")
                return None
        except Exception as e:
            self.logger.logger.error(f"Error extracting job details from page: {e}")
            return None


def create_linkedin_api_scraper(config: ScrapingConfig) -> LinkedInAPIScraper:
    """
    Create an API-only LinkedIn scraper instance.
    
    Args:
        config: Scraping configuration
        
    Returns:
        LinkedInAPIScraper instance
    """
    return LinkedInAPIScraper(config) 