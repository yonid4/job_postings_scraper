#!/usr/bin/env python3
"""
Test script for the Job Tracking System.

This script tests all the major functionality of the job tracking system:
- Job search creation and retrieval
- Job application tracking
- Job favorites management
- Job listings storage and search
- Analytics and reporting
"""

import os
import sys
import tempfile
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add the parent directory to Python path to import src modules
parent_dir = Path(__file__).parent
sys.path.insert(0, str(parent_dir))

from backend.src.data.job_tracker import JobTracker
from backend.src.data.models import (
    JobSearch, JobApplication, JobFavorite, JobListing,
    ApplicationStatus, ApplicationMethod, JobType, ExperienceLevel, RemoteType
)
from backend.src.utils.logger import JobAutomationLogger

logger = JobAutomationLogger()


def create_test_job_listing():
    """Create a sample job listing for testing."""
    return JobListing(
        title="Senior Software Engineer",
        company="TechCorp Inc.",
        location="San Francisco, CA",
        job_url="https://example.com/job/123",
        job_site="linkedin",
        description="We are looking for a senior software engineer to join our team...",
        requirements=["Python", "JavaScript", "5+ years experience"],
        responsibilities=["Develop new features", "Code review", "Mentor junior developers"],
        benefits=["Health insurance", "401k", "Remote work"],
        salary_min=120000,
        salary_max=180000,
        job_type=JobType.FULL_TIME,
        experience_level=ExperienceLevel.SENIOR,
        remote_type=RemoteType.HYBRID,
        posted_date=datetime.now() - timedelta(days=5)
    )


def test_job_tracker_initialization():
    """Test job tracker initialization and database creation."""
    print("🧪 Testing Job Tracker Initialization...")
    
    try:
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        # Initialize job tracker
        tracker = JobTracker(db_path)
        print("✅ Job tracker initialized successfully")
        
        # Clean up
        os.unlink(db_path)
        return True
        
    except Exception as e:
        print(f"❌ Job tracker initialization failed: {e}")
        return False


def test_job_search_operations():
    """Test job search creation and retrieval."""
    print("\n🧪 Testing Job Search Operations...")
    
    try:
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        tracker = JobTracker(db_path)
        
        # Create test job search
        search = JobSearch(
            user_id="test_user_123",
            search_name="Software Engineer Search",
            keywords=["software engineer", "python", "javascript"],
            location="San Francisco, CA",
            remote_preference=RemoteType.HYBRID,
            experience_level=ExperienceLevel.SENIOR,
            job_type=JobType.FULL_TIME,
            date_posted_filter=7,
            salary_min=100000,
            salary_max=200000,
            job_sites=["linkedin", "indeed"]
        )
        
        # Save job search
        search_id = tracker.save_job_search(search)
        print(f"✅ Job search saved with ID: {search_id}")
        
        # Retrieve job search
        retrieved_search = tracker.get_job_search(search_id)
        if retrieved_search and retrieved_search.id == search_id:
            print("✅ Job search retrieved successfully")
        else:
            print("❌ Job search retrieval failed")
            return False
        
        # Get user job searches
        user_searches = tracker.get_user_job_searches("test_user_123")
        if len(user_searches) > 0:
            print(f"✅ Retrieved {len(user_searches)} job searches for user")
        else:
            print("❌ No job searches found for user")
            return False
        
        # Clean up
        os.unlink(db_path)
        return True
        
    except Exception as e:
        print(f"❌ Job search operations failed: {e}")
        return False


