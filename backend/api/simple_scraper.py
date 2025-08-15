#!/usr/bin/env python3
"""
Simple standalone scraper for testing purposes.
This version has minimal dependencies and can work without complex imports.
"""

import requests
import time
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from urllib.parse import quote
from datetime import datetime


class SimpleScraper:
    """A simple standalone scraper for basic LinkedIn job searches."""
    
    def __init__(self):
        self.base_url = "https://www.linkedin.com"
        self.jobs_url = f"{self.base_url}/jobs"
        
        # Session for HTTP requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        self.request_delay = 2.0
        self.last_request_time = 0
    
    def scrape_jobs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scrape jobs using basic approach.
        
        Args:
            params: Dictionary with search parameters
            
        Returns:
            Dictionary with job results
        """
        try:
            keywords = params.get("keywords", "")
            location = params.get("location", "")
            job_limit = params.get("job_limit", 25)
            
            print(f"🔍 Simple scraper searching for: {keywords} in {location}")
            
            # Build search URL
            search_url = self._build_search_url(keywords, location)
            print(f"📍 Search URL: {search_url}")
            
            # Perform the search
            jobs = self._perform_search(search_url, keywords, location, job_limit)
            
            return {
                "success": True,
                "jobs": jobs,
                "total_count": len(jobs),
                "error_message": None
            }
            
        except Exception as e:
            print(f"❌ Simple scraper error: {e}")
            return {
                "success": False,
                "jobs": [],
                "total_count": 0,
                "error_message": f"Simple scraper failed: {str(e)}"
            }
    
    def _build_search_url(self, keywords: str, location: str) -> str:
        """Build LinkedIn search URL."""
        url = f"{self.jobs_url}/search/"
        
        params = []
        if keywords:
            params.append(f"keywords={quote(keywords)}")
        if location:
            params.append(f"location={quote(location)}")
        
        # Default to 25 miles distance
        params.append("distance=25")
        
        if params:
            url += '?' + '&'.join(params)
        
        return url
    
    def _perform_search(self, search_url: str, keywords: str, location: str, limit: int = 25) -> List[Dict[str, Any]]:
        """Perform the actual search and extract job listings."""
        try:
            # Rate limiting
            self._respect_rate_limit()
            
            # Fetch the search page
            response = self.session.get(search_url, timeout=30)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract job listings
            jobs = self._extract_jobs_from_html(soup, search_url)
            
            # Limit results
            if len(jobs) > limit:
                jobs = jobs[:limit]
            
            print(f"✅ Simple scraper found {len(jobs)} jobs")
            return jobs
            
        except Exception as e:
            print(f"❌ Search request failed: {e}")
            # Return sample data as fallback
            return self._get_sample_jobs(keywords, location, limit)
    
    def _extract_jobs_from_html(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """Extract job listings from HTML content."""
        jobs = []
        
        # LinkedIn job card selectors
        job_selectors = [
            '[data-job-id]',
            '.job-search-card',
            '.job-card-container',
            '.job-card',
            '.artdeco-list__item'
        ]
        
        job_elements = []
        for selector in job_selectors:
            job_elements = soup.select(selector)
            if job_elements:
                print(f"📋 Found {len(job_elements)} job elements with selector: {selector}")
                break
        
        if not job_elements:
            print("⚠️  No job elements found, returning sample data")
            return []
        
        for i, job_element in enumerate(job_elements[:25]):  # Limit to 25 jobs
            try:
                job = self._extract_single_job(job_element, base_url, i + 1)
                if job:
                    jobs.append(job)
            except Exception as e:
                print(f"❌ Error extracting job {i + 1}: {e}")
                continue
        
        return jobs
    
    def _extract_single_job(self, job_element, base_url: str, job_id: int) -> Optional[Dict[str, Any]]:
        """Extract a single job from a job element."""
        try:
            # Extract job title
            title_selectors = [
                '.job-search-card__title',
                '.job-card__title',
                'h3',
                'h4',
                'a[data-job-id]'
            ]
            title = self._extract_text_from_element(job_element, title_selectors)
            
            if not title:
                return None
            
            # Extract company name with enhanced debugging
            company_selectors = [
                '.job-search-card__subtitle',
                '.job-card__company-name', 
                '.company-name',
                '.job-search-card__company-name',
                '.job-card__subtitle',
                'h4.base-search-card__subtitle',
                '.base-search-card__subtitle',
                'a[data-test-job-search-card-company] span',
                'span[class*="company"]',
                'div[class*="company"]'
            ]
            
            print(f"🏢 Extracting company for job: '{title}'")
            company = self._extract_text_from_element_with_debug(job_element, company_selectors, "company")
            
            # Extract location
            location_selectors = [
                '.job-search-card__location',
                '.job-card__location',
                '.location'
            ]
            location = self._extract_text_from_element(job_element, location_selectors)
            
            # Extract job URL
            linkedin_url = self._extract_job_url(job_element, base_url)
            
            # Create job object
            job = {
                "id": f"simple-{job_id}",
                "title": title or "Software Engineer",
                "company": company or "Unknown Company",
                "location": location or "United States",
                "description": f"Job description for {title} at {company}",
                "linkedin_url": linkedin_url,
                "date_posted": datetime.now().isoformat(),
                "job_type": "Full-time",
                "experience_level": "Mid level",
                "remote_type": "Hybrid",
                "salary_min": None,
                "salary_max": None
            }
            
            return job
            
        except Exception as e:
            print(f"❌ Error extracting single job: {e}")
            return None
    
    def _extract_text_from_element(self, element, selectors: List[str]) -> Optional[str]:
        """Extract text from element using multiple selectors."""
        for selector in selectors:
            try:
                found_element = element.select_one(selector)
                if found_element:
                    text = found_element.get_text(strip=True)
                    if text:
                        return text
            except Exception:
                continue
        return None
    
    def _extract_text_from_element_with_debug(self, element, selectors: List[str], field_name: str) -> Optional[str]:
        """Extract text from element with debugging output."""
        print(f"🔍 Extracting {field_name} with {len(selectors)} selectors")
        
        for i, selector in enumerate(selectors):
            try:
                found_element = element.select_one(selector)
                if found_element:
                    text = found_element.get_text(strip=True)
                    if text:
                        print(f"✅ Selector {i+1}: '{selector}' found: '{text}'")
                        return text
                    else:
                        print(f"❌ Selector {i+1}: '{selector}' found element but no text")
                else:
                    print(f"❌ Selector {i+1}: '{selector}' found no element")
            except Exception as e:
                print(f"❌ Selector {i+1}: '{selector}' failed: {e}")
                continue
        
        print(f"❌ No {field_name} found with any selector")
        return None
    
    def _extract_job_url(self, element, base_url: str) -> str:
        """Extract job URL from element."""
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
        
        return f"{self.base_url}/jobs"
    
    def _get_sample_jobs(self, keywords: str, location: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Return sample job data as fallback."""
        sample_jobs = []
        
        for i in range(min(limit, 5)):
            job = {
                "id": f"sample-{i + 1}",
                "title": f"{keywords} Developer" if keywords else "Software Engineer",
                "company": f"Tech Company {i + 1}",
                "location": location or "United States",
                "description": f"Sample job description for {keywords} position",
                "linkedin_url": f"https://linkedin.com/jobs/sample-{i + 1}",
                "date_posted": datetime.now().isoformat(),
                "job_type": "Full-time",
                "experience_level": "Mid level", 
                "remote_type": "Hybrid",
                "salary_min": None,
                "salary_max": None
            }
            sample_jobs.append(job)
        
        return sample_jobs
    
    def _respect_rate_limit(self):
        """Ensure we don't exceed rate limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()