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

from src.data.resume_manager import ResumeManager


from src.utils.logger import JobAutomationLogger
from src.utils.captcha_handler import CAPTCHAStatus

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

# Import emergency performance modules
from src.debug.performance_profiler import emergency_profiler
from src.data.emergency_queries import EmergencyJobQueries
from flask_caching import Cache

def create_enhanced_analysis_request(evaluation_job_data, user_profile_data, ai_settings, resume_data=None):
    """
    Create an enhanced AnalysisRequest with complete user profile data.
    
    Args:
        evaluation_job_data: Job data dictionary
        user_profile_data: User profile data from database  
        ai_settings: AI configuration
        resume_data: Optional resume data
        
    Returns:
        AnalysisRequest with enhanced profile fields
    """
    from src.ai.qualification_analyzer import AnalysisRequest
    from src.config.config_manager import UserProfile
    
    # Create UserProfile object for backward compatibility
    user_profile = UserProfile(
        years_of_experience=user_profile_data.years_of_experience or 0,
        experience_level=user_profile_data.experience_level.value if user_profile_data.experience_level else 'entry',
        additional_skills=user_profile_data.skills_technologies or [],
        preferred_locations=user_profile_data.preferred_locations or [],
        salary_min=user_profile_data.salary_min,
        salary_max=user_profile_data.salary_max,
        remote_preference=user_profile_data.work_arrangement_preference.value if user_profile_data.work_arrangement_preference else 'any',
        has_college_degree=user_profile_data.education_level and user_profile_data.education_level.value in ['bachelors', 'masters', 'phd'],
        field_of_study=user_profile_data.field_of_study,
        education_details=user_profile_data.education_level.value if user_profile_data.education_level else 'bachelors'
    )
    
    return AnalysisRequest(
        job_title=evaluation_job_data.get('title', ''),
        company=evaluation_job_data.get('company', ''),
        job_description=evaluation_job_data.get('description', ''),
        ai_settings=ai_settings,
        user_profile=user_profile,
        resume_data=resume_data,
        resume_text=resume_data.get('resume_text') if resume_data else None,
        years_experience=user_profile_data.years_of_experience,
        experience_level=user_profile_data.experience_level.value if user_profile_data.experience_level else None,
        skills=user_profile_data.skills_technologies or [],
        education_level=user_profile_data.education_level.value if user_profile_data.education_level else None,
        field_of_study=user_profile_data.field_of_study,
        education_details=user_profile_data.education_level.value if user_profile_data.education_level else None,
        work_arrangement=user_profile_data.work_arrangement_preference.value if user_profile_data.work_arrangement_preference else None,
        preferred_locations=user_profile_data.preferred_locations or [],
        salary_min=user_profile_data.salary_min,
        salary_max=user_profile_data.salary_max
    )

def perform_enhanced_job_evaluation(qualification_analyzer, evaluation_job_data, user_profile_data, ai_settings, resume_data=None, max_retries=2):
    """
    Perform enhanced job evaluation using the new weighted scoring system.
    
    Args:
        qualification_analyzer: The QualificationAnalyzer instance
        evaluation_job_data: Job data dictionary
        user_profile_data: User profile data from database
        ai_settings: AI configuration
        resume_data: Optional resume data
        max_retries: Maximum retry attempts
        
    Returns:
        JobEvaluationResult with enhanced scoring
    """
    from src.ai.qualification_analyzer import JobEvaluationResult, DailyQuotaExhaustedException
    
    try:
        # Create enhanced analysis request
        analysis_request = create_enhanced_analysis_request(
            evaluation_job_data, user_profile_data, ai_settings, resume_data
        )
        
        # Perform enhanced analysis
        analysis_response = qualification_analyzer.analyze_job_qualification_with_retry(
            analysis_request, max_retries=max_retries
        )
        
        # Create qualification result
        qualification_result = qualification_analyzer.create_qualification_result(
            job_id=evaluation_job_data.get('id', ''),
            job_title=evaluation_job_data.get('title', ''),
            company=evaluation_job_data.get('company', ''),
            linkedin_url=evaluation_job_data.get('linkedin_url', ''),
            analysis_response=analysis_response
        )
        
        return JobEvaluationResult(
            success=True,
            qualification_result=qualification_result,
            attempts=1,
            job_id=evaluation_job_data.get('id', ''),
            job_title=evaluation_job_data.get('title', '')
        )
    
    except DailyQuotaExhaustedException as e:
        # Handle daily quota exhaustion specially
        logger.error(f"🛑 Daily quota exhausted: {e}")
        error_msg = "Daily AI analysis limit reached (200 requests for free tier). Please wait until tomorrow or upgrade your Gemini API plan."
        return JobEvaluationResult(
            success=False,
            qualification_result=None,
            attempts=1,  # Don't count retries for quota exhaustion
            error_message=error_msg,
            job_id=evaluation_job_data.get('id', ''),
            job_title=evaluation_job_data.get('title', '')
        )
        
    except Exception as e:
        logger.error(f"Enhanced job evaluation failed: {e}")
        return JobEvaluationResult(
            success=False,
            qualification_result=None,
            attempts=max_retries + 1,
            error_message=str(e),
            job_id=evaluation_job_data.get('id', ''),
            job_title=evaluation_job_data.get('title', '')
        )

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-change-this')

