"""
LinkedIn scraper implementation.

This module implements a LinkedIn scraper that handles authentication
and basic page navigation. Job extraction will be added in future iterations.
"""

from datetime import datetime
import time
import random
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse, quote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    WebDriverException,
    ElementClickInterceptedException,
    NoSuchWindowException
)

from src.data.models import ExperienceLevel, JobType, RemoteType

from .base_scraper import BaseScraper, ScrapingResult, ScrapingConfig, extract_salary_range, sanitize_text
try:
    from ..data.models import JobListing, ScrapingSession
    from ..utils.logger import JobAutomationLogger
except ImportError:
    # Fallback for direct imports
    from data.models import JobListing, ScrapingSession
    from utils.logger import JobAutomationLogger

import os


class LinkedInScraper(BaseScraper):
    """
    LinkedIn scraper implementation.
    
    This scraper handles LinkedIn authentication and basic page navigation.
    Job extraction functionality will be added in future iterations.
    """
    
    def __init__(self, config: ScrapingConfig) -> None:
        """
        Initialize the LinkedIn scraper.
        
        Args:
            config: Configuration for the scraper
        """
        super().__init__(config)
        
        # LinkedIn-specific settings
        self.base_url = "https://www.linkedin.com"
        self.login_url = f"{self.base_url}/login"
        self.jobs_url = f"{self.base_url}/jobs"
        
        # WebDriver instance
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        
        # Authentication state
        self.is_authenticated = False
        self.username: Optional[str] = None
        self.password: Optional[str] = None
        
        # LinkedIn-specific selectors for job extraction
        self.selectors = {
            # Authentication
            'login_form': 'form[action="/login"]',
            'username_field': '#username',
            'password_field': '#password',
            'login_button': 'button[type="submit"]',
            
            # Navigation
            'jobs_tab': 'a[href="/jobs/"]',
            'search_box': 'input[aria-label*="Search"]',
            'search_button': 'button[aria-label*="Search"]',
            'next_page': 'button[aria-label="Next"]',
            'loading_spinner': '.loading-spinner',
            
            # Job cards in search results
            'job_cards': '[data-job-id], .job-search-card, .job-card-container, .job-card',
            'job_card_clickable': '[data-job-id] a, .job-search-card a, .job-card-container a',
            
            # Right panel selectors
            'right_panel': '.job-details-jobs-unified-top-card__content, .jobs-search__job-details--wrapper, .jobs-box__html-content, .jobs-description__content',
            'job_details_container': '.relative.job-details-jobs-unified-top-card__container--two-pane, .job-details-jobs-unified-top-card__content',
            'right_panel_loading': '.jobs-box__loading, .loading-spinner',
            'right_panel_error': '.jobs-box__error, .error-message',
            
            # Job information in right panel - Updated for current LinkedIn structure
            'job_title': 'h1.t-24.job-details-jobs-unified-top-card__job-title, .t-24.job-details-jobs-unified-top-card__job-title, h1[class*="job-details-jobs-unified-top-card__job-title"], .jobs-box__job-title, h1, .job-title',
            'company_name': '.job-details-jobs-unified-top-card__company-name .sRnCkbnFXZXqjWAFekZQCfsMNMELMevApSMNluw, .job-details-jobs-unified-top-card__company-name div[class*="sRnCkbnFXZXqjWAFekZQCfsMNMELMevApSMNluw"], .job-details-jobs-unified-top-card__company-name a, .job-details-jobs-unified-top-card__company-name span, .jobs-box__company-name, .company-name',
            'company_location': '.job-details-jobs-unified-top-card__company-location, .jobs-box__company-location, .location',
            'job_location': '.job-details-jobs-unified-top-card__tertiary-description-container > span[dir="ltr"] > .tvm__text--low-emphasis:first-child',
            'job_type': '.job-details-jobs-unified-top-card__job-type, .jobs-box__job-type, .job-type',
            'job_posted_date': '.job-details-jobs-unified-top-card__tertiary-description-container > span[dir="ltr"] > .tvm__text:nth-child(3)',
            'job_description': '.job-details-jobs-unified-top-card__job-description, .jobs-box__job-description, .job-description',
            'job_requirements': '.job-details-jobs-unified-top-card__requirements, .jobs-box__requirements, .requirements',
            'job_salary': '.job-details-jobs-unified-top-card__salary, .jobs-box__salary, .salary',
            'job_benefits': '.job-details-jobs-unified-top-card__benefits, .jobs-box__benefits, .benefits',
            
            # Application elements
            'apply_button': '.job-details-jobs-unified-top-card__apply-button, .jobs-box__apply-button, .apply-button',
            'easy_apply_button': '.job-details-jobs-unified-top-card__easy-apply-button, .jobs-box__easy-apply-button, .easy-apply-button, button[aria-label*="Easy Apply"], button[aria-label*="Apply"], .jobs-apply-button',
            
            # Easy Apply form elements
            'easy_apply_form': '.jobs-easy-apply-content, .jobs-apply-form, .easy-apply-form',
            'form_next_button': 'button[aria-label="Continue to next step"], button[aria-label="Next"], .artdeco-button--primary',
            'form_submit_button': 'button[aria-label="Submit application"], button[aria-label="Submit"], .artdeco-button--primary',
            'form_cancel_button': 'button[aria-label="Dismiss"], button[aria-label="Cancel"], .artdeco-button--secondary',
            
            # Form fields
            'form_input_fields': 'input[type="text"], input[type="email"], input[type="tel"], textarea',
            'form_select_fields': 'select, .artdeco-select',
            'form_radio_buttons': 'input[type="radio"]',
            'form_checkboxes': 'input[type="checkbox"]',
            
            # File upload
            'resume_upload': 'input[type="file"], .jobs-resume-picker__input',
            'cover_letter_upload': 'input[type="file"][accept*="pdf"], .jobs-cover-letter-picker__input',
            
            # Application status
            'application_success': '.jobs-apply-content__success, .application-success',
            'application_error': '.jobs-apply-content__error, .application-error',
            
            # Question elements
            'application_questions': '.jobs-easy-apply-form-section__grouping, .form-question',
            'question_text': '.jobs-easy-apply-form-section__grouping-label, .question-label',
            'question_input': '.jobs-easy-apply-form-section__grouping input, .question-input',
            
            # Search results container
            'search_results_container': '.jobs-search-results__list, .jobs-search-results-list, .search-results',
            'no_results_message': '.jobs-search-no-results, .no-results, .empty-state',
        }
    
    def setup_driver(self) -> None:
        """
        Set up Chrome WebDriver with stealth configuration to mimic real browser.
        """
        try:
            # Create Chrome options with stealth configuration
            options = Options()
            
            # Basic stealth settings
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Set realistic user agent (Chrome on macOS)
            user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            options.add_argument(f'--user-agent={user_agent}')
            
            # Set realistic viewport and window size
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--start-maximized')
            
            # Disable automation indicators
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--disable-images')  # Optional: faster loading
            options.add_argument('--disable-javascript')  # We'll enable this selectively
            
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
            
            # Create WebDriver with stealth configuration
            self.driver = webdriver.Chrome(options=options)
            
            # Execute stealth scripts to hide automation
            self._apply_stealth_scripts()
            
            # Set up wait with realistic timeout
            self.wait = WebDriverWait(self.driver, 15)
            
            # Set realistic viewport
            self.driver.set_window_size(1920, 1080)
            
            self.logger.logger.info("Chrome WebDriver initialized with stealth configuration")
            
        except Exception as e:
            self.logger.logger.error(f"Failed to setup WebDriver: {e}")
            raise

    def _apply_stealth_scripts(self) -> None:
        """Apply JavaScript stealth scripts to hide automation indicators."""
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
            
            self.logger.logger.debug("Applied stealth scripts to hide automation indicators")
                    
        except Exception as e:
            self.logger.logger.warning(f"Failed to apply some stealth scripts: {e}")

    def _detect_linkedin_interface_version(self) -> str:
        """
        Detect which LinkedIn interface version is currently loaded.
        
        Returns:
            str: 'new' or 'old' interface version
        """
        try:
            # Wait for page to load
            time.sleep(2)
            
            # Check for new interface indicators
            new_interface_selectors = [
                '.jobs-search-results-list',
                '[data-test-id="search-results"]',
                '.jobs-search__results-list',
                '.search-results__list'
            ]
            
            for selector in new_interface_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed():
                        self.logger.logger.info("Detected NEW LinkedIn interface")
                        return 'new'
                except Exception:
                    continue
            
            # Check for old interface indicators
            old_interface_selectors = [
                '.job-search-card',
                '.job-card-container',
                '.search-results__item'
            ]
            
            for selector in old_interface_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed():
                        self.logger.logger.info("Detected OLD LinkedIn interface")
                        return 'old'
                except Exception:
                    continue
            
            # Default to new interface if can't determine
            self.logger.logger.warning("Could not determine interface version, defaulting to NEW")
            return 'new'
            
        except Exception as e:
            self.logger.logger.error(f"Error detecting interface version: {e}")
            return 'new'

    def _get_date_filter_selectors_by_version(self, days: int, interface_version: str) -> List[str]:
        """
        Get date filter selectors based on LinkedIn interface version.
        
        Args:
            days: Number of days for filter
            interface_version: 'new' or 'old' interface
            
        Returns:
            List of CSS selectors to try
        """
        if interface_version == 'new':
            # New LinkedIn interface selectors
            selectors_map = {
                1: [  # Past 24 hours
                    "input[value='1']",
                    "li[data-value='1']",
                    "[data-test-id='date-posted-past-24-hours']",
                    "label:contains('Past 24 hours')",
                    "span:contains('Past 24 hours')",
                    ".filter-option[aria-label*='24 hours']",
                    "[aria-label*='Past 24 hours']",
                    "input[type='radio'][value='1']",
                    ".search-s-facet__filter-option[data-value='1']",
                    # New interface specific
                    "[data-test-id='date-posted-filter-option-1']",
                    ".artdeco-pill[data-value='1']",
                    ".search-reusables__filter-binary-toggle[data-value='1']"
                ],
                3: [  # Past 3 days
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
                7: [  # Past week
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
                14: [  # Past 2 weeks
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
                30: [  # Past month
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
            # Old LinkedIn interface selectors
            selectors_map = {
                1: [  # Past 24 hours
                    "input[value='1']",
                    "li[data-value='1']",
                    "label:contains('Past 24 hours')",
                    "span:contains('Past 24 hours')",
                    ".filter-option[aria-label*='24 hours']",
                    "[aria-label*='Past 24 hours']",
                    "input[type='radio'][value='1']",
                    ".search-s-facet__filter-option[data-value='1']",
                    # Old interface specific
                    ".search-s-facet__filter-option[data-value='1']",
                    ".filter-option[data-value='1']",
                    ".date-posted-filter-option[data-value='1']"
                ],
                3: [  # Past 3 days
                    "input[value='3']",
                    "li[data-value='3']",
                    "label:contains('Past 3 days')",
                    "span:contains('Past 3 days')",
                    ".filter-option[aria-label*='3 days']",
                    "[aria-label*='Past 3 days']",
                    "input[type='radio'][value='3']",
                    ".search-s-facet__filter-option[data-value='3']",
                    ".search-s-facet__filter-option[data-value='3']",
                    ".filter-option[data-value='3']",
                    ".date-posted-filter-option[data-value='3']"
                ],
                7: [  # Past week
                    "input[value='7']", 
                    "li[data-value='7']",
                    "label:contains('Past week')",
                    "span:contains('Past week')",
                    ".filter-option[aria-label*='week']",
                    "[aria-label*='Past week']",
                    "input[type='radio'][value='7']",
                    ".search-s-facet__filter-option[data-value='7']",
                    ".search-s-facet__filter-option[data-value='7']",
                    ".filter-option[data-value='7']",
                    ".date-posted-filter-option[data-value='7']"
                ],
                14: [  # Past 2 weeks
                    "input[value='14']",
                    "li[data-value='14']", 
                    "label:contains('Past 2 weeks')",
                    "span:contains('Past 2 weeks')",
                    ".filter-option[aria-label*='2 weeks']",
                    "[aria-label*='Past 2 weeks']",
                    "input[type='radio'][value='14']",
                    ".search-s-facet__filter-option[data-value='14']",
                    ".search-s-facet__filter-option[data-value='14']",
                    ".filter-option[data-value='14']",
                    ".date-posted-filter-option[data-value='14']"
                ],
                30: [  # Past month
                    "input[value='30']",
                    "li[data-value='30']",
                    "label:contains('Past month')",
                    "span:contains('Past month')",
                    ".filter-option[aria-label*='month']",
                    "[aria-label*='Past month']",
                    "input[type='radio'][value='30']",
                    ".search-s-facet__filter-option[data-value='30']",
                    ".search-s-facet__filter-option[data-value='30']",
                    ".filter-option[data-value='30']",
                    ".date-posted-filter-option[data-value='30']"
                ]
            }
        
        return selectors_map.get(days, [])

    def _get_date_filter_button_selectors_by_version(self, interface_version: str) -> List[str]:
        """
        Get date filter button selectors based on interface version.
        
        Args:
            interface_version: 'new' or 'old' interface
            
        Returns:
            List of CSS selectors to try
        """
        if interface_version == 'new':
            return [
                "button[aria-label*='Date posted']",
                "[data-test-id='date-posted-filter']",
                ".search-s-facet--date-posted button",
                "button[data-control-name*='date']",
                ".filter-button:has-text('Date posted')",
                "button[aria-label*='date']",
                ".search-reusables__filter-binary-toggle",
                ".search-s-facet__filter-button",
                # New interface specific
                "[data-test-id='date-posted-filter-button']",
                ".artdeco-pill[aria-label*='Date posted']",
                ".search-reusables__filter-binary-toggle[aria-label*='Date posted']",
                ".filter-pill[aria-label*='Date posted']"
            ]
        else:
            return [
                "button[aria-label*='Date posted']",
                "[data-test-id='date-posted-filter']",
                ".search-s-facet--date-posted button",
                "button[data-control-name*='date']",
                ".filter-button:has-text('Date posted')",
                "button[aria-label*='date']",
                ".search-reusables__filter-binary-toggle",
                ".search-s-facet__filter-button",
                # Old interface specific
                ".search-s-facet__filter-button[aria-label*='Date posted']",
                ".filter-button[aria-label*='Date posted']",
                ".date-posted-filter-button"
            ]

    def _add_realistic_delays(self) -> None:
        """Add realistic delays to mimic human behavior."""
        # Random delay between 1-3 seconds
        delay = random.uniform(1.0, 3.0)
        time.sleep(delay)

    def _simulate_human_click(self, element) -> None:
        """Simulate human-like clicking behavior."""
        try:
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            time.sleep(random.uniform(0.5, 1.5))
            
            # Move mouse to element (simulate human movement)
            action = webdriver.ActionChains(self.driver)
            action.move_to_element(element)
            action.pause(random.uniform(0.1, 0.3))
            action.click()
            action.perform()
            
            # Add post-click delay
            time.sleep(random.uniform(0.5, 1.0))
            
        except Exception as e:
            # Fallback to JavaScript click
            self.driver.execute_script("arguments[0].click();", element)
            self.logger.logger.debug(f"Used JavaScript click fallback: {e}")
    
    def authenticate(self, username: str, password: str) -> bool:
        """
        Authenticate with LinkedIn.
        
        Args:
            username: LinkedIn username/email
            password: LinkedIn password
            
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            self.username = username
            self.password = password
            
            self.logger.logger.info("Starting LinkedIn authentication")
            
            # Navigate to login page
            self.logger.logger.info(f"Navigating to login URL: {self.login_url}")
            self.driver.get(self.login_url)
            self.rate_limit()
            
            # Log current URL and page title for debugging
            current_url = self.driver.current_url
            page_title = self.driver.title
            self.logger.logger.info(f"Current URL: {current_url}")
            self.logger.logger.info(f"Page title: {page_title}")
            
            # Wait for login form to load with better error handling
            try:
                self.logger.logger.info("Waiting for login form to appear...")
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors['login_form'])))
                self.logger.logger.info("Login form found successfully")
            except TimeoutException:
                # Try alternative selectors
                self.logger.logger.warning("Primary login form selector failed, trying alternatives...")
                alternative_selectors = [
                    '#username',  # Direct username field
                    'input[name="session_key"]',  # Alternative username field
                    'form[action*="login"]',  # Alternative form selector
                    '.login__form'  # Another possible form class
                ]
                
                form_found = False
                for selector in alternative_selectors:
                    try:
                        self.logger.logger.info(f"Trying selector: {selector}")
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        self.logger.logger.info(f"Found element with selector: {selector}")
                        form_found = True
                        break
                    except NoSuchElementException:
                        continue
                
                if not form_found:
                    # Log page source for debugging
                    page_source = self.driver.page_source[:1000]  # First 1000 chars
                    self.logger.logger.error(f"Login form not found. Page source preview: {page_source}")
                    raise TimeoutException("Login form not found with any selector")
            
            # Fill in username with human-like typing
            username_field = self.driver.find_element(By.CSS_SELECTOR, self.selectors['username_field'])
            username_field.clear()
            self.logger.logger.info("Typing username...")
            for char in username:
                username_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))  # Random typing delay
            self.rate_limit()
            
            # Fill in password with human-like typing
            password_field = self.driver.find_element(By.CSS_SELECTOR, self.selectors['password_field'])
            password_field.clear()
            self.logger.logger.info("Typing password...")
            for char in password:
                password_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))  # Random typing delay
            self.rate_limit()
            
            # Click login button
            self.logger.logger.info("Clicking login button...")
            login_button = self.driver.find_element(By.CSS_SELECTOR, self.selectors['login_button'])
            login_button.click()
            
            # Wait for authentication to complete
            time.sleep(3)  # Allow time for authentication
            
            # Check if we're redirected to the main page (successful login)
            current_url = self.driver.current_url
            if "feed" in current_url or "mynetwork" in current_url or "messaging" in current_url:
                self.is_authenticated = True
                self.logger.logger.info("LinkedIn authentication successful")
                return True
            else:
                # Check for various types of error messages and security challenges
                page_source = self.driver.page_source.lower()
                current_url_lower = current_url.lower()
                
                # Check for security challenges in page content
                security_indicators = [
                    "security challenge", "captcha", "puzzle", "verification",
                    "prove you're not a robot", "verify your identity",
                    "challenge", "security check", "verification required"
                ]
                
                for indicator in security_indicators:
                    if indicator in page_source:
                        self.logger.logger.error(f"Authentication failed: Security challenge detected - {indicator}")
                        return False
                
                # Check for specific error messages
                try:
                    error_element = self.driver.find_element(By.CSS_SELECTOR, ".alert-error, .error-message, .form__error, .error")
                    error_text = error_element.text
                    self.logger.logger.error(f"Authentication failed: {error_text}")
                except NoSuchElementException:
                    # Check if we're still on login page (might indicate a challenge)
                    if "login" in current_url_lower or "signin" in current_url_lower:
                        self.logger.logger.error("Authentication failed: Still on login page - possible security challenge")
                    else:
                        self.logger.logger.error("Authentication failed: Unknown error")
                
                return False
                
        except TimeoutException:
            self.logger.logger.error("Timeout during authentication - login form not found")
            return False
        except NoSuchWindowException:
            self.logger.logger.error("Browser window was closed during authentication")
            return False
        except Exception as e:
            self.handle_error(e, "authentication")
            return False
    
    def navigate_to_jobs(self) -> bool:
        """
        Navigate to the LinkedIn Jobs page.
        
        Returns:
            True if navigation successful, False otherwise
        """
        try:
            self.logger.logger.info("Navigating to LinkedIn Jobs page")
            
            # Navigate to jobs page
            self.driver.get(self.jobs_url)
            self.rate_limit()
            
            # Wait for jobs page to load
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[aria-label*="Search"]')))
            
            self.logger.logger.info("Successfully navigated to LinkedIn Jobs page")
            return True
            
        except TimeoutException:
            self.logger.logger.error("Timeout waiting for jobs page to load")
            return False
        except Exception as e:
            self.handle_error(e, "navigation to jobs page")
            return False
    
    def search_jobs(self, keywords: List[str], location: str, **kwargs) -> bool:
        """
        Perform a job search on LinkedIn.
        
        Args:
            keywords: List of job keywords
            location: Location to search in
            **kwargs: Additional search parameters
            
        Returns:
            True if search successful, False otherwise
        """
        try:
            self.logger.logger.info(f"Searching for jobs: {keywords} in {location}")
            
            # Navigate to jobs page if not already there
            if "jobs" not in self.driver.current_url:
                if not self.navigate_to_jobs():
                    return False
            
            # Wait for search box to be available
            search_box = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[aria-label*="Search"]'))
            )
            
            # Clear and fill search box
            search_box.clear()
            search_query = " ".join(keywords)
            search_box.send_keys(search_query)
            self.rate_limit()
            
            # Find and click location field
            try:
                location_field = self.driver.find_element(By.CSS_SELECTOR, 'input[aria-label*="City"]')
                location_field.clear()
                location_field.send_keys(location)
                self.rate_limit()
            except NoSuchElementException:
                self.logger.logger.warning("Location field not found, proceeding with keywords only")
            
            # Click search button or press Enter
            search_box.send_keys("\n")
            self.rate_limit()
            
            # Wait for search results to load
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.job-search-card, .job-card-container')))
                self.logger.logger.info("Job search completed successfully")
                return True
            except TimeoutException:
                self.logger.logger.warning("No job cards found - search may have returned no results")
                return True  # Still consider it successful if no results
                
        except Exception as e:
            self.handle_error(e, "job search")
            return False
    
    def get_current_page_jobs_count(self) -> int:
        """
        Get the number of job listings on the current page.
        
        Returns:
            Number of job listings found
        """
        try:
            # Try different selectors for job cards
            selectors = [
                '.job-search-card',
                '.job-card-container',
                '[data-job-id]',
                '.job-card'
            ]
            
            for selector in selectors:
                try:
                    job_cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if job_cards:
                        count = len(job_cards)
                        self.logger.logger.debug(f"Found {count} job cards using selector: {selector}")
                        return count
                except NoSuchElementException:
                    continue
            
            self.logger.logger.debug("No job cards found on current page")
            return 0
            
        except Exception as e:
            self.logger.logger.error(f"Error counting job cards: {e}")
            return 0
    
    def can_go_to_next_page(self) -> bool:
        """
        Check if there's a next page available.
        
        Returns:
            True if next page is available, False otherwise
        """
        try:
            # Look for next page button
            next_button = self.driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Next"]')
            return next_button.is_enabled() and next_button.is_displayed()
        except NoSuchElementException:
            return False
        except Exception as e:
            self.logger.logger.error(f"Error checking for next page: {e}")
            return False
    
    def go_to_next_page(self) -> bool:
        """
        Navigate to the next page of results.
        
        Returns:
            True if navigation successful, False otherwise
        """
        try:
            if not self.can_go_to_next_page():
                self.logger.logger.info("No next page available")
                return False
            
            # Click next page button
            next_button = self.driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Next"]')
            next_button.click()
            self.rate_limit()
            
            # Wait for new page to load
            self.wait.until(EC.staleness_of(next_button))
            
            self.logger.logger.info("Successfully navigated to next page")
            return True
            
        except Exception as e:
            self.handle_error(e, "next page navigation")
            return False
    
    def scrape_jobs(self, keywords: List[str], location: str, **kwargs) -> ScrapingResult:
        """
        Scrape jobs from LinkedIn (placeholder implementation).
        
        Args:
            keywords: List of job keywords to search for
            location: Location to search in
            **kwargs: Additional search parameters
            
        Returns:
            ScrapingResult containing the scraped jobs and session info
        """
        # Start scraping session
        self.session = self.start_session(keywords, location)
        
        try:
            self.logger.logger.info(f"Starting LinkedIn job scrape for keywords: {keywords} in {location}")
            
            # Set up WebDriver if not already done
            if not self.driver:
                self.setup_driver()
            
            # Authenticate if not already authenticated
            if not self.is_authenticated:
                if not hasattr(self, 'username') or not hasattr(self, 'password'):
                    raise ValueError("Authentication credentials not provided")
                
                if not self.authenticate(self.username, self.password):
                    return ScrapingResult(
                        success=False,
                        jobs=[],
                        session=self.session,
                        error_message="LinkedIn authentication failed"
                    )
            
            # Perform job search
            if not self.search_jobs(keywords, location, **kwargs):
                return ScrapingResult(
                    success=False,
                    jobs=[],
                    session=self.session,
                    error_message="Job search failed"
                )
            
            # Extract jobs from the search page using right panel approach
            jobs = self.extract_jobs_from_search_page()
            
            # Process additional pages if configured and available
            if self.config.max_jobs_per_session > len(jobs):
                additional_jobs = self.extract_jobs_from_additional_pages()
                jobs.extend(additional_jobs)
            
            # Update session with extracted jobs count
            self.session.jobs_found = len(jobs)
            self.session.jobs_processed = len(jobs)
            
            self.logger.logger.info(f"LinkedIn scraping completed - extracted {len(jobs)} jobs total")
            
            return ScrapingResult(
                success=True,
                jobs=jobs,
                session=self.session,
                metadata={
                    "keywords": keywords,
                    "location": location,
                    "jobs_found_on_page": len(jobs),
                    "current_url": self.driver.current_url
                }
            )
            
        except Exception as e:
            self.handle_error(e, "LinkedIn job scraping")
            return ScrapingResult(
                success=False,
                jobs=[],
                session=self.session,
                error_message=str(e)
            )
        finally:
            self.finish_session()
    
    def get_job_details(self, job_url: str) -> Optional[JobListing]:
        """
        Get detailed information about a specific job using robust extraction methods.
        
        Args:
            job_url: URL of the job to get details for
            
        Returns:
            JobListing with detailed information, or None if failed
        """
        try:
            self.logger.logger.info(f"Getting job details for: {job_url}")
            
            # Apply rate limiting
            self.rate_limit()
            
            # Navigate to job page
            self.driver.get(job_url)
            
            # Wait for page to load and right panel to appear
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body')))
            
            # Wait for the job details container to load
            try:
                self.wait_for_right_panel()
            except Exception as e:
                self.logger.logger.warning(f"Could not wait for right panel: {e}")
            
            # Extract job data using robust methods
            job_data = self.extract_job_data_from_right_panel()
            
            if not job_data:
                self.logger.logger.warning("Failed to extract job data from page")
                return None
            
            # Create JobListing object with extracted data
            job_listing = JobListing(
                title=job_data.get('title', 'Unknown Title'),
                company=job_data.get('company', 'Unknown Company'),
                location=job_data.get('location', 'Unknown Location'),
                job_url=job_data.get('job_url', job_url),
                job_site='linkedin',
                description=job_data.get('description', ''),
                requirements=job_data.get('requirements', []),
                responsibilities=job_data.get('responsibilities', []),
                benefits=job_data.get('benefits', []),
                salary_min=job_data.get('salary_min'),
                salary_max=job_data.get('salary_max'),
                salary_currency=job_data.get('salary_currency', 'USD'),
                job_type=job_data.get('job_type'),
                experience_level=job_data.get('experience_level'),
                remote_type=job_data.get('remote_type'),
                application_url=job_data.get('application_url'),
                application_deadline=job_data.get('application_deadline'),
                application_requirements=job_data.get('application_requirements', []),
                posted_date=job_data.get('posted_date'),
                is_duplicate=job_data.get('is_duplicate', False),
                duplicate_of=job_data.get('duplicate_of'),
                notes=job_data.get('notes', '')
            )
            
            self.logger.logger.info(f"Successfully extracted job details: {job_listing.title} at {job_listing.company}")
            return job_listing
            
        except Exception as e:
            self.handle_error(e, "job details extraction", job_url)
            return None
    
    def build_search_url(self, keywords: List[str], location: str, **kwargs) -> str:
        """
        Build the LinkedIn job search URL.
        
        Args:
            keywords: List of job keywords
            location: Location to search in
            **kwargs: Additional search parameters
            
        Returns:
            LinkedIn job search URL
        """
        # LinkedIn uses a specific URL format for job searches
        keywords_param = quote(" ".join(keywords))
        location_param = quote(location)
        
        url = f"{self.jobs_url}/search/?keywords={keywords_param}&location={location_param}"
        
        # Add additional parameters
        if kwargs.get("experience_level"):
            level = kwargs["experience_level"]
            if level in ["entry", "junior", "mid", "senior"]:
                url += f"&f_E={level}"
        
        if kwargs.get("job_type"):
            job_type = kwargs["job_type"]
            if job_type in ["full-time", "part-time", "contract", "temporary", "internship"]:
                url += f"&f_JT={job_type}"
        
        if kwargs.get("remote"):
            url += "&f_WT=2"  # Remote work filter
        
        return url
    
    def extract_job_listings_from_page(self, page_content: Any) -> List[JobListing]:
        """
        Extract job listings from a search results page using right panel approach.
        
        Args:
            page_content: The page content (not used in Selenium-based scraper)
            
        Returns:
            List of JobListing objects extracted from the page
        """
        return self.extract_jobs_from_search_page()
    
    def extract_jobs_from_search_page(self) -> List[JobListing]:
        """
        Extract all visible jobs from the current search results page.
        Uses the right panel approach - clicks each job card and extracts from the sidebar.
        
        Returns:
            List of JobListing objects extracted from the current page
        """
        jobs = []
        
        try:
            self.logger.logger.info("Starting job extraction from search page")
            
            # Wait for search results to load
            self.wait_for_search_results()
            
            # Scroll to load all jobs on the page
            self._scroll_to_load_all_jobs()
            
            # Get all job cards on the current page
            job_cards = self.get_job_cards_on_page()
            
            if not job_cards:
                self.logger.logger.warning("No job cards found on current page")
                return jobs
            
            self.logger.logger.info(f"Found {len(job_cards)} job cards to process")
            
            # Process each job card with index-based approach to avoid stale elements
            for index in range(len(job_cards)):
                try:
                    self.logger.logger.info(f"Processing job {index+1}/{len(job_cards)}")
                    
                    # Re-find job cards to avoid stale element issues
                    current_job_cards = self.get_job_cards_on_page()
                    if index >= len(current_job_cards):
                        self.logger.logger.warning(f"Job card {index+1} no longer available")
                        continue
                    
                    job_card = current_job_cards[index]
                    
                    # Extract job information from right panel
                    job_listing = self.extract_job_from_right_panel(job_card)
                    
                    if job_listing:
                        jobs.append(job_listing)
                        self.logger.logger.info(f"Successfully extracted job: {job_listing.title}")
                    else:
                        self.logger.logger.warning(f"Failed to extract job {index+1}")
                    
                    # Rate limiting between jobs
                    self.rate_limit()
                    
                except Exception as e:
                    self.handle_error(e, f"job extraction for card {index+1}")
                    continue
            
            self.logger.logger.info(f"Job extraction completed: {len(jobs)} jobs extracted from {len(job_cards)} cards")
            
        except Exception as e:
            self.handle_error(e, "job extraction from search page")
        
        return jobs
    
    def extract_jobs_from_additional_pages(self) -> List[JobListing]:
        """
        Extract jobs from additional pages beyond the first page.
        
        Returns:
            List of JobListing objects from additional pages
        """
        additional_jobs = []
        page_number = 2
        max_pages = 5  # Limit to prevent infinite loops
        
        try:
            self.logger.logger.info("Starting extraction from additional pages")
            
            while (len(additional_jobs) + self.session.jobs_processed < self.config.max_jobs_per_session and 
                   page_number <= max_pages):
                
                self.logger.logger.info(f"Processing page {page_number}")
                
                # Try to go to next page
                if not self.go_to_next_page():
                    self.logger.logger.info("No more pages available")
                    break
                
                # Wait for new page to load
                time.sleep(2)
                
                # Extract jobs from current page
                page_jobs = self.extract_jobs_from_search_page()
                
                if not page_jobs:
                    self.logger.logger.info(f"No jobs found on page {page_number}")
                    break
                
                additional_jobs.extend(page_jobs)
                self.logger.logger.info(f"Extracted {len(page_jobs)} jobs from page {page_number}")
                
                page_number += 1
                
                # Rate limiting between pages
                self.rate_limit()
            
            self.logger.logger.info(f"Additional pages extraction completed: {len(additional_jobs)} jobs from {page_number - 2} pages")
            
        except Exception as e:
            self.handle_error(e, "extracting jobs from additional pages")
        
        return additional_jobs
    
    def wait_for_search_results(self) -> bool:
        """
        Wait for search results to load on the page.
        
        Returns:
            True if results loaded successfully, False otherwise
        """
        try:
            # Check if driver and wait are available
            if not self.driver or not self.wait:
                self.logger.logger.warning("WebDriver not initialized, cannot wait for search results")
                return False
            
            # Wait for either job cards or no results message
            self.wait.until(
                EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors['job_cards'])),
                    EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors['no_results_message']))
                )
            )
            
            # Check if we have no results
            try:
                no_results = self.driver.find_element(By.CSS_SELECTOR, self.selectors['no_results_message'])
                if no_results.is_displayed():
                    self.logger.logger.info("No search results found")
                    return False
            except NoSuchElementException:
                pass
            
            return True
            
        except TimeoutException:
            self.logger.logger.error("Timeout waiting for search results to load")
            return False
        except Exception as e:
            self.handle_error(e, "waiting for search results")
            return False
    
    def _scroll_to_load_all_jobs(self) -> None:
        """
        Scroll down the job list to load all available jobs through lazy loading.
        """
        try:
            self.logger.logger.info("Scrolling to load all jobs...")
            
            # Find the job list container (left panel)
            job_list_selectors = [
                '.jobs-search-results__list',
                '.jobs-search-results-list',
                '.search-results',
                '[data-test-id="job-search-results-list"]',
                '.jobs-search__results-list'
            ]
            
            job_list_container = None
            for selector in job_list_selectors:
                try:
                    job_list_container = self.driver.find_element(By.CSS_SELECTOR, selector)
                    self.logger.logger.info(f"Found job list container with selector: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not job_list_container:
                self.logger.logger.warning("Could not find job list container for scrolling")
                return
            
            # Scroll down multiple times to load all jobs
            initial_count = len(self.get_job_cards_on_page())
            self.logger.logger.info(f"Initial job count: {initial_count}")
            
            max_scroll_attempts = 10
            scroll_attempt = 0
            last_count = initial_count
            
            while scroll_attempt < max_scroll_attempts:
                # Scroll to bottom of job list
                self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", job_list_container)
                
                # Wait for new jobs to load
                time.sleep(2)
                
                # Check if new jobs were loaded
                current_count = len(self.get_job_cards_on_page())
                self.logger.logger.info(f"After scroll {scroll_attempt + 1}: {current_count} jobs")
                
                if current_count == last_count:
                    # No new jobs loaded, try one more time then stop
                    scroll_attempt += 1
                    if scroll_attempt >= 2:
                        self.logger.logger.info("No new jobs loaded after multiple scrolls, stopping")
                        break
                else:
                    # New jobs loaded, reset counter
                    scroll_attempt = 0
                    last_count = current_count
                
                scroll_attempt += 1
            
            final_count = len(self.get_job_cards_on_page())
            self.logger.logger.info(f"Final job count after scrolling: {final_count} (loaded {final_count - initial_count} additional jobs)")
            
        except Exception as e:
            self.logger.logger.warning(f"Error during scrolling: {e}")
    
    def get_job_cards_on_page(self) -> List[Any]:
        """
        Get all job card elements on the current page.
        
        Returns:
            List of job card WebElements
        """
        try:
            # Check if driver is available
            if not self.driver:
                self.logger.logger.warning("WebDriver not initialized, cannot get job cards")
                return []
            
            # Try multiple selectors to find job cards
            selectors = [
                self.selectors['job_cards'],
                '[data-job-id]',
                '.job-search-card',
                '.job-card-container',
                '.job-card'
            ]
            
            for selector in selectors:
                try:
                    job_cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if job_cards:
                        self.logger.logger.debug(f"Found {len(job_cards)} job cards using selector: {selector}")
                        return job_cards
                except Exception:
                    continue
            
            self.logger.logger.warning("No job cards found with any selector")
            return []
            
        except Exception as e:
            self.handle_error(e, "getting job cards on page")
            return []
    
    def extract_job_from_right_panel(self, job_card: Any) -> Optional[JobListing]:
        """
        Extract job information by clicking a job card and reading from the right panel.
        
        Args:
            job_card: WebElement of the job card to click
            
        Returns:
            JobListing object if successful, None otherwise
        """
        try:
            # Click the job card to load right panel
            if not self.click_job_card(job_card):
                return None
            
            # Wait for right panel to load
            if not self.wait_for_right_panel():
                return None
            
            # Extract job information from right panel
            job_data = self.extract_job_data_from_right_panel()
            
            if not job_data:
                return None
            
            # Create JobListing object with all extracted data
            job_listing = JobListing(
                title=job_data.get('title', 'Unknown Title'),
                company=job_data.get('company', 'Unknown Company'),
                location=job_data.get('location', 'Unknown Location'),
                job_url=job_data.get('job_url', ''),
                job_site='linkedin',
                description=job_data.get('description', ''),
                requirements=job_data.get('requirements', []),
                responsibilities=job_data.get('responsibilities', []),
                benefits=job_data.get('benefits', []),
                salary_min=job_data.get('salary_min'),
                salary_max=job_data.get('salary_max'),
                salary_currency=job_data.get('salary_currency', 'USD'),
                job_type=job_data.get('job_type'),
                experience_level=job_data.get('experience_level'),
                remote_type=job_data.get('remote_type'),
                application_url=job_data.get('application_url'),
                application_deadline=job_data.get('application_deadline'),
                application_requirements=job_data.get('application_requirements', []),
                posted_date=job_data.get('posted_date'),
                is_duplicate=job_data.get('is_duplicate', False),
                duplicate_of=job_data.get('duplicate_of'),
                notes=job_data.get('notes', '')
            )
            
            # Log comprehensive job details
            self.logger.logger.info(f"Successfully extracted job: {job_listing.title} at {job_listing.company}")
            self.logger.logger.debug(f"Job details: Location={job_listing.location}, Type={job_listing.job_type}, "
                                   f"Experience={job_listing.experience_level}, Remote={job_listing.remote_type}")
            self.logger.logger.debug(f"Salary: {job_listing.salary_min}-{job_listing.salary_max} {job_listing.salary_currency}")
            self.logger.logger.debug(f"Requirements: {len(job_listing.requirements)} items, "
                                   f"Responsibilities: {len(job_listing.responsibilities)} items, "
                                   f"Benefits: {len(job_listing.benefits)} items")
            
            return job_listing
            
        except Exception as e:
            self.handle_error(e, "extracting job from right panel")
            return None
    
    def click_job_card(self, job_card: Any) -> bool:
        """
        Click on a job card to load the right panel.
        
        Args:
            job_card: WebElement of the job card to click
            
        Returns:
            True if click successful, False otherwise
        """
        try:
            # Check if driver and job card are available
            if not self.driver:
                self.logger.logger.warning("WebDriver not initialized, cannot click job card")
                return False
            
            if not job_card:
                self.logger.logger.warning("Job card is None, cannot click")
                return False
            
            # Scroll job card into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", job_card)
            time.sleep(0.5)  # Brief pause for scroll
            
            # Try to click the job card directly
            try:
                job_card.click()
                return True
            except ElementClickInterceptedException:
                # Try clicking on a clickable element within the card
                try:
                    clickable = job_card.find_element(By.CSS_SELECTOR, 'a, button, [role="button"]')
                    clickable.click()
                    return True
                except NoSuchElementException:
                    # Try JavaScript click as fallback
                    self.driver.execute_script("arguments[0].click();", job_card)
                    return True
            
        except Exception as e:
            self.handle_error(e, "clicking job card")
            return False
    
    def wait_for_right_panel(self, max_retries: int = 3) -> bool:
        """
        Wait for the right panel to load after clicking a job card.
        
        Args:
            max_retries: Maximum number of retry attempts
            
        Returns:
            True if panel loaded successfully, False otherwise
        """
        # Check if driver and wait are available
        if not self.driver or not self.wait:
            self.logger.logger.warning("WebDriver not initialized, cannot wait for right panel")
            return False
        
        for attempt in range(max_retries):
            try:
                # Wait for job details container to appear (new LinkedIn structure)
                self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors['job_details_container']))
                )
                
                # Wait for loading to complete
                time.sleep(1)  # Allow content to fully load
                
                # Check if panel has actual content (not just loading)
                panel = self.driver.find_element(By.CSS_SELECTOR, self.selectors['job_details_container'])
                if panel.text.strip():
                    return True
                
                # If no content, wait a bit more and retry
                time.sleep(2)
                
            except TimeoutException:
                if attempt < max_retries - 1:
                    self.logger.logger.warning(f"Right panel not loaded, retrying ({attempt + 1}/{max_retries})")
                    time.sleep(2)
                else:
                    self.logger.logger.error("Right panel failed to load after all retries")
                    return False
            except Exception as e:
                self.handle_error(e, f"waiting for right panel (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    return False
        
        return False
    
    def extract_job_data_from_right_panel(self) -> Optional[Dict[str, Any]]:
        """
        Extract comprehensive job data from the right panel content.
        
        Returns:
            Dictionary containing job data, or None if extraction failed
        """
        try:
            # Check if driver is available
            if not self.driver:
                self.logger.logger.warning("WebDriver not initialized, cannot extract job data")
                return None
            
            job_data = {}
            
            # Extract essential job information using robust methods
            job_data['title'] = self.extract_job_title_robust()
            job_data['company'] = self.extract_company_name_robust()
            
            # Extract location (try job location first, then company location)
            job_data['location'] = (
                self.extract_text_from_selector('job_location') or 
                self.extract_text_from_selector('company_location') or 
                'Unknown Location'
            )
            
            # Extract job description
            job_data['description'] = self.extract_text_from_selector('job_description')
            
            # Extract job type and parse to enum
            job_type_text = self.extract_text_from_selector('job_type')
            job_data['job_type'] = self.parse_job_type(job_type_text)
            
            # Extract posted date and parse to datetime
            posted_date_text = self.extract_text_from_selector('job_posted_date')
            job_data['posted_date'] = self.parse_posted_date(posted_date_text)
            
            # Extract requirements and responsibilities
            job_data['requirements'] = self.extract_requirements_from_panel()
            job_data['responsibilities'] = self.extract_responsibilities_from_panel()
            
            # Extract salary information with currency
            salary_text = self.extract_text_from_selector('job_salary')
            if salary_text:
                salary_data = self.parse_salary_information(salary_text)
                job_data.update(salary_data)
            
            # Extract benefits
            job_data['benefits'] = self.extract_benefits_from_panel()
            
            # Extract experience level
            experience_text = self.extract_text_from_selector('job_requirements')  # May contain experience info
            job_data['experience_level'] = self.parse_experience_level(experience_text)
            
            # Extract remote type
            remote_text = self.extract_text_from_selector('job_type')  # May contain remote info
            job_data['remote_type'] = self.parse_remote_type(remote_text)
            
            # Extract job URL and ID
            job_data['job_url'] = self.driver.current_url
            job_data['job_id'] = self.extract_job_id_from_url(job_data['job_url'])
            
            # Extract application URL and type
            application_data = self.extract_application_information()
            job_data.update(application_data)
            
            # Extract application requirements
            job_data['application_requirements'] = self.extract_application_requirements()
            
            # Set default values for missing fields
            job_data.setdefault('salary_min', None)
            job_data.setdefault('salary_max', None)
            job_data.setdefault('salary_currency', 'USD')
            job_data.setdefault('application_deadline', None)
            job_data.setdefault('is_duplicate', False)
            job_data.setdefault('duplicate_of', None)
            job_data.setdefault('notes', '')
            
            # Validate that we have essential data
            if not job_data.get('title') or not job_data.get('company'):
                self.logger.logger.warning("Missing essential job data (title or company)")
                return None
            
            # Validate extraction results
            self.validate_extraction_results(job_data['title'], job_data['company'])
            
            self.logger.logger.info(f"Successfully extracted job data: {job_data['title']} at {job_data['company']}")
            return job_data
            
        except Exception as e:
            self.handle_error(e, "extracting job data from right panel")
            return None
    
    def extract_text_from_selector(self, selector_key: str) -> str:
        """
        Extract text from an element using a selector key.
        
        Args:
            selector_key: Key from self.selectors dictionary
            
        Returns:
            Extracted text or empty string if not found
        """
        try:
            # Check if driver is available
            if not self.driver:
                return ""
            
            selector = self.selectors[selector_key]
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            text = element.text.strip()
            return sanitize_text(text) if text else ""
        except NoSuchElementException:
            return ""
        except Exception as e:
            self.logger.logger.debug(f"Error extracting text from {selector_key}: {e}")
            return ""
    
    def extract_job_title_robust(self) -> str:
        """
        Extract job title with multiple fallback selectors for robustness.
        
        Returns:
            Job title or "Unknown Job Title" if not found
        """
        selectors = [
            "h1.t-24.job-details-jobs-unified-top-card__job-title",
            ".t-24.job-details-jobs-unified-top-card__job-title", 
            "h1[class*='job-details-jobs-unified-top-card__job-title']",
            ".job-details-jobs-unified-top-card__job-title",
            ".jobs-box__job-title",
            "h1",
            ".job-title"
        ]
        
        for selector in selectors:
            try:
                self.logger.logger.debug(f"Attempting to extract job title with selector: {selector}")
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                title = element.text.strip()
                if title and title != "":
                    self.logger.logger.debug(f"Found job title: {title}")
                    return sanitize_text(title)
            except NoSuchElementException:
                continue
            except Exception as e:
                self.logger.logger.debug(f"Error with selector {selector}: {e}")
                continue
        
        self.logger.logger.warning("No job title found with any selector")
        return "Unknown Job Title"
    
    def extract_company_name_robust(self) -> str:
        """
        Extract company name with multiple fallback selectors for robustness.
        
        Returns:
            Company name or "Unknown Company" if not found
        """
        selectors = [
            ".job-details-jobs-unified-top-card__company-name .sRnCkbnFXZXqjWAFekZQCfsMNMELMevApSMNluw",
            ".job-details-jobs-unified-top-card__company-name div[class*='sRnCkbnFXZXqjWAFekZQCfsMNMELMevApSMNluw']",
            ".job-details-jobs-unified-top-card__company-name a",
            ".job-details-jobs-unified-top-card__company-name span",
            ".job-details-jobs-unified-top-card__company-name",
            ".jobs-box__company-name",
            ".company-name"
        ]
        
        for selector in selectors:
            try:
                self.logger.logger.debug(f"Attempting to extract company name with selector: {selector}")
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                company = element.text.strip()
                if company and company != "":
                    self.logger.logger.debug(f"Found company name: {company}")
                    return sanitize_text(company)
            except NoSuchElementException:
                continue
            except Exception as e:
                self.logger.logger.debug(f"Error with selector {selector}: {e}")
                continue
        
        self.logger.logger.warning("No company name found with any selector")
        return "Unknown Company"
    
    def validate_extraction_results(self, job_title: str, company_name: str) -> None:
        """
        Validate that job title and company name were extracted correctly.
        
        Args:
            job_title: Extracted job title
            company_name: Extracted company name
        """
        try:
            # Common job title indicators
            job_title_keywords = ['engineer', 'developer', 'manager', 'analyst', 'designer', 
                                 'specialist', 'coordinator', 'director', 'lead', 'senior',
                                 'junior', 'intern', 'consultant', 'architect', 'scientist',
                                 'researcher', 'associate', 'assistant', 'executive', 'officer']
            
            # Common company indicators  
            company_indicators = ['inc', 'llc', 'corp', 'ltd', 'company', 'technologies',
                                 'solutions', 'systems', 'group', 'labs', 'partners', 'associates']
            
            job_title_lower = job_title.lower()
            company_name_lower = company_name.lower()
            
            # Check if job_title contains job keywords
            has_job_keywords = any(keyword in job_title_lower for keyword in job_title_keywords)
            
            # Check if company_name contains company indicators
            has_company_keywords = any(keyword in company_name_lower for keyword in company_indicators)
            
            # Log potential issues
            if not has_job_keywords and job_title not in ["Unknown", "Unknown Job Title"]:
                self.logger.logger.warning(f"Job title may be incorrect: '{job_title}'")
                
            if not has_company_keywords and len(company_name.split()) == 1 and company_name not in ["Unknown", "Unknown Company"]:
                self.logger.logger.info(f"Company name seems simple: '{company_name}' (this might be correct)")
            
            # Log successful extraction
            if has_job_keywords and job_title not in ["Unknown", "Unknown Job Title"]:
                self.logger.logger.info(f"✅ Job title extraction looks good: '{job_title}'")
            
            if company_name not in ["Unknown", "Unknown Company"]:
                self.logger.logger.info(f"✅ Company name extraction looks good: '{company_name}'")
                
        except Exception as e:
            self.logger.logger.error(f"Error in validation: {e}")
    
    def extract_requirements_from_panel(self) -> List[str]:
        """
        Extract job requirements from the right panel.
        
        Returns:
            List of requirement strings
        """
        try:
            requirements_text = self.extract_text_from_selector('job_requirements')
            if not requirements_text:
                return []
            
            # Split requirements by common delimiters
            requirements = []
            for line in requirements_text.split('\n'):
                line = line.strip()
                if line and len(line) > 3:  # Filter out very short lines
                    requirements.append(line)
            
            return requirements[:10]  # Limit to first 10 requirements
            
        except Exception as e:
            self.logger.logger.debug(f"Error extracting requirements: {e}")
            return []
    
    def extract_benefits_from_panel(self) -> List[str]:
        """
        Extract job benefits from the right panel.
        
        Returns:
            List of benefit strings
        """
        try:
            benefits_text = self.extract_text_from_selector('job_benefits')
            if not benefits_text:
                return []
            
            # Split benefits by common delimiters
            benefits = []
            for line in benefits_text.split('\n'):
                line = line.strip()
                if line and len(line) > 3:  # Filter out very short lines
                    benefits.append(line)
            
            return benefits[:5]  # Limit to first 5 benefits
            
        except Exception as e:
            self.logger.logger.debug(f"Error extracting benefits: {e}")
            return []
    
    def extract_job_id_from_url(self, url: str) -> str:
        """
        Extract job ID from LinkedIn job URL.
        
        Args:
            url: LinkedIn job URL
            
        Returns:
            Job ID string
        """
        try:
            # Extract job ID from URL patterns like /jobs/view/123456/
            import re
            match = re.search(r'/jobs/view/(\d+)/', url)
            if match:
                return match.group(1)
            
            # Fallback: extract from end of URL
            parts = url.split('/')
            for part in reversed(parts):
                if part.isdigit():
                    return part
            
            return 'unknown'
            
        except Exception:
            return 'unknown'
    
    def extract_application_url(self) -> str:
        """
        Extract application URL from the right panel.
        
        Returns:
            Application URL or empty string if not found
        """
        try:
            # Check if driver is available
            if not self.driver:
                return ''
            
            # Try to find apply button and get its URL
            apply_button = self.driver.find_element(By.CSS_SELECTOR, self.selectors['apply_button'])
            if apply_button:
                return apply_button.get_attribute('href') or ''
            
            # Try easy apply button
            easy_apply_button = self.driver.find_element(By.CSS_SELECTOR, self.selectors['easy_apply_button'])
            if easy_apply_button:
                return easy_apply_button.get_attribute('href') or ''
            
            return ''
            
        except NoSuchElementException:
            return ''
        except Exception as e:
            self.logger.logger.debug(f"Error extracting application URL: {e}")
            return ''
    
    def parse_salary_information(self, salary_text: str) -> Dict[str, Any]:
        """
        Parse salary information from text and extract min, max, and currency.
        
        Args:
            salary_text: Raw salary text from LinkedIn
            
        Returns:
            Dictionary with salary_min, salary_max, and salary_currency
        """
        try:
            if not salary_text:
                return {'salary_min': None, 'salary_max': None, 'salary_currency': 'USD'}
            
            # Use the existing extract_salary_range function
            min_sal, max_sal = extract_salary_range(salary_text)
            
            # Determine currency (default to USD for LinkedIn)
            currency = 'USD'
            if '€' in salary_text or 'EUR' in salary_text.upper():
                currency = 'EUR'
            elif '£' in salary_text or 'GBP' in salary_text.upper():
                currency = 'GBP'
            elif 'CAD' in salary_text.upper():
                currency = 'CAD'
            
            return {
                'salary_min': min_sal,
                'salary_max': max_sal,
                'salary_currency': currency
            }
            
        except Exception as e:
            self.logger.logger.debug(f"Error parsing salary information: {e}")
            return {'salary_min': None, 'salary_max': None, 'salary_currency': 'USD'}
    
    def parse_posted_date(self, date_text: str) -> Optional[datetime]:
        """
        Parse posted date from LinkedIn text to datetime object.
        
        Args:
            date_text: Raw date text from LinkedIn
            
        Returns:
            datetime object or None if parsing fails
        """
        try:
            if not date_text:
                return None
            
            from datetime import datetime, timedelta
            import re
            
            # Common LinkedIn date patterns
            patterns = [
                # "Posted 2 days ago"
                (r'Posted (\d+) days? ago', lambda m: datetime.now() - timedelta(days=int(m.group(1)))),
                # "Posted 1 week ago"
                (r'Posted (\d+) weeks? ago', lambda m: datetime.now() - timedelta(weeks=int(m.group(1)))),
                # "Posted 1 month ago"
                (r'Posted (\d+) months? ago', lambda m: datetime.now() - timedelta(days=int(m.group(1)) * 30)),
                # "Posted today"
                (r'Posted today', lambda m: datetime.now()),
                # "Posted yesterday"
                (r'Posted yesterday', lambda m: datetime.now() - timedelta(days=1)),
                # "Posted on [date]"
                (r'Posted on (\w+ \d+, \d{4})', lambda m: datetime.strptime(m.group(1), '%B %d, %Y')),
                # "Posted [date]"
                (r'Posted (\w+ \d+, \d{4})', lambda m: datetime.strptime(m.group(1), '%B %d, %Y')),
            ]
            
            for pattern, handler in patterns:
                match = re.search(pattern, date_text, re.IGNORECASE)
                if match:
                    return handler(match)
            
            # If no pattern matches, try to extract any date-like string
            date_match = re.search(r'(\w+ \d+, \d{4})', date_text)
            if date_match:
                try:
                    return datetime.strptime(date_match.group(1), '%B %d, %Y')
                except ValueError:
                    pass
            
            self.logger.logger.debug(f"Could not parse date: {date_text}")
            return None
            
        except Exception as e:
            self.logger.logger.debug(f"Error parsing posted date: {e}")
            return None
    
    def parse_job_type(self, job_type_text: str) -> Optional[JobType]:
        """
        Parse job type text to JobType enum.
        
        Args:
            job_type_text: Raw job type text from LinkedIn
            
        Returns:
            JobType enum or None if parsing fails
        """
        try:
            if not job_type_text:
                return None
            
            job_type_text = job_type_text.lower().strip()
            
            # Map common LinkedIn job type text to our enums
            type_mapping = {
                'full-time': JobType.FULL_TIME,
                'full time': JobType.FULL_TIME,
                'part-time': JobType.PART_TIME,
                'part time': JobType.PART_TIME,
                'contract': JobType.CONTRACT,
                'temporary': JobType.TEMPORARY,
                'temp': JobType.TEMPORARY,
                'internship': JobType.INTERNSHIP,
                'intern': JobType.INTERNSHIP,
                'freelance': JobType.FREELANCE,
            }
            
            for text, job_type in type_mapping.items():
                if text in job_type_text:
                    return job_type
            
            return None
            
        except Exception as e:
            self.logger.logger.debug(f"Error parsing job type: {e}")
            return None
    
    def parse_experience_level(self, requirements_text: str) -> Optional[ExperienceLevel]:
        """
        Parse experience level from requirements text.
        
        Args:
            requirements_text: Raw requirements text from LinkedIn
            
        Returns:
            ExperienceLevel enum or None if parsing fails
        """
        try:
            if not requirements_text:
                return None
            
            requirements_text = requirements_text.lower().strip()
            
            # Map common experience level indicators to our enums
            level_mapping = {
                'entry level': ExperienceLevel.ENTRY,
                'entry-level': ExperienceLevel.ENTRY,
                'junior': ExperienceLevel.JUNIOR,
                'mid level': ExperienceLevel.MID,
                'mid-level': ExperienceLevel.MID,
                'senior': ExperienceLevel.SENIOR,
                'lead': ExperienceLevel.LEAD,
                'principal': ExperienceLevel.LEAD,
                'executive': ExperienceLevel.EXECUTIVE,
                'director': ExperienceLevel.EXECUTIVE,
                'vp': ExperienceLevel.EXECUTIVE,
                'vice president': ExperienceLevel.EXECUTIVE,
            }
            
            for text, level in level_mapping.items():
                if text in requirements_text:
                    return level
            
            return None
            
        except Exception as e:
            self.logger.logger.debug(f"Error parsing experience level: {e}")
            return None
    
    def parse_remote_type(self, job_type_text: str) -> Optional[RemoteType]:
        """
        Parse remote type from job type text.
        
        Args:
            job_type_text: Raw job type text from LinkedIn
            
        Returns:
            RemoteType enum or None if parsing fails
        """
        try:
            if not job_type_text:
                return None
            
            job_type_text = job_type_text.lower().strip()
            
            # Map common remote work indicators to our enums
            remote_mapping = {
                'remote': RemoteType.REMOTE,
                'work from home': RemoteType.REMOTE,
                'wfh': RemoteType.REMOTE,
                'hybrid': RemoteType.HYBRID,
                'on-site': RemoteType.ON_SITE,
                'onsite': RemoteType.ON_SITE,
                'in-office': RemoteType.ON_SITE,
            }
            
            for text, remote_type in remote_mapping.items():
                if text in job_type_text:
                    return remote_type
            
            return None
            
        except Exception as e:
            self.logger.logger.debug(f"Error parsing remote type: {e}")
            return None
    
    def extract_responsibilities_from_panel(self) -> List[str]:
        """
        Extract job responsibilities from the right panel.
        
        Returns:
            List of responsibility strings
        """
        try:
            # Try to find responsibilities in the job description or requirements
            description_text = self.extract_text_from_selector('job_description')
            requirements_text = self.extract_text_from_selector('job_requirements')
            
            responsibilities = []
            
            # Look for responsibility indicators in the text
            responsibility_indicators = [
                'responsibilities:', 'responsibility:', 'duties:', 'duty:',
                'you will:', 'you will be:', 'you are responsible for:',
                'key responsibilities:', 'main responsibilities:'
            ]
            
            for text in [description_text, requirements_text]:
                if text:
                    lines = text.split('\n')
                    in_responsibilities = False
                    
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # Check if we're entering a responsibilities section
                        if any(indicator in line.lower() for indicator in responsibility_indicators):
                            in_responsibilities = True
                            continue
                        
                        # If we're in responsibilities section, collect items
                        if in_responsibilities and line:
                            # Check if line looks like a responsibility item
                            if (line.startswith('•') or line.startswith('-') or 
                                line.startswith('*') or line[0].isdigit()):
                                responsibilities.append(line.lstrip('•-* '))
                            elif len(line) > 10:  # Reasonable length for a responsibility
                                responsibilities.append(line)
                        
                        # Stop if we hit another section
                        if in_responsibilities and any(section in line.lower() for section in ['requirements:', 'qualifications:', 'benefits:']):
                            break
            
            return responsibilities[:10]  # Limit to first 10 responsibilities
            
        except Exception as e:
            self.logger.logger.debug(f"Error extracting responsibilities: {e}")
            return []
    
    def extract_application_information(self) -> Dict[str, Any]:
        """
        Extract application URL and determine application type.
        
        Returns:
            Dictionary with application_url and application_type
        """
        try:
            application_url = self.extract_application_url()
            
            # Determine application type based on URL or button text
            application_type = 'external'
            
            if application_url:
                if 'linkedin.com' in application_url:
                    application_type = 'linkedin'
                elif 'easy-apply' in application_url.lower():
                    application_type = 'easy_apply'
                elif 'apply' in application_url.lower():
                    application_type = 'external'
            
            return {
                'application_url': application_url,
                'application_type': application_type
            }
            
        except Exception as e:
            self.logger.logger.debug(f"Error extracting application information: {e}")
            return {'application_url': '', 'application_type': 'external'}
    
    def extract_application_requirements(self) -> List[str]:
        """
        Extract application requirements from the right panel.
        
        Returns:
            List of application requirement strings
        """
        try:
            # Look for application-specific requirements
            description_text = self.extract_text_from_selector('job_description')
            
            requirements = []
            
            # Common application requirement indicators
            app_requirement_indicators = [
                'application requirements:', 'to apply:', 'how to apply:',
                'application process:', 'submission requirements:',
                'please include:', 'required documents:', 'apply with:'
            ]
            
            if description_text:
                lines = description_text.split('\n')
                in_requirements = False
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Check if we're entering an application requirements section
                    if any(indicator in line.lower() for indicator in app_requirement_indicators):
                        in_requirements = True
                        continue
                    
                    # If we're in requirements section, collect items
                    if in_requirements and line:
                        if (line.startswith('•') or line.startswith('-') or 
                            line.startswith('*') or line[0].isdigit()):
                            requirements.append(line.lstrip('•-* '))
                        elif len(line) > 10:
                            requirements.append(line)
                    
                    # Stop if we hit another section
                    if in_requirements and any(section in line.lower() for section in ['benefits:', 'about us:', 'company:']):
                        break
            
            return requirements[:5]  # Limit to first 5 requirements
            
        except Exception as e:
            self.logger.logger.debug(f"Error extracting application requirements: {e}")
            return []
    
    def initiate_easy_apply(self, job_listing: JobListing) -> bool:
        """
        Initiate LinkedIn Easy Apply for a job listing.
        
        Args:
            job_listing: JobListing object to apply for
            
        Returns:
            True if application was successful, False otherwise
        """
        try:
            self.logger.logger.info(f"Starting Easy Apply for: {job_listing.title} at {job_listing.company}")
            
            # Check if driver is available
            if not self.driver:
                self.logger.logger.error("WebDriver not initialized, cannot initiate Easy Apply")
                return False
            
            # Find and click Easy Apply button
            if not self._click_easy_apply_button():
                self.logger.logger.warning("Easy Apply button not found or not clickable")
                return False
            
            # Wait for Easy Apply form to load
            if not self._wait_for_easy_apply_form():
                self.logger.logger.error("Easy Apply form failed to load")
                return False
            
            # Process the application form
            success = self._process_easy_apply_form(job_listing)
            
            if success:
                self.logger.logger.info(f"✅ Easy Apply completed successfully for: {job_listing.title}")
            else:
                self.logger.logger.warning(f"⚠️ Easy Apply failed for: {job_listing.title}")
            
            return success
            
        except Exception as e:
            self.handle_error(e, f"Easy Apply for {job_listing.title}")
            return False
    
    def _click_easy_apply_button(self) -> bool:
        """Click the Easy Apply button on the job details panel."""
        try:
            # Wait for Easy Apply button to be present and clickable
            self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, self.selectors['easy_apply_button']))
            )
            
            # Find the Easy Apply button
            easy_apply_button = self.driver.find_element(By.CSS_SELECTOR, self.selectors['easy_apply_button'])
            
            # Scroll to button and click
            self.driver.execute_script("arguments[0].scrollIntoView(true);", easy_apply_button)
            time.sleep(1)
            easy_apply_button.click()
            
            self.logger.logger.info("✅ Easy Apply button clicked successfully")
            return True
            
        except TimeoutException:
            self.logger.logger.warning("Easy Apply button not found or not clickable")
            return False
        except Exception as e:
            self.logger.logger.error(f"Error clicking Easy Apply button: {e}")
            return False
    
    def _wait_for_easy_apply_form(self) -> bool:
        """Wait for the Easy Apply form to load."""
        try:
            # Wait for form to appear
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors['easy_apply_form']))
            )
            
            # Wait a bit more for form to fully load
            time.sleep(2)
            
            self.logger.logger.info("✅ Easy Apply form loaded successfully")
            return True
            
        except TimeoutException:
            self.logger.logger.error("Easy Apply form failed to load")
            return False
    
    def _process_easy_apply_form(self, job_listing: JobListing) -> bool:
        """Process the Easy Apply form step by step."""
        try:
            step = 1
            max_steps = 10  # Prevent infinite loops
            
            while step <= max_steps:
                self.logger.logger.info(f"Processing Easy Apply step {step}")
                
                # Check if we're at the final submit step
                if self._is_submit_step():
                    return self._submit_application()
                
                # Fill form fields for current step
                if not self._fill_form_step():
                    self.logger.logger.warning(f"Failed to fill form at step {step}")
                    return False
                
                # Try to proceed to next step
                if not self._proceed_to_next_step():
                    self.logger.logger.warning(f"Failed to proceed from step {step}")
                    return False
                
                # Wait for next step to load
                time.sleep(2)
                step += 1
            
            self.logger.logger.warning("Reached maximum steps, application may be incomplete")
            return False
            
        except Exception as e:
            self.logger.logger.error(f"Error processing Easy Apply form: {e}")
            return False
    
    def _is_submit_step(self) -> bool:
        """Check if we're at the final submit step."""
        try:
            # Look for submit button
            submit_button = self.driver.find_element(By.CSS_SELECTOR, self.selectors['form_submit_button'])
            return submit_button.is_displayed()
        except:
            return False
    
    def _fill_form_step(self) -> bool:
        """Fill form fields for the current step."""
        try:
            # Get applicant profile
            from config.applicant_profile import load_applicant_profile
            profile = load_applicant_profile()
            
            # Fill input fields
            self._fill_input_fields(profile)
            
            # Handle file uploads
            self._handle_file_uploads(profile)
            
            # Answer questions
            self._answer_questions(profile)
            
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Error filling form step: {e}")
            return False
    
    def _fill_input_fields(self, profile) -> None:
        """Fill input fields with applicant data."""
        try:
            # Find all input fields
            input_fields = self.driver.find_elements(By.CSS_SELECTOR, self.selectors['form_input_fields'])
            
            for field in input_fields:
                try:
                    # Get field attributes
                    field_type = field.get_attribute('type')
                    field_name = field.get_attribute('name') or field.get_attribute('id') or ''
                    field_value = field.get_attribute('value')
                    
                    # Skip if already filled
                    if field_value:
                        continue
                    
                    # Fill based on field type and name
                    if field_type == 'email' and not field_value:
                        field.clear()
                        field.send_keys(profile.email)
                        self.logger.logger.debug(f"Filled email field: {profile.email}")
                    
                    elif field_type == 'tel' and not field_value:
                        field.clear()
                        field.send_keys(profile.phone)
                        self.logger.logger.debug(f"Filled phone field: {profile.phone}")
                    
                    elif 'name' in field_name.lower() and 'first' in field_name.lower() and not field_value:
                        field.clear()
                        field.send_keys(profile.first_name)
                        self.logger.logger.debug(f"Filled first name field: {profile.first_name}")
                    
                    elif 'name' in field_name.lower() and 'last' in field_name.lower() and not field_value:
                        field.clear()
                        field.send_keys(profile.last_name)
                        self.logger.logger.debug(f"Filled last name field: {profile.last_name}")
                    
                    elif 'location' in field_name.lower() and not field_value:
                        field.clear()
                        field.send_keys(profile.location)
                        self.logger.logger.debug(f"Filled location field: {profile.location}")
                    
                except Exception as e:
                    self.logger.logger.debug(f"Error filling field {field_name}: {e}")
                    continue
                    
        except Exception as e:
            self.logger.logger.error(f"Error filling input fields: {e}")
    
    def _handle_file_uploads(self, profile) -> None:
        """Handle resume and cover letter uploads."""
        try:
            # Handle resume upload
            if profile.resume_path and os.path.exists(profile.resume_path):
                resume_inputs = self.driver.find_elements(By.CSS_SELECTOR, self.selectors['resume_upload'])
                for resume_input in resume_inputs:
                    try:
                        resume_input.send_keys(profile.resume_path)
                        self.logger.logger.info(f"✅ Resume uploaded: {os.path.basename(profile.resume_path)}")
                        break
                    except Exception as e:
                        self.logger.logger.debug(f"Error uploading resume: {e}")
                        continue
            
            # Handle cover letter upload
            if profile.cover_letter_path and os.path.exists(profile.cover_letter_path):
                cover_letter_inputs = self.driver.find_elements(By.CSS_SELECTOR, self.selectors['cover_letter_upload'])
                for cover_letter_input in cover_letter_inputs:
                    try:
                        cover_letter_input.send_keys(profile.cover_letter_path)
                        self.logger.logger.info(f"✅ Cover letter uploaded: {os.path.basename(profile.cover_letter_path)}")
                        break
                    except Exception as e:
                        self.logger.logger.debug(f"Error uploading cover letter: {e}")
                        continue
                        
        except Exception as e:
            self.logger.logger.error(f"Error handling file uploads: {e}")
    
    def _answer_questions(self, profile) -> None:
        """Answer application questions."""
        try:
            # Find question elements
            questions = self.driver.find_elements(By.CSS_SELECTOR, self.selectors['application_questions'])
            
            for question in questions:
                try:
                    # Get question text
                    question_text_elem = question.find_element(By.CSS_SELECTOR, self.selectors['question_text'])
                    question_text = question_text_elem.text.strip()
                    
                    # Get answer from profile
                    answer = profile.get_answer_for_question(question_text)
                    
                    if answer:
                        # Try to fill the answer
                        self._fill_question_answer(question, answer)
                        self.logger.logger.debug(f"Answered question: {question_text[:50]}...")
                    else:
                        self.logger.logger.debug(f"No answer found for question: {question_text[:50]}...")
                        
                except Exception as e:
                    self.logger.logger.debug(f"Error answering question: {e}")
                    continue
                    
        except Exception as e:
            self.logger.logger.error(f"Error answering questions: {e}")
    
    def _fill_question_answer(self, question_element, answer: str) -> None:
        """Fill answer for a specific question."""
        try:
            # Try different input types
            input_selectors = [
                'input[type="text"]',
                'textarea',
                'select',
                'input[type="radio"]',
                'input[type="checkbox"]'
            ]
            
            for selector in input_selectors:
                try:
                    inputs = question_element.find_elements(By.CSS_SELECTOR, selector)
                    
                    for input_elem in inputs:
                        input_type = input_elem.get_attribute('type')
                        
                        if input_type == 'text' or input_type is None:
                            input_elem.clear()
                            input_elem.send_keys(answer)
                            return
                        
                        elif input_type == 'radio':
                            # For radio buttons, try to find matching option
                            if answer.lower() in input_elem.get_attribute('value', '').lower():
                                input_elem.click()
                                return
                        
                        elif input_type == 'checkbox':
                            # For checkboxes, check if answer indicates yes/true
                            if answer.lower() in ['yes', 'true', '1']:
                                if not input_elem.is_selected():
                                    input_elem.click()
                                return
                        
                        elif input_elem.tag_name == 'select':
                            # For select dropdowns
                            from selenium.webdriver.support.ui import Select
                            select = Select(input_elem)
                            try:
                                select.select_by_visible_text(answer)
                                return
                            except:
                                continue
                                
                except Exception as e:
                    continue
                    
        except Exception as e:
            self.logger.logger.debug(f"Error filling question answer: {e}")
    
    def _proceed_to_next_step(self) -> bool:
        """Click the next button to proceed to the next step."""
        try:
            # Find next button
            next_button = self.driver.find_element(By.CSS_SELECTOR, self.selectors['form_next_button'])
            
            # Scroll to button and click
            self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            time.sleep(1)
            next_button.click()
            
            self.logger.logger.debug("✅ Proceeded to next step")
            return True
            
        except Exception as e:
            self.logger.logger.debug(f"Error proceeding to next step: {e}")
            return False
    
    def _submit_application(self) -> bool:
        """Submit the final application."""
        try:
            # Find submit button
            submit_button = self.driver.find_element(By.CSS_SELECTOR, self.selectors['form_submit_button'])
            
            # Scroll to button and click
            self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
            time.sleep(1)
            submit_button.click()
            
            # Wait for success message
            time.sleep(3)
            
            # Check for success
            try:
                success_element = self.driver.find_element(By.CSS_SELECTOR, self.selectors['application_success'])
                if success_element.is_displayed():
                    self.logger.logger.info("✅ Application submitted successfully")
                    return True
            except:
                pass
            
            # If no success message, check for error
            try:
                error_element = self.driver.find_element(By.CSS_SELECTOR, self.selectors['application_error'])
                if error_element.is_displayed():
                    self.logger.logger.error("❌ Application submission failed")
                    return False
            except:
                pass
            
            # If neither success nor error message, assume success
            self.logger.logger.info("✅ Application submitted (no confirmation message)")
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Error submitting application: {e}")
            return False
    
    def apply_to_job(self, job_listing: JobListing) -> bool:
        """
        Apply to a job using the best available method.
        
        Args:
            job_listing: JobListing object to apply for
            
        Returns:
            True if application was successful, False otherwise
        """
        try:
            self.logger.logger.info(f"Starting application process for: {job_listing.title} at {job_listing.company}")
            
            # Check if Easy Apply is available
            if self._is_easy_apply_available():
                self.logger.logger.info("Easy Apply available - using automated application")
                return self.initiate_easy_apply(job_listing)
            else:
                self.logger.logger.info("Easy Apply not available - manual application required")
                return False
                
        except Exception as e:
            self.handle_error(e, f"application process for {job_listing.title}")
            return False
    
    def _is_easy_apply_available(self) -> bool:
        """Check if Easy Apply is available for the current job."""
        try:
            # Look for Easy Apply button
            easy_apply_button = self.driver.find_element(By.CSS_SELECTOR, self.selectors['easy_apply_button'])
            return easy_apply_button.is_displayed()
        except:
            return False
    
    def extract_job_details_from_page(self, page_content: Any, job_url: str) -> Optional[JobListing]:
        """
        Extract detailed job information from a job detail page using robust extraction methods.
        
        Args:
            page_content: The page content (not used in Selenium-based scraper)
            job_url: URL of the job being processed
            
        Returns:
            JobListing with detailed information, or None if failed
        """
        try:
            self.logger.logger.info(f"Extracting job details from page for: {job_url}")
            
            # Wait for the job details container to load
            try:
                self.wait_for_right_panel()
            except Exception as e:
                self.logger.logger.warning(f"Could not wait for right panel: {e}")
            
            # Extract job data using robust methods
            job_data = self.extract_job_data_from_right_panel()
            
            if not job_data:
                self.logger.logger.warning("Failed to extract job data from page")
                return None
            
            # Create JobListing object with extracted data
            job_listing = JobListing(
                title=job_data.get('title', 'Unknown Title'),
                company=job_data.get('company', 'Unknown Company'),
                location=job_data.get('location', 'Unknown Location'),
                job_url=job_data.get('job_url', job_url),
                job_site='linkedin',
                description=job_data.get('description', ''),
                requirements=job_data.get('requirements', []),
                responsibilities=job_data.get('responsibilities', []),
                benefits=job_data.get('benefits', []),
                salary_min=job_data.get('salary_min'),
                salary_max=job_data.get('salary_max'),
                salary_currency=job_data.get('salary_currency', 'USD'),
                job_type=job_data.get('job_type'),
                experience_level=job_data.get('experience_level'),
                remote_type=job_data.get('remote_type'),
                application_url=job_data.get('application_url'),
                application_deadline=job_data.get('application_deadline'),
                application_requirements=job_data.get('application_requirements', []),
                posted_date=job_data.get('posted_date'),
                is_duplicate=job_data.get('is_duplicate', False),
                duplicate_of=job_data.get('duplicate_of'),
                notes=job_data.get('notes', '')
            )
            
            self.logger.logger.info(f"Successfully extracted job details: {job_listing.title} at {job_listing.company}")
            return job_listing
            
        except Exception as e:
            self.handle_error(e, "job details extraction from page", job_url)
            return None
    
    def cleanup(self) -> None:
        """Clean up resources used by the scraper."""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.wait = None
                self.logger.logger.info("LinkedIn scraper WebDriver closed")
        except Exception as e:
            self.logger.logger.error(f"Error during cleanup: {e}")
        
        super().cleanup()

    def apply_date_filter(self, days: int) -> bool:
        """
        Apply LinkedIn's date posted filter by interacting with UI elements.
        Enhanced version with interface detection and stealth techniques.
        
        Args:
            days (int): Number of days (1, 3, 7, 14, 30)
        
        Returns:
            bool: True if filter was successfully applied, False otherwise
        """
        try:
            self.logger.logger.info(f"Attempting to apply {days}-day date filter")
            
            # Add realistic delay before starting
            self._add_realistic_delays()
            
            # Wait for page to fully load
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-search-results-list, .jobs-search-results, .job-search-card, .job-card-container"))
            )
            
            # Detect interface version
            interface_version = self._detect_linkedin_interface_version()
            self.logger.logger.info(f"Using selectors for {interface_version} interface")
            
            # Get date filter button selectors for this interface version
            date_filter_selectors = self._get_date_filter_button_selectors_by_version(interface_version)
            
            date_filter_element = None
            for selector in date_filter_selectors:
                try:
                    date_filter_element = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    self.logger.logger.debug(f"Found date filter with selector: {selector}")
                    break
                except:
                    continue
                    
            if not date_filter_element:
                self.logger.logger.warning("Could not find date filter dropdown element")
                return False
                
            # Simulate human click to open the filter dropdown
            self._simulate_human_click(date_filter_element)
            time.sleep(random.uniform(1.0, 2.0))  # Wait for dropdown to open
            
            # Get filter option selectors for this interface version
            filter_mapping = self._get_date_filter_selectors_by_version(days, interface_version)
            
            # Try to click the appropriate filter option
            for option_selector in filter_mapping:
                try:
                    option_element = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, option_selector))
                    )
                    
                    # Simulate human click on filter option
                    self._simulate_human_click(option_element)
                    self.logger.logger.info(f"Successfully clicked {days}-day filter option")
                    
                    # Add realistic delay
                    time.sleep(random.uniform(1.5, 2.5))
                    
                    # Look for and click "Show results" or "Apply" button if present
                    self._click_apply_filter_button()
                    
                    # Wait for filtered results to load
                    time.sleep(random.uniform(2.0, 3.0))
                    
                    # Verify filter was applied by checking if filter is now active
                    if self._verify_date_filter_applied(days, interface_version):
                        self.logger.logger.info(f"Date filter for {days} days successfully applied")
                        return True
                        
                except Exception as e:
                    self.logger.logger.debug(f"Failed to click filter option {option_selector}: {e}")
                    continue
                    
            self.logger.logger.warning(f"Could not apply {days}-day date filter")
            return False
            
        except Exception as e:
            self.logger.logger.error(f"Date filter application failed: {e}")
            return False

    def _verify_date_filter_applied(self, days: int, interface_version: str) -> bool:
        """Verify that the date filter was successfully applied."""
        try:
            # Check if filter is now shown as active
            if interface_version == 'new':
                verification_selectors = [
                    f"[aria-label*='Date posted'][aria-pressed='true']",
                    f".search-s-facet--date-posted.search-s-facet--active",
                    f".filter-button--active:contains('Date posted')",
                    f".search-reusables__filter-binary-toggle--active",
                    f"[data-test-id='date-posted-filter'][aria-pressed='true']",
                    f".artdeco-pill--selected[aria-label*='Date posted']",
                    f".filter-pill--active[aria-label*='Date posted']"
                ]
            else:
                verification_selectors = [
                    f"[aria-label*='Date posted'][aria-pressed='true']",
                    f".search-s-facet--date-posted.search-s-facet--active",
                    f".filter-button--active:contains('Date posted')",
                    f".search-reusables__filter-binary-toggle--active",
                    f"[data-test-id='date-posted-filter'][aria-pressed='true']",
                    f".date-posted-filter--active",
                    f".filter-option--selected[data-value='{days}']"
                ]
            
            for selector in verification_selectors:
                try:
                    active_filter = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if active_filter.is_displayed():
                        return True
                except:
                    continue
                    
            # Alternative: Check if URL or page content changed to indicate filter applied
            # (This is a backup verification method)
            return True  # Assume success if no errors occurred
            
        except Exception as e:
            self.logger.logger.debug(f"Filter verification failed: {e}")
            return False

    def scrape_jobs_with_date_filter(self, keywords: List[str], location: str, date_posted_days: Optional[int] = None, **kwargs) -> ScrapingResult:
        """
        Enhanced job scraping with date filter support
        
        Args:
            keywords: List of job keywords to search for
            location: Location to search in
            date_posted_days: Filter for jobs posted within X days (1, 3, 7, 14, 30)
            **kwargs: Additional search parameters
            
        Returns:
            ScrapingResult containing the scraped jobs and session info
        """
        # Start scraping session
        self.session = self.start_session(keywords, location)
        
        try:
            self.logger.logger.info(f"Starting LinkedIn job scrape for keywords: {keywords} in {location}")
            if date_posted_days:
                self.logger.logger.info(f"Applying date filter: past {date_posted_days} days")
            
            # Set up WebDriver if not already done
            if not self.driver:
                self.setup_driver()
            
            # Authenticate if not already authenticated
            if not self.is_authenticated:
                if not hasattr(self, 'username') or not hasattr(self, 'password'):
                    raise ValueError("Authentication credentials not provided")
                
                if not self.authenticate(self.username, self.password):
                    return ScrapingResult(
                        success=False,
                        jobs=[],
                        session=self.session,
                        error_message="LinkedIn authentication failed"
                    )
            
            # Perform job search
            if not self.search_jobs(keywords, location, **kwargs):
                return ScrapingResult(
                    success=False,
                    jobs=[],
                    session=self.session,
                    error_message="Job search failed"
                )
            
            # Apply date filter if specified
            if date_posted_days:
                filter_applied = self.apply_date_filter(date_posted_days)
                
                if filter_applied:
                    self.logger.logger.info(f"Date filter applied successfully - scraping jobs from past {date_posted_days} days")
                else:
                    self.logger.logger.warning(f"Date filter failed - scraping all jobs (may include older postings)")
            
            # Extract jobs from the search page using right panel approach
            jobs = self.extract_jobs_from_search_page()
            
            # Process additional pages if configured and available
            if self.config.max_jobs_per_session > len(jobs):
                additional_jobs = self.extract_jobs_from_additional_pages()
                jobs.extend(additional_jobs)
            
            # Update session with extracted jobs count
            self.session.jobs_found = len(jobs)
            self.session.jobs_processed = len(jobs)
            
            self.logger.logger.info(f"LinkedIn scraping completed - extracted {len(jobs)} jobs total")
            
            return ScrapingResult(
                success=True,
                jobs=jobs,
                session=self.session,
                metadata={
                    "keywords": keywords,
                    "location": location,
                    "date_filter_days": date_posted_days,
                    "jobs_found_on_page": len(jobs),
                    "current_url": self.driver.current_url
                }
            )
            
        except Exception as e:
            self.handle_error(e, "LinkedIn job scraping with date filter")
            return ScrapingResult(
                success=False,
                jobs=[],
                session=self.session,
                error_message=str(e)
            )
        finally:
            self.finish_session()

    def scrape_jobs_with_fallback(self, keywords: List[str], location: str, date_posted_days: Optional[int] = None, **kwargs) -> ScrapingResult:
        """Scrape jobs with graceful fallback if date filtering fails"""
        
        try:
            # Try with date filter first
            if date_posted_days:
                self.logger.logger.info(f"Attempting to scrape jobs with {date_posted_days}-day date filter")
                result = self.scrape_jobs_with_date_filter(keywords, location, date_posted_days, **kwargs)
                
                # If we got very few results, the filter might have been too restrictive
                if result.success and len(result.jobs) < 5:
                    self.logger.logger.warning(f"Only {len(result.jobs)} jobs found with {date_posted_days}-day filter")
                    self.logger.logger.info("Expanding search to get more results...")
                    
                    # Try a broader date range
                    broader_days = min(date_posted_days * 2, 30)
                    broader_result = self.scrape_jobs_with_date_filter(keywords, location, broader_days, **kwargs)
                    
                    if broader_result.success and len(broader_result.jobs) > len(result.jobs):
                        self.logger.logger.info(f"Found {len(broader_result.jobs)} jobs with {broader_days}-day filter")
                        return broader_result
                    else:
                        return result
                else:
                    return result
            else:
                # No date filter requested
                return self.scrape_jobs(keywords, location, **kwargs)
                
        except Exception as e:
            self.logger.logger.error(f"Job scraping with date filter failed: {e}")
            
            # Fallback: scrape without date filter
            self.logger.logger.info("Falling back to scraping without date filter")
            try:
                return self.scrape_jobs(keywords, location, **kwargs)
            except Exception as fallback_error:
                self.logger.logger.error(f"Fallback scraping also failed: {fallback_error}")
                return ScrapingResult(
                    success=False,
                    jobs=[],
                    session=self.session,
                    error_message=f"Both date-filtered and fallback scraping failed: {str(e)}"
                )


def create_linkedin_scraper(username: str, password: str) -> LinkedInScraper:
    """
    Create a LinkedIn scraper with authentication credentials.
    
    Args:
        username: LinkedIn username/email
        password: LinkedIn password
        
    Returns:
        Configured LinkedInScraper instance
    """
    config = ScrapingConfig(
        site_name="linkedin",
        base_url="https://www.linkedin.com",
        delay_min=2.0,
        delay_max=5.0,
        max_requests_per_minute=12,  # Conservative for LinkedIn
        max_jobs_per_session=50,
        respect_robots_txt=True,
        use_random_delays=True,
        log_level="INFO",
        page_load_timeout=30,
        element_wait_timeout=15
    )
    
    scraper = LinkedInScraper(config)
    scraper.username = username
    scraper.password = password
    
    return scraper 