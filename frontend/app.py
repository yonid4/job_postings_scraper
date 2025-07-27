#!/usr/bin/env python3
"""
Flask web application for the AI Job Qualification Screening System.

This provides a user-friendly web interface for:
- User profile management
- Job search URL input
- Qualification analysis results
- Google Sheets integration
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
from typing import Dict, Any
from werkzeug.utils import secure_filename

# Add the parent directory to Python path to import src modules
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from src.config.config_manager import ConfigurationManager
from src.utils.job_link_processor import JobLinkProcessor
from src.ai.qualification_analyzer import QualificationAnalyzer, AnalysisRequest
from src.data.models import QualificationResult, QualificationStatus, UserDecision
from src.data.google_sheets_manager import GoogleSheetsManager
from src.data.resume_manager import ResumeManager
from src.data.job_tracker import JobTracker
from src.data.models import JobApplication, ApplicationStatus, ApplicationMethod, JobFavorite
from src.utils.logger import JobAutomationLogger

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
        
        # Initialize Google Sheets if configured
        api_settings = config_manager.get_api_settings()
        if (api_settings.google_sheets_spreadsheet_id and 
            api_settings.google_sheets_credentials_path and
            os.path.exists(api_settings.google_sheets_credentials_path)):
            try:
                sheets_manager = GoogleSheetsManager(
                    api_settings.google_sheets_spreadsheet_id,
                    api_settings.google_sheets_credentials_path
                )
                logger.info("Google Sheets manager initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Google Sheets: {e}")
                sheets_manager = None
        else:
            logger.info("Google Sheets not configured - skipping initialization")
            sheets_manager = None
        
        # Initialize resume manager
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'job_automation.db')
        
        # Ensure data directory exists
        data_dir = os.path.dirname(db_path)
        os.makedirs(data_dir, exist_ok=True)
        
        upload_folder = os.path.join(UPLOAD_FOLDER, 'resumes')
        resume_manager = ResumeManager(db_path, upload_folder, qualification_analyzer)
        
        # Initialize job tracker
        job_tracker = JobTracker(db_path)
        
        logger.info("System components initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing system: {e}")
        raise


def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    ALLOWED_EXTENSIONS = {'pdf', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_user_id():
    """Get the current user ID from session or generate a temporary one."""
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return session['user_id']


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')


@app.route('/profile')
def profile():
    """User profile management page."""
    try:
        if config_manager is None:
            flash("System not properly initialized. Please restart the application.", 'error')
            return render_template('profile.html', profile=None)
        
        user_profile = config_manager.get_user_profile()
        return render_template('profile.html', profile=user_profile)
    except Exception as e:
        flash(f"Error loading profile: {e}", 'error')
        return render_template('profile.html', profile=None)


@app.route('/profile/update', methods=['POST'])
def update_profile():
    """Update user profile."""
    try:
        if config_manager is None:
            flash("System not properly initialized. Please restart the application.", 'error')
            return redirect(url_for('profile'))
        
        # Create profile data from form
        profile_data = {
            'years_of_experience': int(request.form.get('years_of_experience', 0)),
            'has_college_degree': 'has_college_degree' in request.form,
            'field_of_study': request.form.get('field_of_study', ''),
            'experience_level': request.form.get('experience_level', 'entry'),
            'salary_min': int(request.form.get('salary_min')) if request.form.get('salary_min') else None,
            'salary_max': int(request.form.get('salary_max')) if request.form.get('salary_max') else None,
            'remote_preference': request.form.get('remote_preference', 'any'),
            'preferred_locations': request.form.get('preferred_locations', '').split(','),
            'additional_skills': request.form.get('additional_skills', '').split(',')
        }
        
        # Clean up empty strings
        profile_data['preferred_locations'] = [loc.strip() for loc in profile_data['preferred_locations'] if loc.strip()]
        profile_data['additional_skills'] = [skill.strip() for skill in profile_data['additional_skills'] if skill.strip()]
        
        # Update configuration
        config_manager.update_configuration_section('user_profile', profile_data)
        config_manager.save_configuration()
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
        
    except Exception as e:
        flash(f"Error updating profile: {e}", 'error')
        return redirect(url_for('profile'))


@app.route('/search')
def search():
    """Job search page."""
    return render_template('search.html')


@app.route('/search/analyze', methods=['POST'])
def analyze_jobs():
    """Analyze jobs from search URLs with resume processing."""
    try:
        if config_manager is None or job_processor is None or qualification_analyzer is None:
            return jsonify({'error': 'System not properly initialized. Please restart the application.'})
        
        # Get search URL from form (new format)
        search_url = request.form.get('search_url', '').strip()
        
        # Fallback to old format for backward compatibility
        if not search_url:
            search_urls = request.form.get('search_urls', '').strip().split('\n')
            search_urls = [url.strip() for url in search_urls if url.strip()]
            if search_urls:
                search_url = search_urls[0]  # Use first URL if multiple provided
        
        if not search_url:
            return jsonify({'error': 'No search URL provided'})
        
        # Get qualification threshold from form
        qualification_threshold = int(request.form.get('qualification_threshold', 70))
        session['qualification_threshold'] = qualification_threshold
        
        # Log the received data for debugging
        logger.info(f"Received search request - URL: {search_url}")
        logger.info(f"Form data: {dict(request.form)}")
        logger.info(f"Qualification threshold: {qualification_threshold}")
        
        # Get user profile
        user_profile = config_manager.get_user_profile()
        ai_settings = config_manager.get_ai_settings()
        
        # Ensure resume is processed (lazy processing)
        resume_data = None
        if resume_manager:
            user_id = get_user_id()
            resume_data = resume_manager.ensure_resume_processed(user_id)
            if resume_data:
                logger.info(f"Using resume data for user {user_id}")
            else:
                logger.info(f"No resume data available for user {user_id}")
        
        # Check if this is a LinkedIn URL and use enhanced scraper
        if 'linkedin.com/jobs' in search_url.lower():
            logger.info("Detected LinkedIn URL - checking date filter requirements")
            
            # Extract keywords and location from LinkedIn URL or use defaults
            keywords = request.form.get('keywords', 'Software Engineer').strip()
            location = request.form.get('location', 'San Francisco, CA').strip()
            date_posted = request.form.get('date_posted')
            
            # Convert date_posted to integer days
            date_posted_days = None
            if date_posted and date_posted != 'any':
                try:
                    date_posted_days = int(date_posted)
                    logger.info(f"User requested jobs from past {date_posted_days} days - using enhanced scraper with authentication")
                except ValueError:
                    logger.warning(f"Invalid date_posted value: {date_posted}")
            
            # Determine which scraper to use based on date filter
            if date_posted_days is None:
                # No date filter or "Any time" selected - use regular scraping without browser
                logger.info("No date filter selected - using regular LinkedIn scraping without authentication")
                
                try:
                    # Use the regular job processor for basic LinkedIn scraping
                    from src.utils.job_link_processor import JobLinkProcessor
                    
                    job_processor = JobLinkProcessor()
                    job_links = job_processor.process_job_links([search_url])
                    
                    if not job_links:
                        return jsonify({'error': 'No jobs found in the provided URLs'})
                    
                    # Analyze scraped jobs
                    results = []
                    for job_link in job_links[:10]:  # Limit to first 10 jobs
                        if job_link.error or not job_link.title:
                            continue
                        try:
                            # Create analysis request with resume data
                            request_obj = AnalysisRequest(
                                job_title=job_link.title,
                                company=job_link.company,
                                job_description=job_link.description or "No description available",
                                user_profile=user_profile,
                                ai_settings=ai_settings,
                                resume_data=resume_data
                            )
                            
                            # Run analysis
                            analysis_response = qualification_analyzer.analyze_job_qualification(request_obj)
                            
                            results.append({
                                'job_title': job_link.title,
                                'company': job_link.company,
                                'location': job_link.location or "Unknown Location",
                                'job_url': job_link.url,
                                'score': analysis_response.qualification_score,
                                'status': analysis_response.qualification_status.value,
                                'reasoning': analysis_response.ai_reasoning,
                                'strengths': analysis_response.matching_strengths,
                                'concerns': analysis_response.potential_concerns,
                                'required_experience': analysis_response.required_experience,
                                'education_requirements': analysis_response.education_requirements,
                                'key_skills': analysis_response.key_skills_mentioned
                            })
                        except Exception as e:
                            logger.error(f"Error analyzing job {job_link.title}: {e}")
                            continue
                    
                except Exception as e:
                    logger.error(f"Regular LinkedIn scraping error: {e}")
                    return jsonify({'error': f'LinkedIn scraping failed: {str(e)}'})
                    
            else:
                # Specific date filter selected - use enhanced scraper with authentication
                logger.info(f"Date filter selected ({date_posted_days} days) - using enhanced scraper with authentication")
                
                # Initialize enhanced LinkedIn scraper
                from src.scrapers.linkedin_scraper_enhanced import EnhancedLinkedInScraper
                from src.utils.session_manager import SessionManager
                from src.scrapers.linkedin_scraper_enhanced import ScrapingConfig
                
                session_manager = SessionManager()
                config = ScrapingConfig(
                    max_jobs_per_session=20,
                    delay_min=2.0,
                    delay_max=3.0,
                    max_retries=3,
                    page_load_timeout=30,
                    site_name="linkedin",
                    base_url="https://www.linkedin.com"
                )
                
                # Add LinkedIn credentials to config
                linkedin_config = config_manager.get_linkedin_settings()
                config.linkedin_username = linkedin_config.username
                config.linkedin_password = linkedin_config.password
                
                scraper = EnhancedLinkedInScraper(config, session_manager)
                
                try:
                    # Split keywords into list
                    keywords_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]
                    
                    # Scrape jobs (authentication required for LinkedIn)
                    scraping_result = scraper.scrape_jobs_with_enhanced_date_filter(
                        keywords=keywords_list,
                        location=location,
                        date_posted_days=date_posted_days,
                        require_auth=True  # Authentication required for LinkedIn
                    )
                    
                    if not scraping_result.success:
                        return jsonify({'error': f'LinkedIn scraping failed: {scraping_result.error_message}'})
                    
                    # Analyze scraped jobs
                    results = []
                    for job in scraping_result.jobs[:10]:  # Limit to first 10 jobs
                        try:
                            # Create analysis request with resume data
                            request_obj = AnalysisRequest(
                                job_title=job.title,
                                company=job.company,
                                job_description=job.description or "No description available",
                                user_profile=user_profile,
                                ai_settings=ai_settings,
                                resume_data=resume_data
                            )
                            
                            # Run analysis
                            analysis_response = qualification_analyzer.analyze_job_qualification(request_obj)
                            
                            results.append({
                                'job_title': job.title,
                                'company': job.company,
                                'location': job.location or "Unknown Location",
                                'job_url': job.job_url,
                                'score': analysis_response.qualification_score,
                                'status': analysis_response.qualification_status.value,
                                'reasoning': analysis_response.ai_reasoning,
                                'strengths': analysis_response.matching_strengths,
                                'concerns': analysis_response.potential_concerns,
                                'required_experience': analysis_response.required_experience,
                                'education_requirements': analysis_response.education_requirements,
                                'key_skills': analysis_response.key_skills_mentioned
                            })
                        except Exception as e:
                            logger.error(f"Error analyzing job {job.title}: {e}")
                            continue
                    
                except Exception as e:
                    logger.error(f"LinkedIn scraping error: {e}")
                    return jsonify({'error': f'LinkedIn scraping failed: {str(e)}'})
                    
        else:
            # Use regular job link processor for non-LinkedIn URLs
            job_links = job_processor.process_job_links([search_url])
            
            if not job_links:
                return jsonify({'error': 'No jobs found in the provided URLs'})
            
            # Analyze jobs with resume data if available
            results = []
            for job_link in job_links[:10]:  # Limit to first 10 jobs
                if job_link.error or not job_link.title:
                    continue
                
                # Create analysis request with resume data
                request_obj = AnalysisRequest(
                    job_title=job_link.title,
                    company=job_link.company or "Unknown Company",
                    job_description=job_link.description or "No description available",
                    user_profile=user_profile,
                    ai_settings=ai_settings,
                    resume_data=resume_data  # Add resume data to analysis
                )
                
                # Run analysis
                analysis_response = qualification_analyzer.analyze_job_qualification(request_obj)
                
                # Create qualification result
                qualification_result = QualificationResult(
                    job_title=job_link.title,
                    company=job_link.company or "Unknown Company",
                    job_url=job_link.url,
                    qualification_score=analysis_response.qualification_score,
                    qualification_status=analysis_response.qualification_status,
                    ai_reasoning=analysis_response.ai_reasoning,
                    required_experience=analysis_response.required_experience,
                    education_requirements=analysis_response.education_requirements,
                    key_skills_mentioned=analysis_response.key_skills_mentioned,
                    matching_strengths=analysis_response.matching_strengths,
                    potential_concerns=analysis_response.potential_concerns,
                    user_decision=UserDecision.PENDING
                )
                
                results.append({
                    'job_title': job_link.title,
                    'company': job_link.company or "Unknown Company",
                    'location': job_link.location or "Unknown Location",
                    'job_url': job_link.url,
                    'score': analysis_response.qualification_score,
                    'status': analysis_response.qualification_status.value,
                    'reasoning': analysis_response.ai_reasoning,
                    'strengths': analysis_response.matching_strengths,
                    'concerns': analysis_response.potential_concerns,
                    'required_experience': analysis_response.required_experience,
                    'education_requirements': analysis_response.education_requirements,
                    'key_skills': analysis_response.key_skills_mentioned
                })
        
        # Store results in server-side cache instead of session
        analysis_id = str(uuid.uuid4())
        analysis_cache[analysis_id] = results
        
        # Store only the analysis ID in session
        session['current_analysis_id'] = analysis_id
        
        # Clean up old analysis results to prevent memory issues
        cleanup_old_analysis_results()
        
        return jsonify({
            'success': True,
            'results': results,
            'total_jobs': len(results),
            'analysis_id': analysis_id
        })
        
    except Exception as e:
        logger.error(f"Error analyzing jobs: {e}")
        return jsonify({'error': f'Analysis failed: {str(e)}'})


@app.route('/search/linkedin/captcha', methods=['POST'])
def handle_linkedin_captcha():
    """Handle CAPTCHA challenges and continue LinkedIn scraping after user completion."""
    try:
        if config_manager is None or qualification_analyzer is None:
            return jsonify({'error': 'System not properly initialized. Please restart the application.'})
        
        # Get the original search parameters from session or request
        search_params = {
            'keywords': request.form.get('keywords', '').strip(),
            'location': request.form.get('location', '').strip(),
            'date_posted': request.form.get('date_posted'),
            'qualification_threshold': int(request.form.get('qualification_threshold', 70)),
            'work_arrangement': request.form.getlist('work_arrangement'),
            'experience_level': request.form.getlist('experience_level'),
            'job_type': request.form.getlist('job_type')
        }
        
        # Validate required parameters
        if not search_params['keywords']:
            return jsonify({'error': 'Keywords are required'})
        
        if not search_params['location']:
            return jsonify({'error': 'Location is required'})
        
        # Convert date_posted to integer days for LinkedIn scraper
        date_posted_days = None
        if search_params['date_posted'] and search_params['date_posted'] != 'any':
            try:
                date_posted_days = int(search_params['date_posted'])
                logger.info(f"User requested jobs from past {date_posted_days} days")
            except ValueError:
                logger.warning(f"Invalid date_posted value: {search_params['date_posted']}")
        
        # Get user profile and AI settings
        user_profile = config_manager.get_user_profile()
        ai_settings = config_manager.get_ai_settings()
        
        # Ensure resume is processed (lazy processing)
        resume_data = None
        if resume_manager:
            user_id = get_user_id()
            resume_data = resume_manager.ensure_resume_processed(user_id)
            if resume_data:
                logger.info(f"Using resume data for user {user_id}")
            else:
                logger.info(f"No resume data available for user {user_id}")
        
        # Extract filter parameters
        work_arrangement = search_params['work_arrangement'][0] if search_params['work_arrangement'] else None
        experience_level = search_params['experience_level'][0] if search_params['experience_level'] else None
        job_type = search_params['job_type'][0] if search_params['job_type'] else None
        
        logger.info("Continuing LinkedIn scraping after CAPTCHA completion")
        
        # Initialize enhanced LinkedIn scraper with authentication
        from src.scrapers.linkedin_scraper_enhanced import EnhancedLinkedInScraper
        from src.utils.session_manager import SessionManager
        from src.scrapers.base_scraper import ScrapingConfig
        
        # Create session manager for persistent sessions
        session_manager = SessionManager()
        
        # Create scraping config with LinkedIn credentials
        config = ScrapingConfig(
            max_jobs_per_session=50,
            delay_min=2.0,
            delay_max=3.0,
            max_retries=3,
            page_load_timeout=30,
            site_name="linkedin",
            base_url="https://www.linkedin.com"
        )
        
        # Add LinkedIn credentials to config
        linkedin_config = config_manager.get_linkedin_settings()
        config.linkedin_username = linkedin_config.username
        config.linkedin_password = linkedin_config.password
        
        # Initialize enhanced scraper with authentication
        scraper = EnhancedLinkedInScraper(config, session_manager)
        
        try:
            # Split keywords into list
            keywords = [kw.strip() for kw in search_params['keywords'].split(',') if kw.strip()]
            
            # Scrape jobs with date filtering (authentication required for LinkedIn)
            logger.info(f"Continuing LinkedIn scraping with keywords: {keywords}, location: {search_params['location']}")
            if date_posted_days:
                logger.info(f"Applying date filter: past {date_posted_days} days")
            
            scraping_result = scraper.scrape_jobs_with_enhanced_date_filter(
                keywords=keywords,
                location=search_params['location'],
                date_posted_days=date_posted_days,
                require_auth=True,  # Authentication required for LinkedIn
                work_arrangement=work_arrangement,
                experience_level=experience_level,
                job_type=job_type
            )
            
            if not scraping_result.success:
                # Check if it's a CAPTCHA challenge
                if ("captcha" in scraping_result.error_message.lower() or 
                    "puzzle" in scraping_result.error_message.lower() or 
                    "security challenge" in scraping_result.error_message.lower()):
                    return jsonify({
                        'error': 'CAPTCHA_CHALLENGE',
                        'message': 'LinkedIn requires manual verification. Please complete the security challenge in the browser window and try again.',
                        'requires_manual_intervention': True
                    })
                return jsonify({'error': f'LinkedIn scraping failed: {scraping_result.error_message}'})
            
            # Analyze scraped jobs
            results = []
            for job in scraping_result.jobs[:20]:  # Limit to first 20 jobs
                try:
                    # Create analysis request with resume data
                    request_obj = AnalysisRequest(
                        job_title=job.title,
                        company=job.company,
                        job_description=job.description or "No description available",
                        user_profile=user_profile,
                        ai_settings=ai_settings,
                        resume_data=resume_data
                    )
                    
                    # Run analysis
                    analysis_response = qualification_analyzer.analyze_job_qualification(request_obj)
                    
                    # Create result object
                    result = {
                        'job_title': job.title,
                        'company': job.company,
                        'location': job.location or "Unknown Location",
                        'job_url': job.job_url,
                        'score': analysis_response.qualification_score,
                        'status': analysis_response.qualification_status.value,
                        'reasoning': analysis_response.ai_reasoning,
                        'strengths': analysis_response.matching_strengths,
                        'concerns': analysis_response.potential_concerns,
                        'required_experience': analysis_response.required_experience,
                        'education_requirements': analysis_response.education_requirements,
                        'key_skills': analysis_response.key_skills_mentioned,
                        'posted_date': job.posted_date.isoformat() if job.posted_date else None,
                        'job_type': job.job_type.value if job.job_type else None,
                        'experience_level': job.experience_level.value if job.experience_level else None
                    }
                    
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error analyzing job {job.title}: {e}")
                    continue
            
            # Store results in cache and session
            analysis_id = f"linkedin_{int(time.time())}"
            analysis_cache[analysis_id] = results
            session['current_analysis_id'] = analysis_id
            
            return jsonify({
                'success': True,
                'results': results,
                'total_jobs': len(results),
                'analysis_id': analysis_id,
                'date_filter_applied': date_posted_days is not None,
                'date_filter_days': date_posted_days
            })
            
        except Exception as e:
            logger.error(f"LinkedIn scraping error after CAPTCHA: {e}")
            return jsonify({'error': f'LinkedIn scraping failed: {str(e)}'})
        finally:
            # Cleanup scraper
            try:
                scraper.cleanup()
            except:
                pass
                
    except Exception as e:
        logger.error(f"CAPTCHA handling error: {e}")
        return jsonify({'error': f'CAPTCHA handling failed: {str(e)}'})


@app.route('/search/linkedin', methods=['POST'])
def search_linkedin_jobs():
    """Search LinkedIn jobs with date filtering using Selenium."""
    try:
        if config_manager is None or qualification_analyzer is None:
            return jsonify({'error': 'System not properly initialized. Please restart the application.'})
        
        # Extract search parameters including all filters
        search_params = {
            'keywords': request.form.get('keywords', '').strip(),
            'location': request.form.get('location', '').strip(),
            'date_posted': request.form.get('date_posted'),
            'qualification_threshold': int(request.form.get('qualification_threshold', 70)),
            'work_arrangement': request.form.getlist('work_arrangement'),
            'experience_level': request.form.getlist('experience_level'),
            'job_type': request.form.getlist('job_type')
        }
        
        # Debug logging for filter data
        logger.info(f"DEBUG: Raw form data received:")
        logger.info(f"  work_arrangement (getlist): {request.form.getlist('work_arrangement')}")
        logger.info(f"  experience_level (getlist): {request.form.getlist('experience_level')}")
        logger.info(f"  job_type (getlist): {request.form.getlist('job_type')}")
        logger.info(f"  work_arrangement (get): {request.form.get('work_arrangement')}")
        logger.info(f"  experience_level (get): {request.form.get('experience_level')}")
        logger.info(f"  job_type (get): {request.form.get('job_type')}")
        logger.info(f"  All form keys: {list(request.form.keys())}")
        
        # Validate required parameters
        if not search_params['keywords']:
            return jsonify({'error': 'Keywords are required'})
        
        if not search_params['location']:
            return jsonify({'error': 'Location is required'})
        
        # Convert date_posted to integer days for LinkedIn scraper
        date_posted_days = None
        if search_params['date_posted'] and search_params['date_posted'] != 'any':
            try:
                date_posted_days = int(search_params['date_posted'])
                logger.info(f"User requested jobs from past {date_posted_days} days")
            except ValueError:
                logger.warning(f"Invalid date_posted value: {search_params['date_posted']}")
        
        # Get user profile and AI settings
        user_profile = config_manager.get_user_profile()
        ai_settings = config_manager.get_ai_settings()
        
        # Ensure resume is processed (lazy processing)
        resume_data = None
        if resume_manager:
            user_id = get_user_id()
            resume_data = resume_manager.ensure_resume_processed(user_id)
            if resume_data:
                logger.info(f"Using resume data for user {user_id}")
            else:
                logger.info(f"No resume data available for user {user_id}")
        
        # Check if any filters that require UI interaction are selected
        work_arrangement = search_params['work_arrangement'][0] if search_params['work_arrangement'] else None
        experience_level = search_params['experience_level'][0] if search_params['experience_level'] else None
        job_type = search_params['job_type'][0] if search_params['job_type'] else None
        
        # Define default LinkedIn filter values
        linkedin_defaults = {
            "sort_by": "Most relevant",
            "date_posted": "Any time", 
            "experience_level": None,
            "company": None,
            "job_type": None,
            "remote": None
        }
        
        # Check if any non-default filters are applied
        has_custom_filters = False
        
        # Check date filter
        if date_posted_days is not None:
            has_custom_filters = True
            logger.info(f"Date filter detected: past {date_posted_days} days")
            
        # Check work arrangement (Remote filter)
        if work_arrangement:
            has_custom_filters = True
            logger.info(f"Work arrangement filter detected: {work_arrangement}")
            
        # Check experience level
        if experience_level:
            has_custom_filters = True
            logger.info(f"Experience level filter detected: {experience_level}")
            
        # Check job type
        if job_type:
            has_custom_filters = True
            logger.info(f"Job type filter detected: {job_type}")
        
        logger.info(f"Filter detection result: has_custom_filters = {has_custom_filters}")
        logger.info(f"Applied filters: date_posted_days={date_posted_days}, work_arrangement={work_arrangement}, experience_level={experience_level}, job_type={job_type}")
        
        # Determine which scraper to use based on filters
        if not has_custom_filters:
            # No custom filters selected - use regular scraping without browser
            logger.info("No custom filters selected - using regular LinkedIn scraping without authentication")
            
            try:
                # Use the regular job processor for basic LinkedIn scraping
                from src.utils.job_link_processor import JobLinkProcessor
                
                # Build LinkedIn search URL
                keywords = search_params['keywords'].replace(' ', '%20')
                location = search_params['location'].replace(' ', '%20')
                search_url = f"https://www.linkedin.com/jobs/search/?keywords={keywords}&location={location}"
                
                job_processor = JobLinkProcessor()
                job_links = job_processor.process_job_links([search_url])
                
                if not job_links:
                    return jsonify({'error': 'No jobs found in the provided URLs'})
                
                # Analyze scraped jobs
                results = []
                for job_link in job_links[:20]:  # Limit to first 20 jobs
                    if job_link.error or not job_link.title:
                        continue
                    try:
                        # Create analysis request with resume data
                        request_obj = AnalysisRequest(
                            job_title=job_link.title,
                            company=job_link.company,
                            job_description=job_link.description or "No description available",
                            user_profile=user_profile,
                            ai_settings=ai_settings,
                            resume_data=resume_data
                        )
                        
                        # Run analysis
                        analysis_response = qualification_analyzer.analyze_job_qualification(request_obj)
                        
                        results.append({
                            'job_title': job_link.title,
                            'company': job_link.company,
                            'location': job_link.location or "Unknown Location",
                            'job_url': job_link.url,
                            'score': analysis_response.qualification_score,
                            'status': analysis_response.qualification_status.value,
                            'reasoning': analysis_response.ai_reasoning,
                            'strengths': analysis_response.matching_strengths,
                            'concerns': analysis_response.potential_concerns,
                            'required_experience': analysis_response.required_experience,
                            'education_requirements': analysis_response.education_requirements,
                            'key_skills': analysis_response.key_skills_mentioned
                        })
                    except Exception as e:
                        logger.error(f"Error analyzing job {job_link.title}: {e}")
                        continue
                
                # Store results in cache and session
                analysis_id = f"linkedin_{int(time.time())}"
                analysis_cache[analysis_id] = results
                session['current_analysis_id'] = analysis_id
                
                return jsonify({
                    'success': True,
                    'results': results,
                    'total_jobs': len(results),
                    'analysis_id': analysis_id,
                    'date_filter_applied': False,
                    'date_filter_days': None
                })
                
            except Exception as e:
                logger.error(f"Regular LinkedIn scraping error: {e}")
                return jsonify({'error': f'LinkedIn scraping failed: {str(e)}'})
                
        else:
            # Custom filters that require UI interaction selected - use fixed scraper with authentication
            filter_info = []
            if date_posted_days:
                filter_info.append(f"date filter ({date_posted_days} days)")
            if work_arrangement:
                filter_info.append(f"work arrangement ({work_arrangement})")
            if experience_level:
                filter_info.append(f"experience level ({experience_level})")
            if job_type:
                filter_info.append(f"job type ({job_type})")
            
            logger.info(f"Custom filters requiring UI interaction selected: {', '.join(filter_info)} - using enhanced scraper with authentication")
            
            # Initialize enhanced LinkedIn scraper (supports all filters with proper clicking)
            from src.scrapers.linkedin_scraper_enhanced import EnhancedLinkedInScraper
            from src.utils.session_manager import SessionManager
            from src.scrapers.base_scraper import ScrapingConfig
            
            # Create session manager for persistent sessions
            session_manager = SessionManager()
            
            # Create scraping config with LinkedIn credentials
            config = ScrapingConfig(
                max_jobs_per_session=50,
                delay_min=2.0,
                delay_max=3.0,
                max_retries=3,
                page_load_timeout=30,
                site_name="linkedin",
                base_url="https://www.linkedin.com"
            )
            
            # Add LinkedIn credentials to config
            linkedin_config = config_manager.get_linkedin_settings()
            config.linkedin_username = linkedin_config.username
            config.linkedin_password = linkedin_config.password
            
            # Initialize enhanced scraper with authentication
            scraper = EnhancedLinkedInScraper(config, session_manager)
            
            try:
                # Split keywords into list
                keywords = [kw.strip() for kw in search_params['keywords'].split(',') if kw.strip()]
                
                # Scrape jobs with date filtering (authentication required for LinkedIn)
                logger.info(f"Starting LinkedIn scraping with keywords: {keywords}, location: {search_params['location']}")
                if date_posted_days:
                    logger.info(f"Applying date filter: past {date_posted_days} days")
                

                
                scraping_result = scraper.scrape_jobs_with_enhanced_date_filter(
                    keywords=keywords,
                    location=search_params['location'],
                    date_posted_days=date_posted_days,
                    require_auth=True,  # Authentication required for LinkedIn
                    work_arrangement=work_arrangement,
                    experience_level=experience_level,
                    job_type=job_type
                )
                
                # Debug logging for scraping result
                logger.info(f"Scraping result received - success: {scraping_result.success}")
                if not scraping_result.success:
                    logger.info(f"Scraping result error: {scraping_result.error_message}")
                else:
                    logger.info(f"Scraping result jobs count: {len(scraping_result.jobs)}")
                
                if not scraping_result.success:
                    # Debug logging
                    logger.info(f"Scraping failed with error: {scraping_result.error_message}")
                    
                    # Check if it's a CAPTCHA challenge
                    if ("captcha" in scraping_result.error_message.lower() or 
                        "puzzle" in scraping_result.error_message.lower() or 
                        "security challenge" in scraping_result.error_message.lower()):
                        logger.info("CAPTCHA challenge detected - returning CAPTCHA_CHALLENGE response")
                        return jsonify({
                            'error': 'CAPTCHA_CHALLENGE',
                            'message': 'LinkedIn requires manual verification. Please complete the security challenge in the browser window and try again.',
                            'requires_manual_intervention': True
                        })
                    logger.info("Regular error - returning standard error response")
                    return jsonify({'error': f'LinkedIn scraping failed: {scraping_result.error_message}'})
                
                # Analyze scraped jobs
                results = []
                for job in scraping_result.jobs[:20]:  # Limit to first 20 jobs
                    try:
                        # Create analysis request with resume data
                        request_obj = AnalysisRequest(
                            job_title=job.title,
                            company=job.company,
                            job_description=job.description or "No description available",
                            user_profile=user_profile,
                            ai_settings=ai_settings,
                            resume_data=resume_data
                        )
                        
                        # Run analysis
                        analysis_response = qualification_analyzer.analyze_job_qualification(request_obj)
                        
                        # Create result object
                        result = {
                            'job_title': job.title,
                            'company': job.company,
                            'location': job.location or "Unknown Location",
                            'job_url': job.job_url,
                            'score': analysis_response.qualification_score,
                            'status': analysis_response.qualification_status.value,
                            'reasoning': analysis_response.ai_reasoning,
                            'strengths': analysis_response.matching_strengths,
                            'concerns': analysis_response.potential_concerns,
                            'required_experience': analysis_response.required_experience,
                            'education_requirements': analysis_response.education_requirements,
                            'key_skills': analysis_response.key_skills_mentioned,
                            'posted_date': job.posted_date.isoformat() if job.posted_date else None,
                            'job_type': job.job_type.value if job.job_type else None,
                            'experience_level': job.experience_level.value if job.experience_level else None
                        }
                        
                        results.append(result)
                        
                    except Exception as e:
                        logger.error(f"Error analyzing job {job.title}: {e}")
                        continue
                
                # Store results in server-side cache
                analysis_id = str(uuid.uuid4())
                analysis_cache[analysis_id] = results
                session['current_analysis_id'] = analysis_id
                
                # Clean up old analysis results
                cleanup_old_analysis_results()
                
                logger.info(f"LinkedIn search completed - found {len(results)} jobs")
                
                return jsonify({
                    'success': True,
                    'results': results,
                    'total_jobs': len(results),
                    'analysis_id': analysis_id,
                    'date_filter_applied': date_posted_days is not None,
                    'date_filter_days': date_posted_days
                })
                
            finally:
                # Always cleanup the scraper
                scraper.cleanup()
                
    except Exception as e:
        logger.error(f"Error in LinkedIn job search: {e}")
        return jsonify({'error': f'LinkedIn search failed: {str(e)}'})


@app.route('/results')
def results():
    """Display analysis results."""
    analysis_id = session.get('current_analysis_id')
    if not analysis_id:
        flash("No analysis results available. Please perform a search first.", 'info')
        return redirect(url_for('search'))
    
    results = analysis_cache.get(analysis_id)
    if not results:
        flash("Analysis results not found in cache.", 'info')
        return redirect(url_for('search'))
    
    # Get qualification threshold from session or use default
    qualification_threshold = session.get('qualification_threshold', 70)
    
    return render_template('results.html', 
                         results=results, 
                         qualification_threshold=qualification_threshold)


@app.route('/results/save', methods=['POST'])
def save_results():
    """Save qualified jobs to Google Sheets."""
    try:
        if sheets_manager is None:
            return jsonify({'error': 'Google Sheets not configured'})
        
        # Get results from cache instead of session
        analysis_id = session.get('current_analysis_id')
        if not analysis_id:
            return jsonify({'error': 'No analysis results available'})
        
        results = analysis_cache.get(analysis_id)
        if not results:
            return jsonify({'error': 'Analysis results not found'})
        
        # Filter for qualified jobs (score >= 60)
        qualified_jobs = [r for r in results if r['score'] >= 60]
        
        if not qualified_jobs:
            return jsonify({'error': 'No qualified jobs to save'})
        
        # Save to Google Sheets
        saved_count = 0
        skipped_count = 0
        
        for job_data in qualified_jobs:
            qualification_result = QualificationResult(
                job_title=job_data['job_title'],
                company=job_data['company'],
                job_url=job_data['job_url'],
                qualification_score=job_data['score'],
                qualification_status=QualificationStatus(job_data['status']),
                ai_reasoning=job_data['reasoning'],
                required_experience=job_data['required_experience'],
                education_requirements=job_data['education_requirements'],
                key_skills_mentioned=job_data['key_skills'],
                matching_strengths=job_data['strengths'],
                potential_concerns=job_data['concerns'],
                user_decision=UserDecision.APPROVED
            )
            
            if sheets_manager.write_qualification_result(qualification_result):
                saved_count += 1
            else:
                skipped_count += 1  # This will be duplicates
        
        # Create appropriate message
        if saved_count > 0 and skipped_count > 0:
            flash(f'Successfully saved {saved_count} new jobs to Google Sheets! Skipped {skipped_count} duplicates.', 'success')
        elif saved_count > 0:
            flash(f'Successfully saved {saved_count} qualified jobs to Google Sheets!', 'success')
        elif skipped_count > 0:
            flash(f'All {skipped_count} jobs were already in Google Sheets (duplicates skipped).', 'info')
        else:
            flash('No jobs were saved. Please check the logs for errors.', 'warning')
        
        return jsonify({
            'success': True, 
            'saved_count': saved_count,
            'skipped_count': skipped_count
        })
        
    except Exception as e:
        logger.error(f"Error saving results: {e}")
        return jsonify({'error': f'Save failed: {str(e)}'})


@app.route('/results/save_single', methods=['POST'])
def save_single_job():
    """Save a single job to Google Sheets."""
    try:
        if sheets_manager is None:
            return jsonify({'error': 'Google Sheets not configured'})
        
        job_url = request.form.get('job_url')
        if not job_url:
            return jsonify({'error': 'No job URL provided'})
        
        # Get results from cache
        analysis_id = session.get('current_analysis_id')
        if not analysis_id:
            return jsonify({'error': 'No analysis results available'})
        
        results = analysis_cache.get(analysis_id)
        if not results:
            return jsonify({'error': 'Analysis results not found'})
        
        # Log for debugging
        logger.info(f"Looking for job URL: {job_url}")
        logger.info(f"Available job URLs: {[r['job_url'] for r in results]}")
        
        # Find the specific job
        job_data = None
        for result in results:
            if result['job_url'] == job_url:
                job_data = result
                logger.info(f"Found job: {job_data['job_title']}")
                break
        
        if not job_data:
            logger.error(f"Job not found for URL: {job_url}")
            return jsonify({'error': 'Job not found in results'})
        
        # Create qualification result
        qualification_result = QualificationResult(
            job_title=job_data['job_title'],
            company=job_data['company'],
            job_url=job_data['job_url'],
            qualification_score=job_data['score'],
            qualification_status=QualificationStatus(job_data['status']),
            ai_reasoning=job_data['reasoning'],
            required_experience=job_data['required_experience'],
            education_requirements=job_data['education_requirements'],
            key_skills_mentioned=job_data['key_skills'],
            matching_strengths=job_data['strengths'],
            potential_concerns=job_data['concerns'],
            user_decision=UserDecision.APPROVED
        )
        
        # Save to Google Sheets
        if sheets_manager.write_qualification_result(qualification_result):
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Job already exists in Google Sheets'})
        
    except Exception as e:
        logger.error(f"Error saving single job: {e}")
        return jsonify({'error': f'Save failed: {str(e)}'})


@app.route('/results/save_all', methods=['POST'])
def save_all_qualified_jobs():
    """Save all qualified jobs to Google Sheets."""
    try:
        if sheets_manager is None:
            return jsonify({'error': 'Google Sheets not configured'})
        
        # Get results from cache
        analysis_id = session.get('current_analysis_id')
        if not analysis_id:
            return jsonify({'error': 'No analysis results available'})
        
        results = analysis_cache.get(analysis_id)
        if not results:
            return jsonify({'error': 'Analysis results not found'})
        
        # Get qualification threshold from session or use default
        qualification_threshold = session.get('qualification_threshold', 70)
        
        # Filter for qualified jobs based on threshold
        qualified_jobs = [r for r in results if r['score'] >= qualification_threshold]
        
        if not qualified_jobs:
            return jsonify({'error': 'No qualified jobs to save'})
        
        # Save to Google Sheets
        saved_count = 0
        for job_data in qualified_jobs:
            qualification_result = QualificationResult(
                job_title=job_data['job_title'],
                company=job_data['company'],
                job_url=job_data['job_url'],
                qualification_score=job_data['score'],
                qualification_status=QualificationStatus(job_data['status']),
                ai_reasoning=job_data['reasoning'],
                required_experience=job_data['required_experience'],
                education_requirements=job_data['education_requirements'],
                key_skills_mentioned=job_data['key_skills'],
                matching_strengths=job_data['strengths'],
                potential_concerns=job_data['concerns'],
                user_decision=UserDecision.APPROVED
            )
            
            if sheets_manager.write_qualification_result(qualification_result):
                saved_count += 1
        
        return jsonify({
            'success': True,
            'count': saved_count
        })
        
    except Exception as e:
        logger.error(f"Error saving all qualified jobs: {e}")
        return jsonify({'error': f'Save failed: {str(e)}'})


@app.route('/results/save_all_jobs', methods=['POST'])
def save_all_jobs():
    """Save ALL jobs (not just qualified ones) to Google Sheets."""
    try:
        if sheets_manager is None:
            return jsonify({'error': 'Google Sheets not configured'})
        
        # Get results from cache
        analysis_id = session.get('current_analysis_id')
        if not analysis_id:
            return jsonify({'error': 'No analysis results available'})
        
        results = analysis_cache.get(analysis_id)
        if not results:
            return jsonify({'error': 'Analysis results not found'})
        
        if not results:
            return jsonify({'error': 'No jobs to save'})
        
        # Save ALL jobs to Google Sheets (not just qualified ones)
        saved_count = 0
        for job_data in results:
            qualification_result = QualificationResult(
                job_title=job_data['job_title'],
                company=job_data['company'],
                job_url=job_data['job_url'],
                qualification_score=job_data['score'],
                qualification_status=QualificationStatus(job_data['status']),
                ai_reasoning=job_data['reasoning'],
                required_experience=job_data['required_experience'],
                education_requirements=job_data['education_requirements'],
                key_skills_mentioned=job_data['key_skills'],
                matching_strengths=job_data['strengths'],
                potential_concerns=job_data['concerns'],
                user_decision=UserDecision.APPROVED
            )
            
            if sheets_manager.write_qualification_result(qualification_result):
                saved_count += 1
        
        return jsonify({
            'success': True,
            'count': saved_count
        })
        
    except Exception as e:
        logger.error(f"Error saving all jobs: {e}")
        return jsonify({'error': f'Save failed: {str(e)}'})


@app.route('/resume/upload', methods=['POST'])
def upload_resume():
    """Handle resume upload with lazy processing."""
    try:
        if resume_manager is None:
            return jsonify({'error': 'Resume system not initialized'}), 500
        
        if 'resume' not in request.files:
            return jsonify({'error': 'No file selected'}), 400
        
        file = request.files['resume']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload PDF or DOCX'}), 400
        
        # Save file to temporary location
        user_id = get_user_id()
        filename = secure_filename(file.filename)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name
        
        try:
            # Upload to resume manager
            result = resume_manager.upload_resume(user_id, temp_file_path, filename)
            
            if result['success']:
                logger.info(f"Resume uploaded successfully for user {user_id}: {filename}")
                return jsonify(result)
            else:
                return jsonify(result), 400
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except Exception as e:
        logger.error(f"Error uploading resume: {e}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@app.route('/resume/status')
def get_resume_status():
    """Get the current resume status for the user."""
    try:
        if resume_manager is None:
            return jsonify({'error': 'Resume system not initialized'}), 500
        
        user_id = get_user_id()
        status = resume_manager.get_resume_status(user_id)
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting resume status: {e}")
        return jsonify({'error': f'Failed to get status: {str(e)}'}), 500





@app.route('/settings')
def settings():
    """System settings page."""
    try:
        if config_manager is None:
            flash("System not properly initialized. Please restart the application.", 'error')
            return render_template('settings.html', ai_settings=None, api_settings=None)
        
        ai_settings = config_manager.get_ai_settings()
        api_settings = config_manager.get_api_settings()
        return render_template('settings.html', ai_settings=ai_settings, api_settings=api_settings)
    except Exception as e:
        flash(f"Error loading settings: {e}", 'error')
        return render_template('settings.html', ai_settings=None, api_settings=None)


@app.route('/settings/update', methods=['POST'])
def update_settings():
    """Update system settings."""
    try:
        if config_manager is None:
            flash("System not properly initialized. Please restart the application.", 'error')
            return redirect(url_for('settings'))
        
        # Update AI settings
        ai_data = {
            'api_key': request.form.get('ai_api_key', ''),
            'model': request.form.get('ai_model', 'gemini-2.0-flash-lite'),
            'qualification_threshold': int(request.form.get('qualification_threshold', 70)),
            'max_tokens': int(request.form.get('max_tokens', 2000)),
            'temperature': float(request.form.get('temperature', 0.1))
        }
        
        # Update API settings
        api_data = {
            'google_sheets_spreadsheet_id': request.form.get('google_sheets_id', ''),
            'google_sheets_worksheet_name': request.form.get('google_sheets_worksheet', 'Qualified Jobs')
        }
        
        config_manager.update_configuration_section('ai_settings', ai_data)
        config_manager.update_configuration_section('api_settings', api_data)
        config_manager.save_configuration()
        
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('settings'))
        
    except Exception as e:
        flash(f"Error updating settings: {e}", 'error')
        return redirect(url_for('settings'))


@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'system_initialized': config_manager is not None,
        'timestamp': datetime.now().isoformat()
    })


# Job Results Page Routes
@app.route('/jobs')
def jobs_page():
    """Main jobs page showing all job opportunities and application status."""
    user_id = get_user_id()
    
    # Get filters from query parameters
    company_filter = request.args.get('company', '')
    location_filter = request.args.get('location', '')
    status_filter = request.args.get('status', '')
    salary_min = request.args.get('salary_min', '')
    salary_max = request.args.get('salary_max', '')
    page = int(request.args.get('page', 1))
    per_page = 20
    
    # Build filters dict
    filters = {}
    if company_filter:
        filters['company'] = company_filter
    if location_filter:
        filters['location'] = location_filter
    if salary_min:
        filters['salary_min'] = int(salary_min)
    if salary_max:
        filters['salary_max'] = int(salary_max)
    
    try:
        # Get job listings with filters
        job_listings = job_tracker.search_job_listings(user_id, filters, limit=per_page)
        
        # Get application status for each job
        jobs_with_status = []
        for job in job_listings:
            application = job_tracker.get_job_application(user_id, job.id)
            is_favorited = job_tracker.is_job_favorited(user_id, job.id)
            
            jobs_with_status.append({
                'job': job,
                'application': application,
                'is_favorited': is_favorited
            })
        
        # Get application analytics
        analytics = job_tracker.get_application_analytics(user_id, days=30)
        
        return render_template('jobs.html', 
                             jobs=jobs_with_status,
                             analytics=analytics,
                             filters={
                                 'company': company_filter,
                                 'location': location_filter,
                                 'status': status_filter,
                                 'salary_min': salary_min,
                                 'salary_max': salary_max
                             },
                             page=page)
                             
    except Exception as e:
        logger.error(f"Error loading jobs page: {e}")
        flash('Error loading jobs. Please try again.', 'error')
        return render_template('jobs.html', jobs=[], analytics={}, filters={}, page=1)


@app.route('/jobs/<job_id>')
def job_detail(job_id):
    """Detailed view of a specific job."""
    user_id = get_user_id()
    
    try:
        job = job_tracker.get_job_listing(job_id)
        if not job:
            flash('Job not found.', 'error')
            return redirect(url_for('jobs_page'))
        
        application = job_tracker.get_job_application(user_id, job_id)
        is_favorited = job_tracker.is_job_favorited(user_id, job_id)
        
        return render_template('job_detail.html', 
                             job=job,
                             application=application,
                             is_favorited=is_favorited)
                             
    except Exception as e:
        logger.error(f"Error loading job detail: {e}")
        flash('Error loading job details.', 'error')
        return redirect(url_for('jobs_page'))


@app.route('/api/jobs/apply', methods=['POST'])
def apply_to_job():
    """Mark a job as applied to."""
    user_id = get_user_id()
    data = request.get_json()
    
    job_id = data.get('job_id')
    applied_date = data.get('applied_date')
    application_method = data.get('application_method', 'manual')
    notes = data.get('notes', '')
    
    if not job_id:
        return jsonify({'error': 'Job ID is required'}), 400
    
    try:
        # Check if application already exists
        existing_application = job_tracker.get_job_application(user_id, job_id)
        
        if existing_application:
            # Update existing application
            job_tracker.update_application_status(
                user_id, job_id, 
                ApplicationStatus.APPLIED, 
                notes
            )
            message = 'Application updated successfully'
        else:
            # Create new application
            application = JobApplication(
                user_id=user_id,
                job_id=job_id,
                applied_date=datetime.fromisoformat(applied_date) if applied_date else datetime.now(),
                application_method=ApplicationMethod(application_method),
                status=ApplicationStatus.APPLIED,
                notes=notes
            )
            job_tracker.save_job_application(application)
            message = 'Application recorded successfully'
        
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        logger.error(f"Error applying to job: {e}")
        return jsonify({'error': 'Failed to record application'}), 500


@app.route('/api/jobs/status', methods=['POST'])
def update_application_status():
    """Update application status."""
    user_id = get_user_id()
    data = request.get_json()
    
    job_id = data.get('job_id')
    status = data.get('status')
    notes = data.get('notes', '')
    
    if not job_id or not status:
        return jsonify({'error': 'Job ID and status are required'}), 400
    
    try:
        success = job_tracker.update_application_status(
            user_id, job_id, 
            ApplicationStatus(status), 
            notes
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Status updated successfully'})
        else:
            return jsonify({'error': 'Application not found'}), 404
            
    except Exception as e:
        logger.error(f"Error updating application status: {e}")
        return jsonify({'error': 'Failed to update status'}), 500


@app.route('/api/jobs/favorite', methods=['POST'])
def toggle_job_favorite():
    """Toggle job favorite status."""
    user_id = get_user_id()
    data = request.get_json()
    
    job_id = data.get('job_id')
    notes = data.get('notes', '')
    priority = data.get('priority', 1)
    
    if not job_id:
        return jsonify({'error': 'Job ID is required'}), 400
    
    try:
        is_favorited = job_tracker.is_job_favorited(user_id, job_id)
        
        if is_favorited:
            # Remove from favorites
            success = job_tracker.remove_job_favorite(user_id, job_id)
            message = 'Removed from favorites'
        else:
            # Add to favorites
            favorite = JobFavorite(
                user_id=user_id,
                job_id=job_id,
                notes=notes,
                priority=priority
            )
            job_tracker.add_job_favorite(favorite)
            message = 'Added to favorites'
            success = True
        
        return jsonify({
            'success': success,
            'message': message,
            'is_favorited': not is_favorited
        })
        
    except Exception as e:
        logger.error(f"Error toggling favorite: {e}")
        return jsonify({'error': 'Failed to update favorite status'}), 500


@app.route('/api/jobs/bulk-apply', methods=['POST'])
def bulk_apply_to_jobs():
    """Apply to multiple jobs at once."""
    user_id = get_user_id()
    data = request.get_json()
    
    job_ids = data.get('job_ids', [])
    applied_date = data.get('applied_date')
    application_method = data.get('application_method', 'manual')
    notes = data.get('notes', '')
    
    if not job_ids:
        return jsonify({'error': 'No jobs selected'}), 400
    
    try:
        success_count = 0
        for job_id in job_ids:
            try:
                # Check if application already exists
                existing_application = job_tracker.get_job_application(user_id, job_id)
                
                if not existing_application:
                    # Create new application
                    application = JobApplication(
                        user_id=user_id,
                        job_id=job_id,
                        applied_date=datetime.fromisoformat(applied_date) if applied_date else datetime.now(),
                        application_method=ApplicationMethod(application_method),
                        status=ApplicationStatus.APPLIED,
                        notes=notes
                    )
                    job_tracker.save_job_application(application)
                    success_count += 1
            except Exception as e:
                logger.error(f"Error applying to job {job_id}: {e}")
                continue
        
        return jsonify({
            'success': True,
            'message': f'Successfully applied to {success_count} jobs',
            'applied_count': success_count,
            'total_count': len(job_ids)
        })
        
    except Exception as e:
        logger.error(f"Error in bulk apply: {e}")
        return jsonify({'error': 'Failed to process bulk applications'}), 500


@app.route('/api/jobs/analytics')
def get_job_analytics():
    """Get job application analytics."""
    user_id = get_user_id()
    days = int(request.args.get('days', 30))
    
    try:
        analytics = job_tracker.get_application_analytics(user_id, days)
        return jsonify(analytics)
        
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        return jsonify({'error': 'Failed to load analytics'}), 500


@app.route('/api/jobs/search-history')
def get_search_history():
    """Get user's job search history."""
    user_id = get_user_id()
    limit = int(request.args.get('limit', 20))
    
    try:
        searches = job_tracker.get_user_job_searches(user_id, limit)
        return jsonify([search.to_dict() for search in searches])
        
    except Exception as e:
        logger.error(f"Error getting search history: {e}")
        return jsonify({'error': 'Failed to load search history'}), 500


