"""
Tests for the AI Job Qualification Screening System.

This module contains tests for the core functionality of the qualification
screening system, including AI analysis, job link processing, and data models.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from pathlib import Path

from src.config.config_manager import ConfigurationManager, UserProfile, AISettings
from src.data.models import JobListing, QualificationResult, QualificationStatus, UserDecision
from src.ai.qualification_analyzer import QualificationAnalyzer, AnalysisRequest, AnalysisResponse
from src.utils.job_link_processor import JobLinkProcessor, JobLinkInfo


class TestConfigurationManager:
    """Test configuration management functionality."""
    
    def test_user_profile_loading(self):
        """Test that user profile loads correctly from configuration."""
        config_manager = ConfigurationManager()
        user_profile = config_manager.get_user_profile()
        
        assert isinstance(user_profile, UserProfile)
        assert isinstance(user_profile.years_of_experience, int)
        assert isinstance(user_profile.has_college_degree, bool)
        assert isinstance(user_profile.additional_skills, list)
    
    def test_ai_settings_loading(self):
        """Test that AI settings load correctly from configuration."""
        config_manager = ConfigurationManager()
        ai_settings = config_manager.get_ai_settings()
        
        assert isinstance(ai_settings, AISettings)
        assert isinstance(ai_settings.model, str)
        assert isinstance(ai_settings.qualification_threshold, int)
        assert 0 <= ai_settings.qualification_threshold <= 100
    
    def test_configuration_update(self):
        """Test configuration update functionality."""
        config_manager = ConfigurationManager()
        
        # Update user profile
        config_manager.update_configuration('user_profile', 'years_of_experience', 5)
        
        # Verify update
        user_profile = config_manager.get_user_profile()
        assert user_profile.years_of_experience == 5


class TestDataModels:
    """Test data model functionality."""
    
    def test_job_listing_creation(self):
        """Test JobListing creation and serialization."""
        job = JobListing(
            title="Software Engineer",
            company="Tech Corp",
            location="San Francisco, CA",
            job_url="https://example.com/job/123",
            job_site="linkedin",
            description="We are looking for a talented software engineer..."
        )
        
        assert job.title == "Software Engineer"
        assert job.company == "Tech Corp"
        assert job.job_site == "linkedin"
        
        # Test serialization
        job_dict = job.to_dict()
        assert job_dict['title'] == "Software Engineer"
        assert job_dict['company'] == "Tech Corp"
        
        # Test deserialization
        job_from_dict = JobListing.from_dict(job_dict)
        assert job_from_dict.title == job.title
        assert job_from_dict.company == job.company
    
    def test_qualification_result_creation(self):
        """Test QualificationResult creation and serialization."""
        qualification = QualificationResult(
            job_id="job-123",
            job_title="Software Engineer",
            company="Tech Corp",
            job_url="https://example.com/job/123",
            qualification_score=85,
            qualification_status=QualificationStatus.QUALIFIED,
            ai_reasoning="Strong match for experience and skills",
            required_experience="3-5 years",
            education_requirements="Bachelor's degree",
            key_skills_mentioned=["Python", "JavaScript"],
            matching_strengths=["Python experience"],
            potential_concerns=["Limited JavaScript experience"]
        )
        
        assert qualification.qualification_score == 85
        assert qualification.qualification_status == QualificationStatus.QUALIFIED
        assert qualification.user_decision == UserDecision.PENDING
        
        # Test serialization
        qual_dict = qualification.to_dict()
        assert qual_dict['qualification_score'] == 85
        assert qual_dict['qualification_status'] == 'qualified'
        
        # Test deserialization
        qual_from_dict = QualificationResult.from_dict(qual_dict)
        assert qual_from_dict.qualification_score == qualification.qualification_score
        assert qual_from_dict.qualification_status == qualification.qualification_status


class TestJobLinkProcessor:
    """Test job link processing functionality."""
    
    def test_url_cleaning(self):
        """Test URL cleaning and validation."""
        processor = JobLinkProcessor()
        
        # Test valid URLs
        assert processor._clean_url("https://linkedin.com/jobs/view/123") == "https://linkedin.com/jobs/view/123"
        assert processor._clean_url("linkedin.com/jobs/view/123") == "https://linkedin.com/jobs/view/123"
        
        # Test invalid URLs
        assert processor._clean_url("") is None
        assert processor._clean_url("not-a-url") is None
    
    def test_job_site_identification(self):
        """Test job site identification from URLs."""
        processor = JobLinkProcessor()
        
        assert processor._identify_job_site("https://linkedin.com/jobs/view/123") == "linkedin"
        assert processor._identify_job_site("https://indeed.com/viewjob?jk=abc") == "indeed"
        assert processor._identify_job_site("https://glassdoor.com/Job/123") == "glassdoor"
        assert processor._identify_job_site("https://unknown.com/job") is None
    
    def test_link_validation(self):
        """Test job link validation."""
        processor = JobLinkProcessor()
        
        test_links = [
            "https://linkedin.com/jobs/view/123",
            "https://indeed.com/viewjob?jk=abc",
            "https://unknown.com/job",
            "not-a-url"
        ]
        
        results = processor.validate_job_links(test_links)
        
        assert len(results['valid']) == 2  # LinkedIn and Indeed
        assert len(results['unsupported']) == 1  # Unknown site
        assert len(results['invalid']) == 1  # Not a URL


class TestQualificationAnalyzer:
    """Test AI qualification analysis functionality."""
    
    @patch('src.ai.qualification_analyzer.genai')
    def test_analyzer_initialization(self, mock_genai):
        """Test qualification analyzer initialization."""
        ai_settings = AISettings(api_key="test-key", model="gemini-2.0-flash-lite")
        
        with patch('google.generativeai.GenerativeModel'):
            analyzer = QualificationAnalyzer(ai_settings)
            assert analyzer.ai_settings == ai_settings
    
    def test_score_to_status_conversion(self):
        """Test qualification score to status conversion."""
        ai_settings = AISettings(api_key="test-key")
        analyzer = QualificationAnalyzer(ai_settings)
        
        assert analyzer._score_to_status(95) == QualificationStatus.HIGHLY_QUALIFIED
        assert analyzer._score_to_status(85) == QualificationStatus.QUALIFIED
        assert analyzer._score_to_status(65) == QualificationStatus.SOMEWHAT_QUALIFIED
        assert analyzer._score_to_status(25) == QualificationStatus.NOT_QUALIFIED
    
    def test_analysis_prompt_creation(self):
        """Test analysis prompt creation."""
        ai_settings = AISettings(api_key="test-key")
        analyzer = QualificationAnalyzer(ai_settings)
        
        user_profile = UserProfile(
            years_of_experience=3,
            has_college_degree=True,
            field_of_study="Computer Science",
            experience_level="mid",
            additional_skills=["Python", "JavaScript"]
        )
        
        request = AnalysisRequest(
            job_title="Software Engineer",
            company="Tech Corp",
            job_description="We are looking for a Python developer...",
            user_profile=user_profile,
            ai_settings=ai_settings
        )
        
        prompt = analyzer._create_analysis_prompt(request)
        
        assert "Software Engineer" in prompt
        assert "Tech Corp" in prompt
        assert "Python developer" in prompt
        assert "3" in prompt  # Years of experience
        assert "Computer Science" in prompt
        assert "Python" in prompt
        assert "JavaScript" in prompt
    
    def test_ai_response_parsing(self):
        """Test AI response parsing."""
        ai_settings = AISettings(api_key="test-key")
        analyzer = QualificationAnalyzer(ai_settings)
        
        # Test valid JSON response
        valid_response = '''
        {
            "qualification_score": 85,
            "ai_reasoning": "Strong match for experience and skills",
            "required_experience": "3-5 years",
            "education_requirements": "Bachelor's degree",
            "key_skills_mentioned": ["Python", "JavaScript"],
            "matching_strengths": ["Python experience"],
            "potential_concerns": ["Limited JavaScript experience"]
        }
        '''
        
        result = analyzer._parse_ai_response(valid_response)
        
        assert result['qualification_score'] == 85
        assert result['ai_reasoning'] == "Strong match for experience and skills"
        assert result['key_skills_mentioned'] == ["Python", "JavaScript"]
        assert result['matching_strengths'] == ["Python experience"]
        assert result['potential_concerns'] == ["Limited JavaScript experience"]
    
    def test_ai_response_parsing_invalid(self):
        """Test AI response parsing with invalid JSON."""
        ai_settings = AISettings(api_key="test-key")
        analyzer = QualificationAnalyzer(ai_settings)
        
        # Test invalid JSON response
        invalid_response = "This is not valid JSON"
        
        result = analyzer._parse_ai_response(invalid_response)
        
        assert result['qualification_score'] == 0
        assert "Failed to parse AI response" in result['ai_reasoning']
        assert result['potential_concerns'] == ['AI response parsing failed']


class TestIntegration:
    """Test integration between components."""
    
    @patch('src.ai.qualification_analyzer.genai')
    def test_system_initialization(self, mock_genai):
        """Test that the system can be initialized without errors."""
        from main import JobQualificationSystem
        
        # Mock Gemini client to avoid API key requirement
        with patch('google.generativeai.GenerativeModel'):
            # This should not raise any exceptions
            system = JobQualificationSystem()
            
            assert system.config_manager is not None
            assert system.logger is not None
            assert system.VERSION == "2.0.0"
    
    def test_data_model_integration(self):
        """Test that data models work together correctly."""
        # Create a job listing
        job = JobListing(
            title="Software Engineer",
            company="Tech Corp",
            job_url="https://example.com/job/123"
        )
        
        # Create a qualification result for that job
        qualification = QualificationResult(
            job_id=job.id,
            job_title=job.title,
            company=job.company,
            job_url=job.job_url,
            qualification_score=85,
            qualification_status=QualificationStatus.QUALIFIED
        )
        
        # Verify the relationship
        assert qualification.job_id == job.id
        assert qualification.job_title == job.title
        assert qualification.company == job.company


if __name__ == "__main__":
    pytest.main([__file__]) 