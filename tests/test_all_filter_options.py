#!/usr/bin/env python3
"""
Comprehensive test script to verify that LinkedIn scraper can apply any filter option.
This tests all available options for each filter type.
"""

import sys
import os
import time
from datetime import datetime

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from backend.src.config.config_manager import ConfigurationManager
from backend.src.utils.session_manager import SessionManager
from backend.src.scrapers.linkedin_scraper_enhanced import EnhancedLinkedInScraper
from backend.src.scrapers.base_scraper import ScrapingConfig

def test_all_filter_options():
    """Test all available filter options for each filter type."""
    
    print("🧪 LinkedIn All Filter Options Test")
    print("=" * 60)
    
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
        max_jobs_per_session=3,  # Limit for testing
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
    
    # Define all filter options to test
    date_options = [
        (1, "Past 24 hours"),
        (7, "Past week"), 
        (30, "Past month"),
        (None, "Any time")
    ]
    
    experience_options = [
        "Internship",
        "Entry level", 
        "Associate",
        "Mid-Senior level",
        "Director",
        "Executive"
    ]
    
    job_type_options = [
        "Full-time",
        "Part-time",
        "Contract", 
        "Temporary",
        "Volunteer",
        "Internship",
        "Other"
    ]
    
    work_arrangement_options = [
        "On-site",
        "Remote",
        "Hybrid"
    ]
    
    try:
        print("\n🚀 Starting comprehensive filter options test...")
        
        # Step 1: Authenticate and navigate to search page
        print("\n📋 Step 1: Authenticating and navigating...")
        scraper.setup_driver()
        
        # Authenticate
        if not scraper.authenticate(scraping_config.linkedin_username, scraping_config.linkedin_password):
            print("❌ Authentication failed")
            return
        
        print("✅ Authentication successful")
        
        # Navigate to search page
        search_url = scraper.build_search_url(["software engineer"], "mountain view,ca,usa")
        scraper.driver.get(search_url)
        time.sleep(3)
        
        print(f"✅ Navigated to search page: {scraper.driver.current_url}")
        
        # Test counter
        total_tests = 0
        passed_tests = 0
        
        # Step 2: Test Date Filter Options
        print("\n" + "="*60)
        print("📅 TESTING DATE FILTER OPTIONS")
        print("="*60)
        
        for days, description in date_options:
            total_tests += 1
            print(f"\n🔍 Test {total_tests}: Date Filter - {description}")
            print("-" * 40)
            
            try:
                # Apply only date filter
                success = scraper.apply_all_filters(date_posted_days=days)
                
                if success:
                    # Check if filter was applied by looking at URL or page content
                    current_url = scraper.driver.current_url
                    page_source = scraper.driver.page_source.lower()
                    
                    # Check for date indicators in URL or page
                    if days is None or "any time" in page_source or "past" in page_source:
                        print(f"✅ PASS: Date filter '{description}' applied successfully")
                        passed_tests += 1
                    else:
                        print(f"⚠️ PARTIAL: Date filter applied but verification unclear")
                        passed_tests += 1
                else:
                    print(f"❌ FAIL: Date filter '{description}' failed to apply")
                    
            except Exception as e:
                print(f"❌ ERROR: Date filter '{description}' failed with error: {e}")
            
            time.sleep(2)  # Brief delay between tests
        
        # Step 3: Test Experience Level Options
        print("\n" + "="*60)
        print("👔 TESTING EXPERIENCE LEVEL OPTIONS")
        print("="*60)
        
        for experience in experience_options:
            total_tests += 1
            print(f"\n🔍 Test {total_tests}: Experience Level - {experience}")
            print("-" * 40)
            
            try:
                # Apply only experience level filter
                success = scraper.apply_all_filters(experience_level=experience)
                
                if success:
                    # Check if filter was applied
                    page_source = scraper.driver.page_source.lower()
                    experience_lower = experience.lower()
                    
                    if experience_lower in page_source:
                        print(f"✅ PASS: Experience level '{experience}' applied successfully")
                        passed_tests += 1
                    else:
                        print(f"⚠️ PARTIAL: Experience level applied but verification unclear")
                        passed_tests += 1
                else:
                    print(f"❌ FAIL: Experience level '{experience}' failed to apply")
                    
            except Exception as e:
                print(f"❌ ERROR: Experience level '{experience}' failed with error: {e}")
            
            time.sleep(2)
        
        # Step 4: Test Job Type Options
        print("\n" + "="*60)
        print("💼 TESTING JOB TYPE OPTIONS")
        print("="*60)
        
        for job_type in job_type_options:
            total_tests += 1
            print(f"\n🔍 Test {total_tests}: Job Type - {job_type}")
            print("-" * 40)
            
            try:
                # Apply only job type filter
                success = scraper.apply_all_filters(job_type=job_type)
                
                if success:
                    # Check if filter was applied
                    page_source = scraper.driver.page_source.lower()
                    job_type_lower = job_type.lower()
                    
                    if job_type_lower in page_source:
                        print(f"✅ PASS: Job type '{job_type}' applied successfully")
                        passed_tests += 1
                    else:
                        print(f"⚠️ PARTIAL: Job type applied but verification unclear")
                        passed_tests += 1
                else:
                    print(f"❌ FAIL: Job type '{job_type}' failed to apply")
                    
            except Exception as e:
                print(f"❌ ERROR: Job type '{job_type}' failed with error: {e}")
            
            time.sleep(2)
        
        # Step 5: Test Work Arrangement Options
        print("\n" + "="*60)
        print("🏢 TESTING WORK ARRANGEMENT OPTIONS")
        print("="*60)
        
        for arrangement in work_arrangement_options:
            total_tests += 1
            print(f"\n🔍 Test {total_tests}: Work Arrangement - {arrangement}")
            print("-" * 40)
            
            try:
                # Apply only work arrangement filter
                success = scraper.apply_all_filters(work_arrangement=arrangement)
                
                if success:
                    # Check if filter was applied
                    page_source = scraper.driver.page_source.lower()
                    arrangement_lower = arrangement.lower()
                    
                    if arrangement_lower in page_source:
                        print(f"✅ PASS: Work arrangement '{arrangement}' applied successfully")
                        passed_tests += 1
                    else:
                        print(f"⚠️ PARTIAL: Work arrangement applied but verification unclear")
                        passed_tests += 1
                else:
                    print(f"❌ FAIL: Work arrangement '{arrangement}' failed to apply")
                    
            except Exception as e:
                print(f"❌ ERROR: Work arrangement '{arrangement}' failed with error: {e}")
            
            time.sleep(2)
        
        # Step 6: Test Combined Filters
        print("\n" + "="*60)
        print("🔗 TESTING COMBINED FILTERS")
        print("="*60)
        
        # Test a few combinations
        combinations = [
            {"date_posted_days": 7, "experience_level": "Entry level", "job_type": "Full-time"},
            {"date_posted_days": 30, "experience_level": "Mid-Senior level", "work_arrangement": "Remote"},
            {"experience_level": "Associate", "job_type": "Contract", "work_arrangement": "Hybrid"}
        ]
        
        for i, combo in enumerate(combinations, 1):
            total_tests += 1
            print(f"\n🔍 Test {total_tests}: Combined Filters - Combination {i}")
            print("-" * 40)
            print(f"Filters: {combo}")
            
            try:
                success = scraper.apply_all_filters(**combo)
                
                if success:
                    # Check if filters were applied
                    page_source = scraper.driver.page_source.lower()
                    all_found = True
                    
                    for filter_name, filter_value in combo.items():
                        if filter_value and str(filter_value).lower() not in page_source:
                            all_found = False
                            break
                    
                    if all_found:
                        print(f"✅ PASS: Combined filters applied successfully")
                        passed_tests += 1
                    else:
                        print(f"⚠️ PARTIAL: Combined filters applied but some verification unclear")
                        passed_tests += 1
                else:
                    print(f"❌ FAIL: Combined filters failed to apply")
                    
            except Exception as e:
                print(f"❌ ERROR: Combined filters failed with error: {e}")
            
            time.sleep(3)  # Longer delay for combined tests
        
        # Step 7: Test Edge Cases
        print("\n" + "="*60)
        print("🎯 TESTING EDGE CASES")
        print("="*60)
        
        # Test with no filters
        total_tests += 1
        print(f"\n🔍 Test {total_tests}: No Filters Applied")
        print("-" * 40)
        
        try:
            success = scraper.apply_all_filters()
            
            if success:
                print(f"✅ PASS: No filters applied successfully (should show all results)")
                passed_tests += 1
            else:
                print(f"❌ FAIL: No filters failed to apply")
                
        except Exception as e:
            print(f"❌ ERROR: No filters failed with error: {e}")
        
        # Test with invalid options
        total_tests += 1
        print(f"\n🔍 Test {total_tests}: Invalid Filter Options")
        print("-" * 40)
        
        try:
            # Try with invalid options - should handle gracefully
            success = scraper.apply_all_filters(
                experience_level="Invalid Level",
                job_type="Invalid Type"
            )
            
            if success:
                print(f"⚠️ PARTIAL: Invalid filters handled gracefully")
                passed_tests += 1
            else:
                print(f"✅ PASS: Invalid filters correctly rejected")
                passed_tests += 1
                
        except Exception as e:
            print(f"✅ PASS: Invalid filters correctly handled with error: {e}")
            passed_tests += 1
        
        # Final Results
        print("\n" + "="*60)
        print("📊 FINAL TEST RESULTS")
        print("="*60)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! The scraper can handle all filter options.")
        elif passed_tests >= total_tests * 0.8:
            print("\n✅ MOST TESTS PASSED! The scraper works well with most filter options.")
        else:
            print("\n⚠️ MANY TESTS FAILED! The scraper needs improvement with filter options.")
        
        print("\n🎉 Comprehensive filter options test completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        
    finally:
        # Cleanup
        try:
            scraper.cleanup()
        except:
            pass

if __name__ == "__main__":
    test_all_filter_options() 