#!/usr/bin/env python3
"""
Flask web application for the AI Job Qualification Screening System with Supabase Integration.

This provides a user-friendly web interface for:
- User authentication and profile management
- Job search URL input
- Qualification analysis results
- Database storage and retrieval
- Resume upload and processing
"""

import os
import sys
import tempfile
import time
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_session import Session
import logging
import uuid
from typing import Dict, Any, Optional
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Add the parent directory to Python path to import src modules
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from src.config.config_manager import ConfigurationManager, UserProfile, AISettings
from src.utils.job_link_processor import JobLinkProcessor
from src.ai.qualification_analyzer import QualificationAnalyzer, AnalysisRequest
from src.data.models import QualificationResult, QualificationStatus, UserDecision
from src.data.google_sheets_manager import GoogleSheetsManager
from src.data.resume_manager import ResumeManager
from src.data.job_tracker import JobTracker
from src.data.models import JobApplication, ApplicationStatus, ApplicationMethod, JobFavorite
from src.utils.logger import JobAutomationLogger

# Supabase integration
from src.auth.flask_integration import get_auth_manager, supabase_integration, get_current_user, get_user_id, get_db_manager, get_authenticated_db_manager
from src.data.supabase_manager import Job as SupabaseJob, Application as SupabaseApplication, JobSearch, ApplicationStatus as SupabaseApplicationStatus, ApplicationMethod as SupabaseApplicationMethod

# New Supabase Auth integration
from src.auth.auth_context import init_auth_context, get_auth_context
from src.auth.template_context import register_template_context_processors

# Import the new auth decorators
from src.auth.auth_context import login_required, email_verified_required, get_user_profile

# Import profile routes
from profile_routes import profile_bp

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-change-this')

# Configure session to use server-side storage
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Configure upload settings
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create upload directories
os.makedirs(os.path.join(UPLOAD_FOLDER, 'resumes'), exist_ok=True)

# Supabase configuration
app.config['SUPABASE_URL'] = os.getenv('SUPABASE_URL')
app.config['NEXT_PUBLIC_SUPABASE_ANON_KEY'] = os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')

# Initialize Supabase integration
supabase_integration.init_app(app)

# Initialize new Supabase Auth context
try:
    from supabase import create_client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_anon_key = os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')
    
    if supabase_url and supabase_anon_key:
        supabase_client = create_client(supabase_url, supabase_anon_key)
        init_auth_context(supabase_client)
        logger.info("Supabase Auth context initialized successfully")
    else:
        logger.warning("Supabase credentials not found, auth context not initialized")
except Exception as e:
    logger.error(f"Failed to initialize Supabase Auth context: {e}")

# Register template context processors
register_template_context_processors(app)

# Initialize logger
logger = JobAutomationLogger()

# Global variables for system components
config_manager = None
job_processor = None
qualification_analyzer = None
sheets_manager = None
resume_manager = None
job_tracker = None

# Server-side storage for analysis results (in-memory cache)
analysis_cache: Dict[str, Any] = {}

def cleanup_old_analysis_results():
    """Clean up old analysis results from cache to prevent memory issues."""
    try:
        # Keep only the most recent 10 analysis results
        if len(analysis_cache) > 10:
            # Remove oldest entries (simple approach - in production you might want timestamps)
            keys_to_remove = list(analysis_cache.keys())[:-10]
            for key in keys_to_remove:
                del analysis_cache[key]
            logger.info(f"Cleaned up {len(keys_to_remove)} old analysis results from cache")
    except Exception as e:
        logger.error(f"Error cleaning up analysis cache: {e}")


def initialize_system():
    """Initialize the system components."""
    global config_manager, job_processor, qualification_analyzer, sheets_manager, resume_manager, job_tracker
    
    try:
        config_manager = ConfigurationManager()
        job_processor = JobLinkProcessor()
        
        # Initialize AI analyzer
        ai_settings = config_manager.get_ai_settings()
        if ai_settings.api_key:
            qualification_analyzer = QualificationAnalyzer(ai_settings)
        else:
            # Use custom analyzer if no API key
            from examples.custom_analyzer_example import CustomRuleBasedAnalyzer
            qualification_analyzer = CustomRuleBasedAnalyzer(ai_settings)
        
        # Initialize Google Sheets manager
        sheets_manager = GoogleSheetsManager()
        
        # Initialize resume manager
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'resumes.db')
        upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads', 'resumes')
        resume_manager = ResumeManager(db_path, upload_folder)
        
        # Initialize job tracker
        job_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'jobs.db')
        job_tracker = JobTracker(job_db_path)
        
        logger.info("System components initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing system components: {e}")
        raise


