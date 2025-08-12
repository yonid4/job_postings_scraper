#!/usr/bin/env python3
"""
Test database saving functionality for new LinkedIn scraper features.
"""

import unittest
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock

from backend.src.data.job_tracker import JobTracker
from backend.src.data.models import JobListing, JobType, ExperienceLevel, RemoteType


class TestDatabaseSaving(unittest.TestCase):
    """Test that new LinkedIn features are properly saved to database."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Create job tracker
        self.job_tracker = JobTracker(self.db_path)
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary database file
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_save_job_listing_with_new_features(self):
        """Test saving a job listing with the new features."""
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
        
        # Save to database
        job_id = self.job_tracker.save_job_listing(job_listing)
        
        # Verify the job was saved
        self.assertEqual(job_id, 'test-job-123')
        
        # Retrieve from database
        retrieved_job = self.job_tracker.get_job_listing('test-job-123')
        
        # Verify all fields are saved correctly
        self.assertIsNotNone(retrieved_job)
        self.assertEqual(retrieved_job.id, 'test-job-123')
        self.assertEqual(retrieved_job.title, 'Software Engineer')
        self.assertEqual(retrieved_job.company, 'Test Company')
        self.assertEqual(retrieved_job.location, 'San Francisco, CA')
        self.assertEqual(retrieved_job.linkedin_url, 'https://linkedin.com/jobs/view/123')
        self.assertEqual(retrieved_job.job_site, 'linkedin')
        self.assertEqual(retrieved_job.description, 'Test job description with improved extraction')
        self.assertEqual(retrieved_job.requirements, ['Python', 'JavaScript'])
        self.assertEqual(retrieved_job.responsibilities, ['Write code', 'Debug issues'])
        self.assertEqual(retrieved_job.benefits, ['Health insurance', '401k'])
        self.assertEqual(retrieved_job.salary_min, 80000)
        self.assertEqual(retrieved_job.salary_max, 120000)
        self.assertEqual(retrieved_job.salary_currency, 'USD')
        self.assertEqual(retrieved_job.job_type, JobType.FULL_TIME)
        self.assertEqual(retrieved_job.experience_level, ExperienceLevel.MID)
        self.assertEqual(retrieved_job.remote_type, RemoteType.REMOTE)
        self.assertEqual(retrieved_job.application_url, 'https://company.com/apply/123')  # Should be saved as job_url in DB
        self.assertEqual(retrieved_job.work_arrangement, 'Remote')  # New field
        self.assertIsNotNone(retrieved_job.posted_date)
        self.assertIsNotNone(retrieved_job.scraped_date)
        self.assertIsNotNone(retrieved_job.last_updated)
    
    def test_save_job_listing_with_null_application_url(self):
        """Test saving a job listing with null application URL (Easy Apply case)."""
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
        
        # Save to database
        job_id = self.job_tracker.save_job_listing(job_listing)
        
        # Retrieve from database
        retrieved_job = self.job_tracker.get_job_listing('test-job-easy-apply')
        
        # Verify null application URL is handled correctly
        self.assertIsNotNone(retrieved_job)
        self.assertIsNone(retrieved_job.application_url)
        self.assertEqual(retrieved_job.work_arrangement, 'Remote')
    
    def test_save_job_listing_with_null_work_arrangement(self):
        """Test saving a job listing with null work arrangement."""
        job_listing = JobListing(
            id='test-job-no-arrangement',
            title='Job Without Work Arrangement',
            company='Test Company',
            location='San Francisco, CA',
            linkedin_url='https://linkedin.com/jobs/view/789',
            job_site='linkedin',
            description='Job without work arrangement info',
            application_url='https://company.com/apply/789',
            work_arrangement=None,  # No work arrangement info
            posted_date=datetime.now(),
            scraped_date=datetime.now(),
            last_updated=datetime.now()
        )
        
        # Save to database
        job_id = self.job_tracker.save_job_listing(job_listing)
        
        # Retrieve from database
        retrieved_job = self.job_tracker.get_job_listing('test-job-no-arrangement')
        
        # Verify null work arrangement is handled correctly
        self.assertIsNotNone(retrieved_job)
        self.assertEqual(retrieved_job.application_url, 'https://company.com/apply/789')
        self.assertIsNone(retrieved_job.work_arrangement)
    
    def test_save_job_listing_with_different_work_arrangements(self):
        """Test saving job listings with different work arrangements."""
        work_arrangements = ['On-site', 'Remote', 'Hybrid']
        
        for i, arrangement in enumerate(work_arrangements):
            job_listing = JobListing(
                id=f'test-job-{i}',
                title=f'Job {i}',
                company='Test Company',
                location='San Francisco, CA',
                linkedin_url=f'https://linkedin.com/jobs/view/{i}',
                job_site='linkedin',
                description=f'Job {i} description',
                application_url=f'https://company.com/apply/{i}',
                work_arrangement=arrangement,
                posted_date=datetime.now(),
                scraped_date=datetime.now(),
                last_updated=datetime.now()
            )
            
            # Save to database
            job_id = self.job_tracker.save_job_listing(job_listing)
            
            # Retrieve from database
            retrieved_job = self.job_tracker.get_job_listing(f'test-job-{i}')
            
            # Verify work arrangement is saved correctly
            self.assertIsNotNone(retrieved_job)
            self.assertEqual(retrieved_job.work_arrangement, arrangement)
    
    def test_database_migration_handles_existing_data(self):
        """Test that database migration handles existing data correctly."""
        # Create a job listing with old schema (if it exists)
        # This test ensures that the migration doesn't break existing data
        
        job_listing = JobListing(
            id='migration-test-job',
            title='Migration Test Job',
            company='Test Company',
            location='San Francisco, CA',
            linkedin_url='https://linkedin.com/jobs/view/migration-test',
            job_site='linkedin',
            description='Test job for migration',
            application_url='https://company.com/apply/migration-test',
            work_arrangement='Hybrid',
            posted_date=datetime.now(),
            scraped_date=datetime.now(),
            last_updated=datetime.now()
        )
        
        # Save to database
        job_id = self.job_tracker.save_job_listing(job_listing)
        
        # Create a new job tracker instance to trigger migration
        new_job_tracker = JobTracker(self.db_path)
        
        # Retrieve the job to ensure migration didn't break it
        retrieved_job = new_job_tracker.get_job_listing('migration-test-job')
        
        # Verify the job is still accessible
        self.assertIsNotNone(retrieved_job)
        self.assertEqual(retrieved_job.id, 'migration-test-job')
        self.assertEqual(retrieved_job.application_url, 'https://company.com/apply/migration-test')
        self.assertEqual(retrieved_job.work_arrangement, 'Hybrid')


if __name__ == '__main__':
    unittest.main() 