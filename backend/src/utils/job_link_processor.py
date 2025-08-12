"""
Job link processor for the AI Job Qualification Screening System.

This module provides functionality to process user-provided job links
and extract job information from various job sites, including search pages.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, parse_qs
from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup
import time
import json

from ..data.models import JobListing

logger = logging.getLogger(__name__)


@dataclass
class JobLinkInfo:
    """Information extracted from a job link."""
    
    url: str
    job_site: str
    job_id: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    error: Optional[str] = None


class JobLinkProcessor:
    """
    Processor for handling user-provided job links.
    
    This class can extract job information from various job sites
    and prepare it for AI qualification analysis.
    Supports both individual job pages and search result pages.
    """
    
    # Supported job sites and their URL patterns
    SUPPORTED_SITES = {
        'linkedin': {
            'patterns': [
                r'linkedin\.com/jobs/view/',
                r'linkedin\.com/jobs/collections/',
                r'linkedin\.com/jobs/search/'
            ],
            'extractors': {
                'job_id': r'/jobs/view/([^/?]+)',
                'title': r'<title[^>]*>([^<]+)</title>',
                'company': r'<span[^>]*class="[^"]*company[^"]*"[^>]*>([^<]+)</span>',
            }
        },
        'indeed': {
            'patterns': [
                r'indeed\.com/viewjob\?',
                r'indeed\.com/jobs/',
                r'indeed\.com/company/'
            ],
            'extractors': {
                'job_id': r'jk=([^&]+)',
                'title': r'<title[^>]*>([^<]+)</title>',
                'company': r'<span[^>]*class="[^"]*company[^"]*"[^>]*>([^<]+)</span>',
            }
        },
        'glassdoor': {
            'patterns': [
                r'glassdoor\.com/Job/',
                r'glassdoor\.com/job-listing/'
            ],
            'extractors': {
                'job_id': r'/Job/([^/?]+)',
                'title': r'<title[^>]*>([^<]+)</title>',
                'company': r'<span[^>]*class="[^"]*company[^"]*"[^>]*>([^<]+)</span>',
            }
        },
        'monster': {
            'patterns': [
                r'monster\.com/job/',
                r'monster\.com/jobs/'
            ],
            'extractors': {
                'job_id': r'/job/([^/?]+)',
                'title': r'<title[^>]*>([^<]+)</title>',
                'company': r'<span[^>]*class="[^"]*company[^"]*"[^>]*>([^<]+)</span>',
            }
        }
    }
    
    def __init__(self, user_agent: str = None, timeout: int = 30):
        """
        Initialize the job link processor.
        
        Args:
            user_agent: Custom user agent string
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        
        # Set up headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': user_agent or 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def process_job_links(self, links: List[str]) -> List[JobLinkInfo]:
        """
        Process a list of job links and extract job information.
        
        Args:
            links: List of job URLs to process
            
        Returns:
            List of JobLinkInfo objects with extracted information
        """
        job_links = []
        
        for i, link in enumerate(links, 1):
            logger.info(f"Processing job link {i}/{len(links)}: {link}")
            
            # Clean the URL
            cleaned_url = self._clean_url(link)
            if not cleaned_url:
                logger.warning(f"Invalid URL: {link}")
                job_links.append(JobLinkInfo(url=link, job_site="unknown", error="Invalid URL"))
                continue
            
            # Identify the job site
            job_site = self._identify_job_site(cleaned_url)
            if not job_site:
                logger.warning(f"Unsupported job site: {cleaned_url}")
                job_links.append(JobLinkInfo(url=cleaned_url, job_site="unknown", error="Unsupported job site"))
                continue
            
            # Check if this is a search page
            if self._is_search_page(cleaned_url, job_site):
                logger.info(f"Detected search page for {job_site}, extracting multiple jobs")
                search_jobs = self._extract_jobs_from_search(cleaned_url, job_site)
                job_links.extend(search_jobs)
            else:
                # Extract from individual job page
                job_info = self._extract_job_info(cleaned_url, job_site)
                job_links.append(job_info)
            
            # Add delay between requests to be respectful
            if i < len(links):
                time.sleep(1)
        
        return job_links
    
    def _is_search_page(self, url: str, job_site: str) -> bool:
        """Check if the URL is a search page."""
        if job_site == 'linkedin':
            return 'jobs/search' in url
        elif job_site == 'indeed':
            return 'jobs?' in url and 'jk=' not in url
        elif job_site == 'glassdoor':
            return 'Job/' in url and 'jobs' in url
        return False
    
    def _extract_jobs_from_search(self, url: str, job_site: str) -> List[JobLinkInfo]:
        """Extract multiple jobs from a search page."""
        try:
            if job_site == 'linkedin':
                return self._extract_linkedin_search_jobs(url)
            elif job_site == 'indeed':
                return self._extract_indeed_search_jobs(url)
            else:
                logger.warning(f"Search page extraction not implemented for {job_site}")
                return []
        except Exception as e:
            logger.error(f"Error extracting jobs from search page {url}: {e}")
            return [JobLinkInfo(url=url, job_site=job_site, error=f"Search extraction failed: {str(e)}")]
    
    def _extract_linkedin_search_jobs(self, url: str) -> List[JobLinkInfo]:
        """Extract jobs from LinkedIn search page."""
        try:
            # Fetch the search page
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            job_links = []
            
            # Look for job cards in the search results
            # LinkedIn uses various selectors for job cards
            job_card_selectors = [
                'div[data-job-id]',  # Job cards with data-job-id attribute
                'li[data-job-id]',   # Job cards in list format
                '.job-search-card',   # Common class for job cards
                '.job-card-container', # Another common class
                '[data-testid*="job-card"]', # Test IDs
                '.artdeco-list__item', # List items that might contain jobs
                '.job-card-list__item', # LinkedIn specific job card items
                '.job-card-list__item--active', # Active job cards
                '.job-card-list__item--inactive' # Inactive job cards
            ]
            
            job_cards = []
            for selector in job_card_selectors:
                job_cards = soup.select(selector)
                if job_cards:
                    logger.info(f"Found {len(job_cards)} job cards with selector: {selector}")
                    break
            
            if not job_cards:
                # Try to find any elements that might contain job information
                logger.info("No job cards found with standard selectors, trying alternative approach")
                job_cards = soup.find_all(['div', 'li'], class_=re.compile(r'job|position|listing', re.I))
            
            logger.info(f"Processing {len(job_cards)} job cards")
            
            for card in job_cards[:10]:  # Limit to first 10 jobs to avoid overwhelming
                try:
                    job_info = self._extract_job_from_linkedin_card(card, url)
                    if job_info and job_info.title:  # Only add if we got meaningful data
                        job_links.append(job_info)
                        logger.debug(f"Successfully extracted job: {job_info.title}")
                except Exception as e:
                    logger.debug(f"Error extracting job from card: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(job_links)} jobs from LinkedIn search")
            return job_links
            
        except Exception as e:
            logger.error(f"Error extracting LinkedIn search jobs: {e}")
            return [JobLinkInfo(url=url, job_site='linkedin', error=f"LinkedIn search extraction failed: {str(e)}")]
    
    def _extract_job_from_linkedin_card(self, card, base_url: str) -> Optional[JobLinkInfo]:
        """Extract job information from a LinkedIn job card."""
        try:
            # Extract job ID - try multiple approaches
            job_id = None
            
            # Method 1: Look for data attributes
            job_id_attrs = ['data-job-id', 'data-entity-urn', 'data-job-urn', 'data-urn']
            for attr in job_id_attrs:
                job_id = card.get(attr)
                if job_id:
                    # Clean up the job ID if it's a URN
                    if job_id.startswith('urn:li:jobPosting:'):
                        job_id = job_id.replace('urn:li:jobPosting:', '')
                    break
            
            # Method 2: Extract from href attributes
            if not job_id:
                links = card.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    # Try different LinkedIn job URL patterns
                    patterns = [
                        r'/jobs/view/([^/?]+)',  # Standard format
                        r'/jobs/view/urn:li:jobPosting:([^/?]+)',  # URN format
                        r'/jobs/view/([0-9]+)',  # Numeric ID
                        r'jobPosting:([^/?]+)',  # URN in URL
                        r'jobs/view/([^/?]+)'  # Without leading slash
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, href)
                        if match:
                            job_id = match.group(1)
                            break
                    
                    if job_id:
                        break
            
            # Method 3: Look for job ID in any attribute or text
            if not job_id:
                # Search for any numeric ID that might be a job ID
                all_attrs = card.attrs
                for attr_name, attr_value in all_attrs.items():
                    if isinstance(attr_value, str) and 'job' in attr_name.lower():
                        # Look for numeric patterns
                        numbers = re.findall(r'\d{8,}', attr_value)  # 8+ digit numbers
                        if numbers:
                            job_id = numbers[0]
                            break
            
            # Extract title - try multiple approaches
            title = None
            
            # Method 1: Look for title in heading elements with updated LinkedIn selectors
            # For search page cards, we need to be more specific about job titles vs company names
            title_selectors = [
                # Job card selectors (search results) - these should be job titles
                '.job-card-list__title',
                '.job-card-list__title a',
                '.job-card-list__title span',
                'a[data-testid*="job-title"]',
                'a[class*="job-title"]',
                'span[class*="job-title"]',
                '[data-testid*="job-title"]',
                # Look for links that contain job titles (not company names)
                'a[href*="/jobs/view/"]',  # Links to job pages
                'a[href*="jobPosting"]',   # Job posting links
                # Fallback selectors
                'h3 a', 'h2 a', 'h4 a',  # Title in heading with link
                'h3', 'h2', 'h4',        # Title in heading without link
            ]
            
            for selector in title_selectors:
                title_elem = card.select_one(selector)
                if title_elem:
                    potential_title = title_elem.get_text(strip=True)
                    if potential_title and len(potential_title) > 3 and not potential_title.lower().startswith('linkedin'):
                        # Additional validation: job titles are usually longer and more descriptive
                        if len(potential_title.split()) >= 2:  # At least 2 words
                            title = potential_title
                            break
            
            # Method 2: Look for any link that might contain the job title
            if not title:
                links = card.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    if '/jobs/view/' in href:
                        link_text = link.get_text(strip=True)
                        if link_text and len(link_text) > 3 and not link_text.lower().startswith('linkedin'):
                            # Additional validation for job titles
                            if len(link_text.split()) >= 2:  # At least 2 words
                                title = link_text
                                break
            
            # Extract company - be more specific about company selectors
            company = None
            company_selectors = [
                # LinkedIn specific company selectors
                '.job-card-container__company-name',
                '.job-card-list__company-name',
                '.job-card-list__subtitle',  # Often contains company
                '.job-card-container__subtitle',  # Often contains company
                # Look for company links (not job links)
                'a[href*="/company/"]',  # Company profile links
                'a[href*="company"]',    # Any company-related links
                # Generic company selectors
                'a[class*="company"]',
                'span[class*="company"]',
                '[data-testid*="company"]',
                '[data-testid*="company-name"]',
                '.job-card-list__company'
            ]
            
            for selector in company_selectors:
                company_elem = card.select_one(selector)
                if company_elem:
                    potential_company = company_elem.get_text(strip=True)
                    if potential_company and len(potential_company) > 2 and not potential_company.lower().startswith('linkedin'):
                        # Additional validation: company names are usually shorter and single words/phrases
                        if len(potential_company.split()) <= 3:  # Usually 1-3 words
                            company = potential_company
                            break
            
            # Extract location
            location = None
            location_selectors = [
                'span[class*="location"]',  # Location span
                '[data-testid*="location"]',  # Test ID for location
                '.job-card-container__metadata-item',  # LinkedIn metadata
                '.job-card-container__location',  # LinkedIn specific
                '.job-card-list__location',  # LinkedIn specific
                '[data-testid*="location"]',  # Test ID for location
                '.job-card-list__metadata-item'  # Metadata items
            ]
            
            for selector in location_selectors:
                location_elem = card.select_one(selector)
                if location_elem:
                    location = location_elem.get_text(strip=True)
                    if location and len(location) > 2:
                        break
            
            # Extract description/snippet
            description = None
            description_selectors = [
                'p[class*="description"]',  # Description paragraph
                'span[class*="description"]',  # Description span
                '[data-testid*="description"]',  # Test ID for description
                '.job-card-container__description',  # LinkedIn specific
                '.job-card-container__snippet',  # Job snippet
                '.job-card-list__description',  # LinkedIn specific
                '.job-card-list__snippet',  # LinkedIn snippet
                '[data-testid*="job-snippet"]',  # Test ID for job snippet
                '.job-card-list__metadata-item'  # Metadata items might contain description
            ]
            
            for selector in description_selectors:
                desc_elem = card.select_one(selector)
                if desc_elem:
                    description = desc_elem.get_text(strip=True)
                    if description and len(description) > 20:
                        break
            
            # If no description found, try to get any text content from the card
            if not description:
                # Get all text content and use as description
                all_text = card.get_text(strip=True)
                if all_text and len(all_text) > 50:
                    # Remove title and company if they're in the text
                    if title and title in all_text:
                        all_text = all_text.replace(title, '').strip()
                    if company and company in all_text:
                        all_text = all_text.replace(company, '').strip()
                    description = all_text[:500]  # Limit to 500 characters
            
            # Construct job URL - try multiple approaches
            linkedin_url = None
            
            # Method 1: Use job ID to construct URL
            if job_id:
                linkedin_url = f"https://www.linkedin.com/jobs/view/{job_id}"
            
            # Method 2: Look for direct job links in the card
            if not linkedin_url:
                links = card.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    if '/jobs/view/' in href:
                        # Make sure it's a complete URL
                        if href.startswith('http'):
                            linkedin_url = href
                        elif href.startswith('/'):
                            linkedin_url = f"https://www.linkedin.com{href}"
                        else:
                            linkedin_url = f"https://www.linkedin.com/{href}"
                        break
            
            # Method 3: Fallback to base URL if no job-specific URL found
            if not linkedin_url:
                linkedin_url = base_url
            
            # Debug logging
            logger.debug(f"Extracted job URL: {linkedin_url} (job_id: {job_id}, title: {title})")
            
            # Validation: Ensure title and company are not the same
            if title and company and title.lower() == company.lower():
                # If they're the same, it's likely we extracted the same element twice
                # Try to find a different company
                for selector in company_selectors:
                    company_elem = card.select_one(selector)
                    if company_elem and company_elem.get_text(strip=True) != title:
                        potential_company = company_elem.get_text(strip=True)
                        if potential_company and len(potential_company) > 2 and len(potential_company.split()) <= 3:
                            company = potential_company
                            break
            
            # Only return if we have at least a title
            if not title:
                return None
            
            return JobLinkInfo(
                url=linkedin_url,
                job_site='linkedin',
                job_id=job_id,
                title=title,
                company=company,
                location=location,
                description=description
            )
            
        except Exception as e:
            logger.debug(f"Error extracting job from LinkedIn card: {e}")
            return None
    
    def _extract_indeed_search_jobs(self, url: str) -> List[JobLinkInfo]:
        """Extract jobs from Indeed search page."""
        # Similar implementation for Indeed
        # This would need Indeed-specific selectors
        logger.info("Indeed search extraction not yet implemented")
        return []
    
    def _clean_url(self, url: str) -> Optional[str]:
        """Clean and validate a URL."""
        try:
            # Remove whitespace
            url = url.strip()
            
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Validate URL format
            parsed = urlparse(url)
            if not parsed.netloc:
                return None
            
            return url
            
        except Exception as e:
            logger.error(f"Error cleaning URL {url}: {e}")
            return None
    
    def _identify_job_site(self, url: str) -> Optional[str]:
        """Identify the job site from the URL."""
        for site_name, site_config in self.SUPPORTED_SITES.items():
            for pattern in site_config['patterns']:
                if re.search(pattern, url, re.IGNORECASE):
                    return site_name
        return None
    
    def _extract_job_info(self, url: str, job_site: str) -> JobLinkInfo:
        """Extract job information from a URL."""
        try:
            # Fetch the page content
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract information based on the job site
            job_info = JobLinkInfo(url=url, job_site=job_site)
            
            # Extract job ID
            job_id = self._extract_job_id(url, job_site)
            if job_id:
                job_info.job_id = job_id
            
            # Extract title
            title = self._extract_title(soup, job_site)
            if title:
                job_info.title = title
            
            # Extract company
            company = self._extract_company(soup, job_site)
            if company:
                job_info.company = company
            
            # Extract location
            location = self._extract_location(soup, job_site)
            if location:
                job_info.location = location
            
            # Extract description
            description = self._extract_description(soup, job_site)
            if description:
                job_info.description = description
            
            return job_info
            
        except requests.RequestException as e:
            logger.error(f"Request error for {url}: {e}")
            return JobLinkInfo(url=url, job_site=job_site, error=f"Request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Error extracting job info from {url}: {e}")
            return JobLinkInfo(url=url, job_site=job_site, error=str(e))
    
    def _extract_job_id(self, url: str, job_site: str) -> Optional[str]:
        """Extract job ID from URL."""
        if job_site in self.SUPPORTED_SITES:
            extractors = self.SUPPORTED_SITES[job_site]['extractors']
            if 'job_id' in extractors:
                match = re.search(extractors['job_id'], url)
                if match:
                    return match.group(1)
        return None
    
    def _extract_title(self, soup: BeautifulSoup, job_site: str) -> Optional[str]:
        """Extract job title from HTML."""
        # LinkedIn-specific selectors
        if job_site == 'linkedin':
            title_selectors = [
                # Primary LinkedIn selectors (right panel)
                'h1.t-24.job-details-jobs-unified-top-card__job-title',
                '.t-24.job-details-jobs-unified-top-card__job-title',
                'h1[class*="job-details-jobs-unified-top-card__job-title"]',
                '.job-details-jobs-unified-top-card__job-title',
                # Job card selectors (search results)
                '.job-card-list__title',
                '.job-card-list__title a',
                '.job-card-list__title span',
                'a[data-testid*="job-title"]',
                'a[class*="job-title"]',
                'span[class*="job-title"]',
                '[data-testid*="job-title"]',
                # Fallback selectors
                'h1[class*="title"]',
                'h1[class*="job-title"]',
                'h1[class*="position"]',
                'h1',
                'title'
            ]
        else:
            # Generic selectors for other sites
            title_selectors = [
                'h1[class*="title"]',
                'h1[class*="job-title"]',
                'h1[class*="position"]',
                'h1',
                'title'
            ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title and len(title) > 5:  # Basic validation
                    return title
        
        return None
    
    def _extract_company(self, soup: BeautifulSoup, job_site: str) -> Optional[str]:
        """Extract company name from HTML."""
        # LinkedIn-specific selectors
        if job_site == 'linkedin':
            company_selectors = [
                # Primary LinkedIn selectors (right panel)
                '.job-details-jobs-unified-top-card__company-name .sRnCkbnFXZXqjWAFekZQCfsMNMELMevApSMNluw',
                '.job-details-jobs-unified-top-card__company-name div[class*="sRnCkbnFXZXqjWAFekZQCfsMNMELMevApSMNluw"]',
                '.job-details-jobs-unified-top-card__company-name a',
                '.job-details-jobs-unified-top-card__company-name span',
                '.job-details-jobs-unified-top-card__company-name',
                # Job card selectors (search results)
                '.job-card-list__company-name',
                '.job-card-list__subtitle',
                '.job-card-container__company-name',
                '.job-card-container__subtitle',
                'a[class*="company"]',
                'span[class*="company"]',
                '[data-testid*="company"]',
                '[data-testid*="company-name"]',
                '.job-card-list__company',
                # Fallback selectors
                '[class*="company"]',
                '[class*="employer"]',
                '[class*="organization"]',
                'a[href*="company"]'
            ]
        else:
            # Generic selectors for other sites
            company_selectors = [
                '[class*="company"]',
                '[class*="employer"]',
                '[class*="organization"]',
                'a[href*="company"]',
                'span[class*="company"]'
            ]
        
        for selector in company_selectors:
            element = soup.select_one(selector)
            if element:
                company = element.get_text(strip=True)
                if company and len(company) > 2:  # Basic validation
                    return company
        
        return None
    
    def _extract_location(self, soup: BeautifulSoup, job_site: str) -> Optional[str]:
        """Extract job location from HTML."""
        # Try multiple selectors for location
        location_selectors = [
            '[class*="location"]',
            '[class*="address"]',
            '[class*="city"]',
            'span[class*="location"]',
            'div[class*="location"]'
        ]
        
        for selector in location_selectors:
            element = soup.select_one(selector)
            if element:
                location = element.get_text(strip=True)
                if location and len(location) > 3:  # Basic validation
                    return location
        
        return None
    
    def _extract_description(self, soup: BeautifulSoup, job_site: str) -> Optional[str]:
        """Extract job description from HTML."""
        # Try multiple selectors for job description
        description_selectors = [
            '[class*="description"]',
            '[class*="details"]',
            '[class*="content"]',
            'div[class*="job-description"]',
            'section[class*="description"]',
            'article'
        ]
        
        for selector in description_selectors:
            elements = soup.select(selector)
            for element in elements:
                description = element.get_text(strip=True)
                if description and len(description) > 100:  # Basic validation
                    return description
        
        return None
    
    def create_job_listings(self, job_links: List[JobLinkInfo]) -> List[JobListing]:
        """
        Convert JobLinkInfo objects to JobListing objects.
        
        Args:
            job_links: List of JobLinkInfo objects
            
        Returns:
            List of JobListing objects
        """
        job_listings = []
        
        for job_link in job_links:
            if job_link.error:
                logger.warning(f"Skipping job link with error: {job_link.error}")
                continue
            
            job_listing = JobListing(
                id=job_link.job_id or f"job-{len(job_listings)}",  # Use job_id or generate one
                title=job_link.title or "Unknown Title",
                company=job_link.company or "Unknown Company",
                location=job_link.location or "Unknown Location",
                linkedin_url=job_link.url,
                job_site=job_link.job_site,
                description=job_link.description or "",
                notes=f"Extracted from user-provided link"
            )
            
            job_listings.append(job_listing)
        
        return job_listings
    
    def validate_job_links(self, links: List[str]) -> Dict[str, List[str]]:
        """
        Validate a list of job links and categorize them.
        
        Args:
            links: List of job URLs to validate
            
        Returns:
            Dictionary with 'valid', 'invalid', and 'unsupported' categories
        """
        results = {
            'valid': [],
            'invalid': [],
            'unsupported': []
        }
        
        for link in links:
            try:
                cleaned_url = self._clean_url(link)
                if not cleaned_url:
                    results['invalid'].append(link)
                    continue
                
                job_site = self._identify_job_site(cleaned_url)
                if not job_site:
                    results['unsupported'].append(cleaned_url)
                else:
                    results['valid'].append(cleaned_url)
                    
            except Exception as e:
                logger.error(f"Error validating link {link}: {e}")
                results['invalid'].append(link)
        
        return results 

    def extract_application_url(self, job_description: str) -> Optional[str]:
        """
        Extract job application URL from job description.
        
        Args:
            job_description: Job description text
            
        Returns:
            Application URL if found, None otherwise
        """
        if not job_description:
            return None
        
        # Common patterns for application URLs
        patterns = [
            r'https?://[^\s<>"]*apply[^\s<>"]*',
            r'https?://[^\s<>"]*application[^\s<>"]*',
            r'https?://[^\s<>"]*careers[^\s<>"]*',
            r'https?://[^\s<>"]*jobs[^\s<>"]*',
            r'https?://[^\s<>"]*workday[^\s<>"]*',
            r'https?://[^\s<>"]*greenhouse[^\s<>"]*',
            r'https?://[^\s<>"]*lever[^\s<>"]*',
            r'https?://[^\s<>"]*bamboohr[^\s<>"]*',
            r'https?://[^\s<>"]*icims[^\s<>"]*',
            r'https?://[^\s<>"]*jobvite[^\s<>"]*'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, job_description, re.IGNORECASE)
            if matches:
                # Return the first match, cleaned up
                url = matches[0].strip()
                # Remove trailing punctuation
                url = re.sub(r'[.,;!?]+$', '', url)
                return url
        
        return None 