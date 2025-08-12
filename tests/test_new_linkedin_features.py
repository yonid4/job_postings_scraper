#!/usr/bin/env python3
"""
Test the three new LinkedIn scraper features:
1. Extract Job Application URL (only for external applications)
2. Extract Work Arrangement Type
3. Improve Job Description Extraction
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from backend.src.scrapers.linkedin_scraper_enhanced import EnhancedLinkedInScraper
from backend.src.scrapers.base_scraper import ScrapingConfig
from backend.src.data.models import JobListing


class TestNewLinkedInFeatures(unittest.TestCase):
    """Test the three new LinkedIn scraper features."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = ScrapingConfig(
            site_name="linkedin",
            base_url="https://www.linkedin.com"
        )
        self.scraper = EnhancedLinkedInScraper(self.config)
        
        # Mock the WebDriver
        self.mock_driver = Mock()
        self.scraper.driver = self.mock_driver
        
        # Mock the logger
        self.mock_logger = Mock()
        self.scraper.logger = self.mock_logger
    
    def test_extract_application_url_from_panel_easy_apply(self):
        """Test that Easy Apply buttons return None."""
        # Mock an Easy Apply button
        mock_button = Mock()
        mock_button.text = "Easy Apply"
        mock_button.get_attribute.return_value = None
        
        self.mock_driver.find_element.return_value = mock_button
        
        result = self.scraper.extract_application_url_from_panel()
        
        self.assertIsNone(result)
        self.mock_driver.find_element.assert_called()
    
    def test_extract_application_url_from_panel_external(self):
        """Test that external Apply buttons return the URL."""
        # Mock an external Apply button
        mock_button = Mock()
        mock_button.text = "Apply"
        mock_button.get_attribute.side_effect = lambda attr: {
            'href': 'https://company.com/apply/123',
            'onclick': None,
            'data-url': None
        }.get(attr)
        
        self.mock_driver.find_element.return_value = mock_button
        
        result = self.scraper.extract_application_url_from_panel()
        
        self.assertEqual(result, 'https://company.com/apply/123')
    
    def test_extract_application_url_from_panel_onclick(self):
        """Test extraction from onclick attribute."""
        # Mock an Apply button with onclick
        mock_button = Mock()
        mock_button.text = "Apply"
        mock_button.get_attribute.side_effect = lambda attr: {
            'href': None,
            'onclick': "window.open('https://company.com/apply/456')",
            'data-url': None
        }.get(attr)
        
        self.mock_driver.find_element.return_value = mock_button
        
        result = self.scraper.extract_application_url_from_panel()
        
        self.assertEqual(result, 'https://company.com/apply/456')
    
    def test_extract_work_arrangement_from_panel_on_site(self):
        """Test extraction of On-site work arrangement."""
        # Mock work arrangement button
        mock_element = Mock()
        mock_element.text = "On-site"
        
        self.mock_driver.find_elements.return_value = [mock_element]
        
        result = self.scraper.extract_work_arrangement_from_panel()
        
        self.assertEqual(result, 'On-site')
    
    def test_extract_work_arrangement_from_panel_remote(self):
        """Test extraction of Remote work arrangement."""
        # Mock work arrangement button
        mock_element = Mock()
        mock_element.text = "Remote"
        
        self.mock_driver.find_elements.return_value = [mock_element]
        
        result = self.scraper.extract_work_arrangement_from_panel()
        
        self.assertEqual(result, 'Remote')
    
    def test_extract_work_arrangement_from_panel_hybrid(self):
        """Test extraction of Hybrid work arrangement."""
        # Mock work arrangement button
        mock_element = Mock()
        mock_element.text = "Hybrid"
        
        self.mock_driver.find_elements.return_value = [mock_element]
        
        result = self.scraper.extract_work_arrangement_from_panel()
        
        self.assertEqual(result, 'Hybrid')
    
    def test_extract_work_arrangement_from_panel_not_found(self):
        """Test when no work arrangement is found."""
        self.mock_driver.find_elements.return_value = []
        
        result = self.scraper.extract_work_arrangement_from_panel()
        
        self.assertIsNone(result)
    
    def test_improve_job_description_extraction_success(self):
        """Test improved job description extraction."""
        # Mock job description element
        mock_element = Mock()
        mock_element.get_attribute.return_value = "<div>Job description content</div>"
        mock_element.text = "Job description content"
        
        self.mock_driver.find_element.return_value = mock_element
        
        result = self.scraper.improve_job_description_extraction()
        
        self.assertEqual(result, "Job description content")
    
    def test_improve_job_description_extraction_fallback(self):
        """Test fallback to basic extraction."""
        # Mock that no elements are found
        self.mock_driver.find_element.side_effect = NoSuchElementException()
        
        # Mock the fallback method
        with patch.object(self.scraper, 'extract_text_from_selector') as mock_fallback:
            mock_fallback.return_value = "Fallback description"
            
            result = self.scraper.improve_job_description_extraction()
            
            self.assertEqual(result, "Fallback description")
    
    def test_job_listing_creation_with_new_fields(self):
        """Test that JobListing is created with new fields."""
        job_data = {
            'job_id': '123',
            'title': 'Software Engineer',
            'company': 'Test Company',
            'location': 'San Francisco, CA',
            'description': 'Test job description',
            'url': 'https://linkedin.com/jobs/view/123',
            'application_url': 'https://company.com/apply/123',
            'work_arrangement': 'Remote',
            'requirements': ['Python', 'JavaScript'],
            'benefits': ['Health insurance', '401k'],
            'responsibilities': ['Write code', 'Debug issues']
        }
        
        # Mock the extraction methods
        with patch.object(self.scraper, 'extract_job_data_from_right_panel') as mock_extract:
            mock_extract.return_value = job_data
            
            # Mock other required methods
            with patch.object(self.scraper, 'click_job_card') as mock_click:
                with patch.object(self.scraper, 'wait_for_right_panel') as mock_wait:
                    mock_click.return_value = True
                    mock_wait.return_value = True
                    
                    # Create a mock job card
                    mock_job_card = Mock()
                    
                    result = self.scraper.extract_job_from_right_panel(mock_job_card)
                    
                    self.assertIsInstance(result, JobListing)
                    self.assertEqual(result.application_url, 'https://company.com/apply/123')
                    self.assertEqual(result.work_arrangement, 'Remote')
    
    def test_job_listing_model_serialization(self):
        """Test that JobListing can be serialized with new fields."""
        job_listing = JobListing(
            id='123',
            title='Software Engineer',
            company='Test Company',
            location='San Francisco, CA',
            description='Test description',
            linkedin_url='https://linkedin.com/jobs/view/123',
            application_url='https://company.com/apply/123',
            work_arrangement='Remote',
            requirements=['Python'],
            benefits=['Health insurance'],
            responsibilities=['Write code']
        )
        
        # Test to_dict
        job_dict = job_listing.to_dict()
        
        self.assertEqual(job_dict['application_url'], 'https://company.com/apply/123')
        self.assertEqual(job_dict['work_arrangement'], 'Remote')
        
        # Test from_dict
        new_job = JobListing.from_dict(job_dict)
        
        self.assertEqual(new_job.application_url, 'https://company.com/apply/123')
        self.assertEqual(new_job.work_arrangement, 'Remote')


if __name__ == '__main__':
    unittest.main() 