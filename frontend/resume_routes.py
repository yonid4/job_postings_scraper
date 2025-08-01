#!/usr/bin/env python3
"""
Resume management routes for Flask application with Supabase integration.

This module provides endpoints for:
- Resume upload and storage
- Resume status checking
- Resume processing management
"""

import os
import tempfile
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import logging
from pathlib import Path

from src.data.resume_manager import ResumeManager
from src.auth.auth_context import login_required, get_user_id
from src.utils.logger import JobAutomationLogger

logger = JobAutomationLogger()

# Create blueprint
resume_bp = Blueprint('resume', __name__, url_prefix='/resume')


def get_resume_manager():
    """Get the resume manager instance from the app context."""
    try:
        logger.info("=== get_resume_manager called ===")
        logger.info(f"Current app: {current_app}")
        logger.info(f"Current app config keys: {list(current_app.config.keys())}")
        resume_manager = current_app.config.get('resume_manager')
        logger.info(f"Resume manager from config: {resume_manager}")
        return resume_manager
    except Exception as e:
        logger.error(f"Error in get_resume_manager: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None


@resume_bp.route('/upload', methods=['POST'])
@login_required
def upload_resume():
    """
    Upload a resume file to Supabase Storage.
    
    Expected form data:
    - resume: Resume file (PDF or DOCX)
    
    Returns:
        JSON response with upload result
    """
    try:
        logger.info("=== Resume upload route called ===")
        logger.info(f"Request files: {list(request.files.keys())}")
        logger.info(f"Request content type: {request.content_type}")
        
        user_id = get_user_id()
        logger.info(f"User ID: {user_id}")
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        # Check if file was uploaded
        if 'resume' not in request.files:
            logger.error(f"No 'resume' field in request.files. Available fields: {list(request.files.keys())}")
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file: FileStorage = request.files['resume']
        logger.info(f"File received: {file.filename}")
        
        # Check if file was selected
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Validate file type
        filename = secure_filename(file.filename)
        if not filename:
            return jsonify({
                'success': False,
                'error': 'Invalid filename'
            }), 400
        
        logger.info(f"Processing file: {filename}")
        
        # Get resume manager
        resume_manager = get_resume_manager()
        logger.info(f"Resume manager: {resume_manager}")
        if not resume_manager:
            return jsonify({
                'success': False,
                'error': 'Resume manager not available'
            }), 500
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name
            logger.info(f"File saved to temporary location: {temp_file_path}")
        
        try:
            # Upload to Supabase Storage via ResumeManager
            logger.info(f"Calling resume_manager.upload_resume({user_id}, {temp_file_path}, {filename})")
            result = resume_manager.upload_resume(user_id, temp_file_path, filename)
            logger.info(f"Resume upload result: {result}")
            
            if result['success']:
                logger.info(f"Resume uploaded successfully for user {user_id}: {filename}")
                return jsonify(result), 200
            else:
                logger.error(f"Resume upload failed for user {user_id}: {result.get('error', 'Unknown error')}")
                return jsonify(result), 400
                
        finally:
            # Clean up temporary file (ResumeManager should handle this, but just in case)
            try:
                os.unlink(temp_file_path)
                logger.info(f"Temporary file cleaned up: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Could not clean up temporary file {temp_file_path}: {e}")
        
    except Exception as e:
        logger.error(f"Error in resume upload endpoint: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'Upload failed: {str(e)}'
        }), 500


@resume_bp.route('/status', methods=['GET'])
@login_required
def get_resume_status():
    """
    Get the current resume status for the authenticated user.
    
    Returns:
        JSON response with resume status information
    """
    try:
        user_id = get_user_id()
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        # Get resume manager
        resume_manager = get_resume_manager()
        if not resume_manager:
            return jsonify({
                'success': False,
                'error': 'Resume manager not available'
            }), 500
        
        # Get resume status
        status = resume_manager.get_resume_status(user_id)
        
        return jsonify({
            'success': True,
            'status': status
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting resume status for user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get resume status: {str(e)}'
        }), 500


@resume_bp.route('/process', methods=['POST'])
@login_required
def process_resume():
    """
    Trigger resume processing for the authenticated user.
    
    This endpoint forces processing of the user's resume if it hasn't been processed yet.
    
    Returns:
        JSON response with processing result
    """
    try:
        user_id = get_user_id()
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        # Get resume manager
        resume_manager = get_resume_manager()
        if not resume_manager:
            return jsonify({
                'success': False,
                'error': 'Resume manager not available'
            }), 500
        
        # Process resume
        processed_data = resume_manager.ensure_resume_processed(user_id)
        
        if processed_data:
            logger.info(f"Resume processing completed for user {user_id}")
            return jsonify({
                'success': True,
                'message': 'Resume processed successfully',
                'processed': True,
                'data_available': True
            }), 200
        else:
            logger.warning(f"Resume processing failed for user {user_id}")
            return jsonify({
                'success': False,
                'error': 'Resume processing failed or no resume found'
            }), 400
        
    except Exception as e:
        logger.error(f"Error processing resume for user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Processing failed: {str(e)}'
        }), 500


@resume_bp.route('/delete', methods=['DELETE'])
@login_required
def delete_resume():
    """
    Delete the user's current resume.
    
    Returns:
        JSON response with deletion result
    """
    try:
        user_id = get_user_id()
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        # Get resume manager
        resume_manager = get_resume_manager()
        if not resume_manager:
            return jsonify({
                'success': False,
                'error': 'Resume manager not available'
            }), 500
        
        # Get current resume
        current_resume = resume_manager.get_latest_user_resume(user_id)
        
        if not current_resume:
            return jsonify({
                'success': False,
                'error': 'No resume found to delete'
            }), 404
        
        # Deactivate the resume (this will also delete the file from storage)
        resume_manager._deactivate_user_resumes(user_id)
        
        logger.info(f"Resume deleted for user {user_id}")
        return jsonify({
            'success': True,
            'message': 'Resume deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting resume for user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Deletion failed: {str(e)}'
        }), 500


@resume_bp.route('/download', methods=['GET'])
@login_required
def download_resume():
    """
    Get a download URL for the user's current resume.
    
    Returns:
        JSON response with download URL
    """
    try:
        user_id = get_user_id()
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        # Get resume manager
        resume_manager = get_resume_manager()
        if not resume_manager:
            return jsonify({
                'success': False,
                'error': 'Resume manager not available'
            }), 500
        
        # Get current resume
        current_resume = resume_manager.get_latest_user_resume(user_id)
        
        if not current_resume:
            return jsonify({
                'success': False,
                'error': 'No resume found'
            }), 404
        
        # Return the public URL (file_path contains the public URL)
        return jsonify({
            'success': True,
            'download_url': current_resume.file_path,
            'filename': current_resume.filename,
            'file_size': current_resume.file_size,
            'file_type': current_resume.file_type
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting download URL for user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get download URL: {str(e)}'
        }), 500 