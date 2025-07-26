#!/usr/bin/env python3
"""
Test script to verify the improved CAPTCHA handling flow.
This script tests the exact flow that should happen when a user applies filters.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.session_manager import SessionManager
from src.config.config_manager import ConfigurationManager
from src.utils.logger import JobAutomationLogger

def test_captcha_flow():
    """Test the CAPTCHA handling flow."""
    
    # Initialize logger
    logger = JobAutomationLogger()
    
    # Initialize configuration manager
    config_manager = ConfigurationManager()
    
    # Get LinkedIn credentials
    linkedin_config = config_manager.get_linkedin_settings()
    username = linkedin_config.username
    password = linkedin_config.password
    
    print(f"Testing CAPTCHA flow with username: {username}")
    print("This test will:")
    print("1. Create a session manager")
    print("2. Open a browser")
    print("3. Navigate to LinkedIn login")
    print("4. Fill in credentials")
    print("5. Click login")
    print("6. Check for CAPTCHA and wait for user input if detected")
    print("7. Continue with the process")
    print()
    
    # Create session manager
    session_manager = SessionManager()
    
    try:
        # Create a session
        session_id = session_manager.create_session("captcha_test")
        print(f"Created session: {session_id}")
        
        # Authenticate (this should handle CAPTCHA if detected)
        print("Starting authentication...")
        success = session_manager.authenticate(username, password)
        
        if success:
            print("✅ Authentication successful!")
            
            # Test navigation to a search URL
            search_url = "https://www.linkedin.com/jobs/search/?keywords=python&location=remote"
            print(f"Navigating to search URL: {search_url}")
            session_manager.driver.get(search_url)
            
            print("✅ Successfully navigated to search results!")
            print("The browser should now be ready for filter application.")
            
        else:
            print("❌ Authentication failed")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        
    finally:
        # Keep the browser open for manual inspection
        print("\nTest completed. Browser will remain open for manual inspection.")
        print("Press Enter to close the browser...")
        input()

if __name__ == "__main__":
    test_captcha_flow() 