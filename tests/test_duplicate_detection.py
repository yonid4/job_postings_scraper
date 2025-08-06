#!/usr/bin/env python3
"""
Test script for duplicate job detection functionality.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.config.config_manager import ConfigurationManager
from src.data.google_sheets_manager import GoogleSheetsManager
from src.data.models import QualificationResult, QualificationStatus, UserDecision
from datetime import datetime

def test_duplicate_detection():
    """Test the duplicate detection functionality."""
    
    try:
        # Initialize configuration
        config_manager = ConfigurationManager()
        api_settings = config_manager.get_api_settings()
        
        if not api_settings.google_sheets_spreadsheet_id:
            print("❌ Google Sheets not configured. Please set up the spreadsheet ID in settings.")
            return
        
        # Initialize Google Sheets manager
        sheets_manager = GoogleSheetsManager(
            credentials_path=api_settings.google_sheets_credentials_path,
            spreadsheet_id=api_settings.google_sheets_spreadsheet_id
        )
        
        # Test data with LinkedIn URLs
        test_job = QualificationResult(
            job_title="Software Engineer",
            company="Test Company",
            linkedin_url="https://www.linkedin.com/jobs/view/1234567890",
            qualification_score=85,
            qualification_status=QualificationStatus.QUALIFIED,
            ai_reasoning="Great match for the position",
            required_experience="2-3 years",
            education_requirements="Bachelor's degree",
            key_skills_mentioned=["Python", "JavaScript"],
            matching_strengths=["Python experience"],
            potential_concerns=["Limited JavaScript experience"],
            user_decision=UserDecision.APPROVED
        )
        
        print("🧪 Testing duplicate detection with LinkedIn URLs...")
        
        # First, check if this job already exists
        is_duplicate = sheets_manager.is_job_duplicate(test_job.job_title, test_job.company, test_job.job_url)
        print(f"   Job '{test_job.job_title}' at '{test_job.company}' is duplicate: {is_duplicate}")
        
        # Try to write the job
        success = sheets_manager.write_qualification_result(test_job)
        print(f"   Write result: {'Success' if success else 'Skipped (duplicate)'}")
        
        # Try to write the same job again
        print("\n🔄 Testing duplicate write...")
        success2 = sheets_manager.write_qualification_result(test_job)
        print(f"   Second write result: {'Success' if success2 else 'Skipped (duplicate)'}")
        
        if not success2:
            print("✅ Duplicate detection working correctly!")
        else:
            print("❌ Duplicate detection failed - job was written twice")
        
        # Test with different job (different LinkedIn URL)
        different_job = QualificationResult(
            job_title="Data Scientist",
            company="Different Company",
            linkedin_url="https://www.linkedin.com/jobs/view/9876543210",
            qualification_score=90,
            qualification_status=QualificationStatus.QUALIFIED,
            ai_reasoning="Excellent match",
            required_experience="3-5 years",
            education_requirements="Master's degree",
            key_skills_mentioned=["Python", "Machine Learning"],
            matching_strengths=["Python experience", "ML background"],
            potential_concerns=["May be overqualified"],
            user_decision=UserDecision.APPROVED
        )
        
        print("\n🧪 Testing different job with different LinkedIn URL...")
        is_duplicate_diff = sheets_manager.is_job_duplicate(different_job.job_title, different_job.company, different_job.job_url)
        print(f"   Job '{different_job.job_title}' at '{different_job.company}' is duplicate: {is_duplicate_diff}")
        
        success3 = sheets_manager.write_qualification_result(different_job)
        print(f"   Write result: {'Success' if success3 else 'Skipped (duplicate)'}")
        
        if success3:
            print("✅ Different job written successfully!")
        else:
            print("❌ Different job was incorrectly flagged as duplicate")
        
        # Test URL normalization with different LinkedIn URL formats
        print("\n🧪 Testing LinkedIn URL normalization...")
        
        # Same job ID but different URL formats
        same_job_different_format = QualificationResult(
            job_title="Software Engineer",
            company="Test Company",
            linkedin_url="https://www.linkedin.com/jobs/view/1234567890?refId=abc123&trackingId=xyz789",
            qualification_score=85,
            qualification_status=QualificationStatus.QUALIFIED,
            ai_reasoning="Great match for the position",
            required_experience="2-3 years",
            education_requirements="Bachelor's degree",
            key_skills_mentioned=["Python", "JavaScript"],
            matching_strengths=["Python experience"],
            potential_concerns=["Limited JavaScript experience"],
            user_decision=UserDecision.APPROVED
        )
        
        is_duplicate_normalized = sheets_manager.is_job_duplicate(
            same_job_different_format.job_title, 
            same_job_different_format.company, 
            same_job_different_format.job_url
        )
        print(f"   Same job with different URL format is duplicate: {is_duplicate_normalized}")
        
        if is_duplicate_normalized:
            print("✅ URL normalization working correctly!")
        else:
            print("❌ URL normalization failed - same job not detected as duplicate")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    test_duplicate_detection() 