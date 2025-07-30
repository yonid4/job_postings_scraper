#!/usr/bin/env python3
"""
Quick Start Demo for Automatic User Profile Creation System

This script demonstrates the complete system in action, showing:
1. User registration with automatic profile creation
2. Profile management and updates
3. Integration with Supabase Auth
4. Error handling and logging
"""

import os
import sys
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv

# Add the parent directory to Python path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

load_dotenv()

from supabase import create_client, Client
from src.data.auto_profile_manager import AutoProfileManager, ProfileCreationResult
from src.auth.profile_integration import ProfileAuthIntegration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_basic_profile_creation():
    """Demonstrate basic profile creation functionality."""
    print("\n🎯 Demo 1: Basic Profile Creation")
    print("=" * 40)
    
    # Initialize
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not service_role_key:
        print("❌ Missing environment variables!")
        return False
    
    client = create_client(supabase_url, service_role_key)
    profile_manager = AutoProfileManager(client, testing_mode=True)
    
    # Create a test user
    test_email = f"demo_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
    test_password = "demo123456"
    
    print(f"📧 Creating test user: {test_email}")
    
    try:
        auth_response = client.auth.admin.create_user({
            "email": test_email,
            "password": test_password,
            "email_confirm": True
        })
        
        if not auth_response.user:
            print("❌ Failed to create test user")
            return False
        
        user_id = auth_response.user.id
        print(f"✅ User created: {user_id}")
        
        # Wait for trigger to create profile
        print("⏳ Waiting for automatic profile creation...")
        time.sleep(3)
        
        # Check if profile was created
        profile = profile_manager.get_profile(user_id)
        
        if profile:
            print("✅ Profile created automatically!")
            print(f"   Profile ID: {profile['profile_id']}")
            print(f"   Years of Experience: {profile['years_of_experience']}")
            print(f"   Experience Level: {profile['experience_level']}")
            print(f"   Education Level: {profile['education_level']}")
            print(f"   Profile Completed: {profile['profile_completed']}")
        else:
            print("⚠️  Profile not created automatically, creating manually...")
            result = profile_manager.create_profile_automatically(user_id)
            if result.success:
                print("✅ Profile created manually")
            else:
                print(f"❌ Failed to create profile: {result.error_details}")
                return False
        
        # Clean up
        client.auth.admin.delete_user(user_id)
        print("🧹 Test user cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in basic demo: {e}")
        return False


def demo_profile_management():
    """Demonstrate profile management operations."""
    print("\n🎯 Demo 2: Profile Management")
    print("=" * 40)
    
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    client = create_client(supabase_url, service_role_key)
    profile_manager = AutoProfileManager(client, testing_mode=True)
    
    # Create test user
    test_email = f"management_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
    
    try:
        auth_response = client.auth.admin.create_user({
            "email": test_email,
            "password": "demo123456",
            "email_confirm": True
        })
        
        user_id = auth_response.user.id
        print(f"✅ Test user created: {user_id}")
        
        # Wait for profile creation
        time.sleep(3)
        
        # Get initial profile
        profile = profile_manager.get_profile(user_id)
        if not profile:
            print("❌ No profile found")
            return False
        
        print(f"📋 Initial profile:")
        print(f"   Experience: {profile['years_of_experience']} years")
        print(f"   Level: {profile['experience_level']}")
        print(f"   Education: {profile['education_level']}")
        
        # Update profile
        print("\n🔄 Updating profile...")
        updates = {
            "years_of_experience": 5,
            "experience_level": "senior",
            "education_level": "masters",
            "field_of_study": "Computer Science",
            "skills_technologies": ["Python", "JavaScript", "React", "Node.js"],
            "work_arrangement_preference": "hybrid",
            "preferred_locations": ["San Francisco", "New York"],
            "salary_min": 100000,
            "salary_max": 150000
        }
        
        result = profile_manager.update_profile(user_id, updates)
        if result.success:
            print("✅ Profile updated successfully!")
        else:
            print(f"❌ Profile update failed: {result.error_details}")
            return False
        
        # Get updated profile
        updated_profile = profile_manager.get_profile(user_id)
        print(f"\n📋 Updated profile:")
        print(f"   Experience: {updated_profile['years_of_experience']} years")
        print(f"   Level: {updated_profile['experience_level']}")
        print(f"   Education: {updated_profile['education_level']}")
        print(f"   Field: {updated_profile['field_of_study']}")
        print(f"   Skills: {updated_profile['skills_technologies']}")
        print(f"   Work Preference: {updated_profile['work_arrangement_preference']}")
        print(f"   Locations: {updated_profile['preferred_locations']}")
        print(f"   Salary: ${updated_profile['salary_min']:,} - ${updated_profile['salary_max']:,}")
        
        # Check completion status
        is_complete, completion_details = profile_manager.get_profile_completion_status(user_id)
        print(f"\n📊 Profile completion:")
        print(f"   Complete: {is_complete}")
        print(f"   Completion: {completion_details['completion_percentage']}%")
        print(f"   Missing fields: {completion_details['missing_fields']}")
        
        # Clean up
        client.auth.admin.delete_user(user_id)
        print("🧹 Test user cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in management demo: {e}")
        return False