# Initialize emergency cache
cache = Cache(config={'CACHE_TYPE': 'simple'})
cache.init_app(app)

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
resume_manager = None

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
    global config_manager, job_processor, qualification_analyzer, resume_manager
    
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
        

        
        # Initialize resume manager with Supabase integration
        try:
            from supabase import create_client
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')  # CHANGED: Use service role key
            
            if supabase_url and supabase_service_key:
                supabase_client = create_client(supabase_url, supabase_service_key)  # CHANGED: Use service key
                resume_manager = ResumeManager(
                    supabase_client=supabase_client,
                    bucket_name="resumes",
                    ai_client=qualification_analyzer
                )
                logger.info("ResumeManager initialized with Supabase integration (service role)")
                
                # Store in app config for routes to access
                app.config['resume_manager'] = resume_manager
                
            else:
                logger.error("Supabase URL or service role key not found in environment variables")
                logger.error("Required: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
                raise Exception("Missing Supabase credentials")
                
        except Exception as e:
            logger.error(f"Error initializing ResumeManager: {e}")
            raise
        
        logger.info("System components initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing system components: {e}")
        raise


def allowed_file(filename):
    """Check if file extension is allowed."""
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Register authentication blueprint
from auth_routes import auth_bp
app.register_blueprint(auth_bp)

# Register profile blueprint
app.register_blueprint(profile_bp, url_prefix='/profile')

# Register resume blueprint
from resume_routes import resume_bp
app.register_blueprint(resume_bp)

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

@app.route('/resume/status')
@login_required
def get_resume_status():
    """Get resume processing status using Supabase."""
    try:
        logger.info("=== get_resume_status route called ===")
        user = get_current_user()
        logger.info(f"User: {user}")
        if not user:
            logger.error("No user found")
            return jsonify({'success': False, 'error': 'User not authenticated'})
        
        # Use the new resume manager for status
        resume_manager = app.config.get('resume_manager')
        logger.info(f"Resume manager: {resume_manager}")
        if not resume_manager:
            logger.error("Resume manager not available")
            return jsonify({'success': False, 'error': 'Resume manager not available'})
        
        # Get user ID - try both 'user_id' and 'id' fields
        user_id = user.get('user_id') or user.get('id')
        logger.info(f"User ID: {user_id}")
        if not user_id:
            logger.error(f"No user ID found in user data: {user}")
            return jsonify({'success': False, 'error': 'User ID not found'})
        
        logger.info(f"Calling resume_manager.get_resume_status({user_id})")
        status = resume_manager.get_resume_status(user_id)
        logger.info(f"Resume status result: {status}")
        
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        logger.error(f"Resume status error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
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
        
        linkedin_url = request.form.get('linkedin_url', '').strip()
        
        if not linkedin_url:
            return jsonify({'success': False, 'error': 'Job URL is required'})
        
        # Get profile data for analysis using authenticated database manager
        db_manager = get_authenticated_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available or user not authenticated'})
        
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
            processed_url = job_processor.process_url(linkedin_url)
            
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


# @app.route('/search/linkedin', methods=['POST'])
# @login_required
# def search_linkedin_jobs():
#     """Search LinkedIn jobs and save to database."""
#     try:
#         user = get_current_user()
#         if not user:
#             return jsonify({'success': False, 'error': 'User not authenticated'})
        
#         keywords = request.form.get('keywords', '').strip()
#         location = request.form.get('location', '').strip()
#         max_jobs = int(request.form.get('max_jobs', 10))
        
#         if not keywords:
#             return jsonify({'success': False, 'error': 'Keywords are required'})
        
#         # Create search record using authenticated database manager
#         db_manager = get_authenticated_db_manager()
#         if not db_manager:
#             return jsonify({'success': False, 'error': 'Database not available or user not authenticated'})
        
#         # Ensure user profile exists (create if it doesn't)
#         user_profile = db_manager.profiles.get_profile(user['user_id'])
#         if not user_profile:
#             # Create a basic user profile if it doesn't exist
#             basic_profile_data = {
#                 'experience_level': 'entry',
#                 'education_level': 'bachelors',
#                 'years_of_experience': 0,
#                 'work_arrangement_preference': 'any'
#             }
#             success, message, profile = db_manager.profiles.create_profile(user['user_id'], basic_profile_data)
#             if not success:
#                 return jsonify({'success': False, 'error': f'Failed to create user profile: {message}'})
#             logger.info(f"Created basic user profile for user {user['user_id']}")
        
#         # Check and process resume if available
#         if resume_manager:
#             try:
#                 resume_status = resume_manager.get_resume_status(user['user_id'])
#                 if resume_status['has_resume'] and not resume_status['is_processed']:
#                     logger.info(f"Processing resume for user {user['user_id']}")
#                     processed_resume = resume_manager.ensure_resume_processed(user['user_id'])
#                     if processed_resume:
#                         logger.info(f"Resume processed successfully for user {user['user_id']}")
#                     else:
#                         logger.warning(f"Failed to process resume for user {user['user_id']}")
#                 elif resume_status['has_resume'] and resume_status['is_processed']:
#                     logger.info(f"Resume already processed for user {user['user_id']}")
#                 else:
#                     logger.info(f"No resume found for user {user['user_id']}")
#             except Exception as e:
#                 logger.error(f"Error processing resume for user {user['user_id']}: {e}")
        
#         # Convert keywords to array format for database
#         keywords_array = [keywords] if keywords else []
        
#         search_data = {
#             'user_id': user['user_id'],
#             'keywords': keywords_array,
#             'location': location,
#             'filters': {},
#             'results_count': 0,
#             'search_date': datetime.now().isoformat()
#         }
        
#         success, message, search_record = db_manager.searches.create_search(search_data)
        
#         if not success:
#             return jsonify({'success': False, 'error': f'Failed to create search record: {message}'})
        
#         # Implement actual LinkedIn scraping
#         try:
#             # Initialize config manager first
#             from src.config.config_manager import ConfigurationManager
#             config_manager = ConfigurationManager()
            
#             # Get LinkedIn credentials from config
#             linkedin_username = config_manager.get_linkedin_settings().username if config_manager else None
#             linkedin_password = config_manager.get_linkedin_settings().password if config_manager else None
            
#             if not linkedin_username or not linkedin_password:
#                 logger.warning("LinkedIn credentials not configured, using mock data")
#                 # Fall back to mock data if credentials not available
#                 mock_jobs = [
#                     {
#                         'job_title': f'Software Engineer - {keywords}',
#                         'company_name': 'Tech Company',
#                         'location': location or 'Remote',
#                         'job_description': f'Looking for a {keywords} developer...',
#                         'job_url': 'https://example.com/job1',
#                         'date_posted': datetime.now().isoformat(),
#                         'work_arrangement': 'Remote',
#                         'experience_level': 'Mid-level',
#                         'job_type': 'Full-time'
#                     }
#                 ]
                
#                 # Save mock jobs to database
#                 saved_jobs = []
#                 for job_data in mock_jobs:
#                     job_data['user_id'] = user['user_id']
#                     job_data['date_found'] = datetime.now().isoformat()
                    
#                     success, message, job = db_manager.jobs.create_job(job_data)
#                     if success and job:
#                         saved_jobs.append(job)
                
#                 # Update search results count
#                 db_manager.searches.update_search_results(search_record.search_id, user['user_id'], len(saved_jobs))
                
#                 return jsonify({
#                     'success': True,
#                     'message': f'Found and saved {len(saved_jobs)} jobs (mock data - LinkedIn credentials not configured)',
#                     'jobs_count': len(saved_jobs),
#                     'search_id': search_record.search_id
#                 })
            
#             # Import search strategy manager and CAPTCHA handler
#             from src.utils.search_strategy_manager import search_strategy_manager
#             from src.utils.captcha_handler import captcha_handler
            
#             # Get additional filters from request
#             date_posted = request.form.get('date_posted')
#             work_arrangement = request.form.get('work_arrangement')
#             experience_level = request.form.get('experience_level')
#             job_type = request.form.get('job_type')
            
#             # Convert date_posted to days
#             date_posted_days = None
#             if date_posted and date_posted != 'any':
#                 date_mapping = {
#                     '1': 1,
#                     '3': 3,
#                     '7': 7,
#                     '14': 14,
#                     '30': 30
#                 }
#                 date_posted_days = date_mapping.get(date_posted)
            
#             # Determine search strategy based on filters
#             search_params = search_strategy_manager.create_search_parameters_from_dict({
#                 'keywords': [keywords],
#                 'location': location,
#                 'date_posted_days': date_posted_days,
#                 'work_arrangement': work_arrangement,
#                 'experience_level': experience_level,
#                 'job_type': job_type
#             })
            
#             strategy_info = search_strategy_manager.get_search_strategy_info(search_params)
#             logger.info(f"Search strategy: {strategy_info['method']} - {strategy_info['reason']}")
            
#             # Choose appropriate scraper based on strategy
#             if strategy_info['method'] == 'api_only':
#                 # Use API-only scraper for basic searches
#                 from src.scrapers.linkedin_api_scraper import create_linkedin_api_scraper
#                 from src.scrapers.base_scraper import ScrapingConfig
                
#                 # Create proper ScrapingConfig for API scraper
#                 scraping_settings = config_manager.get_scraping_settings()
#                 scraping_config = ScrapingConfig(
#                     site_name="linkedin",
#                     base_url="https://www.linkedin.com",
#                     delay_min=scraping_settings.delay_min,
#                     delay_max=scraping_settings.delay_max,
#                     max_jobs_per_session=scraping_settings.max_jobs_per_session,
#                     respect_robots_txt=scraping_settings.respect_robots_txt,
#                     request_timeout=scraping_settings.timeout,
#                     max_retries=scraping_settings.retry_attempts
#                 )
#                 scraper = create_linkedin_api_scraper(scraping_config)
#                 logger.info("Using API-only scraper for fast execution")
#             else:
#                 # Use WebDriver scraper for advanced searches
#                 from src.scrapers.linkedin_scraper_enhanced import create_enhanced_linkedin_scraper
                
#                 scraper = create_enhanced_linkedin_scraper(
#                     username=linkedin_username,
#                     password=linkedin_password,
#                     use_persistent_session=True
#                 )
#                 logger.info("Using WebDriver scraper for advanced filters")
            
#             # Prepare search parameters
#             search_keywords = [keywords] if keywords else []
#             search_location = location or ""
            
#             logger.info(f"Starting LinkedIn scraping for keywords: {search_keywords} in {search_location}")
            
#             # Perform the scraping
#             if strategy_info['method'] == 'api_only':
#                 # Use API-only scraping method
#                 scraping_result = scraper.scrape_jobs(
#                     keywords=search_keywords,
#                     location=search_location
#                 )
#             else:
#                 # Use WebDriver scraping method with enhanced date filter
#                 scraping_result = scraper.scrape_jobs_with_enhanced_date_filter(
#                     keywords=search_keywords,
#                     location=search_location,
#                     date_posted_days=date_posted_days,
#                     work_arrangement=work_arrangement,
#                     experience_level=experience_level,
#                     job_type=job_type
#                 )
            
#             if not scraping_result.success:
#                 # Check if it's a CAPTCHA challenge
#                 if "captcha" in scraping_result.error_message.lower() or "puzzle" in scraping_result.error_message.lower():
#                     return jsonify({
#                         'error': 'CAPTCHA_CHALLENGE',
#                         'message': 'LinkedIn requires manual verification. Please complete the security challenge in the browser window and try again.',
#                         'requires_manual_intervention': True,
#                         'strategy_info': strategy_info
#                     })
                
#                 logger.error(f"LinkedIn scraping failed: {scraping_result.error_message}")
#                 return jsonify({
#                     'success': False,
#                     'error': f'LinkedIn scraping failed: {scraping_result.error_message}',
#                     'strategy_info': strategy_info
#                 })
            
#             # Convert scraped jobs to database format
#             saved_jobs = []
#             for job_listing in scraping_result.jobs:
#                 job_data = {
#                     'user_id': user['user_id'],
#                     'job_title': job_listing.title,
#                     'company_name': job_listing.company,
#                     'location': job_listing.location,
#                     'job_description': job_listing.description,
#                     'job_url': job_listing.job_url,
#                     'date_posted': job_listing.posted_date.isoformat() if job_listing.posted_date else None,
#                     'work_arrangement': job_listing.remote_type,
#                     'experience_level': job_listing.experience_level,
#                     'job_type': job_listing.job_type,
#                     'date_found': datetime.now().isoformat()
#                 }
                
#                 success, message, job = db_manager.jobs.create_job(job_data)
#                 if success and job:
#                     saved_jobs.append(job)
#                     logger.info(f"Saved job: {job_listing.title} at {job_listing.company}")
#                 else:
#                     logger.warning(f"Failed to save job: {message}")
            
#             # Update search results count
#             db_manager.searches.update_search_results(search_record.search_id, user['user_id'], len(saved_jobs))
            
#             # Clean up scraper
#             scraper.cleanup()
            
#             return jsonify({
#                 'success': True,
#                 'message': f'Found and saved {len(saved_jobs)} jobs from LinkedIn',
#                 'jobs_count': len(saved_jobs),
#                 'search_id': search_record.search_id,
#                 'scraping_metadata': scraping_result.metadata,
#                 'strategy_info': strategy_info
#             })
            
#         except Exception as e:
#             logger.error(f"Error during LinkedIn scraping: {e}")
#             return jsonify({
#                 'success': False,
#                 'error': f'LinkedIn scraping error: {str(e)}'
#             })
        
#     except Exception as e:
#         logger.error(f"LinkedIn search error: {e}")
#         return jsonify({'success': False, 'error': str(e)})


# @app.route('/search/linkedin/captcha', methods=['POST'])
# @login_required
# def continue_after_captcha():
#     """Continue LinkedIn search after CAPTCHA has been solved."""
#     try:
#         user = get_current_user()
#         if not user:
#             return jsonify({'success': False, 'error': 'User not authenticated'})
        
#         # Get original search parameters from session or request
#         keywords = request.form.get('keywords', '').strip()
#         location = request.form.get('location', '').strip()
#         date_posted = request.form.get('date_posted')
#         work_arrangement = request.form.get('work_arrangement')
#         experience_level = request.form.get('experience_level')
#         job_type = request.form.get('job_type')
        
#         if not keywords:
#             return jsonify({'success': False, 'error': 'Keywords are required'})
        
#         # Get LinkedIn credentials
#         from src.config.config_manager import ConfigurationManager
#         config_manager = ConfigurationManager()
#         linkedin_username = config_manager.get_linkedin_settings().username if config_manager else None
#         linkedin_password = config_manager.get_linkedin_settings().password if config_manager else None
        
#         if not linkedin_username or not linkedin_password:
#             return jsonify({'success': False, 'error': 'LinkedIn credentials not configured'})
        
#         # Import required modules
#         from src.utils.search_strategy_manager import search_strategy_manager
#         from src.scrapers.linkedin_scraper_enhanced import create_enhanced_linkedin_scraper
        
#         # Convert date_posted to days
#         date_posted_days = None
#         if date_posted and date_posted != 'any':
#             date_mapping = {
#                 '1': 1, '3': 3, '7': 7, '14': 14, '30': 30
#             }
#             date_posted_days = date_mapping.get(date_posted)
        
#         # Create search parameters
#         search_params = search_strategy_manager.create_search_parameters_from_dict({
#             'keywords': [keywords],
#             'location': location,
#             'date_posted_days': date_posted_days,
#             'work_arrangement': work_arrangement,
#             'experience_level': experience_level,
#             'job_type': job_type
#         })
        
#         # Create WebDriver scraper for CAPTCHA continuation
#         scraper = create_enhanced_linkedin_scraper(
#             username=linkedin_username,
#             password=linkedin_password,
#             use_persistent_session=True
#         )
        
#         # Prepare search parameters
#         search_keywords = [keywords] if keywords else []
#         search_location = location or ""
        
#         # Perform the scraping with WebDriver (since CAPTCHA was solved)
#         scraping_result = scraper.scrape_jobs_with_enhanced_date_filter(
#             keywords=search_keywords,
#             location=search_location,
#             date_posted_days=date_posted_days,
#             work_arrangement=work_arrangement,
#             experience_level=experience_level,
#             job_type=job_type
#         )
        
#         if not scraping_result.success:
#             logger.error(f"LinkedIn scraping failed after CAPTCHA: {scraping_result.error_message}")
#             return jsonify({
#                 'success': False,
#                 'error': f'LinkedIn scraping failed after CAPTCHA: {scraping_result.error_message}'
#             })
        
#         # Convert scraped jobs to database format and save
#         db_manager = get_authenticated_db_manager()
#         if not db_manager:
#             return jsonify({'success': False, 'error': 'Database not available'})
        
#         saved_jobs = []
#         for job_listing in scraping_result.jobs:
#             job_data = {
#                 'user_id': user['user_id'],
#                 'job_title': job_listing.title,
#                 'company_name': job_listing.company,
#                 'location': job_listing.location,
#                 'job_description': job_listing.description,
#                 'job_url': job_listing.job_url,
#                 'date_posted': job_listing.posted_date.isoformat() if job_listing.posted_date else None,
#                 'work_arrangement': job_listing.remote_type,
#                 'experience_level': job_listing.experience_level,
#                 'job_type': job_listing.job_type,
#                 'date_found': datetime.now().isoformat()
#             }
            
#             success, message, job = db_manager.jobs.create_job(job_data)
#             if success and job:
#                 saved_jobs.append(job)
        
#         # Clean up scraper
#         scraper.cleanup()
        
#         return jsonify({
#             'success': True,
#             'message': f'Successfully found and saved {len(saved_jobs)} jobs after CAPTCHA verification',
#             'jobs_count': len(saved_jobs),
#             'captcha_solved': True
#         })
        
#     except Exception as e:
#         logger.error(f"CAPTCHA continuation error: {e}")
#         return jsonify({'success': False, 'error': f'CAPTCHA continuation failed: {str(e)}'})

@app.route('/search/linkedin', methods=['POST'])
@login_required
def search_linkedin_jobs():
    """Search LinkedIn jobs and save to database with proper CAPTCHA handling."""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'User not authenticated'})
        
        keywords = request.form.get('keywords', '').strip()
        location = request.form.get('location', '').strip()
        max_jobs = int(request.form.get('max_jobs', 10))
        
        if not keywords:
            return jsonify({'success': False, 'error': 'Keywords are required'})
        
        # Create search record using authenticated database manager
        db_manager = get_authenticated_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available or user not authenticated'})
        
        # Ensure user profile exists (create if it doesn't)
        user_profile = db_manager.profiles.get_profile(user['user_id'])
        if not user_profile:
            basic_profile_data = {
                'experience_level': 'entry',
                'education_level': 'bachelors',
                'years_of_experience': 0,
                'work_arrangement_preference': 'any'
            }
            success, message, profile = db_manager.profiles.create_profile(user['user_id'], basic_profile_data)
            if not success:
                return jsonify({'success': False, 'error': f'Failed to create user profile: {message}'})
            logger.info(f"Created basic user profile for user {user['user_id']}")
        
        # Check and process resume if available - this is critical for job evaluation
        resume_data = None
        if resume_manager:
            try:
                resume_status = resume_manager.get_resume_status(user['user_id'])
                if resume_status['has_resume'] and not resume_status['is_processed']:
                    logger.info(f"Processing resume for user {user['user_id']} before job evaluation")
                    processed_resume = resume_manager.ensure_resume_processed(user['user_id'])
                    if processed_resume:
                        logger.info(f"Resume processed successfully for user {user['user_id']}")
                        resume_data = processed_resume
                    else:
                        logger.warning(f"Failed to process resume for user {user['user_id']}")
                elif resume_status['has_resume'] and resume_status['is_processed']:
                    logger.info(f"Resume already processed for user {user['user_id']}")
                    # Get the processed resume data for job evaluation
                    resume_data = resume_manager.get_latest_user_resume(user['user_id'])
                    if resume_data and resume_data.processed_data:
                        resume_data = resume_data.processed_data
                else:
                    logger.info(f"No resume found for user {user['user_id']}")
            except Exception as e:
                logger.error(f"Error processing resume for user {user['user_id']}: {e}")
        
        # Convert keywords to array format for database
        keywords_array = [keywords] if keywords else []
        
        search_data = {
            'user_id': user['user_id'],
            'keywords': keywords_array,
            'location': location,
            'filters': {},
            'results_count': 0,
            'search_date': datetime.now().isoformat()
        }
        
        success, message, search_record = db_manager.searches.create_search(search_data)
        
        if not success:
            return jsonify({'success': False, 'error': f'Failed to create search record: {message}'})
        
        # Implement actual LinkedIn scraping with proper CAPTCHA handling
        try:
            # Initialize config manager first
            from src.config.config_manager import ConfigurationManager
            config_manager = ConfigurationManager()
            
            # Get LinkedIn credentials from config
            linkedin_username = config_manager.get_linkedin_settings().username if config_manager else None
            linkedin_password = config_manager.get_linkedin_settings().password if config_manager else None
            
            if not linkedin_username or not linkedin_password:
                logger.warning("LinkedIn credentials not configured, using mock data")
                # Fall back to mock data (existing code remains the same)
                mock_jobs = [
                    {
                        'job_title': f'Software Engineer - {keywords}',
                        'company_name': 'Tech Company',
                        'location': location or 'Remote',
                        'job_description': f'Looking for a {keywords} developer...',
                        'linkedin_url': 'https://www.linkedin.com/jobs/view/example1',
                        'job_url': '',  # Clear job_url field
                        'date_posted': datetime.now().isoformat(),
                        'work_arrangement': 'Remote',
                        'experience_level': 'Mid-level',
                        'job_type': 'Full-time'
                    }
                ]
                
                saved_jobs = []
                for job_data in mock_jobs:
                    job_data['user_id'] = user['user_id']
                    job_data['date_found'] = datetime.now().isoformat()
                    
                    success, message, job = db_manager.jobs.create_job(job_data)
                    if success and job:
                        saved_jobs.append(job)
                
                db_manager.searches.update_search_results(search_record.search_id, user['user_id'], len(saved_jobs))
                
                return jsonify({
                    'success': True,
                    'message': f'Found and saved {len(saved_jobs)} jobs (mock data - LinkedIn credentials not configured)',
                    'jobs_count': len(saved_jobs),
                    'search_id': search_record.search_id
                })
            
            # Import search strategy manager and CAPTCHA handler
            from src.utils.search_strategy_manager import search_strategy_manager
            from src.utils.captcha_handler import captcha_handler
            
            # Get additional filters from request
            date_posted = request.form.get('date_posted')
            work_arrangement = request.form.get('work_arrangement')
            experience_level = request.form.get('experience_level')
            job_type = request.form.get('job_type')
            
            # Convert date_posted to days
            date_posted_days = None
            if date_posted and date_posted != 'any':
                date_mapping = {'1': 1, '3': 3, '7': 7, '14': 14, '30': 30}
                date_posted_days = date_mapping.get(date_posted)
            
            # Determine search strategy based on filters
            search_params = search_strategy_manager.create_search_parameters_from_dict({
                'keywords': [keywords],
                'location': location,
                'date_posted_days': date_posted_days,
                'work_arrangement': work_arrangement,
                'experience_level': experience_level,
                'job_type': job_type
            })
            
            strategy_info = search_strategy_manager.get_search_strategy_info(search_params)
            logger.info(f"Search strategy: {strategy_info['method']} - {strategy_info['reason']}")
            
            # Choose appropriate scraper based on strategy
            scraper = None
            if strategy_info['method'] == 'api_only':
                # Use API-only scraper for basic searches
                from src.scrapers.linkedin_api_scraper import create_linkedin_api_scraper
                from src.scrapers.base_scraper import ScrapingConfig
                
                scraping_settings = config_manager.get_scraping_settings()
                scraping_config = ScrapingConfig(
                    site_name="linkedin",
                    base_url="https://www.linkedin.com",
                    delay_min=scraping_settings.delay_min,
                    delay_max=scraping_settings.delay_max,
                    max_jobs_per_session=scraping_settings.max_jobs_per_session,
                    respect_robots_txt=scraping_settings.respect_robots_txt,
                    request_timeout=scraping_settings.timeout,
                    max_retries=scraping_settings.retry_attempts
                )
                scraper = create_linkedin_api_scraper(scraping_config)
                logger.info("Using API-only scraper for fast execution")
                
                # Perform API-only scraping (no CAPTCHA handling needed)
                search_keywords = [keywords] if keywords else []
                search_location = location or ""
                
                scraping_result = scraper.scrape_jobs(
                    keywords=search_keywords,
                    location=search_location
                )
                
            else:
                # Use WebDriver scraper for advanced searches with CAPTCHA handling
                from src.scrapers.linkedin_scraper_enhanced import create_enhanced_linkedin_scraper
                
                scraper = create_enhanced_linkedin_scraper(
                    username=linkedin_username,
                    password=linkedin_password,
                    use_persistent_session=True
                )
                
                # PROPER CAPTCHA INTEGRATION: Set up CAPTCHA handler BEFORE scraping
                if hasattr(scraper, 'driver') and scraper.driver:
                    captcha_handler.set_driver(scraper.driver)
                    captcha_handler.set_timeout(600)  # 10 minutes timeout
                    logger.info("CAPTCHA handler configured with WebDriver")
                    
                    # Check for CAPTCHA immediately after driver setup
                    captcha_info = captcha_handler.detect_captcha()
                    
                    if captcha_info.status == CAPTCHAStatus.DETECTED:
                        logger.warning(f"CAPTCHA detected before scraping: {captcha_info.message}")
                        
                        # Return proper CAPTCHA challenge response
                        instructions = captcha_handler._generate_user_instructions(captcha_info)
                        
                        return jsonify({
                            'success': False,
                            'error': 'CAPTCHA_CHALLENGE',
                            'captcha_detected': True,
                            'captcha_info': {
                                'type': captcha_info.captcha_type,
                                'message': captcha_info.message,
                                'timeout_seconds': captcha_info.timeout_seconds
                            },
                            'instructions': instructions,
                            'requires_manual_intervention': True,
                            'strategy_info': strategy_info,
                            'search_params': {
                                'keywords': keywords,
                                'location': location,
                                'date_posted': date_posted,
                                'work_arrangement': work_arrangement,
                                'experience_level': experience_level,
                                'job_type': job_type
                            }
                        })
                
                logger.info("Using WebDriver scraper for advanced filters with CAPTCHA handling")
                
                # ENHANCED CAPTCHA HANDLING: Check for CAPTCHA during authentication
                # The scraper will handle authentication internally, but we need to catch CAPTCHA challenges
                try:
                    # Prepare search parameters
                    search_keywords = [keywords] if keywords else []
                    search_location = location or ""
                    
                    # Perform WebDriver scraping with CAPTCHA monitoring
                    scraping_result = scraper.scrape_jobs_with_enhanced_date_filter(
                        keywords=search_keywords,
                        location=search_location,
                        date_posted_days=date_posted_days,
                        work_arrangement=work_arrangement,
                        experience_level=experience_level,
                        job_type=job_type
                    )
                    
                    # Check if the result indicates a CAPTCHA challenge
                    if not scraping_result.success and 'CAPTCHA_CHALLENGE' in scraping_result.error_message:
                        logger.warning("CAPTCHA challenge detected during scraping")
                        
                        # Get current CAPTCHA info
                        captcha_info = captcha_handler.detect_captcha()
                        instructions = captcha_handler._generate_user_instructions(captcha_info)
                        
                        return jsonify({
                            'success': False,
                            'error': 'CAPTCHA_CHALLENGE',
                            'captcha_detected': True,
                            'captcha_info': {
                                'type': captcha_info.captcha_type,
                                'message': captcha_info.message,
                                'timeout_seconds': captcha_info.timeout_seconds
                            },
                            'instructions': instructions,
                            'requires_manual_intervention': True,
                            'strategy_info': strategy_info,
                            'search_params': {
                                'keywords': keywords,
                                'location': location,
                                'date_posted': date_posted,
                                'work_arrangement': work_arrangement,
                                'experience_level': experience_level,
                                'job_type': job_type
                            }
                        })
                    
                except Exception as scraping_error:
                    # Check for CAPTCHA if scraping fails
                    if hasattr(scraper, 'driver') and scraper.driver:
                        captcha_info = captcha_handler.detect_captcha()
                        
                        if captcha_info.status == CAPTCHAStatus.DETECTED:
                            logger.warning(f"CAPTCHA detected during scraping error: {captcha_info.message}")
                            
                            instructions = captcha_handler._generate_user_instructions(captcha_info)
                            
                            return jsonify({
                                'success': False,
                                'error': 'CAPTCHA_CHALLENGE',
                                'captcha_detected': True,
                                'captcha_info': {
                                    'type': captcha_info.captcha_type,
                                    'message': captcha_info.message,
                                    'timeout_seconds': captcha_info.timeout_seconds
                                },
                                'instructions': instructions,
                                'requires_manual_intervention': True,
                                'strategy_info': strategy_info,
                                'search_params': {
                                    'keywords': keywords,
                                    'location': location,
                                    'date_posted': date_posted,
                                    'work_arrangement': work_arrangement,
                                    'experience_level': experience_level,
                                    'job_type': job_type
                                }
                            })
                    
                    # Re-raise if not CAPTCHA-related
                    raise scraping_error
            
            # Handle scraping results
            if not scraping_result or not scraping_result.success:
                # Check if the error is CAPTCHA-related
                if scraping_result and 'CAPTCHA_CHALLENGE' in scraping_result.error_message:
                    logger.warning("CAPTCHA challenge detected in scraping result")
                    
                    # Get current CAPTCHA info
                    captcha_info = captcha_handler.detect_captcha()
                    instructions = captcha_handler._generate_user_instructions(captcha_info)
                    
                    return jsonify({
                        'success': False,
                        'error': 'CAPTCHA_CHALLENGE',
                        'captcha_detected': True,
                        'captcha_info': {
                            'type': captcha_info.captcha_type,
                            'message': captcha_info.message,
                            'timeout_seconds': captcha_info.timeout_seconds
                        },
                        'instructions': instructions,
                        'requires_manual_intervention': True,
                        'strategy_info': strategy_info,
                        'search_params': {
                            'keywords': keywords,
                            'location': location,
                            'date_posted': date_posted,
                            'work_arrangement': work_arrangement,
                            'experience_level': experience_level,
                            'job_type': job_type
                        }
                    })
                
                # Final CAPTCHA check for WebDriver failures
                if strategy_info['method'] == 'webdriver' and hasattr(scraper, 'driver') and scraper.driver:
                    captcha_info = captcha_handler.detect_captcha()
                    
                    if captcha_info.status == CAPTCHAStatus.DETECTED:
                        logger.warning(f"CAPTCHA detected after scraping failure: {captcha_info.message}")
                        
                        instructions = captcha_handler._generate_user_instructions(captcha_info)
                        
                        return jsonify({
                            'success': False,
                            'error': 'CAPTCHA_CHALLENGE',
                            'captcha_detected': True,
                            'captcha_info': {
                                'type': captcha_info.captcha_type,
                                'message': captcha_info.message,
                                'timeout_seconds': captcha_info.timeout_seconds
                            },
                            'instructions': instructions,
                            'requires_manual_intervention': True,
                            'strategy_info': strategy_info,
                            'search_params': {
                                'keywords': keywords,
                                'location': location,
                                'date_posted': date_posted,
                                'work_arrangement': work_arrangement,
                                'experience_level': experience_level,
                                'job_type': job_type
                            }
                        })
                
                error_msg = scraping_result.error_message if scraping_result else "Unknown scraping error"
                logger.error(f"LinkedIn scraping failed: {error_msg}")
                return jsonify({
                    'success': False,
                    'error': f'LinkedIn scraping failed: {error_msg}',
                    'strategy_info': strategy_info
                })
            
            # Convert scraped jobs to database format and evaluate them
            saved_jobs = []
            evaluated_jobs = []
            
            # Get user profile for evaluation
            user_profile_data = db_manager.profiles.get_profile(user['user_id'])
            if not user_profile_data:
                logger.warning(f"No user profile found for user {user['user_id']}, skipping job evaluation")
                user_profile = None
            else:
                # Create UserProfile object for evaluation
                from src.config.config_manager import UserProfile, AISettings
                user_profile = UserProfile(
                    years_of_experience=user_profile_data.years_of_experience or 0,
                    experience_level=user_profile_data.experience_level.value if user_profile_data.experience_level else 'entry',
                    additional_skills=user_profile_data.skills_technologies or [],
                    preferred_locations=user_profile_data.preferred_locations or [],
                    salary_min=user_profile_data.salary_min,
                    salary_max=user_profile_data.salary_max,
                    remote_preference=user_profile_data.work_arrangement_preference.value if user_profile_data.work_arrangement_preference else 'any',
                    has_college_degree=user_profile_data.education_level and user_profile_data.education_level.value in ['bachelors', 'masters', 'phd'],
                    field_of_study=user_profile_data.field_of_study,
                    education_details=user_profile_data.education_level.value if user_profile_data.education_level else 'bachelors'
                )
                
                # Get AI settings
                ai_settings = config_manager.get_ai_settings()
            
            # Process each scraped job
            for job_listing in scraping_result.jobs:
                job_data = {
                    'user_id': user['user_id'],
                    'job_title': job_listing.title,
                    'company_name': job_listing.company,
                    'location': job_listing.location,
                    'job_description': job_listing.description,
                    'linkedin_url': job_listing.linkedin_url,  # Use linkedin_url field
                    'job_url': job_listing.application_url,  # Save application URL as job_url
                    'date_posted': job_listing.posted_date.isoformat() if job_listing.posted_date else None,
                    'work_arrangement': job_listing.work_arrangement,  # Use new work_arrangement field
                    'experience_level': job_listing.experience_level,
                    'job_type': job_listing.job_type,
                    'date_found': datetime.now().isoformat()
                }
                
                # Save job to database
                success, message, job = db_manager.jobs.create_job(job_data)
                if success and job:
                    saved_jobs.append(job)
                    logger.info(f"Saved job: {job_listing.title} at {job_listing.company}")
                    
                    # Evaluate job if user profile is available
                    if user_profile and ai_settings:
                        try:
                            # Initialize qualification analyzer if not already done
                            if not hasattr(app, 'qualification_analyzer'):
                                from src.ai.qualification_analyzer import QualificationAnalyzer
                                app.qualification_analyzer = QualificationAnalyzer(ai_settings)
                            
                            # Check if quota is available before attempting evaluation
                            quota_available, quota_message = app.qualification_analyzer.is_quota_available()
                            if not quota_available:
                                logger.warning(f"🛑 Stopping job evaluations: {quota_message}")
                                # Add message to response that evaluations were stopped
                                if 'quota_warning' not in session:
                                    session['quota_warning'] = quota_message
                                break  # Stop processing more jobs
                            
                            # Prepare job data for evaluation
                            evaluation_job_data = {
                                'id': job.job_id,
                                'title': job.job_title,
                                'company': job.company_name,
                                'description': job.job_description or '',
                                'linkedin_url': job.linkedin_url or ''
                            }
                            
                            # Evaluate job with enhanced weighted scoring
                            evaluation_result = perform_enhanced_job_evaluation(
                                app.qualification_analyzer, evaluation_job_data, user_profile_data, ai_settings, resume_data, max_retries=2
                            )
                            
                            if evaluation_result.success and evaluation_result.qualification_result:
                                # Save qualification result to existing jobs table fields
                                qual_result = evaluation_result.qualification_result
                                
                                # Update job with evaluation results
                                job_updates = {
                                    'gemini_evaluation': qual_result.ai_reasoning,
                                    'gemini_score': qual_result.qualification_score
                                }
                                
                                success, message, updated_job = db_manager.jobs.update_job(job.job_id, user['user_id'], job_updates)
                                if success:
                                    evaluated_jobs.append({
                                        'job_id': job.job_id,
                                        'job_title': job.job_title,
                                        'company': job.company_name,
                                        'qualification_score': qual_result.qualification_score,
                                        'qualification_status': qual_result.qualification_status.value
                                    })
                                    logger.info(f"✅ Evaluated job: {job.job_title} - Score: {qual_result.qualification_score}")
                                else:
                                    logger.warning(f"Failed to save evaluation to job: {message}")
                            else:
                                logger.warning(f"Job evaluation failed for {job.job_title}: {evaluation_result.error_message}")
                                
                        except Exception as eval_error:
                            logger.error(f"Error evaluating job {job.job_title}: {eval_error}")
                    else:
                        logger.info(f"Skipping evaluation for job {job.job_title} - no user profile or AI settings")
                else:
                    logger.warning(f"Failed to save job: {message}")
            
            # Update search results count
            db_manager.searches.update_search_results(search_record.search_id, user['user_id'], len(saved_jobs))
            
            # Clean up scraper
            if scraper:
                scraper.cleanup()
            
            # Prepare response
            response_data = {
                'success': True,
                'message': f'Found and saved {len(saved_jobs)} jobs from LinkedIn',
                'jobs_count': len(saved_jobs),
                'search_id': search_record.search_id,
                'scraping_metadata': scraping_result.metadata,
                'strategy_info': strategy_info
            }
            
            # Add evaluation results if available
            if evaluated_jobs:
                response_data['evaluated_jobs_count'] = len(evaluated_jobs)
                response_data['evaluation_summary'] = {
                    'total_evaluated': len(evaluated_jobs),
                    'highly_qualified': len([j for j in evaluated_jobs if j['qualification_status'] == 'highly_qualified']),
                    'qualified': len([j for j in evaluated_jobs if j['qualification_status'] == 'qualified']),
                    'somewhat_qualified': len([j for j in evaluated_jobs if j['qualification_status'] == 'somewhat_qualified']),
                    'not_qualified': len([j for j in evaluated_jobs if j['qualification_status'] == 'not_qualified'])
                }
                response_data['message'] += f' and evaluated {len(evaluated_jobs)} jobs'
            
            # Add quota warning if present
            if 'quota_warning' in session:
                response_data['quota_warning'] = session.pop('quota_warning')
                if len(evaluated_jobs) < len(saved_jobs):
                    response_data['message'] += f'. AI evaluation stopped due to quota limits.'
            
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"Error during LinkedIn scraping: {e}")
            return jsonify({
                'success': False,
                'error': f'LinkedIn scraping error: {str(e)}'
            })
        
    except Exception as e:
        logger.error(f"LinkedIn search error: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/search/linkedin/captcha', methods=['POST'])
@login_required
def continue_after_captcha():
    """Continue LinkedIn search after CAPTCHA has been solved using proper CAPTCHA handler."""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'User not authenticated'})
        
        # Get original search parameters from request
        keywords = request.form.get('keywords', '').strip()
        location = request.form.get('location', '').strip()
        date_posted = request.form.get('date_posted')
        work_arrangement = request.form.get('work_arrangement')
        experience_level = request.form.get('experience_level')
        job_type = request.form.get('job_type')
        
        if not keywords:
            return jsonify({'success': False, 'error': 'Keywords are required'})
        
        # Get LinkedIn credentials
        from src.config.config_manager import ConfigurationManager
        config_manager = ConfigurationManager()
        linkedin_username = config_manager.get_linkedin_settings().username if config_manager else None
        linkedin_password = config_manager.get_linkedin_settings().password if config_manager else None
        
        if not linkedin_username or not linkedin_password:
            return jsonify({'success': False, 'error': 'LinkedIn credentials not configured'})
        
        # Import required modules
        from src.utils.search_strategy_manager import search_strategy_manager
        from src.utils.captcha_handler import captcha_handler
        from src.scrapers.linkedin_scraper_enhanced import create_enhanced_linkedin_scraper
        
        # Convert date_posted to days
        date_posted_days = None
        if date_posted and date_posted != 'any':
            date_mapping = {'1': 1, '3': 3, '7': 7, '14': 14, '30': 30}
            date_posted_days = date_mapping.get(date_posted)
        
        # Create WebDriver scraper for CAPTCHA continuation
        scraper = None
        try:
            scraper = create_enhanced_linkedin_scraper(
                username=linkedin_username,
                password=linkedin_password,
                use_persistent_session=True
            )
            
            # PROPER CAPTCHA INTEGRATION: Set up CAPTCHA handler properly
            if hasattr(scraper, 'driver') and scraper.driver:
                captcha_handler.set_driver(scraper.driver)
                captcha_handler.set_timeout(600)  # 10 minutes timeout
                logger.info("CAPTCHA handler configured for continuation")
                
                # Detect current CAPTCHA status
                captcha_info = captcha_handler.detect_captcha()
                
                if captcha_info.status == CAPTCHAStatus.DETECTED:
                    logger.info("CAPTCHA still detected, checking if it has been solved...")
                    
                    # Use the non-blocking method to check if CAPTCHA has been solved
                    solved_status = captcha_handler.check_captcha_solved(captcha_info)
                    
                    if solved_status.status == CAPTCHAStatus.SOLVED:
                        logger.info("CAPTCHA has been solved, proceeding with scraping")
                    elif solved_status.status == CAPTCHAStatus.DETECTED:
                        logger.info("CAPTCHA still needs to be solved by user")
                        instructions = captcha_handler._generate_user_instructions(captcha_info)
                        
                        return jsonify({
                            'success': False,
                            'error': 'CAPTCHA_CHALLENGE',
                            'captcha_detected': True,
                            'captcha_info': {
                                'type': captcha_info.captcha_type,
                                'message': captcha_info.message,
                                'timeout_seconds': captcha_info.timeout_seconds
                            },
                            'instructions': instructions,
                            'requires_manual_intervention': True,
                            'message': 'Please complete the CAPTCHA challenge in the browser window'
                        })
                    else:
                        logger.error(f"CAPTCHA status error: {solved_status.message}")
                        return jsonify({
                            'success': False,
                            'error': 'CAPTCHA_ERROR',
                            'message': f'CAPTCHA status check failed: {solved_status.message}'
                        })
                    
                elif captcha_info.status == CAPTCHAStatus.NOT_DETECTED:
                    logger.info("No CAPTCHA detected, proceeding with scraping")
                    
                else:
                    logger.error(f"CAPTCHA detection error: {captcha_info.message}")
                    return jsonify({
                        'success': False,
                        'error': 'CAPTCHA_ERROR',
                        'message': f'CAPTCHA detection failed: {captcha_info.message}'
                    })
            
            # Prepare search parameters
            search_keywords = [keywords] if keywords else []
            search_location = location or ""
            
            logger.info(f"Proceeding with scraping after CAPTCHA handling: {search_keywords} in {search_location}")
            
            # Perform the scraping with WebDriver
            scraping_result = scraper.scrape_jobs_with_enhanced_date_filter(
                keywords=search_keywords,
                location=search_location,
                date_posted_days=date_posted_days,
                work_arrangement=work_arrangement,
                experience_level=experience_level,
                job_type=job_type
            )
            
            if not scraping_result.success:
                # Check for new CAPTCHA after scraping attempt
                captcha_info = captcha_handler.detect_captcha()
                
                if captcha_info.status == CAPTCHAStatus.DETECTED:
                    logger.warning("New CAPTCHA detected after scraping attempt")
                    instructions = captcha_handler._generate_user_instructions(captcha_info)
                    
                    return jsonify({
                        'success': False,
                        'error': 'CAPTCHA_CHALLENGE',
                        'captcha_detected': True,
                        'captcha_info': {
                            'type': captcha_info.captcha_type,
                            'message': captcha_info.message,
                            'timeout_seconds': captcha_info.timeout_seconds
                        },
                        'instructions': instructions,
                        'requires_manual_intervention': True
                    })
                
                logger.error(f"LinkedIn scraping failed after CAPTCHA: {scraping_result.error_message}")
                return jsonify({
                    'success': False,
                    'error': f'LinkedIn scraping failed after CAPTCHA: {scraping_result.error_message}'
                })
            
            # Convert scraped jobs to database format and evaluate them
            db_manager = get_authenticated_db_manager()
            if not db_manager:
                return jsonify({'success': False, 'error': 'Database not available'})
            
            saved_jobs = []
            evaluated_jobs = []
            
            # Get user profile for evaluation
            user_profile_data = db_manager.profiles.get_profile(user['user_id'])
            if not user_profile_data:
                logger.warning(f"No user profile found for user {user['user_id']}, skipping job evaluation")
                user_profile = None
            else:
                # Create UserProfile object for evaluation
                from src.config.config_manager import UserProfile, AISettings
                user_profile = UserProfile(
                    years_of_experience=user_profile_data.years_of_experience or 0,
                    experience_level=user_profile_data.experience_level.value if user_profile_data.experience_level else 'entry',
                    additional_skills=user_profile_data.skills_technologies or [],
                    preferred_locations=user_profile_data.preferred_locations or [],
                    salary_min=user_profile_data.salary_min,
                    salary_max=user_profile_data.salary_max,
                    remote_preference=user_profile_data.work_arrangement_preference.value if user_profile_data.work_arrangement_preference else 'any',
                    has_college_degree=user_profile_data.education_level and user_profile_data.education_level.value in ['bachelors', 'masters', 'phd'],
                    field_of_study=user_profile_data.field_of_study,
                    education_details=user_profile_data.education_level.value if user_profile_data.education_level else 'bachelors'
                )
                
                # Get AI settings
                ai_settings = config_manager.get_ai_settings()
            
            # Check and process resume if available - this is critical for job evaluation
            resume_data = None
            if resume_manager:
                try:
                    resume_status = resume_manager.get_resume_status(user['user_id'])
                    if resume_status['has_resume'] and not resume_status['is_processed']:
                        logger.info(f"Processing resume for user {user['user_id']} before job evaluation")
                        processed_resume = resume_manager.ensure_resume_processed(user['user_id'])
                        if processed_resume:
                            logger.info(f"Resume processed successfully for user {user['user_id']}")
                            resume_data = processed_resume
                        else:
                            logger.warning(f"Failed to process resume for user {user['user_id']}")
                    elif resume_status['has_resume'] and resume_status['is_processed']:
                        logger.info(f"Resume already processed for user {user['user_id']}")
                        # Get the processed resume data for job evaluation
                        resume_data = resume_manager.get_latest_user_resume(user['user_id'])
                        if resume_data and resume_data.processed_data:
                            resume_data = resume_data.processed_data
                    else:
                        logger.info(f"No resume found for user {user['user_id']}")
                except Exception as e:
                    logger.error(f"Error processing resume for user {user['user_id']}: {e}")
            
            # Process each scraped job
            for job_listing in scraping_result.jobs:
                job_data = {
                    'user_id': user['user_id'],
                    'job_title': job_listing.title,
                    'company_name': job_listing.company,
                    'location': job_listing.location,
                    'job_description': job_listing.description,
                    'linkedin_url': job_listing.linkedin_url,  # Use linkedin_url field
                    'job_url': job_listing.application_url,  # Save application URL as job_url
                    'date_posted': job_listing.posted_date.isoformat() if job_listing.posted_date else None,
                    'work_arrangement': job_listing.work_arrangement,  # Use new work_arrangement field
                    'experience_level': job_listing.experience_level,
                    'job_type': job_listing.job_type,
                    'date_found': datetime.now().isoformat()
                }
                
                # Save job to database
                success, message, job = db_manager.jobs.create_job(job_data)
                if success and job:
                    saved_jobs.append(job)
                    logger.info(f"Saved job after CAPTCHA: {job_listing.title} at {job_listing.company}")
                    
                    # Evaluate job if user profile is available
                    if user_profile and ai_settings:
                        try:
                            # Initialize qualification analyzer if not already done
                            if not hasattr(app, 'qualification_analyzer'):
                                from src.ai.qualification_analyzer import QualificationAnalyzer
                                app.qualification_analyzer = QualificationAnalyzer(ai_settings)
                            
                            # Prepare job data for evaluation
                            evaluation_job_data = {
                                'id': job.job_id,
                                'title': job.job_title,
                                'company': job.company_name,
                                'description': job.job_description or '',
                                'linkedin_url': job.linkedin_url or ''
                            }
                            
                            # Evaluate job with enhanced weighted scoring
                            evaluation_result = perform_enhanced_job_evaluation(
                                app.qualification_analyzer, evaluation_job_data, user_profile_data, ai_settings, resume_data, max_retries=2
                            )
                            
                            if evaluation_result.success and evaluation_result.qualification_result:
                                # Save qualification result to existing jobs table fields
                                qual_result = evaluation_result.qualification_result
                                
                                # Update job with evaluation results
                                job_updates = {
                                    'gemini_evaluation': qual_result.ai_reasoning,
                                    'gemini_score': qual_result.qualification_score
                                }
                                
                                success, message, updated_job = db_manager.jobs.update_job(job.job_id, user['user_id'], job_updates)
                                if success:
                                    evaluated_jobs.append({
                                        'job_id': job.job_id,
                                        'job_title': job.job_title,
                                        'company': job.company_name,
                                        'qualification_score': qual_result.qualification_score,
                                        'qualification_status': qual_result.qualification_status.value
                                    })
                                    logger.info(f"✅ Evaluated job after CAPTCHA: {job.job_title} - Score: {qual_result.qualification_score}")
                                else:
                                    logger.warning(f"Failed to save evaluation to job: {message}")
                            else:
                                logger.warning(f"Job evaluation failed for {job.job_title}: {evaluation_result.error_message}")
                                
                        except Exception as eval_error:
                            logger.error(f"Error evaluating job {job.job_title}: {eval_error}")
                    else:
                        logger.info(f"Skipping evaluation for job {job.job_title} - no user profile or AI settings")
                else:
                    logger.warning(f"Failed to save job: {message}")
            
            # Prepare response
            response_data = {
                'success': True,
                'message': f'Successfully found and saved {len(saved_jobs)} jobs after CAPTCHA verification',
                'jobs_count': len(saved_jobs),
                'captcha_solved': True
            }
            
            # Add evaluation results if available
            if evaluated_jobs:
                response_data['evaluated_jobs_count'] = len(evaluated_jobs)
                response_data['evaluation_summary'] = {
                    'total_evaluated': len(evaluated_jobs),
                    'highly_qualified': len([j for j in evaluated_jobs if j['qualification_status'] == 'highly_qualified']),
                    'qualified': len([j for j in evaluated_jobs if j['qualification_status'] == 'qualified']),
                    'somewhat_qualified': len([j for j in evaluated_jobs if j['qualification_status'] == 'somewhat_qualified']),
                    'not_qualified': len([j for j in evaluated_jobs if j['qualification_status'] == 'not_qualified'])
                }
                response_data['message'] += f' and evaluated {len(evaluated_jobs)} jobs'
            
            # Add quota warning if present
            if 'quota_warning' in session:
                response_data['quota_warning'] = session.pop('quota_warning')
                if len(evaluated_jobs) < len(saved_jobs):
                    response_data['message'] += f'. AI evaluation stopped due to quota limits.'
            
            return jsonify(response_data)
            
        finally:
            # Clean up scraper
            if scraper:
                scraper.cleanup()
        
    except Exception as e:
        logger.error(f"CAPTCHA continuation error: {e}")
        return jsonify({'success': False, 'error': f'CAPTCHA continuation failed: {str(e)}'})


