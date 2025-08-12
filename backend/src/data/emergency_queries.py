import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class EmergencyJobData:
    """Minimal job data structure for emergency fast queries."""
    job_id: str
    job_title: str
    company_name: str
    location: Optional[str]
    salary_range: Optional[str]
    linkedin_url: str
    application_status: Optional[str]
    applied_date: Optional[datetime]
    created_at: datetime

class EmergencyJobQueries:
    """Emergency ultra-fast job queries using raw SQL to bypass ORM overhead."""
    
    def __init__(self, supabase_client):
        self.client = supabase_client
        
    def get_jobs_emergency_fast(self, user_id: str, page: int = 1, limit: int = 10) -> Tuple[List[EmergencyJobData], int]:
        """
        EMERGENCY: Ultra-fast job query using raw SQL.
        Target: <200ms execution time
        """
        start_time = time.time()
        
        try:
            # Calculate offset
            offset = (page - 1) * limit
            
            # EMERGENCY: Raw SQL query - NO ORM overhead
            query = """
            SELECT 
                j.job_id,
                j.job_title, 
                j.company_name,
                j.location,
                j.salary_range,
                j.linkedin_url,
                j.created_at,
                a.application_status,
                a.applied_date
            FROM jobs j
            LEFT JOIN applications a ON j.job_id = a.job_id AND a.user_id = %s
            WHERE j.user_id = %s
            ORDER BY j.created_at DESC
            LIMIT %s OFFSET %s
            """
            
            # Execute raw query with parameters
            result = self.client.rpc('execute_sql', {
                'query': query,
                'params': [user_id, user_id, limit, offset]
            }).execute()
            
            # Parse results into minimal data structure
            jobs = []
            for row in result.data:
                job = EmergencyJobData(
                    job_id=row['job_id'],
                    job_title=row['job_title'],
                    company_name=row['company_name'],
                    location=row['location'],
                    salary_range=row['salary_range'],
                    linkedin_url=row['linkedin_url'],
                    application_status=row['application_status'],
                    applied_date=row['applied_date'],
                    created_at=row['created_at']
                )
                jobs.append(job)
            
            # Get total count with separate fast query
            count_query = """
            SELECT COUNT(*) as total
            FROM jobs j
            WHERE j.user_id = %s
            """
            
            count_result = self.client.rpc('execute_sql', {
                'query': count_query,
                'params': [user_id]
            }).execute()
            
            total_count = count_result.data[0]['total'] if count_result.data else 0
            
            duration = time.time() - start_time
            logger.info(f"🚨 EMERGENCY QUERY: get_jobs_emergency_fast took {duration:.3f}s for {len(jobs)} jobs")
            
            if duration > 0.2:
                logger.error(f"🚨 CRITICAL: Emergency query still slow: {duration:.3f}s")
            
            return jobs, total_count
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"🚨 EMERGENCY QUERY ERROR: {duration:.3f}s - {e}")
            raise
    
    def get_jobs_with_minimal_data(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        ULTRA-MINIMAL: Get only essential job data for list view.
        Target: <100ms execution time
        """
        start_time = time.time()
        
        try:
            # MINIMAL: Only essential fields for list view
            query = """
            SELECT 
                j.job_id,
                j.job_title, 
                j.company_name,
                j.location,
                a.application_status
            FROM jobs j
            LEFT JOIN applications a ON j.job_id = a.job_id AND a.user_id = %s
            WHERE j.user_id = %s
            ORDER BY j.created_at DESC
            LIMIT %s
            """
            
            result = self.client.rpc('execute_sql', {
                'query': query,
                'params': [user_id, user_id, limit]
            }).execute()
            
            # Convert to simple dictionaries
            jobs = []
            for row in result.data:
                jobs.append({
                    'job_id': row['job_id'],
                    'job_title': row['job_title'],
                    'company_name': row['company_name'],
                    'location': row['location'],
                    'application_status': row['application_status']
                })
            
            duration = time.time() - start_time
            logger.info(f"🚨 MINIMAL QUERY: get_jobs_with_minimal_data took {duration:.3f}s for {len(jobs)} jobs")
            
            return jobs
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"🚨 MINIMAL QUERY ERROR: {duration:.3f}s - {e}")
            raise
    
    def get_job_count_fast(self, user_id: str) -> int:
        """
        EMERGENCY: Fast count query only.
        Target: <50ms execution time
        """
        start_time = time.time()
        
        try:
            query = "SELECT COUNT(*) as total FROM jobs WHERE user_id = %s"
            
            result = self.client.rpc('execute_sql', {
                'query': query,
                'params': [user_id]
            }).execute()
            
            count = result.data[0]['total'] if result.data else 0
            
            duration = time.time() - start_time
            logger.info(f"🚨 COUNT QUERY: get_job_count_fast took {duration:.3f}s")
            
            return count
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"🚨 COUNT QUERY ERROR: {duration:.3f}s - {e}")
            return 0
    
    def pre_render_jobs_html(self, jobs: List[EmergencyJobData]) -> str:
        """
        EMERGENCY: Pre-render HTML in Python to avoid template overhead.
        Target: <50ms rendering time
        """
        start_time = time.time()
        
        html_parts = []
        for job in jobs:
            # MINIMAL HTML - no complex styling
            status_class = "text-success" if job.application_status == "applied" else "text-muted"
            status_text = job.application_status or "Not Applied"
            
            html = f"""
            <div class="job-card">
                <div class="job-title">{job.job_title}</div>
                <div class="company">{job.company_name}</div>
                <div class="location">{job.location or 'Location not specified'}</div>
                <div class="status {status_class}">{status_text}</div>
                <a href="/jobs/{job.job_id}" class="btn btn-sm btn-primary">View Details</a>
            </div>
            """
            html_parts.append(html)
        
        final_html = "\n".join(html_parts)
        
        duration = time.time() - start_time
        logger.info(f"🚨 PRE-RENDER: pre_render_jobs_html took {duration:.3f}s for {len(jobs)} jobs")
        
        return final_html

# Emergency query timeout handler
def emergency_query_timeout(func):
    """Decorator to enforce emergency query timeouts."""
    import functools
    import signal
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Emergency query timeout: {func.__name__}")
        
        # Set 2-second timeout for emergency queries
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(2)
        
        try:
            result = func(*args, **kwargs)
            signal.alarm(0)  # Cancel timeout
            return result
        except TimeoutError:
            logger.error(f"🚨 EMERGENCY QUERY TIMEOUT: {func.__name__}")
            raise
        except Exception as e:
            signal.alarm(0)  # Cancel timeout
            raise
    
    return wrapper 