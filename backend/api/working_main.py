from fastapi import FastAPI
import sys
import os
from pathlib import Path

# Add the backend directory to sys.path so we can import from src
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

app = FastAPI(title="Job Qualification API", version="1.0.0")

# Import the simple scraper as a fallback
from .simple_scraper import SimpleScraper

# AI scoring system imports (commented out for performance)
# To enable AI scoring:
# 1. Uncomment the imports below
# 2. Set GEMINI_API_KEY environment variable
# 3. Uncomment the ai_analyzer initialization
# 4. Uncomment the **calculate_ai_score(job) lines in job results
# from src.ai.qualification_analyzer import QualificationAnalyzer, AnalysisRequest, AnalysisResponse
# from src.config.config_manager import AISettings

# Try to import advanced scrapers with better error handling
enhanced_scraper = None
api_scraper = None
simple_scraper = SimpleScraper()

# Initialize AI analyzer (commented out for performance)
# Uncomment this section and set GEMINI_API_KEY to enable AI scoring
# ai_analyzer = None
# try:
#     ai_settings = AISettings(
#         gemini_api_key=os.getenv('GEMINI_API_KEY', ''),
#         model_name='gemini-1.5-flash',
#         temperature=0.3,
#         max_tokens=2048
#     )
#     if ai_settings.gemini_api_key:
#         ai_analyzer = QualificationAnalyzer(ai_settings)
#         print("✅ AI analyzer initialized successfully")
#     else:
#         print("⚠️  No GEMINI_API_KEY found - AI scoring disabled")
# except Exception as e:
#     print(f"❌ Failed to initialize AI analyzer: {e}")
#     ai_analyzer = None

print("🔧 Attempting to import scrapers...")
print("✅ Simple scraper loaded as fallback")

# First, let's try the API scraper (no browser dependencies)
try:
    from src.scrapers.base_scraper import ScrapingConfig
    print("✅ ScrapingConfig imported successfully")
    
    from src.scrapers.linkedin_api_scraper import LinkedInAPIScraper
    print("✅ LinkedInAPIScraper imported successfully")
    
    # Create API scraper with proper configuration
    config = ScrapingConfig(
        site_name="LinkedIn",
        base_url="https://www.linkedin.com",
        search_url_template="https://www.linkedin.com/jobs/search/",
        max_jobs_per_session=50
    )
    api_scraper = LinkedInAPIScraper(config)
    print("✅ API scraper initialized successfully")
    
except Exception as e:
    print(f"❌ Failed to import API scraper: {e}")
    api_scraper = None

# Try to import enhanced scraper (has browser dependencies)
try:
    from src.scrapers.linkedin_scraper_enhanced import EnhancedLinkedInScraper
    print("✅ EnhancedLinkedInScraper imported successfully")
    
    # Create enhanced scraper with proper configuration
    config = ScrapingConfig(
        site_name="LinkedIn",
        base_url="https://www.linkedin.com",
        search_url_template="https://www.linkedin.com/jobs/search/",
        max_jobs_per_session=50
    )
    enhanced_scraper = EnhancedLinkedInScraper(config)
    print("✅ Enhanced scraper initialized successfully")
    
except Exception as e:
    print(f"❌ Failed to import enhanced scraper: {e}")
    enhanced_scraper = None

def choose_scraper(search_params):
    """Choose between Enhanced, API, and Simple scraper based on search complexity"""
    has_advanced_filters = (
        search_params.get("datePosted", "any") != "any" or
        search_params.get("experienceLevel", []) or
        search_params.get("workArrangement", []) or
        search_params.get("jobType", [])
    )
    
    if has_advanced_filters and enhanced_scraper:
        return enhanced_scraper, "WebDriver Mode"
    elif api_scraper:
        return api_scraper, "Fast API Mode"
    elif simple_scraper:
        return simple_scraper, "Simple Scraper Mode"
    else:
        return None, "No scraper available"