def test_job_application_operations():
    """Test job application tracking."""
    print("\n🧪 Testing Job Application Operations...")
    
    try:
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        tracker = JobTracker(db_path)
        
        # Create test job listing first
        job = create_test_job_listing()
        job_id = tracker.save_job_listing(job)
        
        # Create test application
        application = JobApplication(
            user_id="test_user_123",
            job_id=job_id,
            applied_date=datetime.now(),
            application_method=ApplicationMethod.LINKEDIN_EASY_APPLY,
            status=ApplicationStatus.APPLIED,
            notes="Applied through LinkedIn Easy Apply",
            cover_letter_used=True
        )
        
        # Save application
        app_id = tracker.save_job_application(application)
        print(f"✅ Job application saved with ID: {app_id}")
        
        # Retrieve application
        retrieved_app = tracker.get_job_application("test_user_123", job_id)
        if retrieved_app and retrieved_app.id == app_id:
            print("✅ Job application retrieved successfully")
        else:
            print("❌ Job application retrieval failed")
            return False
        
        # Update application status
        success = tracker.update_application_status(
            "test_user_123", job_id, 
            ApplicationStatus.INTERVIEWING, 
            "Got a call back!"
        )
        if success:
            print("✅ Application status updated successfully")
        else:
            print("❌ Application status update failed")
            return False
        
        # Get user applications
        user_apps = tracker.get_user_applications("test_user_123")
        if len(user_apps) > 0:
            print(f"✅ Retrieved {len(user_apps)} applications for user")
        else:
            print("❌ No applications found for user")
            return False
        
        # Clean up
        os.unlink(db_path)
        return True
        
    except Exception as e:
        print(f"❌ Job application operations failed: {e}")
        return False


def test_job_favorites_operations():
    """Test job favorites management."""
    print("\n🧪 Testing Job Favorites Operations...")
    
    try:
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        tracker = JobTracker(db_path)
        
        # Create test job listing
        job = create_test_job_listing()
        job_id = tracker.save_job_listing(job)
        
        # Create test favorite
        favorite = JobFavorite(
            user_id="test_user_123",
            job_id=job_id,
            notes="Great opportunity!",
            priority=5
        )
        
        # Add to favorites
        fav_id = tracker.add_job_favorite(favorite)
        print(f"✅ Job added to favorites with ID: {fav_id}")
        
        # Check if favorited
        is_favorited = tracker.is_job_favorited("test_user_123", job_id)
        if is_favorited:
            print("✅ Job favorited status confirmed")
        else:
            print("❌ Job favorited status check failed")
            return False
        
        # Get user favorites
        user_favorites = tracker.get_user_favorites("test_user_123")
        if len(user_favorites) > 0:
            print(f"✅ Retrieved {len(user_favorites)} favorites for user")
        else:
            print("❌ No favorites found for user")
            return False
        
        # Remove from favorites
        success = tracker.remove_job_favorite("test_user_123", job_id)
        if success:
            print("✅ Job removed from favorites successfully")
        else:
            print("❌ Job removal from favorites failed")
            return False
        
        # Verify removal
        is_favorited = tracker.is_job_favorited("test_user_123", job_id)
        if not is_favorited:
            print("✅ Job favorited status correctly updated after removal")
        else:
            print("❌ Job favorited status not updated after removal")
            return False
        
        # Clean up
        os.unlink(db_path)
        return True
        
    except Exception as e:
        print(f"❌ Job favorites operations failed: {e}")
        return False


