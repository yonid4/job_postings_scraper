"""
Applicant Profile Configuration

This module manages applicant profile data for automated job applications,
including personal information, resume/cover letter paths, and application preferences.
"""

import os
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

@dataclass
class ApplicantProfile:
    """Applicant profile data for automated job applications."""
    
    # Personal Information
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    
    # Resume and Cover Letter
    resume_path: str = ""
    cover_letter_path: str = ""
    cover_letter_text: str = ""
    
    # Application Preferences
    auto_apply_enabled: bool = True
    max_applications_per_session: int = 5
    skip_complex_applications: bool = True
    require_manual_review: bool = False
    
    # Question Answering
    default_answers: Dict[str, str] = field(default_factory=dict)
    question_mappings: Dict[str, str] = field(default_factory=dict)
    
    # Experience and Skills
    years_of_experience: int = 0
    skills: List[str] = field(default_factory=list)
    education: str = ""
    
    @classmethod
    def from_env(cls) -> 'ApplicantProfile':
        """Load applicant profile from environment variables."""
        profile = cls()
        
        # Personal Information
        profile.first_name = os.getenv('APPLICANT_FIRST_NAME', '')
        profile.last_name = os.getenv('APPLICANT_LAST_NAME', '')
        profile.email = os.getenv('APPLICANT_EMAIL', '')
        profile.phone = os.getenv('APPLICANT_PHONE', '')
        profile.location = os.getenv('APPLICANT_LOCATION', '')
        
        # Resume and Cover Letter
        profile.resume_path = os.getenv('APPLICANT_RESUME_PATH', '')
        profile.cover_letter_path = os.getenv('APPLICANT_COVER_LETTER_PATH', '')
        profile.cover_letter_text = os.getenv('APPLICANT_COVER_LETTER_TEXT', '')
        
        # Application Preferences
        profile.auto_apply_enabled = os.getenv('AUTO_APPLY_ENABLED', 'true').lower() == 'true'
        profile.max_applications_per_session = int(os.getenv('MAX_APPLICATIONS_PER_SESSION', '5'))
        profile.skip_complex_applications = os.getenv('SKIP_COMPLEX_APPLICATIONS', 'true').lower() == 'true'
        profile.require_manual_review = os.getenv('REQUIRE_MANUAL_REVIEW', 'false').lower() == 'true'
        
        # Experience and Skills
        profile.years_of_experience = int(os.getenv('APPLICANT_YEARS_EXPERIENCE', '0'))
        profile.education = os.getenv('APPLICANT_EDUCATION', '')
        
        # Parse skills from comma-separated string
        skills_str = os.getenv('APPLICANT_SKILLS', '')
        if skills_str:
            profile.skills = [skill.strip() for skill in skills_str.split(',') if skill.strip()]
        
        # Load default answers from environment
        profile._load_default_answers_from_env()
        
        return profile
    
    def _load_default_answers_from_env(self) -> None:
        """Load default answers from environment variables."""
        # Common question mappings
        self.default_answers = {
            'willing_to_relocate': os.getenv('ANSWER_WILLING_TO_RELOCATE', 'Yes'),
            'work_authorization': os.getenv('ANSWER_WORK_AUTHORIZATION', 'Yes'),
            'remote_work': os.getenv('ANSWER_REMOTE_WORK', 'Yes'),
            'salary_expectations': os.getenv('ANSWER_SALARY_EXPECTATIONS', 'Negotiable'),
            'start_date': os.getenv('ANSWER_START_DATE', 'Immediately'),
            'notice_period': os.getenv('ANSWER_NOTICE_PERIOD', '2 weeks'),
        }
        
        # Question mappings for common variations
        self.question_mappings = {
            'relocate': 'willing_to_relocate',
            'authorization': 'work_authorization',
            'remote': 'remote_work',
            'salary': 'salary_expectations',
            'start': 'start_date',
            'notice': 'notice_period',
        }
    
    def validate(self) -> Dict[str, bool]:
        """Validate the applicant profile."""
        validation_results = {
            'personal_info': bool(self.first_name and self.last_name and self.email),
            'resume_path': bool(self.resume_path and os.path.exists(self.resume_path)),
            'cover_letter': bool(self.cover_letter_path and os.path.exists(self.cover_letter_path)) if self.cover_letter_path else True,
            'phone': bool(self.phone),
            'location': bool(self.location),
        }
        
        return validation_results
    
    def get_answer_for_question(self, question_text: str) -> Optional[str]:
        """Get an appropriate answer for a given question."""
        question_lower = question_text.lower()
        
        # Check direct mappings first
        for key, answer in self.default_answers.items():
            if key in question_lower:
                return answer
        
        # Check question mappings
        for pattern, answer_key in self.question_mappings.items():
            if pattern in question_lower and answer_key in self.default_answers:
                return self.default_answers[answer_key]
        
        # Check for common question patterns
        if 'experience' in question_lower and 'year' in question_lower:
            return str(self.years_of_experience)
        
        if 'skill' in question_lower and self.skills:
            return ', '.join(self.skills[:3])  # Return first 3 skills
        
        if 'education' in question_lower and self.education:
            return self.education
        
        return None
    
    def print_summary(self) -> None:
        """Print a summary of the applicant profile (without sensitive data)."""
        print("\n" + "="*60)
        print("APPLICANT PROFILE SUMMARY")
        print("="*60)
        
        # Personal Information
        print(f"👤 Name: {self.first_name} {self.last_name}")
        print(f"📧 Email: {self.email.split('@')[0]}@..." if '@' in self.email else f"📧 Email: {self.email}")
        print(f"📱 Phone: {'*' * (len(self.phone) - 4) + self.phone[-4:] if len(self.phone) > 4 else self.phone}")
        print(f"📍 Location: {self.location}")
        
        # Files
        print(f"📄 Resume: {'✅ Found' if self.resume_path and os.path.exists(self.resume_path) else '❌ Not found'}")
        print(f"📝 Cover Letter: {'✅ Found' if self.cover_letter_path and os.path.exists(self.cover_letter_path) else '❌ Not found'}")
        
        # Preferences
        print(f"🤖 Auto Apply: {'✅ Enabled' if self.auto_apply_enabled else '❌ Disabled'}")
        print(f"📊 Max Applications: {self.max_applications_per_session}")
        print(f"⏭️  Skip Complex: {'✅ Yes' if self.skip_complex_applications else '❌ No'}")
        print(f"👀 Manual Review: {'✅ Required' if self.require_manual_review else '❌ Not required'}")
        
        # Experience and Skills
        print(f"⏰ Years Experience: {self.years_of_experience}")
        print(f"🎯 Skills: {', '.join(self.skills[:5])}{'...' if len(self.skills) > 5 else ''}")
        
        print("="*60)

def load_applicant_profile() -> ApplicantProfile:
    """Load and validate applicant profile."""
    # Load .env file if available
    try:
        from dotenv import load_dotenv
        from pathlib import Path
        
        # Look for .env file in project root
        env_path = Path(__file__).parent.parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            logger.info(f"Loaded applicant profile from .env file: {env_path}")
        else:
            logger.info(f"No .env file found at {env_path}")
    except ImportError:
        logger.info("python-dotenv not available")
    except Exception as e:
        logger.warning(f"Error loading .env file: {e}")
    
    profile = ApplicantProfile.from_env()
    
    # Validate profile
    validation = profile.validate()
    
    print("\n🔧 Applicant Profile Validation:")
    for component, is_valid in validation.items():
        status = "✅" if is_valid else "❌"
        print(f"   {status} {component.replace('_', ' ').title()}")
    
    # Check critical components
    if not validation['personal_info']:
        logger.warning("Personal information incomplete - auto apply may fail")
    
    if not validation['resume_path']:
        logger.warning("Resume path not found - auto apply may fail")
    
    return profile 