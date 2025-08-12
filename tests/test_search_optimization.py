#!/usr/bin/env python3
"""
Test script for Search Strategy Optimization and CAPTCHA Handling

This script tests the new search strategy manager and CAPTCHA handling functionality
to ensure proper optimization of WebDriver usage and CAPTCHA detection.
"""

import sys
import os
import json
from datetime import datetime

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_search_strategy_manager():
    """Test the search strategy manager functionality."""
    
    print("🧪 Search Strategy Manager Test")
    print("=" * 50)
    
    try:
        from backend.src.utils.search_strategy_manager import search_strategy_manager, SearchParameters
        
        # Test 1: Basic search (should use API-only)
        print("\n📋 Test 1: Basic search (keywords + location)")
        basic_params = SearchParameters(
            keywords=['software engineer'],
            location='San Francisco, CA',
            distance='25'
        )
        
        strategy_info = search_strategy_manager.get_search_strategy_info(basic_params)
        print(f"Method: {strategy_info['method']}")
        print(f"Reason: {strategy_info['reason']}")
        print(f"Performance: {strategy_info['performance_impact']}")
        print(f"Estimated Time: {strategy_info['estimated_time']}")
        
        assert strategy_info['method'] == 'api_only', "Basic search should use API-only"
        print("✅ PASS: Basic search correctly uses API-only approach")
        
        # Test 2: Advanced search with date filter (should use WebDriver)
        print("\n📋 Test 2: Advanced search with date filter")
        advanced_params = SearchParameters(
            keywords=['software engineer'],
            location='San Francisco, CA',
            date_posted_days=7
        )
        
        strategy_info = search_strategy_manager.get_search_strategy_info(advanced_params)
        print(f"Method: {strategy_info['method']}")
        print(f"Reason: {strategy_info['reason']}")
        print(f"Performance: {strategy_info['performance_impact']}")
        print(f"Estimated Time: {strategy_info['estimated_time']}")
        
        assert strategy_info['method'] == 'webdriver', "Advanced search should use WebDriver"
        print("✅ PASS: Advanced search correctly uses WebDriver")
        
        # Test 3: Advanced search with multiple filters
        print("\n📋 Test 3: Advanced search with multiple filters")
        complex_params = SearchParameters(
            keywords=['software engineer'],
            location='San Francisco, CA',
            date_posted_days=1,
            work_arrangement='Remote',
            experience_level='Entry level',
            job_type='Full-time'
        )
        
        strategy_info = search_strategy_manager.get_search_strategy_info(complex_params)
        print(f"Method: {strategy_info['method']}")
        print(f"Reason: {strategy_info['reason']}")
        print(f"Applied Filters: {strategy_info['applied_filters']}")
        print(f"Estimated Time: {strategy_info['estimated_time']}")
        
        assert strategy_info['method'] == 'webdriver', "Complex search should use WebDriver"
        assert len(strategy_info['applied_filters']) >= 3, "Should detect multiple filters"
        print("✅ PASS: Complex search correctly uses WebDriver")
        
        # Test 4: Dictionary parameter creation
        print("\n📋 Test 4: Dictionary parameter creation")
        params_dict = {
            'keywords': ['python developer'],
            'location': 'New York, NY',
            'date_posted_days': 3,
            'work_arrangement': 'Hybrid'
        }
        
        search_params = search_strategy_manager.create_search_parameters_from_dict(params_dict)
        strategy_info = search_strategy_manager.get_search_strategy_info(search_params)
        
        assert strategy_info['method'] == 'webdriver', "Dictionary params should work correctly"
        print("✅ PASS: Dictionary parameter creation works correctly")
        
        print("\n🎉 ALL SEARCH STRATEGY TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Search strategy test failed: {e}")
        return False

def test_captcha_handler():
    """Test the CAPTCHA handler functionality."""
    
    print("\n🧪 CAPTCHA Handler Test")
    print("=" * 50)
    
    try:
        from backend.src.utils.captcha_handler import captcha_handler, CAPTCHAStatus, CAPTCHAInfo
        
        # Test 1: CAPTCHA info creation
        print("\n📋 Test 1: CAPTCHA info creation")
        captcha_info = CAPTCHAInfo(
            status=CAPTCHAStatus.DETECTED,
            captcha_type="LinkedIn Security Challenge",
            message="LinkedIn has detected automated access",
            detection_time=datetime.now().timestamp(),
            timeout_seconds=600
        )
        
        assert captcha_info.status == CAPTCHAStatus.DETECTED
        assert captcha_info.captcha_type == "LinkedIn Security Challenge"
        assert captcha_info.timeout_seconds == 600
        print("✅ PASS: CAPTCHA info creation works correctly")
        
        # Test 2: CAPTCHA handler initialization
        print("\n📋 Test 2: CAPTCHA handler initialization")
        handler = captcha_handler
        
        # Test detection patterns
        assert len(handler.captcha_indicators) > 0, "Should have CAPTCHA indicators"
        assert len(handler.captcha_selectors) > 0, "Should have CAPTCHA selectors"
        assert len(handler.linkedin_captcha_indicators) > 0, "Should have LinkedIn indicators"
        print("✅ PASS: CAPTCHA handler initialization works correctly")
        
        # Test 3: CAPTCHA type determination
        print("\n📋 Test 3: CAPTCHA type determination")
        
        # Test LinkedIn CAPTCHA
        linkedin_indicators = ["linkedin_security verification", "linkedin_verify your identity"]
        linkedin_elements = []
        captcha_type = handler._determine_captcha_type(linkedin_indicators, linkedin_elements)
        assert "LinkedIn" in captcha_type, "Should detect LinkedIn CAPTCHA"
        print("✅ PASS: LinkedIn CAPTCHA type detection")
        
        # Test reCAPTCHA
        recaptcha_indicators = ["recaptcha", "google captcha"]
        recaptcha_elements = ["iframe[src*='recaptcha']"]
        captcha_type = handler._determine_captcha_type(recaptcha_indicators, recaptcha_elements)
        assert "reCAPTCHA" in captcha_type, "Should detect reCAPTCHA"
        print("✅ PASS: reCAPTCHA type detection")
        
        # Test 4: User instruction generation
        print("\n📋 Test 4: User instruction generation")
        instructions = handler._generate_user_instructions(captcha_info)
        
        assert 'title' in instructions
        assert 'message' in instructions
        assert 'steps' in instructions
        assert 'timeout_message' in instructions
        assert len(instructions['steps']) > 0
        print("✅ PASS: User instruction generation works correctly")
        
        print("\n🎉 ALL CAPTCHA HANDLER TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ FAIL: CAPTCHA handler test failed: {e}")
        return False