def test_job_listings_operations():
    """Test job listings storage and search."""
    print("\n🧪 Testing Job Listings Operations...")
    
    try:
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        tracker = JobTracker(db_path)
        
        # Create multiple test job listings
        jobs = [
            JobListing(
                title="Frontend Developer",
                company="WebCorp",
                location="New York, NY",
                job_url="https://example.com/job/1",
                job_site="indeed",
                description="Frontend developer needed...",
                salary_min=80000,
                salary_max=120000,
                job_type=JobType.FULL_TIME
            ),
            JobListing(
                title="Backend Engineer",
                company="DataCorp",
                location="San Francisco, CA",
                job_url="https://example.com/job/2",
                job_site="linkedin",
                description="Backend engineer needed...",
                salary_min=100000,
                salary_max=150000,
                job_type=JobType.FULL_TIME
            ),
            JobListing(
                title="DevOps Engineer",
                company="CloudCorp",
                location="Remote",
                job_url="https://example.com/job/3",
                job_site="glassdoor",
                description="DevOps engineer needed...",
                salary_min=90000,
                salary_max=140000,
                job_type=JobType.FULL_TIME
            )
        ]
        
        # Save all jobs
        job_ids = []
        for job in jobs:
            job_id = tracker.save_job_listing(job)
            job_ids.append(job_id)
            print(f"✅ Job saved: {job.title} at {job.company}")
        
        # Test search with filters
        filters = {"company": "WebCorp"}
        results = tracker.search_job_listings("test_user_123", filters)
        if len(results) == 1 and results[0].company == "WebCorp":
            print("✅ Company filter working correctly")
        else:
            print("❌ Company filter not working correctly")
            return False
        
        # Test location filter
        filters = {"location": "San Francisco"}
        results = tracker.search_job_listings("test_user_123", filters)
        if len(results) == 1 and "San Francisco" in results[0].location:
            print("✅ Location filter working correctly")
        else:
            print("❌ Location filter not working correctly")
            return False
        
        # Test salary filter
        filters = {"salary_min": 95000}
        results = tracker.search_job_listings("test_user_123", filters)
        if len(results) >= 1:
            print("✅ Salary filter working correctly")
        else:
            print("❌ Salary filter not working correctly")
            return False
        
        # Clean up
        os.unlink(db_path)
        return True
        
    except Exception as e:
        print(f"❌ Job listings operations failed: {e}")
        return False


def test_analytics():
    """Test analytics and reporting functionality."""
    print("\n🧪 Testing Analytics...")
    
    try:
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        tracker = JobTracker(db_path)
        
        # Create test job and applications
        job = create_test_job_listing()
        job_id = tracker.save_job_listing(job)
        
        # Create multiple applications with different statuses
        applications = [
            JobApplication(
                user_id="test_user_123",
                job_id=job_id,
                status=ApplicationStatus.APPLIED,
                application_method=ApplicationMethod.MANUAL
            ),
            JobApplication(
                user_id="test_user_123",
                job_id=job_id,
                status=ApplicationStatus.INTERVIEWING,
                application_method=ApplicationMethod.LINKEDIN_EASY_APPLY,
                response_received=True
            ),
            JobApplication(
                user_id="test_user_123",
                job_id=job_id,
                status=ApplicationStatus.REJECTED,
                application_method=ApplicationMethod.EMAIL
            )
        ]
        
        # Save applications
        for app in applications:
            tracker.save_job_application(app)
        
        # Get analytics
        analytics = tracker.get_application_analytics("test_user_123", days=30)
        
        if analytics:
            print("✅ Analytics retrieved successfully")
            print(f"   - Total applications: {analytics.get('total_applications', 0)}")
            print(f"   - Response rate: {analytics.get('response_rate', 0)}%")
            print(f"   - Status counts: {analytics.get('status_counts', {})}")
        else:
            print("❌ Analytics retrieval failed")
            return False
        
        # Clean up
        os.unlink(db_path)
        return True
        
    except Exception as e:
        print(f"❌ Analytics test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Starting Job Tracking System Tests")
    print("=" * 50)
    
    tests = [
        ("Job Tracker Initialization", test_job_tracker_initialization),
        ("Job Search Operations", test_job_search_operations),
        ("Job Application Operations", test_job_application_operations),
        ("Job Favorites Operations", test_job_favorites_operations),
        ("Job Listings Operations", test_job_listings_operations),
        ("Analytics", test_analytics)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The job tracking system is working correctly.")
        print("\n📝 Next steps:")
        print("1. Start the Flask app: python frontend/app.py")
        print("2. Navigate to the Jobs page to test the UI")
        print("3. Try creating job searches and tracking applications")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 