#!/usr/bin/env python3
"""
Job Qualification Analysis Script

This script processes real job URLs and analyzes them using the AI qualification system.
It provides batch processing, progress tracking, and saves results to Google Sheets.
"""

import sys
import time
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from main import JobQualificationSystem
from src.data.models import QualificationResult, QualificationStatus, UserDecision
from src.utils.job_link_processor import JobLinkProcessor


class JobAnalysisRunner:
    """Main class for running job qualification analysis."""
    
    def __init__(self):
        """Initialize the job analysis runner."""
        print("🚀 Initializing Job Qualification Analysis System...")
        self.system = JobQualificationSystem()
        self.job_processor = JobLinkProcessor()
        
    def analyze_single_job(self, job_url: str, save_to_sheets: bool = True) -> QualificationResult:
        """
        Analyze a single job URL.
        
        Args:
            job_url: The job URL to analyze
            save_to_sheets: Whether to save results to Google Sheets
            
        Returns:
            QualificationResult object
        """
        print(f"\n📋 Analyzing: {job_url}")
        print("=" * 60)
        
        try:
            # Process the job link
            job_links = [job_url]
            job_link_infos = self.job_processor.process_job_links(job_links)
            
            if not job_link_infos:
                print("❌ Failed to extract job information from URL")
                return None
            
            job_link_info = job_link_infos[0]
            print(f"✅ Job extracted: {job_link_info.title} at {job_link_info.company}")
            
            # Convert JobLinkInfo to JobListing
            job_listings = self.job_processor.create_job_listings(job_link_infos)
            if not job_listings:
                print("❌ Failed to create job listing from extracted data")
                return None
            
            job_listing = job_listings[0]
            
            # Get user profile and AI settings
            user_profile = self.system.config_manager.get_user_profile()
            ai_settings = self.system.config_manager.get_ai_settings()
            
            # Create analysis request
            from src.ai.qualification_analyzer import AnalysisRequest
            request = AnalysisRequest(
                job_title=job_listing.title,
                company=job_listing.company,
                job_description=job_listing.description,
                user_profile=user_profile,
                ai_settings=ai_settings
            )
            
            # Perform AI analysis
            print("🤖 Running AI qualification analysis...")
            start_time = time.time()
            
            if not ai_settings.api_key:
                print("⚠️  No Gemini API key - using custom rule-based analysis")
                from examples.custom_analyzer_example import CustomRuleBasedAnalyzer
                analyzer = CustomRuleBasedAnalyzer(ai_settings)
            else:
                analyzer = self.system.qualification_analyzer
            
            analysis_response = analyzer.analyze_job_qualification(request)
            analysis_time = time.time() - start_time
            
            # Create qualification result
            qualification_result = analyzer.create_qualification_result(
                job_id=job_listing.id,
                job_title=job_listing.title,
                company=job_listing.company,
                job_url=job_listing.job_url,
                analysis_response=analysis_response
            )
            
            # Display results
            self._display_analysis_results(qualification_result, analysis_time)
            
            # Save to Google Sheets if requested
            if save_to_sheets and self.system.sheets_manager:
                print("\n💾 Saving to Google Sheets...")
                success = self.system.sheets_manager.write_qualification_result(qualification_result)
                if success:
                    print("✅ Saved to Google Sheets successfully!")
                else:
                    print("❌ Failed to save to Google Sheets")
            
            return qualification_result
            
        except Exception as e:
            print(f"❌ Error analyzing job: {e}")
            return None
    
    def analyze_multiple_jobs(self, job_urls: List[str], save_to_sheets: bool = True) -> List[QualificationResult]:
        """
        Analyze multiple job URLs in batch.
        
        Args:
            job_urls: List of job URLs to analyze
            save_to_sheets: Whether to save results to Google Sheets
            
        Returns:
            List of QualificationResult objects
        """
        print(f"\n🎯 Batch Analysis: {len(job_urls)} jobs")
        print("=" * 60)
        
        results = []
        successful = 0
        failed = 0
        
        for i, job_url in enumerate(job_urls, 1):
            print(f"\n📊 Progress: {i}/{len(job_urls)}")
            result = self.analyze_single_job(job_url, save_to_sheets)
            
            if result:
                results.append(result)
                successful += 1
            else:
                failed += 1
            
            # Add delay between requests to be respectful
            if i < len(job_urls):
                print("⏳ Waiting 2 seconds before next analysis...")
                time.sleep(2)
        
        # Display summary
        self._display_batch_summary(results, successful, failed)
        
        return results
    
    def _display_analysis_results(self, result: QualificationResult, analysis_time: float):
        """Display detailed analysis results."""
        print(f"\n📊 ANALYSIS RESULTS")
        print(f"Job: {result.job_title} at {result.company}")
        print(f"URL: {result.job_url}")
        print(f"Analysis Time: {analysis_time:.2f} seconds")
        print("-" * 40)
        
        # Score and status
        status_emoji = {
            QualificationStatus.HIGHLY_QUALIFIED: "🟢",
            QualificationStatus.QUALIFIED: "🟡", 
            QualificationStatus.SOMEWHAT_QUALIFIED: "🟠",
            QualificationStatus.NOT_QUALIFIED: "🔴"
        }
        
        emoji = status_emoji.get(result.qualification_status, "⚪")
        print(f"{emoji} Qualification Score: {result.qualification_score}/100")
        print(f"Status: {result.qualification_status.value.replace('_', ' ').title()}")
        
        # AI Reasoning
        print(f"\n💭 AI Reasoning:")
        print(f"   {result.ai_reasoning}")
        
        # Requirements
        if result.required_experience:
            print(f"\n🎯 Required Experience: {result.required_experience}")
        if result.education_requirements:
            print(f"🎓 Education Requirements: {result.education_requirements}")
        
        # Skills
        if result.key_skills_mentioned:
            print(f"\n🔧 Key Skills Mentioned: {', '.join(result.key_skills_mentioned)}")
        
        # Strengths and Concerns
        if result.matching_strengths:
            print(f"\n✅ Strengths:")
            for strength in result.matching_strengths:
                print(f"   • {strength}")
        
        if result.potential_concerns:
            print(f"\n⚠️  Concerns:")
            for concern in result.potential_concerns:
                print(f"   • {concern}")
        
        # Recommendation
        print(f"\n🎯 RECOMMENDATION:")
        if result.qualification_score >= 80:
            print("   🟢 HIGHLY RECOMMENDED - Strong match, definitely apply!")
        elif result.qualification_score >= 60:
            print("   🟡 RECOMMENDED - Good match, worth applying")
        elif result.qualification_score >= 40:
            print("   🟠 MAYBE - Some gaps, but could be worth a shot")
        else:
            print("   🔴 NOT RECOMMENDED - Significant gaps, focus on other opportunities")
    
    def _display_batch_summary(self, results: List[QualificationResult], successful: int, failed: int):
        """Display batch analysis summary."""
        print(f"\n📈 BATCH ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Total Jobs: {successful + failed}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(successful/(successful+failed)*100):.1f}%")
        
        if results:
            # Score distribution
            scores = [r.qualification_score for r in results]
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)
            
            print(f"\n📊 Score Statistics:")
            print(f"   Average Score: {avg_score:.1f}/100")
            print(f"   Highest Score: {max_score}/100")
            print(f"   Lowest Score: {min_score}/100")
            
            # Status distribution
            status_counts = {}
            for result in results:
                status = result.qualification_status.value
                status_counts[status] = status_counts.get(status, 0) + 1
            
            print(f"\n🏷️  Status Distribution:")
            for status, count in status_counts.items():
                percentage = (count / len(results)) * 100
                print(f"   {status.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
            
            # Top recommendations
            top_jobs = sorted(results, key=lambda x: x.qualification_score, reverse=True)[:3]
            print(f"\n🏆 TOP RECOMMENDATIONS:")
            for i, job in enumerate(top_jobs, 1):
                print(f"   {i}. {job.job_title} at {job.company}: {job.qualification_score}/100")
    
    def show_user_profile(self):
        """Display current user profile."""
        user_profile = self.system.config_manager.get_user_profile()
        
        print(f"\n👤 YOUR PROFILE")
        print("=" * 40)
        print(f"Years of Experience: {user_profile.years_of_experience}")
        print(f"Education: {'College graduate' if user_profile.has_college_degree else 'No college degree'}")
        if user_profile.has_college_degree:
            print(f"Field of Study: {user_profile.field_of_study}")
        print(f"Experience Level: {user_profile.experience_level}")
        print(f"Salary Range: ${user_profile.salary_min:,} - ${user_profile.salary_max:,}")
        print(f"Remote Preference: {user_profile.remote_preference}")
        print(f"Preferred Locations: {', '.join(user_profile.preferred_locations)}")
        print(f"Skills: {', '.join(user_profile.additional_skills)}")
    
    def test_google_sheets(self):
        """Test Google Sheets connection and write a sample result."""
        if not self.system.sheets_manager:
            print("❌ Google Sheets not configured")
            return False
        
        print("🧪 Testing Google Sheets connection...")
        
        # Test connection
        if not self.system.sheets_manager.test_connection():
            print("❌ Google Sheets connection failed")
            return False
        
        print("✅ Google Sheets connection successful")
        
        # Create a sample qualification result
        from datetime import datetime
        sample_result = QualificationResult(
            job_id="test-job-001",
            job_title="Test Software Engineer",
            company="Test Company",
            job_url="https://example.com/test-job",
            qualification_score=75,
            qualification_status=QualificationStatus.QUALIFIED,
            ai_reasoning="This is a test qualification result for Google Sheets testing.",
            required_experience="1-2 years",
            education_requirements="Bachelor's degree",
            key_skills_mentioned=["Python", "React"],
            matching_strengths=["Python experience"],
            potential_concerns=["Limited React experience"],
            user_decision=UserDecision.PENDING,
            ai_model_used="test",
            analysis_duration=1.5
        )
        
        # Write to Google Sheets
        print("📝 Writing test result to Google Sheets...")
        success = self.system.sheets_manager.write_qualification_result(sample_result)
        
        if success:
            print("✅ Test result written successfully!")
            print("📊 Check your Google Sheets to see the test data")
            return True
        else:
            print("❌ Failed to write test result")
            return False


def main():
    """Main function to run the job analysis."""
    print("🎯 Job Qualification Analysis System")
    print("=" * 50)
    
    runner = JobAnalysisRunner()
    
    while True:
        print(f"\n📋 MAIN MENU")
        print("1. Analyze single job URL")
        print("2. Analyze multiple jobs from list")
        print("3. Analyze jobs from file")
        print("4. View my profile settings")
        print("5. Test Google Sheets connection")
        print("6. Exit")
        
        choice = input("\nChoose option (1-6): ").strip()
        
        if choice == "1":
            # Single job analysis
            job_url = input("Enter job URL: ").strip()
            if job_url:
                save_choice = input("Save to Google Sheets? (y/n): ").strip().lower()
                save_to_sheets = save_choice in ['y', 'yes']
                runner.analyze_single_job(job_url, save_to_sheets)
            else:
                print("❌ No URL provided")
        
        elif choice == "2":
            # Multiple jobs from list
            print("Enter job URLs (one per line, press Enter twice when done):")
            job_urls = []
            while True:
                url = input().strip()
                if not url:
                    break
                job_urls.append(url)
            
            if job_urls:
                save_choice = input("Save to Google Sheets? (y/n): ").strip().lower()
                save_to_sheets = save_choice in ['y', 'yes']
                runner.analyze_multiple_jobs(job_urls, save_to_sheets)
            else:
                print("❌ No URLs provided")
        
        elif choice == "3":
            # Jobs from file
            file_path = input("Enter file path with job URLs (one per line): ").strip()
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    job_urls = [line.strip() for line in f if line.strip()]
                
                if job_urls:
                    save_choice = input("Save to Google Sheets? (y/n): ").strip().lower()
                    save_to_sheets = save_choice in ['y', 'yes']
                    runner.analyze_multiple_jobs(job_urls, save_to_sheets)
                else:
                    print("❌ No URLs found in file")
            else:
                print("❌ File not found")
        
        elif choice == "4":
            # Show user profile
            runner.show_user_profile()
        
        elif choice == "5":
            # Test Google Sheets
            runner.test_google_sheets()
        
        elif choice == "6":
            # Exit
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please enter 1-6.")


if __name__ == "__main__":
    main() 