@app.route('/search/linkedin/captcha/check', methods=['POST'])
@login_required  
def check_captcha_status():
    """Check if CAPTCHA has been solved using the proper CAPTCHA handler."""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'User not authenticated'})
        
        # Get LinkedIn credentials
        from src.config.config_manager import ConfigurationManager
        config_manager = ConfigurationManager()
        linkedin_username = config_manager.get_linkedin_settings().username if config_manager else None
        linkedin_password = config_manager.get_linkedin_settings().password if config_manager else None
        
        if not linkedin_username or not linkedin_password:
            return jsonify({'success': False, 'error': 'LinkedIn credentials not configured'})
        
        # Import required modules
        from src.utils.captcha_handler import captcha_handler
        from src.scrapers.linkedin_scraper_enhanced import create_enhanced_linkedin_scraper
        
        # Create WebDriver scraper for CAPTCHA checking
        scraper = None
        try:
            scraper = create_enhanced_linkedin_scraper(
                username=linkedin_username,
                password=linkedin_password,
                use_persistent_session=True
            )
            
            # Set up CAPTCHA handler with the scraper's WebDriver
            if hasattr(scraper, 'driver') and scraper.driver:
                captcha_handler.set_driver(scraper.driver)
                
                # Use the proper CAPTCHA detection method
                captcha_info = captcha_handler.detect_captcha()
                
                if captcha_info.status == CAPTCHAStatus.NOT_DETECTED:
                    return jsonify({
                        'success': True,
                        'captcha_solved': True,
                        'message': 'CAPTCHA appears to be solved - you can continue with the search'
                    })
                elif captcha_info.status == CAPTCHAStatus.DETECTED:
                    instructions = captcha_handler._generate_user_instructions(captcha_info)
                    return jsonify({
                        'success': False,
                        'captcha_solved': False,
                        'captcha_detected': True,
                        'captcha_info': {
                            'type': captcha_info.captcha_type,
                            'message': captcha_info.message,
                            'timeout_seconds': captcha_info.timeout_seconds
                        },
                        'instructions': instructions,
                        'message': 'CAPTCHA still needs to be solved'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'CAPTCHA status check failed: {captcha_info.message}'
                    })
            else:
                return jsonify({
                    'success': False,
                    'error': 'WebDriver not available for CAPTCHA checking'
                })
                
        finally:
            # Clean up scraper
            if scraper:
                scraper.cleanup()
        
    except Exception as e:
        logger.error(f"CAPTCHA status check error: {e}")
        return jsonify({'success': False, 'error': f'CAPTCHA status check failed: {str(e)}'})


