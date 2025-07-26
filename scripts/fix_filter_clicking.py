#!/usr/bin/env python3
"""
Fix for LinkedIn filter clicking issue.
The problem is that the code is clicking on the entire filter section instead of the specific filter option.
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
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def fix_filter_clicking():
    """Test and demonstrate the proper way to click filter options."""
    
    print("🔧 LinkedIn Filter Clicking Fix")
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
        max_jobs_per_session=3,
        delay_min=2.0,
        delay_max=4.0,
        max_retries=3,
        page_load_timeout=30
    )
    
    # Add LinkedIn credentials to config
    scraping_config.linkedin_username = linkedin_config.username
    scraping_config.linkedin_password = linkedin_config.password
    
    # Initialize enhanced scraper
    scraper = EnhancedLinkedInScraper(scraping_config, session_manager)
    
    try:
        print("\n🚀 Starting filter clicking fix test...")
        
        # Step 1: Setup driver
        print("\n📋 Step 1: Setting up driver...")
        scraper.setup_driver()
        
        # Step 2: Handle authentication
        print("\n📋 Step 2: Handling authentication...")
        
        auth_success = False
        try:
            auth_success = scraper.authenticate(scraping_config.linkedin_username, scraping_config.linkedin_password)
        except Exception as e:
            print(f"⚠️ Authentication error: {e}")
        
        if not auth_success:
            print("\n🔒 Please manually authenticate in the browser window.")
            print("Once you're logged in, press Enter to continue...")
            input()
            
            current_url = scraper.driver.current_url
            if "linkedin.com" in current_url and "login" not in current_url.lower():
                print("✅ Manual authentication successful")
                auth_success = True
            else:
                print("❌ Authentication failed")
                return
        
        print("✅ Authentication successful")
        
        # Step 3: Navigate to search page
        print("\n📋 Step 3: Navigating to search page...")
        search_url = scraper.build_search_url(["software engineer"], "mountain view,ca,usa")
        scraper.driver.get(search_url)
        time.sleep(5)
        
        print(f"✅ Navigated to: {scraper.driver.current_url}")
        
        # Step 4: Open filters modal
        print("\n📋 Step 4: Opening filters modal...")
        
        # Try to open the "All filters" modal
        try:
            # Look for the "All filters" button
            all_filters_selectors = [
                "button[aria-label*='All filters']",
                "button[aria-label*='all filters']",
                "button:contains('All filters')",
                ".artdeco-pill[aria-label*='All filters']",
                ".artdeco-pill:contains('All filters')"
            ]
            
            all_filters_button = None
            for selector in all_filters_selectors:
                try:
                    all_filters_button = scraper.driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"✅ Found 'All filters' button with selector: {selector}")
                    break
                except:
                    continue
            
            if not all_filters_button:
                print("❌ Could not find 'All filters' button")
                return
            
            # Click the button
            all_filters_button.click()
            time.sleep(3)
            print("✅ 'All filters' modal opened")
            
        except Exception as e:
            print(f"❌ Error opening filters modal: {e}")
            return
        
        # Step 5: Analyze the modal structure
        print("\n📋 Step 5: Analyzing modal structure...")
        
        try:
            # Find the modal content
            modal_content = scraper.driver.find_element(By.CSS_SELECTOR, ".artdeco-modal__content")
            
            # Find all filter sections
            filter_sections = modal_content.find_elements(By.TAG_NAME, "li")
            print(f"Found {len(filter_sections)} filter sections")
            
            # Look for the Date posted section
            date_section = None
            for section in filter_sections:
                try:
                    h3_elements = section.find_elements(By.TAG_NAME, "h3")
                    for h3 in h3_elements:
                        if "date posted" in h3.text.lower():
                            date_section = section
                            print("✅ Found Date posted section")
                            break
                    if date_section:
                        break
                except:
                    continue
            
            if not date_section:
                print("❌ Could not find Date posted section")
                return
            
            # Analyze the Date posted section structure
            print("\n📋 Analyzing Date posted section structure...")
            
            # Get all elements in the date section
            all_elements = date_section.find_elements(By.XPATH, ".//*")
            print(f"Found {len(all_elements)} elements in Date posted section")
            
            # Look for input elements (radio buttons/checkboxes)
            input_elements = date_section.find_elements(By.CSS_SELECTOR, "input[type='radio'], input[type='checkbox']")
            print(f"Found {len(input_elements)} input elements")
            
            # Analyze each input element
            for i, input_elem in enumerate(input_elements):
                try:
                    input_id = input_elem.get_attribute('id')
                    input_value = input_elem.get_attribute('value')
                    input_name = input_elem.get_attribute('name')
                    
                    print(f"\nInput {i+1}:")
                    print(f"  ID: {input_id}")
                    print(f"  Value: {input_value}")
                    print(f"  Name: {input_name}")
                    
                    # Try to find the corresponding label
                    if input_id:
                        try:
                            label = date_section.find_element(By.CSS_SELECTOR, f"label[for='{input_id}']")
                            print(f"  Label text: '{label.text}'")
                        except:
                            print(f"  No label found for ID {input_id}")
                    
                    # Look for parent elements that might contain the text
                    parent = input_elem.find_element(By.XPATH, "..")
                    print(f"  Parent text: '{parent.text[:100]}...'")
                    
                except Exception as e:
                    print(f"  Error analyzing input {i+1}: {e}")
            
            # Look for clickable elements with specific text
            print("\n📋 Looking for clickable elements with 'Past 24 hours' text...")
            
            target_text = "Past 24 hours"
            clickable_elements = []
            
            # Method 1: Look for elements containing the exact text
            for element in all_elements:
                try:
                    if element.is_displayed() and element.is_enabled():
                        element_text = element.text.strip()
                        if target_text.lower() in element_text.lower():
                            clickable_elements.append({
                                'element': element,
                                'text': element_text,
                                'tag': element.tag_name,
                                'class': element.get_attribute('class')
                            })
                except:
                    continue
            
            print(f"Found {len(clickable_elements)} elements containing '{target_text}'")
            
            for i, elem_info in enumerate(clickable_elements):
                print(f"\nElement {i+1}:")
                print(f"  Tag: {elem_info['tag']}")
                print(f"  Class: {elem_info['class']}")
                print(f"  Text: '{elem_info['text']}'")
            
            # Method 2: Look for radio buttons and their labels
            print("\n📋 Looking for radio buttons and labels...")
            
            radio_buttons = date_section.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            print(f"Found {len(radio_buttons)} radio buttons")
            
            for i, radio in enumerate(radio_buttons):
                try:
                    radio_id = radio.get_attribute('id')
                    radio_value = radio.get_attribute('value')
                    
                    print(f"\nRadio {i+1}:")
                    print(f"  ID: {radio_id}")
                    print(f"  Value: {radio_value}")
                    
                    # Find the label
                    if radio_id:
                        try:
                            label = date_section.find_element(By.CSS_SELECTOR, f"label[for='{radio_id}']")
                            print(f"  Label: '{label.text}'")
                            
                            if target_text.lower() in label.text.lower():
                                print(f"  ✅ This is the target radio button!")
                                
                                # Try clicking the label
                                print(f"  Attempting to click the label...")
                                label.click()
                                time.sleep(2)
                                
                                # Check if it was selected
                                if radio.is_selected():
                                    print(f"  ✅ Radio button is now selected!")
                                else:
                                    print(f"  ❌ Radio button is not selected")
                                
                        except Exception as e:
                            print(f"  Error with label: {e}")
                    
                except Exception as e:
                    print(f"  Error analyzing radio {i+1}: {e}")
            
            # Method 3: Look for clickable divs or spans
            print("\n📋 Looking for clickable divs/spans...")
            
            clickable_divs = date_section.find_elements(By.CSS_SELECTOR, "div[role='radio'], span[role='radio'], div[tabindex], span[tabindex]")
            print(f"Found {len(clickable_divs)} clickable divs/spans")
            
            for i, div in enumerate(clickable_divs):
                try:
                    div_text = div.text.strip()
                    div_role = div.get_attribute('role')
                    div_tabindex = div.get_attribute('tabindex')
                    
                    print(f"\nClickable div {i+1}:")
                    print(f"  Role: {div_role}")
                    print(f"  Tabindex: {div_tabindex}")
                    print(f"  Text: '{div_text}'")
                    
                    if target_text.lower() in div_text.lower():
                        print(f"  ✅ This is the target clickable element!")
                        
                        # Try clicking it
                        print(f"  Attempting to click...")
                        div.click()
                        time.sleep(2)
                        
                        # Check if any radio button is now selected
                        selected_radios = date_section.find_elements(By.CSS_SELECTOR, "input[type='radio']:checked")
                        if selected_radios:
                            print(f"  ✅ A radio button is now selected!")
                        else:
                            print(f"  ❌ No radio button is selected")
                
                except Exception as e:
                    print(f"  Error with clickable div {i+1}: {e}")
            
        except Exception as e:
            print(f"❌ Error analyzing modal: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n🎉 Modal analysis completed!")
        print("\nBased on this analysis, we can see the proper way to click filter options.")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Keep browser open for manual inspection
        print("\n🔍 Browser will remain open for manual inspection.")
        print("Press Enter to close the browser...")
        input()
        
        # Cleanup
        try:
            scraper.cleanup()
        except:
            pass

if __name__ == "__main__":
    fix_filter_clicking() 