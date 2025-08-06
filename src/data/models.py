"""
Data models for the AI Job Qualification Screening System.

This module defines the core data structures used throughout the application,
including job listings, qualification analysis results, and tracking data.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid


class QualificationStatus(Enum):
    """Enumeration of possible qualification statuses."""
    
    HIGHLY_QUALIFIED = "highly_qualified"
    QUALIFIED = "qualified"
    SOMEWHAT_QUALIFIED = "somewhat_qualified"
    NOT_QUALIFIED = "not_qualified"
    PENDING_REVIEW = "pending_review"
    MANUAL_OVERRIDE = "manual_override"


class UserDecision(Enum):
    """Enumeration of user decisions on AI recommendations."""
    
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING = "pending"
    NEEDS_REVIEW = "needs_review"


class JobType(Enum):
    """Enumeration of job types."""
    
    FULL_TIME = "full-time"
    PART_TIME = "part-time"
    CONTRACT = "contract"
    TEMPORARY = "temporary"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"


class ExperienceLevel(Enum):
    """Enumeration of experience levels."""
    
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"


class RemoteType(Enum):
    """Enumeration of remote work types."""
    
    ON_SITE = "on-site"
    REMOTE = "remote"
    HYBRID = "hybrid"


class ApplicationStatus(Enum):
    """Enumeration of application statuses."""
    
    NOT_APPLIED = "not_applied"
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    OFFERED = "offered"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    ACCEPTED = "accepted"


class ApplicationMethod(Enum):
    """Enumeration of application methods."""
    
    MANUAL = "manual"
    AUTOMATED = "automated"
    LINKEDIN_EASY_APPLY = "linkedin_easy_apply"
    INDEED_QUICK_APPLY = "indeed_quick_apply"
    EMAIL = "email"
    COMPANY_WEBSITE = "company_website"


@dataclass
class Resume:
    """
    Represents a user's uploaded resume with lazy processing support.
    
    This class tracks resume uploads and their processing status,
    allowing for efficient AI-powered resume analysis when needed.
    """
    
    # Core identification
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    filename: str = ""
    file_path: str = ""  # Public URL for file access
    storage_path: Optional[str] = None  # Internal storage path for management
    file_hash: str = ""
    
    # Processing status
    is_processed: bool = False
    processed_data: Optional[Dict[str, Any]] = None
    processing_error: Optional[str] = None
    
    # Timestamps
    uploaded_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    
    # File metadata
    file_size: Optional[int] = None
    file_type: str = ""  # pdf, docx
    is_active: bool = True
    
    def __post_init__(self) -> None:
        """Validate and set default values after initialization."""
        if not self.id:
            self.id = str(uuid.uuid4())
        
        if not self.uploaded_at:
            self.uploaded_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the resume to a dictionary for storage."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'filename': self.filename,
            'file_path': self.file_path,
            'storage_path': self.storage_path,
            'file_hash': self.file_hash,
            'is_processed': self.is_processed,
            'processed_data': self.processed_data,
            'processing_error': self.processing_error,
            'uploaded_at': self.uploaded_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Resume':
        """Create a resume from a dictionary."""
        # Convert datetime strings back to datetime objects
        uploaded_at = datetime.fromisoformat(data['uploaded_at']) if data.get('uploaded_at') else datetime.now()
        processed_at = datetime.fromisoformat(data['processed_at']) if data.get('processed_at') else None
        last_used_at = datetime.fromisoformat(data['last_used_at']) if data.get('last_used_at') else None
        
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            user_id=data.get('user_id', ''),
            filename=data.get('filename', ''),
            file_path=data.get('file_path', ''),
            storage_path=data.get('storage_path'),
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


@dataclass
class JobListing:
    """
    Represents a job listing from a job site.
    
    This class contains all the information about a job posting,
    including details about the position, company, and requirements.
    """
    
    # Core job information
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    company: str = ""
    location: str = ""
    linkedin_url: str = ""
    job_site: str = ""  # indeed, linkedin, glassdoor, etc.
    
    # Job details
    description: str = ""
    requirements: List[str] = field(default_factory=list)
    responsibilities: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)
    
    # Compensation and type
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: str = "USD"
    job_type: Optional[JobType] = None
    experience_level: Optional[ExperienceLevel] = None
    remote_type: Optional[RemoteType] = None
    
    # Application details
    application_url: Optional[str] = None
    application_deadline: Optional[datetime] = None
    application_requirements: List[str] = field(default_factory=list)
    
    # Metadata
    posted_date: Optional[datetime] = None
    scraped_date: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    # Internal tracking
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None
    notes: str = ""
    
    def __post_init__(self) -> None:
        """Validate and set default values after initialization."""
        if not self.id:
            self.id = str(uuid.uuid4())
        
        if not self.scraped_date:
            self.scraped_date = datetime.now()
        
        if not self.last_updated:
            self.last_updated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the job listing to a dictionary for storage."""
        return {
            'id': self.id,
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'linkedin_url': self.linkedin_url,
            'job_site': self.job_site,
            'description': self.description,
            'requirements': self.requirements,
            'responsibilities': self.responsibilities,
            'benefits': self.benefits,
            'salary_min': self.salary_min,
            'salary_max': self.salary_max,
            'salary_currency': self.salary_currency,
            'job_type': self.job_type.value if self.job_type else None,
            'experience_level': self.experience_level.value if self.experience_level else None,
            'remote_type': self.remote_type.value if self.remote_type else None,
            'application_url': self.application_url,
            'application_deadline': self.application_deadline.isoformat() if self.application_deadline else None,
            'application_requirements': self.application_requirements,
            'posted_date': self.posted_date.isoformat() if self.posted_date else None,
            'scraped_date': self.scraped_date.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'is_duplicate': self.is_duplicate,
            'duplicate_of': self.duplicate_of,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobListing':
        """Create a job listing from a dictionary."""
        # Convert enum values back to enum objects
        job_type = JobType(data['job_type']) if data.get('job_type') else None
        experience_level = ExperienceLevel(data['experience_level']) if data.get('experience_level') else None
        remote_type = RemoteType(data['remote_type']) if data.get('remote_type') else None
        
        # Convert datetime strings back to datetime objects
        application_deadline = datetime.fromisoformat(data['application_deadline']) if data.get('application_deadline') else None
        posted_date = datetime.fromisoformat(data['posted_date']) if data.get('posted_date') else None
        scraped_date = datetime.fromisoformat(data['scraped_date']) if data.get('scraped_date') else datetime.now()
        last_updated = datetime.fromisoformat(data['last_updated']) if data.get('last_updated') else datetime.now()
        
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            title=data.get('title', ''),
            company=data.get('company', ''),
            location=data.get('location', ''),
            linkedin_url=data.get('linkedin_url', ''),
            job_site=data.get('job_site', ''),
            description=data.get('description', ''),
            requirements=data.get('requirements', []),
            responsibilities=data.get('responsibilities', []),
            benefits=data.get('benefits', []),
            salary_min=data.get('salary_min'),
            salary_max=data.get('salary_max'),
            salary_currency=data.get('salary_currency', 'USD'),
            job_type=job_type,
            experience_level=experience_level,
            remote_type=remote_type,
            application_url=data.get('application_url'),
            application_deadline=application_deadline,
            application_requirements=data.get('application_requirements', []),
            posted_date=posted_date,
            scraped_date=scraped_date,
            last_updated=last_updated,
            is_duplicate=data.get('is_duplicate', False),
            duplicate_of=data.get('duplicate_of'),
            notes=data.get('notes', '')
        )


