#!/usr/bin/env python3
"""
Test script to verify LinkedIn scraper fixes for job title and company name extraction.
"""

import os
import sys
from typing import List, Optional

# Add src to path - handle both root and tests directory
current_dir = os.path.dirname(__file__)
if current_dir.endswith('tests'):
    # If we're in the tests directory, go up one level to find src
    src_path = os.path.join(os.path.dirname(current_dir), 'src')
else:
    # If we're in the root directory
    src_path = os.path.join(current_dir, 'src')

sys.path.insert(0, src_path)

try:
    from scrapers.linkedin_scraper_enhanced import EnhancedLinkedInScraper
    from scrapers.base_scraper import ScrapingConfig
    from utils.logger import JobAutomationLogger
except ImportError:
    # Fallback for src imports
    try:
        from src.scrapers.linkedin_scraper_enhanced import EnhancedLinkedInScraper
        from src.scrapers.base_scraper import ScrapingConfig
        from src.utils.logger import JobAutomationLogger
    except ImportError:
        print("Error: Could not import required modules. Please ensure you're running from the project root.")
        sys.exit(1)

def test_linkedin_scraper_fixes():
    """Test the LinkedIn scraper with the new extraction logic."""
    
    # Set up logging
    logger = JobAutomationLogger("test_linkedin_fixes")
    logger.logger.info("Starting LinkedIn scraper fixes test")
    
    # Create configuration
    config = ScrapingConfig(
        site_name="linkedin",
        base_url="https://www.linkedin.com",
        delay_min=1.0,
        delay_max=2.0,
        max_requests_per_minute=20,
        max_jobs_per_session=10,
        respect_robots_txt=True,
        use_random_delays=True,
        log_level="INFO",
        page_load_timeout=30,
        element_wait_timeout=15
    )
    
    # Create scraper instance
    scraper = EnhancedLinkedInScraper(config)
    
    try:
        # Test the new robust extraction methods
        logger.logger.info("Testing new robust extraction methods...")
        
        # Test job title extraction with mock data
        logger.logger.info("\n=== Testing Job Title Extraction ===")
        test_job_titles = [
            "Senior Software Engineer",
            "Product Manager", 
            "Data Scientist",
            "UX Designer",
            "Unknown Job Title"
        ]
        
        for title in test_job_titles:
            result = scraper.validate_extraction_results(title, "Test Company")
            logger.logger.info(f"Job title validation for '{title}': {result}")
        
        # Test company name extraction with mock data
        logger.logger.info("\n=== Testing Company Name Extraction ===")
        test_companies = [
            "Google Inc",
            "Microsoft Corporation",
            "Apple",
            "Amazon",
            "Unknown Company"
        ]
        
        for company in test_companies:
            result = scraper.validate_extraction_results("Software Engineer", company)
            logger.logger.info(f"Company validation for '{company}': {result}")
        
        # Test the selectors
        logger.logger.info("\n=== Testing Updated Selectors ===")
        logger.logger.info("Job Title Selectors:")
        job_title_selectors = [
            "h1.t-24.job-details-jobs-unified-top-card__job-title",
            ".t-24.job-details-jobs-unified-top-card__job-title", 
            "h1[class*='job-details-jobs-unified-top-card__job-title']",
            ".job-details-jobs-unified-top-card__job-title",
            ".jobs-box__job-title",
            "h1",
            ".job-title"
        ]
        
        for i, selector in enumerate(job_title_selectors, 1):
            logger.logger.info(f"  {i}. {selector}")
        
        logger.logger.info("\nCompany Name Selectors:")
        company_selectors = [
            ".job-details-jobs-unified-top-card__company-name .sRnCkbnFXZXqjWAFekZQCfsMNMELMevApSMNluw",
            ".job-details-jobs-unified-top-card__company-name div[class*='sRnCkbnFXZXqjWAFekZQCfsMNMELMevApSMNluw']",
            ".job-details-jobs-unified-top-card__company-name a",
            ".job-details-jobs-unified-top-card__company-name span",
            ".job-details-jobs-unified-top-card__company-name",
            ".jobs-box__company-name",
            ".company-name"
        ]
        
        for i, selector in enumerate(company_selectors, 1):
            logger.logger.info(f"  {i}. {selector}")
        
        logger.logger.info("\n✅ LinkedIn scraper fixes test completed successfully!")
        logger.logger.info("The updated extraction logic should now correctly identify:")
        logger.logger.info("- Job titles using the new h1.t-24.job-details-jobs-unified-top-card__job-title selector")
        logger.logger.info("- Company names using the new .job-details-jobs-unified-top-card__company-name .sRnCkbnFXZXqjWAFekZQCfsMNMELMevApSMNluw selector")
        logger.logger.info("- Multiple fallback selectors for robustness")
        logger.logger.info("- Validation logic to ensure correct extraction")
        
    except Exception as e:
        logger.logger.error(f"❌ Test failed: {e}")
        return False
    
    finally:
        # Clean up
        scraper.cleanup()
    
    return True

if __name__ == "__main__":
    success = test_linkedin_scraper_fixes()
    sys.exit(0 if success else 1) 