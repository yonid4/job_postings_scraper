from fastapi import FastAPI
import sys
import os

# Add the backend directory to sys.path so we can import from src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from src.ai.qualification_analyzer import QualificationAnalyzer, AnalysisRequest
    from src.config.config_manager import AISettings, UserProfile
    from src.scrapers.linkedin_scraper_enhanced import LinkedInScraperEnhanced
except ImportError:
    # Fallback if import fails
    QualificationAnalyzer = None
    AnalysisRequest = None
    AISettings = None
    UserProfile = None
    LinkedInScraperEnhanced = None

app = FastAPI(title="Job Qualification API", version="1.0.0")

# Initialize analyzer if available
try:
    # Create basic AI settings for the analyzer
    ai_settings = AISettings(api_key=os.getenv("GEMINI_API_KEY", "dummy"), model="gemini-2.0-flash-lite") if AISettings else None
    analyzer = QualificationAnalyzer(ai_settings) if QualificationAnalyzer and ai_settings else None
except:
    analyzer = None

# Initialize scraper
scraper = LinkedInScraperEnhanced() if LinkedInScraperEnhanced else None

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Backend API is running"}

@app.get("/")
async def root():
    return {"message": "Job Qualification API v1.0.0"}

@app.post("/api/jobs/analyze")
async def analyze_job(job_data: dict):
    """Wrapper around existing analyze_job_qualification function"""
    if not analyzer or not AnalysisRequest or not UserProfile:
        return {"error": "Analyzer not available"}
    
    try:
        # Create a basic user profile (simplified for API)
        user_profile = UserProfile(
            years_of_experience=job_data.get("experience_years", 0),
            has_college_degree=job_data.get("has_degree", True),
            field_of_study=job_data.get("field_of_study", "Computer Science"),
            experience_level="entry",
            additional_skills=job_data.get("skills", []),
            preferred_locations=job_data.get("locations", [])
        )
        
        # Create analysis request
        request = AnalysisRequest(
            job_title=job_data.get("title", "Software Engineer"),
            company=job_data.get("company", "Unknown Company"),
            job_description=job_data.get("description", ""),
            user_profile=user_profile,
            ai_settings=analyzer.ai_settings
        )
        
        # Call existing function - NO CHANGES TO LOGIC
        result = analyzer.analyze_job_qualification(request)
        
        # Convert result to dictionary for JSON response
        return {
            "qualification_score": result.qualification_score,
            "qualification_status": result.qualification_status.value,
            "ai_reasoning": result.ai_reasoning,
            "required_experience": result.required_experience,
            "education_requirements": result.education_requirements,
            "key_skills_mentioned": result.key_skills_mentioned,
            "matching_strengths": result.matching_strengths,
            "potential_concerns": result.potential_concerns,
            "analysis_duration": result.analysis_duration
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/scraping/linkedin")
async def scrape_linkedin(search_params: dict):
    """Wrapper around existing LinkedIn scraper"""
    if not scraper:
        return {"error": "Scraper not available"}
    
    try:
        # Call existing method - EXACT SAME LOGIC
        jobs = scraper.scrape_jobs(search_params)
        return {"jobs": jobs, "count": len(jobs) if jobs else 0}
    except Exception as e:
        return {"error": str(e)}

# Additional endpoints for frontend compatibility
@app.get("/api/debug/test")
async def debug_test():
    """Debug endpoint for testing connectivity"""
    return {
        "status": "ok",
        "message": "Debug endpoint working",
        "analyzer_available": analyzer is not None,
        "scraper_available": scraper is not None,
        "timestamp": "2024-01-01T00:00:00Z"
    }

@app.post("/api/jobs/search")
async def search_jobs(search_params: dict):
    """Search for jobs using the available scrapers"""
    if not scraper:
        return {"error": "Scraper not available", "success": False}
    
    try:
        # Extract search parameters
        keywords = search_params.get("keywords", "")
        location = search_params.get("location", "")
        website = search_params.get("website", "linkedin")
        job_limit = search_params.get("jobLimit", 25)
        
        if not keywords or not location:
            return {
                "error": "Keywords and location are required",
                "success": False
            }
        
        # Prepare search parameters for scraper
        scraper_params = {
            "keywords": keywords,
            "location": location,
            "job_limit": job_limit,
            "date_posted": search_params.get("datePosted", "any"),
            "experience_level": search_params.get("experienceLevel", []),
            "work_arrangement": search_params.get("workArrangement", []),
            "job_type": search_params.get("jobType", [])
        }
        
        # Use the LinkedIn scraper to get real jobs
        print(f"🔍 Searching for jobs: {keywords} in {location}")
        jobs_result = scraper.scrape_jobs(scraper_params)
        
        if not jobs_result or not jobs_result.success:
            return {
                "error": jobs_result.error_message if jobs_result else "Scraping failed",
                "success": False,
                "requires_manual_intervention": True
            }
        
        # Convert JobListing objects to the expected format
        results = []
        for job in jobs_result.jobs:
            # Basic job analysis score (simplified for now)
            score = 75  # Default score, could be enhanced with AI analysis
            
            results.append({
                "id": job.id,
                "job_title": job.title,
                "company": job.company,
                "location": job.location,
                "job_url": job.linkedin_url or job.indeed_url or job.glassdoor_url,
                "score": score,
                "reasoning": f"Found {job.title} position at {job.company}",
                "key_skills": [],  # Could be extracted from description
                "strengths": ["Position matches search criteria"],
                "concerns": [],
                "required_experience": job.experience_required or "Not specified",
                "education_requirements": job.education_required or "Not specified",
                "date_posted": job.date_posted.isoformat() if job.date_posted else None,
                "salary_range": f"${job.salary_min:,} - ${job.salary_max:,}" if job.salary_min and job.salary_max else "Not specified"
            })
        
        return {
            "success": True,
            "jobs_count": len(results),
            "total_jobs": len(results),
            "results": results,
            "strategy_info": {
                "method": "LinkedIn Scraper",
                "estimated_time": "10-30 seconds",
                "performance_impact": "Medium",
                "reason": "Using enhanced LinkedIn scraper with session management"
            }
        }
        
    except Exception as e:
        print(f"❌ Search error: {str(e)}")
        return {
            "error": f"Search failed: {str(e)}",
            "success": False,
            "requires_manual_intervention": True
        }

@app.get("/api/jobs/tracker")
async def jobs_tracker():
    """Jobs tracker endpoint - returns sample data for testing"""
    # For now, keep sample data for tracker since it's a different feature
    # In the future, this could load saved jobs from database
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
        },
        {
            "id": "2", 
            "title": "Frontend Developer",
            "company": "WebSolutions",
            "location": "Remote",
            "salary_range": "$90,000 - $130,000",
            "description": "Join our frontend team working with React and TypeScript...",
            "linkedin_url": "https://linkedin.com/jobs/2",
            "date_found": "2024-01-14",
            "qualification_score": 92,
            "gemini_score": 92,
            "gemini_evaluation": "Excellent match - perfect fit for your skills"
        },
        {
            "id": "3",
            "title": "Full Stack Developer", 
            "company": "StartupXYZ",
            "location": "New York, NY",
            "salary_range": "$100,000 - $140,000",
            "description": "Looking for a full stack developer with Python and React experience...",
            "linkedin_url": "https://linkedin.com/jobs/3",
            "date_found": "2024-01-13",
            "qualification_score": 78,
            "gemini_score": 78,
            "gemini_evaluation": "Good match - some skills overlap, room for growth"
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
