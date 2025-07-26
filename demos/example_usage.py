#!/usr/bin/env python3
"""
Example Usage Script for Job Qualification Analysis

This script demonstrates how to use the job qualification analysis system
with real job URLs from LinkedIn, Indeed, and other job sites.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from run_job_analysis import JobAnalysisRunner


def example_single_job_analysis():
    """Example of analyzing a single job."""
    print("🎯 Example: Single Job Analysis")
    print("=" * 50)
    
    # Example job URL (replace with real LinkedIn/Indeed URL)
    example_job_url = "https://www.linkedin.com/jobs/view/software-engineer-python"
    
    runner = JobAnalysisRunner()
    
    print(f"Analyzing: {example_job_url}")
    result = runner.analyze_single_job(example_job_url, save_to_sheets=False)
    
    if result:
        print(f"\n✅ Analysis complete!")
        print(f"Job: {result.job_title} at {result.company}")
        print(f"Score: {result.qualification_score}/100")
        print(f"Status: {result.qualification_status.value}")
    else:
        print("❌ Analysis failed")


def example_batch_analysis():
    """Example of analyzing multiple jobs."""
    print("\n🎯 Example: Batch Job Analysis")
    print("=" * 50)
    
    # Example job URLs (replace with real URLs)
    example_job_urls = [
        "https://www.linkedin.com/jobs/view/entry-level-software-engineer",
        "https://www.linkedin.com/jobs/view/python-developer",
        "https://www.linkedin.com/jobs/view/senior-software-engineer",
        "https://www.indeed.com/viewjob?jk=abc123",
        "https://www.glassdoor.com/Job/software-engineer-jobs-SRCH_KO0,17.htm"
    ]
    
    runner = JobAnalysisRunner()
    
    print(f"Analyzing {len(example_job_urls)} jobs...")
    results = runner.analyze_multiple_jobs(example_job_urls, save_to_sheets=False)
    
    print(f"\n✅ Batch analysis complete!")
    print(f"Successfully analyzed: {len(results)} jobs")


def example_with_real_urls():
    """Example with instructions for real URLs."""
    print("\n🎯 Example: Using Real Job URLs")
    print("=" * 50)
    
    print("To use this system with real job URLs:")
    print()
    print("1. Find job postings on LinkedIn, Indeed, or Glassdoor")
    print("2. Copy the job URL (e.g., https://www.linkedin.com/jobs/view/123456)")
    print("3. Run the analysis script:")
    print("   python run_job_analysis.py")
    print()
    print("4. Choose option 1 for single job or option 2 for multiple jobs")
    print("5. Paste your job URLs")
    print("6. Choose whether to save results to Google Sheets")
    print()
    print("Example job URLs you can test with:")
    print("- LinkedIn: https://www.linkedin.com/jobs/view/[job-id]")
    print("- Indeed: https://www.indeed.com/viewjob?jk=[job-key]")
    print("- Glassdoor: https://www.glassdoor.com/Job/[job-url]")
    print()
    print("The system will:")
    print("✅ Extract job information from the URL")
    print("✅ Analyze your qualifications against the job requirements")
    print("✅ Provide a 0-100 qualification score")
    print("✅ Give detailed reasoning and recommendations")
    print("✅ Save results to Google Sheets (if configured)")


def example_user_profile():
    """Example of viewing user profile."""
    print("\n👤 Example: Your Profile")
    print("=" * 50)
    
    runner = JobAnalysisRunner()
    runner.show_user_profile()
    
    print("\n💡 To update your profile:")
    print("1. Edit config/settings.json")
    print("2. Update the 'user_profile' section")
    print("3. Restart the system")


def main():
    """Main example function."""
    print("🎯 Job Qualification Analysis - Example Usage")
    print("=" * 60)
    
    while True:
        print("\n📋 EXAMPLE MENU")
        print("1. Single job analysis example")
        print("2. Batch analysis example")
        print("3. Real URL usage instructions")
        print("4. View your profile")
        print("5. Exit")
        
        choice = input("\nChoose example (1-5): ").strip()
        
        if choice == "1":
            example_single_job_analysis()
        elif choice == "2":
            example_batch_analysis()
        elif choice == "3":
            example_with_real_urls()
        elif choice == "4":
            example_user_profile()
        elif choice == "5":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-5.")


if __name__ == "__main__":
    main() 