"""
Authentication routes for Flask application.

Handles user registration, login, logout, email verification,
and password reset functionality with Supabase integration.
"""

import os
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

from src.auth.flask_integration import get_auth_manager, get_db_manager, login_required, get_current_user
from src.data.supabase_manager import User

logger = logging.getLogger(__name__)

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    User registration route.
    
    GET: Display registration form
    POST: Process registration
    """
    if request.method == 'GET':
        return render_template('auth/register.html')
    
    # Handle POST request
    try:
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '').strip()
        
        # Validate input
        if not email or not password or not full_name:
            flash("All fields are required.", "error")
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template('auth/register.html')
        
        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "error")
            return render_template('auth/register.html')
        
        # Get auth manager
        auth_manager = get_auth_manager()
        if not auth_manager:
            flash("Authentication system not available.", "error")
            return render_template('auth/register.html')
        
        # Register user
        success, message, user_data = auth_manager.register_user(email, password, full_name)
        
        if success:
            # Create user record in database
            db_manager = get_db_manager()
            if db_manager:
                user_record = {
                    'user_id': user_data['user_id'],
                    'email': email,
                    'full_name': full_name,
                    'subscription_status': 'free',
                    'search_preferences': {}
                }
                
                db_success, db_message, user = db_manager.users.create_user(user_record)
                if not db_success:
                    logger.error(f"Failed to create user record: {db_message}")
            
            # Check if in testing mode
            testing_mode = os.getenv('TESTING_MODE', 'false').lower() == 'true'
            
            if testing_mode:
                # Auto-login in testing mode
                login_success, login_message, _ = auth_manager.login_user(email, password)
                if login_success:
                    flash("Registration successful! You are now logged in.", "success")
                    return redirect(url_for('index'))
                else:
                    flash(f"Registration successful but login failed: {login_message}", "warning")
                    return redirect(url_for('auth.login_supabase'))
            else:
                flash("Registration successful! Please check your email to verify your account.", "success")
                return redirect(url_for('auth.login_supabase'))
        else:
            flash(f"Registration failed: {message}", "error")
            return render_template('auth/register.html')
            
    except Exception as e:
        logger.error(f"Registration error: {e}")
        flash("An unexpected error occurred during registration.", "error")
        return render_template('auth/register.html')


@auth_bp.route('/register-supabase', methods=['GET'])
def register_supabase():
    """
    Supabase-based registration route.
    
    GET: Display registration form with Supabase JavaScript client
    """
    # Debug: Check if environment variables are available
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_anon_key = os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_anon_key:
        logger.warning("Missing Supabase environment variables")
        flash("Configuration error: Missing Supabase credentials", "error")
    
    return render_template('auth/register_supabase.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login route.
    
    GET: Display login form
    POST: Process login
    """
    if request.method == 'GET':
        return render_template('auth/login.html')
    
    # Handle POST request
    try:
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        # Validate input
        if not email or not password:
            flash("Email and password are required.", "error")
            return render_template('auth/login.html')
        
        # Get auth manager
        auth_manager = get_auth_manager()
        if not auth_manager:
            flash("Authentication system not available.", "error")
            return render_template('auth/login.html')
        
        # Login user
        success, message, user_data = auth_manager.login_user(email, password)
        
        if success:
            flash("Login successful!", "success")
            return redirect(url_for('index'))
        else:
            flash(f"Login failed: {message}", "error")
            return render_template('auth/login.html')
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        flash("An unexpected error occurred during login.", "error")
        return render_template('auth/login.html')


