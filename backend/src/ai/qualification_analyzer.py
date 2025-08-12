"""
AI-powered job qualification analyzer for the Job Qualification Screening System.

This module provides functionality to analyze job descriptions against user qualifications
using Google's Gemini models to determine qualification scores and provide detailed reasoning.
"""

import os
import json
import logging
import time
import re
import threading
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
import google.generativeai as genai
from datetime import datetime, timedelta

from ..config.config_manager import UserProfile, AISettings
from ..data.models import QualificationResult, QualificationStatus, UserDecision

logger = logging.getLogger(__name__)


class DailyQuotaExhaustedException(Exception):
    """Raised when daily quota is exhausted and no more requests can be made today."""
    pass


class GeminiQuotaManager:
    """
    Global quota manager for Gemini API that handles quota exceeded errors
    and implements intelligent retry delays with buffer time.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure global quota management."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the quota manager (only once due to singleton)."""
        if not hasattr(self, '_initialized') or not self._initialized:
            self._quota_exceeded_until = None
            self._quota_lock = threading.Lock()
            self._buffer_seconds = 10  # Buffer time to add to retry_delay
            self._min_wait_time = 5    # Minimum wait time even if no retry_delay

            # Rate limiting attributes - Minute limits
            self._rpm_limit = int(os.getenv('GEMINI_RPM_LIMIT', 20))
            self._tpm_limit = int(os.getenv('GEMINI_TPM_LIMIT', 2000000))
            
            # Rate limiting attributes - Daily limits
            self._rpd_limit = int(os.getenv('GEMINI_RPD_LIMIT', 1500))
            
            self._rate_limiting_enabled = os.getenv('GEMINI_ENABLE_RATE_LIMITING', 'true').lower() == 'true'
            
            # Request tracking for RPM
            self._request_times = []  # List of request timestamps
            
            # Token tracking for TPM
            self._token_usage = []
            
            # Daily tracking
            self._daily_request_times = []  # List of request timestamps for the day
            self._last_daily_reset = datetime.now().date()

            self._initialized = True
    
    def _check_daily_reset(self) -> None:
        """Check if we need to reset daily counters (called within lock)."""
        current_date = datetime.now().date()
        if current_date > self._last_daily_reset:
            logger.info(f"📅 Resetting daily rate limit counters for {current_date}")
            self._daily_request_times = []
            self._last_daily_reset = current_date
    
    def is_quota_exceeded(self) -> bool:
        """Check if quota is currently exceeded and requests should be paused."""
        with self._quota_lock:
            if self._quota_exceeded_until is None:
                return False
            
            now = datetime.now()
            if now >= self._quota_exceeded_until:
                # Quota period has expired
                self._quota_exceeded_until = None
                logger.info("📈 Gemini quota period has expired, resuming requests")
                return False
            
            # Still in quota exceeded period
            remaining_time = (self._quota_exceeded_until - now).total_seconds()
            logger.debug(f"⏸️ Quota still exceeded, {remaining_time:.1f} seconds remaining")
            return True
    
    def handle_quota_error(self, error_message: str) -> int:
        """
        Handle quota exceeded error and set global pause period.
        
        Args:
            error_message: The full error message from Gemini API
            
        Returns:
            Total wait time in seconds (retry_delay + buffer)
        """
        retry_delay = self._extract_retry_delay(error_message)
        
        with self._quota_lock:
            # Calculate total wait time with buffer
            total_wait_seconds = max(retry_delay + self._buffer_seconds, self._min_wait_time)
            
            # Set the quota exceeded period
            self._quota_exceeded_until = datetime.now() + timedelta(seconds=total_wait_seconds)
            
            logger.warning(f"🚫 Gemini quota exceeded! Pausing ALL requests for {total_wait_seconds} seconds")
            logger.warning(f"   API retry_delay: {retry_delay}s, buffer: {self._buffer_seconds}s")
            logger.info(f"   Requests will resume at: {self._quota_exceeded_until.strftime('%H:%M:%S')}")
            
            return total_wait_seconds
    
    def _extract_retry_delay(self, error_message: str) -> int:
        """
        Extract retry_delay from Gemini error message.
        
        Args:
            error_message: Full error message from Gemini API
            
        Returns:
            Retry delay in seconds (0 if not found)
        """
        try:
            # Look for retry_delay pattern in the error message
            # Example: "retry_delay {\n  seconds: 44\n}"
            retry_delay_match = re.search(r'retry_delay\s*\{[^}]*seconds:\s*(\d+)', error_message, re.DOTALL)
            
            if retry_delay_match:
                retry_seconds = int(retry_delay_match.group(1))
                logger.debug(f"📊 Extracted retry_delay: {retry_seconds} seconds")
                return retry_seconds
            
            # Also look for retry_delay in JSON format
            # Example: {"retry_delay": 86400} for daily limits
            json_match = re.search(r'"retry_delay"\s*:\s*(\d+)', error_message)
            if json_match:
                retry_seconds = int(json_match.group(1))
                logger.debug(f"📊 Extracted retry_delay from JSON: {retry_seconds} seconds")
                return retry_seconds
            
            # Check for "retry after" patterns
            # Example: "retry after 24 hours" or "retry after 86400 seconds"
            retry_after_match = re.search(r'retry after\s+(\d+)\s*(hours?|minutes?|seconds?)', error_message, re.IGNORECASE)
            if retry_after_match:
                value = int(retry_after_match.group(1))
                unit = retry_after_match.group(2).lower()
                
                if 'hour' in unit:
                    retry_seconds = value * 3600
                elif 'minute' in unit:
                    retry_seconds = value * 60
                else:  # seconds
                    retry_seconds = value
                
                logger.debug(f"📊 Extracted retry_after: {retry_seconds} seconds")
                return retry_seconds
            
            # If we detect daily limit error but no specific time, assume 24 hours
            error_lower = error_message.lower()
            if any(indicator in error_lower for indicator in ['per day', 'daily', 'rpd', 'tpd']):
                logger.warning("⚠️ Daily limit detected without specific retry_delay, assuming 24 hours")
                return 86400  # 24 hours in seconds
            
            logger.warning("⚠️ Could not extract retry_delay from error message, using minimum wait time")
            logger.debug(f"Error message: {error_message}")
            return 0
                
        except Exception as e:
            logger.error(f"❌ Error parsing retry_delay: {e}")
            return 0
    
    def wait_for_quota_reset(self) -> None:
        """Wait until quota is reset if currently exceeded."""
        if not self.is_quota_exceeded():
            return
        
        with self._quota_lock:
            if self._quota_exceeded_until is None:
                return
            
            now = datetime.now()
            if now >= self._quota_exceeded_until:
                return
            
            wait_time = (self._quota_exceeded_until - now).total_seconds()
            logger.info(f"⏳ Waiting {wait_time:.1f} seconds for quota reset...")
            
        # Wait outside the lock to allow other threads to check status
        time.sleep(wait_time)
    
    def reset_quota_status(self) -> None:
        """Manually reset quota status (for testing or emergency use)."""
        with self._quota_lock:
            if self._quota_exceeded_until is not None:
                logger.info("🔄 Manually resetting quota status")
                self._quota_exceeded_until = None
    
    def get_quota_status(self) -> Dict[str, Any]:
        """Get current quota status information."""
        with self._quota_lock:
            if self._quota_exceeded_until is None:
                return {
                    "quota_exceeded": False,
                    "remaining_time": 0,
                    "reset_time": None,
                    "is_daily_limit": False
                }
            
            now = datetime.now()
            remaining_time = max(0, (self._quota_exceeded_until - now).total_seconds())
            
            # Check if this is a daily limit (long wait time)
            is_daily_limit = remaining_time > 3600  # More than 1 hour suggests daily limit
            
            return {
                "quota_exceeded": remaining_time > 0,
                "remaining_time": remaining_time,
                "reset_time": self._quota_exceeded_until.isoformat() if remaining_time > 0 else None,
                "is_daily_limit": is_daily_limit
            }
        
    def check_rate_limits_and_wait(self, estimated_tokens: int = 1000) -> None:
        """
        Check RPM, TPM, and RPD limits and wait if necessary before making a request.
        
        Args:
            estimated_tokens: Estimated tokens for the upcoming request
        """
        if not self._rate_limiting_enabled:
            return
        
        with self._quota_lock:
            now = datetime.now()
            
            # Check if we need to reset daily counters
            self._check_daily_reset()
            
            # Clean old entries (older than 1 minute)
            cutoff_time = now - timedelta(minutes=1)
            self._request_times = [t for t in self._request_times if t > cutoff_time]
            self._token_usage = [(t, tokens) for t, tokens in self._token_usage if t > cutoff_time]
            
            # Check RPM limit
            if len(self._request_times) >= self._rpm_limit:
                oldest_request = min(self._request_times)
                wait_until_rpm = oldest_request + timedelta(minutes=1)
                wait_seconds_rpm = max(0, (wait_until_rpm - now).total_seconds())
            else:
                wait_seconds_rpm = 0
            
            # Check TPM limit
            current_tokens = sum(tokens for _, tokens in self._token_usage)
            if current_tokens + estimated_tokens > self._tpm_limit:
                # Find when we can make the request without exceeding TPM
                sorted_usage = sorted(self._token_usage, key=lambda x: x[0])
                tokens_to_free = (current_tokens + estimated_tokens) - self._tpm_limit
                
                wait_until_tpm = now
                freed_tokens = 0
                for timestamp, tokens in sorted_usage:
                    freed_tokens += tokens
                    wait_until_tpm = timestamp + timedelta(minutes=1)
                    if freed_tokens >= tokens_to_free:
                        break
                
                wait_seconds_tpm = max(0, (wait_until_tpm - now).total_seconds())
            else:
                wait_seconds_tpm = 0
            
            # Check RPD limit
            if len(self._daily_request_times) >= self._rpd_limit:
                # Need to wait until next day
                next_day = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                wait_seconds_rpd = (next_day - now).total_seconds()
            else:
                wait_seconds_rpd = 0
            
            # Wait for the longest of all limits
            wait_seconds = max(wait_seconds_rpm, wait_seconds_tpm, wait_seconds_rpd)
            
            if wait_seconds > 0:
                if wait_seconds_rpd > 0:
                    wait_type = "RPD"
                    logger.warning(f"🚦 Daily rate limit reached: Waiting until tomorrow ({wait_seconds/3600:.1f} hours) due to {wait_type} limit")
                else:
                    wait_type = "RPM" if wait_seconds_rpm > wait_seconds_tpm else "TPM"
                    logger.info(f"🚦 Rate limiting: Waiting {wait_seconds:.1f}s due to {wait_type} limit")
                
        # Wait outside the lock
        if wait_seconds > 0:
            time.sleep(wait_seconds)

    def record_request(self, token_count: int = 1000) -> None:
        """
        Record a request for rate limiting tracking.
        
        Args:
            token_count: Actual tokens used in the request
        """
        if not self._rate_limiting_enabled:
            return
        
        with self._quota_lock:
            now = datetime.now()
            
            # Check if we need to reset daily counters
            self._check_daily_reset()
            
            # Record for minute-based limits
            self._request_times.append(now)
            self._token_usage.append((now, token_count))
            
            # Record for daily limits
            self._daily_request_times.append(now)
            
            # Keep only last minute of data for minute-based tracking
            cutoff_time = now - timedelta(minutes=1)
            self._request_times = [t for t in self._request_times if t > cutoff_time]
            self._token_usage = [(t, tokens) for t, tokens in self._token_usage if t > cutoff_time]

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limiting status."""
        if not self._rate_limiting_enabled:
            return {"rate_limiting_enabled": False}
        
        with self._quota_lock:
            now = datetime.now()
            cutoff_time = now - timedelta(minutes=1)
            
            # Check if we need to reset daily counters
            self._check_daily_reset()
            
            # Clean and count current usage
            recent_requests = [t for t in self._request_times if t > cutoff_time]
            recent_tokens = sum(tokens for t, tokens in self._token_usage if t > cutoff_time)
            
            # Count daily usage
            daily_requests = len(self._daily_request_times)
            
            return {
                "rate_limiting_enabled": True,
                # Minute limits
                "rpm_limit": self._rpm_limit,
                "tpm_limit": self._tpm_limit,
                "current_rpm": len(recent_requests),
                "current_tpm": recent_tokens,
                "rpm_available": self._rpm_limit - len(recent_requests),
                "tpm_available": self._tpm_limit - recent_tokens,
                # Daily limits
                "rpd_limit": self._rpd_limit,
                "current_rpd": daily_requests,
                "rpd_available": self._rpd_limit - daily_requests,
                "last_daily_reset": self._last_daily_reset.isoformat()
            }


@dataclass
class AnalysisRequest:
    """Request for job qualification analysis with enhanced profile support."""
    
    # Core job information
    job_title: str
    company: str
    job_description: str
    
    # AI configuration
    ai_settings: AISettings
    
    # Enhanced user profile data (for backward compatibility)
    user_profile: Optional[UserProfile] = None
    
    # Resume data (structured or raw text)
    resume_data: Optional[Dict[str, Any]] = None
    resume_text: Optional[str] = None
    
    # Detailed profile fields for weighted scoring
    years_experience: Optional[int] = None
    experience_level: Optional[str] = None
    skills: Optional[List[str]] = None
    education_level: Optional[str] = None
    field_of_study: Optional[str] = None
    education_details: Optional[str] = None
    work_arrangement: Optional[str] = None
    preferred_locations: Optional[List[str]] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    
    def __post_init__(self):
        """Extract profile data from user_profile if detailed fields not provided."""
        if self.user_profile and not self.years_experience:
            self.years_experience = self.user_profile.years_of_experience
            self.experience_level = self.user_profile.experience_level
            self.skills = self.user_profile.additional_skills
            self.education_level = "college" if self.user_profile.has_college_degree else "high_school"
            self.field_of_study = self.user_profile.field_of_study
            self.education_details = self.user_profile.education_details
            self.work_arrangement = self.user_profile.remote_preference
            self.preferred_locations = self.user_profile.preferred_locations
            self.salary_min = self.user_profile.salary_min
            self.salary_max = self.user_profile.salary_max
    
    @property
    def has_resume(self) -> bool:
        """Check if resume data is available."""
        return bool(self.resume_data or self.resume_text)
    
    def get_resume_content(self) -> str:
        """Get resume content as text."""
        if self.resume_text:
            return self.resume_text
        elif self.resume_data:
            # Convert structured resume data to text format
            content_parts = []
            
            if 'summary' in self.resume_data:
                content_parts.append(f"Summary: {self.resume_data['summary']}")
            
            if 'experience' in self.resume_data:
                content_parts.append("Experience:")
                for exp in self.resume_data['experience']:
                    content_parts.append(f"- {exp.get('title', '')} at {exp.get('company', '')} ({exp.get('duration', '')})")
                    if exp.get('description'):
                        content_parts.append(f"  {exp['description']}")
            
            if 'education' in self.resume_data:
                content_parts.append("Education:")
                for edu in self.resume_data['education']:
                    content_parts.append(f"- {edu.get('degree', '')} in {edu.get('field', '')} from {edu.get('institution', '')}")
            
            if 'skills' in self.resume_data:
                skills_data = self.resume_data['skills']
                if isinstance(skills_data, dict):
                    for category, skill_list in skills_data.items():
                        if isinstance(skill_list, list):
                            content_parts.append(f"{category}: {', '.join(skill_list)}")
                elif isinstance(skills_data, list):
                    content_parts.append(f"Skills: {', '.join(skills_data)}")
            
            if 'projects' in self.resume_data:
                content_parts.append("Projects:")
                for project in self.resume_data['projects']:
                    content_parts.append(f"- {project.get('name', '')}")
                    if project.get('description'):
                        content_parts.append(f"  {project['description']}")
            
            if 'certifications' in self.resume_data:
                certs = self.resume_data['certifications']
                if isinstance(certs, list) and certs:
                    content_parts.append(f"Certifications: {', '.join(certs)}")
            
            return "\n".join(content_parts)
        
        return ""


@dataclass
class AnalysisResponse:
    """Response from AI qualification analysis with enhanced scoring details."""
    
    # Core scoring
    qualification_score: int
    qualification_status: QualificationStatus
    confidence_score: int  # New: confidence in the assessment (0-100)
    
    # AI analysis
    ai_reasoning: str
    required_experience: str
    education_requirements: str
    key_skills_mentioned: List[str]
    matching_strengths: List[str]
    potential_concerns: List[str]
    recommendations: List[str]  # New: specific improvement suggestions
    
    # Component scoring breakdown (for transparency)
    component_scores: Dict[str, int] = field(default_factory=dict)  # New: detailed breakdown
    requirements_met: str = ""  # New: "X out of Y requirements satisfied"
    
    # Metadata
    ai_model_used: str = ""
    analysis_duration: float = 0.0
    scoring_method: str = ""  # New: "resume_weighted" or "profile_only"


@dataclass
class JobEvaluationResult:
    """Result of job evaluation with retry information."""
    
    success: bool
    qualification_result: Optional[QualificationResult]
    attempts: int
    error_message: Optional[str] = None
    job_id: str = ""
    job_title: str = ""


class QualificationAnalyzer:
    """
    AI-powered analyzer for job qualification assessment with robust retry logic.
    
    This class uses Google's Gemini models to analyze job descriptions
    and determine if a user qualifies for specific positions.
    Implements retry logic for failed API calls and JSON parsing.
    """
    
    def __init__(self, ai_settings: AISettings):
        """
        Initialize the qualification analyzer.
        
        Args:
            ai_settings: AI configuration settings
        """
        self.ai_settings = ai_settings
        self.model = None
        self.quota_manager = GeminiQuotaManager()
        self._initialize_client()
    
    def is_quota_available(self) -> Tuple[bool, Optional[str]]:
        """
        Check if quota is available for making requests.
        
        Returns:
            Tuple of (is_available, error_message)
            - is_available: True if requests can be made, False otherwise
            - error_message: Human-readable message if quota is not available
        """
        quota_status = self.quota_manager.get_quota_status()
        
        if not quota_status['quota_exceeded']:
            return True, None
        
        if quota_status['is_daily_limit']:
            hours_remaining = quota_status['remaining_time'] / 3600
            return False, f"Daily quota limit reached. Please wait {hours_remaining:.1f} hours until tomorrow or upgrade your Gemini API plan."
        else:
            minutes_remaining = quota_status['remaining_time'] / 60
            return False, f"Temporary rate limit. Please wait {minutes_remaining:.1f} minutes before trying again."
    
    def _initialize_client(self) -> None:
        """Initialize the Google Gemini client."""
        try:
            if not self.ai_settings.api_key:
                raise ValueError("Google Gemini API key not provided")
            
            # Configure the Gemini API
            genai.configure(api_key=self.ai_settings.api_key)
            
            # Initialize the model
            self.model = genai.GenerativeModel(self.ai_settings.model)
            
            logger.info("Google Gemini client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Gemini client: {e}")
            raise
    
    def analyze_job_qualification_with_retry(self, request: AnalysisRequest, max_retries: int = 2) -> AnalysisResponse:
        """
        Analyze job qualification using AI with retry logic.
        
        Args:
            request: Analysis request containing job and user information
            max_retries: Maximum number of retry attempts (default: 2)
            
        Returns:
            Analysis response with qualification assessment
            
        Raises:
            Exception: If all retry attempts fail
        """
        last_error = None
        
        for attempt in range(max_retries + 1):  # +1 for initial attempt
            try:
                logger.info(f"Gemini analysis attempt {attempt + 1}/{max_retries + 1} for job: {request.job_title}")
                
                # Call the API
                response = self._call_gemini_api_with_retry(request, attempt)
                
                # Parse the response
                parsed_data = self._parse_ai_response_with_retry(response, attempt)
                
                # Create analysis response
                analysis_response = self._create_analysis_response(parsed_data, request)
                
                logger.info(f"✅ Gemini analysis successful on attempt {attempt + 1} for job: {request.job_title}")
                return analysis_response
                
            except DailyQuotaExhaustedException as e:
                # Don't retry for daily quota exhaustion
                logger.error(f"🛑 Stopping analysis - daily quota exhausted: {e}")
                raise
            except Exception as e:
                last_error = e
                logger.warning(f"⚠️ Gemini analysis attempt {attempt + 1} failed for job '{request.job_title}': {e}")
                
                if attempt < max_retries:
                    # Wait before retry with exponential backoff
                    wait_time = (2 ** attempt) * 1  # 1s, 2s, 4s, etc.
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ All {max_retries + 1} attempts failed for job '{request.job_title}': {e}")
        
        # If we get here, all attempts failed
        raise Exception(f"Gemini analysis failed after {max_retries + 1} attempts: {last_error}")
    
    def _call_gemini_api_with_retry(self, request: AnalysisRequest, attempt: int) -> str:
        """
        Call the Gemini API with quota-aware retry logic and proactive rate limiting.
        
        Args:
            request: Analysis request
            attempt: Current attempt number (for logging)
            
        Returns:
            API response text
            
        Raises:
            Exception: If API call fails
        """
        try:
            # Check if quota is currently exceeded and wait if necessary
            if self.quota_manager.is_quota_exceeded():
                logger.info(f"⏸️ Quota exceeded, waiting before API call for job: {request.job_title}")
                self.quota_manager.wait_for_quota_reset()
            
            # NEW: Proactive rate limiting check
            estimated_tokens = self._estimate_tokens(request)
            self.quota_manager.check_rate_limits_and_wait(estimated_tokens)
            
            prompt = self._create_analysis_prompt(request)
            
            # Generate content using Gemini
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.ai_settings.temperature,
                    max_output_tokens=self.ai_settings.max_tokens,
                )
            )
            
            if not response.text:
                raise ValueError("Empty response from Gemini API")
            
            # NEW: Record the actual request for rate limiting
            actual_tokens = self._calculate_actual_tokens(prompt, response.text)
            self.quota_manager.record_request(actual_tokens)
            
            return response.text
            
        except Exception as e:
            error_message = str(e)
            
            # Check if this is a quota exceeded error
            if self._is_quota_exceeded_error(error_message):
                logger.warning(f"🚫 Quota exceeded on attempt {attempt + 1} for job '{request.job_title}'")
                
                # Check if this is specifically a daily quota exhaustion (free tier limit)
                if self._is_daily_quota_exhausted_error(error_message):
                    logger.error(f"🛑 Daily quota exhausted for free tier (200 requests/day). Cannot process more jobs today.")
                    # For daily exhaustion, set a very long wait time to effectively stop processing
                    self.quota_manager.handle_quota_error(error_message)
                    raise DailyQuotaExhaustedException(
                        "Daily free tier limit (200 requests) reached. Please wait until tomorrow or upgrade your plan."
                    )
                
                # Handle the quota error globally
                wait_time = self.quota_manager.handle_quota_error(error_message)
                
                # Re-raise with enhanced error message
                raise Exception(f"Quota exceeded (waiting {wait_time}s): {error_message}")
            else:
                logger.error(f"Gemini API call failed on attempt {attempt + 1}: {e}")
                raise
    
    def _is_quota_exceeded_error(self, error_message: str) -> bool:
        """
        Check if the error is a quota exceeded error.
        
        Args:
            error_message: The error message to check
            
        Returns:
            True if this is a quota exceeded error
        """
        quota_indicators = [
            "429",
            "exceeded your current quota", 
            "quota exceeded",
            "quota limit",
            "rate limit",
            "too many requests",
            "retry_delay",
            "per day",
            "daily quota",
            "rpd",
            "requests per day",
            "GenerateRequestsPerDayPerProjectPerModel-FreeTier",
            "free_tier_requests"
        ]
        
        error_lower = error_message.lower()
        return any(indicator in error_lower for indicator in quota_indicators)
    
    def _is_daily_quota_exhausted_error(self, error_message: str) -> bool:
        """
        Check if this is specifically a daily quota exhaustion error (free tier limit reached).
        
        Args:
            error_message: The error message to check
            
        Returns:
            True if this is a daily quota exhaustion error
        """
        # Check for free tier daily limit indicators
        daily_exhaustion_indicators = [
            "GenerateRequestsPerDayPerProjectPerModel-FreeTier",
            "free_tier_requests",
            "quota_value: 200"  # Free tier limit
        ]
        
        return any(indicator in error_message for indicator in daily_exhaustion_indicators)
    
    def _parse_ai_response_with_retry(self, response: str, attempt: int) -> Dict[str, Any]:
        """
        Parse the enhanced AI response with retry logic for JSON parsing errors.
        
        Args:
            response: Raw API response text
            attempt: Current attempt number (for logging)
            
        Returns:
            Parsed JSON data with enhanced validation
            
        Raises:
            Exception: If JSON parsing fails
        """
        try:
            # Try to extract JSON from the response
            # Sometimes the AI includes additional text before or after the JSON
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in AI response")
            
            json_str = response[json_start:json_end]
            data = json.loads(json_str)
            
            # Validate required fields
            required_fields = ['qualification_score', 'ai_reasoning']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Ensure qualification score is within valid range (1-100, not 0)
            score = data.get('qualification_score', 1)
            if not isinstance(score, int) or score < 1 or score > 100:
                data['qualification_score'] = max(1, min(100, int(score)))
            
            # Ensure confidence score is within valid range
            confidence = data.get('confidence_score', 50)
            if not isinstance(confidence, int) or confidence < 1 or confidence > 100:
                data['confidence_score'] = max(1, min(100, int(confidence)))
            
            # Ensure component_scores is a dictionary
            if 'component_scores' not in data or not isinstance(data['component_scores'], dict):
                data['component_scores'] = {}
            
            # Validate component scores are within range
            for component, score in data['component_scores'].items():
                if not isinstance(score, (int, float)) or score < 0 or score > 100:
                    data['component_scores'][component] = max(0, min(100, int(score)))
                else:
                    data['component_scores'][component] = int(score)
            
            # Ensure lists are properly formatted
            list_fields = ['key_skills_mentioned', 'matching_strengths', 'potential_concerns', 'recommendations']
            for list_field in list_fields:
                if list_field not in data or not isinstance(data[list_field], list):
                    data[list_field] = []
            
            # Ensure string fields are properly formatted
            string_fields = ['required_experience', 'education_requirements', 'requirements_met']
            for string_field in string_fields:
                if string_field not in data or not isinstance(data[string_field], str):
                    data[string_field] = ""
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed on attempt {attempt + 1}: {e}")
            logger.error(f"Response: {response}")
            raise ValueError(f"Invalid JSON response: {e}")
        except Exception as e:
            logger.error(f"Response parsing failed on attempt {attempt + 1}: {e}")
            raise
    
    def _create_analysis_response(self, parsed_data: Dict[str, Any], request: AnalysisRequest) -> AnalysisResponse:
        """
        Create enhanced AnalysisResponse from parsed data.
        
        Args:
            parsed_data: Parsed JSON data from API
            request: Original analysis request
            
        Returns:
            AnalysisResponse object with enhanced fields
        """
        score = parsed_data.get('qualification_score', 1)
        
        return AnalysisResponse(
            qualification_score=score,
            qualification_status=self._score_to_status(score),
            confidence_score=parsed_data.get('confidence_score', 50),
            ai_reasoning=parsed_data.get('ai_reasoning', ''),
            required_experience=parsed_data.get('required_experience', ''),
            education_requirements=parsed_data.get('education_requirements', ''),
            key_skills_mentioned=parsed_data.get('key_skills_mentioned', []),
            matching_strengths=parsed_data.get('matching_strengths', []),
            potential_concerns=parsed_data.get('potential_concerns', []),
            recommendations=parsed_data.get('recommendations', []),
            component_scores=parsed_data.get('component_scores', {}),
            requirements_met=parsed_data.get('requirements_met', ''),
            ai_model_used=self.ai_settings.model,
            analysis_duration=0.0,  # Will be set by caller
            scoring_method="resume_weighted" if request.has_resume else "profile_only"
        )
    
    def evaluate_job_with_retry(self, job: Dict[str, Any], user_profile: UserProfile, max_retries: int = 2, resume_data: Optional[Dict[str, Any]] = None) -> JobEvaluationResult:
        """
        Evaluate a single job with retry logic.
        
        Args:
            job: Job dictionary with title, company, description, etc.
            user_profile: User qualification profile
            max_retries: Maximum number of retry attempts
            resume_data: Optional processed resume data for enhanced analysis
            
        Returns:
            JobEvaluationResult with success status and qualification result
        """
        job_id = job.get('id', '')
        job_title = job.get('title', 'Unknown')
        last_error = None
        
        logger.info(f"🔍 Starting job evaluation for: {job_title} (ID: {job_id})")
        
        for attempt in range(max_retries + 1):
            try:
                # Create analysis request
                request = AnalysisRequest(
                    job_title=job.get('title', ''),
                    company=job.get('company', ''),
                    job_description=job.get('description', ''),
                    user_profile=user_profile,
                    ai_settings=self.ai_settings,
                    resume_data=resume_data
                )
                
                # Analyze with retry logic
                start_time = time.time()
                analysis_response = self.analyze_job_qualification_with_retry(request, max_retries=0)  # No retries here since we handle it in the loop
                analysis_duration = time.time() - start_time
                
                # Update analysis duration
                analysis_response.analysis_duration = analysis_duration
                
                # Create qualification result
                qualification_result = self.create_qualification_result(
                    job_id=job_id,
                    job_title=job.get('title', ''),
                    company=job.get('company', ''),
                    linkedin_url=job.get('linkedin_url', ''),
                    analysis_response=analysis_response
                )
                
                logger.info(f"✅ Job evaluation successful for '{job_title}' (attempt {attempt + 1})")
                
                return JobEvaluationResult(
                    success=True,
                    qualification_result=qualification_result,
                    attempts=attempt + 1,
                    job_id=job_id,
                    job_title=job_title
                )
                
            except Exception as e:
                last_error = e
                error_msg = f"Job evaluation failed on attempt {attempt + 1}: {e}"
                logger.warning(f"⚠️ {error_msg} for job: {job_title}")
                
                if attempt < max_retries:
                    # Wait before retry with exponential backoff
                    wait_time = (2 ** attempt) * 1  # 1s, 2s, 4s, etc.
                    logger.info(f"Retrying job '{job_title}' in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ All {max_retries + 1} attempts failed for job '{job_title}': {e}")
        
        # If we get here, all attempts failed
        return JobEvaluationResult(
            success=False,
            qualification_result=None,
            attempts=max_retries + 1,
            error_message=f"All {max_retries + 1} attempts failed: {str(last_error) if last_error else 'Unknown error'}",
            job_id=job_id,
            job_title=job_title
        )
    
    def batch_analyze_jobs_with_retry(self, jobs: List[Dict[str, Any]], user_profile: UserProfile, max_retries: int = 2) -> Tuple[List[QualificationResult], List[JobEvaluationResult]]:
        """
        Analyze multiple jobs with robust retry logic.
        
        Args:
            jobs: List of job dictionaries with title, company, description, etc.
            user_profile: User qualification profile
            max_retries: Maximum number of retry attempts per job
            
        Returns:
            Tuple of (successful_results, all_evaluation_results)
            - successful_results: Only jobs that passed Gemini evaluation
            - all_evaluation_results: All evaluation results including failures
        """
        successful_results = []
        all_evaluation_results = []
        
        logger.info(f"🚀 Starting batch analysis of {len(jobs)} jobs with retry logic")
        
        for i, job in enumerate(jobs, 1):
            job_title = job.get('title', 'Unknown')
            logger.info(f"📋 Processing job {i}/{len(jobs)}: {job_title}")
            
            # Evaluate job with retry logic
            evaluation_result = self.evaluate_job_with_retry(job=job, user_profile=user_profile, max_retries=max_retries)
            all_evaluation_results.append(evaluation_result)
            
            if evaluation_result.success:
                successful_results.append(evaluation_result.qualification_result)
                logger.info(f"✅ Job {i}/{len(jobs)} successful: {job_title}")
            else:
                logger.warning(f"❌ Job {i}/{len(jobs)} failed after {evaluation_result.attempts} attempts: {job_title}")
                logger.debug(f"   Error: {evaluation_result.error_message}")
            
            # Add delay between requests to respect rate limits
            if i < len(jobs):
                # Check quota status before proceeding to next job
                if self.quota_manager.is_quota_exceeded():
                    logger.info("⏸️ Quota exceeded during batch processing, waiting before next job...")
                    self.quota_manager.wait_for_quota_reset()
                else:
                    time.sleep(1)  # 1 second delay between requests
        
        # Log summary
        successful_count = len(successful_results)
        failed_count = len(jobs) - successful_count
        
        logger.info(f"📊 Batch analysis completed:")
        logger.info(f"   ✅ Successful: {successful_count}/{len(jobs)} jobs")
        logger.info(f"   ❌ Failed: {failed_count}/{len(jobs)} jobs")
        
        if failed_count > 0:
            logger.warning(f"⚠️ {failed_count} jobs failed Gemini evaluation and will not be saved to database")
        
        return successful_results, all_evaluation_results
    
    # Legacy methods for backward compatibility
    
    def analyze_job_qualification(self, request: AnalysisRequest) -> AnalysisResponse:
        """
        Legacy method for job qualification analysis (maintains backward compatibility).
        
        Args:
            request: Analysis request containing job and user information
            
        Returns:
            Analysis response with qualification assessment
        """
        return self.analyze_job_qualification_with_retry(request, max_retries=2)
    
    def batch_analyze_jobs(
        self, 
        jobs: List[Dict[str, Any]], 
        user_profile: UserProfile
    ) -> List[QualificationResult]:
        """
        Legacy method for batch job analysis (maintains backward compatibility).
        
        Args:
            jobs: List of job dictionaries with title, company, description, etc.
            user_profile: User qualification profile
            
        Returns:
            List of QualificationResult objects (only successful evaluations)
        """
        successful_results, _ = self.batch_analyze_jobs_with_retry(jobs, user_profile, max_retries=2)
        return successful_results
    
    def _call_gemini_api(self, prompt: str) -> str:
        """
        Legacy method for Gemini API calls with quota awareness (maintains backward compatibility).
        
        Args:
            prompt: Analysis prompt
            
        Returns:
            API response text
        """
        try:
            # Check if quota is currently exceeded and wait if necessary
            if self.quota_manager.is_quota_exceeded():
                logger.info("⏸️ Quota exceeded, waiting before legacy API call...")
                self.quota_manager.wait_for_quota_reset()
            
            # Generate content using Gemini
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.ai_settings.temperature,
                    max_output_tokens=self.ai_settings.max_tokens,
                )
            )
            
            return response.text
            
        except Exception as e:
            error_message = str(e)
            
            # Check if this is a quota exceeded error
            if self._is_quota_exceeded_error(error_message):
                logger.warning("🚫 Quota exceeded in legacy API call")
                wait_time = self.quota_manager.handle_quota_error(error_message)
                raise Exception(f"Quota exceeded (waiting {wait_time}s): {error_message}")
            else:
                logger.error(f"Gemini API call failed: {e}")
                raise
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """
        Legacy method for parsing AI responses (maintains backward compatibility).
        
        Args:
            response: Raw API response text
            
        Returns:
            Parsed JSON data
        """
        try:
            # Try to extract JSON from the response
            # Sometimes the AI includes additional text before or after the JSON
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in AI response")
            
            json_str = response[json_start:json_end]
            data = json.loads(json_str)
            
            # Validate required fields
            required_fields = ['qualification_score', 'ai_reasoning']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Ensure qualification score is within valid range
            score = data.get('qualification_score', 0)
            if not isinstance(score, int) or score < 0 or score > 100:
                data['qualification_score'] = max(0, min(100, int(score)))
            
            # Ensure lists are properly formatted
            for list_field in ['key_skills_mentioned', 'matching_strengths', 'potential_concerns']:
                if list_field not in data or not isinstance(data[list_field], list):
                    data[list_field] = []
            
            # Ensure string fields are properly formatted
            for string_field in ['required_experience', 'education_requirements']:
                if string_field not in data or not isinstance(data[string_field], str):
                    data[string_field] = ""
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"Response: {response}")
            # Return a default response
            return {
                'qualification_score': 0,
                'ai_reasoning': f"Failed to parse AI response: {str(e)}",
                'required_experience': '',
                'education_requirements': '',
                'key_skills_mentioned': [],
                'matching_strengths': [],
                'potential_concerns': ['AI response parsing failed']
            }
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            raise
    
    def create_qualification_result(
        self, 
        job_id: str,
        job_title: str,
        company: str,
        linkedin_url: str,
        analysis_response: AnalysisResponse
    ) -> QualificationResult:
        """
        Create a QualificationResult from enhanced analysis response.
        
        Args:
            job_id: The job ID
            job_title: The job title
            company: The company name
            linkedin_url: The job URL
            analysis_response: The AI analysis response with enhanced scoring
            
        Returns:
            QualificationResult object
        """
        # Create enhanced AI reasoning that includes component breakdown
        enhanced_reasoning = analysis_response.ai_reasoning
        
        if analysis_response.component_scores:
            enhanced_reasoning += "\n\nComponent Scores Breakdown:\n"
            for component, score in analysis_response.component_scores.items():
                enhanced_reasoning += f"• {component.replace('_', ' ').title()}: {score}/100\n"
        
        if analysis_response.requirements_met:
            enhanced_reasoning += f"\nRequirements Analysis: {analysis_response.requirements_met}\n"
        
        if analysis_response.recommendations:
            enhanced_reasoning += f"\nRecommendations:\n"
            for rec in analysis_response.recommendations:
                enhanced_reasoning += f"• {rec}\n"
        
        enhanced_reasoning += f"\nScoring Method: {analysis_response.scoring_method.replace('_', ' ').title()}"
        enhanced_reasoning += f"\nConfidence Score: {analysis_response.confidence_score}/100"
        
        return QualificationResult(
            job_id=job_id,
            job_title=job_title,
            company=company,
            linkedin_url=linkedin_url,
            qualification_score=analysis_response.qualification_score,
            qualification_status=analysis_response.qualification_status,
            ai_reasoning=enhanced_reasoning,
            required_experience=analysis_response.required_experience,
            education_requirements=analysis_response.education_requirements,
            key_skills_mentioned=analysis_response.key_skills_mentioned,
            matching_strengths=analysis_response.matching_strengths,
            potential_concerns=analysis_response.potential_concerns,
            user_decision=UserDecision.PENDING,
            ai_model_used=analysis_response.ai_model_used,
            analysis_duration=analysis_response.analysis_duration
        )
    
    def _create_analysis_prompt(self, request: AnalysisRequest) -> str:
        """
        Create an analysis prompt with sophisticated weighted scoring.
        
        This method implements intelligent scoring based on available data:
        - Resume + Profile: 70% resume analysis + 30% profile verification
        - Profile Only: 100% profile-based analysis with weighted components
        """
        
        # Determine if resume is available
        has_resume = request.has_resume
        resume_content = request.get_resume_content() if has_resume else "Not provided"
        
        # Format candidate information
        years_exp = request.years_experience or 0
        exp_level = request.experience_level or "not specified"
        skills = request.skills or []
        education_level = request.education_level or "not specified"
        field_of_study = request.field_of_study or "not specified"
        education_details = request.education_details or ""
        work_arrangement = request.work_arrangement or "any"
        locations = request.preferred_locations or ["any"]
        salary_min = request.salary_min or "not specified"
        salary_max = request.salary_max or "not specified"
        
        # Create the prompt
        prompt = f"""
