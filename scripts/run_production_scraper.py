#!/usr/bin/env python3
"""
Production LinkedIn Job Scraper

This script performs live job extraction from LinkedIn using secure credentials
and provides comprehensive monitoring and reporting.

Usage:
    python3 run_production_scraper.py

Environment Variables Required:
    LINKEDIN_USERNAME: Your LinkedIn email
    LINKEDIN_PASSWORD: Your LinkedIn password
    GOOGLE_SHEETS_CREDENTIALS_PATH: Path to Google Sheets service account JSON
    GOOGLE_SHEETS_SPREADSHEET_ID: Google Sheets spreadsheet ID

Optional Environment Variables:
    MAX_JOBS_PER_SESSION: Maximum jobs to extract (default: 10)
    DELAY_MIN: Minimum delay between actions (default: 3.0)
    DELAY_MAX: Maximum delay between actions (default: 6.0)
    ELEMENT_WAIT_TIMEOUT: Element wait timeout (default: 20)
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config.production_config import load_production_config
from scrapers import create_linkedin_scraper
from data.google_sheets_manager import GoogleSheetsManager
from data.models import JobListing
from scrapers.base_scraper import ScrapingResult
from utils.logger import JobAutomationLogger

# Configure logging
logger = JobAutomationLogger(__name__)

class ProductionScraper:
    """Production scraper with comprehensive monitoring and reporting."""
    
    def __init__(self):
        """Initialize the production scraper."""
        self.config = None
        self.scraper = None
        self.sheets_manager = None
        self.start_time = None
        self.results = {
            'jobs_attempted': 0,
            'jobs_extracted': 0,
            'jobs_written': 0,
            'jobs_failed': 0,
            'applications_attempted': 0,
            'applications_submitted': 0,
            'applications_failed': 0,
            'errors': [],
            'session_duration': 0
        }
    
    def initialize(self) -> bool:
        """Initialize the scraper with production configuration."""
        try:
            print("🚀 Initializing Production LinkedIn Job Scraper...")
            
            # Load production configuration
            self.config = load_production_config()
            self.config.print_summary()
            
            # Initialize LinkedIn scraper
            if not self.config.linkedin:
                raise ValueError("LinkedIn credentials not configured")
            
            self.scraper = create_linkedin_scraper(
                username=self.config.linkedin.username,
                password=self.config.linkedin.password
            )
            
            # Override scraper config with production settings
            self.scraper.config.max_jobs_per_session = self.config.max_jobs_per_session
            self.scraper.config.delay_min = self.config.delay_min
            self.scraper.config.delay_max = self.config.delay_max
            self.scraper.config.element_wait_timeout = self.config.element_wait_timeout
            
            print("✅ LinkedIn scraper initialized successfully")
            
            # Initialize Google Sheets manager if configured
            if self.config.google_sheets:
                self.sheets_manager = GoogleSheetsManager(
                    credentials_path=self.config.google_sheets.credentials_path,
                    spreadsheet_id=self.config.google_sheets.spreadsheet_id
                )
                
                if self.sheets_manager.test_connection():
                    print("✅ Google Sheets manager initialized successfully")
                else:
                    print("⚠️  Google Sheets connection failed - continuing without persistence")
                    self.sheets_manager = None
            else:
                print("⚠️  Google Sheets not configured - data will not be persisted")
            
            # Load applicant profile for auto-apply
            try:
                from config.applicant_profile import load_applicant_profile
                self.applicant_profile = load_applicant_profile()
                self.applicant_profile.print_summary()
            except Exception as e:
                print(f"⚠️  Failed to load applicant profile: {e}")
                self.applicant_profile = None
            
            return True
            
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            logger.error(f"Production scraper initialization failed: {e}")
            return False
    
    def run_job_search(self, keywords: List[str], location: str, **kwargs) -> bool:
        """Run a job search with comprehensive monitoring."""
        try:
            self.start_time = datetime.now()
            print(f"\n🔍 Starting job search...")
            print(f"   Keywords: {', '.join(keywords)}")
            print(f"   Location: {location}")
            print(f"   Max Jobs: {self.config.max_jobs_per_session}")
            print(f"   Additional filters: {kwargs}")
            
            # Perform the search
            result = self.scraper.scrape_jobs(
                keywords=keywords,
                location=location,
                **kwargs
            )
            
            # Process results
            self.process_results(result)
            
            return result.success
            
        except Exception as e:
            error_msg = f"Job search failed: {e}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            self.results['errors'].append(error_msg)
            return False
    
    def process_results(self, result: ScrapingResult) -> None:
        """Process scraping results and write to Google Sheets."""
        try:
            # Update session duration
            self.results['session_duration'] = result.session.total_duration or 0
            
            if result.success and result.jobs:
                print(f"\n📊 Processing {len(result.jobs)} extracted jobs...")
                
                for i, job in enumerate(result.jobs, 1):
                    self.results['jobs_attempted'] += 1
                    
                    try:
                        # Validate job data
                        if self.validate_job(job):
                            self.results['jobs_extracted'] += 1
                            
                            # Write to Google Sheets if available
                            if self.sheets_manager:
                                if self.sheets_manager.write_job_listing(job):
                                    self.results['jobs_written'] += 1
                                    print(f"   ✅ Job {i}: {job.title} at {job.company} - EXTRACTED & WRITTEN")
                                    
                                    # Attempt auto-apply if enabled
                                    if self.applicant_profile and self.applicant_profile.auto_apply_enabled:
                                        if self._attempt_auto_apply(job):
                                            print(f"   🚀 Job {i}: {job.title} at {job.company} - AUTO-APPLIED")
                                        else:
                                            print(f"   ⚠️  Job {i}: {job.title} at {job.company} - AUTO-APPLY FAILED")
                                else:
                                    self.results['jobs_failed'] += 1
                                    print(f"   ⚠️  Job {i}: {job.title} at {job.company} - EXTRACTED but WRITE FAILED")
                            else:
                                print(f"   ✅ Job {i}: {job.title} at {job.company} - EXTRACTED (no persistence)")
                        else:
                            self.results['jobs_failed'] += 1
                            print(f"   ❌ Job {i}: {job.title} at {job.company} - VALIDATION FAILED")
                    
                    except Exception as e:
                        self.results['jobs_failed'] += 1
                        error_msg = f"Job {i} processing failed: {e}"
                        print(f"   ❌ {error_msg}")
                        self.results['errors'].append(error_msg)
                
                print(f"\n📈 Extraction Summary:")
                print(f"   ✅ Successfully extracted: {self.results['jobs_extracted']}")
                print(f"   📊 Written to Google Sheets: {self.results['jobs_written']}")
                print(f"   ❌ Failed: {self.results['jobs_failed']}")
                
            else:
                print(f"❌ No jobs extracted: {result.error_message}")
                self.results['errors'].append(result.error_message or "No jobs found")
            
        except Exception as e:
            error_msg = f"Results processing failed: {e}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            self.results['errors'].append(error_msg)
    
    def validate_job(self, job: JobListing) -> bool:
        """Validate that a job has essential data."""
        essential_fields = [
            job.title and job.title != 'Unknown Title',
            job.company and job.company != 'Unknown Company',
            job.location and job.location != 'Unknown Location',
            job.job_url,
            job.description and len(job.description) > 20
        ]
        
        # Debug: Print what's missing
        if not all(essential_fields):
            print(f"   🔍 Validation failed for: {job.title} at {job.company}")
            if not (job.title and job.title != 'Unknown Title'):
                print(f"      ❌ Title: '{job.title}'")
            if not (job.company and job.company != 'Unknown Company'):
                print(f"      ❌ Company: '{job.company}'")
            if not (job.location and job.location != 'Unknown Location'):
                print(f"      ❌ Location: '{job.location}'")
            if not job.job_url:
                print(f"      ❌ Job URL: '{job.job_url}'")
            if not (job.description and len(job.description) > 20):
                print(f"      ❌ Description: '{job.description[:50]}...' (length: {len(job.description)})")
        
        return all(essential_fields)
    
    def _attempt_auto_apply(self, job: JobListing) -> bool:
        """Attempt to auto-apply to a job using Easy Apply."""
        try:
            self.results['applications_attempted'] += 1
            
            # Check if we've reached the maximum applications
            if self.results['applications_submitted'] >= self.applicant_profile.max_applications_per_session:
                self.logger.logger.info(f"Reached maximum applications per session ({self.applicant_profile.max_applications_per_session})")
                return False
            
            # Attempt to apply using the scraper
            success = self.scraper.apply_to_job(job)
            
            if success:
                self.results['applications_submitted'] += 1
                
                # Create Application record and write to Google Sheets
                if self.sheets_manager:
                    from data.models import Application, ApplicationStatus
                    from datetime import datetime
                    
                    application = Application(
                        job_listing=job,
                        application_date=datetime.now(),
                        application_method='linkedin_easy_apply',
                        status=ApplicationStatus.APPLIED,
                        resume_used=self.applicant_profile.resume_path,
                        cover_letter_used=self.applicant_profile.cover_letter_path if self.applicant_profile.cover_letter_path else None,
                        notes='Auto-applied via LinkedIn Easy Apply'
                    )
                    
                    self.sheets_manager.write_application(application)
                
                return True
            else:
                self.results['applications_failed'] += 1
                return False
                
        except Exception as e:
            self.results['applications_failed'] += 1
            error_msg = f"Auto-apply failed for {job.title}: {e}"
            self.logger.logger.error(error_msg)
            self.results['errors'].append(error_msg)
            return False
    
    def print_final_report(self) -> None:
        """Print comprehensive final report."""
        print("\n" + "="*80)
        print("PRODUCTION SCRAPING SESSION REPORT")
        print("="*80)
        
        # Session summary
        print(f"📅 Session Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Total Duration: {self.results['session_duration']:.2f} seconds")
        
        # Job statistics
        print(f"\n📊 Job Statistics:")
        print(f"   🔍 Jobs Attempted: {self.results['jobs_attempted']}")
        print(f"   ✅ Successfully Extracted: {self.results['jobs_extracted']}")
        print(f"   📝 Written to Google Sheets: {self.results['jobs_written']}")
        print(f"   ❌ Failed: {self.results['jobs_failed']}")
        
        if self.results['jobs_attempted'] > 0:
            extraction_rate = (self.results['jobs_extracted'] / self.results['jobs_attempted']) * 100
            write_rate = (self.results['jobs_written'] / self.results['jobs_extracted']) * 100 if self.results['jobs_extracted'] > 0 else 0
            
            print(f"   📈 Extraction Success Rate: {extraction_rate:.1f}%")
            print(f"   📈 Write Success Rate: {write_rate:.1f}%")
        
        # Application statistics
        if self.results['applications_attempted'] > 0:
            print(f"\n🚀 Application Statistics:")
            print(f"   🔍 Applications Attempted: {self.results['applications_attempted']}")
            print(f"   ✅ Successfully Submitted: {self.results['applications_submitted']}")
            print(f"   ❌ Failed: {self.results['applications_failed']}")
            
            application_rate = (self.results['applications_submitted'] / self.results['applications_attempted']) * 100
            print(f"   📈 Application Success Rate: {application_rate:.1f}%")
        
        # Error summary
        if self.results['errors']:
            print(f"\n⚠️  Errors Encountered ({len(self.results['errors'])}):")
            for i, error in enumerate(self.results['errors'][:5], 1):  # Show first 5 errors
                print(f"   {i}. {error}")
            if len(self.results['errors']) > 5:
                print(f"   ... and {len(self.results['errors']) - 5} more errors")
        else:
            print(f"\n✅ No errors encountered")
        
        # Performance metrics
        if self.results['session_duration'] > 0 and self.results['jobs_extracted'] > 0:
            avg_job_time = self.results['session_duration'] / self.results['jobs_extracted']
            print(f"\n⚡ Performance Metrics:")
            print(f"   🕐 Average Time per Job: {avg_job_time:.2f} seconds")
            print(f"   🚀 Jobs per Minute: {(self.results['jobs_extracted'] / (self.results['session_duration'] / 60)):.1f}")
        
        print("="*80)
    
    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            if self.scraper:
                self.scraper.cleanup()
                print("✅ Scraper cleanup completed")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")

def main():
    """Main production scraper execution."""
    scraper = ProductionScraper()
    
    try:
        # Initialize
        if not scraper.initialize():
            print("❌ Failed to initialize production scraper")
            return 1
        
        # Run job search with production configuration
        success = scraper.run_job_search(
            keywords=scraper.config.default_keywords,
            location=scraper.config.default_location,
            experience_level=scraper.config.default_experience_level,
            job_type=scraper.config.default_job_type
        )
        
        # Print final report
        scraper.print_final_report()
        
        # Return appropriate exit code
        if success and scraper.results['jobs_extracted'] > 0:
            print("\n🎉 Production scraping completed successfully!")
            return 0
        else:
            print("\n⚠️  Production scraping completed with issues")
            return 1
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Production scraping interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Production scraping failed: {e}")
        logger.error(f"Production scraping failed: {e}")
        return 1
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 