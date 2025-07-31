#!/usr/bin/env python3
"""
CAPTCHA Handler

This module provides comprehensive CAPTCHA detection and handling functionality
for web automation scenarios. It includes automatic detection, user notification,
waiting mechanisms, and timeout handling.
"""

import time
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class CAPTCHAStatus(Enum):
    """Enumeration of CAPTCHA status states."""
    NOT_DETECTED = "not_detected"
    DETECTED = "detected"
    SOLVED = "solved"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class CAPTCHAInfo:
    """Information about detected CAPTCHA."""
    status: CAPTCHAStatus
    captcha_type: str
    message: str
    detection_time: float
    timeout_seconds: int = 600  # 10 minutes default


class CAPTCHAHandler:
    """
    Comprehensive CAPTCHA detection and handling system.
    
    This class provides:
    - Automatic CAPTCHA detection
    - User-friendly notification
    - Waiting mechanisms with timeout
    - Retry logic
    - Fallback handling
    """
    
    def __init__(self, driver=None, timeout_seconds: int = 600):
        """
        Initialize the CAPTCHA handler.
        
        Args:
            driver: Selenium WebDriver instance
            timeout_seconds: Maximum time to wait for CAPTCHA solution (default: 10 minutes)
        """
        self.driver = driver
        self.timeout_seconds = timeout_seconds
        self.logger = logging.getLogger(__name__)
        
        # CAPTCHA detection patterns
        self.captcha_indicators = [
            # Text-based indicators
            "captcha", "puzzle", "verification", "security challenge",
            "prove you're not a robot", "verify your identity",
            "challenge", "security check", "verification required",
            "unusual activity", "suspicious activity", "robot check",
            "human verification", "security verification",
            "please verify", "verify you're human"
        ]
        
        # CAPTCHA element selectors
        self.captcha_selectors = [
            "iframe[src*='captcha']",
            "iframe[src*='recaptcha']",
            "iframe[src*='challenge']",
            ".captcha",
            ".recaptcha",
            "[data-test-id*='captcha']",
            "[data-test-id*='challenge']",
            "[class*='captcha']",
            "[class*='recaptcha']",
            "[id*='captcha']",
            "[id*='recaptcha']",
            "div[role='presentation'] iframe",
            ".g-recaptcha",
            "#recaptcha",
            ".captcha-container",
            ".verification-container"
        ]
        
        # LinkedIn-specific CAPTCHA indicators
        self.linkedin_captcha_indicators = [
            "security verification", "verify your identity",
            "unusual activity detected", "suspicious activity",
            "please verify you're human", "security challenge",
            "verification required", "robot check"
        ]
    
    def detect_captcha(self) -> CAPTCHAInfo:
        """
        Detect if a CAPTCHA challenge is present on the current page.
        
        Returns:
            CAPTCHAInfo with detection status and details
        """
        if not self.driver:
            return CAPTCHAInfo(
                status=CAPTCHAStatus.ERROR,
                captcha_type="unknown",
                message="No WebDriver instance available",
                detection_time=time.time()
            )
        
        try:
            detection_time = time.time()
            
            # Check page source for CAPTCHA indicators
            page_source = self.driver.page_source.lower()
            current_url = self.driver.current_url.lower()
            
            # Check for text-based CAPTCHA indicators
            detected_indicators = []
            for indicator in self.captcha_indicators:
                if indicator in page_source:
                    detected_indicators.append(indicator)
            
            # Check for LinkedIn-specific indicators
            for indicator in self.linkedin_captcha_indicators:
                if indicator in page_source:
                    detected_indicators.append(f"linkedin_{indicator}")
            
            # Check for CAPTCHA elements
            captcha_elements = []
            for selector in self.captcha_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            captcha_elements.append(selector)
                            break
                except Exception:
                    continue
            
            # Determine CAPTCHA type and status
            if detected_indicators or captcha_elements:
                captcha_type = self._determine_captcha_type(detected_indicators, captcha_elements)
                message = self._generate_captcha_message(captcha_type, detected_indicators)
                
                self.logger.warning(f"CAPTCHA detected: {captcha_type} - {message}")
                
                return CAPTCHAInfo(
                    status=CAPTCHAStatus.DETECTED,
                    captcha_type=captcha_type,
                    message=message,
                    detection_time=detection_time,
                    timeout_seconds=self.timeout_seconds
                )
            else:
                return CAPTCHAInfo(
                    status=CAPTCHAStatus.NOT_DETECTED,
                    captcha_type="none",
                    message="No CAPTCHA detected",
                    detection_time=detection_time
                )
                
        except Exception as e:
            self.logger.error(f"Error detecting CAPTCHA: {e}")
            return CAPTCHAInfo(
                status=CAPTCHAStatus.ERROR,
                captcha_type="unknown",
                message=f"Error detecting CAPTCHA: {str(e)}",
                detection_time=time.time()
            )
    
    def wait_for_captcha_solution(self, captcha_info: CAPTCHAInfo) -> CAPTCHAInfo:
        """
        Wait for user to solve CAPTCHA with timeout handling.
        
        Args:
            captcha_info: Information about the detected CAPTCHA
            
        Returns:
            Updated CAPTCHAInfo with solution status
        """
        if captcha_info.status != CAPTCHAStatus.DETECTED:
            return captcha_info
        
        self.logger.info(f"Waiting for CAPTCHA solution (timeout: {self.timeout_seconds} seconds)")
        
        start_time = time.time()
        check_interval = 5  # Check every 5 seconds
        
        while time.time() - start_time < self.timeout_seconds:
            # Check if CAPTCHA is still present
            current_captcha = self.detect_captcha()
            
            if current_captcha.status == CAPTCHAStatus.NOT_DETECTED:
                # CAPTCHA appears to be solved
                self.logger.info("CAPTCHA appears to be solved")
                return CAPTCHAInfo(
                    status=CAPTCHAStatus.SOLVED,
                    captcha_type=captcha_info.captcha_type,
                    message="CAPTCHA successfully solved",
                    detection_time=captcha_info.detection_time,
                    timeout_seconds=self.timeout_seconds
                )
            
            # Check if page has changed significantly (indicating successful navigation)
            try:
                current_url = self.driver.current_url
                if "login" not in current_url.lower() and "captcha" not in current_url.lower():
                    # Page has navigated away from CAPTCHA
                    self.logger.info("Page navigated away from CAPTCHA - assuming solved")
                    return CAPTCHAInfo(
                        status=CAPTCHAStatus.SOLVED,
                        captcha_type=captcha_info.captcha_type,
                        message="CAPTCHA appears solved (page navigation detected)",
                        detection_time=captcha_info.detection_time,
                        timeout_seconds=self.timeout_seconds
                    )
            except Exception:
                pass
            
            # Wait before next check
            time.sleep(check_interval)
        
        # Timeout reached
        self.logger.warning(f"CAPTCHA solution timeout after {self.timeout_seconds} seconds")
        return CAPTCHAInfo(
            status=CAPTCHAStatus.TIMEOUT,
            captcha_type=captcha_info.captcha_type,
            message=f"CAPTCHA solution timeout after {self.timeout_seconds} seconds",
            detection_time=captcha_info.detection_time,
            timeout_seconds=self.timeout_seconds
        )
    
    def handle_captcha_with_user_notification(self, captcha_info: CAPTCHAInfo) -> Dict[str, Any]:
        """
        Handle CAPTCHA with user-friendly notification and waiting.
        
        Args:
            captcha_info: Information about the detected CAPTCHA
            
        Returns:
            Dictionary with handling result and user instructions
        """
        if captcha_info.status != CAPTCHAStatus.DETECTED:
            return {
                'success': False,
                'error': f"Invalid CAPTCHA status: {captcha_info.status}",
                'requires_user_action': False
            }
        
        # Generate user-friendly instructions
        instructions = self._generate_user_instructions(captcha_info)
        
        # Wait for solution
        solution_result = self.wait_for_captcha_solution(captcha_info)
        
        if solution_result.status == CAPTCHAStatus.SOLVED:
            return {
                'success': True,
                'message': 'CAPTCHA successfully solved',
                'requires_user_action': False,
                'instructions': instructions
            }
        elif solution_result.status == CAPTCHAStatus.TIMEOUT:
            return {
                'success': False,
                'error': 'CAPTCHA solution timeout - user did not solve within time limit',
                'requires_user_action': True,
                'instructions': instructions,
                'timeout_reached': True
            }
        else:
            return {
                'success': False,
                'error': f'CAPTCHA handling failed: {solution_result.message}',
                'requires_user_action': True,
                'instructions': instructions
            }
    
    def _determine_captcha_type(self, indicators: List[str], elements: List[str]) -> str:
        """Determine the type of CAPTCHA based on indicators and elements."""
        if any('recaptcha' in indicator.lower() for indicator in indicators + elements):
            return "reCAPTCHA"
        elif any('linkedin' in indicator.lower() for indicator in indicators):
            return "LinkedIn Security Challenge"
        elif any('puzzle' in indicator.lower() for indicator in indicators):
            return "Puzzle Challenge"
        elif any('verification' in indicator.lower() for indicator in indicators):
            return "Identity Verification"
        else:
            return "Generic CAPTCHA"
    
    def _generate_captcha_message(self, captcha_type: str, indicators: List[str]) -> str:
        """Generate a user-friendly CAPTCHA message."""
        if captcha_type == "LinkedIn Security Challenge":
            return "LinkedIn has detected automated access and requires manual verification"
        elif captcha_type == "reCAPTCHA":
            return "Google reCAPTCHA challenge detected - please complete the verification"
        elif captcha_type == "Puzzle Challenge":
            return "Security puzzle detected - please solve the challenge to continue"
        else:
            return f"Security verification required ({captcha_type})"
    
    def _generate_user_instructions(self, captcha_info: CAPTCHAInfo) -> Dict[str, str]:
        """Generate user-friendly instructions for CAPTCHA solving."""
        if captcha_info.captcha_type == "LinkedIn Security Challenge":
            return {
                'title': 'LinkedIn Security Verification Required',
                'message': 'LinkedIn has detected automated access and requires manual verification.',
                'steps': [
                    'Look for the browser window that opened automatically',
                    'Complete the security challenge (CAPTCHA, puzzle, or verification)',
                    'Wait for the page to load successfully',
                    'Click the "Continue Analysis" button below'
                ],
                'timeout_message': f'You have {self.timeout_seconds // 60} minutes to complete the verification'
            }
        elif captcha_info.captcha_type == "reCAPTCHA":
            return {
                'title': 'Google reCAPTCHA Challenge',
                'message': 'A Google reCAPTCHA challenge has been detected.',
                'steps': [
                    'Look for the reCAPTCHA widget in the browser window',
                    'Complete the verification (check boxes, image selection, etc.)',
                    'Wait for the verification to complete',
                    'Click the "Continue Analysis" button below'
                ],
                'timeout_message': f'You have {self.timeout_seconds // 60} minutes to complete the verification'
            }
        else:
            return {
                'title': 'Security Verification Required',
                'message': 'A security verification challenge has been detected.',
                'steps': [
                    'Look for the security challenge in the browser window',
                    'Complete the verification as instructed',
                    'Wait for the page to load successfully',
                    'Click the "Continue Analysis" button below'
                ],
                'timeout_message': f'You have {self.timeout_seconds // 60} minutes to complete the verification'
            }
    
    def set_driver(self, driver) -> None:
        """Set the WebDriver instance for CAPTCHA detection."""
        self.driver = driver
    
    def set_timeout(self, timeout_seconds: int) -> None:
        """Set the timeout for CAPTCHA solution waiting."""
        self.timeout_seconds = timeout_seconds


# Global instance for easy access
captcha_handler = CAPTCHAHandler() 