You are an expert job qualification analyst. You MUST return ONLY valid, parseable JSON with no additional text.

JOB DETAILS:
- Title: {request.job_title}
- Company: {request.company}
- Requirements: {request.job_description}

CANDIDATE INFORMATION:
- Resume Available: {has_resume}
- Resume Content: {resume_content}
- Years of Experience: {years_exp}
- Experience Level: {exp_level}
- Skills: {', '.join(skills) if skills else 'None specified'}
- Education Level: {education_level}
- Field of Study: {field_of_study}
- Education Details: {education_details}
- Work Arrangement Preference: {work_arrangement}
- Preferred Locations: {', '.join(locations)}
- Salary Range: ${salary_min} - ${salary_max}

SCORING INSTRUCTIONS:
{"[RESUME AVAILABLE - Use 70/30 Resume+Profile Split]" if has_resume else "[RESUME NOT AVAILABLE - Use 100% Profile Analysis]"}

{self._get_scoring_weights(has_resume)}

CALCULATE COMPONENT SCORES (0-100 each):
{self._get_component_instructions(has_resume)}

CRITICAL JSON FORMATTING REQUIREMENTS:
1. Return ONLY valid JSON - no text before or after
2. All strings must use proper JSON escaping
3. No markdown formatting (**, __, etc.) in JSON string values
4. Use plain text descriptions without special characters
5. All numeric values must be integers (no decimals)
6. Array elements must be properly quoted strings

