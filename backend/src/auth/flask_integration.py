"""
Flask Integration for Supabase Authentication and Database

Provides decorators, utilities, and helpers for integrating Supabase
authentication and database operations with Flask applications.
"""

import os
import logging
from functools import wraps
from typing import Optional, Dict, Any
from flask import session, redirect, url_for, flash, request, current_app, g
from werkzeug.exceptions import Unauthorized, Forbidden
from dotenv import load_dotenv

load_dotenv()

from .supabase_auth_manager import SupabaseAuthManager
from ..data.supabase_manager import SupabaseManager

logger = logging.getLogger(__name__)


class FlaskSupabaseIntegration:
    """
    Flask integration for Supabase authentication and database operations.
    """
    
    def __init__(self, app=None):
        """
        Initialize the Flask-Supabase integration.
        
        Args:
            app: Flask application instance
        """
        self.auth_manager = None
        self.db_manager = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """
        Initialize the integration with a Flask app.
        
        Args:
            app: Flask application instance
        """
        # Get Supabase configuration
        supabase_url = app.config.get('SUPABASE_URL')
        supabase_key = app.config.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY must be configured")
        
        # Initialize managers
        self.auth_manager = SupabaseAuthManager(supabase_url, supabase_key)
        self.db_manager = SupabaseManager(supabase_url, supabase_key)
        
        # Register context processors
        app.context_processor(self._inject_user)
        
        # Register error handlers
        app.register_error_handler(401, self._handle_unauthorized)
        app.register_error_handler(403, self._handle_forbidden)
        
        logger.info("Flask-Supabase integration initialized successfully")
    
    def _inject_user(self):
        """
        Inject current user into template context.
        
        Returns:
            Dictionary with current user data
        """
        if self.auth_manager and self.auth_manager.is_authenticated():
            user = self.auth_manager.get_current_user()
            return {'current_user': user}
        return {'current_user': None}
    
    def _handle_unauthorized(self, error):
        """Handle 401 Unauthorized errors."""
        flash("Please log in to access this page.", "error")
        return redirect(url_for('auth.login_supabase'))
    
    def _handle_forbidden(self, error):
        """Handle 403 Forbidden errors."""
        flash("You don't have permission to access this page.", "error")
        return redirect(url_for('index'))
    
    def login_required(self, f):
        """
        Decorator to require authentication for routes.
        
        Args:
            f: Flask route function
            
        Returns:
            Decorated function
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not self.auth_manager or not self.auth_manager.is_authenticated():
                flash("Please log in to access this page.", "error")
                return redirect(url_for('auth.login_supabase'))
            return f(*args, **kwargs)
        return decorated_function
    
    def admin_required(self, f):
        """
        Decorator to require admin privileges for routes.
        
        Args:
            f: Flask route function
            
        Returns:
            Decorated function
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not self.auth_manager or not self.auth_manager.is_authenticated():
                flash("Please log in to access this page.", "error")
                return redirect(url_for('auth.login_supabase'))
            
            # Check if user is admin (you can customize this logic)
            user = self.auth_manager.get_current_user()
            if not user or user.get('subscription_status') != 'admin':
                flash("Admin privileges required.", "error")
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function


# Global instance
supabase_integration = FlaskSupabaseIntegration()


def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Get the current authenticated user.
    
    Returns:
        User data dictionary or None
    """
    if supabase_integration.auth_manager:
        return supabase_integration.auth_manager.get_current_user()
    return None


def get_user_id() -> Optional[str]:
    """
    Get the current user ID.
    
    Returns:
        User ID string or None
    """
    user = get_current_user()
    return user.get('user_id') if user else None


def is_authenticated() -> bool:
    """
    Check if user is currently authenticated.
    
    Returns:
        True if authenticated, False otherwise
    """
    if supabase_integration.auth_manager:
        return supabase_integration.auth_manager.is_authenticated()
    return False


def login_required(f):
    """
    Decorator to require authentication for routes.
    
    Args:
        f: Flask route function
        
    Returns:
        Decorated function
    """
    return supabase_integration.login_required(f)


def admin_required(f):
    """
    Decorator to require admin privileges for routes.
    
    Args:
        f: Flask route function
        
    Returns:
        Decorated function
    """
    return supabase_integration.admin_required(f)


def get_db_manager() -> Optional[SupabaseManager]:
    """
    Get the database manager instance.
    
    Returns:
        SupabaseManager instance or None
    """
    return supabase_integration.db_manager


def get_authenticated_db_manager() -> Optional[SupabaseManager]:
    """
    Get an authenticated database manager instance using the service role key to bypass RLS.
    
    Returns:
        SupabaseManager instance with admin privileges or None
    """
    if not supabase_integration.auth_manager or not supabase_integration.auth_manager.is_authenticated():
        return None
    
    try:
        # Get the current user's session
        from flask import session
        user_id = session.get('user_id')
        
        if not user_id:
            return None
        
        # Create a new Supabase client with the service role key to bypass RLS
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')  # Use service role key
        
        if not supabase_url or not supabase_key:
            logger.error("SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not found")
            return None
        
        # Create database manager with service role key
        db_manager = SupabaseManager(supabase_url, supabase_key)
        logger.info("Created authenticated database manager with service role key")
        
        return db_manager
        
    except Exception as e:
        logger.error(f"Error creating authenticated database manager: {e}")
        return None


def get_auth_manager() -> Optional[SupabaseAuthManager]:
    """
    Get the authentication manager instance.
    
    Returns:
        SupabaseAuthManager instance or None
    """
    return supabase_integration.auth_manager 