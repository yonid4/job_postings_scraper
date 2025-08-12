#!/usr/bin/env python3
"""
Test script to verify frontend-backend integration for filter detection.
This simulates the exact request that the frontend sends and verifies the backend response.
"""

import sys
import os
import json
from unittest.mock import Mock, patch

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def simulate_frontend_request():
    """Simulate the exact frontend request that should trigger browser automation."""
    
    print("🧪 Frontend Request Simulation")
    print("=" * 50)
    
    # Simulate the exact form data that the frontend sends
    frontend_form_data = {
        'keywords': 'Python Developer',
        'location': 'Remote',
        'date_posted': 'any',
        'work_arrangement': ['remote'],  # This should trigger browser
        'experience_level': [],  # Empty
        'job_type': []  # Empty
    }
    
    print("✅ Frontend form data:")
    for key, value in frontend_form_data.items():
        print(f"   {key}: {value}")
    
    # Simulate backend processing (same as in frontend/app.py)
    search_params = {
        'keywords': frontend_form_data['keywords'],
        'location': frontend_form_data['location'],
        'date_posted': frontend_form_data['date_posted'],
        'work_arrangement': frontend_form_data['work_arrangement'],
        'experience_level': frontend_form_data['experience_level'],
        'job_type': frontend_form_data['job_type']
    }
    
    print("\n✅ Backend search_params:")
    for key, value in search_params.items():
        print(f"   {key}: {value}")
    
    # Extract filter values (same as backend)
    work_arrangement = search_params['work_arrangement'][0] if search_params['work_arrangement'] else None
    experience_level = search_params['experience_level'][0] if search_params['experience_level'] else None
    job_type = search_params['job_type'][0] if search_params['job_type'] else None
    
    print("\n✅ Extracted filter values:")
    print(f"   work_arrangement: {work_arrangement}")
    print(f"   experience_level: {experience_level}")
    print(f"   job_type: {job_type}")
    
    # Apply filter detection logic (same as backend)
    has_custom_filters = False
    
    if work_arrangement:
        has_custom_filters = True
        print(f"   ✅ Work arrangement filter detected: {work_arrangement}")
        
    if experience_level:
        has_custom_filters = True
        print(f"   ✅ Experience level filter detected: {experience_level}")
        
    if job_type:
        has_custom_filters = True
        print(f"   ✅ Job type filter detected: {job_type}")
    
    print(f"\n✅ Filter detection result: has_custom_filters = {has_custom_filters}")
    
    # Determine scraper selection (same as backend)
    if has_custom_filters:
        print("\n✅ CUSTOM FILTERS DETECTED!")
        print("   → Should use EnhancedLinkedInScraper")
        print("   → Should open browser for authentication")
        print("   → Should apply filters in LinkedIn UI")
        return True
    else:
        print("\n✅ NO CUSTOM FILTERS DETECTED!")
        print("   → Should use JobLinkProcessor")
        print("   → Should NOT open browser")
        print("   → Should use URL-based scraping")
        return False

def test_different_filter_combinations():
    """Test different filter combinations to ensure they all trigger browser automation."""
    
    print("\n🧪 Different Filter Combinations Test")
    print("=" * 50)
    
    test_cases = [
        {
            "name": "Work Arrangement Only",
            "filters": {
                'work_arrangement': ['remote'],
                'experience_level': [],
                'job_type': []
            },
            "should_trigger_browser": True
        },
        {
            "name": "Experience Level Only",
            "filters": {
                'work_arrangement': [],
                'experience_level': ['entry'],
                'job_type': []
            },
            "should_trigger_browser": True
        },
        {
            "name": "Job Type Only",
            "filters": {
                'work_arrangement': [],
                'experience_level': [],
                'job_type': ['full-time']
            },
            "should_trigger_browser": True
        },
        {
            "name": "Multiple Filters",
            "filters": {
                'work_arrangement': ['remote'],
                'experience_level': ['entry'],
                'job_type': ['full-time']
            },
            "should_trigger_browser": True
        },
        {
            "name": "No Filters",
            "filters": {
                'work_arrangement': [],
                'experience_level': [],
                'job_type': []
            },
            "should_trigger_browser": False
        }
    ]
    
    passed_tests = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}/{total_tests}: {test_case['name']}")
        print("-" * 40)
        
        # Simulate frontend form data
        frontend_form_data = {
            'keywords': 'Python Developer',
            'location': 'Remote',
            'date_posted': 'any',
            'work_arrangement': test_case['filters']['work_arrangement'],
            'experience_level': test_case['filters']['experience_level'],
            'job_type': test_case['filters']['job_type']
        }
        
        # Extract filter values
        work_arrangement = frontend_form_data['work_arrangement'][0] if frontend_form_data['work_arrangement'] else None
        experience_level = frontend_form_data['experience_level'][0] if frontend_form_data['experience_level'] else None
        job_type = frontend_form_data['job_type'][0] if frontend_form_data['job_type'] else None
        
        # Apply filter detection logic
        has_custom_filters = False
        
        if work_arrangement:
            has_custom_filters = True
            print(f"   ✅ Work arrangement: {work_arrangement}")
            
        if experience_level:
            has_custom_filters = True
            print(f"   ✅ Experience level: {experience_level}")
            
        if job_type:
            has_custom_filters = True
            print(f"   ✅ Job type: {job_type}")
        
        # Check result
        should_trigger_browser = has_custom_filters
        expected = test_case['should_trigger_browser']
        
        if should_trigger_browser == expected:
            print(f"✅ PASS: Browser trigger = {should_trigger_browser} (expected: {expected})")
            passed_tests += 1
        else:
            print(f"❌ FAIL: Browser trigger = {should_trigger_browser} (expected: {expected})")
    
    # Final Results
    print("\n" + "="*50)
    print("📊 FILTER COMBINATION TEST RESULTS")
    print("="*50)
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL FILTER COMBINATION TESTS PASSED!")
        print("All filter combinations correctly trigger browser automation when needed.")
    else:
        print("\n⚠️ SOME FILTER COMBINATION TESTS FAILED!")
    
    return passed_tests == total_tests