# AI scoring helper function (commented out for now)
# def calculate_ai_score(job, user_profile=None):
#     """
#     Calculate AI-powered job qualification score.
#     
#     Args:
#         job: Job object with title, company, description, etc.
#         user_profile: Optional user profile for personalized scoring
#         
#     Returns:
#         dict: Score and analysis details
#     """
#     if not ai_analyzer:
#         return {
#             "score": 75,
#             "reasoning": "AI scoring unavailable - using default score",
#             "key_skills": [],
#             "strengths": ["Position matches search criteria"], 
#             "concerns": [],
#             "confidence": 50
#         }
#     
#     try:
#         # Create analysis request
#         request = AnalysisRequest(
#             job_title=job.title,
#             company=job.company,
#             job_description=getattr(job, 'description', 'No description available'),
#             ai_settings=ai_analyzer.ai_settings,
#             user_profile=user_profile,
#             # Add basic profile data if available
#             skills=["Python", "JavaScript", "React"],  # TODO: Get from user profile
#             experience_level="Mid level",  # TODO: Get from user profile
#             years_experience=3  # TODO: Get from user profile
#         )
#         
#         # Analyze with AI
#         response = ai_analyzer.analyze_job_qualification_with_retry(request)
#         
#         return {
#             "score": response.qualification_score,
#             "reasoning": response.ai_reasoning,
#             "key_skills": response.key_skills_mentioned,
#             "strengths": response.matching_strengths,
#             "concerns": response.potential_concerns,
#             "confidence": response.confidence_score
#         }
#         
#     except Exception as e:
#         print(f"AI scoring failed: {e}")
#         return {
#             "score": 75,
#             "reasoning": f"AI scoring failed: {str(e)} - using default score",
#             "key_skills": [],
#             "strengths": ["Position matches search criteria"],
#             "concerns": ["Could not analyze with AI"],
#             "confidence": 50
#         }

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
        "scrapers": {
            "simple_scraper_available": simple_scraper is not None,
            "api_scraper_available": api_scraper is not None,
            "enhanced_scraper_available": enhanced_scraper is not None,
        },
        "timestamp": "2024-01-01T00:00:00Z"
    }

