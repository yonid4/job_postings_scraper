"""
Authentication Context for Supabase Auth Integration

This module provides authentication state management and utilities
for the main application integration.
"""

import os
import logging
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from flask import session, request, redirect, url_for, flash
from functools import wraps

# Configure logging
logger = logging.getLogger(__name__)

class AuthContext:
    """
    Authentication context for managing Supabase Auth state.
    """
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.current_user = None
        self.user_profile = None
        self.is_loading = False
        self.last_check = None
        self.check_interval = timedelta(minutes=5)  # Check session every 5 minutes
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """
        Get the current authenticated user.
        
        Returns:
            Dict containing user data or None if not authenticated
        """
        try:
            # Check Flask session first
            from flask import session
            if session.get('authenticated') and session.get('user_id'):
                return {
                    'id': session.get('user_id'),
                    'email': session.get('email'),
                    'user_id': session.get('user_id'),
                    'full_name': session.get('full_name', ''),
                    'years_of_experience': session.get('years_of_experience', 0),
                    'experience_level': session.get('experience_level', ''),
                    'education_level': session.get('education_level', ''),
                    'work_arrangement_preference': session.get('work_arrangement_preference', ''),
                    'field_of_study': session.get('field_of_study', ''),
                    'skills_technologies': session.get('skills_technologies', ''),
                    'preferred_locations': session.get('preferred_locations', ''),
                    'salary_min': session.get('salary_min'),
                    'salary_max': session.get('salary_max'),
                    'linkedin_credentials': session.get('linkedin_credentials', '')
                }
            
            # Check if we have a recent session check
            if (self.last_check and 
                datetime.now() - self.last_check < self.check_interval and 
                self.current_user):
                return self.current_user
            
            # Get session from Supabase
            session_data = self.supabase.auth.get_session()
            
            if session_data and session_data.user:
                # Get user metadata
                user_metadata = session_data.user.user_metadata or {}
                
                self.current_user = {
                    'id': session_data.user.id,
                    'email': session_data.user.email,
                    'email_confirmed_at': session_data.user.email_confirmed_at,
                    'created_at': session_data.user.created_at,
                    'last_sign_in_at': session_data.user.last_sign_in_at,
                    'full_name': user_metadata.get('full_name', ''),
                    'years_of_experience': user_metadata.get('years_of_experience', 0),
                    'experience_level': user_metadata.get('experience_level', ''),
                    'education_level': user_metadata.get('education_level', ''),
                    'work_arrangement_preference': user_metadata.get('work_arrangement_preference', ''),
                    'field_of_study': user_metadata.get('field_of_study', ''),
                    'skills_technologies': user_metadata.get('skills_technologies', ''),
                    'preferred_locations': user_metadata.get('preferred_locations', ''),
                    'salary_min': user_metadata.get('salary_min'),
                    'salary_max': user_metadata.get('salary_max'),
                    'linkedin_credentials': user_metadata.get('linkedin_credentials', '')
                }
                self.last_check = datetime.now()
                return self.current_user
            else:
                self.current_user = None
                self.user_profile = None
                return None
                
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            self.current_user = None
            self.user_profile = None
            return None
    
    def get_user_profile(self) -> Optional[Dict[str, Any]]:
        """
        Get the current user's profile data.
        
        Returns:
            Dict containing profile data or None if not found
        """
        try:
            user = self.get_current_user()
            if not user:
                return None
            
            # Check if we have cached profile data
            if self.user_profile and self.user_profile.get('user_id') == user['id']:
                return self.user_profile
            
            # Fetch profile from database
            response = self.supabase.table('user_profiles').select('*').eq('user_id', user['id']).execute()
            
            if response.data:
                self.user_profile = response.data[0]
                return self.user_profile
            else:
                logger.warning(f"No profile found for user {user['id']}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None
    
    def is_authenticated(self) -> bool:
        """
        Check if user is currently authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        # Check Flask session first
        from flask import session
        if session.get('authenticated') and session.get('user_id'):
            return True
        
        # Fallback to Supabase client check
        return self.get_current_user() is not None
    
    def is_email_verified(self) -> bool:
        """
        Check if current user's email is verified.
        
        Returns:
            True if email is verified, False otherwise
        """
        user = self.get_current_user()
        return user and user.get('email_confirmed_at') is not None
    
    def logout(self) -> bool:
        """
        Logout the current user.
        
        Returns:
            True if logout successful, False otherwise
        """
        try:
            self.supabase.auth.sign_out()
            self.current_user = None
            self.user_profile = None
            self.last_check = None
            return True
        except Exception as e:
            logger.error(f"Error during logout: {e}")
            return False
    
    def refresh_session(self) -> bool:
        """
        Refresh the current session.
        
        Returns:
            True if refresh successful, False otherwise
        """
        try:
            self.supabase.auth.refresh_session()
            self.last_check = None  # Force re-check
            return True
        except Exception as e:
            logger.error(f"Error refreshing session: {e}")
            return False

# Global auth context instance
auth_context = None

def init_auth_context(supabase_client):
    """
    Initialize the global authentication context.
    
    Args:
        supabase_client: Configured Supabase client instance
    """
    global auth_context
    auth_context = AuthContext(supabase_client)
    logger.info("Authentication context initialized")

def get_auth_context() -> AuthContext:
    """
    Get the global authentication context.
    
    Returns:
        AuthContext instance
    """
    if auth_context is None:
        raise RuntimeError("Authentication context not initialized. Call init_auth_context() first.")
    return auth_context

# Flask integration utilities
def login_required(f: Callable) -> Callable:
    """
    Decorator to protect routes that require authentication.
    
    Args:
        f: Flask route function to protect
        
    Returns:
        Wrapped function that checks authentication
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = get_auth_context()
        
        if not auth.is_authenticated():
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('auth.login_supabase'))
        
        return f(*args, **kwargs)
    
    return decorated_function

def email_verified_required(f: Callable) -> Callable:
    """
    Decorator to protect routes that require email verification.
    
    Args:
        f: Flask route function to protect
        
    Returns:
        Wrapped function that checks email verification
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = get_auth_context()
        
        if not auth.is_authenticated():
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('auth.login_supabase'))
        
        if not auth.is_email_verified():
            flash("Please verify your email address to access this page.", "warning")
            return redirect(url_for('auth.verify_email'))
        
        return f(*args, **kwargs)
    
    return decorated_function

def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Get current user data for use in templates.
    
    Returns:
        Dict containing user data or None
    """
    try:
        auth = get_auth_context()
        return auth.get_current_user()
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        return None

def get_user_profile() -> Optional[Dict[str, Any]]:
    """
    Get current user profile data for use in templates.
    
    Returns:
        Dict containing profile data or None
    """
    try:
        auth = get_auth_context()
        return auth.get_user_profile()
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return None

def is_authenticated() -> bool:
    """
    Check if user is authenticated for use in templates.
    
    Returns:
        True if authenticated, False otherwise
    """
    try:
        auth = get_auth_context()
        return auth.is_authenticated()
    except Exception as e:
        logger.error(f"Error checking authentication: {e}")
        return False 