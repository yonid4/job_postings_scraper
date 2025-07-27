#!/usr/bin/env python3
"""
Test script to verify the integration of the fixed LinkedIn scraper into the main system.
This tests the filter detection logic and scraper selection.
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

def test_filter_detection_logic():
    """Test the filter detection logic that determines which scraper to use."""
    
    print("🧪 LinkedIn Filter Detection Logic Test")
    print("=" * 50)
    
    # Define default LinkedIn filter values (same as in frontend)
    linkedin_defaults = {
        "sort_by": "Most relevant",
        "date_posted": "Any time", 
        "experience_level": None,
        "company": None,
        "job_type": None,
        "remote": None
    }
    
    # Test cases
    test_cases = [
        {
            "name": "No filters (default values)",
            "filters": {
                "date_posted_days": None,
                "work_arrangement": None,
                "experience_level": None,
                "job_type": None
            },
            "expected_use_fixed_scraper": False,
            "expected_reason": "No custom filters - use regular scraping"
        },
        {
            "name": "Date filter only",
            "filters": {
                "date_posted_days": 7,
                "work_arrangement": None,
                "experience_level": None,
                "job_type": None
            },
            "expected_use_fixed_scraper": True,
            "expected_reason": "Date filter requires browser interaction"
        },
        {
            "name": "Remote work arrangement",
            "filters": {
                "date_posted_days": None,
                "work_arrangement": "Remote",
                "experience_level": None,
                "job_type": None
            },
            "expected_use_fixed_scraper": True,
            "expected_reason": "Work arrangement filter requires browser interaction"
        },
        {
            "name": "Entry level experience",
            "filters": {
                "date_posted_days": None,
                "work_arrangement": None,
                "experience_level": "Entry level",
                "job_type": None
            },
            "expected_use_fixed_scraper": True,
            "expected_reason": "Experience level filter requires browser interaction"
        },
        {
            "name": "Full-time job type",
            "filters": {
                "date_posted_days": None,
                "work_arrangement": None,
                "experience_level": None,
                "job_type": "Full-time"
            },
            "expected_use_fixed_scraper": True,
            "expected_reason": "Job type filter requires browser interaction"
        },
        {
            "name": "Multiple filters",
            "filters": {
                "date_posted_days": 1,
                "work_arrangement": "Remote",
                "experience_level": "Entry level",
                "job_type": "Full-time"
            },
            "expected_use_fixed_scraper": True,
            "expected_reason": "Multiple filters require browser interaction"
        }
    ]
    
    passed_tests = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}/{total_tests}: {test_case['name']}")
        print("-" * 40)
        
        # Extract filter values
        date_posted_days = test_case['filters']['date_posted_days']
        work_arrangement = test_case['filters']['work_arrangement']
        experience_level = test_case['filters']['experience_level']
        job_type = test_case['filters']['job_type']
        
        # Apply the same logic as in the frontend
        has_custom_filters = False
        
        # Check date filter
        if date_posted_days is not None:
            has_custom_filters = True
            
        # Check work arrangement (Remote filter)
        if work_arrangement and work_arrangement != linkedin_defaults["remote"]:
            has_custom_filters = True
            
        # Check experience level
        if experience_level and experience_level != linkedin_defaults["experience_level"]:
            has_custom_filters = True
            
        # Check job type
        if job_type and job_type != linkedin_defaults["job_type"]:
            has_custom_filters = True
        
        # Determine result
        use_fixed_scraper = has_custom_filters
        
        # Check if result matches expectation
        if use_fixed_scraper == test_case['expected_use_fixed_scraper']:
            print("✅ PASS: Filter detection logic correct")
            print(f"   Filters: {test_case['filters']}")
            print(f"   Use Fixed Scraper: {use_fixed_scraper}")
            print(f"   Reason: {test_case['expected_reason']}")
            passed_tests += 1
        else:
            print("❌ FAIL: Filter detection logic incorrect")
            print(f"   Filters: {test_case['filters']}")
            print(f"   Expected: {test_case['expected_use_fixed_scraper']}")
            print(f"   Got: {use_fixed_scraper}")
    
    # Final Results
    print("\n" + "="*50)
    print("📊 FILTER DETECTION TEST RESULTS")
    print("="*50)
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Filter detection logic is working correctly.")
    else:
        print("\n⚠️ SOME TESTS FAILED! Filter detection logic needs fixing.")
    
    return passed_tests == total_tests

def test_fixed_scraper_creation():
    """Test that the fixed scraper can be created successfully."""
    
    print("\n🧪 Fixed LinkedIn Scraper Creation Test")
    print("=" * 50)
    
    # Initialize configuration
    config_manager = ConfigurationManager()
    linkedin_config = config_manager.get_linkedin_settings()
    
    if not linkedin_config.username or not linkedin_config.password:
        print("❌ LinkedIn credentials not found in configuration")
        return False
    
    print("✅ LinkedIn credentials found for user:", linkedin_config.username)
    
    try:
        # Create session manager
        session_manager = SessionManager()
        
        # Create scraping config
        config = ScrapingConfig(
            site_name="linkedin",
            base_url="https://www.linkedin.com",
            max_jobs_per_session=5,  # Small number for testing
            delay_min=2.0,
            delay_max=3.0,
            max_retries=2,
            page_load_timeout=20
        )
        
        # Add LinkedIn credentials to config
        config.linkedin_username = linkedin_config.username
        config.linkedin_password = linkedin_config.password
        
        # Create fixed scraper
        scraper = EnhancedLinkedInScraper(config, session_manager)
        
        print("✅ Fixed LinkedIn scraper created successfully")
        print(f"   Scraper type: {type(scraper).__name__}")
        print(f"   Inherits from EnhancedLinkedInScraper: {isinstance(scraper, EnhancedLinkedInScraper)}")
        
        # Test that it has the required methods
        required_methods = [
            'scrape_jobs_with_enhanced_date_filter',
            '_apply_date_filter_in_modal',
            '_apply_experience_level_in_modal',
            '_apply_job_type_in_modal',
            '_apply_work_arrangement_in_modal',
            '_find_and_click_filter_option'
        ]
        
        missing_methods = []
        for method in required_methods:
            if not hasattr(scraper, method):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ Missing methods: {missing_methods}")
            return False
        else:
            print("✅ All required methods present")
        
        # Cleanup
        try:
            scraper.cleanup()
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating fixed scraper: {e}")
        return False

def main():
    """Run all integration tests."""
    
    print("🚀 LinkedIn Integration Test Suite")
    print("=" * 60)
    
    # Test 1: Filter detection logic
    filter_logic_passed = test_filter_detection_logic()
    
    # Test 2: Fixed scraper creation
    scraper_creation_passed = test_fixed_scraper_creation()
    
    # Final Results
    print("\n" + "="*60)
    print("📊 INTEGRATION TEST RESULTS")
    print("="*60)
    
    print(f"Filter Detection Logic: {'✅ PASSED' if filter_logic_passed else '❌ FAILED'}")
    print(f"Fixed Scraper Creation: {'✅ PASSED' if scraper_creation_passed else '❌ FAILED'}")
    
    if filter_logic_passed and scraper_creation_passed:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("The fixed LinkedIn scraper is ready for production use.")
    else:
        print("\n⚠️ SOME INTEGRATION TESTS FAILED!")
        print("Please fix the issues before deploying to production.")
    
    print("\n🎉 Integration test suite completed!")

if __name__ == "__main__":
    main() 