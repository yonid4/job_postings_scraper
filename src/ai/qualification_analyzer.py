"""
AI-powered job qualification analyzer for the Job Qualification Screening System.

This module provides functionality to analyze job descriptions against user qualifications
using Google's Gemini models to determine qualification scores and provide detailed reasoning.
"""

import os
import json
import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import google.generativeai as genai
from datetime import datetime

from ..config.config_manager import UserProfile, AISettings
from ..data.models import QualificationResult, QualificationStatus, UserDecision

logger = logging.getLogger(__name__)


@dataclass
class AnalysisRequest:
    """Request for job qualification analysis."""
    
    job_title: str
    company: str
    job_description: str
    user_profile: UserProfile
    ai_settings: AISettings
    resume_data: Optional[Dict[str, Any]] = None


@dataclass
class AnalysisResponse:
    """Response from AI qualification analysis."""
    
    qualification_score: int
    qualification_status: QualificationStatus
    ai_reasoning: str
    required_experience: str
    education_requirements: str
    key_skills_mentioned: List[str]
    matching_strengths: List[str]
    potential_concerns: List[str]
    ai_model_used: str
    analysis_duration: float


class QualificationAnalyzer:
    """
    AI-powered analyzer for job qualification assessment.
    
    This class uses Google's Gemini models to analyze job descriptions
    and determine if a user qualifies for specific positions.
    """
    
    def __init__(self, ai_settings: AISettings):
        """
        Initialize the qualification analyzer.
        
        Args:
            ai_settings: AI configuration settings
        """
        self.ai_settings = ai_settings
        self.model = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize the Google Gemini client."""
        try:
            if not self.ai_settings.api_key:
                raise ValueError("Google Gemini API key not provided")
            
            # Configure the Gemini API
            genai.configure(api_key=self.ai_settings.api_key)
            
            # Initialize the model
            self.model = genai.GenerativeModel(self.ai_settings.model)
            
            logger.info("Google Gemini client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Gemini client: {e}")
            raise
    
    def analyze_job_qualification(self, request: AnalysisRequest) -> AnalysisResponse:
        """
        Analyze job qualification using AI.
        
        Args:
            request: Analysis request containing job and user information
            
        Returns:
            Analysis response with qualification assessment
        """
        start_time = time.time()
        
        try:
            # Create the analysis prompt
            prompt = self._create_analysis_prompt(request)
            
            # Call Gemini API
            response = self._call_gemini_api(prompt)
            
            # Parse the response
            analysis_data = self._parse_ai_response(response)
            
            # Calculate analysis duration
            analysis_duration = time.time() - start_time
            
            # Create analysis response
            analysis_response = AnalysisResponse(
                qualification_score=analysis_data.get('qualification_score', 0),
                qualification_status=self._score_to_status(analysis_data.get('qualification_score', 0)),
                ai_reasoning=analysis_data.get('ai_reasoning', ''),
                required_experience=analysis_data.get('required_experience', ''),
                education_requirements=analysis_data.get('education_requirements', ''),
                key_skills_mentioned=analysis_data.get('key_skills_mentioned', []),
                matching_strengths=analysis_data.get('matching_strengths', []),
                potential_concerns=analysis_data.get('potential_concerns', []),
                ai_model_used=self.ai_settings.model,
                analysis_duration=analysis_duration
            )
            
            logger.info(f"Qualification analysis completed for {request.job_title} at {request.company}")
            logger.info(f"Score: {analysis_response.qualification_score}, Status: {analysis_response.qualification_status.value}")
            
            return analysis_response
            
        except Exception as e:
            logger.error(f"Failed to analyze job qualification: {e}")
            # Return a default response for failed analysis
            return AnalysisResponse(
                qualification_score=0,
                qualification_status=QualificationStatus.NOT_QUALIFIED,
                ai_reasoning=f"Analysis failed: {str(e)}",
                required_experience="",
                education_requirements="",
                key_skills_mentioned=[],
                matching_strengths=[],
                potential_concerns=[f"Analysis error: {str(e)}"],
                ai_model_used=self.ai_settings.model,
                analysis_duration=time.time() - start_time
            )
    
    def _create_analysis_prompt(self, request: AnalysisRequest) -> str:
        """
        Create the analysis prompt for Gemini.
        
        You can customize this method to create different types of prompts
        or add your own analysis logic.
        """
        
        # Format user profile information
        education_info = f"College graduate: {'Yes' if request.user_profile.has_college_degree else 'No'}"
        if request.user_profile.has_college_degree and request.user_profile.field_of_study:
            education_info += f", Field of study: {request.user_profile.field_of_study}"
        if request.user_profile.education_details:
            education_info += f", Details: {request.user_profile.education_details}"
        
        skills_info = ", ".join(request.user_profile.additional_skills) if request.user_profile.additional_skills else "None specified"
        
        # Add resume data if available
        resume_section = ""
        if request.resume_data:
            resume_section = f"""

