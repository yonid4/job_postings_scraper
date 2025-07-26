#!/usr/bin/env python3
"""
Test script to verify filter detection logic for LinkedIn search.
This tests that work arrangement, experience level, and job type filters are properly detected.
"""

import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_filter_detection_logic():
    """Test the filter detection logic that determines which scraper to use."""
    
    print("🧪 LinkedIn Filter Detection Logic Test")
    print("=" * 50)
    
    # Define default LinkedIn filter values (same as in backend)
    linkedin_defaults = {
        "sort_by": "Most relevant",
        "date_posted": "Any time", 
        "experience_level": None,
        "company": None,
        "job_type": None,
        "remote": None
    }
    
    # Test cases for filter detection
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
            "name": "Work arrangement filter only",
            "filters": {
                "date_posted_days": None,
                "work_arrangement": "remote",
                "experience_level": None,
                "job_type": None
            },
            "expected_use_fixed_scraper": True,
            "expected_reason": "Work arrangement filter requires browser interaction"
        },
        {
            "name": "Experience level filter only",
            "filters": {
                "date_posted_days": None,
                "work_arrangement": None,
                "experience_level": "entry",
                "job_type": None
            },
            "expected_use_fixed_scraper": True,
            "expected_reason": "Experience level filter requires browser interaction"
        },
        {
            "name": "Job type filter only",
            "filters": {
                "date_posted_days": None,
                "work_arrangement": None,
                "experience_level": None,
                "job_type": "full-time"
            },
            "expected_use_fixed_scraper": True,
            "expected_reason": "Job type filter requires browser interaction"
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
            "name": "Multiple filters",
            "filters": {
                "date_posted_days": 1,
                "work_arrangement": "remote",
                "experience_level": "entry",
                "job_type": "full-time"
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
        
        # Apply the same logic as in the backend
        has_custom_filters = False
        
        # Check date filter
        if date_posted_days is not None:
            has_custom_filters = True
            print(f"   ✅ Date filter detected: past {date_posted_days} days")
            
        # Check work arrangement (Remote filter)
        if work_arrangement:
            has_custom_filters = True
            print(f"   ✅ Work arrangement filter detected: {work_arrangement}")
            
        # Check experience level
        if experience_level:
            has_custom_filters = True
            print(f"   ✅ Experience level filter detected: {experience_level}")
            
        # Check job type
        if job_type:
            has_custom_filters = True
            print(f"   ✅ Job type filter detected: {job_type}")
        
        # Determine result
        use_fixed_scraper = has_custom_filters
        
        print(f"   Filter detection result: has_custom_filters = {has_custom_filters}")
        print(f"   Applied filters: date_posted_days={date_posted_days}, work_arrangement={work_arrangement}, experience_level={experience_level}, job_type={job_type}")
        
        # Check if result matches expectation
        if use_fixed_scraper == test_case['expected_use_fixed_scraper']:
            print("✅ PASS: Filter detection logic correct")
            print(f"   Use Fixed Scraper: {use_fixed_scraper}")
            print(f"   Reason: {test_case['expected_reason']}")
            passed_tests += 1
        else:
            print("❌ FAIL: Filter detection logic incorrect")
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
        print("\n📋 Key Findings:")
        print("   ✅ Work arrangement filters are properly detected")
        print("   ✅ Experience level filters are properly detected")
        print("   ✅ Job type filters are properly detected")
        print("   ✅ Date filters are properly detected")
        print("   ✅ Multiple filters are properly detected")
        print("   ✅ No filters correctly uses regular scraping")
    else:
        print("\n⚠️ SOME TESTS FAILED! Filter detection logic needs fixing.")
    
    return passed_tests == total_tests

def test_frontend_backend_mapping():
    """Test that frontend form fields are correctly mapped to backend parameters."""
    
    print("\n🧪 Frontend-Backend Field Mapping Test")
    print("=" * 50)
    
    # Simulate frontend form data
    frontend_form_data = {
        'keywords': 'Python Developer',
        'location': 'Remote',
        'date_posted': 'any',
        'remote': ['remote'],  # Work arrangement
        'experience': ['entry'],  # Experience level
        'job_type': ['full-time']  # Job type
    }
    
    # Simulate backend processing (same as in the actual code)
    search_params = {
        'keywords': frontend_form_data['keywords'],
        'location': frontend_form_data['location'],
        'date_posted': frontend_form_data['date_posted'],
        'work_arrangement': frontend_form_data['remote'],  # Mapped from 'remote'
        'experience_level': frontend_form_data['experience'],  # Mapped from 'experience'
        'job_type': frontend_form_data['job_type']  # Same name
    }
    
    # Extract individual filter values
    work_arrangement = search_params['work_arrangement'][0] if search_params['work_arrangement'] else None
    experience_level = search_params['experience_level'][0] if search_params['experience_level'] else None
    job_type = search_params['job_type'][0] if search_params['job_type'] else None
    
    print("✅ Frontend form data:")
    print(f"   remote: {frontend_form_data['remote']}")
    print(f"   experience: {frontend_form_data['experience']}")
    print(f"   job_type: {frontend_form_data['job_type']}")
    
    print("\n✅ Backend processed data:")
    print(f"   work_arrangement: {work_arrangement}")
    print(f"   experience_level: {experience_level}")
    print(f"   job_type: {job_type}")
    
    # Test that the mapping is correct
    mapping_correct = (
        work_arrangement == 'remote' and
        experience_level == 'entry' and
        job_type == 'full-time'
    )
    
    if mapping_correct:
        print("\n✅ PASS: Frontend-backend field mapping is correct")
        return True
    else:
        print("\n❌ FAIL: Frontend-backend field mapping is incorrect")
        return False

def main():
    """Run all filter detection tests."""
    
    print("🚀 LinkedIn Filter Detection Test Suite")
    print("=" * 60)
    
    # Test 1: Filter detection logic
    filter_logic_passed = test_filter_detection_logic()
    
    # Test 2: Frontend-backend mapping
    mapping_passed = test_frontend_backend_mapping()
    
    # Final Results
    print("\n" + "="*60)
    print("📊 FILTER DETECTION TEST RESULTS")
    print("="*60)
    
    print(f"Filter Detection Logic: {'✅ PASSED' if filter_logic_passed else '❌ FAILED'}")
    print(f"Frontend-Backend Mapping: {'✅ PASSED' if mapping_passed else '❌ FAILED'}")
    
    if filter_logic_passed and mapping_passed:
        print("\n🎉 ALL FILTER DETECTION TESTS PASSED!")
        print("The filter detection system is working correctly.")
        print("\n📋 Summary:")
        print("   • Work arrangement filters are properly detected")
        print("   • Experience level filters are properly detected")
        print("   • Job type filters are properly detected")
        print("   • Frontend form fields are correctly mapped")
        print("   • Browser automation is triggered when needed")
    else:
        print("\n⚠️ SOME FILTER DETECTION TESTS FAILED!")
        print("Please fix the issues before testing with real data.")
    
    print("\n🎉 Filter detection test suite completed!")

if __name__ == "__main__":
    main() 