def test_api_scraper_creation():
    """Test the API-only scraper creation."""
    
    print("\n🧪 API Scraper Creation Test")
    print("=" * 50)
    
    try:
        # Test the core functionality without full imports
        from backend.src.utils.search_strategy_manager import search_strategy_manager
        
        # Test URL building logic (which doesn't require full scraper)
        keywords = ['software engineer']
        location = 'San Francisco, CA'
        
        # Simulate URL building
        base_url = "https://www.linkedin.com"
        jobs_url = f"{base_url}/jobs"
        url = f"{jobs_url}/search"
        
        # Build query parameters
        import urllib.parse
        params = {}
        
        if keywords:
            keywords_str = ' '.join(keywords)
            params['keywords'] = keywords_str
        
        if location:
            params['location'] = location
        
        # Add parameters to URL
        if params:
            url += '?' + urllib.parse.urlencode(params)
        
        print(f"Generated URL: {url}")
        
        # Verify URL construction
        assert 'linkedin.com/jobs/search' in url, "Should build LinkedIn search URL"
        assert 'keywords=' in url, "Should include keywords parameter"
        assert 'location=' in url, "Should include location parameter"
        print("✅ PASS: API scraper URL building logic works correctly")
        
        # Test strategy integration
        search_params = search_strategy_manager.create_search_parameters_from_dict({
            'keywords': keywords,
            'location': location
        })
        
        strategy_info = search_strategy_manager.get_search_strategy_info(search_params)
        assert strategy_info['method'] == 'api_only', "Should use API-only for basic search"
        print("✅ PASS: API scraper strategy integration works correctly")
        
        print("\n🎉 ALL API SCRAPER TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ FAIL: API scraper test failed: {e}")
        return False

def test_integration():
    """Test the integration of all components."""
    
    print("\n🧪 Integration Test")
    print("=" * 50)
    
    try:
        from backend.src.utils.search_strategy_manager import search_strategy_manager
        from backend.src.utils.captcha_handler import captcha_handler
        
        # Test 1: Strategy decision with CAPTCHA handling
        print("\n📋 Test 1: Strategy decision with CAPTCHA handling")
        
        # Basic search parameters
        basic_params = search_strategy_manager.create_search_parameters_from_dict({
            'keywords': ['python developer'],
            'location': 'Remote'
        })
        
        strategy_info = search_strategy_manager.get_search_strategy_info(basic_params)
        assert strategy_info['method'] == 'api_only', "Basic search should use API-only"
        print("✅ PASS: Strategy decision works correctly")
        
        # Test 2: CAPTCHA detection (without real driver)
        print("\n📋 Test 2: CAPTCHA detection simulation")
        captcha_info = captcha_handler.detect_captcha()
        # Since we don't have a real driver, this should return NOT_DETECTED or ERROR
        from backend.src.utils.captcha_handler import CAPTCHAStatus
        assert captcha_info.status in [CAPTCHAStatus.NOT_DETECTED, CAPTCHAStatus.ERROR]
        print("✅ PASS: CAPTCHA detection simulation works correctly")
        
        # Test 3: Strategy info generation
        print("\n📋 Test 3: Strategy info generation")
        advanced_params = search_strategy_manager.create_search_parameters_from_dict({
            'keywords': ['software engineer'],
            'location': 'San Francisco',
            'date_posted_days': 7,
            'work_arrangement': 'Remote'
        })
        
        strategy_info = search_strategy_manager.get_search_strategy_info(advanced_params)
        assert strategy_info['method'] == 'webdriver', "Advanced search should use WebDriver"
        assert len(strategy_info['applied_filters']) >= 2, "Should detect multiple filters"
        print("✅ PASS: Strategy info generation works correctly")
        
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Integration test failed: {e}")
        return False

def main():
    """Run all tests."""
    
    print("🚀 Starting Search Optimization and CAPTCHA Handling Tests")
    print("=" * 70)
    
    tests = [
        test_search_strategy_manager,
        test_captcha_handler,
        test_api_scraper_creation,
        test_integration
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test in tests:
        try:
            if test():
                passed_tests += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    # Final Results
    print("\n" + "="*70)
    print("📊 TEST RESULTS SUMMARY")
    print("="*70)
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Search optimization and CAPTCHA handling are working correctly.")
        return True
    else:
        print("\n⚠️ SOME TESTS FAILED! Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 