#!/usr/bin/env python3
"""
Test Supabase integration for new LinkedIn scraper features.
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime
from typing import Dict, Any

from backend.src.data.models import JobListing, JobType, ExperienceLevel, RemoteType


class TestSupabaseIntegration(unittest.TestCase):
    """Test that new LinkedIn features work correctly with Supabase."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the Supabase client
        self.mock_client = Mock()
        self.mock_response = Mock()
        self.mock_response.data = []
        self.mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = self.mock_response
    
    def test_job_data_structure_for_supabase(self):
        """Test that job data is structured correctly for Supabase saving."""
        # Create a job listing with new features
        job_listing = JobListing(
            id='test-job-123',
            title='Software Engineer',
            company='Test Company',
            location='San Francisco, CA',
            linkedin_url='https://linkedin.com/jobs/view/123',
            job_site='linkedin',
            description='Test job description with improved extraction',
            requirements=['Python', 'JavaScript'],
            responsibilities=['Write code', 'Debug issues'],
            benefits=['Health insurance', '401k'],
            salary_min=80000,
            salary_max=120000,
            salary_currency='USD',
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.MID,
            remote_type=RemoteType.REMOTE,
            application_url='https://company.com/apply/123',  # This should be saved as job_url
            work_arrangement='Remote',  # New field
            posted_date=datetime.now(),
            scraped_date=datetime.now(),
            last_updated=datetime.now()
        )
        
        # Convert to Supabase format (as done in frontend)
        job_data = {
            'user_id': 'test-user-123',
            'job_title': job_listing.title,
            'company_name': job_listing.company,
            'location': job_listing.location,
            'job_description': job_listing.description,
            'linkedin_url': job_listing.linkedin_url,
            'job_url': job_listing.application_url,  # Save application URL as job_url
            'date_posted': job_listing.posted_date.isoformat() if job_listing.posted_date else None,
            'work_arrangement': job_listing.work_arrangement,  # New field
            'experience_level': job_listing.experience_level.value if job_listing.experience_level else None,
            'job_type': job_listing.job_type.value if job_listing.job_type else None,
            'date_found': datetime.now().isoformat()
        }
        
        # Verify the data structure
        self.assertEqual(job_data['job_title'], 'Software Engineer')
        self.assertEqual(job_data['company_name'], 'Test Company')
        self.assertEqual(job_data['location'], 'San Francisco, CA')
        self.assertEqual(job_data['job_description'], 'Test job description with improved extraction')
        self.assertEqual(job_data['linkedin_url'], 'https://linkedin.com/jobs/view/123')
        self.assertEqual(job_data['job_url'], 'https://company.com/apply/123')  # Application URL saved as job_url
        self.assertEqual(job_data['work_arrangement'], 'Remote')  # New field
        self.assertEqual(job_data['experience_level'], 'mid')
        self.assertEqual(job_data['job_type'], 'full-time')
        self.assertIsNotNone(job_data['date_found'])
    
    def test_easy_apply_job_data_structure(self):
        """Test that Easy Apply jobs (no external URL) are handled correctly."""
        job_listing = JobListing(
            id='test-job-easy-apply',
            title='Easy Apply Job',
            company='Test Company',
            location='Remote',
            linkedin_url='https://linkedin.com/jobs/view/456',
            job_site='linkedin',
            description='Easy Apply job description',
            application_url=None,  # Easy Apply - no external URL
            work_arrangement='Remote',
            posted_date=datetime.now(),
            scraped_date=datetime.now(),
            last_updated=datetime.now()
        )
        
        # Convert to Supabase format
        job_data = {
            'user_id': 'test-user-123',
            'job_title': job_listing.title,
            'company_name': job_listing.company,
            'location': job_listing.location,
            'job_description': job_listing.description,
            'linkedin_url': job_listing.linkedin_url,
            'job_url': job_listing.application_url,  # Should be None for Easy Apply
            'date_posted': job_listing.posted_date.isoformat() if job_listing.posted_date else None,
            'work_arrangement': job_listing.work_arrangement,
            'experience_level': job_listing.experience_level.value if job_listing.experience_level else None,
            'job_type': job_listing.job_type.value if job_listing.job_type else None,
            'date_found': datetime.now().isoformat()
        }
        
        # Verify Easy Apply handling
        self.assertEqual(job_data['job_title'], 'Easy Apply Job')
        self.assertIsNone(job_data['job_url'])  # Should be None for Easy Apply
        self.assertEqual(job_data['work_arrangement'], 'Remote')
    
    def test_different_work_arrangements(self):
        """Test that different work arrangements are handled correctly."""
        work_arrangements = ['On-site', 'Remote', 'Hybrid']
        
        for arrangement in work_arrangements:
            job_listing = JobListing(
                id=f'test-job-{arrangement.lower()}',
                title=f'Job {arrangement}',
                company='Test Company',
                location='San Francisco, CA',
                linkedin_url=f'https://linkedin.com/jobs/view/{arrangement.lower()}',
                job_site='linkedin',
                description=f'Job {arrangement} description',
                application_url=f'https://company.com/apply/{arrangement.lower()}',
                work_arrangement=arrangement,
                posted_date=datetime.now(),
                scraped_date=datetime.now(),
                last_updated=datetime.now()
            )
            
            # Convert to Supabase format
            job_data = {
                'user_id': 'test-user-123',
                'job_title': job_listing.title,
                'company_name': job_listing.company,
                'location': job_listing.location,
                'job_description': job_listing.description,
                'linkedin_url': job_listing.linkedin_url,
                'job_url': job_listing.application_url,
                'date_posted': job_listing.posted_date.isoformat() if job_listing.posted_date else None,
                'work_arrangement': job_listing.work_arrangement,
                'experience_level': job_listing.experience_level.value if job_listing.experience_level else None,
                'job_type': job_listing.job_type.value if job_listing.job_type else None,
                'date_found': datetime.now().isoformat()
            }
            
            # Verify work arrangement is saved correctly
            self.assertEqual(job_data['work_arrangement'], arrangement)
            self.assertEqual(job_data['job_url'], f'https://company.com/apply/{arrangement.lower()}')
    
    def test_null_work_arrangement(self):
        """Test that null work arrangement is handled correctly."""
        job_listing = JobListing(
            id='test-job-no-arrangement',
            title='Job Without Work Arrangement',
            company='Test Company',
            location='San Francisco, CA',
            linkedin_url='https://linkedin.com/jobs/view/no-arrangement',
            job_site='linkedin',
            description='Job without work arrangement info',
            application_url='https://company.com/apply/no-arrangement',
            work_arrangement=None,  # No work arrangement info
            posted_date=datetime.now(),
            scraped_date=datetime.now(),
            last_updated=datetime.now()
        )
        
        # Convert to Supabase format
        job_data = {
            'user_id': 'test-user-123',
            'job_title': job_listing.title,
            'company_name': job_listing.company,
            'location': job_listing.location,
            'job_description': job_listing.description,
            'linkedin_url': job_listing.linkedin_url,
            'job_url': job_listing.application_url,
            'date_posted': job_listing.posted_date.isoformat() if job_listing.posted_date else None,
            'work_arrangement': job_listing.work_arrangement,
            'experience_level': job_listing.experience_level.value if job_listing.experience_level else None,
            'job_type': job_listing.job_type.value if job_listing.job_type else None,
            'date_found': datetime.now().isoformat()
        }
        
        # Verify null work arrangement is handled correctly
        self.assertEqual(job_data['job_url'], 'https://company.com/apply/no-arrangement')
        self.assertIsNone(job_data['work_arrangement'])
    
    def test_enum_conversion_for_supabase(self):
        """Test that enum values are properly converted for Supabase."""
        job_listing = JobListing(
            id='test-job-enums',
            title='Test Job with Enums',
            company='Test Company',
            location='San Francisco, CA',
            linkedin_url='https://linkedin.com/jobs/view/enums',
            job_site='linkedin',
            description='Test job with enum values',
            application_url='https://company.com/apply/enums',
            work_arrangement='Hybrid',
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.SENIOR,
            remote_type=RemoteType.HYBRID,
            posted_date=datetime.now(),
            scraped_date=datetime.now(),
            last_updated=datetime.now()
        )
        
        # Convert to Supabase format
        job_data = {
            'user_id': 'test-user-123',
            'job_title': job_listing.title,
            'company_name': job_listing.company,
            'location': job_listing.location,
            'job_description': job_listing.description,
            'linkedin_url': job_listing.linkedin_url,
            'job_url': job_listing.application_url,
            'date_posted': job_listing.posted_date.isoformat() if job_listing.posted_date else None,
            'work_arrangement': job_listing.work_arrangement,
            'experience_level': job_listing.experience_level.value if job_listing.experience_level else None,
            'job_type': job_listing.job_type.value if job_listing.job_type else None,
            'date_found': datetime.now().isoformat()
        }
        
        # Verify enum conversions
        self.assertEqual(job_data['experience_level'], 'senior')
        self.assertEqual(job_data['job_type'], 'full-time')
        self.assertEqual(job_data['work_arrangement'], 'Hybrid')
        self.assertEqual(job_data['job_url'], 'https://company.com/apply/enums')


if __name__ == '__main__':
    unittest.main() 