@app.route('/jobs')
@login_required
def jobs_page():
    """Display jobs page with optimized approach - template compatible"""
    # Initialize default values for template safety
    jobs_data = []
    filters = {
        'company': request.args.get('company', ''),
        'location': request.args.get('location', ''),
        'title': request.args.get('title', ''),
        'status': request.args.get('status', ''),
        'salary_min': request.args.get('salary_min', ''),
        'salary_max': request.args.get('salary_max', '')
    }
    
    # Default analytics to prevent template errors
    analytics = {
        'total_applications': 0,
        'response_rate': 0.0,
        'responses_received': 0,
        'status_counts': {
            'interviewing': 0,
            'applied': 0,
            'rejected': 0,
            'offered': 0
        }
    }
    
    try:
        # Get authenticated database manager
        db_manager = get_authenticated_db_manager()
        if not db_manager:
            flash('Database connection failed', 'error')
            return render_template('jobs.html', jobs=jobs_data, filters=filters, analytics=analytics)
        
        user_id = session.get('user_id')
        if not user_id:
            flash('Please log in to view jobs', 'error')
            return redirect(url_for('auth.login'))

        logger.info("Starting optimized jobs query...")
        start_time = time.time()
        
        # OPTIMIZED: Get all jobs and applications in 2 queries
        try:
            logger.info("Attempting to use new SupabaseManager methods...")
            jobs_data_raw = db_manager.get_all_jobs(user_id)
            applications_data_raw = db_manager.get_applications_by_user(user_id)
            
            logger.info(f"New methods successful: {len(jobs_data_raw)} jobs, {len(applications_data_raw)} applications")
            
        except Exception as method_error:
            logger.warning(f"New methods failed: {method_error}")
            
            # Fallback to direct client access
            logger.info("Attempting direct client access...")
            jobs_response = db_manager.client.table('jobs').select('*').eq(
                'user_id', user_id
            ).order('date_found', desc=True).execute()
            
            applications_response = db_manager.client.table('applications').select(
                'job_id'
            ).eq('user_id', user_id).execute()
            
            jobs_data_raw = jobs_response.data if jobs_response.data else []
            applications_data_raw = applications_response.data if applications_response.data else []
            
            logger.info(f"Direct client successful: {len(jobs_data_raw)} jobs, {len(applications_data_raw)} applications")
        
        # Create lookup dictionary for application counts
        application_counts = {}
        for app in applications_data_raw:
            job_id = app.get('job_id')
            if job_id:
                application_counts[job_id] = application_counts.get(job_id, 0) + 1
        
        # Process jobs - create the structure your template expects
        for job in jobs_data_raw:
            job_dict = dict(job) if hasattr(job, 'items') else job
            
            # Debug: Log the job structure to understand field names
            logger.info(f"Job dict keys: {list(job_dict.keys())}")
            logger.info(f"Sample job data: {job_dict}")
            
            # Try different possible field names for job_id
            job_id = job_dict.get('job_id') or job_dict.get('id')
            
            # Try different possible field names for other fields
            job_title = job_dict.get('job_title') or job_dict.get('title')
            company_name = job_dict.get('company_name') or job_dict.get('company')
            location = job_dict.get('location', '')
            linkedin_url = job_dict.get('linkedin_url') or job_dict.get('url', '#')
            job_description = job_dict.get('job_description') or job_dict.get('description', '')
            salary_range = job_dict.get('salary_range', '')
            job_type = job_dict.get('job_type', '')
            experience_level = job_dict.get('experience_level', '')
            work_arrangement = job_dict.get('work_arrangement', '')
            date_found = job_dict.get('date_found', '')
            
            # Skip jobs without a valid job_id
            if not job_id:
                logger.warning(f"Skipping job without valid ID: {job_dict}")
                continue
            
            # Create job data in the format your template expects
            job_data_entry = {
                'job': {
                    'job_id': str(job_id),  # Ensure job_id is a string
                    'job_title': job_title or 'Unknown Title',
                    'company_name': company_name or 'Unknown Company',
                    'location': location,
                    'linkedin_url': linkedin_url,
                    'job_description': job_description,
                    'salary_range': salary_range,
                    'job_type': job_type,
                    'experience_level': experience_level,
                    'work_arrangement': work_arrangement,
                    'date_found': date_found
                },
                'application': None,  # You'd need to fetch actual application details
                'is_favorited': False,  # You'd need to fetch favorites data
                'application_count': application_counts.get(job_id, 0),
                'has_applied': application_counts.get(job_id, 0) > 0
            }
            
            jobs_data.append(job_data_entry)
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # Update analytics
        total_applications = len([job_data for job_data in jobs_data if job_data.get('has_applied')])
        analytics.update({
            'total_applications': total_applications,
            'status_counts': {
                'interviewing': 0,
                'applied': total_applications,
                'rejected': 0,
                'offered': 0
            }
        })
        
        logger.info(f"✅ OPTIMIZED: Loaded {len(jobs_data)} jobs in {query_time:.3f}s with 2 queries")
        
        # Add some template variables your template might expect
        today = datetime.now().strftime('%Y-%m-%d')
        page = int(request.args.get('page', 1))
        
        return render_template('jobs.html', 
                             jobs=jobs_data, 
                             filters=filters, 
                             analytics=analytics,
                             today=today,
                             page=page)
        
    except Exception as e:
        logger.error(f"❌ Error in optimized jobs_page: {str(e)}")
        # logger.exception("Full traceback:")
        flash('Error loading jobs', 'error')
        
        return render_template('jobs.html', 
                             jobs=jobs_data, 
                             filters=filters, 
                             analytics=analytics,
                             today=datetime.now().strftime('%Y-%m-%d'),
                             page=1)

