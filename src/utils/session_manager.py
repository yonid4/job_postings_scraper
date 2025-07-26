#!/usr/bin/env python3
"""
Session Manager for LinkedIn Automation

This module provides persistent browser session management to ensure
the automation gets the same interface as manual browsing by maintaining
cookies, authentication state, and browser fingerprinting.
"""

import os
import json
import pickle
import time
import random
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from src.utils.logger import JobAutomationLogger


class SessionManager:
    """
    Manages persistent browser sessions for LinkedIn automation.
    
    This class handles:
    - Cookie persistence and restoration
    - Authentication state management
    - Browser fingerprinting consistency
    - Session data storage and retrieval
    """
    
    def __init__(self, session_dir: str = "sessions"):
        """
        Initialize the session manager.
        
        Args:
            session_dir: Directory to store session data
        """
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(exist_ok=True)
        self.logger = JobAutomationLogger()
        self.current_session_id = None
        self.driver = None
        
    def create_session(self, session_name: str = None, use_persistent_profile: bool = True) -> str:
        """
        Create a new browser session with stealth configuration.
        
        Args:
            session_name: Optional name for the session
            use_persistent_profile: Whether to use persistent user data directory
            
        Returns:
            Session ID for the created session
        """
        try:
            # Generate session ID
            if session_name:
                session_id = f"{session_name}_{int(time.time())}"
            else:
                session_id = f"linkedin_session_{int(time.time())}"
            
            self.current_session_id = session_id
            session_path = self.session_dir / session_id
            session_path.mkdir(exist_ok=True)
            
            # If WebDriver is already provided, use it
            if self.driver:
                self.logger.logger.info(f"Using existing WebDriver for session: {session_id}")
                # Save session metadata
                self._save_session_metadata(session_id)
                return session_id
            
            # Create Chrome options with stealth configuration
            options = Options()
            
            # User data directory for persistent session (only if requested)
            if use_persistent_profile:
                user_data_dir = session_path / "chrome_data"
                options.add_argument(f'--user-data-dir={user_data_dir}')
                
                # Profile directory for consistent fingerprinting
                profile_dir = session_path / "chrome_profile"
                options.add_argument(f'--profile-directory={profile_dir}')
            else:
                # Use temporary directory for non-persistent sessions
                temp_dir = tempfile.mkdtemp(prefix="chrome_temp_")
                options.add_argument(f'--user-data-dir={temp_dir}')
            
            # Essential stealth settings
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
            
            # Additional stability options
            options.add_argument('--disable-web-security')
            options.add_argument('--allow-running-insecure-content')
            options.add_argument('--disable-features=TranslateUI')
            options.add_argument('--disable-component-extensions-with-background-pages')
            options.add_argument('--disable-default-apps')
            options.add_argument('--disable-sync')
            options.add_argument('--disable-translate')
            options.add_argument('--hide-scrollbars')
            options.add_argument('--mute-audio')
            options.add_argument('--no-first-run')
            options.add_argument('--no-default-browser-check')
            options.add_argument('--disable-background-networking')
            options.add_argument('--disable-background-timer-throttling')
            options.add_argument('--disable-client-side-phishing-detection')
            options.add_argument('--disable-default-apps')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-hang-monitor')
            options.add_argument('--disable-prompt-on-repost')
            options.add_argument('--disable-sync')
            options.add_argument('--disable-web-resources')
            options.add_argument('--metrics-recording-only')
            options.add_argument('--no-first-run')
            options.add_argument('--safebrowsing-disable-auto-update')
            options.add_argument('--enable-automation')
            options.add_argument('--password-store=basic')
            options.add_argument('--use-mock-keychain')
            
            # Create WebDriver with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.driver = webdriver.Chrome(options=options)
                    break
                except WebDriverException as e:
                    if "Browser window not found" in str(e) and attempt < max_retries - 1:
                        self.logger.logger.warning(f"Browser window not found, retrying... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(2)
                        continue
                    else:
                        raise
            
            # Apply stealth scripts
            self._apply_stealth_scripts()
            
            # Set up wait
            self.wait = WebDriverWait(self.driver, 15)
            
            # Set realistic viewport
            self.driver.set_window_size(1920, 1080)
            
            # Save session metadata
            self._save_session_metadata(session_id)
            
            self.logger.logger.info(f"Created new session: {session_id}")
            return session_id
            
        except Exception as e:
            self.logger.logger.error(f"Failed to create session: {e}")
            # Try fallback without persistent profile
            if use_persistent_profile:
                self.logger.logger.info("Retrying without persistent profile...")
                return self.create_session(session_name, use_persistent_profile=False)
            raise
    
    def load_session(self, session_id: str, use_persistent_profile: bool = True) -> bool:
        """
        Load an existing browser session.
        
        Args:
            session_id: ID of the session to load
            use_persistent_profile: Whether to use persistent user data directory
            
        Returns:
            True if session loaded successfully, False otherwise
        """
        try:
            session_path = self.session_dir / session_id
            if not session_path.exists():
                self.logger.logger.warning(f"Session {session_id} not found")
                return False
            
            # Check if session is still valid
            if not self._is_session_valid(session_id):
                self.logger.logger.warning(f"Session {session_id} has expired")
                return False
            
            self.current_session_id = session_id
            
            # Create Chrome options with existing user data
            options = Options()
            
            if use_persistent_profile:
                user_data_dir = session_path / "chrome_data"
                profile_dir = session_path / "chrome_profile"
                
                if user_data_dir.exists():
                    options.add_argument(f'--user-data-dir={user_data_dir}')
                if profile_dir.exists():
                    options.add_argument(f'--profile-directory={profile_dir}')
            else:
                # Use temporary directory for non-persistent sessions
                temp_dir = tempfile.mkdtemp(prefix="chrome_temp_")
                options.add_argument(f'--user-data-dir={temp_dir}')
            
            # Apply same stealth settings
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            options.add_argument(f'--user-agent={user_agent}')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--start-maximized')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--disable-gpu')
            options.add_argument('--lang=en-US')
            options.add_argument('--accept-lang=en-US,en;q=0.9')
            
            # Additional stability options
            options.add_argument('--disable-web-security')
            options.add_argument('--allow-running-insecure-content')
            options.add_argument('--disable-features=TranslateUI')
            options.add_argument('--disable-component-extensions-with-background-pages')
            options.add_argument('--disable-default-apps')
            options.add_argument('--disable-sync')
            options.add_argument('--disable-translate')
            options.add_argument('--hide-scrollbars')
            options.add_argument('--mute-audio')
            options.add_argument('--no-first-run')
            options.add_argument('--no-default-browser-check')
            options.add_argument('--disable-background-networking')
            options.add_argument('--disable-background-timer-throttling')
            options.add_argument('--disable-client-side-phishing-detection')
            options.add_argument('--disable-default-apps')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-hang-monitor')
            options.add_argument('--disable-prompt-on-repost')
            options.add_argument('--disable-sync')
            options.add_argument('--disable-web-resources')
            options.add_argument('--metrics-recording-only')
            options.add_argument('--no-first-run')
            options.add_argument('--safebrowsing-disable-auto-update')
            options.add_argument('--enable-automation')
            options.add_argument('--password-store=basic')
            options.add_argument('--use-mock-keychain')
            
            # Create WebDriver with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.driver = webdriver.Chrome(options=options)
                    break
                except WebDriverException as e:
                    if "Browser window not found" in str(e) and attempt < max_retries - 1:
                        self.logger.logger.warning(f"Browser window not found, retrying... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(2)
                        continue
                    else:
                        raise
            
            # Apply stealth scripts
            self._apply_stealth_scripts()
            
            # Set up wait
            self.wait = WebDriverWait(self.driver, 15)
            
            # Set realistic viewport
            self.driver.set_window_size(1920, 1080)
            
            # Update session metadata
            self._update_session_metadata(session_id)
            
            self.logger.logger.info(f"Loaded session: {session_id}")
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Failed to load session {session_id}: {e}")
            # Try fallback without persistent profile
            if use_persistent_profile:
                self.logger.logger.info("Retrying without persistent profile...")
                return self.load_session(session_id, use_persistent_profile=False)
            return False
    
    def save_cookies(self, domain: str = "linkedin.com") -> bool:
        """
        Save cookies for the current session.
        
        Args:
            domain: Domain to save cookies for
            
        Returns:
            True if cookies saved successfully, False otherwise
        """
        try:
            if not self.driver or not self.current_session_id:
                return False
            
            cookies = self.driver.get_cookies()
            cookie_file = self.session_dir / self.current_session_id / f"cookies_{domain}.json"
            
            with open(cookie_file, 'w') as f:
                json.dump(cookies, f, indent=2)
            
            self.logger.logger.debug(f"Saved {len(cookies)} cookies for {domain}")
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Failed to save cookies: {e}")
            return False
    
    def load_cookies(self, domain: str = "linkedin.com") -> bool:
        """
        Load cookies for the current session.
        
        Args:
            domain: Domain to load cookies for
            
        Returns:
            True if cookies loaded successfully, False otherwise
        """
        try:
            if not self.driver or not self.current_session_id:
                return False
            
            cookie_file = self.session_dir / self.current_session_id / f"cookies_{domain}.json"
            
            if not cookie_file.exists():
                self.logger.logger.debug(f"No saved cookies found for {domain}")
                return False
            
            with open(cookie_file, 'r') as f:
                cookies = json.load(f)
            
            # Load cookies into browser
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    self.logger.logger.debug(f"Failed to load cookie {cookie.get('name', 'unknown')}: {e}")
            
            self.logger.logger.debug(f"Loaded {len(cookies)} cookies for {domain}")
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Failed to load cookies: {e}")
            return False
    
    def is_authenticated(self, domain: str = "linkedin.com") -> bool:
        """
        Check if the current session is authenticated.
        
        Args:
            domain: Domain to check authentication for
            
        Returns:
            True if authenticated, False otherwise
        """
        try:
            if not self.driver:
                return False
            
            # Navigate to LinkedIn
            self.driver.get(f"https://www.{domain}")
            time.sleep(2)
            
            # Check for authentication indicators
            auth_indicators = [
                '.global-nav__me-photo',  # Profile photo
                '.global-nav__me',  # Me menu
                '[data-control-name="identity_welcome_message"]',  # Welcome message
                '.nav-item__profile-member-photo',  # Profile photo (alternative)
                '.global-nav__primary-item--me'  # Me menu (alternative)
            ]
            
            for indicator in auth_indicators:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, indicator)
                    if element.is_displayed():
                        self.logger.logger.info("Session is authenticated")
                        return True
                except:
                    continue
            
            # Check for login page indicators
            login_indicators = [
                '#username',  # Username field
                '#password',  # Password field
                '.login__form',  # Login form
                '[data-test-id="login-form"]'  # Login form (alternative)
            ]
            
            for indicator in login_indicators:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, indicator)
                    if element.is_displayed():
                        self.logger.logger.info("Session is not authenticated (login page detected)")
                        return False
                except:
                    continue
            
            # If we can't determine, assume not authenticated
            self.logger.logger.warning("Could not determine authentication status")
            return False
            
        except Exception as e:
            self.logger.logger.error(f"Error checking authentication: {e}")
            return False
    
    def authenticate(self, username: str, password: str) -> bool:
        """
        Authenticate the current session.
        
        Args:
            username: LinkedIn username/email
            password: LinkedIn password
            
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            if not self.driver:
                return False
            
            # Navigate to LinkedIn login
            self.driver.get("https://www.linkedin.com/login")
            time.sleep(2)
            
            # Fill username
            username_field = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '#username'))
            )
            username_field.clear()
            username_field.send_keys(username)
            time.sleep(random.uniform(0.5, 1.0))
            
            # Fill password
            password_field = self.driver.find_element(By.CSS_SELECTOR, '#password')
            password_field.clear()
            password_field.send_keys(password)
            time.sleep(random.uniform(0.5, 1.0))
            
            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            login_button.click()
            
            # Wait for authentication to complete
            time.sleep(5)
            
            # Check for security challenges first, before checking authentication status
            if self._check_for_security_challenge():
                # Handle security challenge and wait for user input
                return self._handle_security_challenge_during_auth()
            
            # Check if authentication was successful
            if self.is_authenticated():
                # Save cookies after successful authentication
                self.save_cookies()
                self.logger.logger.info("Authentication successful")
                return True
            else:
                self.logger.logger.error("Authentication failed - no security challenge detected")
                return False
                
        except Exception as e:
            self.logger.logger.error(f"Authentication error: {e}")
            return False
    
    def _check_for_security_challenge(self) -> bool:
        """
        Check if a security challenge is present on the current page.
        
        Returns:
            True if security challenge detected, False otherwise
        """
        try:
            page_source = self.driver.page_source.lower()
            current_url = self.driver.current_url.lower()
            
            # Check for specific security challenges
            security_indicators = [
                "security challenge", "captcha", "puzzle", "verification",
                "prove you're not a robot", "verify your identity",
                "challenge", "security check", "verification required",
                "unusual activity", "suspicious activity", "robot check"
            ]
            
            for indicator in security_indicators:
                if indicator in page_source:
                    self.logger.logger.info(f"Security challenge detected: {indicator}")
                    return True
            
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
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed():
                        self.logger.logger.info(f"CAPTCHA element found: {selector}")
                        return True
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
                    self.logger.logger.info(f"CAPTCHA text found: {pattern}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.logger.error(f"Error checking for security challenge: {e}")
            return False
    
    def _handle_security_challenge_during_auth(self) -> bool:
        """
        Handle security challenges during authentication by waiting for user to complete them manually.
        
        Returns:
            True if challenge was handled successfully, False otherwise
        """
        try:
            self.logger.logger.info("🔒 SECURITY CHALLENGE DETECTED")
            self.logger.logger.info("Please complete the security challenge in the browser window.")
            self.logger.logger.info("Press Enter in this terminal when you have completed the challenge...")
            
            # Wait for user to press Enter
            input("Press Enter when you have completed the security challenge...")
            
            self.logger.logger.info("User indicated challenge completion. Checking authentication status...")
            
            # Wait a moment for the page to update
            time.sleep(3)
            
            # Check if authentication is now successful
            if self.is_authenticated():
                # Save cookies after successful authentication
                self.save_cookies()
                self.logger.logger.info("✅ Authentication successful after security challenge!")
                return True
            else:
                self.logger.logger.warning("Authentication still not successful after challenge completion")
                return False
            
        except Exception as e:
            self.logger.logger.error(f"Error handling security challenge: {e}")
            return False
    
    def get_session_info(self, session_id: str = None) -> Dict[str, Any]:
        """
        Get information about a session.
        
        Args:
            session_id: Session ID (uses current if not provided)
            
        Returns:
            Dictionary with session information
        """
        try:
            if not session_id:
                session_id = self.current_session_id
            
            if not session_id:
                return {}
            
            session_path = self.session_dir / session_id
            metadata_file = session_path / "metadata.json"
            
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    return json.load(f)
            else:
                return {}
                
        except Exception as e:
            self.logger.logger.error(f"Error getting session info: {e}")
            return {}
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all available sessions.
        
        Returns:
            List of session information dictionaries
        """
        try:
            sessions = []
            
            for session_dir in self.session_dir.iterdir():
                if session_dir.is_dir():
                    session_info = self.get_session_info(session_dir.name)
                    if session_info:
                        sessions.append(session_info)
            
            # Sort by creation time (newest first)
            sessions.sort(key=lambda x: x.get('created_at', 0), reverse=True)
            
            return sessions
            
        except Exception as e:
            self.logger.logger.error(f"Error listing sessions: {e}")
            return []
    
    def cleanup_session(self, session_id: str = None) -> bool:
        """
        Clean up a session (remove files).
        
        Args:
            session_id: Session ID (uses current if not provided)
            
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            if not session_id:
                session_id = self.current_session_id
            
            if not session_id:
                return False
            
            session_path = self.session_dir / session_id
            
            if session_path.exists():
                import shutil
                shutil.rmtree(session_path)
                self.logger.logger.info(f"Cleaned up session: {session_id}")
                return True
            else:
                self.logger.logger.warning(f"Session {session_id} not found for cleanup")
                return False
                
        except Exception as e:
            self.logger.logger.error(f"Error cleaning up session: {e}")
            return False
    
    def close(self) -> None:
        """Close the current session and cleanup."""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
            
            if self.current_session_id:
                # Save final state
                self.save_cookies()
                self._update_session_metadata(self.current_session_id)
                self.current_session_id = None
                
        except Exception as e:
            self.logger.logger.error(f"Error closing session: {e}")
    
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
            
            self.logger.logger.debug("Applied stealth scripts")
            
        except Exception as e:
            self.logger.logger.warning(f"Failed to apply some stealth scripts: {e}")
    
    def _save_session_metadata(self, session_id: str) -> None:
        """Save session metadata."""
        try:
            metadata = {
                'session_id': session_id,
                'created_at': time.time(),
                'last_accessed': time.time(),
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'viewport': '1920x1080',
                'platform': 'MacIntel',
                'language': 'en-US'
            }
            
            metadata_file = self.session_dir / session_id / "metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            self.logger.logger.error(f"Failed to save session metadata: {e}")
    
    def _update_session_metadata(self, session_id: str) -> None:
        """Update session metadata with last accessed time."""
        try:
            metadata_file = self.session_dir / session_id / "metadata.json"
            
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                metadata['last_accessed'] = time.time()
                
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                    
        except Exception as e:
            self.logger.logger.error(f"Failed to update session metadata: {e}")
    
    def _is_session_valid(self, session_id: str) -> bool:
        """Check if a session is still valid (not expired)."""
        try:
            metadata = self.get_session_info(session_id)
            if not metadata:
                return False
            
            # Sessions expire after 7 days
            created_at = metadata.get('created_at', 0)
            session_age = time.time() - created_at
            max_age = 7 * 24 * 60 * 60  # 7 days in seconds
            
            return session_age < max_age
            
        except Exception as e:
            self.logger.logger.error(f"Error checking session validity: {e}")
            return False 