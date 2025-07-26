#!/usr/bin/env python3
"""
Test script for LinkedIn search page extraction.

This script demonstrates how the enhanced job link processor can extract
multiple jobs from LinkedIn search pages without needing individual job URLs.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.job_link_processor import JobLinkProcessor
from src.ai.qualification_analyzer import QualificationAnalyzer, AnalysisRequest
from src.config.config_manager import ConfigurationManager
from src.data.models import JobListing


def test_linkedin_search_extraction():
    """Test extracting jobs from LinkedIn search pages."""
    print("🎯 Testing LinkedIn Search Page Extraction")
    print("=" * 60)
    
    # Example LinkedIn search URLs (these are search pages, not individual jobs)
    search_urls = [
        "https://www.linkedin.com/jobs/search/?currentJobId=4271057209&geoId=103644278&keywords=entry%20level%20software%20engineer&origin=JOB_SEARCH_PAGE_LOCATION_AUTOCOMPLETE&refresh=true&start=25"
    ]
    
    print("📋 Test Search URLs:")
    for i, url in enumerate(search_urls, 1):
        print(f"   {i}. {url}")
    print()
    
    # Initialize the processor
    processor = JobLinkProcessor()
    
    print("🔍 Processing search pages...")
    print("Note: This will extract multiple jobs from each search page")
    print()
    
    for i, search_url in enumerate(search_urls, 1):
        print(f"📊 Processing Search Page {i}:")
        print(f"URL: {search_url[:100]}...")
        
        try:
            # Process the search URL
            job_links = processor.process_job_links([search_url])
            
            print(f"✅ Extracted {len(job_links)} jobs from search page")
            
            # Display extracted jobs
            for j, job_link in enumerate(job_links[:5], 1):  # Show first 5 jobs
                print(f"   {j}. {job_link.title or 'Unknown Title'}")
                print(f"      Company: {job_link.company or 'Unknown Company'}")
                print(f"      Location: {job_link.location or 'Unknown Location'}")
                if job_link.description:
                    desc_preview = job_link.description[:100] + "..." if len(job_link.description) > 100 else job_link.description
                    print(f"      Description: {desc_preview}")
                print()
            
            if len(job_links) > 5:
                print(f"   ... and {len(job_links) - 5} more jobs")
            
            # Convert to JobListing objects
            job_listings = processor.create_job_listings(job_links)
            print(f"📝 Created {len(job_listings)} JobListing objects")
            
        except Exception as e:
            print(f"❌ Error processing search page: {e}")
        
        print("-" * 60)
    
    return job_links


def test_ai_analysis_on_extracted_jobs(job_links):
    """Test AI analysis on the extracted jobs."""
    print("\n🤖 Testing AI Analysis on Extracted Jobs")
    print("=" * 60)
    
    if not job_links:
        print("❌ No jobs extracted, skipping AI analysis")
        return
    
    # Get configuration
    config_manager = ConfigurationManager()
    user_profile = config_manager.get_user_profile()
    ai_settings = config_manager.get_ai_settings()
    
    # Initialize analyzer
    if not ai_settings.api_key:
        print("⚠️  No Gemini API key - using custom rule-based analysis")
        from examples.custom_analyzer_example import CustomRuleBasedAnalyzer
        analyzer = CustomRuleBasedAnalyzer(ai_settings)
    else:
        analyzer = QualificationAnalyzer(ai_settings)
    
    # Analyze first few jobs
    jobs_to_analyze = job_links[:3]  # Analyze first 3 jobs
    
    print(f"📊 Analyzing {len(jobs_to_analyze)} extracted jobs...")
    print()
    
    for i, job_link in enumerate(jobs_to_analyze, 1):
        if job_link.error or not job_link.title:
            print(f"⏭️  Skipping job {i} (no valid data)")
            continue
        
        print(f"🎯 Job {i}: {job_link.title}")
        print(f"   Company: {job_link.company}")
        print(f"   Location: {job_link.location}")
        
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
            print("   🤖 Running AI analysis...")
            analysis_response = analyzer.analyze_job_qualification(request)
            
            # Display results
            print(f"   📊 Score: {analysis_response.qualification_score}/100")
            print(f"   🏷️  Status: {analysis_response.qualification_status.value}")
            print(f"   💭 Reasoning: {analysis_response.ai_reasoning[:100]}...")
            
            if analysis_response.matching_strengths:
                print(f"   ✅ Strengths: {', '.join(analysis_response.matching_strengths[:2])}")
            
            if analysis_response.potential_concerns:
                print(f"   ⚠️  Concerns: {', '.join(analysis_response.potential_concerns[:2])}")
            
        except Exception as e:
            print(f"   ❌ Analysis failed: {e}")
        
        print()


def test_url_validation():
    """Test URL validation and categorization."""
    print("\n🔍 Testing URL Validation")
    print("=" * 60)
    
    test_urls = [
        # Valid search URLs
        "https://www.linkedin.com/jobs/search/?keywords=python",
        "https://www.linkedin.com/jobs/search/?currentJobId=4110605130&keywords=software",
        
        # Valid individual job URLs
        "https://www.linkedin.com/jobs/view/4110605130",
        "https://www.indeed.com/viewjob?jk=abc123def456",
        
        # Invalid URLs
        "not-a-url",
        "https://invalid-site.com/jobs",
        
        # Unsupported sites
        "https://random-site.com/jobs",
        "https://github.com/jobs"
    ]
    
    processor = JobLinkProcessor()
    validation_results = processor.validate_job_links(test_urls)
    
    print("📋 Validation Results:")
    print(f"   ✅ Valid URLs: {len(validation_results['valid'])}")
    for url in validation_results['valid']:
        print(f"      - {url}")
    
    print(f"\n   ❌ Invalid URLs: {len(validation_results['invalid'])}")
    for url in validation_results['invalid']:
        print(f"      - {url}")
    
    print(f"\n   ⚠️  Unsupported URLs: {len(validation_results['unsupported'])}")
    for url in validation_results['unsupported']:
        print(f"      - {url}")


def main():
    """Main test function."""
    print("🎯 LinkedIn Search Page Extraction Test")
    print("=" * 60)
    
    print("This test demonstrates:")
    print("1. Extracting multiple jobs from LinkedIn search pages")
    print("2. Running AI analysis on extracted jobs")
    print("3. URL validation and categorization")
    print()
    
    # Test URL validation first
    test_url_validation()
    
    # Test search extraction
    job_links = test_linkedin_search_extraction()
    
    # Test AI analysis
    test_ai_analysis_on_extracted_jobs(job_links)
    
    print("\n✅ Test completed!")
    print("\n💡 Key Benefits:")
    print("• Extract multiple jobs from a single search URL")
    print("• No need to manually collect individual job URLs")
    print("• Batch processing for efficiency")
    print("• AI analysis on all extracted jobs")


if __name__ == "__main__":
    main() 