#!/usr/bin/env python3
"""
Test script to verify that FixedLinkedInScraper can be properly imported and instantiated.
This tests the actual scraper creation that should happen when filters are detected.
"""

import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_scraper_import():
    """Test that FixedLinkedInScraper can be imported successfully."""
    
    print("🧪 FixedLinkedInScraper Import Test")
    print("=" * 50)
    
    try:
        from src.scrapers.linkedin_scraper_fixed import FixedLinkedInScraper
        print("✅ SUCCESS: FixedLinkedInScraper imported successfully")
        return True
    except ImportError as e:
        print(f"❌ FAIL: Failed to import FixedLinkedInScraper: {e}")
        return False
    except Exception as e:
        print(f"❌ FAIL: Unexpected error importing FixedLinkedInScraper: {e}")
        return False

def test_scraper_instantiation():
    """Test that FixedLinkedInScraper can be instantiated with proper config."""
    
    print("\n🧪 FixedLinkedInScraper Instantiation Test")
    print("=" * 50)
    
    try:
        # Import required modules
        from src.scrapers.linkedin_scraper_fixed import FixedLinkedInScraper
        from src.utils.session_manager import SessionManager
        from src.scrapers.base_scraper import ScrapingConfig
        
        print("✅ SUCCESS: All required modules imported")
        
        # Create session manager
        session_manager = SessionManager()
        print("✅ SUCCESS: SessionManager created")
        
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
        print("✅ SUCCESS: ScrapingConfig created")
        
        # Try to instantiate the scraper
        scraper = FixedLinkedInScraper(config, session_manager)
        print("✅ SUCCESS: FixedLinkedInScraper instantiated successfully")
        
        # Check that the scraper has the required methods
        required_methods = [
            'scrape_jobs_with_enhanced_date_filter',
            '_apply_date_filter_in_modal',
            '_apply_work_arrangement_in_modal',
            '_apply_experience_level_in_modal',
            '_apply_job_type_in_modal',
            '_find_and_click_filter_option'
        ]
        
        missing_methods = []
        for method_name in required_methods:
            if hasattr(scraper, method_name):
                print(f"   ✅ Method '{method_name}' found")
            else:
                print(f"   ❌ Method '{method_name}' missing")
                missing_methods.append(method_name)
        
        if missing_methods:
            print(f"\n⚠️ WARNING: {len(missing_methods)} required methods are missing")
            return False
        else:
            print(f"\n✅ SUCCESS: All {len(required_methods)} required methods are present")
            return True
            
    except Exception as e:
        print(f"❌ FAIL: Failed to instantiate FixedLinkedInScraper: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_filter_workflow_simulation():
    """Simulate the complete filter detection and scraper selection workflow."""
    
    print("\n🧪 Complete Filter Workflow Simulation")
    print("=" * 50)
    
    # Simulate the exact workflow from the backend
    try:
        # Step 1: Simulate frontend form data
        frontend_form_data = {
            'keywords': 'Python Developer',
            'location': 'Remote',
            'date_posted': 'any',
            'work_arrangement': ['remote'],  # This should trigger browser
            'experience_level': [],  # Empty
            'job_type': []  # Empty
        }
        
        print("✅ Step 1: Frontend form data simulated")
        print(f"   Keywords: {frontend_form_data['keywords']}")
        print(f"   Location: {frontend_form_data['location']}")
        print(f"   Work Arrangement: {frontend_form_data['work_arrangement']}")
        print(f"   Experience Level: {frontend_form_data['experience_level']}")
        print(f"   Job Type: {frontend_form_data['job_type']}")
        
        # Step 2: Extract filter values (same as backend)
        work_arrangement = frontend_form_data['work_arrangement'][0] if frontend_form_data['work_arrangement'] else None
        experience_level = frontend_form_data['experience_level'][0] if frontend_form_data['experience_level'] else None
        job_type = frontend_form_data['job_type'][0] if frontend_form_data['job_type'] else None
        
        print("\n✅ Step 2: Filter values extracted")
        print(f"   work_arrangement: {work_arrangement}")
        print(f"   experience_level: {experience_level}")
        print(f"   job_type: {job_type}")
        
        # Step 3: Apply filter detection logic (same as backend)
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
        
        print(f"\n✅ Step 3: Filter detection result: has_custom_filters = {has_custom_filters}")
        
        # Step 4: Determine scraper selection (same as backend)
        if has_custom_filters:
            print("\n✅ Step 4: Custom filters detected - should use FixedLinkedInScraper")
            
            # Try to import and instantiate the scraper
            from src.scrapers.linkedin_scraper_fixed import FixedLinkedInScraper
            from src.utils.session_manager import SessionManager
            from src.scrapers.base_scraper import ScrapingConfig
            
            session_manager = SessionManager()
            config = ScrapingConfig(
                max_jobs_per_session=50,
                delay_min=2.0,
                delay_max=3.0,
                max_retries=3,
                page_load_timeout=30,
                site_name="linkedin",
                base_url="https://www.linkedin.com"
            )
            
            scraper = FixedLinkedInScraper(config, session_manager)
            print("   ✅ SUCCESS: FixedLinkedInScraper created successfully")
            print("   ✅ This means a browser window should open for authentication")
            
            return True
        else:
            print("\n✅ Step 4: No custom filters - should use JobLinkProcessor")
            print("   ✅ This means no browser window should open")
            return True
            
    except Exception as e:
        print(f"❌ FAIL: Workflow simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all scraper instantiation tests."""
    
    print("🚀 FixedLinkedInScraper Instantiation Test Suite")
    print("=" * 60)
    
    # Test 1: Import test
    import_passed = test_scraper_import()
    
    # Test 2: Instantiation test
    instantiation_passed = test_scraper_instantiation()
    
    # Test 3: Workflow simulation
    workflow_passed = test_filter_workflow_simulation()
    
    # Final Results
    print("\n" + "="*60)
    print("📊 SCRAPER INSTANTIATION TEST RESULTS")
    print("="*60)
    
    print(f"Import Test: {'✅ PASSED' if import_passed else '❌ FAILED'}")
    print(f"Instantiation Test: {'✅ PASSED' if instantiation_passed else '❌ FAILED'}")
    print(f"Workflow Simulation: {'✅ PASSED' if workflow_passed else '❌ FAILED'}")
    
    if import_passed and instantiation_passed and workflow_passed:
        print("\n🎉 ALL SCRAPER INSTANTIATION TESTS PASSED!")
        print("The FixedLinkedInScraper is ready to be used when filters are detected.")
        print("\n📋 Summary:")
        print("   • FixedLinkedInScraper can be imported successfully")
        print("   • FixedLinkedInScraper can be instantiated with proper config")
        print("   • All required methods are present")
        print("   • Filter workflow correctly triggers scraper creation")
        print("   • Browser automation should work when filters are applied")
    else:
        print("\n⚠️ SOME SCRAPER INSTANTIATION TESTS FAILED!")
        print("Please fix the issues before testing with real data.")
    
    print("\n🎉 Scraper instantiation test suite completed!")

if __name__ == "__main__":
    main() 