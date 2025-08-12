"""
Template Context Processors for Authentication

This module provides template context processors to make
authentication data available in all Flask templates.
"""

from flask import render_template
from typing import Dict, Any, Optional
from .auth_context import get_current_user, get_user_profile, is_authenticated

def auth_template_context() -> Dict[str, Any]:
    """
    Template context processor for authentication data.
    
    Returns:
        Dict containing auth-related variables for templates
    """
    try:
        current_user = get_current_user()
        user_profile = get_user_profile()
        authenticated = is_authenticated()
        
        return {
            'current_user': current_user,
            'user_profile': user_profile,
            'is_authenticated': authenticated,
            'user_email': current_user.get('email') if current_user else None,
            'user_id': current_user.get('id') if current_user else None,
            'email_verified': current_user.get('email_confirmed_at') is not None if current_user else False,
            'profile_completed': user_profile.get('profile_completed') if user_profile else False,
            'experience_level': user_profile.get('experience_level') if user_profile else None,
            'education_level': user_profile.get('education_level') if user_profile else None,
            'years_of_experience': user_profile.get('years_of_experience') if user_profile else None
        }
    except Exception as e:
        # Return safe defaults if auth context is not available
        return {
            'current_user': None,
            'user_profile': None,
            'is_authenticated': False,
            'user_email': None,
            'user_id': None,
            'email_verified': False,
            'profile_completed': False,
            'experience_level': None,
            'education_level': None,
            'years_of_experience': None
        }

def register_template_context_processors(app):
    """
    Register template context processors with Flask app.
    
    Args:
        app: Flask application instance
    """
    app.context_processor(auth_template_context)
    
    # Add custom template filters
    @app.template_filter('user_display_name')
    def user_display_name(user_profile):
        """Get user display name from profile or email."""
        if user_profile and user_profile.get('full_name'):
            return user_profile['full_name']
        elif user_profile and user_profile.get('user_email'):
            return user_profile['user_email']
        return 'User'
    
    @app.template_filter('user_avatar')
    def user_avatar(user_profile):
        """Get user avatar or default."""
        if user_profile and user_profile.get('avatar_url'):
            return user_profile['avatar_url']
        return '/static/images/default-avatar.png'
    
    @app.template_filter('experience_label')
    def experience_label(level):
        """Get human-readable experience level."""
        labels = {
            'entry': 'Entry Level',
            'junior': 'Junior',
            'mid': 'Mid-Level',
            'senior': 'Senior',
            'lead': 'Team Lead',
            'manager': 'Manager',
            'director': 'Director',
            'executive': 'Executive'
        }
        return labels.get(level, level.title())
    
    @app.template_filter('education_label')
    def education_label(level):
        """Get human-readable education level."""
        labels = {
            'high_school': 'High School',
            'associate': 'Associate Degree',
            'bachelors': 'Bachelor\'s Degree',
            'masters': 'Master\'s Degree',
            'doctorate': 'Doctorate',
            'other': 'Other'
        }
        return labels.get(level, level.title()) 