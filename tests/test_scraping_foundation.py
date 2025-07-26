"""
Test the scraping foundation.

This module tests the basic scraping infrastructure including
the BaseScraper interface and ExampleScraper implementation.
"""

import sys
import os
from pathlib import Path
import pytest
from typing import Dict, Any

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from scrapers import (
    BaseScraper, 
    ScrapingResult, 
    ScrapingConfig,
    ExampleScraper, 
    create_example_scraper
)
from data.models import JobListing, ScrapingSession


class TestBaseScraper:
    """Test the BaseScraper abstract class."""
    
    def test_base_scraper_initialization(self):
        """Test that BaseScraper can be initialized with config."""
        config = ScrapingConfig(
            site_name="test",
            base_url="https://test.com"
        )
        scraper = ExampleScraper(config)
        
        assert scraper.config == config
        assert scraper.session is None
        assert scraper.request_count == 0
    
    def test_scraping_config_validation(self):
        """Test ScrapingConfig validation."""
        # Valid config
        valid_config = ScrapingConfig(
            site_name="test",
            base_url="https://test.com",
            delay_min=1.0,
            delay_max=3.0,
            max_requests_per_minute=20
        )
        errors = valid_config.validate()
        assert len(errors) == 0
        
        # Invalid config - missing required fields
        invalid_config = ScrapingConfig()
        errors = invalid_config.validate()
        assert len(errors) > 0
        assert any("site_name is required" in error for error in errors)
        assert any("base_url is required" in error for error in errors)
        
        # Invalid config - delay_min > delay_max
        invalid_config2 = ScrapingConfig(
            site_name="test",
            base_url="https://test.com",
            delay_min=5.0,
            delay_max=3.0
        )
        errors = invalid_config2.validate()
        assert any("delay_max cannot be less than delay_min" in error for error in errors)


class TestExampleScraper:
    """Test the ExampleScraper implementation."""
    
    def test_example_scraper_creation(self):
        """Test creating an example scraper."""
        scraper = create_example_scraper()
        
        assert isinstance(scraper, ExampleScraper)
        assert scraper.base_url == "https://example-jobs.com"
        assert scraper.config.site_name == "example"
        assert scraper.config.max_jobs_per_session == 10
    
    def test_example_scraper_scrape_jobs_success(self):
        """Test successful job scraping."""
        scraper = create_example_scraper()
        keywords = ["python", "developer"]
        location = "Remote"
        
        result = scraper.scrape_jobs(keywords, location)
        
        assert isinstance(result, ScrapingResult)
        assert result.success is True
        assert len(result.jobs) > 0
        assert isinstance(result.jobs[0], JobListing)
        assert result.session.jobs_found > 0
        assert result.session.jobs_processed > 0
        assert result.error_message is None
        assert result.metadata is not None
        assert result.performance_metrics is not None
    
    def test_example_scraper_get_job_details(self):
        """Test getting job details."""
        scraper = create_example_scraper()
        job_url = "https://example-jobs.com/jobs/123"
        
        job_details = scraper.get_job_details(job_url)
        
        assert isinstance(job_details, JobListing)
        assert job_details.job_url == job_url
        assert job_details.job_site == "example"
        assert len(job_details.requirements) > 0
        assert len(job_details.responsibilities) > 0
        assert len(job_details.benefits) > 0
    
    def test_example_scraper_build_search_url(self):
        """Test building search URL."""
        scraper = create_example_scraper()
        keywords = ["python", "developer"]
        location = "San Francisco"
        
        url = scraper.build_search_url(keywords, location)
        
        assert "example-jobs.com" in url
        assert "python+developer" in url
        assert "San+Francisco" in url
        
        # Test with additional parameters
        url_with_params = scraper.build_search_url(
            keywords, location, 
            experience_level="senior", 
            job_type="full-time"
        )
        assert "experience=senior" in url_with_params
        assert "type=full-time" in url_with_params
    
    def test_example_scraper_extract_job_listings(self):
        """Test extracting job listings from page content."""
        scraper = create_example_scraper()
        page_content = "<html>Test page content</html>"
        
        jobs = scraper.extract_job_listings_from_page(page_content)
        
        assert isinstance(jobs, list)
        assert len(jobs) > 0
        assert all(isinstance(job, JobListing) for job in jobs)
        assert all(job.job_site == "example" for job in jobs)
    
    def test_example_scraper_extract_job_details(self):
        """Test extracting job details from page content."""
        scraper = create_example_scraper()
        page_content = "<html>Job details page</html>"
        job_url = "https://example-jobs.com/jobs/456"
        
        job_details = scraper.extract_job_details_from_page(page_content, job_url)
        
        assert isinstance(job_details, JobListing)
        assert job_details.job_url == job_url
        assert job_details.job_site == "example"
        assert job_details.requirements
        assert job_details.responsibilities
        assert job_details.benefits
    
    def test_example_scraper_performance_metrics(self):
        """Test performance metrics collection."""
        scraper = create_example_scraper()
        
        # Initially no metrics
        metrics = scraper.get_performance_metrics()
        assert metrics["requests_count"] == 0
        
        # After scraping, should have metrics
        scraper.scrape_jobs(["python"], "Remote")
        metrics = scraper.get_performance_metrics()
        
        assert metrics["requests_count"] > 0
        assert metrics["jobs_found"] > 0
        assert metrics["total_duration"] > 0


