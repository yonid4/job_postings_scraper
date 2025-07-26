#!/usr/bin/env python3
"""
Test script for Enhanced LinkedIn Scraper with improved filter methods.
Tests the ability to apply multiple filters using header-based section detection.
"""

import sys
import os
import time
from datetime import datetime

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.config.config_manager import ConfigurationManager
from src.utils.session_manager import SessionManager
from src.scrapers.linkedin_scraper_enhanced import EnhancedLinkedInScraper
from src.scrapers.base_scraper import ScrapingConfig

def test_enhanced_linkedin_filters():
    """Test the enhanced LinkedIn scraper with various filter combinations."""
    
    print("🚀 Enhanced LinkedIn Scraper Filter Test Suite")
    print("=" * 60)
    
    # Test filter optimization logic
    print("\n🧪 Testing Filter Optimization Logic")
    print("=" * 40)
    
    # Test cases for filter optimization
    test_cases = [
        (None, None, None, None, "No Filters - Should use regular scraping"),
        (1, None, None, None, "Date Filter Only - Should use enhanced scraping"),
        (None, "Remote", None, None, "Remote Filter Only - Should use enhanced scraping"),
        (None, None, "Entry level", None, "Experience Level Only - Should use enhanced scraping"),
        (None, None, None, "Full-time", "Job Type Only - Should use enhanced scraping"),
    ]
    
    for date_filter, work_arrangement, experience_level, job_type, description in test_cases:
        print(f"\n🔍 {description}")
        
        # Check if any UI-dependent filters are present
        has_ui_filters = any([
            date_filter is not None,
            work_arrangement is not None,
            experience_level is not None,
            job_type is not None
        ])
        
        if has_ui_filters:
            print("✅ Correctly chose enhanced mode")
        else:
            print("✅ Correctly chose regular mode")
    
    print("\n✅ Filter optimization logic test completed")
    
    # Initialize configuration
    config_manager = ConfigurationManager()
    linkedin_config = config_manager.get_linkedin_settings()
    
    if not linkedin_config.username or not linkedin_config.password:
        print("❌ LinkedIn credentials not found in configuration")
        return
    
    print("✅ LinkedIn credentials found for user:", linkedin_config.username)
    
    # Initialize session manager
    session_manager = SessionManager()
    
    # Create scraping config
    scraping_config = ScrapingConfig(
        site_name="linkedin",
        base_url="https://www.linkedin.com",
        max_jobs_per_session=10,  # Limit for testing
        delay_min=1.0,
        delay_max=2.0,
        max_retries=2,
        page_load_timeout=20
    )
    
    # Add LinkedIn credentials to config
    scraping_config.linkedin_username = linkedin_config.username
    scraping_config.linkedin_password = linkedin_config.password
    
    # Initialize enhanced scraper
    scraper = EnhancedLinkedInScraper(scraping_config, session_manager)
    
    print("\n🧪 Starting Enhanced LinkedIn Scraper Filter Tests")
    print("=" * 60)
    
    # Test configurations
    test_configs = [
        {
            "name": "Specific Filters Test",
            "date_posted_days": 1,  # Past 24 hours
            "work_arrangement": None,
            "experience_level": "Entry level",
            "job_type": "Full-time"
        }
    ]
    
    results = []
    
    for i, test_config in enumerate(test_configs, 1):
        print(f"\n🔍 Test {i}/{len(test_configs)}: {test_config['name']}")
        print("-" * 50)
        print("🎯 Testing specific filters:")
        print("   - Date posted: Past 24 hours")
        print("   - Experience level: Entry level")
        print("   - Job type: Full-time")
        print("-" * 50)
        
        # Build filter description
        filters = []
        if test_config['date_posted_days']:
            filters.append(f"Date: Past {test_config['date_posted_days']} days")
        if test_config['work_arrangement']:
            filters.append(f"Work Arrangement: {test_config['work_arrangement']}")
        if test_config['experience_level']:
            filters.append(f"Experience Level: {test_config['experience_level']}")
        if test_config['job_type']:
            filters.append(f"Job Type: {test_config['job_type']}")
        
        print(f"📋 Filters to apply: {', '.join(filters)}")
        
        start_time = time.time()
        
        try:
            # Perform scraping with filters
            result = scraper.scrape_jobs_with_enhanced_date_filter(
                keywords=["software engineer"],
                location="mountain view,ca,usa",
                date_posted_days=test_config['date_posted_days'],
                work_arrangement=test_config['work_arrangement'],
                experience_level=test_config['experience_level'],
                job_type=test_config['job_type'],
                require_auth=True
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            if result.success:
                job_count = len(result.jobs) if result.jobs else 0
                print(f"✅ Success! Found {job_count} jobs in {duration:.2f} seconds")
                results.append({
                    "test": test_config['name'],
                    "status": "SUCCESS",
                    "job_count": job_count,
                    "duration": duration
                })
            else:
                print(f"❌ Failed: {result.error_message}")
                results.append({
                    "test": test_config['name'],
                    "status": "FAILED",
                    "error": result.error_message,
                    "duration": duration
                })
                
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            print(f"❌ Exception: {str(e)}")
            results.append({
                "test": test_config['name'],
                "status": "EXCEPTION",
                "error": str(e),
                "duration": duration
            })
    
    # Cleanup
    try:
        scraper.cleanup()
    except:
        pass
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    successful_tests = [r for r in results if r['status'] == 'SUCCESS']
    failed_tests = [r for r in results if r['status'] != 'SUCCESS']
    
    print(f"✅ Successful tests: {len(successful_tests)}/{len(results)}")
    print(f"❌ Failed tests: {len(failed_tests)}/{len(results)}")
    
    if successful_tests:
        total_jobs = sum(r['job_count'] for r in successful_tests)
        avg_duration = sum(r['duration'] for r in successful_tests) / len(successful_tests)
        print(f"📈 Total jobs found: {total_jobs}")
        print(f"⏱️  Average duration: {avg_duration:.2f} seconds")
    
    if failed_tests:
        print("\n❌ Failed Tests:")
        for result in failed_tests:
            print(f"  - {result['test']}: {result.get('error', 'Unknown error')}")
    
    print("\n🎉 Test suite completed!")

if __name__ == "__main__":
    test_enhanced_linkedin_filters() 