@app.post("/api/jobs/search")
async def search_jobs(search_params: dict):
    """Search for jobs using the available scrapers"""
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
        
        # Choose the appropriate scraper
        selected_scraper, strategy_method = choose_scraper(search_params)
        
        if not selected_scraper:
            # Fallback to mock data if no scrapers available
            print("⚠️  No scrapers available, using mock data")
            mock_results = [
                {
                    "id": "mock-1",
                    "job_title": f"{keywords} - Mock Result",
                    "company": "Mock Company",
                    "location": location,
                    "job_url": "https://linkedin.com/jobs/mock-1",
                    "score": 80,
                    "reasoning": f"Mock result for {keywords} in {location}",
                    "key_skills": ["Python", "JavaScript"],
                    "strengths": ["Mock data for testing"],
                    "concerns": ["Not real job data"],
                    "required_experience": "Mock experience",
                    "education_requirements": "Mock education",
                    "date_posted": "2024-01-15",
                    "salary_range": "Mock salary"
                }
            ]
            
            return {
                "success": True,
                "jobs_count": len(mock_results),
                "total_jobs": len(mock_results),
                "results": mock_results,
                "strategy_info": {
                    "method": "Mock Mode",
                    "estimated_time": "1 second",
                    "performance_impact": "None",
                    "reason": "Scrapers not available - using mock data"
                }
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
        
        print(f"🔍 Searching for jobs: {keywords} in {location} using {strategy_method}")
        
        # Use the selected scraper
        if strategy_method == "Simple Scraper Mode":
            # Use simple scraper (returns dict format)
            scraper_result = selected_scraper.scrape_jobs(scraper_params)
            
            if not scraper_result or not scraper_result.get("success", False):
                return {
                    "error": scraper_result.get("error_message", "Simple scraping failed") if scraper_result else "Scraping failed",
                    "success": False,
                    "requires_manual_intervention": True
                }
            
            # Convert simple scraper results to expected format
            results = []
            for job in scraper_result.get("jobs", []):
                results.append({
                    "id": job.get("id"),
                    "job_title": job.get("title"),
                    "company": job.get("company"),
                    "location": job.get("location"),
                    "job_url": job.get("linkedin_url"),
                    "score": 75,  # Hardcoded score - AI scoring available but commented out
                    # **calculate_ai_score(job),  # Uncomment to enable AI scoring
                    "reasoning": f"Found {job.get('title')} position at {job.get('company')}",
                    "key_skills": [],
                    "strengths": ["Position matches search criteria"],
                    "concerns": [],
                    "required_experience": job.get("experience_level", "Not specified"),
                    "education_requirements": "Not specified",
                    "date_posted": job.get("date_posted"),
                    "salary_range": f"${job.get('salary_min'):,} - ${job.get('salary_max'):,}" if job.get('salary_min') else "Not specified"
                })
        else:
            # Use advanced scrapers (return ScrapingResult objects)
            # Convert search parameters to the format expected by the API scraper
            keywords_list = [scraper_params["keywords"]] if isinstance(scraper_params["keywords"], str) else scraper_params["keywords"]
            location = scraper_params["location"]
            
            # Call the scraper with the correct method signature
            jobs_result = selected_scraper.scrape_jobs(
                keywords=keywords_list,
                location=location,
                **{k: v for k, v in scraper_params.items() if k not in ['keywords', 'location']}
            )
            
            if not jobs_result or not jobs_result.success:
                return {
                    "error": jobs_result.error_message if jobs_result else "Scraping failed",
                    "success": False,
                    "requires_manual_intervention": True
                }
            
            # Convert JobListing objects to the expected format
            results = []
            for job in jobs_result.jobs:
                results.append({
                    "id": getattr(job, 'id', f"job-{len(results) + 1}"),
                    "job_title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "job_url": job.linkedin_url or getattr(job, 'indeed_url', None) or getattr(job, 'glassdoor_url', None),
                    "score": 75,  # Hardcoded score - AI scoring available but commented out
                    # **calculate_ai_score(job),  # Uncomment to enable AI scoring
                    "reasoning": f"Found {job.title} position at {job.company}",
                    "key_skills": getattr(job, 'requirements', []) or [],
                    "strengths": ["Position matches search criteria"],
                    "concerns": [],
                    "required_experience": getattr(job, 'experience_level', None) or "Not specified",
                    "education_requirements": getattr(job, 'education_required', None) or "Not specified",
                    "date_posted": job.posted_date.isoformat() if hasattr(job, 'posted_date') and job.posted_date else None,
                    "salary_range": f"${job.salary_min:,} - ${job.salary_max:,}" if hasattr(job, 'salary_min') and job.salary_min else "Not specified"
                })
        
        return {
            "success": True,
            "jobs_count": len(results),
            "total_jobs": len(results),
            "results": results,
            "strategy_info": {
                "method": strategy_method,
                "estimated_time": "10-30 seconds" if strategy_method == "WebDriver Mode" else "2-5 seconds" if strategy_method == "Fast API Mode" else "3-8 seconds",
                "performance_impact": "Medium" if strategy_method == "WebDriver Mode" else "Low",
                "reason": f"Using {strategy_method} based on search complexity"
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
    """Jobs tracker endpoint"""
    return {
        "jobs": [],
        "total_count": 0,
        "status": "success",
        "message": "Tracker endpoint working"
    }

@app.get("/api/jobs/analytics")
async def jobs_analytics():
    """Jobs analytics endpoint"""
    return {
        "total_jobs_tracked": 0,
        "applications_submitted": 0,
        "status": "success",
        "message": "Analytics endpoint working"
    }