@auth_bp.route('/login-supabase', methods=['GET'])
def login_supabase():
    """
    Supabase-based login route.
    
    GET: Display login form with Supabase JavaScript client
    """
    return render_template('auth/login_supabase.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """
    User logout route.
    """
    try:
        # Get auth manager
        auth_manager = get_auth_manager()
        if auth_manager:
            auth_manager.logout_user()
        
        flash("You have been logged out successfully.", "success")
        return redirect(url_for('auth.login_supabase'))
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        flash("An error occurred during logout.", "error")
        return redirect(url_for('auth.login_supabase'))


@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    """
    Email verification route.
    """
    try:
        # Get auth manager
        auth_manager = get_auth_manager()
        if not auth_manager:
            flash("Authentication system not available.", "error")
            return redirect(url_for('auth.login_supabase'))
        
        # Verify email
        success, message = auth_manager.verify_email(token)
        
        if success:
            flash("Email verified successfully! You can now log in.", "success")
        else:
            flash(f"Email verification failed: {message}", "error")
        
        return redirect(url_for('auth.login_supabase'))
        
    except Exception as e:
        logger.error(f"Email verification error: {e}")
        flash("An error occurred during email verification.", "error")
        return redirect(url_for('auth.login_supabase'))


@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    """
    Resend email verification route.
    """
    try:
        email = request.form.get('email', '').strip()
        
        if not email:
            return jsonify({'success': False, 'message': 'Email is required'})
        
        # Get auth manager
        auth_manager = get_auth_manager()
        if not auth_manager:
            return jsonify({'success': False, 'message': 'Authentication system not available'})
        
        # Resend verification
        success, message = auth_manager.resend_verification(email)
        
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        logger.error(f"Resend verification error: {e}")
        return jsonify({'success': False, 'message': 'An unexpected error occurred'})


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """
    Forgot password route.
    
    GET: Display forgot password form
    POST: Process password reset request
    """
    if request.method == 'GET':
        return render_template('auth/forgot_password.html')
    
    # Handle POST request
    try:
        email = request.form.get('email', '').strip()
        
        if not email:
            flash("Email is required.", "error")
            return render_template('auth/forgot_password.html')
        
        # Get auth manager
        auth_manager = get_auth_manager()
        if not auth_manager:
            flash("Authentication system not available.", "error")
            return render_template('auth/forgot_password.html')
        
        # Send password reset
        success, message = auth_manager.send_password_reset(email)
        
        if success:
            flash("Password reset email sent. Please check your email.", "success")
        else:
            flash(f"Password reset failed: {message}", "error")
        
        return render_template('auth/forgot_password.html')
        
    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        flash("An unexpected error occurred.", "error")
        return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """
    Reset password route.
    
    GET: Display reset password form
    POST: Process password reset
    """
    if request.method == 'GET':
        return render_template('auth/reset_password.html', token=token)
    
    # Handle POST request
    try:
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not password or not confirm_password:
            flash("Password and confirmation are required.", "error")
            return render_template('auth/reset_password.html', token=token)
        
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template('auth/reset_password.html', token=token)
        
        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "error")
            return render_template('auth/reset_password.html', token=token)
        
        # Get auth manager
        auth_manager = get_auth_manager()
        if not auth_manager:
            flash("Authentication system not available.", "error")
            return render_template('auth/reset_password.html', token=token)
        
        # Reset password
        success, message = auth_manager.reset_password(token, password)
        
        if success:
            flash("Password reset successful! You can now log in with your new password.", "success")
            return redirect(url_for('auth.login_supabase'))
        else:
            flash(f"Password reset failed: {message}", "error")
            return render_template('auth/reset_password.html', token=token)
        
    except Exception as e:
        logger.error(f"Reset password error: {e}")
        flash("An unexpected error occurred.", "error")
        return render_template('auth/reset_password.html', token=token)


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """
    User profile route - redirects to main profile page.
    """
    # Redirect to main profile page instead of showing auth-specific profile
    return redirect(url_for('profile'))


@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """
    Change password route.
    """
    try:
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not current_password or not new_password or not confirm_password:
            return jsonify({'success': False, 'message': 'All fields are required'})
        
        if new_password != confirm_password:
            return jsonify({'success': False, 'message': 'New passwords do not match'})
        
        if len(new_password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters long'})
        
        # Get auth manager
        auth_manager = get_auth_manager()
        if not auth_manager:
            return jsonify({'success': False, 'message': 'Authentication system not available'})
        
        # Change password
        success, message = auth_manager.change_password(current_password, new_password)
        
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        logger.error(f"Change password error: {e}")
        return jsonify({'success': False, 'message': 'An unexpected error occurred'})


@auth_bp.route('/api/check-auth')
def check_auth():
    """
    API route to check authentication status.
    """
    try:
        # Get auth manager
        auth_manager = get_auth_manager()
        if not auth_manager:
            return jsonify({'authenticated': False, 'message': 'Authentication system not available'})
        
        # Check authentication
        user = auth_manager.get_current_user()
        
        if user:
            return jsonify({
                'authenticated': True,
                'user': {
                    'id': user.get('id'),
                    'email': user.get('email'),
                    'full_name': user.get('user_metadata', {}).get('full_name')
                }
            })
        else:
            return jsonify({'authenticated': False})
        
    except Exception as e:
        logger.error(f"Check auth error: {e}")
        return jsonify({'authenticated': False, 'message': 'An error occurred'}) 


@auth_bp.route('/api/verify-auth', methods=['POST'])
def verify_auth():
    """
    Verify authentication token from client-side Supabase auth.
    """
    try:
        # Get the access token from the request
        access_token = request.json.get('access_token')
        
        if not access_token:
            return jsonify({'success': False, 'error': 'No access token provided'})
        
        # Get auth manager
        auth_manager = get_auth_manager()
        if not auth_manager:
            return jsonify({'success': False, 'error': 'Authentication system not available'})
        
        # Verify the token and get user data
        success, message, user_data = auth_manager.verify_token(access_token)
        
        if success:
            # Store user data in session
            session['user_id'] = user_data.get('user_id')
            session['email'] = user_data.get('email')
            session['authenticated'] = True
            
            return jsonify({
                'success': True,
                'user': user_data
            })
        else:
            return jsonify({'success': False, 'error': message})
            
    except Exception as e:
        logger.error(f"Auth verification error: {e}")
        return jsonify({'success': False, 'error': 'An unexpected error occurred'})


@auth_bp.route('/api/set-session', methods=['POST'])
def set_session():
    """
    Set session data from client-side authentication.
    """
    try:
        # Get session data from request
        session_data = request.json.get('session')
        
        if not session_data:
            return jsonify({'success': False, 'error': 'No session data provided'})
        
        # Store user data in Flask session
        user = session_data.get('user', {})
        session['user_id'] = user.get('id')
        session['email'] = user.get('email')
        session['authenticated'] = True
        
        return jsonify({
            'success': True,
            'message': 'Session set successfully'
        })
        
    except Exception as e:
        logger.error(f"Set session error: {e}")
        return jsonify({'success': False, 'error': 'An unexpected error occurred'}) 