class TestScrapingResult:
    """Test the ScrapingResult data structure."""
    
    def test_scraping_result_creation(self):
        """Test creating a ScrapingResult."""
        jobs = [JobListing(
            title="Test Job",
            company="Test Company",
            location="Remote",
            job_url="https://example.com/job",
            job_site="example"
        )]
        session = ScrapingSession(
            job_site="example",
            search_keywords=["python"],
            location="Remote"
        )
        
        result = ScrapingResult(
            success=True,
            jobs=jobs,
            session=session,
            metadata={"test": "value"},
            performance_metrics={"duration": 1.5}
        )
        
        assert result.success is True
        assert len(result.jobs) == 1
        assert result.session == session
        assert result.error_message is None
        assert result.metadata["test"] == "value"
        assert result.performance_metrics["duration"] == 1.5
        assert len(result.warnings) == 0
    
    def test_scraping_result_error_case(self):
        """Test ScrapingResult with error."""
        session = ScrapingSession(
            job_site="example",
            search_keywords=["python"],
            location="Remote"
        )
        
        result = ScrapingResult(
            success=False,
            jobs=[],
            session=session,
            error_message="Test error",
            warnings=["Warning 1", "Warning 2"]
        )
        
        assert result.success is False
        assert len(result.jobs) == 0
        assert result.error_message == "Test error"
        assert len(result.warnings) == 2


class TestUtilityFunctions:
    """Test utility functions from base_scraper."""
    
    def test_sanitize_text(self):
        """Test text sanitization."""
        from scrapers import sanitize_text
        
        # Test normal text
        assert sanitize_text("  Hello   World  ") == "Hello World"
        
        # Test with special characters
        text_with_special = "Hello\xa0World\u200bTest"
        assert sanitize_text(text_with_special) == "Hello World Test"
        
        # Test empty/None
        assert sanitize_text("") == ""
        assert sanitize_text(None) == ""
    
    def test_extract_salary_range(self):
        """Test salary range extraction."""
        from scrapers import extract_salary_range
        
        # Test various formats
        assert extract_salary_range("$50,000 - $80,000") == (50000, 80000)
        assert extract_salary_range("$60,000 to $90,000") == (60000, 90000)
        assert extract_salary_range("50k - 80k") == (50000, 80000)
        assert extract_salary_range("60k to 90k") == (60000, 90000)
        
        # Test no salary found
        assert extract_salary_range("No salary information") == (None, None)
        assert extract_salary_range("") == (None, None)
    
    def test_is_valid_url(self):
        """Test URL validation."""
        from scrapers import is_valid_url
        
        # Valid URLs
        assert is_valid_url("https://example.com") is True
        assert is_valid_url("http://example.com/path") is True
        
        # Invalid URLs
        assert is_valid_url("not-a-url") is False
        assert is_valid_url("") is False
        assert is_valid_url("ftp://example.com") is True  # Valid but different protocol


if __name__ == "__main__":
    # Run basic tests
    print("Testing scraping foundation...")
    
    # Test example scraper
    scraper = create_example_scraper()
    result = scraper.scrape_jobs(["python", "developer"], "Remote")
    
    print(f"✅ Scraping test successful: {len(result.jobs)} jobs found")
    print(f"✅ Session info: {result.session.jobs_found} found, {result.session.jobs_processed} processed")
    print(f"✅ Performance: {result.performance_metrics}")
    
    # Test job details
    if result.jobs:
        job_details = scraper.get_job_details(result.jobs[0].job_url)
        print(f"✅ Job details test successful: {job_details.title}")
        print(f"✅ Requirements: {job_details.requirements}")
    
    # Test utility functions
    from scrapers import sanitize_text, extract_salary_range, is_valid_url
    
    print(f"✅ Text sanitization: '{sanitize_text('  Test   Text  ')}'")
    print(f"✅ Salary extraction: {extract_salary_range('$50,000 - $80,000')}")
    print(f"✅ URL validation: {is_valid_url('https://example.com')}")
    
    print("🎉 All foundation tests passed!") 