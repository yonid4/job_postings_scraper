#!/usr/bin/env python3
"""
Database migration script for LinkedIn scraper new features.

This script handles the migration of existing databases to support:
1. Adding work_arrangement field to job_listings table
2. Renaming application_url to job_url in job_listings table
3. Creating qualification_results table for AI analysis results
"""

import sqlite3
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def migrate_database(db_path: str) -> bool:
    """
    Migrate the database to support new LinkedIn scraper features.
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        True if migration was successful, False otherwise
    """
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if job_listings table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='job_listings'
            """)
            
            if not cursor.fetchone():
                logger.info("job_listings table doesn't exist, no migration needed")
                return True
            
            # Check current table structure
            cursor.execute("PRAGMA table_info(job_listings)")
            columns = {row[1] for row in cursor.fetchall()}
            
            # Migration 1: Rename application_url to job_url if needed
            if 'application_url' in columns and 'job_url' not in columns:
                logger.info("Migrating: Renaming application_url to job_url")
                cursor.execute("""
                    ALTER TABLE job_listings 
                    RENAME COLUMN application_url TO job_url
                """)
                logger.info("✅ Successfully renamed application_url to job_url")
            
            # Migration 2: Add work_arrangement column if needed
            if 'work_arrangement' not in columns:
                logger.info("Migrating: Adding work_arrangement column")
                cursor.execute("""
                    ALTER TABLE job_listings 
                    ADD COLUMN work_arrangement TEXT
                """)
                logger.info("✅ Successfully added work_arrangement column")
            

            
            conn.commit()
            logger.info("✅ Database migration completed successfully")
            return True
            
    except Exception as e:
        logger.error(f"❌ Database migration failed: {e}")
        return False


def verify_migration(db_path: str) -> bool:
    """
    Verify that the database migration was successful.
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        True if migration is verified, False otherwise
    """
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if job_listings table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='job_listings'
            """)
            
            if not cursor.fetchone():
                logger.warning("job_listings table doesn't exist")
                return False
            
            # Check table structure
            cursor.execute("PRAGMA table_info(job_listings)")
            columns = {row[1] for row in cursor.fetchall()}
            
            # Verify required columns exist
            required_columns = {
                'id', 'title', 'company', 'location', 'linkedin_url', 
                'job_site', 'description', 'requirements', 'responsibilities', 
                'benefits', 'salary_min', 'salary_max', 'salary_currency', 
                'job_type', 'experience_level', 'remote_type', 'job_url', 
                'application_deadline', 'application_requirements', 'work_arrangement',
                'posted_date', 'scraped_date', 'last_updated', 'is_duplicate', 
                'duplicate_of', 'notes', 'created_at'
            }
            
            missing_columns = required_columns - columns
            if missing_columns:
                logger.error(f"❌ Missing required columns: {missing_columns}")
                return False
            
            # Check for old column names that should not exist
            old_columns = {'application_url'}  # This should be renamed to job_url
            old_columns_found = old_columns & columns
            if old_columns_found:
                logger.error(f"❌ Found old column names that should be renamed: {old_columns_found}")
                return False
            
            logger.info("✅ Database migration verification passed")
            return True
            
    except Exception as e:
        logger.error(f"❌ Database migration verification failed: {e}")
        return False


def run_migration(db_path: str) -> bool:
    """
    Run the complete database migration process.
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        True if migration was successful, False otherwise
    """
    logger.info(f"🔄 Starting database migration for: {db_path}")
    
    # Run migration
    if not migrate_database(db_path):
        logger.error("❌ Database migration failed")
        return False
    
    # Verify migration
    if not verify_migration(db_path):
        logger.error("❌ Database migration verification failed")
        return False
    
    logger.info("✅ Database migration completed successfully")
    return True


if __name__ == "__main__":
    import sys
    import os
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get database path from command line or use default
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        # Default database path
        db_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "job_tracker.db")
    
    # Run migration
    success = run_migration(db_path)
    sys.exit(0 if success else 1) 