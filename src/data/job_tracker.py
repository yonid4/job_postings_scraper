"""
Job tracking system for managing job searches, applications, and favorites.

This module provides comprehensive database operations for:
- Job search history and results
- Application status tracking
- Job favorites and bookmarks
- Bulk operations and filtering
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

from src.data.models import (
    JobSearch, JobApplication, JobFavorite, JobListing, 
    ApplicationStatus, ApplicationMethod, QualificationResult
)
from src.utils.logger import JobAutomationLogger

logger = JobAutomationLogger()


class JobTracker:
    """
    Manages job tracking operations including searches, applications, and favorites.
    
    This class provides functionality to:
    - Store and retrieve job search history
    - Track application status and progress
    - Manage job favorites and bookmarks
    - Provide analytics and reporting
    - Handle bulk operations efficiently
    """
    
    def __init__(self, db_path: str):
        """
        Initialize the job tracker.
        
        Args:
            db_path: Path to the SQLite database
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the database with all required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create job_searches table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS job_searches (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        search_name TEXT NOT NULL,
                        keywords TEXT NOT NULL,
                        location TEXT,
                        remote_preference TEXT,
                        experience_level TEXT,
                        job_type TEXT,
                        date_posted_filter INTEGER,
                        salary_min INTEGER,
                        salary_max INTEGER,
                        job_sites TEXT NOT NULL,
                        search_date TEXT NOT NULL,
                        completed_date TEXT,
                        total_jobs_found INTEGER DEFAULT 0,
                        qualified_jobs_count INTEGER DEFAULT 0,
                        jobs_processed INTEGER DEFAULT 0,
                        is_active BOOLEAN DEFAULT TRUE,
                        notes TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create job_applications table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS job_applications (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        job_id TEXT NOT NULL,
                        applied_date TEXT NOT NULL,
                        application_method TEXT NOT NULL,
                        status TEXT NOT NULL,
                        application_url TEXT,
                        cover_letter_used BOOLEAN DEFAULT FALSE,
                        resume_version TEXT,
                        follow_up_date TEXT,
                        interview_date TEXT,
                        response_received BOOLEAN DEFAULT FALSE,
                        response_date TEXT,
                        notes TEXT,
                        salary_offered INTEGER,
                        benefits_offered TEXT,
                        created_date TEXT NOT NULL,
                        last_updated TEXT NOT NULL
                    )
                ''')
                
                # Create job_favorites table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS job_favorites (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        job_id TEXT NOT NULL,
                        favorited_date TEXT NOT NULL,
                        notes TEXT,
                        priority INTEGER DEFAULT 1,
                        created_date TEXT NOT NULL,
                        last_updated TEXT NOT NULL
                    )
                ''')
                
                # Create job_listings table (enhanced version)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS job_listings (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        company TEXT NOT NULL,
                        location TEXT,
                        job_url TEXT NOT NULL,
                        job_site TEXT NOT NULL,
                        description TEXT,
                        requirements TEXT,
                        responsibilities TEXT,
                        benefits TEXT,
                        salary_min INTEGER,
                        salary_max INTEGER,
                        salary_currency TEXT DEFAULT 'USD',
                        job_type TEXT,
                        experience_level TEXT,
                        remote_type TEXT,
                        application_url TEXT,
                        application_deadline TEXT,
                        application_requirements TEXT,
                        posted_date TEXT,
                        scraped_date TEXT NOT NULL,
                        last_updated TEXT NOT NULL,
                        is_duplicate BOOLEAN DEFAULT FALSE,
                        duplicate_of TEXT,
                        notes TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_searches_user_id ON job_searches(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_searches_search_date ON job_searches(search_date)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_applications_user_id ON job_applications(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_applications_job_id ON job_applications(job_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_applications_status ON job_applications(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_favorites_user_id ON job_favorites(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_favorites_job_id ON job_favorites(job_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_listings_company ON job_listings(company)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_listings_location ON job_listings(location)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_listings_posted_date ON job_listings(posted_date)')
                
                conn.commit()
                logger.info("Job tracking database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing job tracking database: {e}")
            raise
    
    # Job Search Operations
    def save_job_search(self, job_search: JobSearch) -> str:
        """Save a job search to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO job_searches (
                        id, user_id, search_name, keywords, location, remote_preference,
                        experience_level, job_type, date_posted_filter, salary_min,
                        salary_max, job_sites, search_date, completed_date,
                        total_jobs_found, qualified_jobs_count, jobs_processed,
                        is_active, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    job_search.id, job_search.user_id, job_search.search_name,
                    json.dumps(job_search.keywords), job_search.location,
                    job_search.remote_preference.value if job_search.remote_preference else None,
                    job_search.experience_level.value if job_search.experience_level else None,
                    job_search.job_type.value if job_search.job_type else None,
                    job_search.date_posted_filter, job_search.salary_min,
                    job_search.salary_max, json.dumps(job_search.job_sites),
                    job_search.search_date.isoformat(),
                    job_search.completed_date.isoformat() if job_search.completed_date else None,
                    job_search.total_jobs_found, job_search.qualified_jobs_count,
                    job_search.jobs_processed, job_search.is_active, job_search.notes
                ))
                
                conn.commit()
                logger.info(f"Job search saved: {job_search.id}")
                return job_search.id
                
        except Exception as e:
            logger.error(f"Error saving job search: {e}")
            raise
    
    def get_user_job_searches(self, user_id: str, limit: int = 50) -> List[JobSearch]:
        """Get job searches for a user."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM job_searches 
                    WHERE user_id = ? 
                    ORDER BY search_date DESC 
                    LIMIT ?
                ''', (user_id, limit))
                
                searches = []
                for row in cursor.fetchall():
                    searches.append(self._row_to_job_search(row))
                
                return searches
                
        except Exception as e:
            logger.error(f"Error getting job searches: {e}")
            return []
    
    def get_job_search(self, search_id: str) -> Optional[JobSearch]:
        """Get a specific job search by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM job_searches WHERE id = ?', (search_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_job_search(row)
                return None
                
        except Exception as e:
            logger.error(f"Error getting job search: {e}")
            return None
    
    # Job Application Operations
    def save_job_application(self, application: JobApplication) -> str:
        """Save a job application to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO job_applications (
                        id, user_id, job_id, applied_date, application_method,
                        status, application_url, cover_letter_used, resume_version,
                        follow_up_date, interview_date, response_received,
                        response_date, notes, salary_offered, benefits_offered,
                        created_date, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    application.id, application.user_id, application.job_id,
                    application.applied_date.isoformat(),
                    application.application_method.value,
                    application.status.value, application.application_url,
                    application.cover_letter_used, application.resume_version,
                    application.follow_up_date.isoformat() if application.follow_up_date else None,
                    application.interview_date.isoformat() if application.interview_date else None,
                    application.response_received,
                    application.response_date.isoformat() if application.response_date else None,
                    application.notes, application.salary_offered,
                    json.dumps(application.benefits_offered),
                    application.created_date.isoformat(),
                    application.last_updated.isoformat()
                ))
                
                conn.commit()
                logger.info(f"Job application saved: {application.id}")
                return application.id
                
        except Exception as e:
            logger.error(f"Error saving job application: {e}")
            raise
    
    def get_user_applications(self, user_id: str, status: Optional[ApplicationStatus] = None, limit: int = 100) -> List[JobApplication]:
        """Get applications for a user, optionally filtered by status."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if status:
                    cursor.execute('''
                        SELECT * FROM job_applications 
                        WHERE user_id = ? AND status = ?
                        ORDER BY applied_date DESC 
                        LIMIT ?
                    ''', (user_id, status.value, limit))
                else:
                    cursor.execute('''
                        SELECT * FROM job_applications 
                        WHERE user_id = ? 
                        ORDER BY applied_date DESC 
                        LIMIT ?
                    ''', (user_id, limit))
                
                applications = []
                for row in cursor.fetchall():
                    applications.append(self._row_to_job_application(row))
                
                return applications
                
        except Exception as e:
            logger.error(f"Error getting applications: {e}")
            return []
    
    def get_job_application(self, user_id: str, job_id: str) -> Optional[JobApplication]:
        """Get application for a specific job."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM job_applications 
                    WHERE user_id = ? AND job_id = ?
                ''', (user_id, job_id))
                
                row = cursor.fetchone()
                if row:
                    return self._row_to_job_application(row)
                return None
                
        except Exception as e:
            logger.error(f"Error getting job application: {e}")
            return None
    
    def update_application_status(self, user_id: str, job_id: str, status: ApplicationStatus, notes: str = "") -> bool:
        """Update the status of a job application."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE job_applications 
                    SET status = ?, notes = ?, last_updated = ?
                    WHERE user_id = ? AND job_id = ?
                ''', (
                    status.value, notes, datetime.now().isoformat(),
                    user_id, job_id
                ))
                
                conn.commit()
                logger.info(f"Application status updated: {job_id} -> {status.value}")
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error updating application status: {e}")
            return False
    
    # Job Favorites Operations
    def add_job_favorite(self, favorite: JobFavorite) -> str:
        """Add a job to favorites."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO job_favorites (
                        id, user_id, job_id, favorited_date, notes, priority,
                        created_date, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    favorite.id, favorite.user_id, favorite.job_id,
                    favorite.favorited_date.isoformat(), favorite.notes,
                    favorite.priority, favorite.created_date.isoformat(),
                    favorite.last_updated.isoformat()
                ))
                
                conn.commit()
                logger.info(f"Job added to favorites: {favorite.job_id}")
                return favorite.id
                
        except Exception as e:
            logger.error(f"Error adding job favorite: {e}")
            raise
    
    def remove_job_favorite(self, user_id: str, job_id: str) -> bool:
        """Remove a job from favorites."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM job_favorites 
                    WHERE user_id = ? AND job_id = ?
                ''', (user_id, job_id))
                
                conn.commit()
                logger.info(f"Job removed from favorites: {job_id}")
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error removing job favorite: {e}")
            return False
    
    def get_user_favorites(self, user_id: str, limit: int = 100) -> List[JobFavorite]:
        """Get favorite jobs for a user."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM job_favorites 
                    WHERE user_id = ? 
                    ORDER BY priority DESC, favorited_date DESC 
                    LIMIT ?
                ''', (user_id, limit))
                
                favorites = []
                for row in cursor.fetchall():
                    favorites.append(self._row_to_job_favorite(row))
                
                return favorites
                
        except Exception as e:
            logger.error(f"Error getting favorites: {e}")
            return []
    
    def is_job_favorited(self, user_id: str, job_id: str) -> bool:
        """Check if a job is favorited by the user."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT COUNT(*) FROM job_favorites 
                    WHERE user_id = ? AND job_id = ?
                ''', (user_id, job_id))
                
                count = cursor.fetchone()[0]
                return count > 0
                
        except Exception as e:
            logger.error(f"Error checking favorite status: {e}")
            return False
    
    # Job Listings Operations
    def save_job_listing(self, job: JobListing) -> str:
        """Save a job listing to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO job_listings (
                        id, title, company, location, job_url, job_site,
                        description, requirements, responsibilities, benefits,
                        salary_min, salary_max, salary_currency, job_type,
                        experience_level, remote_type, application_url,
                        application_deadline, application_requirements,
                        posted_date, scraped_date, last_updated, is_duplicate,
                        duplicate_of, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    job.id, job.title, job.company, job.location, job.job_url,
                    job.job_site, job.description, json.dumps(job.requirements),
                    json.dumps(job.responsibilities), json.dumps(job.benefits),
                    job.salary_min, job.salary_max, job.salary_currency,
                    job.job_type.value if job.job_type else None,
                    job.experience_level.value if job.experience_level else None,
                    job.remote_type.value if job.remote_type else None,
                    job.application_url,
                    job.application_deadline.isoformat() if job.application_deadline else None,
                    json.dumps(job.application_requirements),
                    job.posted_date.isoformat() if job.posted_date else None,
                    job.scraped_date.isoformat(), job.last_updated.isoformat(),
                    job.is_duplicate, job.duplicate_of, job.notes
                ))
                
                conn.commit()
                logger.info(f"Job listing saved: {job.id}")
                return job.id
                
        except Exception as e:
            logger.error(f"Error saving job listing: {e}")
            raise
    
    def get_job_listing(self, job_id: str) -> Optional[JobListing]:
        """Get a specific job listing by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM job_listings WHERE id = ?', (job_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_job_listing(row)
                return None
                
        except Exception as e:
            logger.error(f"Error getting job listing: {e}")
            return None
    
    def search_job_listings(self, user_id: str, filters: Dict[str, Any] = None, limit: int = 100) -> List[JobListing]:
        """Search job listings with filters."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build dynamic query based on filters
                query = 'SELECT * FROM job_listings WHERE 1=1'
                params = []
                
                if filters:
                    if filters.get('company'):
                        query += ' AND company LIKE ?'
                        params.append(f"%{filters['company']}%")
                    
                    if filters.get('location'):
                        query += ' AND location LIKE ?'
                        params.append(f"%{filters['location']}%")
                    
                    if filters.get('title'):
                        query += ' AND title LIKE ?'
                        params.append(f"%{filters['title']}%")
                    
                    if filters.get('salary_min'):
                        query += ' AND salary_max >= ?'
                        params.append(filters['salary_min'])
                    
                    if filters.get('salary_max'):
                        query += ' AND salary_min <= ?'
                        params.append(filters['salary_max'])
                    
                    if filters.get('job_type'):
                        query += ' AND job_type = ?'
                        params.append(filters['job_type'])
                    
                    if filters.get('remote_type'):
                        query += ' AND remote_type = ?'
                        params.append(filters['remote_type'])
                
                query += ' ORDER BY posted_date DESC LIMIT ?'
                params.append(limit)
                
                cursor.execute(query, params)
                
                listings = []
                for row in cursor.fetchall():
                    listings.append(self._row_to_job_listing(row))
                
                return listings
                
        except Exception as e:
            logger.error(f"Error searching job listings: {e}")
            return []
    
    # Analytics and Reporting
    def get_application_analytics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get application analytics for a user."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get date range
                start_date = (datetime.now() - timedelta(days=days)).isoformat()
                
                # Total applications
                cursor.execute('''
                    SELECT COUNT(*) FROM job_applications 
                    WHERE user_id = ? AND applied_date >= ?
                ''', (user_id, start_date))
                total_applications = cursor.fetchone()[0]
                
                # Applications by status
                cursor.execute('''
                    SELECT status, COUNT(*) FROM job_applications 
                    WHERE user_id = ? AND applied_date >= ?
                    GROUP BY status
                ''', (user_id, start_date))
                status_counts = dict(cursor.fetchall())
                
                # Applications by method
                cursor.execute('''
                    SELECT application_method, COUNT(*) FROM job_applications 
                    WHERE user_id = ? AND applied_date >= ?
                    GROUP BY application_method
                ''', (user_id, start_date))
                method_counts = dict(cursor.fetchall())
                
                # Response rate
                cursor.execute('''
                    SELECT COUNT(*) FROM job_applications 
                    WHERE user_id = ? AND applied_date >= ? AND response_received = 1
                ''', (user_id, start_date))
                responses_received = cursor.fetchone()[0]
                
                response_rate = (responses_received / total_applications * 100) if total_applications > 0 else 0
                
                return {
                    'total_applications': total_applications,
                    'status_counts': status_counts,
                    'method_counts': method_counts,
                    'response_rate': round(response_rate, 2),
                    'responses_received': responses_received,
                    'period_days': days
                }
                
        except Exception as e:
            logger.error(f"Error getting application analytics: {e}")
            return {}
    
    # Helper methods for converting database rows to objects
    def _row_to_job_search(self, row: tuple) -> JobSearch:
        """Convert a database row to a JobSearch object."""
        from src.data.models import RemoteType, ExperienceLevel, JobType
        
        return JobSearch(
            id=row[0], user_id=row[1], search_name=row[2],
            keywords=json.loads(row[3]), location=row[4],
            remote_preference=RemoteType(row[5]) if row[5] else None,
            experience_level=ExperienceLevel(row[6]) if row[6] else None,
            job_type=JobType(row[7]) if row[7] else None,
            date_posted_filter=row[8], salary_min=row[9], salary_max=row[10],
            job_sites=json.loads(row[11]), search_date=datetime.fromisoformat(row[12]),
            completed_date=datetime.fromisoformat(row[13]) if row[13] else None,
            total_jobs_found=row[14], qualified_jobs_count=row[15],
            jobs_processed=row[16], is_active=bool(row[17]), notes=row[18]
        )
    
    def _row_to_job_application(self, row: tuple) -> JobApplication:
        """Convert a database row to a JobApplication object."""
        return JobApplication(
            id=row[0], user_id=row[1], job_id=row[2],
            applied_date=datetime.fromisoformat(row[3]),
            application_method=ApplicationMethod(row[4]),
            status=ApplicationStatus(row[5]), application_url=row[6],
            cover_letter_used=bool(row[7]), resume_version=row[8],
            follow_up_date=datetime.fromisoformat(row[9]) if row[9] else None,
            interview_date=datetime.fromisoformat(row[10]) if row[10] else None,
            response_received=bool(row[11]),
            response_date=datetime.fromisoformat(row[12]) if row[12] else None,
            notes=row[13], salary_offered=row[14],
            benefits_offered=json.loads(row[15]) if row[15] else [],
            created_date=datetime.fromisoformat(row[16]),
            last_updated=datetime.fromisoformat(row[17])
        )
    
    def _row_to_job_favorite(self, row: tuple) -> JobFavorite:
        """Convert a database row to a JobFavorite object."""
        return JobFavorite(
            id=row[0], user_id=row[1], job_id=row[2],
            favorited_date=datetime.fromisoformat(row[3]),
            notes=row[4], priority=row[5],
            created_date=datetime.fromisoformat(row[6]),
            last_updated=datetime.fromisoformat(row[7])
        )
    
    def _row_to_job_listing(self, row: tuple) -> JobListing:
        """Convert a database row to a JobListing object."""
        from src.data.models import JobType, ExperienceLevel, RemoteType
        
        return JobListing(
            id=row[0], title=row[1], company=row[2], location=row[3],
            job_url=row[4], job_site=row[5], description=row[6],
            requirements=json.loads(row[7]) if row[7] else [],
            responsibilities=json.loads(row[8]) if row[8] else [],
            benefits=json.loads(row[9]) if row[9] else [],
            salary_min=row[10], salary_max=row[11], salary_currency=row[12],
            job_type=JobType(row[13]) if row[13] else None,
            experience_level=ExperienceLevel(row[14]) if row[14] else None,
            remote_type=RemoteType(row[15]) if row[15] else None,
            application_url=row[16],
            application_deadline=datetime.fromisoformat(row[17]) if row[17] else None,
            application_requirements=json.loads(row[18]) if row[18] else [],
            posted_date=datetime.fromisoformat(row[19]) if row[19] else None,
            scraped_date=datetime.fromisoformat(row[20]),
            last_updated=datetime.fromisoformat(row[21]),
            is_duplicate=bool(row[22]), duplicate_of=row[23], notes=row[24]
        ) 