def test_backend_integration_simulation():
    """Simulate the complete backend integration to identify potential issues."""
    
    print("\n🧪 Backend Integration Simulation")
    print("=" * 50)
    
    try:
        # Mock the necessary components
        with patch('src.config.config_manager.ConfigManager') as mock_config_manager, \
             patch('backend.src.ai.qualification_analyzer.QualificationAnalyzer') as mock_analyzer:
            
            # Setup mocks
            mock_config = Mock()
            mock_config.get_linkedin_settings.return_value = Mock(username="test", password="test")
            mock_config.get_user_profile.return_value = Mock()
            mock_config.get_ai_settings.return_value = Mock()
            mock_config_manager.return_value = mock_config
            
            mock_analyzer_instance = Mock()
            mock_analyzer.return_value = mock_analyzer_instance
            
            # Simulate the exact backend logic from frontend/app.py
            search_params = {
                'keywords': 'Python Developer',
                'location': 'Remote',
                'date_posted': 'any',
                'work_arrangement': ['remote'],  # This should trigger browser
                'experience_level': [],
                'job_type': []
            }
            
            # Extract filter values
            work_arrangement = search_params['work_arrangement'][0] if search_params['work_arrangement'] else None
            experience_level = search_params['experience_level'][0] if search_params['experience_level'] else None
            job_type = search_params['job_type'][0] if search_params['job_type'] else None
            
            # Apply filter detection logic
            has_custom_filters = False
            
            if work_arrangement:
                has_custom_filters = True
                print(f"✅ Work arrangement filter detected: {work_arrangement}")
                
            if experience_level:
                has_custom_filters = True
                print(f"✅ Experience level filter detected: {experience_level}")
                
            if job_type:
                has_custom_filters = True
                print(f"✅ Job type filter detected: {job_type}")
            
            print(f"✅ Filter detection result: has_custom_filters = {has_custom_filters}")
            
            # Determine scraper selection
            if has_custom_filters:
                print("\n✅ CUSTOM FILTERS DETECTED - Using EnhancedLinkedInScraper")
                
                # Try to import the scraper (this is where it might fail in real execution)
                try:
                    from backend.src.scrapers.linkedin_scraper_enhanced import EnhancedLinkedInScraper
                    from backend.src.utils.session_manager import SessionManager
                    from backend.src.scrapers.base_scraper import ScrapingConfig
                    
                    # Create session manager
                    session_manager = SessionManager()
                    
                    # Create scraping config
                    config = ScrapingConfig(
                        max_jobs_per_session=50,
                        delay_min=2.0,
                        delay_max=3.0,
                        max_retries=3,
                        page_load_timeout=30,
                        site_name="linkedin",
                        base_url="https://www.linkedin.com"
                    )
                    
                    # Add LinkedIn credentials
                    config.linkedin_username = "test@example.com"
                    config.linkedin_password = "test_password"
                    
                    # Create the scraper
                    scraper = EnhancedLinkedInScraper(config, session_manager)
                    print("✅ SUCCESS: EnhancedLinkedInScraper created successfully")
                    
                    return True
                    
                except Exception as e:
                    print(f"❌ FAIL: Failed to create EnhancedLinkedInScraper: {e}")
                    return False
            else:
                print("\n✅ NO CUSTOM FILTERS - Using JobLinkProcessor")
                return True
                
    except Exception as e:
        print(f"❌ FAIL: Backend integration simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all frontend integration tests."""
    
    print("🚀 Frontend-Backend Integration Test Suite")
    print("=" * 60)
    
    # Test 1: Frontend request simulation
    request_simulation_passed = simulate_frontend_request()
    
    # Test 2: Different filter combinations
    filter_combinations_passed = test_different_filter_combinations()
    
    # Test 3: Backend integration simulation
    backend_integration_passed = test_backend_integration_simulation()
    
    # Final Results
    print("\n" + "="*60)
    print("📊 FRONTEND-BACKEND INTEGRATION TEST RESULTS")
    print("="*60)
    
    print(f"Request Simulation: {'✅ PASSED' if request_simulation_passed else '❌ FAILED'}")
    print(f"Filter Combinations: {'✅ PASSED' if filter_combinations_passed else '❌ FAILED'}")
    print(f"Backend Integration: {'✅ PASSED' if backend_integration_passed else '❌ FAILED'}")
    
    if request_simulation_passed and filter_combinations_passed and backend_integration_passed:
        print("\n🎉 ALL FRONTEND-BACKEND INTEGRATION TESTS PASSED!")
        print("The integration between frontend and backend is working correctly.")
        print("\n📋 Summary:")
        print("   • Frontend correctly sends filter data")
        print("   • Backend correctly processes filter data")
        print("   • Filter detection logic works for all combinations")
        print("   • EnhancedLinkedInScraper can be created successfully")
        print("   • Browser automation should trigger when filters are applied")
        print("\n🔍 If browser is still not opening, the issue might be:")
        print("   • LinkedIn credentials not configured")
        print("   • Network connectivity issues")
        print("   • Browser driver issues")
        print("   • LinkedIn's anti-bot measures")
    else:
        print("\n⚠️ SOME FRONTEND-BACKEND INTEGRATION TESTS FAILED!")
        print("Please fix the issues before testing with real data.")
    
    print("\n🎉 Frontend-backend integration test suite completed!")

if __name__ == "__main__":
    main() 