def demo_auth_integration():
    """Demonstrate integration with Supabase Auth."""
    print("\n🎯 Demo 3: Auth Integration")
    print("=" * 40)
    
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    client = create_client(supabase_url, service_role_key)
    integration = ProfileAuthIntegration(client, testing_mode=True)
    
    # Create test user
    test_email = f"integration_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
    
    try:
        auth_response = client.auth.admin.create_user({
            "email": test_email,
            "password": "demo123456",
            "email_confirm": True
        })
        
        user_id = auth_response.user.id
        print(f"✅ Test user created: {user_id}")
        
        # Handle user registration
        user_data = {
            "email": test_email,
            "full_name": "Demo User",
            "registration_source": "demo"
        }
        
        print("🔄 Handling user registration...")
        result = integration.handle_user_registration(user_id, user_data)
        
        if result.success:
            print("✅ User registration handled successfully")
        else:
            print(f"⚠️  Registration handling: {result.message}")
        
        # Verify user profile
        print("🔍 Verifying user profile...")
        has_profile, profile_info = integration.verify_user_profile(user_id)
        
        if has_profile:
            print("✅ Profile verified successfully")
            print(f"   Profile ID: {profile_info['profile_id']}")
            print(f"   Complete: {profile_info['is_complete']}")
            print(f"   Created: {profile_info['created_at']}")
        else:
            print("❌ Profile verification failed")
            return False
        
        # Get complete user data
        print("📊 Getting complete user data...")
        user_data = integration.get_user_profile_data(user_id)
        
        if user_data:
            print("✅ Complete user data retrieved:")
            print(f"   Email: {user_data['email']}")
            print(f"   Email Confirmed: {user_data['email_confirmed']}")
            print(f"   Has Profile: {user_data['has_profile']}")
            print(f"   Profile Complete: {user_data.get('profile_complete', False)}")
            print(f"   Created: {user_data['created_at']}")
        else:
            print("❌ Failed to get complete user data")
            return False
        
        # Get profile statistics
        print("📈 Getting profile statistics...")
        stats = integration.get_profile_statistics()
        print(f"   Total Profiles: {stats.get('total_profiles', 0)}")
        print(f"   Complete Profiles: {stats.get('complete_profiles', 0)}")
        print(f"   Completion Rate: {stats.get('completion_rate', 0)}%")
        
        # Clean up
        client.auth.admin.delete_user(user_id)
        print("🧹 Test user cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in integration demo: {e}")
        return False


def demo_error_handling():
    """Demonstrate error handling capabilities."""
    print("\n🎯 Demo 4: Error Handling")
    print("=" * 40)
    
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    client = create_client(supabase_url, service_role_key)
    profile_manager = AutoProfileManager(client, testing_mode=True)
    
    try:
        # Test with non-existent user
        fake_user_id = "00000000-0000-0000-0000-000000000000"
        
        print("🔍 Testing profile retrieval for non-existent user...")
        profile = profile_manager.get_profile(fake_user_id)
        if profile is None:
            print("✅ Correctly returns None for non-existent user")
        else:
            print("❌ Should return None for non-existent user")
        
        # Test invalid profile data
        print("\n🔍 Testing invalid profile data...")
        
        # Create a real user for this test
        test_email = f"error_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
        auth_response = client.auth.admin.create_user({
            "email": test_email,
            "password": "demo123456",
            "email_confirm": True
        })
        
        user_id = auth_response.user.id
        
        # Create profile
        profile_manager.create_profile_automatically(user_id)
        
        # Test invalid updates
        invalid_updates = {
            "experience_level": "invalid_level",
            "years_of_experience": "not_a_number",
            "salary_min": "invalid_salary"
        }
        
        print("🔄 Testing invalid profile updates...")
        result = profile_manager.update_profile(user_id, invalid_updates)
        
        if not result.success:
            print("✅ Correctly rejected invalid data")
            print(f"   Error: {result.error_details}")
        else:
            print("❌ Should have rejected invalid data")
        
        # Test duplicate profile creation
        print("\n🔄 Testing duplicate profile creation...")
        result = profile_manager.create_profile_automatically(user_id)
        
        if not result.success:
            print("✅ Correctly prevented duplicate profile creation")
            print(f"   Message: {result.message}")
        else:
            print("❌ Should have prevented duplicate profile creation")
        
        # Clean up
        client.auth.admin.delete_user(user_id)
        print("🧹 Test user cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in error handling demo: {e}")
        return False


def main():
    """Run all demos."""
    print("🚀 Automatic User Profile Creation System - Quick Start Demo")
    print("=" * 70)
    print()
    
    # Check environment
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not service_role_key:
        print("❌ Missing required environment variables!")
        print("Please ensure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set")
        return False
    
    print("📋 Environment check:")
    print(f"  SUPABASE_URL: {'✓ Set' if supabase_url else '✗ Missing'}")
    print(f"  SUPABASE_SERVICE_ROLE_KEY: {'✓ Set' if service_role_key else '✗ Missing'}")
    print()
    
    # Run demos
    demos = [
        ("Basic Profile Creation", demo_basic_profile_creation),
        ("Profile Management", demo_profile_management),
        ("Auth Integration", demo_auth_integration),
        ("Error Handling", demo_error_handling)
    ]
    
    results = {}
    
    for demo_name, demo_func in demos:
        try:
            print(f"🎬 Running: {demo_name}")
            result = demo_func()
            results[demo_name] = result
            
            if result:
                print(f"✅ {demo_name} completed successfully")
            else:
                print(f"❌ {demo_name} failed")
            
            print()
            
        except Exception as e:
            print(f"❌ {demo_name} failed with exception: {e}")
            results[demo_name] = False
            print()
    
    # Summary
    print("📊 Demo Results Summary")
    print("=" * 30)
    
    passed = 0
    total = len(results)
    
    for demo_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{demo_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} demos passed")
    
    if passed == total:
        print("\n🎉 All demos passed! Your auto profile system is working correctly.")
        print("\n📝 Next steps:")
        print("   1. Integrate with your frontend registration flow")
        print("   2. Add profile update functionality to your UI")
        print("   3. Implement profile completion tracking")
        print("   4. Set up monitoring and alerts")
    else:
        print(f"\n⚠️  {total - passed} demos failed. Please check the logs above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 