REQUIRED JSON STRUCTURE (copy this exact format):
{{
    "qualification_score": 85,
    "confidence_score": 90,
    "component_scores": {{
        {self._get_component_json_keys(has_resume)}
    }},
    "ai_reasoning": "Detailed explanation using plain text only. No special formatting or escape characters.",
    "required_experience": "Experience requirements from job posting",
    "education_requirements": "Education requirements from job posting", 
    "key_skills_mentioned": ["skill1", "skill2", "skill3"],
    "matching_strengths": ["strength 1", "strength 2", "strength 3"],
    "potential_concerns": ["concern 1", "concern 2", "concern 3"],
    "recommendations": ["action 1", "action 2", "action 3"],
    "requirements_met": "X out of Y key requirements satisfied"
}}

SCORING GUIDELINES:
- 90-100: Excellent Match - Exceeds most requirements
- 85-89: Very Strong Match - Meets most requirements with minor gaps  
- 70-84: Good Match - Solid fit with some addressable gaps
- 55-69: Moderate Match - Some relevant experience, significant prep needed
- 40-54: Poor Match - Major qualification gaps
- 1-39: Very Poor Match - Fundamental misalignment

ANALYSIS REQUIREMENTS:
1. Score each component 0-100 based on job requirements
2. Apply exact weights to calculate final score
3. Use specific evidence from resume/profile
4. Provide actionable recommendations
5. Count satisfied vs total requirements
6. Be realistic but constructive