DETAILED RESUME DATA:
Personal Info: {json.dumps(request.resume_data.get('personal_info', {}), indent=2)}
Education: {json.dumps(request.resume_data.get('education', []), indent=2)}
Experience: {json.dumps(request.resume_data.get('experience', []), indent=2)}
Skills: {json.dumps(request.resume_data.get('skills', {}), indent=2)}
Projects: {json.dumps(request.resume_data.get('projects', []), indent=2)}
Certifications: {request.resume_data.get('certifications', [])}
Total Experience: {request.resume_data.get('total_years_experience', 0)} years
Summary: {request.resume_data.get('summary', '')}
"""
        
        prompt = f"""
You are a job qualification expert. Analyze this job description and determine if a candidate qualifies.

CANDIDATE PROFILE:
- Years of Experience: {request.user_profile.years_of_experience}
- Education: {education_info}
- Experience Level: {request.user_profile.experience_level}
- Additional Skills: {skills_info}
- Preferred Locations: {', '.join(request.user_profile.preferred_locations) if request.user_profile.preferred_locations else 'Any'}
- Salary Range: ${request.user_profile.salary_min or 'N/A'} - ${request.user_profile.salary_max or 'N/A'}
- Remote Preference: {request.user_profile.remote_preference}{resume_section}

JOB INFORMATION:
- Title: {request.job_title}
- Company: {request.company}

JOB DESCRIPTION:
{request.job_description}

Please provide a comprehensive analysis in the following JSON format:

{{
    "qualification_score": <0-100 integer>,
    "ai_reasoning": "<detailed reasoning for the score>",
    "required_experience": "<extracted experience requirements>",
    "education_requirements": "<extracted education requirements>",
    "key_skills_mentioned": ["skill1", "skill2", "skill3"],
    "matching_strengths": ["strength1", "strength2"],
    "potential_concerns": ["concern1", "concern2"]
}}

Guidelines for scoring:
- 90-100: Highly Qualified - Perfect match for experience, education, and skills
- 70-89: Qualified - Good match with minor gaps that can be addressed
- 50-69: Somewhat Qualified - Some relevant experience but significant gaps
- 30-49: Marginally Qualified - Limited relevant experience or major gaps
- 0-29: Not Qualified - Significant mismatch in requirements

Focus on:
1. Experience level alignment
2. Education requirements vs candidate background
3. Skills match and transferability
4. Overall fit for the role
5. Potential for growth and learning
6. Specific resume achievements and projects that align with job requirements