def allowed_file(filename):
    """Check if file extension is allowed."""
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_user_id():
    """Get current user ID from session or database."""
    return get_user_id()


# Register authentication blueprint
from auth_routes import auth_bp
app.register_blueprint(auth_bp)

# Register profile blueprint
app.register_blueprint(profile_bp, url_prefix='/profile')

# Update existing routes to use new auth system
@app.route('/')
@login_required
def index():
    """
    Main dashboard page.
    
    GET: Display dashboard with user's job search history and recommendations
    """
    try:
        current_user = get_current_user()
        user_profile = get_user_profile()
        
        # Get user's recent job searches and applications
        # This would integrate with your existing job tracking system
        
        return render_template('index.html', 
                            user=current_user, 
                            profile=user_profile)
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        flash("An error occurred while loading the dashboard.", "error")
        return render_template('index.html')

@app.route('/search')
@login_required
def search():
    """
    Job search page.
    
    GET: Display job search interface
    """
    try:
        current_user = get_current_user()
        user_profile = get_user_profile()
        
        return render_template('search.html', 
                            user=current_user, 
                            profile=user_profile)
    except Exception as e:
        logger.error(f"Error loading search page: {e}")
        flash("An error occurred while loading the search page.", "error")
        return render_template('search.html')

@app.route('/results')
@login_required
def results():
    """Results page for job analysis."""
    user = get_current_user()
    return render_template('results.html', user=user)


@app.route('/settings')
@login_required
def settings():
    """
    User settings page.
    
    GET: Display user settings
    """
    try:
        current_user = get_current_user()
        user_profile = get_user_profile()
        
        return render_template('settings.html', 
                            user=current_user, 
                            profile=user_profile)
    except Exception as e:
        logger.error(f"Error loading settings page: {e}")
        flash("An error occurred while loading settings.", "error")
        return render_template('settings.html')


@app.route('/settings/update', methods=['POST'])
@login_required
def update_settings():
    """Update user settings."""
    try:
        user = get_current_user()
        if not user:
            flash("User not authenticated.", "error")
            return redirect(url_for('settings'))
        
        # Handle settings update logic here
        flash("Settings updated successfully!", "success")
        return redirect(url_for('settings'))
        
    except Exception as e:
        logger.error(f"Settings update error: {e}")
        flash("An error occurred while updating settings.", "error")
        return redirect(url_for('settings'))


