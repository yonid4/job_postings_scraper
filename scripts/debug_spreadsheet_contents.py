#!/usr/bin/env python3
"""
Debug script to check current contents of Google Sheets.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.config.config_manager import ConfigurationManager
from src.data.google_sheets_manager import GoogleSheetsManager

def debug_spreadsheet_contents():
    """Debug the current contents of the Google Sheets."""
    
    try:
        # Initialize configuration
        config_manager = ConfigurationManager()
        api_settings = config_manager.get_api_settings()
        
        if not api_settings.google_sheets_spreadsheet_id:
            print("❌ Google Sheets not configured.")
            return
        
        # Initialize Google Sheets manager
        sheets_manager = GoogleSheetsManager(
            credentials_path=api_settings.google_sheets_credentials_path,
            spreadsheet_id=api_settings.google_sheets_spreadsheet_id
        )
        
        print("🔍 Checking current spreadsheet contents...")
        
        # Get all qualification results
        results = sheets_manager.get_qualification_results()
        
        print(f"📊 Total rows in spreadsheet: {len(results)}")
        
        if results:
            print("\n📋 Current jobs in spreadsheet:")
            print("-" * 80)
            
            for i, result in enumerate(results[:10], 1):  # Show first 10
                title = result.get('Job Title', 'N/A')
                company = result.get('Company Name', 'N/A')
                url = result.get('Job URL', 'N/A')
                score = result.get('Qualification Score', 'N/A')
                
                print(f"{i:2d}. {title} at {company}")
                print(f"    URL: {url}")
                print(f"    Score: {score}")
                print()
            
            if len(results) > 10:
                print(f"... and {len(results) - 10} more jobs")
        
        # Test specific jobs
        print("\n🧪 Testing specific job detection:")
        
        test_cases = [
            ("Software Engineer", "Test Company", "https://www.linkedin.com/jobs/view/1234567890"),
            ("Data Scientist", "Different Company", "https://www.linkedin.com/jobs/view/9876543210"),
            ("Software Engineer", "Different Company", "https://www.linkedin.com/jobs/view/1112223333"),
            ("Data Scientist", "Test Company", "https://www.linkedin.com/jobs/view/4445556666")
        ]
        
        for title, company, url in test_cases:
            is_duplicate = sheets_manager.is_job_duplicate(title, company, url)
            print(f"   '{title}' at '{company}' with URL '{url}': {'DUPLICATE' if is_duplicate else 'NEW'}")
        
    except Exception as e:
        print(f"❌ Error during debugging: {e}")

if __name__ == "__main__":
    debug_spreadsheet_contents() 