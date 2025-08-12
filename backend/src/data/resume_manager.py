"""
Resume manager for database operations and lazy processing with Supabase Storage.

This module handles resume storage, retrieval, and the lazy processing
logic that only processes resumes when needed for job searches.
"""

import os
import json
import tempfile
import requests
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
from supabase import Client

from backend.src.data.models import Resume
from backend.src.data.resume_processor import ResumeProcessor
from backend.src.utils.logger import JobAutomationLogger

logger = JobAutomationLogger()


class ResumeManager:
    """
    Manages resume storage, retrieval, and lazy processing with Supabase Storage.
    
    This class provides functionality to:
    - Store and retrieve resume records from Supabase database
    - Handle lazy processing (only process when needed)
    - Manage file storage in Supabase Storage buckets
    - Track processing status and errors
    """
    
    def __init__(self, supabase_client: Client, bucket_name: str = "resumes", ai_client=None):
        """
        Initialize the resume manager with Supabase integration.
        
        Args:
            supabase_client: Supabase client instance
            bucket_name: Name of the Supabase Storage bucket for resumes
            ai_client: AI client for resume processing (optional)
        """
        self.supabase = supabase_client
        self.bucket_name = bucket_name
        self.processor = ResumeProcessor(ai_client)
        
        # Ensure bucket exists (this will be handled by Supabase)
        logger.info(f"Initialized ResumeManager with bucket: {bucket_name}")
    
    def upload_resume(self, user_id: str, file_path: str, filename: str) -> Dict[str, Any]:
        """
        Upload a resume file to Supabase Storage with lazy processing.
        
        Args:
            user_id: ID of the user uploading the resume
            file_path: Path to the uploaded file
            filename: Original filename
            
        Returns:
            Dictionary with upload result information
        """
        try:
            # Validate file
            if not self.processor.is_supported_file(filename):
                return {
                    'success': False,
                    'error': 'Unsupported file type. Please upload PDF or DOCX files.'
                }
            
            # Calculate file hash
            file_hash = self.processor.calculate_file_hash(file_path)
            
            # Check for duplicate
            existing_resume = self.get_resume_by_hash(user_id, file_hash)
            if existing_resume:
                return {
                    'success': True,
                    'message': 'This resume was already uploaded',
                    'is_processed': existing_resume.is_processed,
                    'resume_id': existing_resume.id
                }
            
            # Get file metadata
            metadata = self.processor.get_file_metadata(file_path)
            
            # Create storage path: {user_id}/{timestamp}_{filename}
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            storage_path = f"{user_id}/{timestamp}_{filename}"
            
            # Upload file to Supabase Storage
            try:
                with open(file_path, 'rb') as file:
                    response = self.supabase.storage.from_(self.bucket_name).upload(
                        path=storage_path,
                        file=file,
                        file_options={"content-type": self._get_content_type(filename)}
                    )
                
                # Get public URL for the uploaded file
                public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(storage_path)
                
                logger.info(f"File uploaded to Supabase Storage: {storage_path}")
                
            except Exception as e:
                error_str = str(e)
                logger.error(f"Error uploading file to Supabase Storage: {e}")
                
                # Check if this is an RLS policy error (expected in some environments)
                if "row-level security policy" in error_str.lower() or "unauthorized" in error_str.lower():
                    logger.warning("RLS policy blocked storage upload - this is expected in test environments")
                    # For now, we'll return an error but in production you'd want to:
                    # 1. Configure proper RLS policies
                    # 2. Use service role key for admin operations
                    # 3. Or implement a fallback storage solution
                    return {
                        'success': False,
                        'error': 'Storage access denied. Please contact your administrator to configure storage permissions.',
                        'details': 'This is likely due to Row Level Security (RLS) policies in Supabase Storage.'
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Storage upload failed: {str(e)}'
                    }
            
            # Deactivate old resumes for this user
            self._deactivate_user_resumes(user_id)
            
            # Create resume record
            resume = Resume(
                user_id=user_id,
                filename=filename,
                file_path=public_url,  # Store public URL
                file_hash=file_hash,
                file_size=metadata.get('file_size'),
                file_type=metadata.get('file_type', ''),
                is_processed=False
            )
            
            # Add storage_path to the resume object for internal tracking
            resume.storage_path = storage_path
            
            # Save to Supabase database
            self.save_resume(resume)
            
            # Clean up temporary file
            try:
                os.remove(file_path)
                logger.debug(f"Cleaned up temporary file: {file_path}")
            except Exception as e:
                logger.warning(f"Could not clean up temporary file {file_path}: {e}")
            
            logger.info(f"Resume uploaded successfully for user {user_id}: {filename}")
            
            return {
                'success': True,
                'message': 'Resume uploaded successfully! It will be processed when you search for jobs.',
                'filename': filename,
                'resume_id': resume.id,
                'is_processed': False
            }
            
        except Exception as e:
            logger.error(f"Error uploading resume for user {user_id}: {e}")
            return {
                'success': False,
                'error': f'Upload failed: {str(e)}'
            }
    
    def ensure_resume_processed(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Ensure user's resume is processed. Process if needed.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Processed resume data or None if processing failed
        """
        try:
            # Get user's latest active resume
            resume = self.get_latest_user_resume(user_id)
            
            if not resume:
                logger.warning(f"No resume found for user {user_id}")
                return None
            
            # Update last used timestamp
            resume.last_used_at = datetime.now()
            self.save_resume(resume)
            
            # If already processed, return cached data
            if resume.is_processed and resume.processed_data:
                logger.info(f"Using cached resume data for user {user_id}")
                return resume.processed_data
            
            # Process resume now
            logger.info(f"Processing resume for user {user_id}")
            
            try:
                # Download file from Supabase Storage for processing
                temp_file_path = self._download_file_for_processing(resume.storage_path)
                
                if not temp_file_path:
                    raise Exception("Failed to download file from storage")
                
                try:
                    # Process with AI
                    processed_data = self.processor.process_resume_with_ai(temp_file_path)
                    
                    # Update database
                    resume.processed_data = processed_data
                    resume.is_processed = True
                    resume.processed_at = datetime.now()
                    resume.processing_error = None
                    
                    self.save_resume(resume)
                    
                    logger.info(f"Resume processing completed for user {user_id}")
                    return processed_data
                    
                finally:
                    # Clean up temporary file
                    try:
                        os.remove(temp_file_path)
                        logger.debug(f"Cleaned up temporary processing file: {temp_file_path}")
                    except Exception as e:
                        logger.warning(f"Could not clean up temporary file {temp_file_path}: {e}")
                
            except Exception as e:
                error_msg = f"Resume processing failed: {str(e)}"
                logger.error(f"User {user_id}: {error_msg}")
                
                # Store error
                resume.processing_error = error_msg
                self.save_resume(resume)
                
                # Return None to fall back to basic profile
                return None
                
        except Exception as e:
            logger.error(f"Error ensuring resume processed for user {user_id}: {e}")
            return None
    
    def _download_file_for_processing(self, storage_path: str) -> Optional[str]:
        """
        Download a file from Supabase Storage for processing.
        
        Args:
            storage_path: Internal storage path of the file
            
        Returns:
            Path to temporary file or None if download failed
        """
        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=Path(storage_path).suffix)
            temp_file_path = temp_file.name
            temp_file.close()
            
            # Download file from Supabase Storage
            response = self.supabase.storage.from_(self.bucket_name).download(storage_path)
            
            # Write to temporary file
            with open(temp_file_path, 'wb') as f:
                f.write(response)
            
            logger.debug(f"Downloaded file from storage: {storage_path} -> {temp_file_path}")
            return temp_file_path
            
        except Exception as e:
            logger.error(f"Error downloading file from storage {storage_path}: {e}")
            return None
    
    def get_latest_user_resume(self, user_id: str) -> Optional[Resume]:
        """
        Get the latest active resume for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Latest resume or None if not found
        """
        try:
            response = self.supabase.table('user_resume').select('*').eq('user_id', user_id).eq('is_active', True).order('uploaded_at', desc=True).limit(1).execute()
            
            if response.data:
                return self._dict_to_resume(response.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest resume for user {user_id}: {e}")
            return None
    
    def get_resume_by_hash(self, user_id: str, file_hash: str) -> Optional[Resume]:
        """
        Get resume by file hash.
        
        Args:
            user_id: ID of the user
            file_hash: Hash of the file
            
        Returns:
            Resume or None if not found
        """
        try:
            response = self.supabase.table('user_resume').select('*').eq('user_id', user_id).eq('file_hash', file_hash).limit(1).execute()
            
            if response.data:
                return self._dict_to_resume(response.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error getting resume by hash for user {user_id}: {e}")
            return None
    
    def save_resume(self, resume: Resume):
        """
        Save or update a resume record in Supabase.
        
        Args:
            resume: Resume object to save
        """
        try:
            # Prepare data for Supabase
            resume_data = {
                'id': resume.id,
                'user_id': resume.user_id,
                'filename': resume.filename,
                'file_path': resume.file_path,
                'storage_path': getattr(resume, 'storage_path', None),  # Add storage_path if available
                'file_hash': resume.file_hash,
                'is_processed': resume.is_processed,
                'processed_data': resume.processed_data,
                'processing_error': resume.processing_error,
                'uploaded_at': resume.uploaded_at.isoformat(),
                'processed_at': resume.processed_at.isoformat() if resume.processed_at else None,
                'last_used_at': resume.last_used_at.isoformat() if resume.last_used_at else None,
                'file_size': resume.file_size,
                'file_type': resume.file_type,
                'is_active': resume.is_active
            }
            
            # Use upsert to insert or update
            response = self.supabase.table('user_resume').upsert(resume_data).execute()
            
            logger.debug(f"Resume saved: {resume.id}")
            
        except Exception as e:
            logger.error(f"Error saving resume {resume.id}: {e}")
            raise
    
    def _deactivate_user_resumes(self, user_id: str):
        """
        Deactivate all resumes for a user.
        
        Args:
            user_id: ID of the user
        """
        try:
            # Get all active resumes for the user
            response = self.supabase.table('user_resume').select('id, storage_path').eq('user_id', user_id).eq('is_active', True).execute()
            
            if response.data:
                # Deactivate in database
                self.supabase.table('user_resume').update({'is_active': False}).eq('user_id', user_id).execute()
                
                # Delete old files from storage
                for resume in response.data:
                    storage_path = resume.get('storage_path')
                    if storage_path:
                        try:
                            self.supabase.storage.from_(self.bucket_name).remove([storage_path])
                            logger.debug(f"Deleted old resume file from storage: {storage_path}")
                        except Exception as e:
                            logger.warning(f"Could not delete old file {storage_path}: {e}")
                
                logger.debug(f"Deactivated resumes for user {user_id}")
                
        except Exception as e:
            logger.error(f"Error deactivating resumes for user {user_id}: {e}")
    
    def _dict_to_resume(self, data: Dict[str, Any]) -> Resume:
        """
        Convert Supabase data dictionary to Resume object.
        
        Args:
            data: Dictionary from Supabase
            
        Returns:
            Resume object
        """
        try:
            # Parse datetime strings
            uploaded_at = datetime.fromisoformat(data['uploaded_at']) if data.get('uploaded_at') else datetime.now()
            processed_at = datetime.fromisoformat(data['processed_at']) if data.get('processed_at') else None
            last_used_at = datetime.fromisoformat(data['last_used_at']) if data.get('last_used_at') else None
            
            resume = Resume(
                id=data.get('id', ''),
                user_id=data.get('user_id', ''),
                filename=data.get('filename', ''),
                file_path=data.get('file_path', ''),
                file_hash=data.get('file_hash', ''),
                is_processed=data.get('is_processed', False),
                processed_data=data.get('processed_data'),
                processing_error=data.get('processing_error'),
                uploaded_at=uploaded_at,
                processed_at=processed_at,
                last_used_at=last_used_at,
                file_size=data.get('file_size'),
                file_type=data.get('file_type', ''),
                is_active=data.get('is_active', True)
            )
            
            # Add storage_path if available
            if 'storage_path' in data:
                resume.storage_path = data['storage_path']
            
            return resume
            
        except Exception as e:
            logger.error(f"Error converting dict to Resume object: {e}")
            raise
    
    def get_resume_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get the current resume status for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary with resume status information
        """
        try:
            resume = self.get_latest_user_resume(user_id)
            
            if not resume:
                return {
                    'has_resume': False,
                    'message': 'No resume uploaded'
                }
            
            return {
                'has_resume': True,
                'filename': resume.filename,
                'is_processed': resume.is_processed,
                'uploaded_at': resume.uploaded_at.isoformat(),
                'processed_at': resume.processed_at.isoformat() if resume.processed_at else None,
                'processing_error': resume.processing_error,
                'file_size': resume.file_size,
                'file_type': resume.file_type
            }
            
        except Exception as e:
            logger.error(f"Error getting resume status for user {user_id}: {e}")
            return {
                'has_resume': False,
                'error': str(e)
            }
    
    def cleanup_old_resumes(self, days_old: int = 30):
        """
        Clean up old resume files and records.
        
        Args:
            days_old: Number of days after which to clean up
        """
        try:
            cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_old)
            
            # Get old resumes
            response = self.supabase.table('user_resume').select('id, storage_path').lt('uploaded_at', cutoff_date.isoformat()).eq('is_active', False).execute()
            
            old_resumes = response.data
            
            for resume in old_resumes:
                # Delete file from storage if it exists
                storage_path = resume.get('storage_path')
                if storage_path:
                    try:
                        self.supabase.storage.from_(self.bucket_name).remove([storage_path])
                        logger.debug(f"Deleted old resume file: {storage_path}")
                    except Exception as e:
                        logger.warning(f"Could not delete old file {storage_path}: {e}")
                
                # Delete database record
                self.supabase.table('user_resume').delete().eq('id', resume['id']).execute()
            
            logger.info(f"Cleaned up {len(old_resumes)} old resumes")
            
        except Exception as e:
            logger.error(f"Error cleaning up old resumes: {e}")
    
    def _get_content_type(self, filename: str) -> str:
        """
        Get the content type for a file based on its extension.
        
        Args:
            filename: Name of the file
            
        Returns:
            Content type string
        """
        extension = Path(filename).suffix.lower()
        content_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword'
        }
        return content_types.get(extension, 'application/octet-stream')