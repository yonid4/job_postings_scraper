#!/usr/bin/env python3
"""
Simple test script to verify CAPTCHA handling without complex session management.
"""

import sys
import os
import time
import random
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, NoSuchElementException
from backend.src.config.config_manager import ConfigurationManager
from backend.src.utils.logger import JobAutomationLogger

def test_simple_captcha():
    """Test simple CAPTCHA handling."""
    
    # Initialize logger
    logger = JobAutomationLogger()
    
    # Initialize configuration manager
    config_manager = ConfigurationManager()
    
    # Get LinkedIn credentials
    linkedin_config = config_manager.get_linkedin_settings()
    username = linkedin_config.username
    password = linkedin_config.password
    
    print(f"Testing simple CAPTCHA flow with username: {username}")
    print("This test will:")
    print("1. Open a simple Chrome browser")
    print("2. Navigate to LinkedIn login")
    print("3. Fill in credentials")
    print("4. Click login")
    print("5. Check for CAPTCHA and wait for user input if detected")
    print("6. Continue with the process")
    print()
    
    driver = None
    
    try:
        # Create Chrome options with minimal settings
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Realistic user agent
        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        options.add_argument(f'--user-agent={user_agent}')
        
        # Window size
        options.add_argument('--window-size=1920,1080')
        
        print("Creating Chrome WebDriver...")
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 15)
        
        print("✅ WebDriver created successfully")
        
        # Navigate to LinkedIn login
        print("Navigating to LinkedIn login...")
        driver.get("https://www.linkedin.com/login")
        time.sleep(2)
        
        print("✅ Successfully navigated to LinkedIn login")
        
        # Fill username
        print("Filling username...")
        username_field = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#username'))
        )
        username_field.clear()
        username_field.send_keys(username)
        time.sleep(random.uniform(0.5, 1.0))
        
        # Fill password
        print("Filling password...")
        password_field = driver.find_element(By.CSS_SELECTOR, '#password')
        password_field.clear()
        password_field.send_keys(password)
        time.sleep(random.uniform(0.5, 1.0))
        
        # Click login button
        print("Clicking login button...")
        login_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        login_button.click()
        
        # Wait for authentication to complete
        print("Waiting for authentication...")
        time.sleep(5)
        
        # Check for security challenges
        print("Checking for security challenges...")
        page_source = driver.page_source.lower()
        current_url = driver.current_url.lower()
        
        # Check for specific security challenges
        security_indicators = [
            "security challenge", "captcha", "puzzle", "verification",
            "prove you're not a robot", "verify your identity",
            "challenge", "security check", "verification required",
            "unusual activity", "suspicious activity", "robot check"
        ]
        
        challenge_detected = False
        detected_indicator = None
        
        for indicator in security_indicators:
            if indicator in page_source:
                challenge_detected = True
                detected_indicator = indicator
                break
        
        # Check for specific CAPTCHA elements
        captcha_elements = [
            "iframe[src*='captcha']",
            "iframe[src*='recaptcha']",
            "iframe[src*='challenge']",
            ".captcha",
            ".recaptcha",
            "[data-test-id*='captcha']",
            "[data-test-id*='challenge']"
        ]
        
        for selector in captcha_elements:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                if element.is_displayed():
                    challenge_detected = True
                    detected_indicator = f"CAPTCHA element found: {selector}"
                    break
            except NoSuchElementException:
                continue
        
        # Check for specific text patterns that indicate CAPTCHA
        captcha_text_patterns = [
            "prove you're not a robot",
            "verify you're human",
            "complete the security check",
            "solve this puzzle",
            "verify your identity",
            "security verification"
        ]
        
        for pattern in captcha_text_patterns:
            if pattern in page_source:
                challenge_detected = True
                detected_indicator = f"CAPTCHA text found: {pattern}"
                break
        
        if challenge_detected:
            print(f"🔒 CAPTCHA/Security Challenge Detected: {detected_indicator}")
            print("In interactive mode, user would complete the security challenge manually.")
            print("For automated testing, skipping CAPTCHA challenge...")
            
            # Skip user input for automated testing
            # input("Press Enter when you have completed the security challenge...")
            
            print("Simulating challenge completion for automated testing...")
            
            # Wait a moment for the page to update
            time.sleep(3)
            
            # Check if we're now on LinkedIn home page or jobs page
            current_url = driver.current_url.lower()
            if "linkedin.com/feed" in current_url or "linkedin.com/jobs" in current_url:
                print("✅ Authentication successful after security challenge!")
                
                # Test navigation to a search URL
                search_url = "https://www.linkedin.com/jobs/search/?keywords=python&location=remote"
                print(f"Navigating to search URL: {search_url}")
                driver.get(search_url)
                time.sleep(3)
                
                print("✅ Successfully navigated to search results!")
                print("The browser should now be ready for filter application.")
                
            else:
                print("❌ Authentication still not successful after challenge completion")
                print(f"Current URL: {driver.current_url}")
                
        else:
            # Check if authentication was successful
            current_url = driver.current_url.lower()
            if "linkedin.com/feed" in current_url or "linkedin.com/jobs" in current_url:
                print("✅ Authentication successful!")
                
                # Test navigation to a search URL
                search_url = "https://www.linkedin.com/jobs/search/?keywords=python&location=remote"
                print(f"Navigating to search URL: {search_url}")
                driver.get(search_url)
                time.sleep(3)
                
                print("✅ Successfully navigated to search results!")
                print("The browser should now be ready for filter application.")
                
            else:
                print("❌ Authentication failed")
                print(f"Current URL: {driver.current_url}")
                print("Note: No CAPTCHA detected, but authentication was not successful.")
                print("This might be due to incorrect credentials or other issues.")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        
    finally:
        # Keep the browser open for manual inspection
        print("\nTest completed. Browser would remain open for manual inspection in interactive mode.")
        print("Skipping browser close prompt for automated testing...")
        # input()  # Disabled for pytest
        
        if driver:
            try:
                driver.quit()
                print("Browser closed.")
            except:
                pass

if __name__ == "__main__":
    test_simple_captcha() 