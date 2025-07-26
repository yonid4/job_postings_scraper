#!/usr/bin/env python3
"""
Test script to debug URL extraction from LinkedIn job cards.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.job_link_processor import JobLinkProcessor
from src.config.config_manager import ConfigurationManager
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_url_extraction():
    """Test URL extraction from LinkedIn search URLs."""
    
    print("🔍 Testing LinkedIn URL Extraction")
    print("=" * 50)
    
    # Initialize components
    config_manager = ConfigurationManager()
    job_processor = JobLinkProcessor()
    
    # Test URLs
    test_urls = [
        "https://www.linkedin.com/jobs/search/?keywords=python%20developer&location=San%20Francisco",
        "https://www.linkedin.com/jobs/search/?currentJobId=4271057209&geoId=103644278&keywords=entry%20level%20software%20engineer&origin=JOB_SEARCH_PAGE_LOCATION_AUTOCOMPLETE&refresh=true&start=25"
    ]
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n📋 Test {i}: {url}")
        print("-" * 30)
        
        try:
            # Process the URL
            job_links = job_processor.process_job_links([url])
            
            print(f"✅ Extracted {len(job_links)} jobs")
            
            # Show details for first few jobs
            for j, job_link in enumerate(job_links[:3], 1):
                print(f"\n  Job {j}:")
                print(f"    Title: {job_link.title}")
                print(f"    Company: {job_link.company}")
                print(f"    Location: {job_link.location}")
                print(f"    Job ID: {job_link.job_id}")
                print(f"    URL: {job_link.url}")
                print(f"    Error: {job_link.error}")
                
                # Check if URL looks like a proper job URL
                if job_link.url and '/jobs/view/' in job_link.url:
                    print(f"    ✅ URL looks like a proper job URL")
                elif job_link.url and 'linkedin.com' in job_link.url:
                    print(f"    ⚠️  URL is LinkedIn but may not be a specific job")
                else:
                    print(f"    ❌ URL doesn't look like a LinkedIn job URL")
                    
        except Exception as e:
            print(f"❌ Error processing URL: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Summary:")
    print("The test above shows what URLs are being extracted.")
    print("If you see URLs that don't contain '/jobs/view/', that's the issue.")
    print("The improved extraction logic should now handle more cases.")

if __name__ == "__main__":
    test_url_extraction() 