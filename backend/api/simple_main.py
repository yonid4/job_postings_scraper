from fastapi import FastAPI
import os

app = FastAPI(title="Job Qualification API", version="1.0.0")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Backend API is running"}

@app.get("/")
async def root():
    return {"message": "Job Qualification API v1.0.0"}

@app.get("/api/debug/test")
async def debug_test():
    """Debug endpoint for testing connectivity"""
    return {
        "status": "ok",
        "message": "Debug endpoint working",
        "timestamp": "2024-01-01T00:00:00Z"
    }

@app.post("/api/jobs/search")
async def search_jobs(search_params: dict):
    """Search for jobs using mock data for now"""
    try:
        # Extract search parameters
        keywords = search_params.get("keywords", "")
        location = search_params.get("location", "")
        job_limit = search_params.get("jobLimit", 25)
        
        if not keywords or not location:
            return {
                "error": "Keywords and location are required",
                "success": False
            }
        
        # Return mock data for now - will be replaced with real scraper
        mock_results = [
            {
                "id": "1",
                "job_title": f"Software Engineer - {keywords}",
                "company": "TechCorp",
                "location": location,
                "job_url": "https://linkedin.com/jobs/1",
                "score": 85,
                "reasoning": f"Found {keywords} position in {location}",
                "key_skills": ["Python", "JavaScript", "React"],
                "strengths": ["Matches search criteria", "Good location"],
                "concerns": [],
                "required_experience": "3+ years",
                "education_requirements": "Bachelor's degree",
                "date_posted": "2024-01-15",
                "salary_range": "$80,000 - $120,000"
            },
            {
                "id": "2",
                "job_title": f"Senior {keywords}",
                "company": "StartupXYZ",
                "location": location,
                "job_url": "https://linkedin.com/jobs/2",
                "score": 78,
                "reasoning": f"Senior level {keywords} position",
                "key_skills": ["Python", "AWS", "Docker"],
                "strengths": ["Senior level", "Modern tech stack"],
                "concerns": ["May require more experience"],
                "required_experience": "5+ years",
                "education_requirements": "Bachelor's degree preferred",
                "date_posted": "2024-01-14",
                "salary_range": "$100,000 - $150,000"
            }
        ]
        
        return {
            "success": True,
            "jobs_count": len(mock_results),
            "total_jobs": len(mock_results),
            "results": mock_results,
            "strategy_info": {
                "method": "Mock Data Mode",
                "estimated_time": "1 second",
                "performance_impact": "None",
                "reason": "Using mock data for testing - real scrapers will be integrated later"
            }
        }
        
    except Exception as e:
        return {
            "error": f"Search failed: {str(e)}",
            "success": False
        }

@app.get("/api/jobs/tracker")
async def jobs_tracker():
    """Jobs tracker endpoint - returns sample data for testing"""
    sample_jobs = [
        {
            "id": "1",
            "title": "Senior Software Engineer",
            "company": "TechCorp",
            "location": "San Francisco, CA",
            "salary_range": "$120,000 - $160,000",
            "description": "We are looking for a senior software engineer to join our team...",
            "linkedin_url": "https://linkedin.com/jobs/1",
            "date_found": "2024-01-15",
            "qualification_score": 85,
            "gemini_score": 85,
            "gemini_evaluation": "Strong match - your experience aligns well with requirements"
        }
    ]
    
    return {
        "jobs": sample_jobs,
        "total_count": len(sample_jobs),
        "status": "success",
        "message": "Sample jobs loaded for testing"
    }

@app.get("/api/jobs/analytics")
async def jobs_analytics():
    """Jobs analytics endpoint - returns sample analytics data"""
    return {
        "total_jobs_tracked": 3,
        "applications_submitted": 1,
        "response_rate": 33.3,
        "responses_received": 1,
        "interviews_scheduled": 0,
        "offers_received": 0,
        "avg_qualification_score": 85,
        "jobs_this_week": 2,
        "status": "success",
        "message": "Sample analytics loaded for testing"
    }