@app.route('/api/jobs/favorites')
def get_favorites():
    """Get user's favorite jobs."""
    user_id = get_user_id()
    limit = int(request.args.get('limit', 50))
    
    try:
        favorites = job_tracker.get_user_favorites(user_id, limit)
        return jsonify([favorite.to_dict() for favorite in favorites])
        
    except Exception as e:
        logger.error(f"Error getting favorites: {e}")
        return jsonify({'error': 'Failed to load favorites'}), 500


# Template filters
@app.template_filter('nl2br')
def nl2br(value):
    """Convert newlines to <br> tags for HTML display."""
    if value:
        return value.replace('\n', '<br>')
    return value

@app.template_filter('get_status_color')
def get_status_color(status):
    """Get Bootstrap color class for application status."""
    status_colors = {
        'not_applied': 'secondary',
        'applied': 'success',
        'interviewing': 'warning',
        'offered': 'info',
        'rejected': 'danger',
        'withdrawn': 'secondary',
        'accepted': 'success'
    }
    return status_colors.get(status, 'secondary')

# Initialize system components immediately
try:
    initialize_system()
    print("✅ System initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize system components: {e}")
    print("   Some features may not work properly")

if __name__ == '__main__':
    print("🌐 Starting web server...")
    print("📱 Open http://localhost:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5000) 