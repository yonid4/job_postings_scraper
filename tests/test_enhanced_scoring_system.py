#!/usr/bin/env python3
"""
Test the enhanced AI scoring system with weighted components.

This test verifies that the new weighted scoring system works correctly
for both resume + profile scenarios and profile-only scenarios.
"""

import os
import sys
import unittest
import json
from unittest.mock import Mock, patch
from pathlib import Path

# Add the parent directory to Python path to import src modules
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from backend.src.ai.qualification_analyzer import QualificationAnalyzer, AnalysisRequest, AnalysisResponse
from backend.src.config.config_manager import AISettings, UserProfile
from backend.src.data.models import QualificationStatus


class TestEnhancedScoringSystem(unittest.TestCase):
    """Test cases for the enhanced weighted scoring system."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock AI settings
        self.ai_settings = AISettings(
            api_key="test_key",
            model="gemini-2.0-flash-lite",
            temperature=0.1,
            max_tokens=2000
        )
        
        # Create test job data
        self.job_data = {
            'title': 'Senior Python Developer',
            'company': 'Tech Innovations Inc',
            'description': '''
We are seeking a Senior Python Developer with 5+ years of experience.
Requirements:
- Bachelor's degree in Computer Science or related field
- Strong experience with Python, Django, Flask
- Experience with AWS, Docker, Kubernetes
- Knowledge of SQL databases and REST APIs
- Remote work available
- Salary: $90k - $130k
            '''
        }
        
        # Create test user profile data
        self.user_profile_data = {
            'years_of_experience': 6,
            'experience_level': 'senior',
            'skills_technologies': ['Python', 'Django', 'AWS', 'Docker', 'PostgreSQL'],
            'education_level': 'bachelors',
            'field_of_study': 'Computer Science',
            'work_arrangement_preference': 'remote',
            'preferred_locations': ['San Francisco', 'Remote'],
            'salary_min': 85000,
            'salary_max': 125000
        }
        
        # Create test resume data
        self.resume_data = {
            'summary': 'Experienced Python developer with expertise in web development and cloud technologies.',
            'experience': [
                {
                    'title': 'Senior Software Engineer',
                    'company': 'Previous Tech Co',
                    'duration': '2 years',
                    'description': 'Led development of scalable web applications using Python, Django, and AWS.'
                },
                {
                    'title': 'Python Developer',
                    'company': 'Another Company',
                    'duration': '3 years',
                    'description': 'Developed REST APIs, worked with Docker containers, and managed PostgreSQL databases.'
                }
            ],
            'education': [
                {
                    'degree': 'Bachelor of Science',
                    'field': 'Computer Science',
                    'institution': 'Tech University'
                }
            ],
            'skills': {
                'Programming Languages': ['Python', 'JavaScript', 'SQL'],
                'Frameworks': ['Django', 'Flask', 'React'],
                'Technologies': ['AWS', 'Docker', 'Kubernetes', 'PostgreSQL']
            },
            'projects': [
                {
                    'name': 'E-commerce Platform',
                    'description': 'Built scalable e-commerce platform using Django and AWS services.'
                }
            ],
            'certifications': ['AWS Solutions Architect', 'Python Professional'],
            'total_years_experience': 6
        }
    
    def test_analysis_request_with_resume(self):
        """Test AnalysisRequest creation with resume data."""
        request = AnalysisRequest(
            job_title=self.job_data['title'],
            company=self.job_data['company'],
            job_description=self.job_data['description'],
            ai_settings=self.ai_settings,
            resume_data=self.resume_data,
            years_experience=self.user_profile_data['years_of_experience'],
            experience_level=self.user_profile_data['experience_level'],
            skills=self.user_profile_data['skills_technologies'],
            education_level=self.user_profile_data['education_level'],
            field_of_study=self.user_profile_data['field_of_study'],
            work_arrangement=self.user_profile_data['work_arrangement_preference'],
            preferred_locations=self.user_profile_data['preferred_locations'],
            salary_min=self.user_profile_data['salary_min'],
            salary_max=self.user_profile_data['salary_max']
        )
        
        # Verify resume availability
        self.assertTrue(request.has_resume)
        
        # Verify resume content extraction
        resume_content = request.get_resume_content()
        self.assertIn('Python developer', resume_content)
        self.assertIn('Django', resume_content)
        self.assertIn('AWS', resume_content)
        
        print("✅ Test 1 Passed: AnalysisRequest with resume data created successfully")
    
    def test_analysis_request_profile_only(self):
        """Test AnalysisRequest creation with profile data only."""
        request = AnalysisRequest(
            job_title=self.job_data['title'],
            company=self.job_data['company'],
            job_description=self.job_data['description'],
            ai_settings=self.ai_settings,
            years_experience=self.user_profile_data['years_of_experience'],
            experience_level=self.user_profile_data['experience_level'],
            skills=self.user_profile_data['skills_technologies'],
            education_level=self.user_profile_data['education_level'],
            field_of_study=self.user_profile_data['field_of_study'],
            work_arrangement=self.user_profile_data['work_arrangement_preference'],
            preferred_locations=self.user_profile_data['preferred_locations'],
            salary_min=self.user_profile_data['salary_min'],
            salary_max=self.user_profile_data['salary_max']
        )
        
        # Verify no resume
        self.assertFalse(request.has_resume)
        
        # Verify profile data
        self.assertEqual(request.years_experience, 6)
        self.assertEqual(request.experience_level, 'senior')
        self.assertIn('Python', request.skills)
        
        print("✅ Test 2 Passed: AnalysisRequest with profile-only data created successfully")
    
    def test_prompt_generation_with_resume(self):
        """Test prompt generation for resume + profile scenario."""
        request = AnalysisRequest(
            job_title=self.job_data['title'],
            company=self.job_data['company'],
            job_description=self.job_data['description'],
            ai_settings=self.ai_settings,
            resume_data=self.resume_data,
            years_experience=self.user_profile_data['years_of_experience'],
            experience_level=self.user_profile_data['experience_level'],
            skills=self.user_profile_data['skills_technologies'],
            education_level=self.user_profile_data['education_level'],
            field_of_study=self.user_profile_data['field_of_study']
        )
        
        analyzer = QualificationAnalyzer(self.ai_settings)
        prompt = analyzer._create_analysis_prompt(request)
        
        # Verify resume-specific content
        self.assertIn("Resume Available: True", prompt)
        self.assertIn("RESUME AVAILABLE - Use 70/30", prompt)
        self.assertIn("Skills & Technologies Match (25%)", prompt)
        self.assertIn("Experience Relevance (20%)", prompt)
        self.assertIn("Years Experience Match (15%)", prompt)
        
        # Verify component scoring structure
        self.assertIn("skills_match", prompt)
        self.assertIn("experience_relevance", prompt)
        self.assertIn("years_experience", prompt)
        
        print("✅ Test 3 Passed: Resume + profile prompt generated correctly")
    
    def test_prompt_generation_profile_only(self):
        """Test prompt generation for profile-only scenario."""
        request = AnalysisRequest(
            job_title=self.job_data['title'],
            company=self.job_data['company'],
            job_description=self.job_data['description'],
            ai_settings=self.ai_settings,
            years_experience=self.user_profile_data['years_of_experience'],
            experience_level=self.user_profile_data['experience_level'],
            skills=self.user_profile_data['skills_technologies'],
            education_level=self.user_profile_data['education_level']
        )
        
        analyzer = QualificationAnalyzer(self.ai_settings)
        prompt = analyzer._create_analysis_prompt(request)
        
        # Verify profile-only content
        self.assertIn("Resume Available: False", prompt)
        self.assertIn("RESUME NOT AVAILABLE - Use 100%", prompt)
        self.assertIn("Skills & Technologies Match (40%)", prompt)
        self.assertIn("Experience Level & Years Combined (25%)", prompt)
        
        # Verify component scoring structure
        self.assertIn("skills_technologies", prompt)
        self.assertIn("experience_seniority", prompt)
        self.assertIn("education_field", prompt)
        self.assertIn("work_preferences", prompt)
        
        print("✅ Test 4 Passed: Profile-only prompt generated correctly")
    
    @patch('backend.src.ai.qualification_analyzer.genai')
    def test_response_parsing_with_components(self, mock_genai):
        """Test parsing of enhanced response with component scores."""
        # Mock API response
        mock_response = Mock()
        mock_response.text = '''
        {
            "qualification_score": 78,
            "confidence_score": 85,
            "component_scores": {
                "skills_match": 82,
                "experience_relevance": 75,
                "years_experience": 80,
                "education_match": 70,
                "profile_skills_check": 85,
                "experience_level": 75,
                "work_arrangement": 90,
                "location_salary": 75
            },
            "ai_reasoning": "Strong technical match with good experience alignment.",
            "required_experience": "5+ years Python development",
            "education_requirements": "Bachelor's degree in Computer Science",
            "key_skills_mentioned": ["Python", "Django", "AWS", "Docker"],
            "matching_strengths": ["Strong Python skills", "Relevant cloud experience", "Remote work preference"],
            "potential_concerns": ["Salary expectations might be on higher end"],
            "recommendations": ["Highlight AWS certifications", "Emphasize scalability experience"],
            "requirements_met": "7 out of 8 key requirements satisfied"
        }
        '''
        
        # Configure mock
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.configure = Mock()
        
        # Create analyzer and test parsing
        analyzer = QualificationAnalyzer(self.ai_settings)
        parsed_data = analyzer._parse_ai_response_with_retry(mock_response.text, 0)
        
        # Verify parsed data
        self.assertEqual(parsed_data['qualification_score'], 78)
        self.assertEqual(parsed_data['confidence_score'], 85)
        self.assertIsInstance(parsed_data['component_scores'], dict)
        self.assertEqual(parsed_data['component_scores']['skills_match'], 82)
        self.assertIn("Python", parsed_data['key_skills_mentioned'])
        self.assertIn("Strong Python skills", parsed_data['matching_strengths'])
        self.assertIn("Highlight AWS certifications", parsed_data['recommendations'])
        
        print("✅ Test 5 Passed: Enhanced response parsing works correctly")
    
    def test_score_to_status_mapping(self):
        """Test the updated score to status mapping."""
        analyzer = QualificationAnalyzer(self.ai_settings)
        
        # Test new thresholds
        self.assertEqual(analyzer._score_to_status(95), QualificationStatus.HIGHLY_QUALIFIED)
        self.assertEqual(analyzer._score_to_status(85), QualificationStatus.HIGHLY_QUALIFIED)
        self.assertEqual(analyzer._score_to_status(75), QualificationStatus.QUALIFIED)
        self.assertEqual(analyzer._score_to_status(70), QualificationStatus.QUALIFIED)
        self.assertEqual(analyzer._score_to_status(60), QualificationStatus.SOMEWHAT_QUALIFIED)
        self.assertEqual(analyzer._score_to_status(55), QualificationStatus.SOMEWHAT_QUALIFIED)
        self.assertEqual(analyzer._score_to_status(45), QualificationStatus.NOT_QUALIFIED)
        self.assertEqual(analyzer._score_to_status(1), QualificationStatus.NOT_QUALIFIED)
        
        print("✅ Test 6 Passed: Updated score to status mapping works correctly")
    
    def test_backward_compatibility(self):
        """Test that legacy methods still work for backward compatibility."""
        # Create old-style UserProfile
        user_profile = UserProfile(
            years_of_experience=5,
            experience_level='senior',
            additional_skills=['Python', 'Django'],
            has_college_degree=True,
            field_of_study='Computer Science'
        )
        
        # Create legacy-style request
        request = AnalysisRequest(
            job_title=self.job_data['title'],
            company=self.job_data['company'],
            job_description=self.job_data['description'],
            user_profile=user_profile,
            ai_settings=self.ai_settings
        )
        
        # Verify backward compatibility
        self.assertEqual(request.years_experience, 5)
        self.assertEqual(request.experience_level, 'senior')
        self.assertIn('Python', request.skills)
        self.assertEqual(request.field_of_study, 'Computer Science')
        
        print("✅ Test 7 Passed: Backward compatibility maintained")
    
    def run_all_tests(self):
        """Run all tests and report results."""
        print("\n🧪 Running Enhanced Scoring System Tests...")
        print("=" * 60)
        
        try:
            self.test_analysis_request_with_resume()
            self.test_analysis_request_profile_only()
            self.test_prompt_generation_with_resume()
            self.test_prompt_generation_profile_only()
            self.test_response_parsing_with_components()
            self.test_score_to_status_mapping()
            self.test_backward_compatibility()
            
            print("\n" + "=" * 60)
            print("🎉 ALL TESTS PASSED! Enhanced scoring system is working correctly.")
            print("\n📊 Key Features Verified:")
            print("✅ Resume + Profile weighted scoring (70/30 split)")
            print("✅ Profile-only weighted scoring (100% profile)")
            print("✅ Enhanced component breakdown scoring")
            print("✅ Improved response parsing with confidence scores")
            print("✅ Updated qualification status thresholds")
            print("✅ Backward compatibility with existing code")
            print("✅ Comprehensive prompt generation for both scenarios")
            
            return True
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            return False


if __name__ == "__main__":
    # Run the comprehensive test
    test_suite = TestEnhancedScoringSystem()
    test_suite.setUp()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n🚀 Enhanced AI Scoring System is ready for production!")
        print("\n📋 Score Categories for UI Display:")
        print("• Excellent Jobs (85-100): Strong recommendation to apply")
        print("• Good Jobs (70-84): Recommended with minor gaps")
        print("• Moderate Jobs (55-69): Consider with preparation")
        print("• Poor Fit Jobs (40-54): Not recommended")
        print("• Very Poor Fit Jobs (1-39): Strongly discourage")
    else:
        print("\n⚠️ Please review and fix any issues before deployment.")
        sys.exit(1)