Provide specific, actionable reasoning for your assessment.
"""
        
        return prompt.strip()
    
    def _call_gemini_api(self, prompt: str) -> str:
        """
        Call the Gemini API with the analysis prompt.
        
        You can customize this method to add your own API call logic,
        error handling, or response processing.
        """
        try:
            # Generate content using Gemini
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.ai_settings.temperature,
                    max_output_tokens=self.ai_settings.max_tokens,
                )
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the AI response and extract structured data.
        
        You can customize this method to handle different response formats
        or add your own parsing logic.
        """
        try:
            # Try to extract JSON from the response
            # Sometimes the AI includes additional text before or after the JSON
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in AI response")
            
            json_str = response[json_start:json_end]
            data = json.loads(json_str)
            
            # Validate required fields
            required_fields = ['qualification_score', 'ai_reasoning']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Ensure qualification score is within valid range
            score = data.get('qualification_score', 0)
            if not isinstance(score, int) or score < 0 or score > 100:
                data['qualification_score'] = max(0, min(100, int(score)))
            
            # Ensure lists are properly formatted
            for list_field in ['key_skills_mentioned', 'matching_strengths', 'potential_concerns']:
                if list_field not in data or not isinstance(data[list_field], list):
                    data[list_field] = []
            
            # Ensure string fields are properly formatted
            for string_field in ['required_experience', 'education_requirements']:
                if string_field not in data or not isinstance(data[string_field], str):
                    data[string_field] = ""
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"Response: {response}")
            # Return a default response
            return {
                'qualification_score': 0,
                'ai_reasoning': f"Failed to parse AI response: {str(e)}",
                'required_experience': '',
                'education_requirements': '',
                'key_skills_mentioned': [],
                'matching_strengths': [],
                'potential_concerns': ['AI response parsing failed']
            }
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            raise
    
    def _score_to_status(self, score: int) -> QualificationStatus:
        """
        Convert qualification score to status.
        
        You can customize this method to use different scoring thresholds
        or add your own status logic.
        """
        if score >= 90:
            return QualificationStatus.HIGHLY_QUALIFIED
        elif score >= 70:
            return QualificationStatus.QUALIFIED
        elif score >= 50:
            return QualificationStatus.SOMEWHAT_QUALIFIED
        else:
            return QualificationStatus.NOT_QUALIFIED
    
    def create_qualification_result(
        self, 
        job_id: str,
        job_title: str,
        company: str,
        job_url: str,
        analysis_response: AnalysisResponse
    ) -> QualificationResult:
        """
        Create a QualificationResult from analysis response.
        
        Args:
            job_id: The job ID
            job_title: The job title
            company: The company name
            job_url: The job URL
            analysis_response: The AI analysis response
            
        Returns:
            QualificationResult object
        """
        return QualificationResult(
            job_id=job_id,
            job_title=job_title,
            company=company,
            job_url=job_url,
            qualification_score=analysis_response.qualification_score,
            qualification_status=analysis_response.qualification_status,
            ai_reasoning=analysis_response.ai_reasoning,
            required_experience=analysis_response.required_experience,
            education_requirements=analysis_response.education_requirements,
            key_skills_mentioned=analysis_response.key_skills_mentioned,
            matching_strengths=analysis_response.matching_strengths,
            potential_concerns=analysis_response.potential_concerns,
            user_decision=UserDecision.PENDING,
            ai_model_used=analysis_response.ai_model_used,
            analysis_duration=analysis_response.analysis_duration
        )
    
    def batch_analyze_jobs(
        self, 
        jobs: List[Dict[str, Any]], 
        user_profile: UserProfile
    ) -> List[QualificationResult]:
        """
        Analyze multiple jobs in batch.
        
        Args:
            jobs: List of job dictionaries with title, company, description, etc.
            user_profile: User qualification profile
            
        Returns:
            List of QualificationResult objects
        """
        results = []
        
        for i, job in enumerate(jobs, 1):
            try:
                logger.info(f"Analyzing job {i}/{len(jobs)}: {job.get('title', 'Unknown')}")
                
                request = AnalysisRequest(
                    job_title=job.get('title', ''),
                    company=job.get('company', ''),
                    job_description=job.get('description', ''),
                    user_profile=user_profile,
                    ai_settings=self.ai_settings
                )
                
                analysis_response = self.analyze_job_qualification(request)
                
                qualification_result = self.create_qualification_result(
                    job_id=job.get('id', ''),
                    job_title=job.get('title', ''),
                    company=job.get('company', ''),
                    job_url=job.get('job_url', ''),
                    analysis_response=analysis_response
                )
                
                results.append(qualification_result)
                
                # Add delay between requests to respect rate limits
                if i < len(jobs):
                    time.sleep(1)  # 1 second delay between requests
                    
            except Exception as e:
                logger.error(f"Failed to analyze job {i}: {e}")
                # Create a failed result
                failed_result = QualificationResult(
                    job_id=job.get('id', ''),
                    job_title=job.get('title', ''),
                    company=job.get('company', ''),
                    job_url=job.get('job_url', ''),
                    qualification_score=0,
                    qualification_status=QualificationStatus.NOT_QUALIFIED,
                    ai_reasoning=f"Analysis failed: {str(e)}",
                    potential_concerns=[f"Analysis error: {str(e)}"]
                )
                results.append(failed_result)
        
        return results
    
    # Customization methods - you can override these to implement your own logic
    
    def custom_analysis_logic(self, request: AnalysisRequest) -> AnalysisResponse:
        """
        Custom analysis logic that you can implement.
        
        Override this method to implement your own qualification analysis
        instead of using the default AI-based approach.
        
        Args:
            request: Analysis request containing job and user information
            
        Returns:
            Analysis response with qualification assessment
        """
        # Example custom logic - you can replace this with your own implementation
        start_time = time.time()
        
        # Your custom analysis logic here
        # For example, you could use rule-based scoring, keyword matching, etc.
        
        # Placeholder implementation
        score = self._calculate_custom_score(request)
        reasoning = self._generate_custom_reasoning(request)
        
        analysis_duration = time.time() - start_time
        
        return AnalysisResponse(
            qualification_score=score,
            qualification_status=self._score_to_status(score),
            ai_reasoning=reasoning,
            required_experience="Custom analysis",
            education_requirements="Custom analysis",
            key_skills_mentioned=[],
            matching_strengths=[],
            potential_concerns=[],
            ai_model_used="custom_logic",
            analysis_duration=analysis_duration
        )
    
    def _calculate_custom_score(self, request: AnalysisRequest) -> int:
        """
        Calculate qualification score using custom logic.
        
        Implement your own scoring algorithm here.
        """
        # Example: Simple keyword matching
        score = 50  # Base score
        
        job_desc_lower = request.job_description.lower()
        user_skills = [skill.lower() for skill in request.user_profile.additional_skills]
        
        # Add points for matching skills
        for skill in user_skills:
            if skill in job_desc_lower:
                score += 10
        
        # Add points for experience level match
        if request.user_profile.experience_level in job_desc_lower:
            score += 20
        
        return min(100, max(0, score))
    
    def _generate_custom_reasoning(self, request: AnalysisRequest) -> str:
        """
        Generate reasoning using custom logic.
        
        Implement your own reasoning generation here.
        """
        return f"Custom analysis for {request.job_title} at {request.company}" 