"""
AI-powered job qualification analyzer for the Job Qualification Screening System.

This module provides functionality to analyze job descriptions against user qualifications
using Google's Gemini models to determine qualification scores and provide detailed reasoning.
"""

import os
import json
import logging
import time
from typing import Dict, Any, Optional, List, Tuple
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


@dataclass
class JobEvaluationResult:
    """Result of job evaluation with retry information."""
    
    success: bool
    qualification_result: Optional[QualificationResult]
    attempts: int
    error_message: Optional[str] = None
    job_id: str = ""
    job_title: str = ""


class QualificationAnalyzer:
    """
    AI-powered analyzer for job qualification assessment with robust retry logic.
    
    This class uses Google's Gemini models to analyze job descriptions
    and determine if a user qualifies for specific positions.
    Implements retry logic for failed API calls and JSON parsing.
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
    
    def analyze_job_qualification_with_retry(self, request: AnalysisRequest, max_retries: int = 2) -> AnalysisResponse:
        """
        Analyze job qualification using AI with retry logic.
        
        Args:
            request: Analysis request containing job and user information
            max_retries: Maximum number of retry attempts (default: 2)
            
        Returns:
            Analysis response with qualification assessment
            
        Raises:
            Exception: If all retry attempts fail
        """
        last_error = None
        
        for attempt in range(max_retries + 1):  # +1 for initial attempt
            try:
                logger.info(f"Gemini analysis attempt {attempt + 1}/{max_retries + 1} for job: {request.job_title}")
                
                # Call the API
                response = self._call_gemini_api_with_retry(request, attempt)
                
                # Parse the response
                parsed_data = self._parse_ai_response_with_retry(response, attempt)
                
                # Create analysis response
                analysis_response = self._create_analysis_response(parsed_data, request)
                
                logger.info(f"✅ Gemini analysis successful on attempt {attempt + 1} for job: {request.job_title}")
                return analysis_response
                
            except Exception as e:
                last_error = e
                logger.warning(f"⚠️ Gemini analysis attempt {attempt + 1} failed for job '{request.job_title}': {e}")
                
                if attempt < max_retries:
                    # Wait before retry with exponential backoff
                    wait_time = (2 ** attempt) * 1  # 1s, 2s, 4s, etc.
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ All {max_retries + 1} attempts failed for job '{request.job_title}': {e}")
        
        # If we get here, all attempts failed
        raise Exception(f"Gemini analysis failed after {max_retries + 1} attempts: {last_error}")
    
    def _call_gemini_api_with_retry(self, request: AnalysisRequest, attempt: int) -> str:
        """
        Call the Gemini API with retry logic for network/API errors.
        
        Args:
            request: Analysis request
            attempt: Current attempt number (for logging)
            
        Returns:
            API response text
            
        Raises:
            Exception: If API call fails
        """
        try:
            prompt = self._create_analysis_prompt(request)
            
            # Generate content using Gemini
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.ai_settings.temperature,
                    max_output_tokens=self.ai_settings.max_tokens,
                )
            )
            
            if not response.text:
                raise ValueError("Empty response from Gemini API")
            
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini API call failed on attempt {attempt + 1}: {e}")
            raise
    
    def _parse_ai_response_with_retry(self, response: str, attempt: int) -> Dict[str, Any]:
        """
        Parse the AI response with retry logic for JSON parsing errors.
        
        Args:
            response: Raw API response text
            attempt: Current attempt number (for logging)
            
        Returns:
            Parsed JSON data
            
        Raises:
            Exception: If JSON parsing fails
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
            logger.error(f"JSON parsing failed on attempt {attempt + 1}: {e}")
            logger.error(f"Response: {response}")
            raise ValueError(f"Invalid JSON response: {e}")
        except Exception as e:
            logger.error(f"Response parsing failed on attempt {attempt + 1}: {e}")
            raise
    
    def _create_analysis_response(self, parsed_data: Dict[str, Any], request: AnalysisRequest) -> AnalysisResponse:
        """
        Create AnalysisResponse from parsed data.
        
        Args:
            parsed_data: Parsed JSON data from API
            request: Original analysis request
            
        Returns:
            AnalysisResponse object
        """
        score = parsed_data.get('qualification_score', 0)
        
        return AnalysisResponse(
            qualification_score=score,
            qualification_status=self._score_to_status(score),
            ai_reasoning=parsed_data.get('ai_reasoning', ''),
            required_experience=parsed_data.get('required_experience', ''),
            education_requirements=parsed_data.get('education_requirements', ''),
            key_skills_mentioned=parsed_data.get('key_skills_mentioned', []),
            matching_strengths=parsed_data.get('matching_strengths', []),
            potential_concerns=parsed_data.get('potential_concerns', []),
            ai_model_used=self.ai_settings.model,
            analysis_duration=0.0  # Will be set by caller
        )
    
    def evaluate_job_with_retry(self, job: Dict[str, Any], user_profile: UserProfile, max_retries: int = 2) -> JobEvaluationResult:
        """
        Evaluate a single job with retry logic.
        
        Args:
            job: Job dictionary with title, company, description, etc.
            user_profile: User qualification profile
            max_retries: Maximum number of retry attempts
            
        Returns:
            JobEvaluationResult with success status and qualification result
        """
        job_id = job.get('id', '')
        job_title = job.get('title', 'Unknown')
        
        logger.info(f"🔍 Starting job evaluation for: {job_title} (ID: {job_id})")
        
        for attempt in range(max_retries + 1):
            try:
                # Create analysis request
                request = AnalysisRequest(
                    job_title=job.get('title', ''),
                    company=job.get('company', ''),
                    job_description=job.get('description', ''),
                    user_profile=user_profile,
                    ai_settings=self.ai_settings
                )
                
                # Analyze with retry logic
                start_time = time.time()
                analysis_response = self.analyze_job_qualification_with_retry(request, max_retries=0)  # No retries here since we handle it in the loop
                analysis_duration = time.time() - start_time
                
                # Update analysis duration
                analysis_response.analysis_duration = analysis_duration
                
                # Create qualification result
                qualification_result = self.create_qualification_result(
                    job_id=job_id,
                    job_title=job.get('title', ''),
                    company=job.get('company', ''),
                    job_url=job.get('job_url', ''),
                    analysis_response=analysis_response
                )
                
                logger.info(f"✅ Job evaluation successful for '{job_title}' (attempt {attempt + 1})")
                
                return JobEvaluationResult(
                    success=True,
                    qualification_result=qualification_result,
                    attempts=attempt + 1,
                    job_id=job_id,
                    job_title=job_title
                )
                
            except Exception as e:
                error_msg = f"Job evaluation failed on attempt {attempt + 1}: {e}"
                logger.warning(f"⚠️ {error_msg} for job: {job_title}")
                
                if attempt < max_retries:
                    # Wait before retry with exponential backoff
                    wait_time = (2 ** attempt) * 1  # 1s, 2s, 4s, etc.
                    logger.info(f"Retrying job '{job_title}' in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ All {max_retries + 1} attempts failed for job '{job_title}': {e}")
        
        # If we get here, all attempts failed
        return JobEvaluationResult(
            success=False,
            qualification_result=None,
            attempts=max_retries + 1,
            error_message=f"All {max_retries + 1} attempts failed: {str(e)}",
            job_id=job_id,
            job_title=job_title
        )
    
    def batch_analyze_jobs_with_retry(self, jobs: List[Dict[str, Any]], user_profile: UserProfile, max_retries: int = 2) -> Tuple[List[QualificationResult], List[JobEvaluationResult]]:
        """
        Analyze multiple jobs with robust retry logic.
        
        Args:
            jobs: List of job dictionaries with title, company, description, etc.
            user_profile: User qualification profile
            max_retries: Maximum number of retry attempts per job
            
        Returns:
            Tuple of (successful_results, all_evaluation_results)
            - successful_results: Only jobs that passed Gemini evaluation
            - all_evaluation_results: All evaluation results including failures
        """
        successful_results = []
        all_evaluation_results = []
        
        logger.info(f"🚀 Starting batch analysis of {len(jobs)} jobs with retry logic")
        
        for i, job in enumerate(jobs, 1):
            job_title = job.get('title', 'Unknown')
            logger.info(f"📋 Processing job {i}/{len(jobs)}: {job_title}")
            
            # Evaluate job with retry logic
            evaluation_result = self.evaluate_job_with_retry(job, user_profile, max_retries)
            all_evaluation_results.append(evaluation_result)
            
            if evaluation_result.success:
                successful_results.append(evaluation_result.qualification_result)
                logger.info(f"✅ Job {i}/{len(jobs)} successful: {job_title}")
            else:
                logger.warning(f"❌ Job {i}/{len(jobs)} failed after {evaluation_result.attempts} attempts: {job_title}")
                logger.debug(f"   Error: {evaluation_result.error_message}")
            
            # Add delay between requests to respect rate limits
            if i < len(jobs):
                time.sleep(1)  # 1 second delay between requests
        
        # Log summary
        successful_count = len(successful_results)
        failed_count = len(jobs) - successful_count
        
        logger.info(f"📊 Batch analysis completed:")
        logger.info(f"   ✅ Successful: {successful_count}/{len(jobs)} jobs")
        logger.info(f"   ❌ Failed: {failed_count}/{len(jobs)} jobs")
        
        if failed_count > 0:
            logger.warning(f"⚠️ {failed_count} jobs failed Gemini evaluation and will not be saved to database")
        
        return successful_results, all_evaluation_results
    
    # Legacy methods for backward compatibility
    
    def analyze_job_qualification(self, request: AnalysisRequest) -> AnalysisResponse:
        """
        Legacy method for job qualification analysis (maintains backward compatibility).
        
        Args:
            request: Analysis request containing job and user information
            
        Returns:
            Analysis response with qualification assessment
        """
        return self.analyze_job_qualification_with_retry(request, max_retries=2)
    
    def batch_analyze_jobs(
        self, 
        jobs: List[Dict[str, Any]], 
        user_profile: UserProfile
    ) -> List[QualificationResult]:
        """
        Legacy method for batch job analysis (maintains backward compatibility).
        
        Args:
            jobs: List of job dictionaries with title, company, description, etc.
            user_profile: User qualification profile
            
        Returns:
            List of QualificationResult objects (only successful evaluations)
        """
        successful_results, _ = self.batch_analyze_jobs_with_retry(jobs, user_profile, max_retries=2)
        return successful_results
    
    def _call_gemini_api(self, prompt: str) -> str:
        """
        Legacy method for Gemini API calls (maintains backward compatibility).
        
        Args:
            prompt: Analysis prompt
            
        Returns:
            API response text
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
        Legacy method for parsing AI responses (maintains backward compatibility).
        
        Args:
            response: Raw API response text
            
        Returns:
            Parsed JSON data
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