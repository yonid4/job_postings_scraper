"""
Configuration management system for the AI Job Qualification Screening System.

This module provides a centralized way to manage application settings,
including user profiles, AI settings, scraping parameters, and API credentials.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union, List
from dataclasses import dataclass, field
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class UserProfile:
    """Configuration for user qualification profile."""
    
    years_of_experience: int = 0
    has_college_degree: bool = False
    field_of_study: str = ""
    education_details: str = ""
    experience_level: str = "entry"  # entry, junior, mid, senior
    additional_skills: List[str] = field(default_factory=list)
    preferred_locations: List[str] = field(default_factory=list)
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    remote_preference: str = "any"  # remote, on-site, hybrid, any


@dataclass
class AISettings:
    """Configuration for AI qualification analysis."""
    
    api_key: str = ""
    model: str = "gpt-4"
    qualification_threshold: int = 70  # Minimum score (0-100) to consider qualified
    max_tokens: int = 2000
    temperature: float = 0.1
    analysis_timeout: int = 60  # seconds
    retry_attempts: int = 3


@dataclass
class JobCriteria:
    """Configuration for job search criteria."""
    
    keywords: list[str] = field(default_factory=list)
    location: str = ""
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    job_type: list[str] = field(default_factory=list)  # full-time, part-time, contract, etc.
    experience_level: list[str] = field(default_factory=list)  # entry, mid, senior, etc.
    remote_preference: str = "any"  # remote, on-site, hybrid, any


@dataclass
class ScrapingSettings:
    """Configuration for web scraping behavior."""
    
    delay_min: float = 1.0  # Minimum delay between requests (seconds)
    delay_max: float = 3.0  # Maximum delay between requests (seconds)
    max_jobs_per_session: int = 100
    user_agent_rotation: bool = True
    respect_robots_txt: bool = True
    timeout: int = 30  # Request timeout in seconds
    retry_attempts: int = 3

@dataclass
class LinkedInSettings:
    """Configuration for LinkedIn scraping."""
    
    username: str = ""
    password: str = ""
    headless: bool = True
    delay_between_actions: float = 2.0
    max_jobs_per_search: int = 50
    use_date_filtering: bool = True


@dataclass
class SystemSettings:
    """Configuration for system behavior."""
    
    log_level: str = "INFO"
    log_file: str = "logs/job_qualification.log"
    data_directory: str = "data"
    backup_enabled: bool = True
    backup_frequency_hours: int = 24
    debug_mode: bool = False


class ConfigurationManager:
    """
    Manages application configuration with support for JSON files and environment variables.
    
    This class provides a centralized way to access all configuration settings
    throughout the application, with support for loading from files and
    environment variables.
    """
    
    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config_path = config_path or "config/settings.json"
        self.config: Dict[str, Any] = {}
        
        # Load configuration from file and environment
        self._load_configuration()
        self._load_from_environment()
    
    def _load_configuration(self) -> None:
        """Load configuration from JSON file."""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    self.config = json.load(f)
                logger.info(f"Configuration loaded from {self.config_path}")
            else:
                logger.warning(f"Configuration file {self.config_path} not found, using defaults")
                self.config = {}
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self.config = {}
    
    def _load_from_environment(self) -> None:
        """Load configuration from environment variables."""
        # AI Settings
        if os.getenv('GEMINI_API_KEY'):
            if 'ai_settings' not in self.config:
                self.config['ai_settings'] = {}
            self.config['ai_settings']['api_key'] = os.getenv('GEMINI_API_KEY')
        
        # LinkedIn Settings
        if os.getenv('LINKEDIN_USERNAME'):
            if 'linkedin' not in self.config:
                self.config['linkedin'] = {}
            self.config['linkedin']['username'] = os.getenv('LINKEDIN_USERNAME')
        
        if os.getenv('LINKEDIN_PASSWORD'):
            if 'linkedin' not in self.config:
                self.config['linkedin'] = {}
            self.config['linkedin']['password'] = os.getenv('LINKEDIN_PASSWORD')
        

    
    def get_user_profile(self) -> UserProfile:
        """Get user profile configuration."""
        profile_data = self.config.get('user_profile', {})
        return UserProfile(
            years_of_experience=profile_data.get('years_of_experience', 0),
            has_college_degree=profile_data.get('has_college_degree', False),
            field_of_study=profile_data.get('field_of_study', ''),
            education_details=profile_data.get('education_details', ''),
            experience_level=profile_data.get('experience_level', 'entry'),
            additional_skills=profile_data.get('additional_skills', []),
            preferred_locations=profile_data.get('preferred_locations', []),
            salary_min=profile_data.get('salary_min'),
            salary_max=profile_data.get('salary_max'),
            remote_preference=profile_data.get('remote_preference', 'any')
        )
    
    def get_ai_settings(self) -> AISettings:
        """Get AI settings configuration."""
        ai_data = self.config.get('ai_settings', {})
        return AISettings(
            api_key=ai_data.get('api_key', ''),
            model=ai_data.get('model', os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-lite')),
            qualification_threshold=ai_data.get('qualification_threshold', 70),
            max_tokens=ai_data.get('max_tokens', 2000),
            temperature=ai_data.get('temperature', 0.1),
            analysis_timeout=ai_data.get('analysis_timeout', 60),
            retry_attempts=ai_data.get('retry_attempts', 3)
        )
    
    def get_job_criteria(self) -> JobCriteria:
        """Get job search criteria configuration."""
        criteria_data = self.config.get('job_criteria', {})
        return JobCriteria(
            keywords=criteria_data.get('keywords', []),
            location=criteria_data.get('location', ''),
            salary_min=criteria_data.get('salary_min'),
            salary_max=criteria_data.get('salary_max'),
            job_type=criteria_data.get('job_type', []),
            experience_level=criteria_data.get('experience_level', []),
            remote_preference=criteria_data.get('remote_preference', 'any')
        )
    
    def get_scraping_settings(self) -> ScrapingSettings:
        """Get scraping settings configuration."""
        scraping_data = self.config.get('scraping_settings', {})
        return ScrapingSettings(
            delay_min=scraping_data.get('delay_min', 1.0),
            delay_max=scraping_data.get('delay_max', 3.0),
            max_jobs_per_session=scraping_data.get('max_jobs_per_session', 100),
            user_agent_rotation=scraping_data.get('user_agent_rotation', True),
            respect_robots_txt=scraping_data.get('respect_robots_txt', True),
            timeout=scraping_data.get('timeout', 30),
            retry_attempts=scraping_data.get('retry_attempts', 3)
        )
    

    
    def get_linkedin_settings(self) -> LinkedInSettings:
        """Get LinkedIn settings configuration."""
        linkedin_data = self.config.get('linkedin', {})
        
        # Check if credentials are loaded from environment
        username = linkedin_data.get('username', '')
        password = linkedin_data.get('password', '')
        
        if username and password:
            logger.info("LinkedIn credentials loaded from environment variables")
        elif not username and not password:
            logger.warning("LinkedIn credentials not found in environment variables or settings")
        else:
            logger.warning("LinkedIn credentials incomplete - check both username and password")
        
        return LinkedInSettings(
            username=username,
            password=password,
            headless=linkedin_data.get('headless', True),
            delay_between_actions=linkedin_data.get('delay_between_actions', 2.0),
            max_jobs_per_search=linkedin_data.get('max_jobs_per_search', 50),
            use_date_filtering=linkedin_data.get('use_date_filtering', True)
        )
    
    def get_system_settings(self) -> SystemSettings:
        """Get system settings configuration."""
        system_data = self.config.get('system_settings', {})
        return SystemSettings(
            log_level=system_data.get('log_level', 'INFO'),
            log_file=system_data.get('log_file', 'logs/job_qualification.log'),
            data_directory=system_data.get('data_directory', 'data'),
            backup_enabled=system_data.get('backup_enabled', True),
            backup_frequency_hours=system_data.get('backup_frequency_hours', 24),
            debug_mode=system_data.get('debug_mode', False)
        )
    
    def save_configuration(self) -> None:
        """Save current configuration to file."""
        try:
            config_file = Path(self.config_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise ConfigurationError(f"Failed to save configuration: {e}")
    
    def update_configuration(self, section: str, key: str, value: Any) -> None:
        """Update a specific configuration value."""
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section][key] = value
        logger.info(f"Updated configuration: {section}.{key} = {value}")
    
    def update_configuration_section(self, section: str, data: Dict[str, Any]) -> None:
        """Update an entire configuration section with a dictionary of values."""
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section].update(data)
        logger.info(f"Updated configuration section: {section} with {len(data)} values")
    
    def get_raw_config(self) -> Dict[str, Any]:
        """Get the raw configuration dictionary."""
        return self.config.copy()


class ConfigurationError(Exception):
    """Exception raised for configuration-related errors."""
    pass 