RESPONSE VALIDATION:
- Your response will be parsed as JSON
- Invalid JSON will cause system failure
- Use only plain text in string values
- No special characters that need escaping
- Test your JSON mentally before responding

RESPOND WITH VALID JSON ONLY:
"""
        
        return prompt.strip()
    
    def _get_scoring_weights(self, has_resume: bool) -> str:
        """Get scoring weights explanation based on data availability."""
        if has_resume:
            return """
WEIGHTED SCORING (Resume + Profile = 70/30 split):
1. Skills & Technologies Match (25%): Compare resume skills with job requirements
2. Experience Relevance (20%): Assess how relevant past experience is to this role
3. Years Experience Match (15%): Compare candidate years vs required experience
4. Education & Certifications (10%): Match education level, field, and certifications
5. Profile Skills Cross-check (12%): Verify profile skills align with resume
6. Experience Level Match (8%): Match experience level (entry/mid/senior)
7. Work Arrangement Fit (5%): Match remote/hybrid/onsite preference
8. Location & Salary Alignment (5%): Geographic and compensation fit"""
        else:
            return """
WEIGHTED SCORING (Profile Only = 100%):
1. Skills & Technologies Match (40%): Primary technical/professional fit assessment
2. Experience Level & Years Combined (25%): Seniority and experience duration evaluation
3. Education & Field of Study (15%): Academic background alignment with job requirements
4. Work Preferences Combined (20%): Work arrangement + location + salary preferences"""
    
    def _get_component_instructions(self, has_resume: bool) -> str:
        """Get component scoring instructions."""
        if has_resume:
            return """
