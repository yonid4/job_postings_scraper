#!/usr/bin/env python3
"""
Demo script showing AI job qualification analysis.

This script demonstrates how the AI analysis works with mock job descriptions,
so you can see the system in action without needing real job URLs.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.ai.qualification_analyzer import AnalysisRequest, QualificationAnalyzer
from src.config.config_manager import ConfigurationManager
from src.data.models import QualificationStatus


def demo_entry_level_job():
    """Demo analysis of an entry-level job."""
    print("🎯 Demo: Entry-Level Software Engineer")
    print("=" * 50)
    
    job_description = """
    Entry-Level Software Engineer
    
    We are looking for a motivated Entry-Level Software Engineer to join our growing team.
    
    Requirements:
    - 0-2 years of experience in software development
    - Bachelor's degree in Computer Science, Information Technology, or related field
    - Basic knowledge of Python, JavaScript, or similar programming languages
    - Familiarity with web development concepts
    - Strong problem-solving and communication skills
    - Eagerness to learn and grow
    
    Nice to have:
    - Experience with React, Node.js, or similar frameworks
    - Knowledge of SQL and databases
    - Experience with Git version control
    - Understanding of cloud platforms (AWS, GCP, Azure)
    
    Responsibilities:
    - Develop and maintain web applications
    - Collaborate with senior developers on projects
    - Participate in code reviews
    - Learn new technologies and best practices
    - Contribute to team documentation
    
    Location: San Francisco, CA (Hybrid)
    Salary: $70,000 - $90,000
    """
    
    return "Entry-Level Software Engineer", "Tech Startup Inc", job_description


def demo_mid_level_job():
    """Demo analysis of a mid-level job."""
    print("🎯 Demo: Mid-Level Software Engineer")
    print("=" * 50)
    
    job_description = """
    Software Engineer (Mid-Level)
    
    We are seeking a Software Engineer with 2-4 years of experience to join our team.
    
    Requirements:
    - 2-4 years of experience in software development
    - Bachelor's degree in Computer Science or related field
    - Strong proficiency in Python and JavaScript
    - Experience with React, Node.js, or similar frameworks
    - Knowledge of SQL databases and REST APIs
    - Experience with Git and version control
    - Understanding of software development best practices
    
    Preferred:
    - Experience with cloud platforms (AWS, GCP, Azure)
    - Knowledge of Docker and containerization
    - Experience with CI/CD pipelines
    - Understanding of microservices architecture
    
    Responsibilities:
    - Design and implement scalable software solutions
    - Collaborate with cross-functional teams
    - Mentor junior developers
    - Participate in technical discussions and planning
    - Contribute to code reviews and documentation
    
    Location: New York, NY (Hybrid)
    Salary: $100,000 - $130,000
    """
    
    return "Software Engineer", "Established Tech Company", job_description


def demo_senior_job():
    """Demo analysis of a senior-level job."""
    print("🎯 Demo: Senior Software Engineer")
    print("=" * 50)
    
    job_description = """
    Senior Software Engineer
    
    We are looking for a Senior Software Engineer with 5+ years of experience to lead technical initiatives.
    
    Requirements:
    - 5+ years of experience in software development
    - Bachelor's degree in Computer Science or related field
    - Expert-level proficiency in Python, JavaScript, and related technologies
    - Deep experience with React, Node.js, and modern web frameworks
    - Strong knowledge of SQL and NoSQL databases
    - Experience with cloud platforms (AWS, GCP, Azure)
    - Experience with Docker, Kubernetes, and microservices
    - Strong understanding of software architecture and design patterns
    - Experience leading technical projects and mentoring developers
    
    Required:
    - Experience with CI/CD pipelines and DevOps practices
    - Strong problem-solving and analytical skills
    - Excellent communication and leadership abilities
    - Experience with agile development methodologies
    
    Responsibilities:
    - Lead technical design and architecture decisions
    - Mentor and guide junior and mid-level developers
    - Collaborate with product managers and stakeholders
    - Drive technical excellence and best practices
    - Participate in code reviews and technical planning
    - Contribute to strategic technical decisions
    
    Location: San Francisco, CA (Hybrid)
    Salary: $150,000 - $200,000
    """
    
    return "Senior Software Engineer", "Major Tech Company", job_description


def run_demo_analysis(job_title, company, job_description):
    """Run AI analysis on the demo job."""
    print(f"📋 Job: {job_title} at {company}")
    print(f"📝 Description: {job_description[:200]}...")
    print()
    
    # Get configuration
    config_manager = ConfigurationManager()
    user_profile = config_manager.get_user_profile()
    ai_settings = config_manager.get_ai_settings()
    
    # Create analysis request
    request = AnalysisRequest(
        job_title=job_title,
        company=company,
        job_description=job_description,
        user_profile=user_profile,
        ai_settings=ai_settings
    )
    
    # Run analysis
    print("🤖 Running AI qualification analysis...")
    
    if not ai_settings.api_key:
        print("⚠️  No Gemini API key - using custom rule-based analysis")
        from examples.custom_analyzer_example import CustomRuleBasedAnalyzer
        analyzer = CustomRuleBasedAnalyzer(ai_settings)
    else:
        analyzer = QualificationAnalyzer(ai_settings)
    
    analysis_response = analyzer.analyze_job_qualification(request)
    
    # Display results
    print(f"\n📊 ANALYSIS RESULTS")
    print(f"Job: {job_title} at {company}")
    print("-" * 40)
    
    # Score and status
    status_emoji = {
        QualificationStatus.HIGHLY_QUALIFIED: "🟢",
        QualificationStatus.QUALIFIED: "🟡", 
        QualificationStatus.SOMEWHAT_QUALIFIED: "🟠",
        QualificationStatus.NOT_QUALIFIED: "🔴"
    }
    
    emoji = status_emoji.get(analysis_response.qualification_status, "⚪")
    print(f"{emoji} Qualification Score: {analysis_response.qualification_score}/100")
    print(f"Status: {analysis_response.qualification_status.value.replace('_', ' ').title()}")
    
    # AI Reasoning
    print(f"\n💭 AI Reasoning:")
    print(f"   {analysis_response.ai_reasoning}")
    
    # Requirements
    if analysis_response.required_experience:
        print(f"\n🎯 Required Experience: {analysis_response.required_experience}")
    if analysis_response.education_requirements:
        print(f"🎓 Education Requirements: {analysis_response.education_requirements}")
    
    # Skills
    if analysis_response.key_skills_mentioned:
        print(f"\n🔧 Key Skills Mentioned: {', '.join(analysis_response.key_skills_mentioned)}")
    
    # Strengths and Concerns
    if analysis_response.matching_strengths:
        print(f"\n✅ Strengths:")
        for strength in analysis_response.matching_strengths:
            print(f"   • {strength}")
    
    if analysis_response.potential_concerns:
        print(f"\n⚠️  Concerns:")
        for concern in analysis_response.potential_concerns:
            print(f"   • {concern}")
    
    # Recommendation
    print(f"\n🎯 RECOMMENDATION:")
    if analysis_response.qualification_score >= 80:
        print("   🟢 HIGHLY RECOMMENDED - Strong match, definitely apply!")
    elif analysis_response.qualification_score >= 60:
        print("   🟡 RECOMMENDED - Good match, worth applying")
    elif analysis_response.qualification_score >= 40:
        print("   🟠 MAYBE - Some gaps, but could be worth a shot")
    else:
        print("   🔴 NOT RECOMMENDED - Significant gaps, focus on other opportunities")
    
    print("\n" + "=" * 60)


def main():
    """Main demo function."""
    print("🎯 Job Qualification Analysis - Demo")
    print("=" * 60)
    
    print("👤 Your Profile:")
    config_manager = ConfigurationManager()
    user_profile = config_manager.get_user_profile()
    print(f"   Experience: {user_profile.years_of_experience} years")
    print(f"   Education: {user_profile.field_of_study}")
    print(f"   Level: {user_profile.experience_level}")
    print(f"   Skills: {', '.join(user_profile.additional_skills[:5])}...")
    print()
    
    # Run demos for different job levels
    demos = [
        ("Entry-Level Job", demo_entry_level_job),
        ("Mid-Level Job", demo_mid_level_job),
        ("Senior-Level Job", demo_senior_job)
    ]
    
    for demo_name, demo_func in demos:
        print(f"\n🎯 {demo_name}")
        print("=" * 60)
        
        job_title, company, job_description = demo_func()
        run_demo_analysis(job_title, company, job_description)
    
    print("\n📈 SUMMARY:")
    print("This demo shows how the AI analyzes different job levels:")
    print("• Entry-level jobs should score high for entry-level candidates")
    print("• Mid-level jobs should score medium for entry-level candidates")
    print("• Senior-level jobs should score low for entry-level candidates")
    print()
    print("💡 The system considers:")
    print("• Experience level matching")
    print("• Skills alignment")
    print("• Education requirements")
    print("• Location and salary preferences")
    print("• Overall fit for the role")


if __name__ == "__main__":
    main() 