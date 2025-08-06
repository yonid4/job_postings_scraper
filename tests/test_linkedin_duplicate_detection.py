#!/usr/bin/env python3
"""
Test script for LinkedIn URL-based duplicate detection.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.config.config_manager import ConfigurationManager
from src.data.google_sheets_manager import GoogleSheetsManager
from src.data.models import QualificationResult, QualificationStatus, UserDecision
from datetime import datetime

def test_linkedin_url_duplicate_detection():
    """Test LinkedIn URL-based duplicate detection."""
    
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
        
        # Test data with LinkedIn URLs - using unique IDs that haven't been used before
        import random
        import time
        
        # Generate unique job IDs using timestamp and random numbers
        timestamp = int(time.time())
        job1_id = f"{timestamp}001"
        job2_id = f"{timestamp}002" 
        job3_id = f"{timestamp}003"
        job4_id = f"{timestamp}004"
        
        job1 = QualificationResult(
            job_title="Frontend Developer",
            company="WebTech Inc",
            linkedin_url=f"https://www.linkedin.com/jobs/view/{job1_id}",
            qualification_score=85,
            qualification_status=QualificationStatus.QUALIFIED,
            ai_reasoning="Great match for the position",
            required_experience="2-3 years",
            education_requirements="Bachelor's degree",
            key_skills_mentioned=["React", "JavaScript"],
            matching_strengths=["React experience"],
            potential_concerns=["Limited backend experience"],
            user_decision=UserDecision.APPROVED
        )
        
        print("🧪 Testing LinkedIn URL-based duplicate detection with fresh URLs...")
        print(f"   Using unique job IDs: {job1_id}, {job2_id}, {job3_id}, {job4_id}")
        
        # First, check if this job already exists
        is_duplicate1 = sheets_manager.is_job_duplicate(job1.job_title, job1.company, job1.linkedin_url)
        print(f"   Job '{job1.job_title}' at '{job1.company}' is duplicate: {is_duplicate1}")
        
        # Try to write the job
        success1 = sheets_manager.write_qualification_result(job1)
        print(f"   Write result: {'Success' if success1 else 'Skipped (duplicate)'}")
        
        # Try to write the same job again
        print("\n🔄 Testing duplicate write...")
        success2 = sheets_manager.write_qualification_result(job1)
        print(f"   Second write result: {'Success' if success2 else 'Skipped (duplicate)'}")
        
        if not success2:
            print("✅ Duplicate detection working correctly!")
        else:
            print("❌ Duplicate detection failed - job was written twice")
        
        # Test with different job (different LinkedIn URL)
        job3 = QualificationResult(
            job_title="Backend Developer",
            company="ServerCorp",
            linkedin_url=f"https://www.linkedin.com/jobs/view/{job3_id}",
            qualification_score=90,
            qualification_status=QualificationStatus.QUALIFIED,
            ai_reasoning="Excellent match",
            required_experience="3-5 years",
            education_requirements="Bachelor's degree",
            key_skills_mentioned=["Python", "Django"],
            matching_strengths=["Python experience", "Django background"],
            potential_concerns=["May be overqualified"],
            user_decision=UserDecision.APPROVED
        )
        
        print("\n🧪 Testing different job with different LinkedIn URL...")
        is_duplicate3 = sheets_manager.is_job_duplicate(job3.job_title, job3.company, job3.linkedin_url)
        print(f"   Job '{job3.job_title}' at '{job3.company}' is duplicate: {is_duplicate3}")
        
        success3 = sheets_manager.write_qualification_result(job3)
        print(f"   Write result: {'Success' if success3 else 'Skipped (duplicate)'}")
        
        # Test URL normalization with different LinkedIn URL formats
        print("\n🧪 Testing LinkedIn URL normalization...")
        
        # Same job ID but different URL formats
        job2 = QualificationResult(
            job_title="Frontend Developer",
            company="WebTech Inc",
            linkedin_url=f"https://www.linkedin.com/jobs/view/{job1_id}?refId=abc123&trackingId=xyz789",
            qualification_score=85,
            qualification_status=QualificationStatus.QUALIFIED,
            ai_reasoning="Great match for the position",
            required_experience="2-3 years",
            education_requirements="Bachelor's degree",
            key_skills_mentioned=["React", "JavaScript"],
            matching_strengths=["React experience"],
            potential_concerns=["Limited backend experience"],
            user_decision=UserDecision.APPROVED
        )
        
        is_duplicate_normalized = sheets_manager.is_job_duplicate(
            job2.job_title, 
            job2.company, 
            job2.linkedin_url
        )
        print(f"   Same job with different URL format is duplicate: {is_duplicate_normalized}")
        
        success2_normalized = sheets_manager.write_qualification_result(job2)
        print(f"   Write result: {'Success' if success2_normalized else 'Skipped (duplicate)'}")
        
        if is_duplicate_normalized and not success2_normalized:
            print("✅ URL normalization working correctly!")
        else:
            print("❌ URL normalization failed - same job not detected as duplicate")
        
        # Test case 4: Same title and company but different URL (should be new)
        # This tests the scenario where a company posts multiple similar positions
        # Since they have different LinkedIn URLs, they should be treated as separate jobs
        job4 = QualificationResult(
            job_title="Frontend Developer",
            company="WebTech Inc",
            linkedin_url=f"https://www.linkedin.com/jobs/view/{job4_id}",
            qualification_score=80,
            qualification_status=QualificationStatus.QUALIFIED,
            ai_reasoning="Good match",
            required_experience="1-2 years",
            education_requirements="Bachelor's degree",
            key_skills_mentioned=["Vue.js", "CSS"],
            matching_strengths=["Vue.js experience"],
            potential_concerns=["No React experience"],
            user_decision=UserDecision.APPROVED
        )
        
        print(f"\n4️⃣ Testing same title/company but different URL: {job4.linkedin_url}")
        is_duplicate4 = sheets_manager.is_job_duplicate(job4.job_title, job4.company, job4.linkedin_url)
        print(f"   Is duplicate: {is_duplicate4}")
        
        success4 = sheets_manager.write_qualification_result(job4)
        print(f"   Write result: {'Success' if success4 else 'Skipped (duplicate)'}")
        
        # Summary
        print(f"\n📊 Test Summary:")
        print(f"   Job 1 (basic URL): {'✅ Pass' if success1 else '❌ Fail'}")
        print(f"   Job 2 (with params): {'✅ Pass' if not success2_normalized else '❌ Fail'} (should be duplicate)")
        print(f"   Job 3 (different job): {'✅ Pass' if success3 else '❌ Fail'}")
        print(f"   Job 4 (same title/company, diff URL): {'✅ Pass' if success4 else '❌ Fail'} (should be new job)")
        
        # Expected results - now job 4 should be treated as new since it has a different URL
        expected_results = [True, False, True, True]  # success1, success2_normalized, success3, success4
        actual_results = [success1, success2_normalized, success3, success4]
        
        if actual_results == expected_results:
            print(f"\n🎉 All tests passed! LinkedIn URL-only duplicate detection working correctly.")
        else:
            print(f"\n❌ Some tests failed. Expected: {expected_results}, Got: {actual_results}")
            
            # Provide detailed feedback
            if not success4:
                print(f"\n💡 Note: Job 4 was flagged as duplicate, but since it has a different LinkedIn URL,")
                print(f"   it should be treated as a new job (same company can have multiple similar positions).")
                print(f"   This is now fixed with URL-only duplicate detection.")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    test_linkedin_url_duplicate_detection()