@app.route('/jobs/<job_id>')
@login_required
def job_detail(job_id):
    """Display job details."""
    try:
        user = get_current_user()
        if not user:
            flash("User not authenticated.", "error")
            return redirect(url_for('auth.login_supabase'))
        
        db_manager = get_authenticated_db_manager()
        if not db_manager:
            flash("Database not available or user not authenticated.", "error")
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
        
        db_manager = get_authenticated_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available or user not authenticated'})
        
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
        
        db_manager = get_authenticated_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available or user not authenticated'})
        
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
        
        db_manager = get_authenticated_db_manager()
        if not db_manager:
            flash("Database not available or user not authenticated.", "error")
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


@app.route('/jobs-tracker')
@login_required
def jobs_tracker():
    """Enhanced job tracker page with comprehensive analytics and tracking - optimized approach."""
    # Initialize default values for template safety
    jobs_data = []
    filters = {
        'search': request.args.get('search', ''),
        'status': request.args.get('status', ''),
        'priority': request.args.get('priority', ''),
        'source': request.args.get('source', ''),
        'applied_date_from': request.args.get('applied_date_from', ''),
        'applied_date_to': request.args.get('applied_date_to', ''),
        'company': request.args.get('company', ''),
        'location': request.args.get('location', ''),
        'salary_min': request.args.get('salary_min', ''),
        'salary_max': request.args.get('salary_max', '')
    }
    
    # Default analytics to prevent template errors
    analytics = {
        'total_jobs_tracked': 0,
        'applications_submitted': 0,
        'response_rate': 0.0,
        'responses_received': 0,
        'interviews_scheduled': 0,
        'offers_received': 0,
        'status_counts': {
            'interviewing': 0,
            'applied': 0,
            'rejected': 0,
            'offered': 0
        }
    }
    
    try:
        user = get_current_user()
        if not user:
            flash('Please log in to view jobs', 'error')
            return redirect(url_for('auth.login'))
        
        # Get authenticated database manager
        db_manager = get_authenticated_db_manager()
        if not db_manager:
            flash('Database connection failed', 'error')
            return render_template('jobs_tracker.html', jobs=jobs_data, filters=filters, analytics=analytics)
        
        user_id = session.get('user_id')
        if not user_id:
            flash('Please log in to view jobs', 'error')
            return redirect(url_for('auth.login'))

        logger.info("Starting optimized jobs_tracker query...")
        start_time = time.time()
        
        # OPTIMIZED: Get all jobs and applications in 2 queries
        try:
            logger.info("Attempting to use new SupabaseManager methods...")
            jobs_data_raw = db_manager.get_all_jobs(user_id)
            applications_data_raw = db_manager.get_applications_by_user(user_id)
            
            logger.info(f"New methods successful: {len(jobs_data_raw)} jobs, {len(applications_data_raw)} applications")
            
        except Exception as method_error:
            logger.warning(f"New methods failed: {method_error}")
            
            # Fallback to direct client access
            logger.info("Attempting direct client access...")
            jobs_response = db_manager.client.table('jobs').select('*').eq(
                'user_id', user_id
            ).order('date_found', desc=True).execute()
            
            applications_response = db_manager.client.table('applications').select('*').eq(
                'user_id', user_id
            ).execute()
            
            jobs_data_raw = jobs_response.data if jobs_response.data else []
            applications_data_raw = applications_response.data if applications_response.data else []
            
            logger.info(f"Direct client successful: {len(jobs_data_raw)} jobs, {len(applications_data_raw)} applications")
        
        # Get favorites for user (enhanced feature for jobs_tracker)
        try:
            favorites_response = db_manager.client.table('job_favorites').select('*').eq(
                'user_id', user_id
            ).execute()
            favorites_data_raw = favorites_response.data if favorites_response.data else []
        except Exception as favorites_error:
            logger.warning(f"Failed to fetch favorites: {favorites_error}")
            favorites_data_raw = []
        
        # Create lookup dictionaries
        application_counts = {}
        applications_lookup = {}
        for app in applications_data_raw:
            job_id = app.get('job_id')
            if job_id:
                application_counts[job_id] = application_counts.get(job_id, 0) + 1
                # Keep the most recent application for this job
                if job_id not in applications_lookup or app.get('applied_date', '') > applications_lookup[job_id].get('applied_date', ''):
                    applications_lookup[job_id] = app
        
        favorites_lookup = {fav['job_id']: fav for fav in favorites_data_raw}
        
        # Process jobs - create the structure your template expects
        processed_jobs = 0
        for job in jobs_data_raw:
            job_dict = dict(job) if hasattr(job, 'items') else job
            
            # Try different possible field names for job_id
            job_id = job_dict.get('job_id') or job_dict.get('id')
            
            # Skip jobs without a valid job_id
            if not job_id:
                logger.warning(f"Skipping job without valid ID: {job_dict}")
                continue
            
            # Get application data
            application = applications_lookup.get(job_id)
            
            # Apply filters (but don't filter here - let frontend handle it)
            # This allows for better interactivity
            
            # Try different possible field names for other fields
            job_title = job_dict.get('job_title') or job_dict.get('title')
            company_name = job_dict.get('company_name') or job_dict.get('company')
            location = job_dict.get('location', '')
            job_description = job_dict.get('job_description') or job_dict.get('description', '')
            salary_range = job_dict.get('salary_range', '')
            job_type = job_dict.get('job_type', '')
            experience_level = job_dict.get('experience_level', '')
            work_arrangement = job_dict.get('work_arrangement', '')
            date_found = job_dict.get('date_found', '')
            

            
            # Get favorite data
            favorite = favorites_lookup.get(job_id)
            is_favorited = favorite is not None
            priority = favorite.get('priority', 'medium') if favorite else 'medium'
            
            # Debug: Log the job data to see what fields are available
            if processed_jobs < 3:  # Only log first 3 jobs to avoid spam
                logger.info(f"Job {job_id} data keys: {list(job_dict.keys())}")
                logger.info(f"Job {job_id} linkedin_job_url: {job_dict.get('linkedin_job_url', 'NOT_FOUND')}")
                logger.info(f"Job {job_id} linkedin_url: {job_dict.get('linkedin_url', 'NOT_FOUND')}")
                logger.info(f"Job {job_id} job_url: {job_dict.get('job_url', 'NOT_FOUND')}")
                logger.info(f"Job {job_id} full data: {job_dict}")
            
                        # Enhanced LinkedIn URL extraction with better debugging
            # According to database schema, we have: linkedin_url and job_url fields
            linkedin_url_raw = job_dict.get('linkedin_url')
            job_url_raw = job_dict.get('job_url')
            
            # Debug: Log all URL-related fields for first few jobs
            if processed_jobs < 3:
                print(f"🔍 DEBUG: Job {job_id} - All URL fields:")
                print(f"  linkedin_url: {linkedin_url_raw}")
                print(f"  job_url: {job_url_raw}")
                print(f"  linkedin_url: {job_dict.get('linkedin_url', 'NOT_FOUND')}")
                print(f"  url: {job_dict.get('url', 'NOT_FOUND')}")
            
            # Priority order: linkedin_url > job_url (only if it's a LinkedIn URL) > linkedin_job_url > url
            linkedin_url = linkedin_url_raw or ''
            
            # If linkedin_url is empty, check if job_url contains a LinkedIn URL
            if not linkedin_url and job_url_raw and 'linkedin.com' in job_url_raw.lower():
                linkedin_url = job_url_raw
            
            # Fallback to other fields if still empty
            if not linkedin_url:
                linkedin_url = (job_dict.get('linkedin_job_url') or 
                               job_dict.get('url') or '')
            
            # Clean up the URL - remove placeholder values
            if linkedin_url in ['#', 'null', 'None', '']:
                linkedin_url = ''
            
            # Create enhanced job data in the format your template expects
            job_data_entry = {
                'job': {
                    'job_id': str(job_id),  # Ensure job_id is a string
                    'job_title': job_title or 'Unknown Title',
                    'company_name': company_name or 'Unknown Company',
                    'location': location,
                    'linkedin_url': linkedin_url,  # Use LinkedIn URL from database
                    'job_url': job_dict.get('job_url', ''),  # Keep original job_url field
                    'job_description': job_description,
                    'salary_range': salary_range,
                    'job_type': job_type,
                    'experience_level': experience_level,
                    'work_arrangement': work_arrangement,
                    'date_found': date_found
                },
                'application': application,
                'is_favorited': is_favorited,
                'priority': priority,
                'source': linkedin_url or 'unknown',  # Use LinkedIn URL as source
                'notes': favorite.get('notes', '') if favorite else '',
                'application_count': application_counts.get(job_id, 0),
                'has_applied': application_counts.get(job_id, 0) > 0
            }
            
            jobs_data.append(job_data_entry)
            processed_jobs += 1
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # Calculate comprehensive analytics
        analytics = calculate_comprehensive_analytics(db_manager, user_id)
        # Update with actual counts
        analytics['total_jobs_tracked'] = len(jobs_data)
        
        logger.info(f"✅ OPTIMIZED: Loaded {len(jobs_data)} jobs in {query_time:.3f}s with 2 queries")
        logger.info(f"Processed {processed_jobs} jobs successfully")
        
        # Add template variables
        today = datetime.now().strftime('%Y-%m-%d')
        page = int(request.args.get('page', 1))
        
        logger.info(f"Passing {len(jobs_data)} jobs to template")
        logger.info(f"Analytics: {analytics}")
        
        return render_template('jobs_tracker.html', 
                             jobs=jobs_data, 
                             filters=filters, 
                             analytics=analytics,
                             today=today,
                             page=page)
        
    except Exception as e:
        logger.error(f"❌ Error in optimized jobs_tracker: {str(e)}")
        logger.exception("Full traceback:")
        flash('Error loading job tracker', 'error')
        
        return render_template('jobs_tracker.html', 
                             jobs=jobs_data, 
                             filters=filters, 
                             analytics=analytics,
                             today=datetime.now().strftime('%Y-%m-%d'),
                             page=1)    