- skills_match: How well resume skills align with job requirements (0-100)
- experience_relevance: Relevance of past roles/projects to this position (0-100)
- years_experience: Years of experience vs requirements (0-100)
- education_match: Education level and field alignment (0-100)
- profile_skills_check: Profile skills consistency with resume (0-100)
- experience_level: Experience level match (entry/mid/senior) (0-100)
- work_arrangement: Remote/hybrid/onsite preference alignment (0-100)
- location_salary: Geographic and compensation fit (0-100)"""
        else:
            return """
- skills_technologies: Technical and professional skills match (0-100)
- experience_seniority: Combined experience level and years assessment (0-100)
- education_field: Education level and field of study alignment (0-100)
- work_preferences: Work arrangement, location, and salary fit (0-100)"""
    
    def _get_component_json_keys(self, has_resume: bool) -> str:
        """Get component JSON keys for the output format."""
        if has_resume:
            return '''
        "skills_match": <0-100>,
        "experience_relevance": <0-100>,
        "years_experience": <0-100>,
        "education_match": <0-100>,
        "profile_skills_check": <0-100>,
        "experience_level": <0-100>,
        "work_arrangement": <0-100>,
        "location_salary": <0-100>'''
        else:
            return '''
        "skills_technologies": <0-100>,
        "experience_seniority": <0-100>,
        "education_field": <0-100>,
        "work_preferences": <0-100>'''
    
    def _score_to_status(self, score: int) -> QualificationStatus:
        """
        Convert qualification score to status using enhanced thresholds.
        
        Updated scoring categories:
        - 85-100: Highly Qualified (Excellent/Very Strong match)
        - 70-84: Qualified (Good match)
        - 55-69: Somewhat Qualified (Moderate match)
        - 1-54: Not Qualified (Poor/Very Poor match)
        """
        if score >= 85:
            return QualificationStatus.HIGHLY_QUALIFIED
        elif score >= 70:
            return QualificationStatus.QUALIFIED
        elif score >= 55:
            return QualificationStatus.SOMEWHAT_QUALIFIED
        else:
            return QualificationStatus.NOT_QUALIFIED
    
    def _estimate_tokens(self, request: AnalysisRequest) -> int:
        """
        Estimate tokens for the upcoming request.
        
        Args:
            request: Analysis request
            
        Returns:
            Estimated token count
        """
        # Rough estimation: 4 characters = 1 token
        prompt = self._create_analysis_prompt(request)
        prompt_tokens = len(prompt) // 4
        
        # Add estimated response tokens (Gemini responses are usually 500-2000 tokens)
        estimated_response_tokens = self.ai_settings.max_tokens // 2  # Conservative estimate
        
        total_estimated = prompt_tokens + estimated_response_tokens
        logger.debug(f"🔢 Estimated tokens for '{request.job_title}': {total_estimated}")
        
        return total_estimated

    def _calculate_actual_tokens(self, prompt: str, response: str) -> int:
        """
        Calculate actual tokens used in the request.
        
        Args:
            prompt: The input prompt
            response: The API response
            
        Returns:
            Actual token count
        """
        # Rough calculation: 4 characters = 1 token
        prompt_tokens = len(prompt) // 4
        response_tokens = len(response) // 4
        
        total_tokens = prompt_tokens + response_tokens
        logger.debug(f"📊 Actual tokens used: {total_tokens} (prompt: {prompt_tokens}, response: {response_tokens})")
        
        return total_tokens
    
    def custom_analysis_logic(self, request: AnalysisRequest) -> AnalysisResponse:
        """
        Custom analysis logic that you can implement.
        
        Override this method to implement your own qualification analysis
        instead of using the default AI-based approach.
        
        Args:
            request: Analysis request containing job and user information
            
        Returns:
            Analysis response with qualification assessment
        """
        # Example custom logic - you can replace this with your own implementation
        start_time = time.time()
        
        # Your custom analysis logic here
        # For example, you could use rule-based scoring, keyword matching, etc.
        
        # Placeholder implementation
        score = self._calculate_custom_score(request)
        reasoning = self._generate_custom_reasoning(request)
        
        analysis_duration = time.time() - start_time
        
        return AnalysisResponse(
            qualification_score=score,
            qualification_status=self._score_to_status(score),
            ai_reasoning=reasoning,
            required_experience="Custom analysis",
            education_requirements="Custom analysis",
            key_skills_mentioned=[],
            matching_strengths=[],
            potential_concerns=[],
            ai_model_used="custom_logic",
            analysis_duration=analysis_duration
        )
    
    def _calculate_custom_score(self, request: AnalysisRequest) -> int:
        """
        Calculate qualification score using custom logic.
        
        Implement your own scoring algorithm here.
        """
        # Example: Simple keyword matching
        score = 50  # Base score
        
        job_desc_lower = request.job_description.lower()
        user_skills = [skill.lower() for skill in request.user_profile.additional_skills]
        
        # Add points for matching skills
        for skill in user_skills:
            if skill in job_desc_lower:
                score += 10
        
        # Add points for experience level match
        if request.user_profile.experience_level in job_desc_lower:
            score += 20
        
        return min(100, max(0, score))
    
    def _generate_custom_reasoning(self, request: AnalysisRequest) -> str:
        """
        Generate reasoning using custom logic.
        
        Implement your own reasoning generation here.
        """
        return f"Custom analysis for {request.job_title} at {request.company}"
    
    def get_quota_status(self) -> Dict[str, Any]:
        """
        Get current quota and rate limiting status information.
        
        Returns:
            Dictionary with quota and rate limiting status information
        """
        quota_status = self.quota_manager.get_quota_status()
        rate_limit_status = self.quota_manager.get_rate_limit_status()
        
        return {
            **quota_status,
            **rate_limit_status
        }
    
    def reset_quota_status(self) -> None:
        """
        Manually reset quota status (for testing or emergency use).
        """
        self.quota_manager.reset_quota_status() 