@dataclass
class QualificationResult:
    """
    Represents the result of AI qualification analysis for a job.
    
    This class contains the AI's assessment of whether a user qualifies
    for a specific job, including scoring and reasoning.
    """
    
    # Core identification
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str = ""
    job_title: str = ""
    company: str = ""
    linkedin_url: str = ""
    
    # AI Analysis results
    qualification_score: int = 0  # 0-100 score
    qualification_status: QualificationStatus = QualificationStatus.NOT_QUALIFIED
    ai_reasoning: str = ""
    
    # Detailed analysis
    required_experience: str = ""
    education_requirements: str = ""
    key_skills_mentioned: List[str] = field(default_factory=list)
    matching_strengths: List[str] = field(default_factory=list)
    potential_concerns: List[str] = field(default_factory=list)
    
    # User interaction
    user_decision: UserDecision = UserDecision.PENDING
    user_notes: str = ""
    manual_override_reason: str = ""
    
    # Metadata
    analysis_date: datetime = field(default_factory=datetime.now)
    ai_model_used: str = ""
    analysis_duration: Optional[float] = None  # seconds
    created_date: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self) -> None:
        """Validate and set default values after initialization."""
        if not self.id:
            self.id = str(uuid.uuid4())
        
        if not self.analysis_date:
            self.analysis_date = datetime.now()
        
        if not self.created_date:
            self.created_date = datetime.now()
        
        if not self.last_updated:
            self.last_updated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the qualification result to a dictionary for storage."""
        return {
            'id': self.id,
            'job_id': self.job_id,
            'job_title': self.job_title,
            'company': self.company,
            'linkedin_url': self.linkedin_url,
            'qualification_score': self.qualification_score,
            'qualification_status': self.qualification_status.value,
            'ai_reasoning': self.ai_reasoning,
            'required_experience': self.required_experience,
            'education_requirements': self.education_requirements,
            'key_skills_mentioned': self.key_skills_mentioned,
            'matching_strengths': self.matching_strengths,
            'potential_concerns': self.potential_concerns,
            'user_decision': self.user_decision.value,
            'user_notes': self.user_notes,
            'manual_override_reason': self.manual_override_reason,
            'analysis_date': self.analysis_date.isoformat(),
            'ai_model_used': self.ai_model_used,
            'analysis_duration': self.analysis_duration,
            'created_date': self.created_date.isoformat(),
            'last_updated': self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QualificationResult':
        """Create a qualification result from a dictionary."""
        # Convert enum values back to enum objects
        qualification_status = QualificationStatus(data['qualification_status']) if data.get('qualification_status') else QualificationStatus.NOT_QUALIFIED
        user_decision = UserDecision(data['user_decision']) if data.get('user_decision') else UserDecision.PENDING
        
        # Convert datetime strings back to datetime objects
        analysis_date = datetime.fromisoformat(data['analysis_date']) if data.get('analysis_date') else datetime.now()
        created_date = datetime.fromisoformat(data['created_date']) if data.get('created_date') else datetime.now()
        last_updated = datetime.fromisoformat(data['last_updated']) if data.get('last_updated') else datetime.now()
        
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            job_id=data.get('job_id', ''),
            job_title=data.get('job_title', ''),
            company=data.get('company', ''),
            linkedin_url=data.get('linkedin_url', ''),
            qualification_score=data.get('qualification_score', 0),
            qualification_status=qualification_status,
            ai_reasoning=data.get('ai_reasoning', ''),
            required_experience=data.get('required_experience', ''),
            education_requirements=data.get('education_requirements', ''),
            key_skills_mentioned=data.get('key_skills_mentioned', []),
            matching_strengths=data.get('matching_strengths', []),
            potential_concerns=data.get('potential_concerns', []),
            user_decision=user_decision,
            user_notes=data.get('user_notes', ''),
            manual_override_reason=data.get('manual_override_reason', ''),
            analysis_date=analysis_date,
            ai_model_used=data.get('ai_model_used', ''),
            analysis_duration=data.get('analysis_duration'),
            created_date=created_date,
            last_updated=last_updated
        )


@dataclass
class ScrapingSession:
    """
    Represents a scraping session for tracking performance and results.
    
    This class tracks the details of each scraping session,
    including performance metrics and results.
    """
    
    # Session information
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    job_site: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    # Results
    jobs_found: int = 0
    jobs_processed: int = 0
    jobs_qualified: int = 0
    jobs_skipped: int = 0
    errors_encountered: int = 0
    
    # Performance metrics
    total_duration: Optional[float] = None  # in seconds
    average_job_time: Optional[float] = None  # in seconds
    
    # Configuration used
    search_keywords: List[str] = field(default_factory=list)
    location: str = ""
    filters_applied: Dict[str, Any] = field(default_factory=dict)
    
    # Status
    completed: bool = False
    error_message: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate and set default values after initialization."""
        if not self.id:
            self.id = str(uuid.uuid4())
        
        if not self.start_time:
            self.start_time = datetime.now()
    
    def finish(self, end_time: Optional[datetime] = None) -> None:
        """Mark the session as completed and calculate metrics."""
        self.end_time = end_time or datetime.now()
        self.completed = True
        
        if self.start_time and self.end_time:
            self.total_duration = (self.end_time - self.start_time).total_seconds()
            
            if self.jobs_processed > 0:
                self.average_job_time = self.total_duration / self.jobs_processed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the scraping session to a dictionary for storage."""
        return {
            'id': self.id,
            'job_site': self.job_site,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'jobs_found': self.jobs_found,
            'jobs_processed': self.jobs_processed,
            'jobs_qualified': self.jobs_qualified,
            'jobs_skipped': self.jobs_skipped,
            'errors_encountered': self.errors_encountered,
            'total_duration': self.total_duration,
            'average_job_time': self.average_job_time,
            'search_keywords': self.search_keywords,
            'location': self.location,
            'filters_applied': self.filters_applied,
            'completed': self.completed,
            'error_message': self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScrapingSession':
        """Create a scraping session from a dictionary."""
        # Convert datetime strings back to datetime objects
        start_time = datetime.fromisoformat(data['start_time']) if data.get('start_time') else datetime.now()
        end_time = datetime.fromisoformat(data['end_time']) if data.get('end_time') else None
        
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            job_site=data.get('job_site', ''),
            start_time=start_time,
            end_time=end_time,
            jobs_found=data.get('jobs_found', 0),
            jobs_processed=data.get('jobs_processed', 0),
            jobs_qualified=data.get('jobs_qualified', 0),
            jobs_skipped=data.get('jobs_skipped', 0),
            errors_encountered=data.get('errors_encountered', 0),
            total_duration=data.get('total_duration'),
            average_job_time=data.get('average_job_time'),
            search_keywords=data.get('search_keywords', []),
            location=data.get('location', ''),
            filters_applied=data.get('filters_applied', {}),
            completed=data.get('completed', False),
            error_message=data.get('error_message')
        ) 


@dataclass
class JobSearch:
    """
    Represents a job search session with parameters and results.
    
    This class tracks search parameters and links to found jobs,
    allowing for search history and result management.
    """
    
    # Core identification
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    search_name: str = ""
    
    # Search parameters
    keywords: List[str] = field(default_factory=list)
    location: str = ""
    remote_preference: Optional[RemoteType] = None
    experience_level: Optional[ExperienceLevel] = None
    job_type: Optional[JobType] = None
    date_posted_filter: Optional[int] = None  # days
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    
    # Search metadata
    job_sites: List[str] = field(default_factory=list)  # linkedin, indeed, etc.
    search_date: datetime = field(default_factory=datetime.now)
    completed_date: Optional[datetime] = None
    
    # Results
    total_jobs_found: int = 0
    qualified_jobs_count: int = 0
    jobs_processed: int = 0
    
    # Status
    is_active: bool = True
    notes: str = ""
    
    def __post_init__(self) -> None:
        """Validate and set default values after initialization."""
        if not self.id:
            self.id = str(uuid.uuid4())
        
        if not self.search_date:
            self.search_date = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the job search to a dictionary for storage."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'search_name': self.search_name,
            'keywords': self.keywords,
            'location': self.location,
            'remote_preference': self.remote_preference.value if self.remote_preference else None,
            'experience_level': self.experience_level.value if self.experience_level else None,
            'job_type': self.job_type.value if self.job_type else None,
            'date_posted_filter': self.date_posted_filter,
            'salary_min': self.salary_min,
            'salary_max': self.salary_max,
            'job_sites': self.job_sites,
            'search_date': self.search_date.isoformat(),
            'completed_date': self.completed_date.isoformat() if self.completed_date else None,
            'total_jobs_found': self.total_jobs_found,
            'qualified_jobs_count': self.qualified_jobs_count,
            'jobs_processed': self.jobs_processed,
            'is_active': self.is_active,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobSearch':
        """Create a job search from a dictionary."""
        # Convert enum values back to enum objects
        remote_preference = RemoteType(data['remote_preference']) if data.get('remote_preference') else None
        experience_level = ExperienceLevel(data['experience_level']) if data.get('experience_level') else None
        job_type = JobType(data['job_type']) if data.get('job_type') else None
        
        # Convert datetime strings back to datetime objects
        search_date = datetime.fromisoformat(data['search_date']) if data.get('search_date') else datetime.now()
        completed_date = datetime.fromisoformat(data['completed_date']) if data.get('completed_date') else None
        
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            user_id=data.get('user_id', ''),
            search_name=data.get('search_name', ''),
            keywords=data.get('keywords', []),
            location=data.get('location', ''),
            remote_preference=remote_preference,
            experience_level=experience_level,
            job_type=job_type,
            date_posted_filter=data.get('date_posted_filter'),
            salary_min=data.get('salary_min'),
            salary_max=data.get('salary_max'),
            job_sites=data.get('job_sites', []),
            search_date=search_date,
            completed_date=completed_date,
            total_jobs_found=data.get('total_jobs_found', 0),
            qualified_jobs_count=data.get('qualified_jobs_count', 0),
            jobs_processed=data.get('jobs_processed', 0),
            is_active=data.get('is_active', True),
            notes=data.get('notes', '')
        )


@dataclass
class JobApplication:
    """
    Represents a job application with status tracking.
    
    This class tracks the user's applications to jobs, including
    both manual and automated applications.
    """
    
    # Core identification
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    job_id: str = ""
    
    # Application details
    applied_date: datetime = field(default_factory=datetime.now)
    application_method: ApplicationMethod = ApplicationMethod.MANUAL
    status: ApplicationStatus = ApplicationStatus.APPLIED
    
    # Application metadata
    application_url: Optional[str] = None
    cover_letter_used: bool = False
    resume_version: Optional[str] = None  # Link to resume used
    
    # Tracking
    follow_up_date: Optional[datetime] = None
    interview_date: Optional[datetime] = None
    response_received: bool = False
    response_date: Optional[datetime] = None
    
    # User notes
    notes: str = ""
    salary_offered: Optional[int] = None
    benefits_offered: List[str] = field(default_factory=list)
    
    # Timestamps
    created_date: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self) -> None:
        """Validate and set default values after initialization."""
        if not self.id:
            self.id = str(uuid.uuid4())
        
        if not self.applied_date:
            self.applied_date = datetime.now()
        
        if not self.created_date:
            self.created_date = datetime.now()
        
        if not self.last_updated:
            self.last_updated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the job application to a dictionary for storage."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'job_id': self.job_id,
            'applied_date': self.applied_date.isoformat(),
            'application_method': self.application_method.value,
            'status': self.status.value,
            'application_url': self.application_url,
            'cover_letter_used': self.cover_letter_used,
            'resume_version': self.resume_version,
            'follow_up_date': self.follow_up_date.isoformat() if self.follow_up_date else None,
            'interview_date': self.interview_date.isoformat() if self.interview_date else None,
            'response_received': self.response_received,
            'response_date': self.response_date.isoformat() if self.response_date else None,
            'notes': self.notes,
            'salary_offered': self.salary_offered,
            'benefits_offered': self.benefits_offered,
            'created_date': self.created_date.isoformat(),
            'last_updated': self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobApplication':
        """Create a job application from a dictionary."""
        # Convert enum values back to enum objects
        application_method = ApplicationMethod(data['application_method']) if data.get('application_method') else ApplicationMethod.MANUAL
        status = ApplicationStatus(data['status']) if data.get('status') else ApplicationStatus.APPLIED
        
        # Convert datetime strings back to datetime objects
        applied_date = datetime.fromisoformat(data['applied_date']) if data.get('applied_date') else datetime.now()
        follow_up_date = datetime.fromisoformat(data['follow_up_date']) if data.get('follow_up_date') else None
        interview_date = datetime.fromisoformat(data['interview_date']) if data.get('interview_date') else None
        response_date = datetime.fromisoformat(data['response_date']) if data.get('response_date') else None
        created_date = datetime.fromisoformat(data['created_date']) if data.get('created_date') else datetime.now()
        last_updated = datetime.fromisoformat(data['last_updated']) if data.get('last_updated') else datetime.now()
        
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            user_id=data.get('user_id', ''),
            job_id=data.get('job_id', ''),
            applied_date=applied_date,
            application_method=application_method,
            status=status,
            application_url=data.get('application_url'),
            cover_letter_used=data.get('cover_letter_used', False),
            resume_version=data.get('resume_version'),
            follow_up_date=follow_up_date,
            interview_date=interview_date,
            response_received=data.get('response_received', False),
            response_date=response_date,
            notes=data.get('notes', ''),
            salary_offered=data.get('salary_offered'),
            benefits_offered=data.get('benefits_offered', []),
            created_date=created_date,
            last_updated=last_updated
        )


@dataclass
class JobFavorite:
    """
    Represents a user's favorite/saved job.
    
    This class allows users to save jobs for later review
    without necessarily applying to them.
    """
    
    # Core identification
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    job_id: str = ""
    
    # Metadata
    favorited_date: datetime = field(default_factory=datetime.now)
    notes: str = ""
    priority: int = 1  # 1-5 scale, 5 being highest priority
    
    # Timestamps
    created_date: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self) -> None:
        """Validate and set default values after initialization."""
        if not self.id:
            self.id = str(uuid.uuid4())
        
        if not self.favorited_date:
            self.favorited_date = datetime.now()
        
        if not self.created_date:
            self.created_date = datetime.now()
        
        if not self.last_updated:
            self.last_updated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the job favorite to a dictionary for storage."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'job_id': self.job_id,
            'favorited_date': self.favorited_date.isoformat(),
            'notes': self.notes,
            'priority': self.priority,
            'created_date': self.created_date.isoformat(),
            'last_updated': self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobFavorite':
        """Create a job favorite from a dictionary."""
        # Convert datetime strings back to datetime objects
        favorited_date = datetime.fromisoformat(data['favorited_date']) if data.get('favorited_date') else datetime.now()
        created_date = datetime.fromisoformat(data['created_date']) if data.get('created_date') else datetime.now()
        last_updated = datetime.fromisoformat(data['last_updated']) if data.get('last_updated') else datetime.now()
        
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            user_id=data.get('user_id', ''),
            job_id=data.get('job_id', ''),
            favorited_date=favorited_date,
            notes=data.get('notes', ''),
            priority=data.get('priority', 1),
            created_date=created_date,
            last_updated=last_updated
        ) 