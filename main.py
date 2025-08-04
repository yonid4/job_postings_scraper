#!/usr/bin/env python3
"""
AI Job Qualification Screening System - Main Entry Point

This is the main entry point for the AI Job Qualification Screening System.
It demonstrates the basic project structure and provides a foundation
for the complete qualification analysis system.
"""

import sys
import os
from pathlib import Path
from typing import Optional, List

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.config_manager import ConfigurationManager, UserProfile, AISettings
from src.utils.logger import setup_logging, JobAutomationLogger
from src.data.models import JobListing, QualificationResult, ScrapingSession, QualificationStatus, UserDecision

from src.ai.qualification_analyzer import QualificationAnalyzer, AnalysisRequest, AnalysisResponse
from src.utils.job_link_processor import JobLinkProcessor, JobLinkInfo


class JobQualificationSystem:
    """
    Main system class for the AI Job Qualification Screening System.
    
    This class orchestrates the various components of the system,
    including configuration management, logging, and the core qualification analysis logic.
    """
    
    VERSION = "2.0.0"
    
    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        Initialize the Job Qualification System.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config_path = config_path
        self.config_manager: Optional[ConfigurationManager] = None
        self.logger: Optional[JobAutomationLogger] = None
        self.qualification_analyzer: Optional[QualificationAnalyzer] = None
        self.job_link_processor: Optional[JobLinkProcessor] = None

        
        # Initialize system components
        self._initialize_system()
    
    def _initialize_system(self) -> None:
        """Initialize all system components."""
        try:
            # Set up logging first
            self._setup_logging()
            
            # Load configuration
            self._load_configuration()
            
            # Initialize AI components
            self._initialize_ai_components()
            

            
            # Log system startup
            if self.logger:
                self.logger.log_system_startup(self.VERSION)
            
            print(f"🚀 AI Job Qualification Screening System v{self.VERSION} initialized successfully!")
            
        except Exception as e:
            print(f"❌ Failed to initialize system: {e}")
            sys.exit(1)
    
    def _setup_logging(self) -> None:
        """Set up the logging system."""
        try:
            # Create logs directory if it doesn't exist
            logs_dir = Path("logs")
            logs_dir.mkdir(exist_ok=True)
            
            # Set up logging with file output
            setup_logging(
                name="job_qualification",
                log_level="INFO",
                log_file="logs/job_qualification.log"
            )
            
            self.logger = JobAutomationLogger(
                name="job_qualification",
                log_level="INFO",
                log_file="logs/job_qualification.log"
            )
            
            print("✅ Logging system initialized")
            
        except Exception as e:
            print(f"❌ Failed to set up logging: {e}")
            raise
    
    def _load_configuration(self) -> None:
        """Load system configuration."""
        try:
            self.config_manager = ConfigurationManager(self.config_path)
            
            # Test configuration loading
            user_profile = self.config_manager.get_user_profile()
            ai_settings = self.config_manager.get_ai_settings()
            scraping_settings = self.config_manager.get_scraping_settings()
            system_settings = self.config_manager.get_system_settings()
            
            if self.logger:
                self.logger.log_configuration_loaded(
                    self.config_manager.config_path
                )
            
            print("✅ Configuration loaded successfully")
            print(f"   - User experience: {user_profile.years_of_experience} years")
            print(f"   - Education: {'Yes' if user_profile.has_college_degree else 'No'}")
            print(f"   - AI model: {ai_settings.model}")
            print(f"   - Qualification threshold: {ai_settings.qualification_threshold}")
            
        except ConfigurationError as e:
            print(f"❌ Configuration error: {e}")
            raise
        except Exception as e:
            print(f"❌ Failed to load configuration: {e}")
            raise
    
    def _initialize_ai_components(self) -> None:
        """Initialize AI components."""
        try:
            ai_settings = self.config_manager.get_ai_settings()
            
            # Initialize qualification analyzer
            self.qualification_analyzer = QualificationAnalyzer(ai_settings)
            
            # Initialize job link processor
            scraping_settings = self.config_manager.get_scraping_settings()
            self.job_link_processor = JobLinkProcessor(
                timeout=scraping_settings.timeout
            )
            
            print("✅ AI components initialized")
            
        except Exception as e:
            print(f"❌ Failed to initialize AI components: {e}")
            raise
    

    
    def demonstrate_data_models(self) -> None:
        """Demonstrate the data models functionality."""
        print("\n📊 Demonstrating Data Models:")
        
        # Create a sample job listing
        job = JobListing(
            title="Software Engineer",
            company="Tech Corp",
            location="San Francisco, CA",
            job_url="https://example.com/job/123",
            job_site="linkedin",
            description="We are looking for a talented software engineer...",
            salary_min=80000,
            salary_max=120000
        )
        
        print(f"   ✅ Created job listing: {job.title} at {job.company}")
        
        # Create a sample qualification result
        qualification = QualificationResult(
            job_id=job.id,
            job_title=job.title,
            company=job.company,
            job_url=job.job_url,
            qualification_score=85,
            qualification_status=QualificationStatus.QUALIFIED,
            ai_reasoning="Strong match for experience and skills",
            required_experience="3-5 years",
            education_requirements="Bachelor's degree",
            key_skills_mentioned=["Python", "JavaScript", "React"],
            matching_strengths=["Python experience", "Web development"],
            potential_concerns=["Limited React experience"]
        )
        
        print(f"   ✅ Created qualification result for {qualification.job_title}")
        print(f"      Score: {qualification.qualification_score}, Status: {qualification.qualification_status.value}")
        
        # Create a sample scraping session
        session = ScrapingSession(
            job_site="linkedin",
            search_keywords=["python", "software engineer"],
            location="San Francisco, CA"
        )
        session.jobs_found = 25
        session.jobs_processed = 20
        session.jobs_qualified = 15
        session.finish()
        
        print(f"   ✅ Created scraping session: {session.jobs_found} jobs found, {session.jobs_qualified} qualified")
        
        # Test serialization/deserialization
        job_dict = job.to_dict()
        job_from_dict = JobListing.from_dict(job_dict)
        
        if job_from_dict.title == job.title:
            print("   ✅ Data model serialization/deserialization working correctly")
        else:
            print("   ❌ Data model serialization/deserialization failed")
    
    def demonstrate_configuration(self) -> None:
        """Demonstrate the configuration system."""
        print("\n⚙️  Demonstrating Configuration System:")
        
        if not self.config_manager:
            print("   ❌ Configuration manager not available")
            return
        
        # Show current configuration
        user_profile = self.config_manager.get_user_profile()
        ai_settings = self.config_manager.get_ai_settings()
        api_settings = self.config_manager.get_api_settings()
        
        print(f"   👤 User Profile:")
        print(f"      - Years of Experience: {user_profile.years_of_experience}")
        print(f"      - Education: {'College graduate' if user_profile.has_college_degree else 'No degree'}")
        print(f"      - Field of Study: {user_profile.field_of_study or 'N/A'}")
        print(f"      - Experience Level: {user_profile.experience_level}")
        print(f"      - Additional Skills: {', '.join(user_profile.additional_skills) if user_profile.additional_skills else 'None'}")
        
        print(f"   🤖 AI Settings:")
        print(f"      - Model: {ai_settings.model}")
        print(f"      - Qualification Threshold: {ai_settings.qualification_threshold}")
        print(f"      - Max Tokens: {ai_settings.max_tokens}")
        print(f"      - Temperature: {ai_settings.temperature}")
        
        print(f"   🔌 API Settings:")

        print(f"      - Email notifications: {'Yes' if api_settings.email_notifications else 'No'}")
    

    
    def demonstrate_ai_analysis(self) -> None:
        """Demonstrate AI qualification analysis functionality."""
        print("\n🤖 Demonstrating AI Qualification Analysis:")
        
        try:
            # Get user profile and AI settings
            user_profile = self.config_manager.get_user_profile()
            ai_settings = self.config_manager.get_ai_settings()
            
            # Create a sample job request
            sample_job = {
                'title': 'Senior Python Developer',
                'company': 'Tech Innovations Inc',
                'description': '''
                We are seeking a Senior Python Developer with 5+ years of experience.
                
                Requirements:
                - 5+ years of experience in Python development
                - Strong knowledge of Django, Flask, or FastAPI
                - Experience with AWS, Docker, and Kubernetes
                - Bachelor's degree in Computer Science or related field
                - Experience with microservices architecture
                - Knowledge of React or Vue.js is a plus
                
                Responsibilities:
                - Design and implement scalable backend services
                - Collaborate with frontend developers
                - Mentor junior developers
                - Participate in code reviews
                
                Location: San Francisco, CA (Hybrid)
                Salary: $120,000 - $180,000
                '''
            }
            
            # Create analysis request
            request = AnalysisRequest(
                job_title=sample_job['title'],
                company=sample_job['company'],
                job_description=sample_job['description'],
                user_profile=user_profile,
                ai_settings=ai_settings
            )
            
            # Perform AI analysis
            print(f"   📋 Analyzing: {sample_job['title']} at {sample_job['company']}")
            
            # Check if we have API key for AI analysis
            if not os.getenv("GEMINI_API_KEY"):
                print("   ⚠️  No Gemini API key provided - using custom rule-based analysis")
                # Use custom analysis logic instead
                from examples.custom_analyzer_example import CustomRuleBasedAnalyzer
                custom_analyzer = CustomRuleBasedAnalyzer(ai_settings)
                result = custom_analyzer.analyze_job_qualification(request)
            else:
                result = self.qualification_analyzer.analyze_job_qualification(request)
            
            # Display results
            print(f"   ✅ Analysis completed in {result.analysis_duration:.2f} seconds")
            print(f"   📊 Qualification Score: {result.qualification_score}/100")
            print(f"   🏷️  Status: {result.qualification_status.value}")
            print(f"   💭 AI Reasoning: {result.ai_reasoning[:100]}...")
            print(f"   🎯 Required Experience: {result.required_experience}")
            print(f"   🎓 Education Requirements: {result.education_requirements}")
            print(f"   🔧 Key Skills: {', '.join(result.key_skills_mentioned[:5])}")
            print(f"   ✅ Strengths: {', '.join(result.matching_strengths[:3])}")
            print(f"   ⚠️  Concerns: {', '.join(result.potential_concerns[:3])}")
            
            # Create qualification result
            qualification_result = self.qualification_analyzer.create_qualification_result(
                job_id="demo-job-001",
                job_title=sample_job['title'],
                company=sample_job['company'],
                job_url="https://example.com/job/demo",
                analysis_response=result
            )
            
            print(f"   📝 Created qualification result with ID: {qualification_result.id}")
            
        except Exception as e:
            print(f"   ❌ AI analysis demonstration failed: {e}")
            if self.logger:
                self.logger.log_error(f"AI analysis demonstration failed: {e}")
    
    def demonstrate_custom_analyzer(self) -> None:
        """Demonstrate custom analyzer functionality."""
        print("\n🔧 Demonstrating Custom Analyzer:")
        
        try:
            # Import custom analyzer
            from examples.custom_analyzer_example import CustomRuleBasedAnalyzer
            
            # Create AI settings (no API key needed for custom analyzer)
            ai_settings = AISettings(api_key="dummy", model="custom_rule_based")
            
            # Create custom analyzer
            custom_analyzer = CustomRuleBasedAnalyzer(ai_settings)
            
            # Get user profile
            user_profile = self.config_manager.get_user_profile()
            
            # Create sample job request
            request = AnalysisRequest(
                job_title="Frontend Developer",
                company="Web Solutions Co",
                job_description="""
                We are looking for a Frontend Developer with 2+ years of experience.
                
                Requirements:
                - 2+ years of experience in frontend development
                - Strong proficiency in JavaScript, React, and CSS
                - Experience with modern build tools (Webpack, Babel)
                - Knowledge of responsive design principles
                - Bachelor's degree preferred but not required
                
                Nice to have:
                - Experience with TypeScript
                - Knowledge of backend technologies (Node.js, Python)
                - Experience with testing frameworks (Jest, Cypress)
                
                Location: Remote (US-based)
                """,
                user_profile=user_profile,
                ai_settings=ai_settings
            )
            
            # Perform custom analysis
            print(f"   📋 Custom analysis: {request.job_title} at {request.company}")
            result = custom_analyzer.analyze_job_qualification(request)
            
            # Display results
            print(f"   ✅ Custom analysis completed in {result.analysis_duration:.2f} seconds")
            print(f"   📊 Score: {result.qualification_score}/100")
            print(f"   🏷️  Status: {result.qualification_status.value}")
            print(f"   💭 Reasoning: {result.ai_reasoning}")
            print(f"   🔧 Skills Found: {', '.join(result.key_skills_mentioned)}")
            print(f"   ✅ Strengths: {', '.join(result.matching_strengths)}")
            print(f"   ⚠️  Concerns: {', '.join(result.potential_concerns)}")
            
            print("   💡 This demonstrates how you can implement your own analysis logic!")
            
        except Exception as e:
            print(f"   ❌ Custom analyzer demonstration failed: {e}")
            if self.logger:
                self.logger.log_error(f"Custom analyzer demonstration failed: {e}")
    
    def demonstrate_job_link_processing(self) -> None:
        """Demonstrate job link processing."""
        print("\n🔗 Demonstrating Job Link Processing:")
        
        if not self.job_link_processor:
            print("   ❌ Job link processor not available")
            return
        
        try:
            # Sample job links for demonstration
            sample_links = [
                "https://linkedin.com/jobs/view/123456789",
                "https://indeed.com/viewjob?jk=abcdef123",
                "https://glassdoor.com/Job/san-francisco-software-engineer-jobs-SRCH_IL.0,13_IC1147401_KO14,31.htm"
            ]
            
            print("   📝 Job link processing foundation ready")
            print("   ✅ Features:")
            print("      - Support for LinkedIn, Indeed, Glassdoor, Monster")
            print("      - Automatic job site detection")
            print("      - Job information extraction")
            print("      - URL validation and cleaning")
            print("      - Error handling and logging")
            print("      - Rate limiting and respectful scraping")
            
            # Validate sample links
            validation_results = self.job_link_processor.validate_job_links(sample_links)
            print(f"   📊 Link validation results:")
            print(f"      - Valid: {len(validation_results['valid'])}")
            print(f"      - Invalid: {len(validation_results['invalid'])}")
            print(f"      - Unsupported: {len(validation_results['unsupported'])}")
            
            print("   ⏳ Job link processing (disabled for demo to avoid web scraping)")
            
        except Exception as e:
            print(f"   ❌ Job link processing demo error: {e}")
            if self.logger:
                self.logger.log_scraping_error("Job Link Processing", e, "demonstration")
    
    def run_demo(self) -> None:
        """Run a comprehensive demonstration of the system."""
        print("\n🎯 Running System Demonstration:")
        
        # Demonstrate core components
        self.demonstrate_data_models()
        self.demonstrate_configuration()

        
        # Demonstrate AI and processing capabilities
        self.demonstrate_ai_analysis()
        self.demonstrate_custom_analyzer()
        self.demonstrate_job_link_processing()
        
        print("\n✅ System demonstration completed!")
        print("💡 You can now:")
        print("   - Configure your user profile in config/settings.json")
        print("   - Add your Gemini API key to use AI analysis")
        print("   - Implement your own custom analysis logic")
        print("   - Process job links and analyze qualifications")

    
    def process_job_links(self, job_links: List[str]) -> List[QualificationResult]:
        """
        Process a list of job links and perform qualification analysis.
        
        Args:
            job_links: List of job URLs to process
            
        Returns:
            List of QualificationResult objects
        """
        if not self.job_link_processor or not self.qualification_analyzer:
            raise RuntimeError("System components not initialized")
        
        print(f"\n🔍 Processing {len(job_links)} job links...")
        
        # Process job links
        job_link_infos = self.job_link_processor.process_job_links(job_links)
        
        # Convert to job listings
        job_listings = self.job_link_processor.create_job_listings(job_link_infos)
        
        print(f"   ✅ Extracted {len(job_listings)} job listings")
        
        # Perform AI qualification analysis
        user_profile = self.config_manager.get_user_profile()
        
        # Convert job listings to dictionaries for batch analysis
        jobs_data = []
        for job in job_listings:
            jobs_data.append({
                'id': job.id,
                'title': job.title,
                'company': job.company,
                'job_url': job.job_url,
                'description': job.description
            })
        
        qualification_results = self.qualification_analyzer.batch_analyze_jobs(
            jobs_data, user_profile
        )
        
        print(f"   ✅ Analyzed {len(qualification_results)} jobs")
        

        
        return qualification_results
    
    def shutdown(self) -> None:
        """Shutdown the system gracefully."""
        if self.logger:
            self.logger.log_system_shutdown()
        
        print("\n👋 AI Job Qualification Screening System shutting down...")


def main() -> None:
    """Main entry point for the application."""
    print("=" * 60)
    print("AI Job Qualification Screening System")
    print("=" * 60)
    
    # Create and run the system
    system = JobQualificationSystem()
    
    try:
        # Run the demonstration
        system.run_demo()
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if system.logger:
            system.logger.logger.error(f"Unexpected error in main: {e}", exc_info=True)
    finally:
        # Always shutdown gracefully
        system.shutdown()


if __name__ == "__main__":
    main() 