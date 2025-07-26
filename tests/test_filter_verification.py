#!/usr/bin/env python3
"""
Test script to verify that LinkedIn filters are actually being applied.
This script will check the page content and URL after filter application.
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

def test_filter_verification():
    """Test that filters are actually being applied by checking page content."""
    
    print("🔍 LinkedIn Filter Verification Test")
    print("=" * 50)
    
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
        max_jobs_per_session=5,  # Limit for testing
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
    
    try:
        print("\n🚀 Starting filter verification test...")
        
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
        
        # Step 2: Check initial page state
        print("\n📋 Step 2: Checking initial page state...")
        initial_url = scraper.driver.current_url
        print(f"Initial URL: {initial_url}")
        
        # Check for any existing filter pills
        filter_pills = scraper.driver.find_elements("css selector", ".artdeco-pill")
        print(f"Initial filter pills found: {len(filter_pills)}")
        for pill in filter_pills:
            try:
                print(f"  - {pill.text}")
            except:
                pass
        
        # Step 3: Apply filters
        print("\n📋 Step 3: Applying filters...")
        print("🎯 Applying: Date=Past 24 hours, Experience=Entry level, Job Type=Full-time")
        
        success = scraper.apply_all_filters(
            date_posted_days=1,
            experience_level="Entry level",
            job_type="Full-time"
        )
        
        if not success:
            print("❌ Filter application failed")
            return
        
        print("✅ Filter application completed")
        
        # Step 4: Check final page state
        print("\n📋 Step 4: Checking final page state...")
        final_url = scraper.driver.current_url
        print(f"Final URL: {final_url}")
        
        # Check if URL changed
        if initial_url != final_url:
            print("✅ URL changed after filter application")
        else:
            print("⚠️ URL did not change (filters may not modify URL)")
        
        # Check for filter pills again
        filter_pills = scraper.driver.find_elements("css selector", ".artdeco-pill")
        print(f"Final filter pills found: {len(filter_pills)}")
        for pill in filter_pills:
            try:
                print(f"  - {pill.text}")
            except:
                pass
        
        # Check for specific filter indicators in the page
        page_source = scraper.driver.page_source.lower()
        
        # Check for date filter indicators
        if "past 24 hours" in page_source or "past 1 day" in page_source:
            print("✅ Date filter indicator found in page")
        else:
            print("❌ Date filter indicator not found in page")
        
        # Check for experience level indicators
        if "entry level" in page_source:
            print("✅ Experience level filter indicator found in page")
        else:
            print("❌ Experience level filter indicator not found in page")
        
        # Check for job type indicators
        if "full-time" in page_source:
            print("✅ Job type filter indicator found in page")
        else:
            print("❌ Job type filter indicator not found in page")
        
        # Step 5: Check job results
        print("\n📋 Step 5: Checking job results...")
        job_cards = scraper.driver.find_elements("css selector", ".job-card-container")
        print(f"Job cards found: {len(job_cards)}")
        
        if len(job_cards) > 0:
            print("✅ Jobs are displayed")
            
            # Check first few job cards for filter compliance
            for i, card in enumerate(job_cards[:3]):
                try:
                    card_text = card.text.lower()
                    print(f"\nJob {i+1}:")
                    
                    # Check if it mentions entry level
                    if "entry level" in card_text or "junior" in card_text:
                        print("  ✅ Appears to be entry level")
                    else:
                        print("  ❓ Level not clearly indicated")
                    
                    # Check if it mentions full-time
                    if "full-time" in card_text or "full time" in card_text:
                        print("  ✅ Appears to be full-time")
                    else:
                        print("  ❓ Job type not clearly indicated")
                        
                except Exception as e:
                    print(f"  ❌ Error checking job card: {e}")
        else:
            print("❌ No job cards found")
        
        print("\n🎉 Filter verification test completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        
    finally:
        # Cleanup
        try:
            scraper.cleanup()
        except:
            pass

if __name__ == "__main__":
    test_filter_verification() 