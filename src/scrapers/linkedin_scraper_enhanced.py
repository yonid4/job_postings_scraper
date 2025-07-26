#!/usr/bin/env python3
"""
Enhanced LinkedIn Scraper with Session Management

This module provides an enhanced LinkedIn scraper that:
- Uses persistent browser sessions to get the same interface as manual browsing
- Handles both old and new LinkedIn interfaces
- Implements comprehensive stealth techniques
- Provides robust date filtering for both interface versions
"""

import time
import random
from typing import List, Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    WebDriverException,
    ElementClickInterceptedException
)

from src.scrapers.linkedin_scraper import LinkedInScraper, ScrapingResult
from src.scrapers.base_scraper import ScrapingConfig
from src.utils.session_manager import SessionManager
from src.utils.logger import JobAutomationLogger
from src.data.models import JobListing


class EnhancedLinkedInScraper(LinkedInScraper):
    """
    Enhanced LinkedIn scraper with session management and stealth techniques.
    
    This scraper uses persistent browser sessions to ensure it gets the same
    interface as manual browsing, and implements comprehensive stealth techniques
    to avoid detection.
    """
    
    def __init__(self, config: ScrapingConfig, session_manager: SessionManager = None):
        """
        Initialize the enhanced LinkedIn scraper.
        
        Args:
            config: Configuration for the scraper
            session_manager: Optional session manager for persistent sessions
        """
        super().__init__(config)
        self.session_manager = session_manager or SessionManager()
        self.interface_version = None
        self.is_authenticated = False
        
        # Set authentication credentials from config if available
        if hasattr(config, 'linkedin_username') and hasattr(config, 'linkedin_password'):
            self.username = config.linkedin_username
            self.password = config.linkedin_password
        else:
            # Try to get from environment or config manager
            import os
            self.username = os.getenv('LINKEDIN_USERNAME')
            self.password = os.getenv('LINKEDIN_PASSWORD')
        
    def setup_driver(self) -> None:
        """
        Set up Chrome WebDriver with enhanced stealth configuration.
        """
        try:
            # Create Chrome options with enhanced stealth configuration
            options = Options()
            
            # Enhanced stealth settings
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Realistic user agent (Chrome on macOS)
            user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            options.add_argument(f'--user-agent={user_agent}')
            
            # Realistic viewport and window size
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--start-maximized')
            
            # Disable automation indicators
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            
            # Performance optimizations
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-software-rasterizer')
            options.add_argument('--disable-background-timer-throttling')
            options.add_argument('--disable-backgrounding-occluded-windows')
            options.add_argument('--disable-renderer-backgrounding')
            
            # Additional stealth settings
            options.add_argument('--disable-features=VizDisplayCompositor')
            options.add_argument('--disable-ipc-flooding-protection')
            
            # Set language and locale
            options.add_argument('--lang=en-US')
            options.add_argument('--accept-lang=en-US,en;q=0.9')
            
            # Create WebDriver
            self.driver = webdriver.Chrome(options=options)
            
            # Apply enhanced stealth scripts
            self._apply_enhanced_stealth_scripts()
            
            # Set up wait with realistic timeout
            self.wait = WebDriverWait(self.driver, 15)
            
            # Set realistic viewport
            self.driver.set_window_size(1920, 1080)
            
            self.logger.logger.info("Enhanced Chrome WebDriver initialized")
            
        except Exception as e:
            self.logger.logger.error(f"Failed to setup WebDriver: {e}")
            raise
    
    def _apply_enhanced_stealth_scripts(self) -> None:
        """Apply enhanced JavaScript stealth scripts."""
        try:
            # Remove webdriver property
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            # Override permissions
            self.driver.execute_script("""
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)
            
            # Override plugins
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
            """)
            
            # Override languages
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
            """)
            
            # Override connection
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'connection', {
                    get: () => ({
                        effectiveType: '4g',
                        rtt: 50,
                        downlink: 10,
                        saveData: false
                    }),
                });
            """)
            
            # Override hardware concurrency
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: () => 8,
                });
            """)
            
            # Override device memory
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'deviceMemory', {
                    get: () => 8,
                });
            """)
            
            # Override platform
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'MacIntel',
                });
            """)
            
            self.logger.logger.debug("Applied enhanced stealth scripts")
            
        except Exception as e:
            self.logger.logger.warning(f"Failed to apply some stealth scripts: {e}")
    
    def create_persistent_session(self, session_name: str = None, use_persistent_profile: bool = True) -> str:
        """
        Create a persistent browser session.
        
        Args:
            session_name: Optional name for the session
            use_persistent_profile: Whether to use persistent user data directory
            
        Returns:
            Session ID
        """
        try:
            session_id = self.session_manager.create_session(session_name, use_persistent_profile)
            self.driver = self.session_manager.driver
            self.wait = self.session_manager.wait
            self.logger.logger.info(f"Created persistent session: {session_id}")
            return session_id
            
        except Exception as e:
            self.logger.logger.error(f"Failed to create persistent session: {e}")
            # Try fallback without persistent profile
            if use_persistent_profile:
                self.logger.logger.info("Retrying without persistent profile...")
                return self.create_persistent_session(session_name, use_persistent_profile=False)
            raise
    
    def load_persistent_session(self, session_id: str, use_persistent_profile: bool = True) -> bool:
        """
        Load an existing persistent session.
        
        Args:
            session_id: Session ID to load
            use_persistent_profile: Whether to use persistent user data directory
            
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            if self.session_manager.load_session(session_id, use_persistent_profile):
                self.driver = self.session_manager.driver
                self.wait = self.session_manager.wait
                
                # Check if already authenticated
                if self.session_manager.is_authenticated():
                    self.is_authenticated = True
                    self.logger.logger.info(f"Loaded authenticated session: {session_id}")
                else:
                    self.logger.logger.info(f"Loaded session (needs authentication): {session_id}")
                
                return True
            else:
                # Try fallback without persistent profile
                if use_persistent_profile:
                    self.logger.logger.info("Retrying without persistent profile...")
                    return self.load_persistent_session(session_id, use_persistent_profile=False)
                return False
                
        except Exception as e:
            self.logger.logger.error(f"Failed to load persistent session: {e}")
            # Try fallback without persistent profile
            if use_persistent_profile:
                self.logger.logger.info("Retrying without persistent profile...")
                return self.load_persistent_session(session_id, use_persistent_profile=False)
            return False
    
    def authenticate_with_session(self, username: str, password: str) -> bool:
        """
        Authenticate using the session manager.
        
        Args:
            username: LinkedIn username/email
            password: LinkedIn password
            
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Use the existing WebDriver from the scraper instead of creating a new one
            if self.driver and not self.session_manager.driver:
                self.logger.logger.info("Using existing WebDriver for session manager...")
                self.session_manager.driver = self.driver
                self.session_manager.wait = self.wait
            
            # Ensure session manager has a WebDriver
            if not self.session_manager.driver:
                self.logger.logger.info("Session manager WebDriver not initialized, creating session...")
                session_id = self.session_manager.create_session()
                if not session_id:
                    self.logger.logger.error("Failed to create session manager session")
                    self.last_auth_error = "Failed to create session manager session"
                    return False
            
            # Use the session manager's WebDriver for authentication
            if self.session_manager.authenticate(username, password):
                self.is_authenticated = True
                self.username = username
                self.password = password
                # Use the session manager's WebDriver
                self.driver = self.session_manager.driver
                self.wait = self.session_manager.wait
                self.logger.logger.info("Authentication successful with session manager")
                return True
            else:
                # Authentication failed - the session manager will have already handled any security challenges
                self.logger.logger.error("Authentication failed with session manager")
                self.last_auth_error = "Authentication failed with session manager"
                return False
                
        except Exception as e:
            self.logger.logger.error(f"Authentication error: {e}")
            self.last_auth_error = f"Authentication error: {e}"
            return False
    

    
    def detect_interface_version(self) -> str:
        """
        Detect which LinkedIn interface version is currently loaded.
        
        Returns:
            'new' or 'old' interface version
        """
        try:
            # Wait for page to load
            time.sleep(2)
            
            # Check for new interface indicators
            new_interface_selectors = [
                '.jobs-search-results-list',
                '[data-test-id="search-results"]',
                '.jobs-search__results-list',
                '.search-results__list',
                '.jobs-search-results__list',
                '.jobs-search-results__list-item'
            ]
            
            for selector in new_interface_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed():
                        self.interface_version = 'new'
                        self.logger.logger.info("Detected NEW LinkedIn interface")
                        return 'new'
                except:
                    continue
            
            # Check for old interface indicators
            old_interface_selectors = [
                '.job-search-card',
                '.job-card-container',
                '.search-results__item',
                '.job-card',
                '.job-search-results__item'
            ]
            
            for selector in old_interface_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed():
                        self.interface_version = 'old'
                        self.logger.logger.info("Detected OLD LinkedIn interface")
                        return 'old'
                except:
                    continue
            
            # Default to new interface if can't determine
            self.interface_version = 'new'
            self.logger.logger.warning("Could not determine interface version, defaulting to NEW")
            return 'new'
            
        except Exception as e:
            self.logger.logger.error(f"Error detecting interface version: {e}")
            self.interface_version = 'new'
            return 'new'
    
    def apply_date_filter_enhanced(self, days: int) -> bool:
        """
        Apply date filter with enhanced interface detection and fallback strategies.
        
        Args:
            days: Number of days for filter (1, 3, 7, 14, 30)
            
        Returns:
            bool: True if filter was successfully applied, False otherwise
        """
        try:
            self.logger.logger.info(f"Applying enhanced date filter for {days} days")
            
            # Detect interface version
            self.interface_version = self.detect_interface_version()
            self.logger.logger.info(f"Detected {self.interface_version.upper()} LinkedIn interface")
            
            # Add realistic delay before attempting to apply filter
            self._add_realistic_delay()
            
            # Get date filter button selectors
            button_selectors = self._get_date_filter_button_selectors()
            self.logger.logger.info(f"Trying {len(button_selectors)} date filter button selectors")
            
            # Debug: Log all filter-related elements on the page
            try:
                filter_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-test-id*='filter'], [aria-label*='filter'], [data-control-name*='filter'], .filter-button, .search-s-facet__filter-button")
                self.logger.logger.info(f"Found {len(filter_elements)} filter-related elements on page")
                for i, elem in enumerate(filter_elements[:5]):  # Log first 5 elements
                    try:
                        aria_label = elem.get_attribute('aria-label') or 'No aria-label'
                        data_test_id = elem.get_attribute('data-test-id') or 'No data-test-id'
                        data_control_name = elem.get_attribute('data-control-name') or 'No data-control-name'
                        class_name = elem.get_attribute('class') or 'No class'
                        self.logger.logger.info(f"  Filter element {i+1}: aria-label='{aria_label}', data-test-id='{data_test_id}', data-control-name='{data_control_name}', class='{class_name}'")
                    except:
                        pass
            except Exception as e:
                self.logger.logger.warning(f"Could not inspect filter elements: {e}")
            
            # Try to find and click the date filter button
            if self._find_and_click_date_filter_button(button_selectors):
                self.logger.logger.info("✅ Date filter successfully applied!")
                return True
            else:
                self.logger.logger.warning("Failed to click date filter button - trying alternative approach")
                
                # Alternative approach: Look for any filter button and try to find date options
                try:
                    # Look for any filter button that might contain date options
                    generic_filter_selectors = [
                        "button[aria-label*='Filter']",
                        ".filter-button",
                        ".search-s-facet__filter-button",
                        "[data-test-id*='filter']",
                        ".artdeco-pill"
                    ]
                    
                    for selector in generic_filter_selectors:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for element in elements:
                                try:
                                    aria_label = element.get_attribute('aria-label') or ''
                                    if 'date' in aria_label.lower() or 'filter' in aria_label.lower():
                                        self.logger.logger.info(f"Found potential date filter element: {aria_label}")
                                        self._simulate_human_click(element)
                                        self._add_realistic_delay()
                                        break
                                except:
                                    continue
                        except:
                            continue
                except Exception as e:
                    self.logger.logger.warning(f"Alternative filter approach failed: {e}")
                
                return False
            
            # Wait for filter options to appear
            self._add_realistic_delay()
            
            # Get date filter option selectors
            option_selectors = self._get_date_filter_option_selectors(days)
            self.logger.logger.info(f"Trying {len(option_selectors)} date filter option selectors for {days} days")
            
            # Try to click the date filter option
            if not self._click_filter_option(option_selectors):
                self.logger.logger.warning(f"Failed to click date filter option for {days} days")
                return False
            
            # Wait for filter to be applied
            self._add_realistic_delay()
            
            # Try to click apply button if it exists
            self._click_apply_button()
            
            # Verify filter was applied
            if self._verify_filter_applied(days):
                self.logger.logger.info(f"✅ Date filter successfully applied for past {days} days")
                return True
            else:
                self.logger.logger.warning(f"⚠️ Date filter verification failed for {days} days")
                return False
                
        except Exception as e:
            self.logger.logger.error(f"Error applying enhanced date filter: {e}")
            return False
    
    def _find_and_click_date_option_in_modal(self, days: int) -> bool:
        """
        Find and click the specific date option within the Date posted section of the modal.
        
        Args:
            days: Number of days to filter for
            
        Returns:
            True if date option was found and clicked, False otherwise
        """
        try:
            # Find the modal content - try multiple selectors
            modal_content = None
            modal_selectors = [
                ".artdeco-modal__content.ember-view.display-flex.relative.mb4.flex-1.justify-center",
                ".artdeco-modal__content",
                "[class*='artdeco-modal__content']"
            ]
            
            for selector in modal_selectors:
                try:
                    modal_content = self.driver.find_element(By.CSS_SELECTOR, selector)
                    self.logger.logger.info(f"Found modal content with selector: {selector}")
                    break
                except:
                    continue
            
            if not modal_content:
                self.logger.logger.error("Could not find modal content")
                return False
            
            # Find the ul list within the modal
            ul_list = None
            ul_selectors = [
                "ul.list-style-none.flex-1",
                "ul.list-style-none",
                "ul[class*='list-style-none']"
            ]
            
            for selector in ul_selectors:
                try:
                    ul_list = modal_content.find_element(By.CSS_SELECTOR, selector)
                    self.logger.logger.info(f"Found ul list with selector: {selector}")
                    break
                except:
                    continue
            
            if not ul_list:
                self.logger.logger.error("Could not find ul list in modal")
                return False
            
            # Get all list items
            list_items = ul_list.find_elements(By.TAG_NAME, "li")
            self.logger.logger.info(f"Found {len(list_items)} filter items in the modal")
            
            # Find the Date posted filter section by looking for the h3 with "Date posted" text
            date_posted_item = None
            for item in list_items:
                try:
                    # Look for h3 element with "Date posted" text
                    h3_elements = item.find_elements(By.TAG_NAME, "h3")
                    for h3 in h3_elements:
                        if h3.text.strip().lower() == "date posted":
                            date_posted_item = item
                            self.logger.logger.info(f"✅ Found Date posted filter section")
                            break
                    if date_posted_item:
                        break
                except Exception as e:
                    self.logger.logger.debug(f"Error checking item for Date posted header: {e}")
                    continue
            
            if not date_posted_item:
                self.logger.logger.warning("Could not find Date posted filter section")
                return False
            
            # Debug: Log all text content in the date posted item
            try:
                all_text = date_posted_item.text
                self.logger.logger.info(f"Date posted item text content: '{all_text}'")
            except Exception as e:
                self.logger.logger.warning(f"Could not get text content: {e}")
            
            # Map days to LinkedIn date filter options
            date_mapping = {
                1: "Past 24 hours",
                7: "Past week", 
                30: "Past month",
                None: "Any time"
            }
            
            target_date_text = date_mapping.get(days, "Past week")
            self.logger.logger.info(f"Looking for date option: '{target_date_text}'")
            
            # Look for the specific date option within this item
            option_selectors = [
                f".//*[contains(text(), '{target_date_text}')]",
                f".//label[contains(text(), '{target_date_text}')]",
                f".//span[contains(text(), '{target_date_text}')]",
                f".//div[contains(text(), '{target_date_text}')]",
                f".//input[@type='radio' and @value='{target_date_text}']",
                f".//input[@type='checkbox' and @value='{target_date_text}']"
            ]
            
            target_option = None
            for selector in option_selectors:
                try:
                    elements = date_posted_item.find_elements(By.XPATH, selector)
                    self.logger.logger.info(f"Found {len(elements)} elements with selector: {selector}")
                    
                    for element in elements:
                        try:
                            element_text = element.text.strip()
                            element_value = element.get_attribute('value') or ''
                            self.logger.logger.info(f"Element text: '{element_text}', value: '{element_value}'")
                            
                            if (element.is_displayed() and 
                                (target_date_text.lower() in element_text.lower() or 
                                 target_date_text.lower() in element_value.lower())):
                                target_option = element
                                self.logger.logger.info(f"✅ Found matching date element: '{element_text}'")
                                break
                        except Exception as e:
                            self.logger.logger.debug(f"Error checking element: {e}")
                            continue
                    
                    if target_option:
                        break
                except Exception as e:
                    self.logger.logger.debug(f"Error with selector {selector}: {e}")
                    continue
            
            if not target_option:
                # Try a more generic approach - look for any clickable element with the date text
                try:
                    all_elements = date_posted_item.find_elements(By.XPATH, ".//*")
                    self.logger.logger.info(f"Found {len(all_elements)} total elements in date posted item")
                    
                    for element in all_elements:
                        try:
                            if element.is_displayed() and element.is_enabled():
                                element_text = element.text.strip()
                                if target_date_text.lower() in element_text.lower():
                                    self.logger.logger.info(f"Found potential target: '{element_text}'")
                                    target_option = element
                                    break
                        except:
                            continue
                except Exception as e:
                    self.logger.logger.debug(f"Error in generic search: {e}")
                
                if not target_option:
                    self.logger.logger.warning(f"Could not find '{target_date_text}' option in Date posted filter")
                    return False
            
            # Click the option
            try:
                target_option.click()
                time.sleep(1)
                self.logger.logger.info(f"✅ Date filter '{target_date_text}' applied")
                return True
            except Exception as e:
                self.logger.logger.error(f"Error clicking date option: {e}")
                return False
                
        except Exception as e:
            self.logger.logger.error(f"Error finding and clicking date option in modal: {e}")
            return False
    
    def _apply_date_filter_in_modal(self, days: int) -> bool:
        """
        Apply Date filter within an already open modal.
        
        Args:
            days: Number of days to filter for
            
        Returns:
            True if date filter was applied successfully, False otherwise
        """
        try:
            self.logger.logger.info(f"Applying Date filter in modal: {days} days")
            
            # Find the modal content - try multiple selectors
            modal_content = None
            modal_selectors = [
                ".artdeco-modal__content.ember-view.display-flex.relative.mb4.flex-1.justify-center",
                ".artdeco-modal__content",
                "[class*='artdeco-modal__content']"
            ]
            
            for selector in modal_selectors:
                try:
                    modal_content = self.driver.find_element(By.CSS_SELECTOR, selector)
                    self.logger.logger.info(f"Found modal content with selector: {selector}")
                    break
                except:
                    continue
            
            if not modal_content:
                self.logger.logger.error("Could not find modal content")
                return False
            
            # Find the ul list within the modal
            ul_list = None
            ul_selectors = [
                "ul.list-style-none.flex-1",
                "ul.list-style-none",
                "ul[class*='list-style-none']"
            ]
            
            for selector in ul_selectors:
                try:
                    ul_list = modal_content.find_element(By.CSS_SELECTOR, selector)
                    self.logger.logger.info(f"Found ul list with selector: {selector}")
                    break
                except:
                    continue
            
            if not ul_list:
                self.logger.logger.error("Could not find ul list in modal")
                return False
            
            # Get all list items
            list_items = ul_list.find_elements(By.TAG_NAME, "li")
            self.logger.logger.info(f"Found {len(list_items)} filter items in the modal")
            
            # Find the Date posted filter section by looking for the h3 with "Date posted" text
            date_posted_item = None
            for item in list_items:
                try:
                    # Look for h3 element with "Date posted" text
                    h3_elements = item.find_elements(By.TAG_NAME, "h3")
                    for h3 in h3_elements:
                        if h3.text.strip().lower() == "date posted":
                            date_posted_item = item
                            self.logger.logger.info(f"✅ Found Date posted filter section")
                            break
                    if date_posted_item:
                        break
                except Exception as e:
                    self.logger.logger.debug(f"Error checking item for Date posted header: {e}")
                    continue
            
            if not date_posted_item:
                self.logger.logger.warning("Could not find Date posted filter section")
                return False
            
            # Debug: Log all text content in the date posted item
            try:
                all_text = date_posted_item.text
                self.logger.logger.info(f"Date posted item text content: '{all_text}'")
            except Exception as e:
                self.logger.logger.warning(f"Could not get text content: {e}")
            
            # Map days to LinkedIn date filter options
            date_mapping = {
                1: "Past 24 hours",
                7: "Past week", 
                30: "Past month",
                None: "Any time"
            }
            
            target_date_text = date_mapping.get(days, "Past week")
            self.logger.logger.info(f"Looking for date option: '{target_date_text}'")
            
            # Look for the specific date option within this item
            option_selectors = [
                f".//*[contains(text(), '{target_date_text}')]",
                f".//label[contains(text(), '{target_date_text}')]",
                f".//span[contains(text(), '{target_date_text}')]",
                f".//div[contains(text(), '{target_date_text}')]",
                f".//input[@type='radio' and @value='{target_date_text}']",
                f".//input[@type='checkbox' and @value='{target_date_text}']"
            ]
            
            target_option = None
            for selector in option_selectors:
                try:
                    elements = date_posted_item.find_elements(By.XPATH, selector)
                    self.logger.logger.info(f"Found {len(elements)} elements with selector: {selector}")
                    
                    for element in elements:
                        try:
                            element_text = element.text.strip()
                            element_value = element.get_attribute('value') or ''
                            self.logger.logger.info(f"Element text: '{element_text}', value: '{element_value}'")
                            
                            if (element.is_displayed() and 
                                (target_date_text.lower() in element_text.lower() or 
                                 target_date_text.lower() in element_value.lower())):
                                target_option = element
                                self.logger.logger.info(f"✅ Found matching date element: '{element_text}'")
                                break
                        except Exception as e:
                            self.logger.logger.debug(f"Error checking element: {e}")
                            continue
                    
                    if target_option:
                        break
                except Exception as e:
                    self.logger.logger.debug(f"Error with selector {selector}: {e}")
                    continue
            
            if not target_option:
                # Try a more generic approach - look for any clickable element with the date text
                try:
                    all_elements = date_posted_item.find_elements(By.XPATH, ".//*")
                    self.logger.logger.info(f"Found {len(all_elements)} total elements in date posted item")
                    
                    for element in all_elements:
                        try:
                            if element.is_displayed() and element.is_enabled():
                                element_text = element.text.strip()
                                if target_date_text.lower() in element_text.lower():
                                    self.logger.logger.info(f"Found potential target: '{element_text}'")
                                    target_option = element
                                    break
                        except:
                            continue
                except Exception as e:
                    self.logger.logger.debug(f"Error in generic search: {e}")
                
                if not target_option:
                    self.logger.logger.warning(f"Could not find '{target_date_text}' option in Date posted filter")
                    return False
            
            # Click the option
            try:
                target_option.click()
                time.sleep(1)
                self.logger.logger.info(f"✅ Date filter '{target_date_text}' applied")
                return True
            except Exception as e:
                self.logger.logger.error(f"Error clicking date option: {e}")
                return False
                
        except Exception as e:
            self.logger.logger.error(f"Error applying date filter in modal: {e}")
            return False
    
    def _add_realistic_delay(self) -> None:
        """Add realistic delay to mimic human behavior."""
        delay = random.uniform(1.0, 3.0)
        time.sleep(delay)
    
    def _wait_for_page_load(self) -> None:
        """Wait for page to fully load."""
        try:
            # Wait for either interface version to load
            selectors = [
                '.jobs-search-results-list',
                '.jobs-search-results',
                '.job-search-card',
                '.job-card-container',
                '.search-results__list'
            ]
            
            for selector in selectors:
                try:
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    break
                except:
                    continue
                    
        except Exception as e:
            self.logger.logger.warning(f"Page load wait failed: {e}")
    
    def _get_date_filter_button_selectors(self) -> List[str]:
        """Get date filter button selectors based on interface version."""
        if self.interface_version == 'new':
            return [
                # New interface selectors
                "button[aria-label*='Date posted']",
                "[data-test-id='date-posted-filter']",
                ".search-s-facet--date-posted button",
                "button[data-control-name*='date']",
                ".filter-button:has-text('Date posted')",
                "button[aria-label*='date']",
                ".search-reusables__filter-binary-toggle",
                ".search-s-facet__filter-button",
                "[data-test-id='date-posted-filter-button']",
                ".artdeco-pill[aria-label*='Date posted']",
                ".search-reusables__filter-binary-toggle[aria-label*='Date posted']",
                ".filter-pill[aria-label*='Date posted']",
                # Additional new interface selectors
                "[data-test-id='date-posted-filter-dropdown']",
                ".search-s-facet__filter-button[aria-label*='Date posted']",
                ".search-reusables__filter-binary-toggle[data-control-name*='date']",
                "button[data-control-name='date-posted-filter']",
                ".search-s-facet__filter-button[data-control-name*='date']",
                # More generic selectors
                "button[aria-label*='Filter']",
                ".filter-button",
                ".search-s-facet__filter-button",
                "[data-test-id*='filter']",
                "[data-control-name*='filter']"
            ]
        else:
            return [
                # Old interface selectors - Updated with exact HTML structure
                # First, target the "All filters" button
                "button.artdeco-pill.search-reusables__all-filters-pill-button",
                "button[aria-label*='Show all filters']",
                ".search-reusables__all-filters-pill-button",
                "button.artdeco-pill[aria-label*='Show all filters']",
                # Look for the "Date posted" title in the filter modal
                ".text-heading-large.inline-block:contains('Date posted')",
                ".text-heading-large.inline-block",
                # Look for any element containing "Date posted" text
                "*:contains('Date posted')",
                # Generic filter selectors for old interface
                "button[aria-label*='Filter']",
                ".filter-button",
                ".search-s-facet__filter-button",
                "[data-test-id*='filter']",
                "[data-control-name*='filter']",
                # Try to find any filter-related button
                ".artdeco-pill",
                ".search-reusables__filter-binary-toggle",
                ".search-s-facet__filter-button",
                # Look for the filter modal content
                ".artdeco-modal__content .text-heading-large.inline-block"
            ]
    
    def _find_and_click_date_filter_button(self, selectors: List[str]) -> bool:
        """Find and click the date filter button."""
        # First, try to click the "All filters" button to open the filter modal
        try:
            all_filters_selectors = [
                "button.artdeco-pill.search-reusables__all-filters-pill-button",
                "button[aria-label*='Show all filters']",
                "button[aria-label*='All filters']",
                "//button[contains(text(), 'All filters')]",
                "//button[contains(text(), 'All Filters')]",
                "//span[contains(text(), 'All filters')]",
                "//span[contains(text(), 'All Filters')]"
            ]
            
            for selector in all_filters_selectors:
                try:
                    element = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    
                    self.logger.logger.info("Found 'All filters' button, clicking to open filter modal")
                    self._simulate_human_click(element)
                    self._add_realistic_delay()
                    
                    # Wait for the modal to fully load
                    self.logger.logger.info("Waiting for filter modal to load...")
                    time.sleep(2)  # Give the modal time to fully render
                    
                    # Debug: Log all text elements in the modal to see what's available
                    try:
                        # First, try to scroll through the modal to load all content
                        modal_content = self.driver.find_element(By.CSS_SELECTOR, ".artdeco-modal__content")
                        self.logger.logger.info("Found modal content, scrolling to load all sections...")
                        
                        # Scroll down in the modal to load all sections
                        self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", modal_content)
                        time.sleep(1)
                        self.driver.execute_script("arguments[0].scrollTop = 0", modal_content)
                        time.sleep(1)
                        
                        modal_elements = self.driver.find_elements(By.CSS_SELECTOR, ".artdeco-modal__content *")
                        self.logger.logger.info(f"Found {len(modal_elements)} elements in the filter modal")
                        
                        # Log more text elements to see what's available
                        text_elements = []
                        for elem in modal_elements:
                            try:
                                text = elem.text.strip()
                                if text and len(text) > 0 and len(text) < 100:  # Increased length limit
                                    text_elements.append(text)
                                    if len(text_elements) >= 20:  # Increased count
                                        break
                            except:
                                continue
                        
                        self.logger.logger.info(f"Text elements found in modal: {text_elements}")
                        
                        # Look for filter section headers or categories
                        filter_headers = self.driver.find_elements(By.CSS_SELECTOR, ".artdeco-modal__content h3, .artdeco-modal__content .text-heading-large, .artdeco-modal__content .filter-section-header")
                        self.logger.logger.info(f"Found {len(filter_headers)} potential filter section headers")
                        
                        for i, header in enumerate(filter_headers):
                            try:
                                text = header.text.strip()
                                if text:
                                    self.logger.logger.info(f"Filter header {i+1}: '{text}'")
                            except:
                                continue
                        
                        # Also try to find any elements containing "date" (case insensitive)
                        date_related_elements = self.driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'date')]")
                        self.logger.logger.info(f"Found {len(date_related_elements)} elements containing 'date' (case insensitive)")
                        
                        for i, elem in enumerate(date_related_elements[:5]):  # Show first 5
                            try:
                                text = elem.text.strip()
                                if text:
                                    self.logger.logger.info(f"Date-related element {i+1}: '{text}'")
                            except:
                                continue
                        
                        # Try to find any elements that might be filter categories or sections
                        filter_sections = self.driver.find_elements(By.CSS_SELECTOR, ".artdeco-modal__content .filter-section, .artdeco-modal__content .search-reusables__filter-binary-toggle, .artdeco-modal__content .search-reusables__filter-pill-button")
                        self.logger.logger.info(f"Found {len(filter_sections)} potential filter sections")
                        
                        for i, section in enumerate(filter_sections[:10]):
                            try:
                                text = section.text.strip()
                                if text and len(text) < 100:
                                    self.logger.logger.info(f"Filter section {i+1}: '{text}'")
                            except:
                                continue
                        
                    except Exception as e:
                        self.logger.logger.warning(f"Could not inspect modal elements: {e}")
                    
                    # Now look for the "Date posted" section in the modal with multiple approaches
                    date_posted_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Date posted') or contains(text(), 'Date Posted') or contains(text(), 'date posted') or contains(text(), 'DATE POSTED')]")
                    self.logger.logger.info(f"Found {len(date_posted_elements)} elements containing 'Date posted' text")
                    
                    if date_posted_elements:
                        for i, element in enumerate(date_posted_elements):
                            try:
                                # Check if this element is clickable and contains "Date posted"
                                text = element.text.strip().lower()
                                self.logger.logger.info(f"Date posted element {i+1}: '{text}'")
                                
                                if 'date posted' in text:
                                    self.logger.logger.info(f"Found 'Date posted' element in modal: {element.text}")
                                    
                                    # Try to click the element
                                    self._simulate_human_click(element)
                                    self.logger.logger.info("Clicked on 'Date posted' element in modal")
                                    
                                    # Wait a moment for the dropdown to open
                                    self._add_realistic_delay()
                                    return True
                                    
                            except Exception as e:
                                self.logger.logger.debug(f"Failed to click 'Date posted' element {i+1} in modal: {e}")
                                continue
                    else:
                        self.logger.logger.warning("No 'Date posted' elements found in the modal")
                        
                        # Try to find and click the "Date posted" filter header specifically
                        try:
                            # Look for the "Date posted" filter header in the list
                            date_posted_header = self.driver.find_element(By.XPATH, "//h3[contains(text(), 'Date posted') or contains(text(), 'Date Posted')]")
                            if date_posted_header:
                                self.logger.logger.info("Found 'Date posted' filter header, clicking on it...")
                                self._simulate_human_click(date_posted_header)
                                self.logger.logger.info("Clicked on 'Date posted' filter header")
                                
                                # Wait for the date options to appear
                                self._add_realistic_delay()
                                
                                # Now look for the date options (Past 24 Hours, Past Week, etc.)
                                date_options = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Past 24 Hours') or contains(text(), 'Past week') or contains(text(), 'Past month') or contains(text(), 'Any time')]")
                                self.logger.logger.info(f"Found {len(date_options)} date filter options")
                                
                                # Find the option that matches our target (7 days = "Past week")
                                target_option = None
                                for option in date_options:
                                    try:
                                        text = option.text.strip().lower()
                                        self.logger.logger.info(f"Date option: '{text}'")
                                        if 'past week' in text or 'past 7 days' in text:
                                            target_option = option
                                            break
                                    except:
                                        continue
                                
                                if target_option:
                                    self.logger.logger.info("Found target date option, clicking on it...")
                                    self._simulate_human_click(target_option)
                                    self.logger.logger.info("Clicked on target date option")
                                    
                                    # Wait for the filter to be applied
                                    self._add_realistic_delay()
                                    return True
                                else:
                                    self.logger.logger.warning("Could not find target date option")
                                    
                        except Exception as e:
                            self.logger.logger.debug(f"Could not find or click 'Date posted' filter header: {e}")
                        
                        # Try alternative approach: look for any clickable elements that might be date filters
                        try:
                            # Look for any buttons or clickable elements in the modal
                            clickable_elements = self.driver.find_elements(By.CSS_SELECTOR, ".artdeco-modal__content button, .artdeco-modal__content [role='button'], .artdeco-modal__content .clickable")
                            self.logger.logger.info(f"Found {len(clickable_elements)} clickable elements in modal")
                            
                            for i, elem in enumerate(clickable_elements[:10]):  # Check first 10
                                try:
                                    text = elem.text.strip()
                                    if text and len(text) < 50:
                                        self.logger.logger.info(f"Clickable element {i+1}: '{text}'")
                                except:
                                    continue
                        except Exception as e:
                            self.logger.logger.debug(f"Could not inspect clickable elements: {e}")
                        
                        # Try a different approach: find all h3 elements and click the one that says "Date posted"
                        try:
                            all_h3_elements = self.driver.find_elements(By.TAG_NAME, "h3")
                            self.logger.logger.info(f"Found {len(all_h3_elements)} h3 elements in modal")
                            
                            for i, h3_elem in enumerate(all_h3_elements):
                                try:
                                    text = h3_elem.text.strip()
                                    self.logger.logger.info(f"H3 element {i+1}: '{text}'")
                                    
                                    if text.lower() == 'date posted':
                                        self.logger.logger.info(f"Found 'Date posted' h3 element at index {i+1}")
                                        
                                        # Don't click on the header - the options are already visible
                                        # Instead, find the Date posted section and look for options within it
                                        return self._find_and_click_date_option_in_modal(days=days)
                                        
                                        # Fallback: try to find date options in the entire modal
                                        for radio in radio_options:
                                            try:
                                                # Find the label associated with this radio/checkbox
                                                radio_id = radio.get_attribute('id')
                                                if radio_id:
                                                    label = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{radio_id}']")
                                                    if label:
                                                        date_options.append(label)
                                            except:
                                                continue
                                        
                                        # Approach 3: Look for any clickable elements that might be date options
                                        clickable_options = self.driver.find_elements(By.CSS_SELECTOR, "button, [role='button'], .clickable, .artdeco-pill")
                                        for clickable in clickable_options:
                                            try:
                                                text = clickable.text.strip().lower()
                                                if any(option in text for option in ['past 24 hours', 'past week', 'past month', 'any time']):
                                                    date_options.append(clickable)
                                            except:
                                                continue
                                        
                                        self.logger.logger.info(f"Found {len(date_options)} total date filter options using multiple approaches")
                                        
                                        # Log all the options we found
                                        for i, option in enumerate(date_options[:10]):  # Show first 10
                                            try:
                                                text = option.text.strip()
                                                if text:
                                                    self.logger.logger.info(f"Date option {i+1}: '{text}'")
                                            except:
                                                continue
                                        
                                        # Find the option that matches our target (7 days = "Past week")
                                        target_option = None
                                        for option in date_options:
                                            try:
                                                text = option.text.strip().lower()
                                                self.logger.logger.info(f"Checking date option: '{text}'")
                                                if 'past week' in text or 'past 7 days' in text:
                                                    target_option = option
                                                    break
                                            except:
                                                continue
                                        
                                        if target_option:
                                            self.logger.logger.info("Found target date option, clicking on it...")
                                            self._simulate_human_click(target_option)
                                            self.logger.logger.info("Clicked on target date option")
                                            
                                            # Wait for the filter to be applied
                                            self._add_realistic_delay()
                                            
                                            # Verify that the filter was applied by checking if we can see the filter pill
                                            try:
                                                # Look for the date filter pill on the page
                                                date_filter_pill = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Past week') or contains(text(), 'Past 24 hours') or contains(text(), 'Past month')]")
                                                if date_filter_pill:
                                                    self.logger.logger.info("✅ Date filter successfully applied and verified!")
                                                    return True
                                            except:
                                                self.logger.logger.info("✅ Date filter applied (verification not needed)")
                                                return True
                                            
                                            return True
                                        else:
                                            self.logger.logger.warning("Could not find target date option")
                                            
                                            # Try clicking on any "Past week" option we can find
                                            for option in date_options:
                                                try:
                                                    text = option.text.strip().lower()
                                                    if 'week' in text:
                                                        self.logger.logger.info(f"Trying to click on option with 'week': '{text}'")
                                                        self._simulate_human_click(option)
                                                        self.logger.logger.info("Clicked on week option")
                                                        self._add_realistic_delay()
                                                        return True
                                                except:
                                                    continue
                                        break
                                        
                                except Exception as e:
                                    self.logger.logger.debug(f"Error processing h3 element {i+1}: {e}")
                                    continue
                                    
                        except Exception as e:
                            self.logger.logger.debug(f"Could not find h3 elements: {e}")
                        
                        # Try to close the modal and look for date filter in the main page
                        self.logger.logger.info("No date filter found in modal, trying to close modal and look on main page...")
                        try:
                            # Look for close button or escape key
                            close_buttons = self.driver.find_elements(By.CSS_SELECTOR, ".artdeco-modal__dismiss, .artdeco-modal__close, button[aria-label*='close'], button[aria-label*='Close']")
                            if close_buttons:
                                self.logger.logger.info("Found close button, closing modal...")
                                self._simulate_human_click(close_buttons[0])
                                time.sleep(1)
                            else:
                                # Try pressing Escape key
                                from selenium.webdriver.common.keys import Keys
                                self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                                time.sleep(1)
                                self.logger.logger.info("Pressed Escape key to close modal")
                        except Exception as e:
                            self.logger.logger.debug(f"Could not close modal: {e}")
                    
                    break  # If we found and clicked the "All filters" button, break out of the loop
                    
                except Exception as e:
                    self.logger.logger.debug(f"Failed to click 'All filters' button with selector {selector}: {e}")
                    continue
                    
        except Exception as e:
            self.logger.logger.debug(f"Failed to open filter modal: {e}")
        
        # Fallback: Try to find the "Date posted" text directly (in case modal is already open)
        try:
            # Look for the "Date posted" text in the filter modal
            date_posted_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Date posted') or contains(text(), 'Date Posted')]")
            
            if date_posted_elements:
                for element in date_posted_elements:
                    try:
                        # Check if this element is clickable and contains "Date posted"
                        text = element.text.strip().lower()
                        if 'date posted' in text:
                            self.logger.logger.info(f"Found 'Date posted' element: {element.text}")
                            
                            # Try to click the element
                            self._simulate_human_click(element)
                            self.logger.logger.info("Clicked on 'Date posted' element")
                            
                            # Wait a moment for the dropdown to open
                            self._add_realistic_delay()
                            return True
                            
                    except Exception as e:
                        self.logger.logger.debug(f"Failed to click 'Date posted' element: {e}")
                        continue
        except Exception as e:
            self.logger.logger.debug(f"Failed to find 'Date posted' text: {e}")
        
        # Final fallback: Try the original selectors
        for selector in selectors:
            try:
                element = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                
                self._simulate_human_click(element)
                self.logger.logger.debug(f"Clicked date filter button with selector: {selector}")
                return True
                
            except Exception as e:
                self.logger.logger.debug(f"Failed to click date filter button with selector {selector}: {e}")
                continue
        
        self.logger.logger.warning("Could not find or click date filter button")
        return False
    
    def _get_date_filter_option_selectors(self, days: int) -> List[str]:
        """Get date filter option selectors based on interface version and days."""
        if self.interface_version == 'new':
            selectors_map = {
                1: [
                    "input[value='1']",
                    "li[data-value='1']",
                    "[data-test-id='date-posted-past-24-hours']",
                    "label:contains('Past 24 hours')",
                    "span:contains('Past 24 hours')",
                    ".filter-option[aria-label*='24 hours']",
                    "[aria-label*='Past 24 hours']",
                    "input[type='radio'][value='1']",
                    ".search-s-facet__filter-option[data-value='1']",
                    "[data-test-id='date-posted-filter-option-1']",
                    ".artdeco-pill[data-value='1']",
                    ".search-reusables__filter-binary-toggle[data-value='1']"
                ],
                3: [
                    "input[value='3']",
                    "li[data-value='3']",
                    "[data-test-id='date-posted-past-3-days']",
                    "label:contains('Past 3 days')",
                    "span:contains('Past 3 days')",
                    ".filter-option[aria-label*='3 days']",
                    "[aria-label*='Past 3 days']",
                    "input[type='radio'][value='3']",
                    ".search-s-facet__filter-option[data-value='3']",
                    "[data-test-id='date-posted-filter-option-3']",
                    ".artdeco-pill[data-value='3']",
                    ".search-reusables__filter-binary-toggle[data-value='3']"
                ],
                7: [
                    "input[value='7']", 
                    "li[data-value='7']",
                    "[data-test-id='date-posted-past-week']",
                    "label:contains('Past week')",
                    "span:contains('Past week')",
                    ".filter-option[aria-label*='week']",
                    "[aria-label*='Past week']",
                    "input[type='radio'][value='7']",
                    ".search-s-facet__filter-option[data-value='7']",
                    "[data-test-id='date-posted-filter-option-7']",
                    ".artdeco-pill[data-value='7']",
                    ".search-reusables__filter-binary-toggle[data-value='7']"
                ],
                14: [
                    "input[value='14']",
                    "li[data-value='14']", 
                    "[data-test-id='date-posted-past-2-weeks']",
                    "label:contains('Past 2 weeks')",
                    "span:contains('Past 2 weeks')",
                    ".filter-option[aria-label*='2 weeks']",
                    "[aria-label*='Past 2 weeks']",
                    "input[type='radio'][value='14']",
                    ".search-s-facet__filter-option[data-value='14']",
                    "[data-test-id='date-posted-filter-option-14']",
                    ".artdeco-pill[data-value='14']",
                    ".search-reusables__filter-binary-toggle[data-value='14']"
                ],
                30: [
                    "input[value='30']",
                    "li[data-value='30']",
                    "[data-test-id='date-posted-past-month']",
                    "label:contains('Past month')",
                    "span:contains('Past month')",
                    ".filter-option[aria-label*='month']",
                    "[aria-label*='Past month']",
                    "input[type='radio'][value='30']",
                    ".search-s-facet__filter-option[data-value='30']",
                    "[data-test-id='date-posted-filter-option-30']",
                    ".artdeco-pill[data-value='30']",
                    ".search-reusables__filter-binary-toggle[data-value='30']"
                ]
            }
        else:
            # Old interface selectors - Updated with exact HTML structure
            selectors_map = {
                1: [
                    # Past 24 Hours options
                    ".search-reusables__secondary-filters-values *:contains('Past 24 Hours')",
                    ".search-reusables__secondary-filters-values *:contains('Past 24 hours')",
                    ".search-reusables__secondary-filters-values *:contains('24 Hours')",
                    ".search-reusables__secondary-filters-values *:contains('24 hours')",
                    ".search-reusables__secondary-filters-values *:contains('1 day')",
                    ".search-reusables__secondary-filters-values *:contains('1 Day')",
                    # Generic selectors for 24 hours
                    "input[value='1']",
                    "li[data-value='1']",
                    "label:contains('Past 24 Hours')",
                    "span:contains('Past 24 Hours')",
                    "button:contains('Past 24 Hours')",
                    "a:contains('Past 24 Hours')"
                ],
                3: [
                    # Past 3 days options
                    ".search-reusables__secondary-filters-values *:contains('Past 3 days')",
                    ".search-reusables__secondary-filters-values *:contains('3 days')",
                    ".search-reusables__secondary-filters-values *:contains('3 Days')",
                    # Generic selectors for 3 days
                    "input[value='3']",
                    "li[data-value='3']",
                    "label:contains('Past 3 days')",
                    "span:contains('Past 3 days')",
                    "button:contains('Past 3 days')",
                    "a:contains('Past 3 days')"
                ],
                7: [
                    # Past week options
                    ".search-reusables__secondary-filters-values *:contains('Past week')",
                    ".search-reusables__secondary-filters-values *:contains('Past Week')",
                    ".search-reusables__secondary-filters-values *:contains('1 week')",
                    ".search-reusables__secondary-filters-values *:contains('1 Week')",
                    # Generic selectors for 7 days
                    "input[value='7']",
                    "li[data-value='7']",
                    "label:contains('Past week')",
                    "span:contains('Past week')",
                    "button:contains('Past week')",
                    "a:contains('Past week')"
                ],
                14: [
                    # Past 2 weeks options
                    ".search-reusables__secondary-filters-values *:contains('Past 2 weeks')",
                    ".search-reusables__secondary-filters-values *:contains('2 weeks')",
                    ".search-reusables__secondary-filters-values *:contains('2 Weeks')",
                    # Generic selectors for 14 days
                    "input[value='14']",
                    "li[data-value='14']",
                    "label:contains('Past 2 weeks')",
                    "span:contains('Past 2 weeks')",
                    "button:contains('Past 2 weeks')",
                    "a:contains('Past 2 weeks')"
                ],
                30: [
                    # Past month options
                    ".search-reusables__secondary-filters-values *:contains('Past Month')",
                    ".search-reusables__secondary-filters-values *:contains('Past month')",
                    ".search-reusables__secondary-filters-values *:contains('1 month')",
                    ".search-reusables__secondary-filters-values *:contains('1 Month')",
                    # Generic selectors for 30 days
                    "input[value='30']",
                    "li[data-value='30']",
                    "label:contains('Past Month')",
                    "span:contains('Past Month')",
                    "button:contains('Past Month')",
                    "a:contains('Past Month')"
                ]
            }
        
        return selectors_map.get(days, [])
    
    def _click_filter_option(self, selectors: List[str]) -> bool:
        """Click on a specific date filter option."""
        for selector in selectors:
            try:
                # Try different approaches to find and click the element
                element = None
                
                # First, try to find by text content using XPath
                if ':contains(' in selector:
                    # Extract the text from the selector
                    text_match = selector.split(':contains(')[1].split(')')[0].strip("'\"")
                    xpath_selector = f"//*[contains(text(), '{text_match}')]"
                    
                    try:
                        elements = self.driver.find_elements(By.XPATH, xpath_selector)
                        for elem in elements:
                            if elem.is_displayed() and elem.is_enabled():
                                element = elem
                                break
                    except:
                        pass
                
                # If not found by text, try CSS selector
                if not element:
                    try:
                        element = WebDriverWait(self.driver, 2).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    except:
                        continue
                
                if element and element.is_displayed() and element.is_enabled():
                    self.logger.logger.info(f"Found filter option: {element.text}")
                    self._simulate_human_click(element)
                    self.logger.logger.info(f"Clicked filter option with selector: {selector}")
                    return True
                    
            except Exception as e:
                self.logger.logger.debug(f"Failed to click filter option with selector {selector}: {e}")
                continue
        
        self.logger.logger.warning("Could not click filter option")
        return False
    
    def _click_apply_button(self) -> bool:
        """Click the apply button if present."""
        apply_selectors = [
            "button[data-control-name='filter_show_results']",
            "[data-test-id='apply-filters']",
            ".search-s-facet__apply-button",
            "button:contains('Show results')",
            "button:contains('Apply')",
            ".filter-apply-button",
            ".search-reusables__filter-binary-toggle__apply-button",
            "button[aria-label*='Apply']",
            "button[aria-label*='Show']"
        ]
        
        for selector in apply_selectors:
            try:
                apply_button = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                
                if apply_button.is_displayed():
                    self._simulate_human_click(apply_button)
                    self.logger.logger.debug("Clicked apply filter button")
                    time.sleep(random.uniform(1.0, 2.0))
                    return True
            except:
                continue
        
        self.logger.logger.debug("No apply button found - filter may auto-apply")
        return False
    
    def _verify_filter_applied(self, days: int) -> bool:
        """
        Verify that the date filter was successfully applied.
        
        Args:
            days: Number of days the filter should be set to
            
        Returns:
            True if filter appears to be applied, False otherwise
        """
        try:
            # Look for filter pills that indicate the filter is applied
            if days == 1:
                pill_text = "Past 24 hours"
            elif days == 7:
                pill_text = "Past week"
            elif days == 30:
                pill_text = "Past month"
            else:
                pill_text = f"Past {days} days"
            
            # Look for the filter pill
            pill_selectors = [
                f"//*[contains(text(), '{pill_text}')]",
                f"//span[contains(text(), '{pill_text}')]",
                f"//button[contains(text(), '{pill_text}')]",
                f"//div[contains(text(), '{pill_text}')]"
            ]
            
            for selector in pill_selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    if element.is_displayed():
                        self.logger.logger.info(f"✅ Date filter verified: found '{pill_text}' pill")
                        return True
                except:
                    continue
            
            self.logger.logger.warning(f"⚠️ Could not verify date filter pill for '{pill_text}'")
            return False
            
        except Exception as e:
            self.logger.logger.error(f"Error verifying date filter: {e}")
            return False

    def apply_work_arrangement_filter(self, work_arrangement: str) -> bool:
        """
        Apply Work Arrangement filter (e.g., "Remote", "On-site", "Hybrid").
        
        Args:
            work_arrangement: The work arrangement to filter for ("Remote", "On-site", "Hybrid")
            
        Returns:
            True if filter was applied successfully, False otherwise
        """
        try:
            self.logger.logger.info(f"Applying Work Arrangement filter: {work_arrangement}")
            
            # First, open the "All filters" modal
            if not self._open_all_filters_modal():
                return False
            
            # Look for the "Work arrangement" section
            work_arrangement_selectors = [
                "//h3[contains(text(), 'Work arrangement')]",
                "//h3[contains(text(), 'Work Arrangement')]",
                "//div[contains(text(), 'Work arrangement')]",
                "//div[contains(text(), 'Work Arrangement')]"
            ]
            
            work_arrangement_header = None
            for selector in work_arrangement_selectors:
                try:
                    work_arrangement_header = self.driver.find_element(By.XPATH, selector)
                    if work_arrangement_header.is_displayed():
                        break
                except:
                    continue
            
            if not work_arrangement_header:
                self.logger.logger.warning("Could not find Work arrangement filter section")
                return False
            
            # Click on the work arrangement header to expand options
            try:
                work_arrangement_header.click()
                time.sleep(2)
            except Exception as e:
                self.logger.logger.error(f"Error clicking Work arrangement header: {e}")
                return False
            
            # Look for the specific work arrangement option
            option_selectors = [
                f"//*[contains(text(), '{work_arrangement}')]",
                f"//label[contains(text(), '{work_arrangement}')]",
                f"//span[contains(text(), '{work_arrangement}')]",
                f"//div[contains(text(), '{work_arrangement}')]"
            ]
            
            target_option = None
            for selector in option_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and work_arrangement.lower() in element.text.lower():
                            target_option = element
                            break
                    if target_option:
                        break
                except:
                    continue
            
            if not target_option:
                self.logger.logger.warning(f"Could not find '{work_arrangement}' option in Work arrangement filter")
                return False
            
            # Click the option
            try:
                target_option.click()
                time.sleep(1)
                self.logger.logger.info(f"✅ Work arrangement filter '{work_arrangement}' applied")
                return True
            except Exception as e:
                self.logger.logger.error(f"Error clicking work arrangement option: {e}")
                return False
                
        except Exception as e:
            self.logger.logger.error(f"Error applying work arrangement filter: {e}")
            return False

    def apply_experience_level_filter(self, experience_level: str) -> bool:
        """
        Apply Experience Level filter.
        
        Args:
            experience_level: The experience level to filter for ("Entry level", "Associate", "Mid-Senior level", "Director", "Executive")
            
        Returns:
            True if filter was applied successfully, False otherwise
        """
        try:
            self.logger.logger.info(f"Applying Experience Level filter: {experience_level}")
            
            # First, open the "All filters" modal
            if not self._open_all_filters_modal():
                return False
            
            # Look for the "Experience level" section
            experience_selectors = [
                "//h3[contains(text(), 'Experience level')]",
                "//h3[contains(text(), 'Experience Level')]",
                "//div[contains(text(), 'Experience level')]",
                "//div[contains(text(), 'Experience Level')]"
            ]
            
            experience_header = None
            for selector in experience_selectors:
                try:
                    experience_header = self.driver.find_element(By.XPATH, selector)
                    if experience_header.is_displayed():
                        break
                except:
                    continue
            
            if not experience_header:
                self.logger.logger.warning("Could not find Experience level filter section")
                return False
            
            # Click on the experience level header to expand options
            try:
                experience_header.click()
                time.sleep(2)
            except Exception as e:
                self.logger.logger.error(f"Error clicking Experience level header: {e}")
                return False
            
            # Look for the specific experience level option
            option_selectors = [
                f"//*[contains(text(), '{experience_level}')]",
                f"//label[contains(text(), '{experience_level}')]",
                f"//span[contains(text(), '{experience_level}')]",
                f"//div[contains(text(), '{experience_level}')]"
            ]
            
            target_option = None
            for selector in option_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and experience_level.lower() in element.text.lower():
                            target_option = element
                            break
                    if target_option:
                        break
                except:
                    continue
            
            if not target_option:
                self.logger.logger.warning(f"Could not find '{experience_level}' option in Experience level filter")
                return False
            
            # Click the option
            try:
                target_option.click()
                time.sleep(1)
                self.logger.logger.info(f"✅ Experience level filter '{experience_level}' applied")
                return True
            except Exception as e:
                self.logger.logger.error(f"Error clicking experience level option: {e}")
                return False
                
        except Exception as e:
            self.logger.logger.error(f"Error applying experience level filter: {e}")
            return False

    def apply_job_type_filter(self, job_type: str) -> bool:
        """
        Apply Job Type filter.
        
        Args:
            job_type: The job type to filter for ("Full-time", "Part-time", "Contract", "Temporary", "Internship")
            
        Returns:
            True if filter was applied successfully, False otherwise
        """
        try:
            self.logger.logger.info(f"Applying Job Type filter: {job_type}")
            
            # First, open the "All filters" modal
            if not self._open_all_filters_modal():
                return False
            
            # Look for the "Job type" section
            job_type_selectors = [
                "//h3[contains(text(), 'Job type')]",
                "//h3[contains(text(), 'Job Type')]",
                "//div[contains(text(), 'Job type')]",
                "//div[contains(text(), 'Job Type')]"
            ]
            
            job_type_header = None
            for selector in job_type_selectors:
                try:
                    job_type_header = self.driver.find_element(By.XPATH, selector)
                    if job_type_header.is_displayed():
                        break
                except:
                    continue
            
            if not job_type_header:
                self.logger.logger.warning("Could not find Job type filter section")
                return False
            
            # Click on the job type header to expand options
            try:
                job_type_header.click()
                time.sleep(2)
            except Exception as e:
                self.logger.logger.error(f"Error clicking Job type header: {e}")
                return False
            
            # Look for the specific job type option
            option_selectors = [
                f"//*[contains(text(), '{job_type}')]",
                f"//label[contains(text(), '{job_type}')]",
                f"//span[contains(text(), '{job_type}')]",
                f"//div[contains(text(), '{job_type}')]"
            ]
            
            target_option = None
            for selector in option_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and job_type.lower() in element.text.lower():
                            target_option = element
                            break
                    if target_option:
                        break
                except:
                    continue
            
            if not target_option:
                self.logger.logger.warning(f"Could not find '{job_type}' option in Job type filter")
                return False
            
            # Click the option
            try:
                target_option.click()
                time.sleep(1)
                self.logger.logger.info(f"✅ Job type filter '{job_type}' applied")
                return True
            except Exception as e:
                self.logger.logger.error(f"Error clicking job type option: {e}")
                return False
                
        except Exception as e:
            self.logger.logger.error(f"Error applying job type filter: {e}")
            return False

    def _open_all_filters_modal(self) -> bool:
        """
        Open the "All filters" modal on LinkedIn.
        
        Returns:
            True if modal was opened successfully, False otherwise
        """
        try:
            # Look for the "All filters" button
            all_filters_selectors = [
                "button.artdeco-pill.search-reusables__all-filters-pill-button",
                "button[aria-label*='Show all filters']",
                "button[aria-label*='All filters']",
                "//button[contains(text(), 'All filters')]",
                "//button[contains(text(), 'All Filters')]",
                "//span[contains(text(), 'All filters')]",
                "//span[contains(text(), 'All Filters')]"
            ]
            
            all_filters_button = None
            for selector in all_filters_selectors:
                try:
                    if selector.startswith("//"):
                        # XPath selector
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        # CSS selector
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            all_filters_button = element
                            break
                    if all_filters_button:
                        break
                except:
                    continue
            
            if not all_filters_button:
                self.logger.logger.warning("Could not find 'All filters' button")
                return False
            
            # Click the "All filters" button
            try:
                all_filters_button.click()
                time.sleep(3)  # Wait for modal to open
                self.logger.logger.info("✅ 'All filters' modal opened successfully")
                return True
            except Exception as e:
                self.logger.logger.error(f"Error clicking 'All filters' button: {e}")
                return False
                
        except Exception as e:
            self.logger.logger.error(f"Error opening 'All filters' modal: {e}")
            return False

    def apply_all_filters(self, date_posted_days: Optional[int] = None, work_arrangement: Optional[str] = None, 
                         experience_level: Optional[str] = None, job_type: Optional[str] = None) -> bool:
        """
        Apply multiple filters at once.
        
        Args:
            date_posted_days: Filter for jobs posted within X days
            work_arrangement: Work arrangement filter ("Remote", "On-site", "Hybrid")
            experience_level: Experience level filter ("Entry level", "Associate", etc.)
            job_type: Job type filter ("Full-time", "Part-time", etc.)
            
        Returns:
            True if all filters were applied successfully, False otherwise
        """
        try:
            self.logger.logger.info("Applying multiple filters...")
            
            # Collect all filters that need to be applied
            all_filters = []
            if date_posted_days:
                all_filters.append(('date_posted', date_posted_days))
            if work_arrangement:
                all_filters.append(('work_arrangement', work_arrangement))
            if experience_level:
                all_filters.append(('experience_level', experience_level))
            if job_type:
                all_filters.append(('job_type', job_type))
            
            if not all_filters:
                self.logger.logger.info("No filters to apply")
                return True
            
            self.logger.logger.info(f"Applying {len(all_filters)} filters: {[f[1] for f in all_filters]}")
            
            # Open the "All filters" modal once for all filters
            if not self._open_all_filters_modal():
                self.logger.logger.warning("Could not open 'All filters' modal")
                return False
            
            # Apply each filter within the same modal session
            for filter_type, filter_value in all_filters:
                if filter_type == 'date_posted':
                    if not self._apply_date_filter_in_modal(filter_value):
                        self.logger.logger.warning(f"Date filter '{filter_value}' failed")
                elif filter_type == 'work_arrangement':
                    if not self._apply_work_arrangement_in_modal(filter_value):
                        self.logger.logger.warning(f"Work arrangement filter '{filter_value}' failed")
                elif filter_type == 'experience_level':
                    if not self._apply_experience_level_in_modal(filter_value):
                        self.logger.logger.warning(f"Experience level filter '{filter_value}' failed")
                elif filter_type == 'job_type':
                    if not self._apply_job_type_in_modal(filter_value):
                        self.logger.logger.warning(f"Job type filter '{filter_value}' failed")
            
            # Click "Show results" or "Apply" button to apply all filters
            if not self._click_apply_button():
                self.logger.logger.warning("Could not click apply button, but filters may still be applied")
            
            self.logger.logger.info("✅ All filters applied")
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Error applying filters: {e}")
            return False

    def _apply_work_arrangement_in_modal(self, work_arrangement: str) -> bool:
        """
        Apply Work Arrangement filter within an already open modal.
        
        Args:
            work_arrangement: The work arrangement to filter for ("Remote", "On-site", "Hybrid")
            
        Returns:
            True if filter was applied successfully, False otherwise
        """
        try:
            self.logger.logger.info(f"Applying Work Arrangement filter in modal: {work_arrangement}")
            
            # Find the modal content - try multiple selectors
            modal_content = None
            modal_selectors = [
                ".artdeco-modal__content.ember-view.display-flex.relative.mb4.flex-1.justify-center",
                ".artdeco-modal__content",
                "[class*='artdeco-modal__content']"
            ]
            
            for selector in modal_selectors:
                try:
                    modal_content = self.driver.find_element(By.CSS_SELECTOR, selector)
                    self.logger.logger.info(f"Found modal content with selector: {selector}")
                    break
                except:
                    continue
            
            if not modal_content:
                self.logger.logger.error("Could not find modal content")
                return False
            
            # Find the ul list within the modal
            ul_list = None
            ul_selectors = [
                "ul.list-style-none.flex-1",
                "ul.list-style-none",
                "ul[class*='list-style-none']"
            ]
            
            for selector in ul_selectors:
                try:
                    ul_list = modal_content.find_element(By.CSS_SELECTOR, selector)
                    self.logger.logger.info(f"Found ul list with selector: {selector}")
                    break
                except:
                    continue
            
            if not ul_list:
                self.logger.logger.error("Could not find ul list in modal")
                return False
            
            # Get all list items
            list_items = ul_list.find_elements(By.TAG_NAME, "li")
            self.logger.logger.info(f"Found {len(list_items)} filter items in the modal")
            
            # Find the Remote filter section by looking for the h3 with "Remote" text
            remote_item = None
            for item in list_items:
                try:
                    # Look for h3 element with "Remote" text
                    h3_elements = item.find_elements(By.TAG_NAME, "h3")
                    for h3 in h3_elements:
                        if h3.text.strip().lower() == "remote":
                            remote_item = item
                            self.logger.logger.info(f"✅ Found Remote filter section")
                            break
                    if remote_item:
                        break
                except Exception as e:
                    self.logger.logger.debug(f"Error checking item for Remote header: {e}")
                    continue
            
            if not remote_item:
                self.logger.logger.warning("Could not find Remote filter section")
                return False
            
            # Debug: Log all text content in the remote item
            try:
                all_text = remote_item.text
                self.logger.logger.info(f"Remote item text content: '{all_text}'")
            except Exception as e:
                self.logger.logger.warning(f"Could not get text content: {e}")
            
            # Look for the specific remote option within this item
            option_selectors = [
                f".//*[contains(text(), '{work_arrangement}')]",
                f".//label[contains(text(), '{work_arrangement}')]",
                f".//span[contains(text(), '{work_arrangement}')]",
                f".//div[contains(text(), '{work_arrangement}')]",
                f".//input[@type='checkbox' and @value='{work_arrangement}']",
                f".//input[@type='radio' and @value='{work_arrangement}']"
            ]
            
            target_option = None
            for selector in option_selectors:
                try:
                    elements = remote_item.find_elements(By.XPATH, selector)
                    self.logger.logger.info(f"Found {len(elements)} elements with selector: {selector}")
                    
                    for element in elements:
                        try:
                            element_text = element.text.strip()
                            element_value = element.get_attribute('value') or ''
                            self.logger.logger.info(f"Element text: '{element_text}', value: '{element_value}'")
                            
                            if (element.is_displayed() and 
                                (work_arrangement.lower() in element_text.lower() or 
                                 work_arrangement.lower() in element_value.lower())):
                                target_option = element
                                self.logger.logger.info(f"✅ Found matching element: '{element_text}'")
                                break
                        except Exception as e:
                            self.logger.logger.debug(f"Error checking element: {e}")
                            continue
                    
                    if target_option:
                        break
                except Exception as e:
                    self.logger.logger.debug(f"Error with selector {selector}: {e}")
                    continue
            
            if not target_option:
                # Try a more generic approach - look for any clickable element with the work arrangement
                try:
                    all_elements = remote_item.find_elements(By.XPATH, ".//*")
                    self.logger.logger.info(f"Found {len(all_elements)} total elements in remote item")
                    
                    for element in all_elements:
                        try:
                            if element.is_displayed() and element.is_enabled():
                                element_text = element.text.strip()
                                if work_arrangement.lower() in element_text.lower():
                                    self.logger.logger.info(f"Found potential target: '{element_text}'")
                                    target_option = element
                                    break
                        except:
                            continue
                except Exception as e:
                    self.logger.logger.debug(f"Error in generic search: {e}")
                
                if not target_option:
                    self.logger.logger.warning(f"Could not find '{work_arrangement}' option in Remote filter")
                    return False
            
            # Click the option
            try:
                target_option.click()
                time.sleep(1)
                self.logger.logger.info(f"✅ Work arrangement filter '{work_arrangement}' applied")
                return True
            except Exception as e:
                self.logger.logger.error(f"Error clicking work arrangement option: {e}")
                return False
                
        except Exception as e:
            self.logger.logger.error(f"Error applying work arrangement filter in modal: {e}")
            return False

    def _apply_experience_level_in_modal(self, experience_level: str) -> bool:
        """
        Apply Experience Level filter within an already open modal.
        
        Args:
            experience_level: The experience level to filter for ("Entry level", "Associate", etc.)
            
        Returns:
            True if filter was applied successfully, False otherwise
        """
        try:
            self.logger.logger.info(f"Applying Experience Level filter in modal: {experience_level}")
            
            # Find the modal content - try multiple selectors
            modal_content = None
            modal_selectors = [
                ".artdeco-modal__content.ember-view.display-flex.relative.mb4.flex-1.justify-center",
                ".artdeco-modal__content",
                "[class*='artdeco-modal__content']"
            ]
            
            for selector in modal_selectors:
                try:
                    modal_content = self.driver.find_element(By.CSS_SELECTOR, selector)
                    self.logger.logger.info(f"Found modal content with selector: {selector}")
                    break
                except:
                    continue
            
            if not modal_content:
                self.logger.logger.error("Could not find modal content")
                return False
            
            # Find the ul list within the modal
            ul_list = None
            ul_selectors = [
                "ul.list-style-none.flex-1",
                "ul.list-style-none",
                "ul[class*='list-style-none']"
            ]
            
            for selector in ul_selectors:
                try:
                    ul_list = modal_content.find_element(By.CSS_SELECTOR, selector)
                    self.logger.logger.info(f"Found ul list with selector: {selector}")
                    break
                except:
                    continue
            
            if not ul_list:
                self.logger.logger.error("Could not find ul list in modal")
                return False
            
            # Get all list items
            list_items = ul_list.find_elements(By.TAG_NAME, "li")
            self.logger.logger.info(f"Found {len(list_items)} filter items in the modal")
            
            # Find the Experience Level filter section by looking for the h3 with "Experience level" text
            experience_item = None
            for item in list_items:
                try:
                    # Look for h3 element with "Experience level" text
                    h3_elements = item.find_elements(By.TAG_NAME, "h3")
                    for h3 in h3_elements:
                        if h3.text.strip().lower() == "experience level":
                            experience_item = item
                            self.logger.logger.info(f"✅ Found Experience Level filter section")
                            break
                    if experience_item:
                        break
                except Exception as e:
                    self.logger.logger.debug(f"Error checking item for Experience Level header: {e}")
                    continue
            
            if not experience_item:
                self.logger.logger.warning("Could not find Experience Level filter section")
                return False
            
            # Debug: Log all text content in the experience item
            try:
                all_text = experience_item.text
                self.logger.logger.info(f"Experience item text content: '{all_text}'")
            except Exception as e:
                self.logger.logger.warning(f"Could not get text content: {e}")
            
            # Look for the specific experience option directly within this item
            # The Experience level section should already be expanded and ready for selection
            option_selectors = [
                f".//*[contains(text(), '{experience_level}')]",
                f".//label[contains(text(), '{experience_level}')]",
                f".//span[contains(text(), '{experience_level}')]",
                f".//div[contains(text(), '{experience_level}')]",
                f".//input[@type='checkbox' and @value='{experience_level}']",
                f".//input[@type='radio' and @value='{experience_level}']"
            ]
            
            target_option = None
            for selector in option_selectors:
                try:
                    elements = experience_item.find_elements(By.XPATH, selector)
                    self.logger.logger.info(f"Found {len(elements)} elements with selector: {selector}")
                    
                    for element in elements:
                        try:
                            element_text = element.text.strip()
                            element_value = element.get_attribute('value') or ''
                            self.logger.logger.info(f"Element text: '{element_text}', value: '{element_value}'")
                            
                            if (element.is_displayed() and 
                                (experience_level.lower() in element_text.lower() or 
                                 experience_level.lower() in element_value.lower())):
                                target_option = element
                                self.logger.logger.info(f"✅ Found matching element: '{element_text}'")
                                break
                        except Exception as e:
                            self.logger.logger.debug(f"Error checking element: {e}")
                            continue
                    
                    if target_option:
                        break
                except Exception as e:
                    self.logger.logger.debug(f"Error with selector {selector}: {e}")
                    continue
            
            if not target_option:
                # Try a more generic approach - look for any clickable element with the experience level
                try:
                    all_elements = experience_item.find_elements(By.XPATH, ".//*")
                    self.logger.logger.info(f"Found {len(all_elements)} total elements in experience item")
                    
                    for element in all_elements:
                        try:
                            if element.is_displayed() and element.is_enabled():
                                element_text = element.text.strip()
                                if experience_level.lower() in element_text.lower():
                                    self.logger.logger.info(f"Found potential target: '{element_text}'")
                                    target_option = element
                                    break
                        except:
                            continue
                except Exception as e:
                    self.logger.logger.debug(f"Error in generic search: {e}")
                
                if not target_option:
                    self.logger.logger.warning(f"Could not find '{experience_level}' option in Experience level filter")
                    return False
            
            # Click the option
            try:
                target_option.click()
                time.sleep(1)
                self.logger.logger.info(f"✅ Experience level filter '{experience_level}' applied")
                return True
            except Exception as e:
                self.logger.logger.error(f"Error clicking experience level option: {e}")
                return False
                
        except Exception as e:
            self.logger.logger.error(f"Error applying experience level filter in modal: {e}")
            return False

    def _apply_job_type_in_modal(self, job_type: str) -> bool:
        """
        Apply Job Type filter within an already open modal.
        
        Args:
            job_type: The job type to filter for ("Full-time", "Part-time", etc.)
            
        Returns:
            True if filter was applied successfully, False otherwise
        """
        try:
            self.logger.logger.info(f"Applying Job Type filter in modal: {job_type}")
            
            # Find the modal content - try multiple selectors
            modal_content = None
            modal_selectors = [
                ".artdeco-modal__content.ember-view.display-flex.relative.mb4.flex-1.justify-center",
                ".artdeco-modal__content",
                "[class*='artdeco-modal__content']"
            ]
            
            for selector in modal_selectors:
                try:
                    modal_content = self.driver.find_element(By.CSS_SELECTOR, selector)
                    self.logger.logger.info(f"Found modal content with selector: {selector}")
                    break
                except:
                    continue
            
            if not modal_content:
                self.logger.logger.error("Could not find modal content")
                return False
            
            # Find the ul list within the modal
            ul_list = None
            ul_selectors = [
                "ul.list-style-none.flex-1",
                "ul.list-style-none",
                "ul[class*='list-style-none']"
            ]
            
            for selector in ul_selectors:
                try:
                    ul_list = modal_content.find_element(By.CSS_SELECTOR, selector)
                    self.logger.logger.info(f"Found ul list with selector: {selector}")
                    break
                except:
                    continue
            
            if not ul_list:
                self.logger.logger.error("Could not find ul list in modal")
                return False
            
            # Get all list items
            list_items = ul_list.find_elements(By.TAG_NAME, "li")
            self.logger.logger.info(f"Found {len(list_items)} filter items in the modal")
            
            # Find the Job Type filter section by looking for the h3 with "Job type" text
            job_type_item = None
            for item in list_items:
                try:
                    # Look for h3 element with "Job type" text
                    h3_elements = item.find_elements(By.TAG_NAME, "h3")
                    for h3 in h3_elements:
                        if h3.text.strip().lower() == "job type":
                            job_type_item = item
                            self.logger.logger.info(f"✅ Found Job Type filter section")
                            break
                    if job_type_item:
                        break
                except Exception as e:
                    self.logger.logger.debug(f"Error checking item for Job Type header: {e}")
                    continue
            
            if not job_type_item:
                self.logger.logger.warning("Could not find Job Type filter section")
                return False
            
            # Debug: Log all text content in the job type item
            try:
                all_text = job_type_item.text
                self.logger.logger.info(f"Job type item text content: '{all_text}'")
            except Exception as e:
                self.logger.logger.warning(f"Could not get text content: {e}")
            
            # Look for the specific job type option within this item
            option_selectors = [
                f".//*[contains(text(), '{job_type}')]",
                f".//label[contains(text(), '{job_type}')]",
                f".//span[contains(text(), '{job_type}')]",
                f".//div[contains(text(), '{job_type}')]",
                f".//input[@type='checkbox' and @value='{job_type}']",
                f".//input[@type='radio' and @value='{job_type}']"
            ]
            
            target_option = None
            for selector in option_selectors:
                try:
                    elements = job_type_item.find_elements(By.XPATH, selector)
                    self.logger.logger.info(f"Found {len(elements)} elements with selector: {selector}")
                    
                    for element in elements:
                        try:
                            element_text = element.text.strip()
                            element_value = element.get_attribute('value') or ''
                            self.logger.logger.info(f"Element text: '{element_text}', value: '{element_value}'")
                            
                            if (element.is_displayed() and 
                                (job_type.lower() in element_text.lower() or 
                                 job_type.lower() in element_value.lower())):
                                target_option = element
                                self.logger.logger.info(f"✅ Found matching element: '{element_text}'")
                                break
                        except Exception as e:
                            self.logger.logger.debug(f"Error checking element: {e}")
                            continue
                    
                    if target_option:
                        break
                except Exception as e:
                    self.logger.logger.debug(f"Error with selector {selector}: {e}")
                    continue
            
            if not target_option:
                # Try a more generic approach - look for any clickable element with the job type
                try:
                    all_elements = job_type_item.find_elements(By.XPATH, ".//*")
                    self.logger.logger.info(f"Found {len(all_elements)} total elements in job type item")
                    
                    for element in all_elements:
                        try:
                            if element.is_displayed() and element.is_enabled():
                                element_text = element.text.strip()
                                if job_type.lower() in element_text.lower():
                                    self.logger.logger.info(f"Found potential target: '{element_text}'")
                                    target_option = element
                                    break
                        except:
                            continue
                except Exception as e:
                    self.logger.logger.debug(f"Error in generic search: {e}")
                
                if not target_option:
                    self.logger.logger.warning(f"Could not find '{job_type}' option in Job type filter")
                    return False
            
            # Click the option
            try:
                target_option.click()
                time.sleep(1)
                self.logger.logger.info(f"✅ Job type filter '{job_type}' applied")
                return True
            except Exception as e:
                self.logger.logger.error(f"Error clicking job type option: {e}")
                return False
                
        except Exception as e:
            self.logger.logger.error(f"Error applying job type filter in modal: {e}")
            return False
    
    def scrape_jobs_with_enhanced_date_filter(self, keywords: List[str], location: str, date_posted_days: Optional[int] = None, require_auth: bool = True, **kwargs) -> ScrapingResult:
        """
        Enhanced job scraping with authentication and date filter support.
        
        Workflow:
        1. Open linkedin.com/login and authenticate
        2. After login, navigate to the generated search URL
        3. Apply the "date posted" filter
        4. Start scraping jobs
        
        Args:
            keywords: List of job keywords to search for
            location: Location to search in
            date_posted_days: Filter for jobs posted within X days (1, 3, 7, 14, 30)
            require_auth: Whether authentication is required (default: True for LinkedIn)
            **kwargs: Additional search parameters
            
        Returns:
            ScrapingResult containing the scraped jobs and session info
        """
        # Start scraping session
        self.session = self.start_session(keywords, location)
        
        try:
            self.logger.logger.info(f"Starting enhanced LinkedIn job scrape for keywords: {keywords} in {location}")
            if date_posted_days:
                self.logger.logger.info(f"Will apply date filter: past {date_posted_days} days")
            
            # Set up WebDriver if not already done
            if not self.driver:
                # If we have a session manager, let it handle the WebDriver
                if self.session_manager and self.session_manager.driver:
                    self.driver = self.session_manager.driver
                    self.wait = self.session_manager.wait
                else:
                    self.setup_driver()
            
            # Step 1: Authenticate if required and not already authenticated
            if require_auth and not self.is_authenticated:
                self.logger.logger.info("Step 1: Authenticating with LinkedIn...")
                
                if not hasattr(self, 'username') or not hasattr(self, 'password'):
                    raise ValueError("Authentication credentials not provided but authentication is required")
                
                if not self.authenticate_with_session(self.username, self.password):
                    # Use the specific error message if available
                    error_message = getattr(self, 'last_auth_error', 'LinkedIn authentication failed')
                    self.logger.logger.info(f"Authentication failed, returning error: {error_message}")
                    return ScrapingResult(
                        success=False,
                        jobs=[],
                        session=self.session,
                        error_message=error_message
                    )
                
                self.logger.logger.info("✅ Authentication successful")
            elif self.is_authenticated:
                self.logger.logger.info("✅ Already authenticated")
            
            # Step 2: Build and navigate to the search URL
            self.logger.logger.info("Step 2: Navigating to search URL...")
            search_url = self.build_search_url(keywords, location, **kwargs)
            self.logger.logger.info(f"Generated search URL: {search_url}")
            
            # Navigate to the search URL
            self.driver.get(search_url)
            self._wait_for_page_load()
            
            # Wait for search results to load
            if not self.wait_for_search_results():
                return ScrapingResult(
                    success=False,
                    jobs=[],
                    session=self.session,
                    error_message="Search results failed to load"
                )
            
            self.logger.logger.info("✅ Successfully navigated to search results")
            
            # Step 3: Apply all filters if specified
            work_arrangement = kwargs.get('work_arrangement')
            experience_level = kwargs.get('experience_level')
            job_type = kwargs.get('job_type')
            
            if any([date_posted_days, work_arrangement, experience_level, job_type]):
                self.logger.logger.info("Step 3: Applying filters...")
                if date_posted_days:
                    self.logger.logger.info(f"  - Date filter: past {date_posted_days} days")
                if work_arrangement:
                    self.logger.logger.info(f"  - Work arrangement: {work_arrangement}")
                if experience_level:
                    self.logger.logger.info(f"  - Experience level: {experience_level}")
                if job_type:
                    self.logger.logger.info(f"  - Job type: {job_type}")
                
                filters_applied = self.apply_all_filters(
                    date_posted_days=date_posted_days,
                    work_arrangement=work_arrangement,
                    experience_level=experience_level,
                    job_type=job_type
                )
                
                if filters_applied:
                    self.logger.logger.info("✅ All filters applied successfully")
                else:
                    self.logger.logger.warning("⚠️ Some filters may have failed - continuing with available results")
            else:
                self.logger.logger.info("Step 3: No filters requested - scraping all jobs")
            
            # Step 4: Start scraping jobs
            self.logger.logger.info("Step 4: Starting job extraction...")
            
            # Extract jobs from the search page using right panel approach
            jobs = self.extract_jobs_from_search_page()
            
            # Process additional pages if configured and available
            if self.config.max_jobs_per_session > len(jobs):
                additional_jobs = self.extract_jobs_from_additional_pages()
                jobs.extend(additional_jobs)
            
            # Update session with extracted jobs count
            self.session.jobs_found = len(jobs)
            self.session.jobs_processed = len(jobs)
            
            self.logger.logger.info(f"✅ Enhanced LinkedIn scraping completed - extracted {len(jobs)} jobs total")
            
            return ScrapingResult(
                success=True,
                jobs=jobs,
                session=self.session,
                metadata={
                    "keywords": keywords,
                    "location": location,
                    "date_filter_days": date_posted_days,
                    "interface_version": self.interface_version,
                    "jobs_found_on_page": len(jobs),
                    "current_url": self.driver.current_url,
                    "authenticated": self.is_authenticated,
                    "search_url": search_url
                }
            )
            
        except Exception as e:
            self.logger.logger.error(f"Exception in scraping method: {e}")
            self.handle_error(e, "Enhanced LinkedIn job scraping with date filter")
            return ScrapingResult(
                success=False,
                jobs=[],
                session=self.session,
                error_message=str(e)
            )
        finally:
            # Only finish session if no security challenge was detected
            if not hasattr(self, 'last_auth_error') or not any(
                indicator in getattr(self, 'last_auth_error', '').lower() 
                for indicator in ['security challenge', 'captcha', 'puzzle', 'verification']
            ):
                self.finish_session()
            else:
                self.logger.logger.info("Security challenge detected - keeping browser open for manual intervention")
    
    def cleanup(self) -> None:
        """Enhanced cleanup with session management."""
        try:
            # Check if there's a security challenge that needs manual intervention
            if hasattr(self, 'last_auth_error') and any(
                indicator in self.last_auth_error.lower() 
                for indicator in ['security challenge', 'captcha', 'puzzle', 'verification']
            ):
                self.logger.logger.info("Security challenge detected - keeping browser open for manual intervention")
                # Don't close the browser or session manager
                return
            
            # Close session manager if using persistent session
            if self.session_manager:
                self.session_manager.close()
            
            # Call parent cleanup
            super().cleanup()
            
        except Exception as e:
            self.logger.logger.error(f"Error during enhanced cleanup: {e}")


def create_enhanced_linkedin_scraper(username: str, password: str, use_persistent_session: bool = True) -> EnhancedLinkedInScraper:
    """
    Create an enhanced LinkedIn scraper with session management.
    
    Args:
        username: LinkedIn username/email
        password: LinkedIn password
        use_persistent_session: Whether to use persistent session management
        
    Returns:
        Configured EnhancedLinkedInScraper instance
    """
    from src.config.config_manager import ConfigurationManager
    
    # Get configuration
    config_manager = ConfigurationManager()
    linkedin_config = config_manager.get_linkedin_settings()
    
    # Create scraping config
    config = ScrapingConfig(
        max_jobs_per_session=linkedin_config.max_jobs_per_search,
        delay_min=linkedin_config.delay_between_actions,
        delay_max=linkedin_config.delay_between_actions + 1.0,
        max_retries=3,
        page_load_timeout=30,
        site_name="linkedin",
        base_url="https://www.linkedin.com"
    )
    
    # Create session manager if requested
    session_manager = None
    if use_persistent_session:
        session_manager = SessionManager()
    
    # Create enhanced scraper
    scraper = EnhancedLinkedInScraper(config, session_manager)
    scraper.username = username
    scraper.password = password
    
    return scraper 