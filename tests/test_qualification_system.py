"""
Tests for the enhanced qualification analyzer with retry logic.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

from backend.src.ai.qualification_analyzer import (
    QualificationAnalyzer, 
    AnalysisRequest, 
    AnalysisResponse,
    JobEvaluationResult
)
from backend.src.config.config_manager import UserProfile, AISettings
from backend.src.data.models import QualificationStatus, UserDecision


class TestQualificationAnalyzerRetryLogic:
    """Test the retry logic for Gemini job evaluation."""
    
    @pytest.fixture
    def ai_settings(self):
        """Create test AI settings."""
        return AISettings(
            api_key="test-api-key",
            model="gemini-pro",
            temperature=0.7,
            max_tokens=1000,
            qualification_threshold=70
        )
    
    @pytest.fixture
    def user_profile(self):
        """Create test user profile."""
        return UserProfile(
            years_of_experience=5,
            has_college_degree=True,
            field_of_study="Computer Science",
            education_details="Bachelor's in Computer Science",
            experience_level="mid",
            additional_skills=["Python", "JavaScript", "React"],
            preferred_locations=["San Francisco", "New York"],
            salary_min=80000,
            salary_max=120000,
            remote_preference="any"
        )
    
    @pytest.fixture
    def mock_job(self):
        """Create a test job."""
        return {
            'id': 'test-job-123',
            'title': 'Software Engineer',
            'company': 'Test Company',
            'linkedin_url': 'https://example.com/job/123',
            'description': 'We are looking for a Python developer with 3+ years of experience.'
        }
    
    @pytest.fixture
    def analyzer(self, ai_settings):
        """Create a qualification analyzer with mocked Gemini client."""
        with patch('backend.src.ai.qualification_analyzer.genai') as mock_genai:
            mock_genai.configure.return_value = None
            mock_model = Mock()
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.types.GenerationConfig.return_value = Mock()
            
            analyzer = QualificationAnalyzer(ai_settings)
            analyzer.model = mock_model
            return analyzer
    
    def test_analyze_job_qualification_with_retry_success_first_attempt(self, analyzer, user_profile, mock_job):
        """Test successful analysis on first attempt."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.text = '''
        {
            "qualification_score": 85,
            "ai_reasoning": "Strong match for Python development role",
            "required_experience": "3+ years Python development",
            "education_requirements": "Bachelor's degree in Computer Science",
            "key_skills_mentioned": ["Python", "JavaScript"],
            "matching_strengths": ["Python", "5 years experience"],
            "potential_concerns": []
        }
        '''
        analyzer.model.generate_content.return_value = mock_response
        
        # Create analysis request
        request = AnalysisRequest(
            job_title=mock_job['title'],
            company=mock_job['company'],
            job_description=mock_job['description'],
            user_profile=user_profile,
            ai_settings=analyzer.ai_settings
        )
        
        # Test the retry method
        result = analyzer.analyze_job_qualification_with_retry(request, max_retries=2)
        
        # Verify result
        assert result.qualification_score == 85
        assert result.qualification_status == QualificationStatus.HIGHLY_QUALIFIED  # Score 85 maps to HIGHLY_QUALIFIED
        assert "Strong match" in result.ai_reasoning
        assert result.ai_model_used == "gemini-pro"
        
        # Verify API was called only once
        analyzer.model.generate_content.assert_called_once()
    
    def test_analyze_job_qualification_with_retry_success_second_attempt(self, analyzer, user_profile, mock_job):
        """Test successful analysis on second attempt after first failure."""
        # Mock first attempt failure, second attempt success
        mock_response = Mock()
        mock_response.text = '''
        {
            "qualification_score": 75,
            "ai_reasoning": "Good match for the role",
            "required_experience": "3+ years experience",
            "education_requirements": "Bachelor's degree",
            "key_skills_mentioned": ["Python"],
            "matching_strengths": ["Python experience"],
            "potential_concerns": []
        }
        '''
        
        # First call fails, second call succeeds
        analyzer.model.generate_content.side_effect = [
            Exception("API timeout"),  # First attempt fails
            mock_response  # Second attempt succeeds
        ]
        
        request = AnalysisRequest(
            job_title=mock_job['title'],
            company=mock_job['company'],
            job_description=mock_job['description'],
            user_profile=user_profile,
            ai_settings=analyzer.ai_settings
        )
        
        # Test the retry method
        result = analyzer.analyze_job_qualification_with_retry(request, max_retries=2)
        
        # Verify result
        assert result.qualification_score == 75
        assert result.qualification_status == QualificationStatus.QUALIFIED
        
        # Verify API was called twice
        assert analyzer.model.generate_content.call_count == 2
    
    def test_analyze_job_qualification_with_retry_all_attempts_fail(self, analyzer, user_profile, mock_job):
        """Test that exception is raised when all attempts fail."""
        # Mock all attempts failing
        analyzer.model.generate_content.side_effect = [
            Exception("API timeout"),
            Exception("Network error"),
            Exception("Service unavailable")
        ]
        
        request = AnalysisRequest(
            job_title=mock_job['title'],
            company=mock_job['company'],
            job_description=mock_job['description'],
            user_profile=user_profile,
            ai_settings=analyzer.ai_settings
        )
        
        # Test that exception is raised
        with pytest.raises(Exception) as exc_info:
            analyzer.analyze_job_qualification_with_retry(request, max_retries=2)
        
        assert "Gemini analysis failed after 3 attempts" in str(exc_info.value)
        
        # Verify API was called three times
        assert analyzer.model.generate_content.call_count == 3
    
    def test_evaluate_job_with_retry_success(self, analyzer, user_profile, mock_job):
        """Test successful job evaluation with retry logic."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.text = '''
        {
            "qualification_score": 90,
            "ai_reasoning": "Excellent match",
            "required_experience": "3+ years",
            "education_requirements": "Bachelor's",
            "key_skills_mentioned": ["Python"],
            "matching_strengths": ["Python", "experience"],
            "potential_concerns": []
        }
        '''
        analyzer.model.generate_content.return_value = mock_response
        
        # Test job evaluation
        result = analyzer.evaluate_job_with_retry(mock_job, user_profile, max_retries=2)
        
        # Verify result
        assert result.success is True
        assert result.qualification_result is not None
        assert result.qualification_result.qualification_score == 90
        assert result.qualification_result.qualification_status == QualificationStatus.HIGHLY_QUALIFIED
        assert result.attempts == 1
        assert result.job_id == "test-job-123"
        assert result.job_title == "Software Engineer"
    
    def test_evaluate_job_with_retry_failure(self, analyzer, user_profile, mock_job):
        """Test failed job evaluation with retry logic."""
        # Mock all attempts failing
        analyzer.model.generate_content.side_effect = [
            Exception("API error"),
            Exception("Network timeout"),
            Exception("Service unavailable")
        ]
        
        # Test job evaluation
        result = analyzer.evaluate_job_with_retry(mock_job, user_profile, max_retries=2)
        
        # Verify result
        assert result.success is False
        assert result.qualification_result is None
        assert result.attempts == 3
        assert "All 3 attempts failed" in result.error_message
        assert result.job_id == "test-job-123"
        assert result.job_title == "Software Engineer"
    
    def test_batch_analyze_jobs_with_retry_mixed_results(self, analyzer, user_profile):
        """Test batch analysis with mixed success/failure results."""
        jobs = [
            {
                'id': 'job-1',
                'title': 'Python Developer',
                'company': 'Company A',
                'job_url': 'https://example.com/job1',
                'description': 'Python role'
            },
            {
                'id': 'job-2',
                'title': 'JavaScript Developer',
                'company': 'Company B',
                'job_url': 'https://example.com/job2',
                'description': 'JavaScript role'
            },
            {
                'id': 'job-3',
                'title': 'Java Developer',
                'company': 'Company C',
                'job_url': 'https://example.com/job3',
                'description': 'Java role'
            }
        ]
        
        # Mock responses: job-1 success, job-2 failure, job-3 success
        mock_response_1 = Mock()
        mock_response_1.text = '''
        {
            "qualification_score": 85,
            "ai_reasoning": "Good match",
            "required_experience": "3+ years",
            "education_requirements": "Bachelor's",
            "key_skills_mentioned": ["Python"],
            "matching_strengths": ["Python"],
            "potential_concerns": []
        }
        '''
        
        mock_response_3 = Mock()
        mock_response_3.text = '''
        {
            "qualification_score": 70,
            "ai_reasoning": "Decent match",
            "required_experience": "2+ years",
            "education_requirements": "Bachelor's",
            "key_skills_mentioned": ["Java"],
            "matching_strengths": ["experience"],
            "potential_concerns": []
        }
        '''
        
        # Mock API calls: success, failure, success
        analyzer.model.generate_content.side_effect = [
            mock_response_1,  # job-1 success
            Exception("API error"),  # job-2 failure
            Exception("Network error"),  # job-2 retry failure
            Exception("Service error"),  # job-2 final failure
            mock_response_3,  # job-3 success
        ]
        
        # Test batch analysis
        successful_results, all_results = analyzer.batch_analyze_jobs_with_retry(
            jobs, user_profile, max_retries=2
        )
        
        # Verify results
        assert len(successful_results) == 2  # Only successful jobs
        assert len(all_results) == 3  # All jobs including failures
        
        # Check successful results
        assert successful_results[0].job_id == "job-1"
        assert successful_results[0].qualification_score == 85
        assert successful_results[1].job_id == "job-3"
        assert successful_results[1].qualification_score == 70
        
        # Check all results
        assert all_results[0].success is True
        assert all_results[1].success is False
        assert all_results[2].success is True
        
        # Verify API was called 5 times (1 + 3 + 1)
        assert analyzer.model.generate_content.call_count == 5
    
    def test_legacy_methods_backward_compatibility(self, analyzer, user_profile, mock_job):
        """Test that legacy methods still work and use retry logic."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.text = '''
        {
            "qualification_score": 80,
            "ai_reasoning": "Good match",
            "required_experience": "3+ years",
            "education_requirements": "Bachelor's",
            "key_skills_mentioned": ["Python"],
            "matching_strengths": ["Python"],
            "potential_concerns": []
        }
        '''
        analyzer.model.generate_content.return_value = mock_response
        
        # Test legacy analyze_job_qualification method
        request = AnalysisRequest(
            job_title=mock_job['title'],
            company=mock_job['company'],
            job_description=mock_job['description'],
            user_profile=user_profile,
            ai_settings=analyzer.ai_settings
        )
        
        result = analyzer.analyze_job_qualification(request)
        assert result.qualification_score == 80
        assert result.qualification_status == QualificationStatus.QUALIFIED
        
        # Test legacy batch_analyze_jobs method
        jobs = [mock_job]
        results = analyzer.batch_analyze_jobs(jobs, user_profile)
        assert len(results) == 1
        assert results[0].qualification_score == 80


if __name__ == "__main__":
    pytest.main([__file__]) 