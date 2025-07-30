"""
Profile Management Routes

This module provides routes for user profile management
with Supabase Auth integration.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from src.auth.auth_context import login_required, get_auth_context, get_current_user, get_user_profile
from src.auth.template_context import auth_template_context
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile')
@login_required
def profile():
    """
    User profile page.
    
    GET: Display user profile with edit capabilities
    """
    try:
        auth = get_auth_context()
        current_user = get_current_user()
        user_profile = get_user_profile()
        
        if not current_user:
            flash("User not found.", "error")
            return redirect(url_for('auth.login'))
        
        return render_template('profile/profile.html', 
                            user=current_user, 
                            profile=user_profile)
                            
    except Exception as e:
        logger.error(f"Error loading profile page: {e}")
        flash("An error occurred while loading your profile.", "error")
        return redirect(url_for('index'))

@profile_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """
    Edit user profile.
    
    GET: Display profile edit form
    POST: Update profile data
    """
    try:
        auth = get_auth_context()
        current_user = get_current_user()
        user_profile = get_user_profile()
        
        if request.method == 'POST':
            # Get form data
            full_name = request.form.get('full_name', '').strip()
            years_of_experience = int(request.form.get('years_of_experience', 0))
            experience_level = request.form.get('experience_level', 'entry')
            education_level = request.form.get('education_level', 'bachelors')
            
            # Validate input
            if not full_name:
                flash("Full name is required.", "error")
                return render_template('profile/edit_profile.html', 
                                    user=current_user, 
                                    profile=user_profile)
            
            if years_of_experience < 0:
                flash("Years of experience cannot be negative.", "error")
                return render_template('profile/edit_profile.html', 
                                    user=current_user, 
                                    profile=user_profile)
            
            # Update profile in database
            try:
                response = auth.supabase.table('user_profiles').update({
                    'full_name': full_name,
                    'years_of_experience': years_of_experience,
                    'experience_level': experience_level,
                    'education_level': education_level,
                    'profile_completed': True
                }).eq('user_id', current_user['id']).execute()
                
                if response.data:
                    flash("Profile updated successfully!", "success")
                    return redirect(url_for('profile.profile'))
                else:
                    flash("Failed to update profile.", "error")
                    
            except Exception as e:
                logger.error(f"Error updating profile: {e}")
                flash("An error occurred while updating your profile.", "error")
        
        return render_template('profile/edit_profile.html', 
                            user=current_user, 
                            profile=user_profile)
                            
    except Exception as e:
        logger.error(f"Error in edit profile: {e}")
        flash("An error occurred.", "error")
        return redirect(url_for('profile.profile'))

@profile_bp.route('/profile/complete', methods=['POST'])
@login_required
def complete_profile():
    """
    Mark profile as completed.
    
    POST: Mark profile as completed
    """
    try:
        auth = get_auth_context()
        current_user = get_current_user()
        
        if not current_user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Update profile completion status
        response = auth.supabase.table('user_profiles').update({
            'profile_completed': True
        }).eq('user_id', current_user['id']).execute()
        
        if response.data:
            return jsonify({'success': True, 'message': 'Profile marked as completed'})
        else:
            return jsonify({'success': False, 'message': 'Failed to update profile'}), 500
            
    except Exception as e:
        logger.error(f"Error completing profile: {e}")
        return jsonify({'success': False, 'message': 'An error occurred'}), 500

@profile_bp.route('/api/profile')
@login_required
def get_profile_api():
    """
    Get user profile data as JSON.
    
    GET: Return user profile data
    """
    try:
        current_user = get_current_user()
        user_profile = get_user_profile()
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': current_user,
            'profile': user_profile
        })
        
    except Exception as e:
        logger.error(f"Error getting profile API: {e}")
        return jsonify({'error': 'An error occurred'}), 500

@profile_bp.route('/api/profile/update', methods=['POST'])
@login_required
def update_profile_api():
    """
    Update user profile via API.
    
    POST: Update profile data
    """
    try:
        auth = get_auth_context()
        current_user = get_current_user()
        
        if not current_user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Get JSON data
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['full_name', 'years_of_experience', 'experience_level', 'education_level']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
        
        # Update profile
        update_data = {
            'full_name': data['full_name'].strip(),
            'years_of_experience': int(data['years_of_experience']),
            'experience_level': data['experience_level'],
            'education_level': data['education_level'],
            'profile_completed': True
        }
        
        response = auth.supabase.table('user_profiles').update(update_data).eq('user_id', current_user['id']).execute()
        
        if response.data:
            return jsonify({
                'success': True, 
                'message': 'Profile updated successfully',
                'profile': response.data[0]
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to update profile'}), 500
            
    except Exception as e:
        logger.error(f"Error updating profile API: {e}")
        return jsonify({'success': False, 'message': 'An error occurred'}), 500 