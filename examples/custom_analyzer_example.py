"""
Example of customizing the AI qualification analyzer.

This file demonstrates how to implement your own analysis logic
instead of relying on the default AI-based approach.
"""

from src.ai.qualification_analyzer import QualificationAnalyzer, AnalysisRequest, AnalysisResponse
from src.config.config_manager import UserProfile, AISettings
from src.data.models import QualificationStatus
import re
import time


class CustomRuleBasedAnalyzer(QualificationAnalyzer):
    """
    Custom analyzer that uses rule-based scoring instead of AI.
    
    This example shows how to implement your own qualification analysis
    using keyword matching, experience scoring, and custom rules.
    """
    
    def analyze_job_qualification(self, request: AnalysisRequest) -> AnalysisResponse:
        """
        Override the default AI analysis with custom rule-based logic.
        """
        start_time = time.time()
        
        try:
            # Use custom analysis logic instead of AI
            score = self._calculate_rule_based_score(request)
            reasoning = self._generate_rule_based_reasoning(request, score)
            
            # Extract information using regex patterns
            required_experience = self._extract_experience_requirements(request.job_description)
            education_requirements = self._extract_education_requirements(request.job_description)
            key_skills = self._extract_skills(request.job_description)
            matching_strengths = self._find_matching_strengths(request)
            potential_concerns = self._identify_concerns(request)
            
            analysis_duration = time.time() - start_time
            
            return AnalysisResponse(
                qualification_score=score,
                qualification_status=self._score_to_status(score),
                ai_reasoning=reasoning,
                required_experience=required_experience,
                education_requirements=education_requirements,
                key_skills_mentioned=key_skills,
                matching_strengths=matching_strengths,
                potential_concerns=potential_concerns,
                ai_model_used="custom_rule_based",
                analysis_duration=analysis_duration
            )
            
        except Exception as e:
            # Return default response for failed analysis
            return AnalysisResponse(
                qualification_score=0,
                qualification_status=QualificationStatus.NOT_QUALIFIED,
                ai_reasoning=f"Custom analysis failed: {str(e)}",
                required_experience="",
                education_requirements="",
                key_skills_mentioned=[],
                matching_strengths=[],
                potential_concerns=[f"Analysis error: {str(e)}"],
                ai_model_used="custom_rule_based",
                analysis_duration=time.time() - start_time
            )
    
    def _calculate_rule_based_score(self, request: AnalysisRequest) -> int:
        """
        Calculate qualification score using custom rules.
        """
        score = 0
        job_desc_lower = request.job_description.lower()
        user_profile = request.user_profile
        
        # Experience scoring (0-30 points)
        experience_score = self._score_experience(user_profile, job_desc_lower)
        score += experience_score
        
        # Education scoring (0-20 points)
        education_score = self._score_education(user_profile, job_desc_lower)
        score += education_score
        
        # Skills scoring (0-40 points)
        skills_score = self._score_skills(user_profile, job_desc_lower)
        score += skills_score
        
        # Location scoring (0-10 points)
        location_score = self._score_location(user_profile, job_desc_lower)
        score += location_score
        
        return min(100, max(0, score))
    
    def _score_experience(self, user_profile: UserProfile, job_desc: str) -> int:
        """Score experience match (0-30 points)."""
        score = 0
        
        # Extract required experience from job description
        experience_patterns = [
            r'(\d+)[\+]?\s*years?\s*of\s*experience',
            r'experience\s*level:\s*(\w+)',
            r'(\d+)[\+]?\s*years?\s*in\s*\w+',
        ]
        
        required_years = None
        for pattern in experience_patterns:
            match = re.search(pattern, job_desc, re.IGNORECASE)
            if match:
                try:
                    required_years = int(match.group(1))
                    break
                except ValueError:
                    continue
        
        if required_years:
            # Score based on experience match
            if user_profile.years_of_experience >= required_years:
                score = 30  # Perfect match
            elif user_profile.years_of_experience >= required_years * 0.8:
                score = 25  # Close match
            elif user_profile.years_of_experience >= required_years * 0.6:
                score = 20  # Somewhat close
            elif user_profile.years_of_experience >= required_years * 0.4:
                score = 15  # Partial match
            else:
                score = 5   # Minimal match
        else:
            # No specific experience requirement found
            score = 15  # Neutral score
        
        return score
    
    def _score_education(self, user_profile: UserProfile, job_desc: str) -> int:
        """Score education match (0-20 points)."""
        score = 0
        
        # Check if degree is required
        degree_required = any(term in job_desc.lower() for term in [
            'bachelor', 'master', 'phd', 'degree required', 'college degree'
        ])
        
        if degree_required:
            if user_profile.has_college_degree:
                score = 20  # Perfect match
            else:
                score = 5   # Missing required degree
        else:
            if user_profile.has_college_degree:
                score = 15  # Bonus for having degree
            else:
                score = 10  # Neutral score
        
        # Bonus for field of study match
        if user_profile.field_of_study and user_profile.field_of_study.lower() in job_desc.lower():
            score += 5
        
        return min(20, score)
    
    def _score_skills(self, user_profile: UserProfile, job_desc: str) -> int:
        """Score skills match (0-40 points)."""
        score = 0
        
        # Common tech skills to look for
        tech_skills = [
            'python', 'javascript', 'java', 'react', 'node.js', 'aws', 'docker',
            'kubernetes', 'sql', 'mongodb', 'postgresql', 'git', 'agile', 'scrum',
            'machine learning', 'ai', 'data science', 'devops', 'ci/cd'
        ]
        
        # Count matching skills
        matching_skills = 0
        for skill in tech_skills:
            if skill in job_desc.lower():
                if skill in [s.lower() for s in user_profile.additional_skills]:
                    matching_skills += 1
        
        # Score based on skill matches (max 40 points)
        if matching_skills >= 5:
            score = 40
        elif matching_skills >= 3:
            score = 30
        elif matching_skills >= 2:
            score = 20
        elif matching_skills >= 1:
            score = 10
        else:
            score = 0
        
        return score
    
    def _score_location(self, user_profile: UserProfile, job_desc: str) -> int:
        """Score location match (0-10 points)."""
        score = 0
        
        # Check if any preferred locations match
        for location in user_profile.preferred_locations:
            if location.lower() in job_desc.lower():
                score = 10
                break
        
        # Check for remote work preferences
        if 'remote' in job_desc.lower() and user_profile.remote_preference in ['remote', 'hybrid']:
            score += 5
        
        return min(10, score)
    
    def _generate_rule_based_reasoning(self, request: AnalysisRequest, score: int) -> str:
        """Generate reasoning based on the rule-based analysis."""
        reasoning_parts = []
        
        if score >= 80:
            reasoning_parts.append("Excellent match for this position.")
        elif score >= 60:
            reasoning_parts.append("Good match with some areas for improvement.")
        elif score >= 40:
            reasoning_parts.append("Moderate match with significant gaps.")
        else:
            reasoning_parts.append("Limited match for this position.")
        
        # Add specific feedback
        user_profile = request.user_profile
        job_desc_lower = request.job_description.lower()
        
        # Experience feedback
        if user_profile.years_of_experience < 2:
            reasoning_parts.append("Limited professional experience may be a concern.")
        
        # Skills feedback
        user_skills_lower = [s.lower() for s in user_profile.additional_skills]
        missing_skills = []
        for skill in ['python', 'javascript', 'react', 'aws']:
            if skill in job_desc_lower and skill not in user_skills_lower:
                missing_skills.append(skill)
        
        if missing_skills:
            reasoning_parts.append(f"Missing key skills: {', '.join(missing_skills)}.")
        
        return " ".join(reasoning_parts)
    
    def _extract_experience_requirements(self, job_description: str) -> str:
        """Extract experience requirements using regex."""
        patterns = [
            r'(\d+)[\+]?\s*years?\s*of\s*experience',
            r'experience\s*level:\s*(\w+)',
            r'(\d+)[\+]?\s*years?\s*in\s*\w+',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, job_description, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return "Experience requirements not specified"
    
    def _extract_education_requirements(self, job_description: str) -> str:
        """Extract education requirements using regex."""
        education_keywords = ['bachelor', 'master', 'phd', 'degree', 'college']
        
        for keyword in education_keywords:
            if keyword in job_description.lower():
                # Find the sentence containing the education requirement
                sentences = job_description.split('.')
                for sentence in sentences:
                    if keyword in sentence.lower():
                        return sentence.strip()
        
        return "Education requirements not specified"
    
    def _extract_skills(self, job_description: str) -> list:
        """Extract mentioned skills from job description."""
        skills = []
        tech_skills = [
            'python', 'javascript', 'java', 'react', 'node.js', 'aws', 'docker',
            'kubernetes', 'sql', 'mongodb', 'postgresql', 'git', 'agile', 'scrum',
            'machine learning', 'ai', 'data science', 'devops', 'ci/cd'
        ]
        
        job_desc_lower = job_description.lower()
        for skill in tech_skills:
            if skill in job_desc_lower:
                skills.append(skill.title())
        
        return skills
    
    def _find_matching_strengths(self, request: AnalysisRequest) -> list:
        """Find strengths that match the job requirements."""
        strengths = []
        user_profile = request.user_profile
        job_desc_lower = request.job_description.lower()
        
        # Check for matching skills
        for skill in user_profile.additional_skills:
            if skill.lower() in job_desc_lower:
                strengths.append(f"Strong {skill} experience")
        
        # Check for experience level match
        if user_profile.experience_level in job_desc_lower:
            strengths.append(f"Appropriate {user_profile.experience_level} level experience")
        
        # Check for education match
        if user_profile.has_college_degree and 'degree' in job_desc_lower:
            strengths.append("Meets education requirements")
        
        return strengths
    
    def _identify_concerns(self, request: AnalysisRequest) -> list:
        """Identify potential concerns for the candidate."""
        concerns = []
        user_profile = request.user_profile
        job_desc_lower = request.job_description.lower()
        
        # Check for missing skills
        user_skills_lower = [s.lower() for s in user_profile.additional_skills]
        missing_skills = []
        for skill in ['python', 'javascript', 'react', 'aws']:
            if skill in job_desc_lower and skill not in user_skills_lower:
                missing_skills.append(skill)
        
        if missing_skills:
            concerns.append(f"Missing key skills: {', '.join(missing_skills)}")
        
        # Check for experience gaps
        if user_profile.years_of_experience < 2:
            concerns.append("Limited professional experience")
        
        # Check for location mismatch
        location_match = False
        for location in user_profile.preferred_locations:
            if location.lower() in job_desc_lower:
                location_match = True
                break
        
        if not location_match and user_profile.preferred_locations:
            concerns.append("Location may not be ideal")
        
        return concerns


# Example usage
def main():
    """Example of using the custom analyzer."""
    
    # Create AI settings (API key not needed for custom analyzer)
    ai_settings = AISettings(api_key="dummy", model="custom")
    
    # Create custom analyzer
    analyzer = CustomRuleBasedAnalyzer(ai_settings)
    
    # Create sample user profile
    user_profile = UserProfile(
        years_of_experience=3,
        has_college_degree=True,
        field_of_study="Computer Science",
        experience_level="mid",
        additional_skills=["Python", "JavaScript", "React", "AWS"],
        preferred_locations=["San Francisco, CA", "New York, NY"]
    )
    
    # Create sample job request
    request = AnalysisRequest(
        job_title="Senior Software Engineer",
        company="Tech Startup",
        job_description="""
        We are seeking a Senior Software Engineer with 5+ years of experience.
        
        Requirements:
        - 5+ years of experience in software development
        - Strong proficiency in Python, JavaScript, and React
        - Experience with AWS and cloud platforms
        - Bachelor's degree in Computer Science or related field
        - Experience with microservices architecture
        
        Location: San Francisco, CA
        """,
        user_profile=user_profile,
        ai_settings=ai_settings
    )
    
    # Analyze the job
    result = analyzer.analyze_job_qualification(request)
    
    # Print results
    print(f"Job: {request.job_title} at {request.company}")
    print(f"Score: {result.qualification_score}/100")
    print(f"Status: {result.qualification_status.value}")
    print(f"Reasoning: {result.ai_reasoning}")
    print(f"Required Experience: {result.required_experience}")
    print(f"Education Requirements: {result.education_requirements}")
    print(f"Key Skills: {', '.join(result.key_skills_mentioned)}")
    print(f"Matching Strengths: {', '.join(result.matching_strengths)}")
    print(f"Potential Concerns: {', '.join(result.potential_concerns)}")


if __name__ == "__main__":
    main() 