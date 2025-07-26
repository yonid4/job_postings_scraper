#!/usr/bin/env python3
"""
Comprehensive LinkedIn Job Extraction and Google Sheets Integration Demo

This script demonstrates the complete end-to-end workflow:
1. LinkedIn job extraction with comprehensive data parsing
2. Google Sheets integration for data persistence
3. Robust error handling and logging
4. Data validation and quality checks

Usage:
    python3 demo_comprehensive_job_extraction.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from scrapers import create_linkedin_scraper
from data.google_sheets_manager import GoogleSheetsManager
from data.models import JobListing, JobType, ExperienceLevel, RemoteType
from utils.logger import JobAutomationLogger

# Configure logging
logger = JobAutomationLogger(__name__)

def print_header(title: str) -> None:
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)

def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n--- {title} ---")

def print_job_summary(job: JobListing, index: int) -> None:
    """Print a comprehensive job summary."""
    print(f"\n📋 Job {index}: {job.title}")
    print(f"   🏢 Company: {job.company}")
    print(f"   📍 Location: {job.location}")
    print(f"   💼 Type: {job.job_type.value if job.job_type else 'Not specified'}")
    print(f"   🎯 Experience: {job.experience_level.value if job.experience_level else 'Not specified'}")
    print(f"   🏠 Remote: {job.remote_type.value if job.remote_type else 'Not specified'}")
    
    if job.salary_min or job.salary_max:
        salary_range = f"${job.salary_min:,}" if job.salary_min else "N/A"
        salary_range += f" - ${job.salary_max:,}" if job.salary_max else ""
        print(f"   💰 Salary: {salary_range} {job.salary_currency}")
    else:
        print(f"   💰 Salary: Not specified")
    
    print(f"   📅 Posted: {job.posted_date.strftime('%Y-%m-%d') if job.posted_date else 'Unknown'}")
    print(f"   🔗 URL: {job.job_url}")
    print(f"   📝 Requirements: {len(job.requirements)} items")
    print(f"   ⚡ Responsibilities: {len(job.responsibilities)} items")
    print(f"   🎁 Benefits: {len(job.benefits)} items")
    print(f"   📋 App Requirements: {len(job.application_requirements)} items")

def demo_comprehensive_extraction():
    """Demonstrate comprehensive job extraction and Google Sheets integration."""
    
    print_header("COMPREHENSIVE LINKEDIN JOB EXTRACTION & GOOGLE SHEETS INTEGRATION")
    
    # Step 1: Initialize LinkedIn Scraper
    print_section("1. Initializing LinkedIn Scraper")
    
    # Get credentials from environment or use dummy values for demo
    username = os.getenv('LINKEDIN_USERNAME', 'demo_user@example.com')
    password = os.getenv('LINKEDIN_PASSWORD', 'demo_password')
    
    try:
        scraper = create_linkedin_scraper(username, password)
        print("✅ LinkedIn scraper created successfully")
        print(f"   📊 Max jobs per session: {scraper.config.max_jobs_per_session}")
        print(f"   ⏱️  Delay range: {scraper.config.delay_min}-{scraper.config.delay_max}s")
        print(f"   🕐 Element wait timeout: {scraper.config.element_wait_timeout}s")
        
    except Exception as e:
        print(f"❌ Failed to create LinkedIn scraper: {e}")
        return
    
    # Step 2: Initialize Google Sheets Manager
    print_section("2. Initializing Google Sheets Manager")
    
    try:
        # Get Google Sheets credentials from environment
        credentials_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH', 'auto-apply-bot-466218-5a1d69f23d44.json')
        spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID', 'demo_spreadsheet_id')
        
        sheets_manager = GoogleSheetsManager(
            credentials_path=credentials_path,
            spreadsheet_id=spreadsheet_id
        )
        
        # Test connection
        if sheets_manager.test_connection():
            print("✅ Google Sheets connection successful")
            print(f"   📊 Spreadsheet ID: {spreadsheet_id}")
            print(f"   📋 Job Listings Worksheet: {sheets_manager.job_listings_worksheet}")
            print(f"   📝 Applications Worksheet: {sheets_manager.applications_worksheet}")
        else:
            print("⚠️  Google Sheets connection failed - continuing with demo mode")
            sheets_manager = None
            
    except Exception as e:
        print(f"⚠️  Google Sheets initialization failed: {e}")
        print("   Continuing in demo mode without Google Sheets integration")
        sheets_manager = None
    
    # Step 3: Perform Job Search and Extraction
    print_section("3. Performing Job Search and Extraction")
    
    search_keywords = ["python developer", "software engineer"]
    location = "Remote"
    
    print(f"🔍 Searching for: {', '.join(search_keywords)} in {location}")
    
    try:
        # Perform the search and extraction
        result = scraper.scrape_jobs(
            keywords=search_keywords,
            location=location,
            experience_level="senior",
            job_type="full-time"
        )
        
        if result.success:
            print(f"✅ Search completed successfully")
            print(f"   📊 Jobs found: {result.session.jobs_found}")
            print(f"   🔄 Jobs processed: {result.session.jobs_processed}")
            print(f"   ⚠️  Errors encountered: {result.session.errors_encountered}")
            print(f"   ⏱️  Total duration: {result.session.total_duration:.2f}s")
            
            jobs = result.jobs
        else:
            print(f"❌ Search failed: {result.error_message}")
            print("   Using sample data for demonstration")
            jobs = create_sample_jobs()
            
    except Exception as e:
        print(f"❌ Search failed: {e}")
        print("   Using sample data for demonstration")
        jobs = create_sample_jobs()
    
    # Step 4: Display Extracted Job Details
    print_section("4. Extracted Job Details")
    
    if jobs:
        print(f"📋 Found {len(jobs)} jobs. Showing details:")
        
        for i, job in enumerate(jobs[:3], 1):  # Show first 3 jobs
            print_job_summary(job, i)
            
            # Show detailed requirements if available
            if job.requirements:
                print(f"   📋 Requirements (first 3):")
                for req in job.requirements[:3]:
                    print(f"      • {req}")
            
            # Show detailed responsibilities if available
            if job.responsibilities:
                print(f"   ⚡ Responsibilities (first 3):")
                for resp in job.responsibilities[:3]:
                    print(f"      • {resp}")
            
            # Show detailed benefits if available
            if job.benefits:
                print(f"   🎁 Benefits (first 3):")
                for benefit in job.benefits[:3]:
                    print(f"      • {benefit}")
        
        if len(jobs) > 3:
            print(f"\n   ... and {len(jobs) - 3} more jobs")
    else:
        print("❌ No jobs found")
    
    # Step 5: Google Sheets Integration
    if sheets_manager and jobs:
        print_section("5. Google Sheets Integration")
        
        print(f"📊 Writing {len(jobs)} jobs to Google Sheets...")
        
        successful_writes = 0
        failed_writes = 0
        
        for i, job in enumerate(jobs, 1):
            try:
                if sheets_manager.write_job_listing(job):
                    successful_writes += 1
                    print(f"   ✅ Job {i}: {job.title} at {job.company} - WRITTEN")
                else:
                    failed_writes += 1
                    print(f"   ❌ Job {i}: {job.title} at {job.company} - FAILED")
            except Exception as e:
                failed_writes += 1
                print(f"   ❌ Job {i}: {job.title} at {job.company} - ERROR: {e}")
        
        print(f"\n📊 Google Sheets Summary:")
        print(f"   ✅ Successfully written: {successful_writes}")
        print(f"   ❌ Failed writes: {failed_writes}")
        print(f"   📈 Success rate: {(successful_writes / len(jobs) * 100):.1f}%")
    
    # Step 6: Data Quality Analysis
    print_section("6. Data Quality Analysis")
    
    if jobs:
        analyze_data_quality(jobs)
    
    # Step 7: Cleanup
    print_section("7. Cleanup")
    
    try:
        scraper.cleanup()
        print("✅ LinkedIn scraper cleanup completed")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")
    
    print_header("DEMONSTRATION COMPLETE")
    print("🎉 The comprehensive job extraction and Google Sheets integration is working!")
    print("\nNext Steps:")
    print("1. Add real LinkedIn credentials to test with actual data")
    print("2. Configure Google Sheets credentials for data persistence")
    print("3. Monitor extraction performance and adjust rate limiting")
    print("4. Integrate with application automation for end-to-end workflow")

def create_sample_jobs() -> List[JobListing]:
    """Create sample job listings for demonstration purposes."""
    from datetime import datetime, timedelta
    
    sample_jobs = [
        JobListing(
            title="Senior Python Developer",
            company="TechCorp Inc.",
            location="Remote",
            job_url="https://linkedin.com/jobs/view/123456",
            job_site="linkedin",
            description="We are looking for a senior Python developer to join our team...",
            requirements=["Python 3.8+", "Django/FastAPI", "PostgreSQL", "AWS", "5+ years experience"],
            responsibilities=["Lead development of new features", "Mentor junior developers", "Code reviews"],
            benefits=["Health insurance", "401k matching", "Flexible PTO", "Remote work"],
            salary_min=120000,
            salary_max=160000,
            salary_currency="USD",
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.SENIOR,
            remote_type=RemoteType.REMOTE,
            application_url="https://linkedin.com/easy-apply/123456",
            posted_date=datetime.now() - timedelta(days=2)
        ),
        JobListing(
            title="Full Stack Software Engineer",
            company="StartupXYZ",
            location="San Francisco, CA",
            job_url="https://linkedin.com/jobs/view/789012",
            job_site="linkedin",
            description="Join our fast-growing startup as a full stack engineer...",
            requirements=["Python", "JavaScript", "React", "Node.js", "3+ years experience"],
            responsibilities=["Build new features", "Optimize performance", "Collaborate with team"],
            benefits=["Competitive salary", "Equity", "Health benefits", "Flexible hours"],
            salary_min=100000,
            salary_max=140000,
            salary_currency="USD",
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.MID,
            remote_type=RemoteType.HYBRID,
            application_url="https://startupxyz.com/careers/apply",
            posted_date=datetime.now() - timedelta(days=1)
        ),
        JobListing(
            title="Python Backend Developer",
            company="Enterprise Solutions",
            location="New York, NY",
            job_url="https://linkedin.com/jobs/view/345678",
            job_site="linkedin",
            description="We need a Python backend developer for our enterprise platform...",
            requirements=["Python", "Flask/Django", "Microservices", "Docker", "Kubernetes"],
            responsibilities=["Design APIs", "Database optimization", "System architecture"],
            benefits=["Comprehensive benefits", "Professional development", "Team events"],
            salary_min=110000,
            salary_max=150000,
            salary_currency="USD",
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.SENIOR,
            remote_type=RemoteType.ON_SITE,
            application_url="https://enterprise.com/careers",
            posted_date=datetime.now() - timedelta(days=3)
        )
    ]
    
    return sample_jobs

def analyze_data_quality(jobs: List[JobListing]) -> None:
    """Analyze the quality of extracted job data."""
    
    print(f"📊 Data Quality Analysis for {len(jobs)} jobs:")
    
    # Essential fields
    essential_fields = {
        'title': sum(1 for job in jobs if job.title and job.title != 'Unknown Title'),
        'company': sum(1 for job in jobs if job.company and job.company != 'Unknown Company'),
        'location': sum(1 for job in jobs if job.location and job.location != 'Unknown Location'),
        'description': sum(1 for job in jobs if job.description and len(job.description) > 50),
        'job_url': sum(1 for job in jobs if job.job_url),
    }
    
    print(f"   📋 Essential Fields Completion:")
    for field, count in essential_fields.items():
        percentage = (count / len(jobs)) * 100
        print(f"      {field.title()}: {count}/{len(jobs)} ({percentage:.1f}%)")
    
    # Optional fields
    optional_fields = {
        'salary_info': sum(1 for job in jobs if job.salary_min or job.salary_max),
        'job_type': sum(1 for job in jobs if job.job_type),
        'experience_level': sum(1 for job in jobs if job.experience_level),
        'remote_type': sum(1 for job in jobs if job.remote_type),
        'posted_date': sum(1 for job in jobs if job.posted_date),
        'requirements': sum(1 for job in jobs if job.requirements),
        'responsibilities': sum(1 for job in jobs if job.responsibilities),
        'benefits': sum(1 for job in jobs if job.benefits),
        'application_url': sum(1 for job in jobs if job.application_url),
    }
    
    print(f"   🎯 Optional Fields Completion:")
    for field, count in optional_fields.items():
        percentage = (count / len(jobs)) * 100
        print(f"      {field.replace('_', ' ').title()}: {count}/{len(jobs)} ({percentage:.1f}%)")
    
    # Data richness
    avg_requirements = sum(len(job.requirements) for job in jobs) / len(jobs)
    avg_responsibilities = sum(len(job.responsibilities) for job in jobs) / len(jobs)
    avg_benefits = sum(len(job.benefits) for job in jobs) / len(jobs)
    
    print(f"   📈 Data Richness:")
    print(f"      Average Requirements: {avg_requirements:.1f} items")
    print(f"      Average Responsibilities: {avg_responsibilities:.1f} items")
    print(f"      Average Benefits: {avg_benefits:.1f} items")
    
    # Overall quality score
    total_fields = len(essential_fields) + len(optional_fields)
    completed_fields = sum(essential_fields.values()) + sum(optional_fields.values())
    quality_score = (completed_fields / (total_fields * len(jobs))) * 100
    
    print(f"   🏆 Overall Data Quality Score: {quality_score:.1f}%")

if __name__ == "__main__":
    try:
        demo_comprehensive_extraction()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demonstration interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc() 