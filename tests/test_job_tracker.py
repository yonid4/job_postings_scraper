"""
Test suite for the enhanced job tracker functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
import os

# Add the frontend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'frontend'))

from app_supabase import app


class TestJobTracker:
    """Test cases for the job tracker functionality."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user."""
        return {
            'user_id': 'test-user-123',
            'email': 'test@example.com',
            'email_verified': True
        }
    
    @pytest.fixture
    def mock_db_manager(self):
        """Mock database manager."""
        mock_manager = Mock()
        
        # Mock jobs data
        mock_jobs = [
            {
                'id': 'job-1',
                'job_title': 'Software Engineer',
                'company_name': 'Tech Corp',
                'location': 'San Francisco, CA',
                'job_url': 'https://example.com/job1',
                'source': 'linkedin',
                'date_found': datetime.now().isoformat()
            },
            {
                'id': 'job-2',
                'job_title': 'Data Scientist',
                'company_name': 'Data Inc',
                'location': 'New York, NY',
                'job_url': 'https://example.com/job2',
                'source': 'indeed',
                'date_found': datetime.now().isoformat()
            }
        ]
        
        # Mock applications data
        mock_applications = [
            {
                'job_id': 'job-1',
                'application_status': 'applied',
                'applied_date': datetime.now().isoformat(),
                'application_method': 'manual',
                'response_received': True,
                'response_date': (datetime.now() + timedelta(days=3)).isoformat()
            }
        ]
        
        # Mock favorites data
        mock_favorites = [
            {
                'job_id': 'job-1',
                'priority': 'high',
                'notes': 'Great opportunity!',
                'favorited_date': datetime.now().isoformat()
            }
        ]
        
        # Mock database responses
        mock_manager.client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = mock_jobs
        mock_manager.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = mock_applications
        
        return mock_manager
    
    def test_jobs_tracker_route_requires_auth(self, client):
        """Test that jobs tracker route requires authentication."""
        response = client.get('/jobs-tracker')
        assert response.status_code == 302  # Redirect to login
    
    @patch('frontend.app_supabase.get_current_user')
    @patch('frontend.app_supabase.get_authenticated_db_manager')
    def test_jobs_tracker_route_success(self, mock_get_db, mock_get_user, client, mock_user, mock_db_manager):
        """Test successful access to jobs tracker route."""
        mock_get_user.return_value = mock_user
        mock_get_db.return_value = mock_db_manager
        
        with client.session_transaction() as sess:
            sess['user_id'] = mock_user['user_id']
        
        response = client.get('/jobs-tracker')
        assert response.status_code == 200
        assert b'My Jobs' in response.data
        assert b'Job Tracker' in response.data
    
    def test_get_enhanced_jobs_data(self):
        """Test the get_enhanced_jobs_data function."""
        from app_supabase import get_enhanced_jobs_data
        
        mock_db_manager = Mock()
        
        # Mock database responses
        mock_jobs = [
            {
                'id': 'job-1',
                'job_title': 'Software Engineer',
                'company_name': 'Tech Corp',
                'location': 'San Francisco, CA',
                'source': 'linkedin'
            }
        ]
        
        mock_applications = [
            {
                'job_id': 'job-1',
                'application_status': 'applied',
                'applied_date': datetime.now().isoformat()
            }
        ]
        
        mock_favorites = [
            {
                'job_id': 'job-1',
                'priority': 'high',
                'notes': 'Great opportunity!'
            }
        ]
        
        # Setup mock responses
        mock_db_manager.client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = mock_jobs
        mock_db_manager.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = mock_applications
        mock_db_manager.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = mock_favorites
        
        # Test function
        result = get_enhanced_jobs_data(mock_db_manager, 'test-user', {})
        
        assert len(result) == 1
        assert result[0]['job']['job_title'] == 'Software Engineer'
        assert result[0]['application']['application_status'] == 'applied'
        assert result[0]['is_favorited'] == True
        assert result[0]['priority'] == 'high'
    
    def test_passes_filters(self):
        """Test the passes_filters function."""
        from app_supabase import passes_filters
        
        job = {
            'job_title': 'Software Engineer',
            'company_name': 'Tech Corp',
            'location': 'San Francisco, CA',
            'source': 'linkedin'
        }
        
        application = {
            'application_status': 'applied',
            'applied_date': datetime.now().isoformat()
        }
        
        # Test search filter
        filters = {'search': 'Software'}
        assert passes_filters(job, application, filters) == True
        
        filters = {'search': 'Marketing'}
        assert passes_filters(job, application, filters) == False
        
        # Test status filter
        filters = {'status': 'applied'}
        assert passes_filters(job, application, filters) == True
        
        filters = {'status': 'interview'}
        assert passes_filters(job, application, filters) == False
        
        # Test source filter
        filters = {'source': 'linkedin'}
        assert passes_filters(job, application, filters) == True
        
        filters = {'source': 'indeed'}
        assert passes_filters(job, application, filters) == False
    
    def test_calculate_comprehensive_analytics(self):
        """Test the calculate_comprehensive_analytics function."""
        from app_supabase import calculate_comprehensive_analytics
        
        mock_db_manager = Mock()
        
        # Mock applications data
        mock_applications = [
            {
                'application_status': 'applied',
                'response_received': True,
                'applied_date': datetime.now().isoformat(),
                'response_date': (datetime.now() + timedelta(days=3)).isoformat(),
                'company_name': 'Tech Corp'
            },
            {
                'application_status': 'interview',
                'response_received': False,
                'company_name': 'Data Inc'
            }
        ]
        
        # Mock jobs data
        mock_jobs = [
            {'id': 'job-1'},
            {'id': 'job-2'}
        ]
        
        # Setup mock responses
        mock_db_manager.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = mock_applications
        mock_db_manager.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = mock_jobs
        
        # Test function
        result = calculate_comprehensive_analytics(mock_db_manager, 'test-user')
        
        assert result['total_jobs_tracked'] == 2
        assert result['applications_submitted'] == 2
        assert result['response_rate'] == 50.0
        assert result['interviews_scheduled'] == 1
        assert 'funnel' in result
        assert 'top_companies' in result
    
    @patch('frontend.app_supabase.get_current_user')
    def test_update_job_status_api(self, mock_get_user, client, mock_user):
        """Test the update job status API endpoint."""
        mock_get_user.return_value = mock_user
        
        with client.session_transaction() as sess:
            sess['user_id'] = mock_user['user_id']
        
        # Test with valid data
        data = {
            'job_id': 'job-123',
            'status': 'applied',
            'notes': 'Applied via company website'
        }
        
        response = client.post('/api/jobs/status-update', 
                             json=data,
                             content_type='application/json')
        
        # Should return 200 even if database operations fail (due to mocking)
        assert response.status_code == 200
    
    def test_get_days_since_applied_filter(self):
        """Test the get_days_since_applied template filter."""
        from app_supabase import get_days_since_applied
        
        # Test with string date
        applied_date = datetime.now() - timedelta(days=5)
        result = get_days_since_applied(applied_date.isoformat())
        assert result == 5
        
        # Test with None
        result = get_days_since_applied(None)
        assert result == 'Unknown'
        
        # Test with datetime object
        result = get_days_since_applied(applied_date)
        assert result == 5


if __name__ == '__main__':
    pytest.main([__file__]) 