def get_enhanced_jobs_data(db_manager, user_id, filters):
    """Get jobs with enhanced data including applications, notes, and priorities - optimized approach."""
    try:
        logger.info("Starting optimized get_enhanced_jobs_data query...")
        start_time = time.time()
        
        # OPTIMIZED: Get all jobs and applications in 2 queries (same as jobs_page)
        try:
            logger.info("Attempting to use new SupabaseManager methods...")
            logger.info("DEBUG: About to call get_all_jobs")
            jobs_data_raw = db_manager.get_all_jobs(user_id)
            logger.info("DEBUG: get_all_jobs completed")
            applications_data_raw = db_manager.get_applications_by_user(user_id)
            
            logger.info(f"New methods successful: {len(jobs_data_raw)} jobs, {len(applications_data_raw)} applications")
            
        except Exception as method_error:
            logger.warning(f"New methods failed: {method_error}")
            
            # Fallback to direct client access (same as jobs_page)
            logger.info("Attempting direct client access...")
            jobs_response = db_manager.client.table('jobs').select('*').eq(
                'user_id', user_id
            ).order('date_found', desc=True).execute()
            
            applications_response = db_manager.client.table('applications').select(
                'job_id'
            ).eq('user_id', user_id).execute()
            
            jobs_data_raw = jobs_response.data if jobs_response.data else []
            applications_data_raw = applications_response.data if applications_response.data else []
            
            logger.info(f"Direct client successful: {len(jobs_data_raw)} jobs, {len(applications_data_raw)} applications")
        
        # Get favorites for user (enhanced feature)
        try:
            favorites_response = db_manager.client.table('job_favorites').select('*').eq(
                'user_id', user_id
            ).execute()
            favorites_data_raw = favorites_response.data if favorites_response.data else []
        except Exception as favorites_error:
            logger.warning(f"Failed to fetch favorites: {favorites_error}")
            favorites_data_raw = []
        
        # Create lookup dictionaries
        applications_lookup = {app['job_id']: app for app in applications_data_raw}
        favorites_lookup = {fav['job_id']: fav for fav in favorites_data_raw}
        
        # Process and filter jobs
        enhanced_jobs = []
        for job in jobs_data_raw:
            job_dict = dict(job) if hasattr(job, 'items') else job
            
            # Try different possible field names for job_id
            job_id = job_dict.get('job_id') or job_dict.get('id')
            
            # Skip jobs without a valid job_id
            if not job_id:
                logger.warning(f"Skipping job without valid ID: {job_dict}")
                continue
            
            # Apply filters
            if not passes_filters(job_dict, applications_lookup.get(job_id), filters):
                continue
            
            # Get application data
            application = applications_lookup.get(job_id)
            
            # Get favorite data
            favorite = favorites_lookup.get(job_id)
            is_favorited = favorite is not None
            priority = favorite.get('priority', 'medium') if favorite else 'medium'
            
            # Enhanced LinkedIn URL extraction (same logic as jobs_tracker)
            linkedin_url_raw = job_dict.get('linkedin_url')
            job_url_raw = job_dict.get('job_url')
            
            # Priority order: linkedin_url > job_url (only if it's a LinkedIn URL) > linkedin_job_url > url
            linkedin_url = linkedin_url_raw or ''
            
            # If linkedin_url is empty, check if job_url contains a LinkedIn URL
            if not linkedin_url and job_url_raw and 'linkedin.com' in job_url_raw.lower():
                linkedin_url = job_url_raw
            
            # Fallback to other fields if still empty
            if not linkedin_url:
                linkedin_url = (job_dict.get('linkedin_job_url') or 
                               job_dict.get('url') or '')
            
            # Clean up the URL - remove placeholder values
            if linkedin_url in ['#', 'null', 'None', '']:
                linkedin_url = ''
            
            # Create enhanced job data
            enhanced_job = {
                'job': {
                    'job_id': str(job_id),  # Ensure job_id is a string
                    'job_title': job_dict.get('job_title') or job_dict.get('title', 'Unknown Title'),
                    'company_name': job_dict.get('company_name') or job_dict.get('company', 'Unknown Company'),
                    'location': job_dict.get('location', ''),
                    'linkedin_url': linkedin_url,  # Use enhanced LinkedIn URL
                    'job_url': job_dict.get('job_url', ''),  # Keep original job_url field
                    'job_description': job_dict.get('job_description') or job_dict.get('description', ''),
                    'salary_range': job_dict.get('salary_range', ''),
                    'job_type': job_dict.get('job_type', ''),
                    'experience_level': job_dict.get('experience_level', ''),
                    'work_arrangement': job_dict.get('work_arrangement', ''),
                    'date_found': job_dict.get('date_found', '')
                },
                'application': application,
                'is_favorited': is_favorited,
                'priority': priority,
                'source': linkedin_url or job_dict.get('source', 'unknown'),
                'notes': favorite.get('notes', '') if favorite else ''
            }
            
            enhanced_jobs.append(enhanced_job)
        
        end_time = time.time()
        query_time = end_time - start_time
        logger.info(f"✅ OPTIMIZED: Loaded {len(enhanced_jobs)} enhanced jobs in {query_time:.3f}s with 2 queries")
        
        return enhanced_jobs
        
    except Exception as e:
        logger.error(f"❌ Error in optimized get_enhanced_jobs_data: {e}")
        return []


