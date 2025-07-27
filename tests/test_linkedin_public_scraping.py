#!/usr/bin/env python3
"""
Test script to verify LinkedIn job scraping with authentication and date filtering.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to Python path to import src modules
parent_dir = Path(__file__).parent
sys.path.insert(0, str(parent_dir))

from src.scrapers.linkedin_scraper_enhanced import EnhancedLinkedInScraper
from src.utils.session_manager import SessionManager
from src.scrapers.linkedin_scraper_enhanced import ScrapingConfig
from src.utils.logger import JobAutomationLogger

logger = JobAutomationLogger()


def test_linkedin_authenticated_scraping():
    """Test LinkedIn job scraping with authentication and date filtering."""
    print("🧪 Testing LinkedIn Authenticated Job Scraping...")
    
    try:
        # Create session manager
        session_manager = SessionManager()
        
        # Create scraping config with LinkedIn credentials
        config = ScrapingConfig(
            max_jobs_per_session=5,  # Small number for testing
            delay_min=2.0,
            delay_max=3.0,
            max_retries=2,
            page_load_timeout=30,
            site_name="linkedin",
            base_url="https://www.linkedin.com"
        )
        
        # Get LinkedIn credentials from settings
        from src.config.config_manager import ConfigurationManager
        config_manager = ConfigurationManager()
        linkedin_config = config_manager.get_linkedin_settings()
        
        if not linkedin_config.username or not linkedin_config.password:
            print("❌ LinkedIn credentials not configured in settings.json")
            return False
        
        # Add LinkedIn credentials to config
        config.linkedin_username = linkedin_config.username
        config.linkedin_password = linkedin_config.password
        
        # Initialize enhanced scraper
        scraper = EnhancedLinkedInScraper(config, session_manager)
        
        print("✅ Enhanced LinkedIn scraper initialized")
        print(f"🔐 Using credentials for: {linkedin_config.username}")
        
        # Test scraping with authentication and date filtering
        keywords = ["Software Engineer"]
        location = "San Francisco, CA"
        
        print(f"🔍 Searching for: {keywords} in {location}")
        print("📝 Using authentication and date filtering")
        
        # Scrape jobs with authentication and date filter
        scraping_result = scraper.scrape_jobs_with_enhanced_date_filter(
            keywords=keywords,
            location=location,
            date_posted_days=7,  # Past week
            require_auth=True  # Authentication required for LinkedIn
        )
        
        if scraping_result.success:
            print(f"✅ Successfully scraped {len(scraping_result.jobs)} jobs")
            
            if scraping_result.jobs:
                print("\n📋 Sample jobs found:")
                for i, job in enumerate(scraping_result.jobs[:3], 1):
                    print(f"  {i}. {job.title} at {job.company}")
                    print(f"     Location: {job.location}")
                    print(f"     URL: {job.job_url}")
                    print()
            else:
                print("⚠️ No jobs found (this might be normal for the test location)")
        else:
            print(f"❌ Scraping failed: {scraping_result.error_message}")
            return False
        
        # Clean up
        scraper.cleanup()
        print("✅ Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the LinkedIn authenticated scraping test."""
    print("🚀 LinkedIn Authenticated Job Scraping Test")
    print("=" * 50)
    
    success = test_linkedin_authenticated_scraping()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 LinkedIn authenticated scraping test PASSED!")
        print("✅ The enhanced LinkedIn scraper works with authentication")
        print("✅ You can now use LinkedIn job search in the web interface")
    else:
        print("❌ LinkedIn authenticated scraping test FAILED")
        print("⚠️ Check the error messages above for details")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 