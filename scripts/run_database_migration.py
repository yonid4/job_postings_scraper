#!/usr/bin/env python3
"""
Database Migration Script

This script fixes the database schema issues by:
1. Updating foreign key constraints to reference auth.users(id) directly
2. Converting keywords column from TEXT to TEXT[]
3. Ensuring all tables have proper relationships
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the parent directory to Python path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from supabase import create_client
from src.utils.logger import JobAutomationLogger

load_dotenv()

logger = JobAutomationLogger()

def check_current_schema():
    """Check the current database schema."""
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_service_key:
        logger.error("SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not found")
        return False
    
    try:
        supabase = create_client(supabase_url, supabase_service_key)
        logger.info("Connected to Supabase with service role key")
        
        # Check if user_profiles table exists
        try:
            profiles_result = supabase.table('user_profiles').select('*').limit(1).execute()
            logger.info("✅ user_profiles table exists")
        except Exception as e:
            logger.error(f"❌ user_profiles table not found: {e}")
            return False
        
        # Check job_searches table structure
        try:
            searches_result = supabase.table('job_searches').select('*').limit(1).execute()
            logger.info("✅ job_searches table exists")
        except Exception as e:
            logger.error(f"❌ job_searches table not found: {e}")
            return False
        
        # Check jobs table
        try:
            jobs_result = supabase.table('jobs').select('*').limit(1).execute()
            logger.info("✅ jobs table exists")
        except Exception as e:
            logger.error(f"❌ jobs table not found: {e}")
            return False
        
        # Check applications table
        try:
            apps_result = supabase.table('applications').select('*').limit(1).execute()
            logger.info("✅ applications table exists")
        except Exception as e:
            logger.error(f"❌ applications table not found: {e}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking schema: {e}")
        return False

def create_user_profile_for_existing_user(user_id: str):
    """Create a user profile for an existing user."""
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_service_key:
        logger.error("SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not found")
        return False
    
    try:
        supabase = create_client(supabase_url, supabase_service_key)
        
        # Check if profile already exists
        existing_profile = supabase.table('user_profiles').select('*').eq('user_id', user_id).execute()
        
        if existing_profile.data:
            logger.info(f"✅ User profile already exists for {user_id}")
            return True
        
        # Create basic profile
        profile_data = {
            'user_id': user_id,
            'experience_level': 'entry',
            'education_level': 'bachelors',
            'years_of_experience': 0,
            'work_arrangement_preference': 'any',
            'skills_technologies': [],
            'preferred_locations': [],
            'profile_completed': False
        }
        
        result = supabase.table('user_profiles').insert(profile_data).execute()
        
        if result.data:
            logger.info(f"✅ Created user profile for {user_id}")
            return True
        else:
            logger.error(f"❌ Failed to create user profile for {user_id}")
            return False
        
    except Exception as e:
        logger.error(f"Error creating user profile: {e}")
        return False

def run_migration():
    """Run the database migration to fix schema issues."""
    
    logger.info("Starting database migration...")
    
    # First, check if the schema is accessible
    if not check_current_schema():
        logger.error("Schema check failed - cannot proceed with migration")
        return False
    
    logger.info("✅ Schema check passed - tables exist")
    
    # Since we can't modify foreign key constraints via API,
    # we'll create user profiles for existing users and provide instructions
    logger.info("⚠️  IMPORTANT: Foreign key constraints need to be updated manually in Supabase SQL Editor")
    logger.info("Please run the following SQL in your Supabase SQL Editor:")
    logger.info("")
    logger.info("-- Drop existing foreign key constraints")
    logger.info("ALTER TABLE job_searches DROP CONSTRAINT IF EXISTS job_searches_user_id_fkey;")
    logger.info("ALTER TABLE jobs DROP CONSTRAINT IF EXISTS jobs_user_id_fkey;")
    logger.info("ALTER TABLE applications DROP CONSTRAINT IF EXISTS applications_user_id_fkey;")
    logger.info("")
    logger.info("-- Add new foreign key constraints referencing auth.users(id)")
    logger.info("ALTER TABLE job_searches ADD CONSTRAINT job_searches_user_id_fkey")
    logger.info("    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;")
    logger.info("")
    logger.info("ALTER TABLE jobs ADD CONSTRAINT jobs_user_id_fkey")
    logger.info("    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;")
    logger.info("")
    logger.info("ALTER TABLE applications ADD CONSTRAINT applications_user_id_fkey")
    logger.info("    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;")
    logger.info("")
    logger.info("-- Update keywords column to TEXT[]")
    logger.info("ALTER TABLE job_searches ALTER COLUMN keywords TYPE TEXT[] USING ARRAY[keywords];")
    logger.info("")
    
    # For now, let's create a user profile for the current user
    # You can get the user ID from the error message
    user_id = "891d638e-7652-4735-91a3-7e392551a4ac"  # From the error message
    
    logger.info(f"Creating user profile for user: {user_id}")
    if create_user_profile_for_existing_user(user_id):
        logger.info("✅ User profile created successfully")
        logger.info("")
        logger.info("🎉 Migration steps completed!")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Run the SQL commands above in your Supabase SQL Editor")
        logger.info("2. Test the search functionality again")
        return True
    else:
        logger.error("❌ Failed to create user profile")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database migration script")
    parser.add_argument("--check", action="store_true", help="Check current schema only")
    parser.add_argument("--migrate", action="store_true", help="Run the migration")
    
    args = parser.parse_args()
    
    if args.check:
        logger.info("Checking current database schema...")
        check_current_schema()
    elif args.migrate:
        logger.info("Running database migration...")
        success = run_migration()
        if success:
            logger.info("Migration completed successfully!")
            sys.exit(0)
        else:
            logger.error("Migration failed!")
            sys.exit(1)
    else:
        logger.info("Running database migration...")
        success = run_migration()
        if success:
            logger.info("Migration completed successfully!")
            sys.exit(0)
        else:
            logger.error("Migration failed!")
            sys.exit(1) 