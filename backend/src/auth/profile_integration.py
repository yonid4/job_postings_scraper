"""
Profile Integration Module for Supabase Auth

Integrates automatic profile creation with the existing Supabase authentication system.
Provides seamless profile management during user registration and login flows.
"""

import os
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from supabase import Client

# Import the auto profile manager
from backend.src.data.auto_profile_manager import AutoProfileManager, ProfileCreationResult

logger = logging.getLogger(__name__)


class ProfileAuthIntegration:
    """
    Integrates automatic profile creation with Supabase authentication.
    
    This class provides:
    - Automatic profile creation during user registration
    - Profile verification during login
    - Profile management utilities
    - Comprehensive logging for debugging
    """
    
    def __init__(self, supabase_client: Client, testing_mode: bool = False):
        """
        Initialize the profile auth integration.
        
        Args:
            supabase_client: Supabase client instance
            testing_mode: Whether running in testing mode
        """
        self.supabase_client = supabase_client
        self.testing_mode = testing_mode
        self.profile_manager = AutoProfileManager(supabase_client, testing_mode)
        
        logger.info(f"ProfileAuthIntegration initialized (testing_mode: {testing_mode})")
    
    def handle_user_registration(self, user_id: str, user_data: Dict[str, Any]) -> ProfileCreationResult:
        """
        Handle automatic profile creation when a user registers.
        
        This method is called after successful user registration to ensure
        a profile is created automatically. The database trigger should handle
        this, but this provides a backup mechanism.
        
        Args:
            user_id: The user ID from Supabase Auth
            user_data: Additional user data from registration
            
        Returns:
            ProfileCreationResult with operation details
        """
        logger.info(f"Handling user registration for: {user_id}")
        logger.info(f"User data: {user_data}")
        
        try:
            # Check if profile already exists (trigger should have created it)
            existing_profile = self.profile_manager.get_profile(user_id)
            
            if existing_profile:
                logger.info(f"Profile already exists for user {user_id} (created by trigger)")
                return ProfileCreationResult(
                    success=True,
                    message="Profile already exists (created automatically)",
                    profile_id=existing_profile['profile_id'],
                    user_id=user_id
                )
            
            # Create profile manually if trigger didn't work
            logger.warning(f"Profile not found for user {user_id}, creating manually")
            result = self.profile_manager.create_profile_automatically(user_id)
            
            if result.success:
                logger.info(f"Profile created successfully for user {user_id}")
                self.profile_manager.log_profile_operation(
                    "registration_profile_creation",
                    user_id,
                    {
                        "method": "manual_creation",
                        "user_data": user_data,
                        "profile_id": result.profile_id
                    }
                )
            else:
                logger.error(f"Failed to create profile for user {user_id}: {result.error_details}")
                self.profile_manager.log_profile_operation(
                    "registration_profile_creation_failed",
                    user_id,
                    {
                        "error": result.error_details,
                        "user_data": user_data
                    }
                )
            
            return result
            
        except Exception as e:
            error_msg = f"Error handling user registration for {user_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            return ProfileCreationResult(
                success=False,
                message="Failed to handle user registration",
                user_id=user_id,
                error_details=str(e)
            )
    
    def verify_user_profile(self, user_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Verify that a user has a profile and get its status.
        
        Args:
            user_id: The user ID
            
        Returns:
            Tuple of (has_profile, profile_info)
        """
        logger.info(f"Verifying profile for user: {user_id}")
        
        try:
            profile = self.profile_manager.get_profile(user_id)
            
            if not profile:
                logger.warning(f"No profile found for user {user_id}")
                return False, {"error": "Profile not found"}
            
            # Get completion status
            is_complete, completion_details = self.profile_manager.get_profile_completion_status(user_id)
            
            profile_info = {
                "profile_id": profile['profile_id'],
                "is_complete": is_complete,
                "completion_details": completion_details,
                "created_at": profile.get('created_at'),
                "updated_at": profile.get('updated_at'),
                "profile_data": profile
            }
            
            logger.info(f"Profile verified for user {user_id}: complete={is_complete}")
            
            return True, profile_info
            
        except Exception as e:
            error_msg = f"Error verifying profile for user {user_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            return False, {"error": str(e)}
    
    def get_user_profile_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get complete user profile data including auth and profile information.
        
        Args:
            user_id: The user ID
            
        Returns:
            Complete user data dictionary or None if not found
        """
        logger.info(f"Getting complete profile data for user: {user_id}")
        
        try:
            # Get auth user data
            auth_user = self.supabase_client.auth.admin.get_user_by_id(user_id)
            
            if not auth_user.user:
                logger.error(f"Auth user not found for user ID: {user_id}")
                return None
            
            # Get profile data
            profile = self.profile_manager.get_profile(user_id)
            
            # Combine auth and profile data
            user_data = {
                "user_id": user_id,
                "email": auth_user.user.email,
                "email_confirmed": auth_user.user.email_confirmed_at is not None,
                "created_at": auth_user.user.created_at,
                "updated_at": auth_user.user.updated_at,
                "profile": profile,
                "has_profile": profile is not None
            }
            
            if profile:
                is_complete, completion_details = self.profile_manager.get_profile_completion_status(user_id)
                user_data["profile_complete"] = is_complete
                user_data["completion_details"] = completion_details
            
            logger.info(f"Complete user data retrieved for user {user_id}")
            return user_data
            
        except Exception as e:
            error_msg = f"Error getting user profile data for {user_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return None
    
    def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> ProfileCreationResult:
        """
        Update a user's profile with validation and logging.
        
        Args:
            user_id: The user ID
            updates: Profile updates to apply
            
        Returns:
            ProfileCreationResult with operation details
        """
        logger.info(f"Updating profile for user: {user_id}")
        logger.info(f"Updates: {updates}")
        
        try:
            # Verify user exists
            auth_user = self.supabase_client.auth.admin.get_user_by_id(user_id)
            if not auth_user.user:
                return ProfileCreationResult(
                    success=False,
                    message="User not found",
                    user_id=user_id,
                    error_details="Auth user not found"
                )
            
            # Update profile
            result = self.profile_manager.update_profile(user_id, updates)
            
            if result.success:
                self.profile_manager.log_profile_operation(
                    "profile_update",
                    user_id,
                    {
                        "updates": updates,
                        "profile_id": result.profile_id
                    }
                )
            else:
                self.profile_manager.log_profile_operation(
                    "profile_update_failed",
                    user_id,
                    {
                        "updates": updates,
                        "error": result.error_details
                    }
                )
            
            return result
            
        except Exception as e:
            error_msg = f"Error updating profile for user {user_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            return ProfileCreationResult(
                success=False,
                message="Failed to update profile",
                user_id=user_id,
                error_details=str(e)
            )
    
    def create_profile_if_missing(self, user_id: str) -> ProfileCreationResult:
        """
        Create a profile for a user if one doesn't exist.
        
        This is useful for existing users who don't have profiles yet.
        
        Args:
            user_id: The user ID
            
        Returns:
            ProfileCreationResult with operation details
        """
        logger.info(f"Creating profile if missing for user: {user_id}")
        
        try:
            # Check if profile exists
            existing_profile = self.profile_manager.get_profile(user_id)
            
            if existing_profile:
                logger.info(f"Profile already exists for user {user_id}")
                return ProfileCreationResult(
                    success=True,
                    message="Profile already exists",
                    profile_id=existing_profile['profile_id'],
                    user_id=user_id
                )
            
            # Create profile
            result = self.profile_manager.create_profile_automatically(user_id)
            
            if result.success:
                self.profile_manager.log_profile_operation(
                    "missing_profile_creation",
                    user_id,
                    {
                        "profile_id": result.profile_id,
                        "created_at": result.created_at
                    }
                )
            else:
                self.profile_manager.log_profile_operation(
                    "missing_profile_creation_failed",
                    user_id,
                    {
                        "error": result.error_details
                    }
                )
            
            return result
            
        except Exception as e:
            error_msg = f"Error creating missing profile for user {user_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            return ProfileCreationResult(
                success=False,
                message="Failed to create missing profile",
                user_id=user_id,
                error_details=str(e)
            )
    
    def get_profile_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about user profiles for monitoring.
        
        Returns:
            Dictionary with profile statistics
        """
        logger.info("Getting profile statistics")
        
        try:
            # Get all profiles
            result = self.supabase_client.table('user_profiles').select('*').execute()
            
            if not result.data:
                return {
                    "total_profiles": 0,
                    "complete_profiles": 0,
                    "incomplete_profiles": 0,
                    "completion_rate": 0.0
                }
            
            profiles = result.data
            total_profiles = len(profiles)
            complete_profiles = sum(1 for p in profiles if p.get('profile_completed', False))
            incomplete_profiles = total_profiles - complete_profiles
            completion_rate = (complete_profiles / total_profiles) * 100 if total_profiles > 0 else 0
            
            stats = {
                "total_profiles": total_profiles,
                "complete_profiles": complete_profiles,
                "incomplete_profiles": incomplete_profiles,
                "completion_rate": round(completion_rate, 2)
            }
            
            logger.info(f"Profile statistics: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting profile statistics: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    def cleanup_orphaned_profiles(self) -> Dict[str, Any]:
        """
        Clean up profiles for users that no longer exist in auth.users.
        
        Returns:
            Dictionary with cleanup results
        """
        logger.info("Cleaning up orphaned profiles")
        
        try:
            # Get all profile user IDs
            profiles_result = self.supabase_client.table('user_profiles').select('user_id').execute()
            
            if not profiles_result.data:
                return {"orphaned_profiles": 0, "cleaned_profiles": 0}
            
            profile_user_ids = [p['user_id'] for p in profiles_result.data]
            cleaned_count = 0
            
            for user_id in profile_user_ids:
                try:
                    # Check if auth user exists
                    auth_user = self.supabase_client.auth.admin.get_user_by_id(user_id)
                    
                    if not auth_user.user:
                        # User doesn't exist, delete profile
                        self.profile_manager.delete_profile(user_id)
                        cleaned_count += 1
                        logger.info(f"Cleaned orphaned profile for user: {user_id}")
                        
                except Exception as e:
                    logger.warning(f"Error checking user {user_id}: {str(e)}")
                    # If we can't check the user, assume it's orphaned and clean it
                    try:
                        self.profile_manager.delete_profile(user_id)
                        cleaned_count += 1
                        logger.info(f"Cleaned potentially orphaned profile for user: {user_id}")
                    except Exception as cleanup_error:
                        logger.error(f"Error cleaning profile for user {user_id}: {str(cleanup_error)}")
            
            result = {
                "total_profiles_checked": len(profile_user_ids),
                "cleaned_profiles": cleaned_count
            }
            
            logger.info(f"Cleanup completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}", exc_info=True)
            return {"error": str(e)} 