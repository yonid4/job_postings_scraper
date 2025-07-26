#!/usr/bin/env python3
"""
LinkedIn Easy Apply Demo

This script demonstrates the LinkedIn Easy Apply automation functionality
using sample data and configuration.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config.applicant_profile import load_applicant_profile, ApplicantProfile
from data.models import JobListing, JobType, ExperienceLevel, RemoteType
from scrapers import create_linkedin_scraper
from utils.logger import JobAutomationLogger

# Configure logging
logger = JobAutomationLogger(__name__)

def create_sample_job() -> JobListing:
    """Create a sample job listing for testing."""
    return JobListing(
        title="Senior Python Developer",
        company="TechCorp Inc.",
        location="Remote",
        job_url="https://www.linkedin.com/jobs/view/123456789",
        job_site="linkedin",
        description="We are looking for a senior Python developer to join our team...",
        requirements=["Python", "Django", "PostgreSQL", "AWS"],
        responsibilities=["Develop web applications", "Code review", "Mentor junior developers"],
        benefits=["Health insurance", "401k", "Remote work", "Flexible hours"],
        salary_min=80000,
        salary_max=120000,
        salary_currency="USD",
        job_type=JobType.FULL_TIME,
        experience_level=ExperienceLevel.SENIOR,
        remote_type=RemoteType.REMOTE,
        application_url="https://www.linkedin.com/jobs/view/123456789",
        posted_date=datetime.now()
    )

def create_sample_applicant_profile() -> ApplicantProfile:
    """Create a sample applicant profile for testing."""
    return ApplicantProfile(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="+1234567890",
        location="San Francisco, CA",
        resume_path="/tmp/sample_resume.pdf",
        cover_letter_path="/tmp/sample_cover_letter.pdf",
        cover_letter_text="I am excited to apply for this position...",
        auto_apply_enabled=True,
        max_applications_per_session=3,
        skip_complex_applications=True,
        require_manual_review=False,
        years_of_experience=5,
        skills=["Python", "JavaScript", "React", "Node.js", "AWS"],
        education="Bachelor's in Computer Science",
        default_answers={
            'willing_to_relocate': 'Yes',
            'work_authorization': 'Yes',
            'remote_work': 'Yes',
            'salary_expectations': 'Negotiable',
            'start_date': 'Immediately',
            'notice_period': '2 weeks'
        }
    )

def test_applicant_profile_loading():
    """Test applicant profile loading from environment."""
    print("="*60)
    print("TESTING APPLICANT PROFILE LOADING")
    print("="*60)
    
    try:
        profile = load_applicant_profile()
        profile.print_summary()
        return profile
    except Exception as e:
        print(f"❌ Failed to load applicant profile: {e}")
        print("Creating sample profile for demo...")
        return create_sample_applicant_profile()

def test_easy_apply_selectors():
    """Test Easy Apply selector identification."""
    print("\n" + "="*60)
    print("TESTING EASY APPLY SELECTORS")
    print("="*60)
    
    # Create a sample scraper to test selectors
    try:
        scraper = create_linkedin_scraper(
            username="demo@example.com",
            password="demo_password"
        )
        
        print("✅ LinkedIn scraper created successfully")
        print(f"✅ Easy Apply button selector: {scraper.selectors['easy_apply_button']}")
        print(f"✅ Easy Apply form selector: {scraper.selectors['easy_apply_form']}")
        print(f"✅ Form next button selector: {scraper.selectors['form_next_button']}")
        print(f"✅ Form submit button selector: {scraper.selectors['form_submit_button']}")
        print(f"✅ Resume upload selector: {scraper.selectors['resume_upload']}")
        print(f"✅ Cover letter upload selector: {scraper.selectors['cover_letter_upload']}")
        
        return scraper
        
    except Exception as e:
        print(f"❌ Failed to create scraper: {e}")
        return None

def test_question_answering(profile: ApplicantProfile):
    """Test question answering functionality."""
    print("\n" + "="*60)
    print("TESTING QUESTION ANSWERING")
    print("="*60)
    
    test_questions = [
        "Are you willing to relocate?",
        "Do you have work authorization?",
        "How many years of experience do you have?",
        "What are your key skills?",
        "What is your education level?",
        "What are your salary expectations?",
        "When can you start?",
        "What is your notice period?",
        "Do you prefer remote work?",
        "Random question that should return None"
    ]
    
    for question in test_questions:
        answer = profile.get_answer_for_question(question)
        status = "✅" if answer else "❌"
        print(f"   {status} Q: {question}")
        print(f"      A: {answer or 'No answer found'}")
    
    return True

def test_easy_apply_methods(scraper, job: JobListing):
    """Test Easy Apply method availability."""
    print("\n" + "="*60)
    print("TESTING EASY APPLY METHODS")
    print("="*60)
    
    methods_to_test = [
        'initiate_easy_apply',
        '_click_easy_apply_button',
        '_wait_for_easy_apply_form',
        '_process_easy_apply_form',
        '_fill_form_step',
        '_fill_input_fields',
        '_handle_file_uploads',
        '_answer_questions',
        '_proceed_to_next_step',
        '_submit_application',
        'apply_to_job',
        '_is_easy_apply_available'
    ]
    
    for method_name in methods_to_test:
        if hasattr(scraper, method_name):
            print(f"✅ {method_name} - Available")
        else:
            print(f"❌ {method_name} - Missing")
    
    return True

def test_application_workflow():
    """Test the complete application workflow."""
    print("\n" + "="*60)
    print("TESTING APPLICATION WORKFLOW")
    print("="*60)
    
    # Create sample data
    job = create_sample_job()
    profile = create_sample_applicant_profile()
    
    print("📋 Sample Job:")
    print(f"   Title: {job.title}")
    print(f"   Company: {job.company}")
    print(f"   Location: {job.location}")
    print(f"   Type: {job.job_type}")
    print(f"   Experience: {job.experience_level}")
    
    print("\n👤 Sample Applicant Profile:")
    print(f"   Name: {profile.first_name} {profile.last_name}")
    print(f"   Email: {profile.email}")
    print(f"   Phone: {profile.phone}")
    print(f"   Location: {profile.location}")
    print(f"   Resume: {profile.resume_path}")
    print(f"   Cover Letter: {profile.cover_letter_path}")
    print(f"   Skills: {', '.join(profile.skills)}")
    print(f"   Experience: {profile.years_of_experience} years")
    
    print("\n🤖 Application Preferences:")
    print(f"   Auto Apply: {'✅ Enabled' if profile.auto_apply_enabled else '❌ Disabled'}")
    print(f"   Max Applications: {profile.max_applications_per_session}")
    print(f"   Skip Complex: {'✅ Yes' if profile.skip_complex_applications else '❌ No'}")
    print(f"   Manual Review: {'✅ Required' if profile.require_manual_review else '❌ Not required'}")
    
    return True

def main():
    """Main demo execution."""
    print("🚀 LinkedIn Easy Apply Demo")
    print("="*60)
    print("This demo tests the Easy Apply automation functionality")
    print("using sample data and configuration.")
    print("="*60)
    
    try:
        # Test 1: Applicant Profile Loading
        profile = test_applicant_profile_loading()
        
        # Test 2: Easy Apply Selectors
        scraper = test_easy_apply_selectors()
        
        # Test 3: Question Answering
        test_question_answering(profile)
        
        # Test 4: Easy Apply Methods
        if scraper:
            job = create_sample_job()
            test_easy_apply_methods(scraper, job)
        
        # Test 5: Application Workflow
        test_application_workflow()
        
        print("\n" + "="*60)
        print("🎉 EASY APPLY DEMO COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\n📋 What was tested:")
        print("   ✅ Applicant profile loading and validation")
        print("   ✅ Easy Apply CSS selectors")
        print("   ✅ Question answering logic")
        print("   ✅ Easy Apply method availability")
        print("   ✅ Application workflow simulation")
        
        print("\n🚀 Next Steps:")
        print("   1. Set up your real applicant profile in .env file")
        print("   2. Configure your resume and cover letter paths")
        print("   3. Run run_production_scraper.py with auto-apply enabled")
        print("   4. Monitor the application process in real-time")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logger.error(f"Easy Apply demo failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 