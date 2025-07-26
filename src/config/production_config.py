"""
Production Configuration Management

This module handles secure loading of production credentials and configuration
from environment variables and secure configuration files.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging

# Try to load python-dotenv for .env file support
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class LinkedInCredentials:
    """LinkedIn authentication credentials."""
    username: str
    password: str
    
    @classmethod
    def from_env(cls) -> Optional['LinkedInCredentials']:
        """Load LinkedIn credentials from environment variables."""
        username = os.getenv('LINKEDIN_USERNAME')
        password = os.getenv('LINKEDIN_PASSWORD')
        
        if not username or not password:
            logger.warning("LinkedIn credentials not found in environment variables")
            return None
        
        return cls(username=username, password=password)
    
    def validate(self) -> bool:
        """Validate that credentials are properly set."""
        return bool(self.username and self.password and '@' in self.username)

@dataclass
class GoogleSheetsConfig:
    """Google Sheets configuration."""
    credentials_path: str
    spreadsheet_id: str
    
    @classmethod
    def from_env(cls) -> Optional['GoogleSheetsConfig']:
        """Load Google Sheets config from environment variables."""
        credentials_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH')
        spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
        
        if not credentials_path or not spreadsheet_id:
            logger.warning("Google Sheets configuration not found in environment variables")
            return None
        
        # Validate credentials file exists
        if not os.path.exists(credentials_path):
            logger.error(f"Google Sheets credentials file not found: {credentials_path}")
            return None
        
        return cls(credentials_path=credentials_path, spreadsheet_id=spreadsheet_id)
    
    def validate(self) -> bool:
        """Validate that configuration is properly set."""
        return bool(self.credentials_path and self.spreadsheet_id and os.path.exists(self.credentials_path))

@dataclass
class ProductionConfig:
    """Production configuration for the job automation system."""
    linkedin: Optional[LinkedInCredentials]
    google_sheets: Optional[GoogleSheetsConfig]
    
    # Scraping configuration
    max_jobs_per_session: int = 10  # Conservative default for production
    delay_min: float = 3.0  # Slightly more conservative delays
    delay_max: float = 6.0
    element_wait_timeout: int = 20  # Longer timeout for production
    
    # Search configuration
    default_keywords: list = None
    default_location: str = "Remote"
    default_experience_level: str = "senior"
    default_job_type: str = "full-time"
    
    def __post_init__(self):
        if self.default_keywords is None:
            self.default_keywords = ["python developer", "software engineer"]
    
    @classmethod
    def load(cls) -> 'ProductionConfig':
        """Load production configuration from environment and files."""
        # Load .env file if available
        if DOTENV_AVAILABLE:
            # Look for .env file in project root (2 levels up from src/config/)
            env_path = Path(__file__).parent.parent.parent / '.env'
            if env_path.exists():
                load_dotenv(env_path)
                logger.info(f"Loaded configuration from .env file: {env_path}")
            else:
                logger.info(f"No .env file found at {env_path}, using environment variables only")
        else:
            logger.info("python-dotenv not available, using environment variables only")
        
        # Load credentials
        linkedin = LinkedInCredentials.from_env()
        google_sheets = GoogleSheetsConfig.from_env()
        
        # Override defaults with environment variables if available
        max_jobs = int(os.getenv('MAX_JOBS_PER_SESSION', '10'))
        delay_min = float(os.getenv('DELAY_MIN', '3.0'))
        delay_max = float(os.getenv('DELAY_MAX', '6.0'))
        timeout = int(os.getenv('ELEMENT_WAIT_TIMEOUT', '20'))
        
        return cls(
            linkedin=linkedin,
            google_sheets=google_sheets,
            max_jobs_per_session=max_jobs,
            delay_min=delay_min,
            delay_max=delay_max,
            element_wait_timeout=timeout
        )
    
    def validate(self) -> Dict[str, bool]:
        """Validate all configuration components."""
        validation_results = {
            'linkedin_credentials': self.linkedin.validate() if self.linkedin else False,
            'google_sheets_config': self.google_sheets.validate() if self.google_sheets else False,
            'scraping_config': self.max_jobs_per_session > 0 and self.delay_min > 0 and self.delay_max > self.delay_min
        }
        
        return validation_results
    
    def print_summary(self) -> None:
        """Print a summary of the configuration (without sensitive data)."""
        print("\n" + "="*60)
        print("PRODUCTION CONFIGURATION SUMMARY")
        print("="*60)
        
        # LinkedIn
        if self.linkedin:
            print(f"✅ LinkedIn: Configured (username: {self.linkedin.username.split('@')[0]}@...)")
        else:
            print("❌ LinkedIn: Not configured")
        
        # Google Sheets
        if self.google_sheets:
            print(f"✅ Google Sheets: Configured (spreadsheet: {self.google_sheets.spreadsheet_id[:20]}...)")
        else:
            print("❌ Google Sheets: Not configured")
        
        # Scraping settings
        print(f"📊 Max Jobs per Session: {self.max_jobs_per_session}")
        print(f"⏱️  Delay Range: {self.delay_min}-{self.delay_max}s")
        print(f"🕐 Element Wait Timeout: {self.element_wait_timeout}s")
        
        # Search settings
        print(f"🔍 Default Keywords: {', '.join(self.default_keywords)}")
        print(f"📍 Default Location: {self.default_location}")
        print(f"🎯 Default Experience: {self.default_experience_level}")
        print(f"💼 Default Job Type: {self.default_job_type}")
        
        print("="*60)

def load_production_config() -> ProductionConfig:
    """Load and validate production configuration."""
    config = ProductionConfig.load()
    
    # Validate configuration
    validation = config.validate()
    
    print("\n🔧 Configuration Validation:")
    for component, is_valid in validation.items():
        status = "✅" if is_valid else "❌"
        print(f"   {status} {component.replace('_', ' ').title()}")
    
    # Check if we have minimum required configuration
    if not validation['linkedin_credentials']:
        raise ValueError("LinkedIn credentials are required for production use")
    
    if not validation['google_sheets_config']:
        logger.warning("Google Sheets not configured - data will not be persisted")
    
    return config 