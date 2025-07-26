#!/usr/bin/env python3
"""
Test script for Google Sheets integration.

This script demonstrates how to use the GoogleSheetsManager class
to write job application data to Google Sheets.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.data.google_sheets_manager import GoogleSheetsManager
from src.data.models import JobListing, Application, ApplicationStatus, JobType, ExperienceLevel, RemoteType
from src.utils.logger import setup_logging


def test_google_sheets_integration():
    """Test the Google Sheets integration functionality."""
    print("🧪 Testing Google Sheets Integration")
    print("=" * 50)
    
    # Set up logging
    logger = setup_logging(name="google_sheets_test", log_level="INFO")
    
    try:
        # Initialize Google Sheets manager
        print("📋 Initializing Google Sheets Manager...")
        sheets_manager = GoogleSheetsManager()
        
        # Test connection
        print("🔗 Testing connection...")
        if sheets_manager.test_connection():
            print("✅ Connection successful!")
        else:
            print("❌ Connection failed!")
            return
        
        # Create sample job listing
        print("\n📝 Creating sample job listing...")
        job_listing = JobListing(
            title="Senior Python Developer",
            company="Tech Innovations Inc",
            location="San Francisco, CA",
            job_url="https://example.com/job/senior-python-dev",
            job_site="indeed",
            description="We are looking for a talented Senior Python Developer to join our team...",
            requirements=["Python", "Django", "PostgreSQL", "AWS"],
            responsibilities=["Develop web applications", "Code review", "Mentor junior developers"],
            benefits=["Health insurance", "401k", "Remote work"],
            salary_min=120000,
            salary_max=160000,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.SENIOR,
            remote_type=RemoteType.HYBRID
        )
        
        # Write job listing to Google Sheets
        print("📊 Writing job listing to Google Sheets...")
        if sheets_manager.write_job_listing(job_listing):
            print("✅ Job listing written successfully!")
        else:
            print("❌ Failed to write job listing!")
        
        # Create sample application
        print("\n📝 Creating sample application...")
        application = Application(
            job_id=job_listing.id,
            job_title=job_listing.title,
            company=job_listing.company,
            job_url=job_listing.job_url,
            application_url="https://example.com/apply/senior-python-dev",
            status=ApplicationStatus.APPLIED,
            application_method="automated",
            resume_used="resume_senior_python.pdf",
            cover_letter_used="cover_letter_senior_python.txt",
            cover_letter_type="customized",
            tags=["python", "senior", "full-time"],
            priority=3
        )
        
        # Write application to Google Sheets
        print("📊 Writing application to Google Sheets...")
        if sheets_manager.write_application(application):
            print("✅ Application written successfully!")
        else:
            print("❌ Failed to write application!")
        
        # Test updating application status
        print("\n🔄 Testing status update...")
        if sheets_manager.update_application_status(
            application.id,
            ApplicationStatus.INTERVIEW_SCHEDULED,
            Response_Received="Yes",
            Response_Type="Interview Scheduled"
        ):
            print("✅ Status updated successfully!")
        else:
            print("❌ Failed to update status!")
        
        # Test retrieving applications
        print("\n📖 Testing application retrieval...")
        applications = sheets_manager.get_applications(limit=5)
        print(f"✅ Retrieved {len(applications)} applications from Google Sheets")
        
        if applications:
            print("Sample application data:")
            for i, app in enumerate(applications[:2], 1):
                print(f"  {i}. {app.get('Job Title', 'N/A')} at {app.get('Company', 'N/A')}")
        
        print("\n🎉 Google Sheets integration test completed successfully!")
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\n📋 Setup Instructions:")
        print("1. Create a .env file in the project root with:")
        print("   GOOGLE_SHEETS_CREDENTIALS_PATH=path/to/your/credentials.json")
        print("   GOOGLE_SHEETS_SPREADSHEET_ID=your-spreadsheet-id")
        print("2. Ensure your credentials file exists and is valid")
        print("3. Make sure your Google Sheet is shared with the service account email")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logger.error(f"Test failed: {e}", exc_info=True)


def create_env_template():
    """Create a template .env file."""
    env_content = """# Google Sheets API Configuration
GOOGLE_SHEETS_CREDENTIALS_PATH=path/to/your/credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=your-spreadsheet-id-here

# Email Configuration (optional)
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# System Configuration
LOG_LEVEL=INFO
DEBUG_MODE=false
"""
    
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, "w") as f:
            f.write(env_content)
        print("✅ Created .env template file")
        print("📝 Please update the .env file with your actual credentials")
    else:
        print("ℹ️  .env file already exists")


if __name__ == "__main__":
    print("Google Sheets Integration Test")
    print("=" * 40)
    
    # Check if .env file exists
    if not Path(".env").exists():
        print("⚠️  No .env file found. Creating template...")
        create_env_template()
        print("\nPlease update the .env file with your credentials and run again.")
        sys.exit(1)
    
    # Run the test
    test_google_sheets_integration() 