def passes_filters(job, application, filters):
    """Check if job passes all applied filters."""
    # Search filter
    if filters.get('search'):
        search_term = filters['search'].lower()
        job_title = job.get('job_title', '').lower()
        company_name = job.get('company_name', '').lower()
        location = job.get('location', '').lower()
        
        if search_term not in job_title and search_term not in company_name and search_term not in location:
            return False
    
    # Status filter
    if filters.get('status'):
        if not application:
            if filters['status'] != 'not_applied':
                return False
        elif application.get('application_status') != filters['status']:
            return False
    
    # Priority filter
    if filters.get('priority'):
        # This would need to be implemented based on your priority system
        pass
    
    # Source filter
    if filters.get('source'):
        if job.get('source') != filters['source']:
            return False
    
    # Date filters
    if filters.get('applied_date_from') or filters.get('applied_date_to'):
        if not application:
            return False
        
        applied_date = application.get('applied_date')
        if not applied_date:
            return False
        
        if filters.get('applied_date_from'):
            if applied_date < filters['applied_date_from']:
                return False
        
        if filters.get('applied_date_to'):
            if applied_date > filters['applied_date_to']:
                return False
    
    return True


def calculate_comprehensive_analytics(db_manager, user_id):
    """Calculate comprehensive analytics for the job tracker."""
    try:
        # Get all applications for user
        applications_response = db_manager.client.table('applications').select('*').eq(
            'user_id', user_id
        ).execute()
        
        applications = applications_response.data if applications_response.data else []
        
        # Get all jobs for user
        jobs_response = db_manager.client.table('jobs').select('*').eq(
            'user_id', user_id
        ).execute()
        
        jobs = jobs_response.data if jobs_response.data else []
        
        # Calculate basic metrics
        total_jobs_tracked = len(jobs)
        applications_submitted = len([app for app in applications if app.get('application_status') != 'not_applied'])
        
        # Calculate response rate
        responses_received = len([app for app in applications if app.get('response_received', False)])
        response_rate = (responses_received / applications_submitted * 100) if applications_submitted > 0 else 0
        
        # Calculate status counts
        status_counts = {}
        for app in applications:
            status = app.get('application_status', 'not_applied')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Calculate active applications (applied but not rejected/withdrawn)
        active_applications = len([app for app in applications 
                                 if app.get('application_status') in ['applied', 'phone_screen', 'interview', 'final_round']])
        
        # Calculate interviews scheduled
        interviews_scheduled = len([app for app in applications 
                                  if app.get('application_status') in ['phone_screen', 'interview', 'final_round']])
        
        # Calculate offers received
        offers_received = len([app for app in applications 
                             if app.get('application_status') == 'offer'])
        
        # Calculate application funnel
        funnel = {
            'applied': (applications_submitted / total_jobs_tracked * 100) if total_jobs_tracked > 0 else 0,
            'interviewing': (interviews_scheduled / applications_submitted * 100) if applications_submitted > 0 else 0,
            'offers': (offers_received / interviews_scheduled * 100) if interviews_scheduled > 0 else 0
        }
        
        # Calculate average response time
        response_times = []
        for app in applications:
            if app.get('response_received') and app.get('applied_date') and app.get('response_date'):
                applied_date = datetime.fromisoformat(app['applied_date'].replace('Z', '+00:00'))
                response_date = datetime.fromisoformat(app['response_date'].replace('Z', '+00:00'))
                days_diff = (response_date - applied_date).days
                response_times.append(days_diff)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Calculate top responding companies
        company_responses = {}
        for app in applications:
            if app.get('response_received'):
                company = app.get('company_name', 'Unknown')
                if company not in company_responses:
                    company_responses[company] = {'responses': 0, 'total': 0}
                company_responses[company]['responses'] += 1
                company_responses[company]['total'] += 1
            else:
                company = app.get('company_name', 'Unknown')
                if company not in company_responses:
                    company_responses[company] = {'responses': 0, 'total': 0}
                company_responses[company]['total'] += 1
        
        top_companies = []
        for company, data in company_responses.items():
            if data['total'] > 0:
                response_rate = (data['responses'] / data['total']) * 100
                top_companies.append({
                    'name': company,
                    'response_rate': round(response_rate, 1)
                })
        
        # Sort by response rate
        top_companies.sort(key=lambda x: x['response_rate'], reverse=True)
        top_companies = top_companies[:5]  # Top 5
        
        return {
            'total_jobs_tracked': total_jobs_tracked,
            'applications_submitted': applications_submitted,
            'response_rate': round(response_rate, 1),
            'responses_received': responses_received,
            'active_applications': active_applications,
            'interviews_scheduled': interviews_scheduled,
            'offers_received': offers_received,
            'status_counts': status_counts,
            'funnel': funnel,
            'avg_response_time': round(avg_response_time, 1),
            'top_companies': top_companies
        }
        
    except Exception as e:
        logger.error(f"Error calculating analytics: {e}")
        return {
            'total_jobs_tracked': 0,
            'applications_submitted': 0,
            'response_rate': 0,
            'responses_received': 0,
            'active_applications': 0,
            'interviews_scheduled': 0,
            'offers_received': 0,
            'status_counts': {},
            'funnel': {'applied': 0, 'interviewing': 0, 'offers': 0},
            'avg_response_time': 0,
            'top_companies': []
        }


