#!/usr/bin/env python3
"""
Enhanced LinkedIn Scraper with Fixed Filter Clicking Logic
This version properly identifies and clicks on specific filter options instead of entire sections.
"""

import time
import random
from typing import List, Optional, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .linkedin_scraper_enhanced import EnhancedLinkedInScraper
from src.scrapers.base_scraper import ScrapingConfig
from src.utils.session_manager import SessionManager
from src.utils.logger import JobAutomationLogger

import logging

logger = logging.getLogger(__name__)

class FixedLinkedInScraper(EnhancedLinkedInScraper):
    """
    Enhanced LinkedIn Scraper with fixed filter clicking logic.
    This version properly identifies and clicks on specific filter options.
    """
    
    def __init__(self, config: ScrapingConfig, session_manager: SessionManager = None):
        super().__init__(config, session_manager)
        self.logger = JobAutomationLogger("fixed_linkedin_scraper")
    
    def _find_and_click_filter_option(self, filter_section, target_text: str, filter_type: str) -> bool:
        """
        Find and click a specific filter option within a filter section.
        
        Args:
            filter_section: The filter section element
            target_text: The text to search for
            filter_type: Type of filter (for logging)
            
        Returns:
            True if option was found and clicked, False otherwise
        """
        try:
            self.logger.logger.info(f"Looking for {filter_type} option: '{target_text}'")
            
            # Method 1: Look for radio buttons and their labels
            input_elements = filter_section.find_elements(By.CSS_SELECTOR, "input[type='radio'], input[type='checkbox']")
            self.logger.logger.info(f"Found {len(input_elements)} input elements in {filter_type} section")
            
            for input_elem in input_elements:
                try:
                    input_id = input_elem.get_attribute('id')
                    if input_id:
                        # Find the corresponding label
                        label = filter_section.find_element(By.CSS_SELECTOR, f"label[for='{input_id}']")
                        if label:
                            label_text = label.text.strip()
                            self.logger.logger.info(f"Found input with label: '{label_text}'")
                            
                            if target_text.lower() in label_text.lower():
                                self.logger.logger.info(f"Found matching {filter_type} input with label: '{label_text}'")
                                # Click the label
                                label.click()
                                time.sleep(1)
                                self.logger.logger.info(f"✅ {filter_type} filter '{target_text}' applied")
                                return True
                except Exception as e:
                    self.logger.logger.debug(f"Error checking input element: {e}")
                    continue
            
            # Method 2: Look for clickable divs/spans with role="radio"
            clickable_elements = filter_section.find_elements(By.CSS_SELECTOR, "div[role='radio'], span[role='radio'], div[tabindex], span[tabindex]")
            self.logger.logger.info(f"Found {len(clickable_elements)} clickable divs/spans in {filter_type} section")
            
            for elem in clickable_elements:
                try:
                    if elem.is_displayed() and elem.is_enabled():
                        elem_text = elem.text.strip()
                        if target_text.lower() in elem_text.lower():
                            self.logger.logger.info(f"Found matching {filter_type} clickable element: '{elem_text}'")
                            elem.click()
                            time.sleep(1)
                            self.logger.logger.info(f"✅ {filter_type} filter '{target_text}' applied")
                            return True
                except Exception as e:
                    self.logger.logger.debug(f"Error checking clickable element: {e}")
                    continue
            
            # Method 3: Look for any clickable element with the text
            all_elements = filter_section.find_elements(By.XPATH, ".//*")
            self.logger.logger.info(f"Found {len(all_elements)} total elements in {filter_type} section")
            
            for element in all_elements:
                try:
                    if element.is_displayed() and element.is_enabled():
                        element_text = element.text.strip()
                        if target_text.lower() in element_text.lower():
                            # Check if this element is actually clickable (not just a container)
                            tag_name = element.tag_name.lower()
                            if tag_name in ['button', 'label', 'div', 'span']:
                                self.logger.logger.info(f"Found potential {filter_type} target: '{element_text}'")
                                element.click()
                                time.sleep(1)
                                self.logger.logger.info(f"✅ {filter_type} filter '{target_text}' applied")
                                return True
                except Exception as e:
                    self.logger.logger.debug(f"Error checking element: {e}")
                    continue
            
            self.logger.logger.warning(f"Could not find '{target_text}' option in {filter_type} filter")
            return False
            
        except Exception as e:
            self.logger.logger.error(f"Error finding and clicking {filter_type} option: {e}")
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
            
            # Find the modal content
            modal_content = self.driver.find_element(By.CSS_SELECTOR, ".artdeco-modal__content")
            
            # Find all filter sections
            filter_sections = modal_content.find_elements(By.TAG_NAME, "li")
            self.logger.logger.info(f"Found {len(filter_sections)} filter sections in modal")
            
            # Find the Date posted filter section
            date_section = None
            for section in filter_sections:
                try:
                    h3_elements = section.find_elements(By.TAG_NAME, "h3")
                    for h3 in h3_elements:
                        if "date posted" in h3.text.lower():
                            date_section = section
                            self.logger.logger.info("✅ Found Date posted filter section")
                            break
                    if date_section:
                        break
                except:
                    continue
            
            if not date_section:
                self.logger.logger.error("Could not find Date posted filter section")
                return False
            
            # Map days to LinkedIn date filter options
            date_mapping = {
                1: "Past 24 hours",
                7: "Past week", 
                30: "Past month",
                None: "Any time"
            }
            
            target_date_text = date_mapping.get(days, "Past week")
            
            # Find and click the date option
            return self._find_and_click_filter_option(date_section, target_date_text, "Date")
            
        except Exception as e:
            self.logger.logger.error(f"Error applying date filter in modal: {e}")
            return False
    
    def _apply_experience_level_in_modal(self, experience_level: str) -> bool:
        """
        Apply Experience Level filter within an already open modal.
        
        Args:
            experience_level: Experience level to filter for
            
        Returns:
            True if experience level filter was applied successfully, False otherwise
        """
        try:
            self.logger.logger.info(f"Applying Experience Level filter in modal: {experience_level}")
            
            # Find the modal content
            modal_content = self.driver.find_element(By.CSS_SELECTOR, ".artdeco-modal__content")
            
            # Find all filter sections
            filter_sections = modal_content.find_elements(By.TAG_NAME, "li")
            
            # Find the Experience Level filter section
            experience_section = None
            for section in filter_sections:
                try:
                    h3_elements = section.find_elements(By.TAG_NAME, "h3")
                    for h3 in h3_elements:
                        if "experience level" in h3.text.lower():
                            experience_section = section
                            self.logger.logger.info("✅ Found Experience Level filter section")
                            break
                    if experience_section:
                        break
                except:
                    continue
            
            if not experience_section:
                self.logger.logger.error("Could not find Experience Level filter section")
                return False
            
            # Find and click the experience level option
            return self._find_and_click_filter_option(experience_section, experience_level, "Experience Level")
            
        except Exception as e:
            self.logger.logger.error(f"Error applying experience level filter in modal: {e}")
            return False
    
    def _apply_job_type_in_modal(self, job_type: str) -> bool:
        """
        Apply Job Type filter within an already open modal.
        
        Args:
            job_type: Job type to filter for
            
        Returns:
            True if job type filter was applied successfully, False otherwise
        """
        try:
            self.logger.logger.info(f"Applying Job Type filter in modal: {job_type}")
            
            # Find the modal content
            modal_content = self.driver.find_element(By.CSS_SELECTOR, ".artdeco-modal__content")
            
            # Find all filter sections
            filter_sections = modal_content.find_elements(By.TAG_NAME, "li")
            
            # Find the Job Type filter section
            job_type_section = None
            for section in filter_sections:
                try:
                    h3_elements = section.find_elements(By.TAG_NAME, "h3")
                    for h3 in h3_elements:
                        if "job type" in h3.text.lower():
                            job_type_section = section
                            self.logger.logger.info("✅ Found Job Type filter section")
                            break
                    if job_type_section:
                        break
                except:
                    continue
            
            if not job_type_section:
                self.logger.logger.error("Could not find Job Type filter section")
                return False
            
            # Find and click the job type option
            return self._find_and_click_filter_option(job_type_section, job_type, "Job Type")
            
        except Exception as e:
            self.logger.logger.error(f"Error applying job type filter in modal: {e}")
            return False
    
    def _apply_work_arrangement_in_modal(self, work_arrangement: str) -> bool:
        """
        Apply Work Arrangement filter within an already open modal.
        
        Args:
            work_arrangement: Work arrangement to filter for
            
        Returns:
            True if work arrangement filter was applied successfully, False otherwise
        """
        try:
            self.logger.logger.info(f"Applying Work Arrangement filter in modal: {work_arrangement}")
            
            # Find the modal content
            modal_content = self.driver.find_element(By.CSS_SELECTOR, ".artdeco-modal__content")
            
            # Find all filter sections
            filter_sections = modal_content.find_elements(By.TAG_NAME, "li")
            
            # Find the Work Arrangement filter section
            work_arrangement_section = None
            for section in filter_sections:
                try:
                    h3_elements = section.find_elements(By.TAG_NAME, "h3")
                    for h3 in h3_elements:
                        if "work arrangement" in h3.text.lower() or "remote" in h3.text.lower():
                            work_arrangement_section = section
                            self.logger.logger.info("✅ Found Work Arrangement filter section")
                            break
                    if work_arrangement_section:
                        break
                except:
                    continue
            
            if not work_arrangement_section:
                self.logger.logger.error("Could not find Work Arrangement filter section")
                return False
            
            # Find and click the work arrangement option
            return self._find_and_click_filter_option(work_arrangement_section, work_arrangement, "Work Arrangement")
            
        except Exception as e:
            self.logger.logger.error(f"Error applying work arrangement filter in modal: {e}")
            return False

def create_fixed_linkedin_scraper(username: str, password: str, use_persistent_session: bool = True) -> FixedLinkedInScraper:
    """
    Create a FixedLinkedInScraper instance with the given credentials.
    
    Args:
        username: LinkedIn username/email
        password: LinkedIn password
        use_persistent_session: Whether to use persistent session
        
    Returns:
        FixedLinkedInScraper instance
    """
    from src.scrapers.base_scraper import ScrapingConfig
    from src.utils.session_manager import SessionManager
    
    # Create session manager
    session_manager = SessionManager()
    
    # Create scraping config
    config = ScrapingConfig(
        site_name="linkedin",
        base_url="https://www.linkedin.com",
        max_jobs_per_session=50,
        delay_min=2.0,
        delay_max=5.0,
        max_retries=3,
        page_load_timeout=30
    )
    
    # Add LinkedIn credentials
    config.linkedin_username = username
    config.linkedin_password = password
    
    # Create and return the scraper
    return FixedLinkedInScraper(config, session_manager) 