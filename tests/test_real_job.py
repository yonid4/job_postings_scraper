#!/usr/bin/env python3
"""
Test script for real job analysis with proper URLs.

This script demonstrates the difference between search URLs and specific job URLs,
and shows how to use the system correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from run_job_analysis import JobAnalysisRunner


def test_with_proper_urls():
    """Test with proper job URLs (not search URLs)."""
    print("🎯 Understanding Job URLs")
    print("=" * 50)
    
    print("❌ SEARCH URLS (These extract MULTIPLE jobs):")
    search_urls = [
        "https://www.linkedin.com/jobs/search/?currentJobId=4110605130&keywords=python",
        "https://www.linkedin.com/jobs/search/?keywords=software+engineer",
        "https://www.indeed.com/jobs?q=python+developer",
        "https://www.glassdoor.com/Job/software-engineer-jobs.htm"
    ]
    
    for url in search_urls:
        print(f"   ❌ {url}")
    
    print("\n✅ INDIVIDUAL JOB URLS (These extract ONE job):")
    individual_job_urls = [
        "https://www.linkedin.com/jobs/view/4110605130",
        "https://www.linkedin.com/jobs/view/software-engineer-at-google-123456",
        "https://www.indeed.com/viewjob?jk=abc123def456",
        "https://www.glassdoor.com/Job/software-engineer-jobs-SRCH_IL.0,17_KO18,31.htm"
    ]
    
    for url in individual_job_urls:
        print(f"   ✅ {url}")
    
    print("\n💡 HOW TO GET PROPER JOB URLS:")
    print("1. Go to LinkedIn/Indeed/Glassdoor")
    print("2. Search for jobs")
    print("3. Click on a specific job posting (not the search page)")
    print("4. Copy the URL from the address bar")
    print("5. Look for these patterns:")
    print("   - LinkedIn: '/jobs/view/' followed by job ID")
    print("   - Indeed: '/viewjob?jk=' followed by job key")
    print("   - Glassdoor: '/Job/' followed by job details")
    
    print("\n🔍 EXAMPLE:")
    print("   Search URL: https://www.linkedin.com/jobs/search/?keywords=python")
    print("   Job URL:    https://www.linkedin.com/jobs/view/4110605130")
    
    print("\n🚀 NEW FEATURE: Search Page Extraction")
    print("The system can now extract multiple jobs from search pages!")
    print("Just provide a LinkedIn search URL and it will extract all visible jobs.")
    
    return individual_job_urls


def test_search_page_extraction():
    """Test extracting multiple jobs from LinkedIn search pages."""
    print("\n🎯 Testing Search Page Extraction")
    print("=" * 50)
    
    print("🚀 NEW FEATURE: Extract Multiple Jobs from Search Pages")
    print("Instead of providing individual job URLs, you can now provide")
    print("LinkedIn search URLs and the system will extract all visible jobs!")
    print()
    
    # Example LinkedIn search URL
    search_url = "https://www.linkedin.com/jobs/search/?currentJobId=4110605130&f_E=2%2C3&f_JT=F&f_PP=102277331%2C104119503%2C106233382%2C104116203%2C101876708%2C102250832%2C100075706%2C105786169&f_SB2=3&f_TPR=r604800&f_WT=1%2C3&geoId=103644278&keywords=entry%20level%20software%20engineer&origin=JOB_SEARCH_PAGE_JOB_FILTER&refresh=true&sortBy=R"
    
    print(f"📋 Testing with search URL:")
    print(f"   {search_url}")
    print()
    
    print("⚠️  This will extract multiple jobs from the search page.")
    print("   The system will analyze each job and provide qualification scores.")
    print()
    
    proceed = input("Do you want to test search page extraction? (y/n): ").strip().lower()
    
    if proceed != 'y':
        print("⏭️  Skipping search page extraction test")
        return
    
    try:
        from src.utils.job_link_processor import JobLinkProcessor
        from src.ai.qualification_analyzer import QualificationAnalyzer, AnalysisRequest
        from src.config.config_manager import ConfigurationManager
        
        print("🔍 Processing search page...")
        
        # Initialize components
        processor = JobLinkProcessor()
        config_manager = ConfigurationManager()
        user_profile = config_manager.get_user_profile()
        ai_settings = config_manager.get_ai_settings()
        
        # Process the search URL
        job_links = processor.process_job_links([search_url])
        
        print(f"✅ Extracted {len(job_links)} jobs from search page")
        
        if not job_links:
            print("❌ No jobs extracted from search page")
            return
        
        # Show extracted jobs
        print("\n📊 Extracted Jobs:")
        for i, job_link in enumerate(job_links[:5], 1):  # Show first 5
            print(f"   {i}. {job_link.title or 'Unknown Title'}")
            print(f"      Company: {job_link.company or 'Unknown Company'}")
            print(f"      Location: {job_link.location or 'Unknown Location'}")
            if job_link.description:
                desc_preview = job_link.description[:80] + "..." if len(job_link.description) > 80 else job_link.description
                print(f"      Description: {desc_preview}")
            print()
        
        if len(job_links) > 5:
            print(f"   ... and {len(job_links) - 5} more jobs")
        
        # Ask if user wants to analyze the jobs
        analyze = input(f"\nDo you want to analyze {len(job_links)} jobs with AI? (y/n): ").strip().lower()
        
        if analyze == 'y':
            print("\n🤖 Running AI analysis on extracted jobs...")
            
            # Initialize analyzer
            if not ai_settings.api_key:
                print("⚠️  No Gemini API key - using custom rule-based analysis")
                from examples.custom_analyzer_example import CustomRuleBasedAnalyzer
                analyzer = CustomRuleBasedAnalyzer(ai_settings)
            else:
                analyzer = QualificationAnalyzer(ai_settings)
            
            # Analyze first 3 jobs to avoid overwhelming
            jobs_to_analyze = job_links[:3]
            
            for i, job_link in enumerate(jobs_to_analyze, 1):
                if job_link.error or not job_link.title:
                    continue
                
                print(f"\n🎯 Analyzing Job {i}: {job_link.title}")
                
                # Create analysis request
                request = AnalysisRequest(
                    job_title=job_link.title,
                    company=job_link.company or "Unknown Company",
                    job_description=job_link.description or "No description available",
                    user_profile=user_profile,
                    ai_settings=ai_settings
                )
                
                try:
                    # Run analysis
                    analysis_response = analyzer.analyze_job_qualification(request)
                    
                    # Display results
                    print(f"   📊 Score: {analysis_response.qualification_score}/100")
                    print(f"   🏷️  Status: {analysis_response.qualification_status.value}")
                    print(f"   💭 Reasoning: {analysis_response.ai_reasoning[:100]}...")
                    
                except Exception as e:
                    print(f"   ❌ Analysis failed: {e}")
        
        print("\n✅ Search page extraction test completed!")
        
    except Exception as e:
        print(f"❌ Error during search page extraction: {e}")


def test_single_job_analysis():
    """Test single job analysis with a proper URL."""
    print("\n🎯 Testing Single Job Analysis")
    print("=" * 50)
    
    print("⚠️  IMPORTANT: You need a SPECIFIC job URL, not a search URL!")
    print()
    print("❌ This WON'T work (search URL):")
    print("   https://www.linkedin.com/jobs/search/?currentJobId=4110605130&...")
    print()
    print("✅ This WILL work (specific job URL):")
    print("   https://www.linkedin.com/jobs/view/4110605130")
    print()
    
    # Ask user for a proper job URL
    print("📝 To test the system:")
    print("1. Go to LinkedIn/Indeed")
    print("2. Find a specific job posting")
    print("3. Click on the job (not the search page)")
    print("4. Copy the URL from your browser")
    print("5. Paste it here")
    print()
    
    job_url = input("Enter a specific job URL (or press Enter to skip): ").strip()
    
    if not job_url:
        print("⏭️  Skipping job analysis test")
        return
    
    # Validate the URL
    if "jobs/search" in job_url or "jobs?q=" in job_url:
        print("❌ This is a search URL, not a specific job URL!")
        print("Please get the URL from a specific job posting page.")
        return
    
    print(f"\n📋 Testing with: {job_url}")
    
    runner = JobAnalysisRunner()
    
    # Show user profile first
    print("\n👤 Your Current Profile:")
    runner.show_user_profile()
    
    # Test the analysis
    print(f"\n📋 Analyzing job...")
    result = runner.analyze_single_job(job_url, save_to_sheets=False)
    
    if result:
        print(f"\n✅ Analysis successful!")
        print(f"Job: {result.job_title}")
        print(f"Company: {result.company}")
        print(f"Score: {result.qualification_score}/100")
        print(f"Status: {result.qualification_status.value}")
    else:
        print(f"\n❌ Analysis failed - check the URL format")


def test_google_sheets():
    """Test Google Sheets connection."""
    print("\n🧪 Testing Google Sheets Connection")
    print("=" * 50)
    
    runner = JobAnalysisRunner()
    success = runner.test_google_sheets()
    
    if success:
        print("✅ Google Sheets is working! You can save results.")
    else:
        print("❌ Google Sheets not configured. Results will only be displayed.")


def main():
    """Main test function."""
    print("🎯 Job Qualification Analysis - Testing")
    print("=" * 60)
    
    while True:
        print("\n📋 TEST MENU")
        print("1. Show proper vs search URLs")
        print("2. Test search page extraction (NEW!)")
        print("3. Test single job analysis")
        print("4. Test Google Sheets connection")
        print("5. View your profile")
        print("6. Exit")
        
        choice = input("\nChoose test (1-6): ").strip()
        
        if choice == "1":
            test_with_proper_urls()
        elif choice == "2":
            test_search_page_extraction()
        elif choice == "3":
            test_single_job_analysis()
        elif choice == "4":
            test_google_sheets()
        elif choice == "5":
            runner = JobAnalysisRunner()
            runner.show_user_profile()
        elif choice == "6":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1-6.")


if __name__ == "__main__":
    main() 