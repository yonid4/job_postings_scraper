"""
Basic tests for the Job Application Automation System.

These tests verify that the core components are working correctly.
"""

import pytest
import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.config.config_manager import ConfigurationManager, JobCriteria, ScrapingSettings
from src.data.models import JobListing, JobApplication, ScrapingSession, ApplicationStatus
from src.utils.logger import setup_logging


class TestConfigurationManager:
    """Test the configuration management system."""
    
    def test_configuration_loading(self):
        """Test that configuration can be loaded successfully."""
        config_manager = ConfigurationManager("config/settings.json")
        
        # Test that we can get configuration sections
        job_criteria = config_manager.get_job_criteria()
        scraping_settings = config_manager.get_scraping_settings()
        
        assert isinstance(job_criteria, JobCriteria)
        assert isinstance(scraping_settings, ScrapingSettings)
        
        # Test that default values are set
        assert isinstance(job_criteria.keywords, list)
        assert isinstance(scraping_settings.delay_min, float)
        assert scraping_settings.delay_min > 0
    
    def test_configuration_defaults(self):
        """Test that default configuration values are correct."""
        config_manager = ConfigurationManager()
        
        job_criteria = config_manager.get_job_criteria()
        scraping_settings = config_manager.get_scraping_settings()
        
        # Test default values
        assert job_criteria.remote_preference == "any"
        assert scraping_settings.retry_attempts == 3
        assert scraping_settings.respect_robots_txt is True


class TestDataModels:
    """Test the data models functionality."""
    
    def test_job_listing_creation(self):
        """Test creating a job listing."""
        job = JobListing(
            title="Software Engineer",
            company="Tech Corp",
            location="San Francisco, CA",
            linkedin_url="https://example.com/job/123",
            job_site="indeed"
        )
        
        assert job.title == "Software Engineer"
        assert job.company == "Tech Corp"
        assert job.job_site == "indeed"
        assert job.id is not None
    
    def test_application_creation(self):
        """Test creating an application record."""
        application = JobApplication(
            job_id="test-job-id",
            user_id="test-user-id",
            application_url="https://example.com/apply/123",
            status=ApplicationStatus.APPLIED
        )
        
        assert application.job_id == "test-job-id"
        assert application.status == ApplicationStatus.APPLIED
        assert application.id is not None
    
    def test_scraping_session(self):
        """Test creating and finishing a scraping session."""
        session = ScrapingSession(
            job_site="indeed",
            search_keywords=["python", "developer"]
        )
        
        # Set some results
        session.jobs_found = 25
        session.jobs_processed = 20
        session.jobs_qualified = 15
        
        # Finish the session
        session.finish()
        
        assert session.completed is True
        assert session.total_duration is not None
        assert session.total_duration > 0
    
    def test_serialization_deserialization(self):
        """Test that data models can be serialized and deserialized."""
        # Create a job listing
        original_job = JobListing(
            title="Test Job",
            company="Test Company",
            location="Test Location",
            linkedin_url="https://example.com/job/test",
            job_site="indeed",
            salary_min=50000,
            salary_max=80000
        )
        
        # Serialize to dictionary
        job_dict = original_job.to_dict()
        
        # Deserialize back to object
        restored_job = JobListing.from_dict(job_dict)
        
        # Verify all fields match
        assert restored_job.title == original_job.title
        assert restored_job.company == original_job.company
        assert restored_job.salary_min == original_job.salary_min
        assert restored_job.salary_max == original_job.salary_max


class TestLogging:
    """Test the logging system."""
    
    def test_logger_setup(self):
        """Test that logging can be set up correctly."""
        logger = setup_logging(name="test_logger", log_level="INFO")
        
        assert logger is not None
        assert logger.name == "test_logger"
        
        # Test that we can log messages
        logger.info("Test log message")
        logger.warning("Test warning message")


def test_system_imports():
    """Test that all system modules can be imported correctly."""
    # Test configuration imports
    from src.config import ConfigurationManager, ConfigurationError
    
    # Test data model imports
    from src.data import JobListing, JobApplication, ScrapingSession
    
    # Test utility imports
    from src.utils import setup_logging, JobAutomationLogger
    
    # If we get here, all imports worked
    assert True


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])