# Enhanced API endpoints for the job tracker
@app.route('/api/jobs/status-update', methods=['POST'])
@login_required
def update_job_status():
    """Update job application status with enhanced features."""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'User not authenticated'})
        
        data = request.get_json()
        job_id = data.get('job_id')
        status = data.get('status')
        notes = data.get('notes', '')
        follow_up_date = data.get('follow_up_date')
        
        if not job_id or not status:
            return jsonify({'success': False, 'error': 'Job ID and status are required'})
        
        db_manager = get_authenticated_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'})
        
        # Check if application exists
        existing_application = db_manager.applications.get_application_by_job(user['user_id'], job_id)
        
        if existing_application:
            # Update existing application
            success, message, application = db_manager.applications.update_application_status(
                existing_application.application_id, 
                user['user_id'], 
                SupabaseApplicationStatus(status), 
                notes
            )
            
            # Update follow-up date if provided
            if follow_up_date and success:
                db_manager.applications.update_follow_up_date(
                    existing_application.application_id,
                    user['user_id'],
                    follow_up_date
                )
        else:
            # Create new application
            application_data = {
                'user_id': user['user_id'],
                'job_id': job_id,
                'application_method': SupabaseApplicationMethod.MANUAL,
                'applied_date': datetime.now().isoformat(),
                'application_status': SupabaseApplicationStatus(status),
                'notes': notes,
                'follow_up_date': follow_up_date
            }
            
            success, message, application = db_manager.applications.create_application(application_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Application status updated successfully',
                'status': status
            })
        else:
            return jsonify({'success': False, 'error': f'Failed to update status: {message}'})
        
    except Exception as e:
        logger.error(f"Update job status error: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/jobs/bulk-status-update', methods=['POST'])
@login_required
def bulk_update_job_status():
    """Bulk update job application statuses."""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'User not authenticated'})
        
        data = request.get_json()
        job_ids = data.get('job_ids', [])
        status = data.get('status')
        notes = data.get('notes', '')
        
        if not job_ids or not status:
            return jsonify({'success': False, 'error': 'Job IDs and status are required'})
        
        db_manager = get_authenticated_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'})
        
        success_count = 0
        for job_id in job_ids:
            try:
                # Check if application exists
                existing_application = db_manager.applications.get_application_by_job(user['user_id'], job_id)
                
                if existing_application:
                    # Update existing application
                    success, message, application = db_manager.applications.update_application_status(
                        existing_application.application_id, 
                        user['user_id'], 
                        SupabaseApplicationStatus(status), 
                        notes
                    )
                else:
                    # Create new application
                    application_data = {
                        'user_id': user['user_id'],
                        'job_id': job_id,
                        'application_method': SupabaseApplicationMethod.MANUAL,
                        'applied_date': datetime.now().isoformat(),
                        'application_status': SupabaseApplicationStatus(status),
                        'notes': notes
                    }
                    
                    success, message, application = db_manager.applications.create_application(application_data)
                
                if success:
                    success_count += 1
                    
            except Exception as e:
                logger.error(f"Error updating job {job_id}: {e}")
                continue
        
        return jsonify({
            'success': True,
            'message': f'Successfully updated {success_count} out of {len(job_ids)} jobs',
            'updated_count': success_count
        })
        
    except Exception as e:
        logger.error(f"Bulk update job status error: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/jobs/add-note', methods=['POST'])
@login_required
def add_job_note():
    """Add or update notes for a job."""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'User not authenticated'})
        
        data = request.get_json()
        job_id = data.get('job_id')
        note = data.get('note', '')
        
        if not job_id:
            return jsonify({'success': False, 'error': 'Job ID is required'})
        
        db_manager = get_authenticated_db_manager()
        if not db_manager:
            return jsonify({'success': False, 'error': 'Database not available'})
        
        # Check if favorite exists
        favorite_response = db_manager.client.table('job_favorites').select('*').eq(
            'user_id', user['user_id']
        ).eq('job_id', job_id).execute()
        
        if favorite_response.data:
            # Update existing favorite
            favorite_id = favorite_response.data[0]['id']
            update_response = db_manager.client.table('job_favorites').update({
                'notes': note,
                'last_updated': datetime.now().isoformat()
            }).eq('id', favorite_id).execute()
            
            success = len(update_response.data) > 0
        else:
            # Create new favorite with note
            create_response = db_manager.client.table('job_favorites').insert({
                'user_id': user['user_id'],
                'job_id': job_id,
                'notes': note,
                'priority': 1,
                'favorited_date': datetime.now().isoformat(),
                'created_date': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }).execute()
            
            success = len(create_response.data) > 0
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Note added successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to add note'})
        
    except Exception as e:
        logger.error(f"Add job note error: {e}")
        return jsonify({'success': False, 'error': str(e)})


# Template filter for getting days since applied
@app.template_filter('get_days_since_applied')
def get_days_since_applied(applied_date):
    """Calculate days since application was submitted."""
    if not applied_date:
        return 'Unknown'
    
    try:
        if isinstance(applied_date, str):
            applied = datetime.fromisoformat(applied_date.replace('Z', '+00:00'))
        else:
            applied = applied_date
        
        today = datetime.now()
        diff = today - applied
        return diff.days
    except Exception as e:
        logger.error(f"Error calculating days since applied: {e}")
        return 'Unknown'


if __name__ == '__main__':
    # Initialize system components
    initialize_system()
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000) 