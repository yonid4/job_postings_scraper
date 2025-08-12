"""
Data management module for the job automation system.
"""

from .supabase_manager import SupabaseManager, UserManager, JobManager, ApplicationManager, SearchHistoryManager
from .supabase_manager import User, Job, Application, JobSearch, ApplicationStatus, ApplicationMethod
from .models import JobListing, JobApplication, QualificationResult, ScrapingSession

__all__ = [
    'SupabaseManager',
    'UserManager', 
    'JobManager',
    'ApplicationManager',
    'SearchHistoryManager',
    'User',
    'Job', 
    'Application',
    'JobSearch',
    'ApplicationStatus',
    'ApplicationMethod',
    'JobListing',
    'JobApplication', 
    'QualificationResult',
    'ScrapingSession'
] 