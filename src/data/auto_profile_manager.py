"""
Automatic Profile Manager for Supabase Integration

Handles automatic user profile creation, management, and integration
with Supabase Auth system. Provides comprehensive logging and error handling.
"""

import os
import logging
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import uuid
from supabase import Client

logger = logging.getLogger(__name__)


class ExperienceLevel(Enum):
    """Experience level enumeration."""
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"


class EducationLevel(Enum):
    """Education level enumeration."""
    HIGH_SCHOOL = "high_school"
    ASSOCIATES = "associates"
    BACHELORS = "bachelors"
    MASTERS = "masters"
    PHD = "phd"
    OTHER = "other"


class WorkArrangement(Enum):
    """Work arrangement preference enumeration."""
    ANY = "any"
    REMOTE = "remote"
    HYBRID = "hybrid"
    ON_SITE = "on_site"


@dataclass
class ProfileCreationResult:
    """Result of profile creation operation."""
    success: bool
    message: str
    profile_id: Optional[str] = None
    user_id: Optional[str] = None
    error_details: Optional[str] = None
    created_at: Optional[datetime] = None


class AutoProfileManager:
    """
    Manages automatic user profile creation and management.
    
    This class handles:
    - Automatic profile creation when users register
    - Profile retrieval and updates
    - Comprehensive logging for debugging
    - Error handling with structured responses
    - Integration with Supabase Auth
    """
    
    def __init__(self, client: Client, testing_mode: bool = False):
        """
        Initialize the AutoProfileManager.
        
        Args:
            client: Supabase client instance
            testing_mode: Whether running in testing mode (affects logging and behavior)
        """
        self.client = client
        self.testing_mode = testing_mode
        self.table_name = "user_profiles"
        
        logger.info(f"AutoProfileManager initialized (testing_mode: {testing_mode})")
    
    def create_profile_automatically(self, user_id: str) -> ProfileCreationResult:
        """
        Create a user profile automatically with default values.
        
        This method is called when a new user registers through Supabase Auth.
        The database trigger should handle this automatically, but this method
        provides a backup and explicit creation capability.
        
        Args:
            user_id: The user ID from Supabase Auth
            
        Returns:
            ProfileCreationResult with operation details
        """
        logger.info(f"Creating automatic profile for user: {user_id}")
        
        try:
            # Check if profile already exists
            existing_profile = self.get_profile(user_id)
            if existing_profile:
                logger.warning(f"Profile already exists for user {user_id}")
                return ProfileCreationResult(
                    success=False,
                    message="Profile already exists for this user",
                    user_id=user_id,
                    error_details="Profile already exists"
                )
            
            # Prepare default profile data
            profile_data = {
                "user_id": user_id,
                "years_of_experience": 0,
                "experience_level": ExperienceLevel.ENTRY.value,
                "education_level": EducationLevel.BACHELORS.value,
                "work_arrangement_preference": WorkArrangement.ANY.value,
                "profile_completed": False,  # Use Python boolean, will be converted to PostgreSQL boolean
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Profile data prepared: {profile_data}")
            
            # Insert profile into database
            result = self.client.table(self.table_name).insert(profile_data).execute()
            
            if result.data:
                profile = result.data[0]
                logger.info(f"Profile created successfully: {profile['profile_id']}")
                
                return ProfileCreationResult(
                    success=True,
                    message="Profile created successfully",
                    profile_id=profile['profile_id'],
                    user_id=user_id,
                    created_at=datetime.fromisoformat(profile['created_at'])
                )
            else:
                logger.error(f"No data returned from profile creation for user {user_id}")
                return ProfileCreationResult(
                    success=False,
                    message="Failed to create profile - no data returned",
                    user_id=user_id,
                    error_details="No data returned from database"
                )
                
        except Exception as e:
            error_msg = f"Failed to create profile for user {user_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            return ProfileCreationResult(
                success=False,
                message="Failed to create profile",
                user_id=user_id,
                error_details=str(e)
            )
    
    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a user's profile.
        
        Args:
            user_id: The user ID
            
        Returns:
            Profile data dictionary or None if not found
        """
        try:
            logger.info(f"Retrieving profile for user: {user_id}")
            
            result = self.client.table(self.table_name).select('*').eq('user_id', user_id).execute()
            
            if result.data:
                profile = result.data[0]
                logger.info(f"Profile found for user {user_id}: {profile['profile_id']}")
                return profile
            else:
                logger.info(f"No profile found for user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving profile for user {user_id}: {str(e)}", exc_info=True)
            return None
    
    def update_profile(self, user_id: str, updates: Dict[str, Any]) -> ProfileCreationResult:
        """
        Update a user's profile.
        
        Args:
            user_id: The user ID
            updates: Dictionary of fields to update
            
        Returns:
            ProfileCreationResult with operation details
        """
        logger.info(f"Updating profile for user: {user_id}")
        logger.info(f"Updates: {updates}")
        
        try:
            # Add updated_at timestamp
            updates['updated_at'] = datetime.utcnow().isoformat()
            
            # Validate profile data
            validation_result = self._validate_profile_data(updates)
            if not validation_result[0]:
                return ProfileCreationResult(
                    success=False,
                    message=f"Invalid profile data: {validation_result[1]}",
                    user_id=user_id,
                    error_details=validation_result[1]
                )
            
            # Update profile
            result = self.client.table(self.table_name).update(updates).eq('user_id', user_id).execute()
            
            if result.data:
                profile = result.data[0]
                logger.info(f"Profile updated successfully for user {user_id}")
                
                # Check if profile is now complete
                is_complete = self._check_profile_completion(profile)
                if is_complete and not profile.get('profile_completed'):
                    # Update profile_completed flag
                    self.client.table(self.table_name).update({'profile_completed': True}).eq('user_id', user_id).execute()
                    logger.info(f"Profile marked as complete for user {user_id}")
                
                return ProfileCreationResult(
                    success=True,
                    message="Profile updated successfully",
                    profile_id=profile['profile_id'],
                    user_id=user_id
                )
            else:
                logger.error(f"No profile found to update for user {user_id}")
                return ProfileCreationResult(
                    success=False,
                    message="Profile not found",
                    user_id=user_id,
                    error_details="Profile not found"
                )
                
        except Exception as e:
            error_msg = f"Failed to update profile for user {user_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            return ProfileCreationResult(
                success=False,
                message="Failed to update profile",
                user_id=user_id,
                error_details=str(e)
            )
    
    def delete_profile(self, user_id: str) -> ProfileCreationResult:
        """
        Delete a user's profile.
        
        Args:
            user_id: The user ID
            
        Returns:
            ProfileCreationResult with operation details
        """
        logger.info(f"Deleting profile for user: {user_id}")
        
        try:
            result = self.client.table(self.table_name).delete().eq('user_id', user_id).execute()
            
            if result.data:
                logger.info(f"Profile deleted successfully for user {user_id}")
                return ProfileCreationResult(
                    success=True,
                    message="Profile deleted successfully",
                    user_id=user_id
                )
            else:
                logger.warning(f"No profile found to delete for user {user_id}")
                return ProfileCreationResult(
                    success=False,
                    message="Profile not found",
                    user_id=user_id,
                    error_details="Profile not found"
                )
                
        except Exception as e:
            error_msg = f"Failed to delete profile for user {user_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            return ProfileCreationResult(
                success=False,
                message="Failed to delete profile",
                user_id=user_id,
                error_details=str(e)
            )
    
    def get_profile_completion_status(self, user_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Get the completion status of a user's profile.
        
        Args:
            user_id: The user ID
            
        Returns:
            Tuple of (is_complete, completion_details)
        """
        try:
            profile = self.get_profile(user_id)
            if not profile:
                return False, {"error": "Profile not found"}
            
            is_complete = self._check_profile_completion(profile)
            completion_details = self._get_completion_details(profile)
            
            logger.info(f"Profile completion status for user {user_id}: {is_complete}")
            
            return is_complete, completion_details
            
        except Exception as e:
            logger.error(f"Error checking profile completion for user {user_id}: {str(e)}", exc_info=True)
            return False, {"error": str(e)}
    
    def _validate_profile_data(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate profile data before saving.
        
        Args:
            data: Profile data to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Validate experience level
            if 'experience_level' in data:
                valid_levels = [level.value for level in ExperienceLevel]
                if data['experience_level'] not in valid_levels:
                    return False, f"Invalid experience_level: {data['experience_level']}"
            
            # Validate education level
            if 'education_level' in data:
                valid_levels = [level.value for level in EducationLevel]
                if data['education_level'] not in valid_levels:
                    return False, f"Invalid education_level: {data['education_level']}"
            
            # Validate work arrangement
            if 'work_arrangement_preference' in data:
                valid_arrangements = [arrangement.value for arrangement in WorkArrangement]
                if data['work_arrangement_preference'] not in valid_arrangements:
                    return False, f"Invalid work_arrangement_preference: {data['work_arrangement_preference']}"
            
            # Validate years of experience
            if 'years_of_experience' in data:
                try:
                    years = int(data['years_of_experience'])
                    if years < 0:
                        return False, "years_of_experience must be non-negative"
                except (ValueError, TypeError):
                    return False, "years_of_experience must be an integer"
            
            # Validate salary ranges
            if 'salary_min' in data and 'salary_max' in data:
                if data['salary_min'] and data['salary_max']:
                    if data['salary_min'] > data['salary_max']:
                        return False, "salary_min cannot be greater than salary_max"
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def _check_profile_completion(self, profile: Dict[str, Any]) -> bool:
        """
        Check if a profile is complete based on required fields.
        
        Args:
            profile: Profile data dictionary
            
        Returns:
            True if profile is complete, False otherwise
        """
        required_fields = [
            'years_of_experience',
            'experience_level',
            'education_level'
        ]
        
        for field in required_fields:
            if not profile.get(field):
                return False
        
        return True
    
    def _get_completion_details(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get detailed information about profile completion status.
        
        Args:
            profile: Profile data dictionary
            
        Returns:
            Dictionary with completion details
        """
        required_fields = [
            'years_of_experience',
            'experience_level',
            'education_level'
        ]
        
        missing_fields = []
        for field in required_fields:
            if not profile.get(field):
                missing_fields.append(field)
        
        completion_percentage = ((len(required_fields) - len(missing_fields)) / len(required_fields)) * 100
        
        return {
            "is_complete": len(missing_fields) == 0,
            "completion_percentage": completion_percentage,
            "missing_fields": missing_fields,
            "total_required_fields": len(required_fields),
            "completed_fields": len(required_fields) - len(missing_fields)
        }
    
    def get_profile_options(self) -> Dict[str, List[str]]:
        """
        Get available options for profile fields.
        
        Returns:
            Dictionary of field options
        """
        return {
            "experience_levels": [level.value for level in ExperienceLevel],
            "education_levels": [level.value for level in EducationLevel],
            "work_arrangements": [arrangement.value for arrangement in WorkArrangement]
        }
    
    def log_profile_operation(self, operation: str, user_id: str, details: Dict[str, Any]):
        """
        Log profile operations for debugging and monitoring.
        
        Args:
            operation: Operation type (create, update, delete, etc.)
            user_id: User ID
            details: Operation details
        """
        log_data = {
            "operation": operation,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "testing_mode": self.testing_mode,
            **details
        }
        
        logger.info(f"Profile operation: {operation} for user {user_id} - {details}")
        
        if self.testing_mode:
            logger.debug(f"Detailed operation data: {log_data}") 