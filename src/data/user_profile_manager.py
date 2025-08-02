"""
User Profile Manager for Supabase Database

Handles user profile operations including creation, retrieval, updates,
and profile completion status for job matching and analysis.
"""

import os
import logging
from typing import Optional, Dict, Any, List, Tuple
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
class UserProfile:
    """User profile data model."""
    profile_id: str
    user_id: str
    years_of_experience: Optional[int] = None
    experience_level: Optional[ExperienceLevel] = None
    education_level: Optional[EducationLevel] = None
    field_of_study: Optional[str] = None
    skills_technologies: Optional[List[str]] = None
    work_arrangement_preference: WorkArrangement = WorkArrangement.ANY
    preferred_locations: Optional[List[str]] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: str = "USD"
    profile_completed: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserProfileManager:
    """Manages user profile database operations."""
    
    def __init__(self, client: Client):
        self.client = client
        self.table_name = "user_profiles"
    
    def create_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Tuple[bool, str, Optional[UserProfile]]:
        """
        Create a new user profile.
        
        Args:
            user_id: User ID
            profile_data: Profile data dictionary
            
        Returns:
            Tuple of (success, message, profile_object)
        """
        try:
            # Validate required fields
            required_fields = ['experience_level', 'education_level']
            for field in required_fields:
                if field not in profile_data:
                    return False, f"Missing required field: {field}", None
            
            # Check if profile already exists
            existing = self.get_profile(user_id)
            if existing:
                return False, "Profile already exists for this user", None
            
            # Generate profile_id
            profile_data['profile_id'] = str(uuid.uuid4())
            profile_data['user_id'] = user_id
            
            # Convert enum values to strings
            if isinstance(profile_data['experience_level'], ExperienceLevel):
                profile_data['experience_level'] = profile_data['experience_level'].value
            
            if isinstance(profile_data['education_level'], EducationLevel):
                profile_data['education_level'] = profile_data['education_level'].value
            
            if isinstance(profile_data.get('work_arrangement_preference'), WorkArrangement):
                profile_data['work_arrangement_preference'] = profile_data['work_arrangement_preference'].value
            
            # Set default values
            if 'salary_currency' not in profile_data:
                profile_data['salary_currency'] = "USD"
            
            if 'profile_completed' not in profile_data:
                profile_data['profile_completed'] = self._check_profile_completion(profile_data)
            
            # Add timestamps
            profile_data['created_at'] = datetime.utcnow().isoformat()
            profile_data['updated_at'] = datetime.utcnow().isoformat()
            
            # Insert profile
            response = self.client.table(self.table_name).insert(profile_data).execute()
            
            if response.data:
                profile = UserProfile(**response.data[0])
                logger.info(f"User profile created successfully for user: {user_id}")
                return True, "Profile created successfully", profile
            else:
                return False, "Failed to create profile", None
                
        except Exception as e:
            logger.error(f"Error creating user profile: {e}")
            return False, f"Failed to create profile: {str(e)}", None
    
    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        Get user profile by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            UserProfile object or None
        """
        try:
            response = self.client.table(self.table_name).select("*").eq("user_id", user_id).execute()
            
            if response.data:
                profile_data = response.data[0]
                
                # Convert string values to enums (only if not NULL)
                if profile_data.get('experience_level'):
                    profile_data['experience_level'] = ExperienceLevel(profile_data['experience_level'])
                else:
                    profile_data['experience_level'] = None
                
                if profile_data.get('education_level'):
                    profile_data['education_level'] = EducationLevel(profile_data['education_level'])
                else:
                    profile_data['education_level'] = None
                
                if profile_data.get('work_arrangement_preference'):
                    profile_data['work_arrangement_preference'] = WorkArrangement(profile_data['work_arrangement_preference'])
                else:
                    profile_data['work_arrangement_preference'] = WorkArrangement.ANY
                
                # Convert datetime strings to datetime objects
                if profile_data.get('created_at'):
                    try:
                        # Handle different timestamp formats
                        created_at_str = profile_data['created_at']
                        if created_at_str.endswith('Z'):
                            created_at_str = created_at_str.replace('Z', '+00:00')
                        # Normalize microseconds to 6 digits
                        if '.' in created_at_str and '+' in created_at_str:
                            parts = created_at_str.split('.')
                            time_part = parts[0]
                            tz_part = parts[1].split('+')[1]
                            micro_part = parts[1].split('+')[0]
                            # Pad microseconds to 6 digits
                            micro_part = micro_part.ljust(6, '0')[:6]
                            created_at_str = f"{time_part}.{micro_part}+{tz_part}"
                        profile_data['created_at'] = datetime.fromisoformat(created_at_str)
                        logger.debug(f"Successfully parsed created_at: {profile_data['created_at']}")
                    except Exception as e:
                        logger.warning(f"Could not parse created_at: {e}")
                        profile_data['created_at'] = None
                
                if profile_data.get('updated_at'):
                    try:
                        # Handle different timestamp formats
                        updated_at_str = profile_data['updated_at']
                        if updated_at_str.endswith('Z'):
                            updated_at_str = updated_at_str.replace('Z', '+00:00')
                        # Normalize microseconds to 6 digits
                        if '.' in updated_at_str and '+' in updated_at_str:
                            parts = updated_at_str.split('.')
                            time_part = parts[0]
                            tz_part = parts[1].split('+')[1]
                            micro_part = parts[1].split('+')[0]
                            # Pad microseconds to 6 digits
                            micro_part = micro_part.ljust(6, '0')[:6]
                            updated_at_str = f"{time_part}.{micro_part}+{tz_part}"
                        profile_data['updated_at'] = datetime.fromisoformat(updated_at_str)
                        logger.debug(f"Successfully parsed updated_at: {profile_data['updated_at']}")
                    except Exception as e:
                        logger.warning(f"Could not parse updated_at: {e}")
                        profile_data['updated_at'] = None
                
                try:
                    return UserProfile(**profile_data)
                except Exception as e:
                    logger.error(f"Error creating UserProfile object: {e}")
                    logger.error(f"Profile data: {profile_data}")
                    return None
            return None
            
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None
    
    def update_profile(self, user_id: str, updates: Dict[str, Any]) -> Tuple[bool, str, Optional[UserProfile]]:
        """
        Update user profile.
        
        Args:
            user_id: User ID
            updates: Dictionary of fields to update
            
        Returns:
            Tuple of (success, message, updated_profile)
        """
        try:
            # Convert enum values to strings
            if 'experience_level' in updates and isinstance(updates['experience_level'], ExperienceLevel):
                updates['experience_level'] = updates['experience_level'].value
            
            if 'education_level' in updates and isinstance(updates['education_level'], EducationLevel):
                updates['education_level'] = updates['education_level'].value
            
            if 'work_arrangement_preference' in updates and isinstance(updates['work_arrangement_preference'], WorkArrangement):
                updates['work_arrangement_preference'] = updates['work_arrangement_preference'].value
            
            # Check profile completion
            if 'profile_completed' not in updates:
                # Get current profile to check completion
                current_profile = self.get_profile(user_id)
                if current_profile:
                    # Merge current data with updates to check completion
                    current_data = {k: v for k, v in current_profile.__dict__.items() if k != 'profile_id' and k != 'user_id' and k != 'created_at' and k != 'updated_at'}
                    current_data.update(updates)
                    updates['profile_completed'] = self._check_profile_completion(current_data)
            
            # Add updated_at timestamp
            updates['updated_at'] = datetime.utcnow().isoformat()
            
            response = self.client.table(self.table_name).update(updates).eq("user_id", user_id).execute()
            
            if response.data:
                profile = UserProfile(**response.data[0])
                logger.info(f"User profile updated successfully for user: {user_id}")
                return True, "Profile updated successfully", profile
            else:
                return False, "Profile not found", None
                
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return False, f"Failed to update profile: {str(e)}", None
    
    def get_complete_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get complete user data including profile information.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with user and profile data or None
        """
        try:
            # Get user data
            user_response = self.client.table("users").select("*").eq("user_id", user_id).execute()
            if not user_response.data:
                return None
            
            user_data = user_response.data[0]
            
            # Get profile data
            profile = self.get_profile(user_id)
            
            # Combine user and profile data
            complete_data = {
                'user': user_data,
                'profile': profile.__dict__ if profile else None
            }
            
            return complete_data
            
        except Exception as e:
            logger.error(f"Error getting complete user data: {e}")
            return None
    
    def is_profile_complete(self, user_id: str) -> bool:
        """
        Check if user profile has all required fields.
        
        Args:
            user_id: User ID
            
        Returns:
            True if profile is complete, False otherwise
        """
        try:
            profile = self.get_profile(user_id)
            if not profile:
                return False
            
            return profile.profile_completed
            
        except Exception as e:
            logger.error(f"Error checking profile completion: {e}")
            return False
    
    def get_analysis_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get profile data needed for job analysis.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with analysis data or None
        """
        try:
            profile = self.get_profile(user_id)
            if not profile:
                return None
            
            return {
                'experience_level': profile.experience_level.value if profile.experience_level else None,
                'skills_technologies': profile.skills_technologies or [],
                'work_arrangement_preference': profile.work_arrangement_preference.value if profile.work_arrangement_preference else None,
                'preferred_locations': profile.preferred_locations or [],
                'salary_min': profile.salary_min,
                'salary_max': profile.salary_max,
                'years_of_experience': profile.years_of_experience,
                'education_level': profile.education_level.value if profile.education_level else None,
                'field_of_study': profile.field_of_study
            }
            
        except Exception as e:
            logger.error(f"Error getting analysis data: {e}")
            return None
    
    def delete_profile(self, user_id: str) -> Tuple[bool, str]:
        """
        Delete user profile.
        
        Args:
            user_id: User ID
            
        Returns:
            Tuple of (success, message)
        """
        try:
            response = self.client.table(self.table_name).delete().eq("user_id", user_id).execute()
            
            if response.data:
                logger.info(f"User profile deleted successfully for user: {user_id}")
                return True, "Profile deleted successfully"
            else:
                return False, "Profile not found"
                
        except Exception as e:
            logger.error(f"Error deleting user profile: {e}")
            return False, f"Failed to delete profile: {str(e)}"
    
    def _check_profile_completion(self, profile_data: Dict[str, Any]) -> bool:
        """
        Check if profile has all required fields for completion.
        
        Args:
            profile_data: Profile data dictionary
            
        Returns:
            True if profile is complete, False otherwise
        """
        required_fields = [
            'years_of_experience',
            'experience_level',
            'education_level',
            'skills_technologies',
            'work_arrangement_preference'
        ]
        
        for field in required_fields:
            if field not in profile_data or profile_data[field] is None:
                return False
            
            # Check if skills_technologies is not empty
            if field == 'skills_technologies' and (not profile_data[field] or len(profile_data[field]) == 0):
                return False
        
        return True
    
    def validate_profile_data(self, profile_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate profile data before saving.
        
        Args:
            profile_data: Profile data dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Validate experience level
            if 'experience_level' in profile_data:
                try:
                    ExperienceLevel(profile_data['experience_level'])
                except ValueError:
                    return False, "Invalid experience level"
            
            # Validate education level
            if 'education_level' in profile_data:
                try:
                    EducationLevel(profile_data['education_level'])
                except ValueError:
                    return False, "Invalid education level"
            
            # Validate work arrangement
            if 'work_arrangement_preference' in profile_data:
                try:
                    WorkArrangement(profile_data['work_arrangement_preference'])
                except ValueError:
                    return False, "Invalid work arrangement preference"
            
            # Validate salary range
            if 'salary_min' in profile_data and 'salary_max' in profile_data:
                if profile_data['salary_min'] and profile_data['salary_max']:
                    if profile_data['salary_min'] > profile_data['salary_max']:
                        return False, "Minimum salary cannot be greater than maximum salary"
            
            # Validate years of experience
            if 'years_of_experience' in profile_data:
                if profile_data['years_of_experience'] < 0:
                    return False, "Years of experience cannot be negative"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating profile data: {e}")
            return False, f"Validation error: {str(e)}" 