@app.route('/resume/upload', methods=['POST'])
@login_required
def upload_resume():
    """Upload resume file."""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'User not authenticated'})
        
        if 'resume' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'})
        
        file = request.files['resume']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        if file and allowed_file(file.filename):
            # Handle resume upload logic here
            return jsonify({'success': True, 'message': 'Resume uploaded successfully'})
        else:
            return jsonify({'success': False, 'error': 'Invalid file type'})
            
    except Exception as e:
        logger.error(f"Resume upload error: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/resume/status')
@login_required
def get_resume_status():
    """Get resume processing status."""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'User not authenticated'})
        
        # Return resume status
        return jsonify({
            'success': True,
            'has_resume': False,
            'status': 'no_resume'
        })
        
    except Exception as e:
        logger.error(f"Resume status error: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/profile')
@login_required
def profile():
    """User profile page."""
    user = get_current_user()
    
    # Load user profile data from database
    db_manager = get_authenticated_db_manager()
    profile_data = None
    
    if db_manager and user:
        profile_data = db_manager.profiles.get_profile(user['user_id'])
    
    return render_template('profile.html', user=user, profile=profile_data)


@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile."""
    try:
        user = get_current_user()
        if not user:
            flash("User not found.", "error")
            return redirect(url_for('profile'))
        
        # Get form data from the actual profile form fields
        years_of_experience = request.form.get('years_of_experience', '0')
        experience_level = request.form.get('experience_level', '').strip()
        education_level = request.form.get('education_level', '').strip()
        work_arrangement_preference = request.form.get('work_arrangement_preference', '').strip()
        field_of_study = request.form.get('field_of_study', '').strip()
        skills_technologies = request.form.get('skills_technologies', '').strip()
        preferred_locations = request.form.get('preferred_locations', '').strip()
        salary_min = request.form.get('salary_min', '').strip()
        salary_max = request.form.get('salary_max', '').strip()
        linkedin_credentials = request.form.get('linkedin_credentials', '').strip()
        
        # Validate required fields
        if not experience_level:
            flash("Experience level is required.", "error")
            return redirect(url_for('profile'))
        
        if not education_level:
            flash("Education level is required.", "error")
            return redirect(url_for('profile'))
        
        if not work_arrangement_preference:
            flash("Work arrangement preference is required.", "error")
            return redirect(url_for('profile'))
        
        if not skills_technologies:
            flash("Skills and technologies are required.", "error")
            return redirect(url_for('profile'))
        
        # Create profile data
        profile_data = {
            'user_id': user['user_id'],
            'years_of_experience': int(years_of_experience),
            'experience_level': experience_level,
            'education_level': education_level,
            'work_arrangement_preference': work_arrangement_preference,
            'field_of_study': field_of_study,
            'skills_technologies': skills_technologies,
            'preferred_locations': preferred_locations,
            'salary_min': int(salary_min) if salary_min else None,
            'salary_max': int(salary_max) if salary_max else None,
            'linkedin_credentials': linkedin_credentials
        }
        
        # Update user profile in database
        db_manager = get_authenticated_db_manager()
        if db_manager:
            # Convert form data to match database schema
            db_profile_data = {
                'years_of_experience': int(years_of_experience) if years_of_experience else None,
                'experience_level': experience_level,
                'education_level': education_level,
                'work_arrangement_preference': work_arrangement_preference,
                'field_of_study': field_of_study if field_of_study else None,
                'skills_technologies': skills_technologies.split(',') if skills_technologies else [],
                'preferred_locations': preferred_locations.split(',') if preferred_locations else [],
                'salary_min': int(salary_min) if salary_min else None,
                'salary_max': int(salary_max) if salary_max else None
            }
            
            # Check if profile exists
            existing_profile = db_manager.profiles.get_profile(user['user_id'])
            
            if existing_profile:
                # Update existing profile
                success, message, updated_profile = db_manager.profiles.update_profile(user['user_id'], db_profile_data)
            else:
                # Create new profile
                success, message, updated_profile = db_manager.profiles.create_profile(user['user_id'], db_profile_data)
            
            if success:
                flash("Profile updated successfully!", "success")
            else:
                flash(f"Failed to update profile: {message}", "error")
        else:
            flash("Database not available.", "error")
        
        return redirect(url_for('profile'))
        
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        flash("An error occurred while updating your profile.", "error")
        return redirect(url_for('profile'))


@app.route('/search/analyze', methods=['POST'])
@login_required
def analyze_jobs():
    """Analyze jobs from URL using profile data."""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'User not authenticated'})
        
        job_url = request.form.get('job_url', '').strip()
        
        if not job_url:
            return jsonify({'success': False, 'error': 'Job URL is required'})
        
        # Get profile data for analysis
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'})
        
        analysis_data = db_manager.profiles.get_analysis_data(user['user_id'])
        if not analysis_data:
            return jsonify({'success': False, 'error': 'Please complete your profile before analyzing jobs'})
        
        # Check if profile is complete
        is_complete = db_manager.profiles.is_profile_complete(user['user_id'])
        if not is_complete:
            return jsonify({'success': False, 'error': 'Please complete your profile before analyzing jobs'})
        
        # Create user profile object from database data
        from src.config.config_manager import UserProfile, AISettings
        user_profile = UserProfile(
            years_of_experience=analysis_data.get('years_of_experience', 0),
            experience_level=analysis_data.get('experience_level', 'entry'),
            additional_skills=analysis_data.get('skills_technologies', []),
            preferred_locations=analysis_data.get('preferred_locations', []),
            salary_min=analysis_data.get('salary_min'),
            salary_max=analysis_data.get('salary_max'),
            remote_preference=analysis_data.get('work_arrangement_preference', 'any')
        )
        
        # Get AI settings from config
        ai_settings = config_manager.get_ai_settings() if config_manager else AISettings()
        
        # Process job URL
        if job_processor:
            processed_url = job_processor.process_url(job_url)
            
            # Analyze job with AI
            if qualification_analyzer:
                # Create analysis request
                from src.ai.qualification_analyzer import AnalysisRequest
                request = AnalysisRequest(
                    job_title="Job Analysis",  # Will be updated with actual job data
                    company="Unknown Company",
                    job_description="Job description will be extracted from URL",
                    user_profile=user_profile,
                    ai_settings=ai_settings
                )
                
                # For now, return a response indicating profile integration is working
                return jsonify({
                    'success': True,
                    'message': 'Profile integration successful - job analysis ready',
                    'profile_data': {
                        'experience_level': analysis_data.get('experience_level'),
                        'skills_count': len(analysis_data.get('skills_technologies', [])),
                        'preferred_locations': analysis_data.get('preferred_locations', []),
                        'salary_range': f"${analysis_data.get('salary_min', 0)} - ${analysis_data.get('salary_max', 'No max')}"
                    },
                    'result': {
                        'status': 'profile_ready',
                        'score': 0,
                        'reasoning': 'Profile data loaded successfully',
                        'recommendations': ['Complete job data extraction to proceed with analysis']
                    }
                })
            else:
                return jsonify({'success': False, 'error': 'AI analyzer not available'})
        else:
            return jsonify({'success': False, 'error': 'Job processor not available'})
            
    except Exception as e:
        logger.error(f"Job analysis error: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/search/linkedin', methods=['POST'])
@login_required
def search_linkedin_jobs():
    """Search LinkedIn jobs and save to database."""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'User not authenticated'})
        
        keywords = request.form.get('keywords', '').strip()
        location = request.form.get('location', '').strip()
        max_jobs = int(request.form.get('max_jobs', 10))
        
        if not keywords:
            return jsonify({'success': False, 'error': 'Keywords are required'})
        
        # Create search record
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'})
        
        search_data = {
            'user_id': user['user_id'],
            'keywords': keywords,
            'location': location,
            'filters': {},
            'results_count': 0,
            'search_date': datetime.now().isoformat()
        }
        
        success, message, search_record = db_manager.searches.create_search(search_data)
        
        if not success:
            return jsonify({'success': False, 'error': f'Failed to create search record: {message}'})
        
        # TODO: Implement actual LinkedIn scraping here
        # For now, return mock data for demonstration
        mock_jobs = [
            {
                'job_title': f'Software Engineer - {keywords}',
                'company_name': 'Tech Company',
                'location': location or 'Remote',
                'job_description': f'Looking for a {keywords} developer...',
                'job_url': 'https://example.com/job1',
                'linkedin_url': 'https://linkedin.com/job1',
                'date_posted': datetime.now().isoformat(),
                'work_arrangement': 'Remote',
                'experience_level': 'Mid-level',
                'job_type': 'Full-time'
            }
        ]
        
        # Save jobs to database
        saved_jobs = []
        for job_data in mock_jobs:
            job_data['user_id'] = user['user_id']
            job_data['date_found'] = datetime.now().isoformat()
            
            success, message, job = db_manager.jobs.create_job(job_data)
            if success and job:
                saved_jobs.append(job)
        
        # Update search results count
        db_manager.searches.update_search_results(search_record.search_id, user['user_id'], len(saved_jobs))
        
        return jsonify({
            'success': True,
            'message': f'Found and saved {len(saved_jobs)} jobs',
            'jobs_count': len(saved_jobs),
            'search_id': search_record.search_id
        })
        
    except Exception as e:
        logger.error(f"LinkedIn search error: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/jobs')
@login_required
def jobs_page():
    """
    User's saved jobs page.
    
    GET: Display user's saved jobs
    """
    try:
        current_user = get_current_user()
        user_profile = get_user_profile()
        
        # Get user's saved jobs from database
        # This would integrate with your existing job tracking system
        
        return render_template('jobs.html', 
                            user=current_user, 
                            profile=user_profile)
    except Exception as e:
        logger.error(f"Error loading jobs page: {e}")
        flash("An error occurred while loading your jobs.", "error")
        return render_template('jobs.html')


@app.route('/jobs/<job_id>')
@login_required
def job_detail(job_id):
    """Display job details."""
    try:
        user = get_current_user()
        if not user:
            flash("User not authenticated.", "error")
            return redirect(url_for('auth.login_supabase'))
        
        db_manager = get_db_manager()
        if not db_manager:
            flash("Database not available.", "error")
            return redirect(url_for('jobs_page'))
        
        # Get job details
        job = db_manager.jobs.get_job_by_id(job_id, user['user_id'])
        
        if not job:
            flash("Job not found.", "error")
            return redirect(url_for('jobs_page'))
        
        # Get application status
        application = db_manager.applications.get_application_by_job(user['user_id'], job_id)
        
        return render_template('job_detail.html', job=job, application=application, user=user)
        
    except Exception as e:
        logger.error(f"Job detail error: {e}")
        flash("An error occurred while loading job details.", "error")
        return redirect(url_for('jobs_page'))


@app.route('/api/jobs/apply', methods=['POST'])
@login_required
def apply_to_job():
    """Apply to a job."""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'User not authenticated'})
        
        job_id = request.form.get('job_id')
        application_method = request.form.get('application_method', 'manual')
        notes = request.form.get('notes', '')
        
        if not job_id:
            return jsonify({'success': False, 'error': 'Job ID is required'})
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'})
        
        # Check if already applied
        existing_application = db_manager.applications.get_application_by_job(user['user_id'], job_id)
        if existing_application:
            return jsonify({'success': False, 'error': 'Already applied to this job'})
        
        # Create application
        application_data = {
            'user_id': user['user_id'],
            'job_id': job_id,
            'application_method': SupabaseApplicationMethod(application_method),
            'applied_date': datetime.now().isoformat(),
            'application_status': SupabaseApplicationStatus.APPLIED,
            'notes': notes
        }
        
        success, message, application = db_manager.applications.create_application(application_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Application submitted successfully',
                'application_id': application.application_id
            })
        else:
            return jsonify({'success': False, 'error': f'Failed to submit application: {message}'})
        
    except Exception as e:
        logger.error(f"Apply to job error: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/jobs/status', methods=['POST'])
@login_required
def update_application_status():
    """Update application status."""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'User not authenticated'})
        
        application_id = request.form.get('application_id')
        status = request.form.get('status')
        notes = request.form.get('notes', '')
        
        if not application_id or not status:
            return jsonify({'success': False, 'error': 'Application ID and status are required'})
        
        db_manager = get_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'})
        
        # Update application status
        success, message, application = db_manager.applications.update_application_status(
            application_id, user['user_id'], SupabaseApplicationStatus(status), notes
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Application status updated successfully',
                'status': status
            })
        else:
            return jsonify({'success': False, 'error': f'Failed to update status: {message}'})
        
    except Exception as e:
        logger.error(f"Update application status error: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/applications')
@login_required
def applications_page():
    """
    User's job applications page.
    
    GET: Display user's job applications
    """
    try:
        current_user = get_current_user()
        user_profile = get_user_profile()
        
        # Get user's applications from database
        # This would integrate with your existing application tracking system
        
        return render_template('applications.html', 
                            user=current_user, 
                            profile=user_profile)
    except Exception as e:
        logger.error(f"Error loading applications page: {e}")
        flash("An error occurred while loading your applications.", "error")
        return render_template('applications.html')


@app.route('/search-history')
@login_required
def search_history():
    """Display user's search history."""
    try:
        user = get_current_user()
        if not user:
            flash("User not authenticated.", "error")
            return redirect(url_for('auth.login_supabase'))
        
        db_manager = get_db_manager()
        if not db_manager:
            flash("Database not available.", "error")
            return redirect(url_for('index'))
        
        # Get user's search history
        searches = db_manager.searches.get_user_searches(user['user_id'], limit=50)
        
        return render_template('search_history.html', searches=searches, user=user)
        
    except Exception as e:
        logger.error(f"Search history error: {e}")
        flash("An error occurred while loading search history.", "error")
        return redirect(url_for('index'))


@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        db_manager = get_db_manager()
        db_status = "connected" if db_manager else "disconnected"
        
        # Check authentication
        auth_manager = supabase_integration.auth_manager
        auth_status = "connected" if auth_manager else "disconnected"
        
        return jsonify({
            'status': 'healthy',
            'database': db_status,
            'authentication': auth_status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.template_filter('nl2br')
def nl2br(value):
    """Convert newlines to HTML line breaks."""
    if value:
        return value.replace('\n', '<br>')
    return value


@app.template_filter('get_status_color')
def get_status_color(status):
    """Get Bootstrap color class for application status."""
    status_colors = {
        'pending': 'warning',
        'applied': 'info',
        'interviewing': 'primary',
        'rejected': 'danger',
        'accepted': 'success',
        'withdrawn': 'secondary'
    }
    return status_colors.get(status, 'secondary')


if __name__ == '__main__':
    # Initialize system components
    initialize_system()
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000) 