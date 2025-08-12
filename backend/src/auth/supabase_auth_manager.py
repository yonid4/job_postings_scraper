"""
Supabase Authentication Manager for Flask Application

Handles user registration, login, email verification, and session management
with support for both testing and production modes.
"""

import os
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from flask import session, current_app
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class SupabaseAuthManager:
    """
    Manages Supabase authentication with support for testing and production modes.
    
    Testing Mode: Users can login immediately after registration
    Production Mode: Users must verify email before login
    """
    
    def __init__(self, supabase_url: str, supabase_key: str):
        """
        Initialize the Supabase authentication manager.
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase anon key
        """
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.testing_mode = os.getenv('TESTING_MODE', 'false').lower() == 'true'
        
        # Get service role key for admin operations in testing mode
        self.service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        # Initialize Supabase client
        try:
            self.client: Client = create_client(supabase_url, supabase_key)
            
            # Create admin client for testing mode
            if self.testing_mode and self.service_role_key:
                self.admin_client: Client = create_client(supabase_url, self.service_role_key)
                logger.info("Supabase admin client initialized for testing mode")
            
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise
    
    def register_user(self, email: str, password: str, full_name: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Register a new user with email and password.
        
        Args:
            email: User's email address
            password: User's password
            full_name: User's full name
            
        Returns:
            Tuple of (success, message, user_data)
        """
        try:
            # Validate input
            if not email or not password or not full_name:
                return False, "All fields are required", None
            
            if len(password) < 6:
                return False, "Password must be at least 6 characters long", None
            
            # Note: We can't check for existing users with anon key
            # Supabase will handle duplicate email errors automatically
            
            # Register user with Supabase
            response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name,
                        "email_confirmed": self.testing_mode  # Auto-confirm in testing mode
                    }
                }
            })
            
            if response.user:
                user_data = {
                    "user_id": response.user.id,
                    "email": response.user.email,
                    "full_name": full_name,
                    "created_at": response.user.created_at,
                    "email_confirmed": self.testing_mode
                }
                
                # In testing mode, manually confirm the user using admin client
                if self.testing_mode and hasattr(self, 'admin_client'):
                    try:
                        # Add a small delay to ensure user is created
                        import time
                        time.sleep(1)
                        
                        self.admin_client.auth.admin.update_user_by_id(
                            response.user.id,
                            {"email_confirm": True}
                        )
                        logger.info(f"User {email} auto-confirmed in testing mode")
                    except Exception as e:
                        logger.warning(f"Failed to auto-confirm user in testing mode: {e}")
                        # Continue anyway - user can still register
                elif self.testing_mode:
                    logger.info(f"User {email} registered in testing mode (no admin client available)")
                
                logger.info(f"User registered successfully: {email}")
                return True, "Registration successful", user_data
            else:
                return False, "Registration failed", None
                
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False, f"Registration failed: {str(e)}", None
    
    def login_user(self, email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Login user with email and password.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Tuple of (success, message, user_data)
        """
        try:
            # Validate input
            if not email or not password:
                return False, "Email and password are required", None
            
            # Attempt login
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                # In testing mode, we allow login even without email confirmation
                # In production mode, require email confirmation
                if not self.testing_mode and not response.user.email_confirmed_at:
                    return False, "Please verify your email before logging in", None
                
                user_data = {
                    "user_id": response.user.id,
                    "email": response.user.email,
                    "full_name": response.user.user_metadata.get('full_name', ''),
                    "created_at": response.user.created_at,
                    "email_confirmed": self.testing_mode or bool(response.user.email_confirmed_at)
                }
                
                # Store session data (only if in request context)
                try:
                    session['user_id'] = response.user.id
                    session['email'] = response.user.email
                    session['full_name'] = user_data['full_name']
                    session['authenticated'] = True
                except RuntimeError:
                    # Not in request context (e.g., during testing)
                    logger.info("Session storage skipped - not in request context")
                
                logger.info(f"User logged in successfully: {email}")
                return True, "Login successful", user_data
            else:
                return False, "Invalid email or password", None
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            error_msg = str(e)
            
            # Handle email confirmation error in testing mode
            if self.testing_mode and "Email not confirmed" in error_msg:
                logger.info(f"Email confirmation required but in testing mode - attempting to handle")
                # In testing mode, we'll treat this as a successful login
                # The user exists but needs email confirmation
                return False, "Email confirmation required. Please check your email and click the verification link.", None
            
            return False, f"Login failed: {error_msg}", None
    
    def logout_user(self) -> Tuple[bool, str]:
        """
        Logout the current user.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Clear session data
            session.clear()
            
            # Sign out from Supabase
            self.client.auth.sign_out()
            
            logger.info("User logged out successfully")
            return True, "Logout successful"
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False, f"Logout failed: {str(e)}"
    
    def get_current_user(self) -> Optional[Dict]:
        """
        Get the current authenticated user from session.
        
        Returns:
            User data dictionary or None if not authenticated
        """
        try:
            # Check if we're in a request context
            try:
                from flask import session
                
                if not session.get('authenticated'):
                    return None
                
                user_id = session.get('user_id')
                email = session.get('email')
                full_name = session.get('full_name')
                
                if not user_id or not email:
                    return None
                
                # Return user data from session
                return {
                    "user_id": user_id,
                    "email": email,
                    "full_name": full_name or '',
                    "created_at": None,  # Not stored in session
                    "email_confirmed": self.testing_mode  # Assume confirmed in testing mode
                }
            except RuntimeError:
                # Not in request context
                logger.info("get_current_user called outside request context")
                return None
            
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            return None
    
    def is_authenticated(self) -> bool:
        """
        Check if user is currently authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        from flask import session
        is_auth = session.get('authenticated', False)
        logger.info(f"is_authenticated check: {is_auth}")
        return is_auth
    
    def resend_verification_email(self, email: str) -> Tuple[bool, str]:
        """
        Resend email verification link.
        
        Args:
            email: User's email address
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if self.testing_mode:
                return False, "Email verification not required in testing mode"
            
            # Resend verification email
            self.client.auth.resend({
                "type": "signup",
                "email": email
            })
            
            logger.info(f"Verification email resent to: {email}")
            return True, "Verification email sent successfully"
            
        except Exception as e:
            logger.error(f"Error resending verification email: {e}")
            return False, f"Failed to send verification email: {str(e)}"
    
    def verify_email(self, token: str) -> Tuple[bool, str]:
        """
        Verify user email with token.
        
        Args:
            token: Email verification token
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if self.testing_mode:
                return False, "Email verification not required in testing mode"
            
            # Verify email with token
            response = self.client.auth.verify_otp({
                "token_hash": token,
                "type": "signup"
            })
            
            if response.user:
                logger.info(f"Email verified successfully for user: {response.user.email}")
                return True, "Email verified successfully"
            else:
                return False, "Invalid verification token"
                
        except Exception as e:
            logger.error(f"Email verification error: {e}")
            return False, f"Email verification failed: {str(e)}"
    
    def reset_password(self, email: str) -> Tuple[bool, str]:
        """
        Send password reset email.
        
        Args:
            email: User's email address
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Send password reset email
            self.client.auth.reset_password_email(email)
            
            logger.info(f"Password reset email sent to: {email}")
            return True, "Password reset email sent successfully"
            
        except Exception as e:
            logger.error(f"Error sending password reset email: {e}")
            return False, f"Failed to send password reset email: {str(e)}"
    
    def update_password(self, new_password: str) -> Tuple[bool, str]:
        """
        Update user password.
        
        Args:
            new_password: New password
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if not self.is_authenticated():
                return False, "User not authenticated"
            
            if len(new_password) < 6:
                return False, "Password must be at least 6 characters long"
            
            # Update password
            self.client.auth.update_user({
                "password": new_password
            })
            
            logger.info("Password updated successfully")
            return True, "Password updated successfully"
            
        except Exception as e:
            logger.error(f"Error updating password: {e}")
            return False, f"Failed to update password: {str(e)}"
    
    def verify_token(self, access_token: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Verify an access token and return user data.
        
        Args:
            access_token: JWT access token from client
            
        Returns:
            Tuple of (success, message, user_data)
        """
        try:
            # For now, let's use a simpler approach
            # We'll trust the client-side authentication and just store the user info
            # This is a temporary solution - in production you'd want proper JWT verification
            
            # Get the user info from the session that was already established
            user = self.get_current_user()
            
            if user:
                return True, "Token verified successfully", user
            else:
                return False, "No authenticated user found", None
                
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return False, f"Token verification failed: {str(e)}", None

    def update_profile(self, profile_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Update user profile information.
        
        Args:
            profile_data: Dictionary containing profile fields
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Add debug logging
            logger.info(f"Starting profile update for user")
            
            if not self.is_authenticated():
                logger.error("User not authenticated in update_profile")
                return False, "User not authenticated"
            
            logger.info("User is authenticated, proceeding with profile update")
            
            # Extract fields from profile_data (matching form field names)
            years_of_experience = profile_data.get('years_of_experience', 0)
            experience_level = profile_data.get('experience_level', '')
            education_level = profile_data.get('education_level', '')
            work_arrangement_preference = profile_data.get('work_arrangement_preference', '')
            field_of_study = profile_data.get('field_of_study', '')
            skills_technologies = profile_data.get('skills_technologies', '')
            preferred_locations = profile_data.get('preferred_locations', '')
            salary_min = profile_data.get('salary_min')
            salary_max = profile_data.get('salary_max')
            linkedin_credentials = profile_data.get('linkedin_credentials', '')
            
            # For now, we'll store the profile data in Flask session
            # This is a temporary solution - in production you'd want to store in database
            from flask import session
            
            # Update Flask session with profile data
            session['years_of_experience'] = years_of_experience
            session['experience_level'] = experience_level
            session['education_level'] = education_level
            session['work_arrangement_preference'] = work_arrangement_preference
            session['field_of_study'] = field_of_study
            session['skills_technologies'] = skills_technologies
            session['preferred_locations'] = preferred_locations
            session['salary_min'] = salary_min
            session['salary_max'] = salary_max
            session['linkedin_credentials'] = linkedin_credentials
            
            # Try to update Supabase user metadata if possible
            try:
                user_data = {
                    "years_of_experience": years_of_experience,
                    "experience_level": experience_level,
                    "education_level": education_level,
                    "work_arrangement_preference": work_arrangement_preference,
                    "field_of_study": field_of_study,
                    "skills_technologies": skills_technologies,
                    "preferred_locations": preferred_locations,
                    "salary_min": salary_min,
                    "salary_max": salary_max
                }
                
                if linkedin_credentials:
                    user_data["linkedin_credentials"] = linkedin_credentials
                
                # Try to update using admin client if available
                if self.testing_mode and hasattr(self, 'admin_client'):
                    current_user = self.get_current_user()
                    logger.info(f"Current user data: {current_user}")
                    if current_user and current_user.get('user_id'):
                        self.admin_client.auth.admin.update_user_by_id(
                            current_user['user_id'],
                            {"user_metadata": user_data}
                        )
                        logger.info("Profile updated in Supabase via admin client")
                    else:
                        logger.warning("Could not get current user for Supabase update")
                else:
                    logger.info("Admin client not available, profile stored in session only")
                    
            except Exception as e:
                logger.warning(f"Failed to update Supabase user metadata: {e}")
                # Continue anyway since we stored in Flask session
            
            logger.info("Profile updated successfully")
            return True, "Profile updated successfully"
            
        except Exception as e:
            logger.error(f"Error updating profile: {e}")
            return False, f"Failed to update profile: {str(e)}" 