#!/usr/bin/env python3
"""
Focused test script for specific LinkedIn filters

This script specifically tests the new filters:
- Work arrangement filter (Remote)
- Experience level filter (Entry level)
- Job type filter (Full-time)

The goal is to verify that these filters are being applied correctly through UI interaction.
"""

import os
import sys
import time
from pathlib import Path

# Add the parent directory to Python path to import src modules
parent_dir = Path(__file__).parent
sys.path.insert(0, str(parent_dir))

from src.scrapers.linkedin_scraper_enhanced import EnhancedLinkedInScraper
from src.scrapers.linkedin_scraper import ScrapingConfig
from src.utils.session_manager import SessionManager
from src.config.config_manager import ConfigurationManager


def test_remote_filter():
    """Test specifically the Remote work filter."""
    
    print("🧪 Testing Remote Work Filter")
    print("=" * 50)
    
    # Initialize configuration
    try:
        config_manager = ConfigurationManager()
        linkedin_config = config_manager.get_linkedin_settings()
        
        if not linkedin_config.username or not linkedin_config.password:
            print("❌ LinkedIn credentials not configured")
            return False
            
        print(f"✅ Using credentials for: {linkedin_config.username}")
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    # Initialize scraper
    session_manager = SessionManager()
    config = ScrapingConfig(
        max_jobs_per_session=5,  # Small limit for testing
        delay_min=1.0,
        delay_max=2.0,
        max_retries=2,
        page_load_timeout=20,
        site_name="linkedin",
        base_url="https://www.linkedin.com"
    )
    
    config.linkedin_username = linkedin_config.username
    config.linkedin_password = linkedin_config.password
    
    scraper = EnhancedLinkedInScraper(config, session_manager)
    
    try:
        print("🔍 Testing Remote filter application...")
        
        # Test with Remote filter only
        scraping_result = scraper.scrape_jobs_with_enhanced_date_filter(
            keywords=["software engineer"],
            location="mountain view,ca,usa",
            date_posted_days=None,  # No date filter
            require_auth=True,
            work_arrangement="Remote",  # Only Remote filter
            experience_level=None,
            job_type=None
        )
        
        if scraping_result.success:
            job_count = len(scraping_result.jobs)
            print(f"✅ SUCCESS: Found {job_count} remote jobs")
            
            if job_count > 0:
                print("📋 Remote jobs found:")
                for i, job in enumerate(scraping_result.jobs[:3], 1):
                    print(f"   {i}. {job.title} at {job.company}")
                    # Check if job title contains "Remote" or similar
                    if "remote" in job.title.lower() or "remote" in (job.location or "").lower():
                        print(f"      ✅ Confirmed remote job")
                    else:
                        print(f"      ⚠️ Job doesn't explicitly mention remote")
            
            return True
        else:
            print(f"❌ FAILED: {scraping_result.error_message}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False
    finally:
        try:
            scraper.cleanup()
            print("🧹 Cleanup completed")
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")


def test_experience_level_filter():
    """Test specifically the Experience Level filter."""
    
    print("\n🧪 Testing Experience Level Filter")
    print("=" * 50)
    
    # Initialize configuration
    try:
        config_manager = ConfigurationManager()
        linkedin_config = config_manager.get_linkedin_settings()
        
        if not linkedin_config.username or not linkedin_config.password:
            print("❌ LinkedIn credentials not configured")
            return False
            
        print(f"✅ Using credentials for: {linkedin_config.username}")
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    # Initialize scraper
    session_manager = SessionManager()
    config = ScrapingConfig(
        max_jobs_per_session=5,  # Small limit for testing
        delay_min=1.0,
        delay_max=2.0,
        max_retries=2,
        page_load_timeout=20,
        site_name="linkedin",
        base_url="https://www.linkedin.com"
    )
    
    config.linkedin_username = linkedin_config.username
    config.linkedin_password = linkedin_config.password
    
    scraper = EnhancedLinkedInScraper(config, session_manager)
    
    try:
        print("🔍 Testing Entry Level filter application...")
        
        # Test with Entry Level filter only
        scraping_result = scraper.scrape_jobs_with_enhanced_date_filter(
            keywords=["software engineer"],
            location="mountain view,ca,usa",
            date_posted_days=None,  # No date filter
            require_auth=True,
            work_arrangement=None,
            experience_level="Entry level",  # Only Entry Level filter
            job_type=None
        )
        
        if scraping_result.success:
            job_count = len(scraping_result.jobs)
            print(f"✅ SUCCESS: Found {job_count} entry level jobs")
            
            if job_count > 0:
                print("📋 Entry level jobs found:")
                for i, job in enumerate(scraping_result.jobs[:3], 1):
                    print(f"   {i}. {job.title} at {job.company}")
                    # Check if job title contains entry level indicators
                    entry_level_indicators = ["entry", "junior", "new grad", "associate", "level 1", "l1"]
                    if any(indicator in job.title.lower() for indicator in entry_level_indicators):
                        print(f"      ✅ Confirmed entry level job")
                    else:
                        print(f"      ⚠️ Job doesn't explicitly mention entry level")
            
            return True
        else:
            print(f"❌ FAILED: {scraping_result.error_message}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False
    finally:
        try:
            scraper.cleanup()
            print("🧹 Cleanup completed")
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")


def test_job_type_filter():
    """Test specifically the Job Type filter."""
    
    print("\n🧪 Testing Job Type Filter")
    print("=" * 50)
    
    # Initialize configuration
    try:
        config_manager = ConfigurationManager()
        linkedin_config = config_manager.get_linkedin_settings()
        
        if not linkedin_config.username or not linkedin_config.password:
            print("❌ LinkedIn credentials not configured")
            return False
            
        print(f"✅ Using credentials for: {linkedin_config.username}")
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    # Initialize scraper
    session_manager = SessionManager()
    config = ScrapingConfig(
        max_jobs_per_session=5,  # Small limit for testing
        delay_min=1.0,
        delay_max=2.0,
        max_retries=2,
        page_load_timeout=20,
        site_name="linkedin",
        base_url="https://www.linkedin.com"
    )
    
    config.linkedin_username = linkedin_config.username
    config.linkedin_password = linkedin_config.password
    
    scraper = EnhancedLinkedInScraper(config, session_manager)
    
    try:
        print("🔍 Testing Full-time filter application...")
        
        # Test with Full-time filter only
        scraping_result = scraper.scrape_jobs_with_enhanced_date_filter(
            keywords=["software engineer"],
            location="mountain view,ca,usa",
            date_posted_days=None,  # No date filter
            require_auth=True,
            work_arrangement=None,
            experience_level=None,
            job_type="Full-time"  # Only Full-time filter
        )
        
        if scraping_result.success:
            job_count = len(scraping_result.jobs)
            print(f"✅ SUCCESS: Found {job_count} full-time jobs")
            
            if job_count > 0:
                print("📋 Full-time jobs found:")
                for i, job in enumerate(scraping_result.jobs[:3], 1):
                    print(f"   {i}. {job.title} at {job.company}")
                    # Check if job title contains full-time indicators
                    full_time_indicators = ["full-time", "full time", "fulltime", "permanent"]
                    if any(indicator in job.title.lower() for indicator in full_time_indicators):
                        print(f"      ✅ Confirmed full-time job")
                    else:
                        print(f"      ⚠️ Job doesn't explicitly mention full-time")
            
            return True
        else:
            print(f"❌ FAILED: {scraping_result.error_message}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False
    finally:
        try:
            scraper.cleanup()
            print("🧹 Cleanup completed")
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")


if __name__ == "__main__":
    print("🚀 Focused LinkedIn Filter Tests")
    print("=" * 60)
    
    # Test each filter individually
    tests = [
        ("Remote Filter", test_remote_filter),
        ("Experience Level Filter", test_experience_level_filter),
        ("Job Type Filter", test_job_type_filter)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
        
        # Wait between tests
        print("⏳ Waiting 10 seconds before next test...")
        time.sleep(10)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    successful_tests = 0
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")
        if success:
            successful_tests += 1
    
    print(f"\n📈 Results: {successful_tests}/{len(tests)} tests passed")
    
    if successful_tests == len(tests):
        print("🎉 ALL FILTER TESTS PASSED!")
        sys.exit(0)
    else:
        print("⚠️ Some filter tests failed. Check the logs above.")
        sys.exit(1) 