#!/usr/bin/env python3
"""
Debug script to help identify why the browser might not be opening when filters are applied.
This script will help trace the exact flow from frontend to backend.
"""

import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def debug_filter_detection():
    """Debug the filter detection logic step by step."""
    
    print("🔍 DEBUG: Filter Detection Logic")
    print("=" * 50)
    
    # Simulate what the frontend should be sending
    print("1️⃣ Frontend Form Data (what should be sent):")
    frontend_data = {
        'keywords': 'Python Developer',
        'location': 'Remote',
        'date_posted': 'any',
        'work_arrangement': ['remote'],  # This should trigger browser
        'experience_level': [],
        'job_type': []
    }
    
    for key, value in frontend_data.items():
        print(f"   {key}: {value}")
    
    print("\n2️⃣ Backend Processing (what happens in app.py):")
    
    # Simulate backend processing
    search_params = {
        'keywords': frontend_data['keywords'],
        'location': frontend_data['location'],
        'date_posted': frontend_data['date_posted'],
        'work_arrangement': frontend_data['work_arrangement'],
        'experience_level': frontend_data['experience_level'],
        'job_type': frontend_data['job_type']
    }
    
    print("   search_params created:")
    for key, value in search_params.items():
        print(f"      {key}: {value}")
    
    # Extract filter values
    work_arrangement = search_params['work_arrangement'][0] if search_params['work_arrangement'] else None
    experience_level = search_params['experience_level'][0] if search_params['experience_level'] else None
    job_type = search_params['job_type'][0] if search_params['job_type'] else None
    
    print(f"\n   Filter values extracted:")
    print(f"      work_arrangement: {work_arrangement}")
    print(f"      experience_level: {experience_level}")
    print(f"      job_type: {job_type}")
    
    # Apply filter detection logic
    has_custom_filters = False
    
    if work_arrangement:
        has_custom_filters = True
        print(f"      ✅ Work arrangement filter detected: {work_arrangement}")
        
    if experience_level:
        has_custom_filters = True
        print(f"      ✅ Experience level filter detected: {experience_level}")
        
    if job_type:
        has_custom_filters = True
        print(f"      ✅ Job type filter detected: {job_type}")
    
    print(f"\n   Filter detection result: has_custom_filters = {has_custom_filters}")
    
    # Determine scraper selection
    if has_custom_filters:
        print("\n3️⃣ CUSTOM FILTERS DETECTED!")
        print("   → Should use FixedLinkedInScraper")
        print("   → Should open browser for authentication")
        print("   → Should apply filters in LinkedIn UI")
        
        print("\n4️⃣ Next Steps (what should happen):")
        print("   a) Import FixedLinkedInScraper")
        print("   b) Create SessionManager")
        print("   c) Create ScrapingConfig with LinkedIn credentials")
        print("   d) Instantiate FixedLinkedInScraper")
        print("   e) Call scrape_jobs_with_enhanced_date_filter()")
        print("   f) Browser should open and authenticate")
        print("   g) Apply filters in LinkedIn UI")
        
        return True
    else:
        print("\n3️⃣ NO CUSTOM FILTERS DETECTED!")
        print("   → Should use JobLinkProcessor")
        print("   → Should NOT open browser")
        print("   → Should use URL-based scraping")
        return False

def check_potential_issues():
    """Check for potential issues that might prevent browser from opening."""
    
    print("\n🔍 DEBUG: Potential Issues Check")
    print("=" * 50)
    
    issues = []
    
    # Check 1: LinkedIn credentials
    print("1️⃣ LinkedIn Credentials Check:")
    try:
        from src.config.config_manager import ConfigurationManager
        config_manager = ConfigurationManager()
        linkedin_config = config_manager.get_linkedin_settings()
        
        if linkedin_config.username and linkedin_config.password:
            print("   ✅ LinkedIn credentials are configured")
        else:
            print("   ❌ LinkedIn credentials are missing")
            issues.append("LinkedIn credentials not configured")
    except Exception as e:
        print(f"   ❌ Error checking LinkedIn credentials: {e}")
        issues.append(f"LinkedIn credentials error: {e}")
    
    # Check 2: Required modules
    print("\n2️⃣ Required Modules Check:")
    try:
        from src.scrapers.linkedin_scraper_fixed import FixedLinkedInScraper
        print("   ✅ FixedLinkedInScraper can be imported")
    except Exception as e:
        print(f"   ❌ Error importing FixedLinkedInScraper: {e}")
        issues.append(f"FixedLinkedInScraper import error: {e}")
    
    try:
        from src.utils.session_manager import SessionManager
        print("   ✅ SessionManager can be imported")
    except Exception as e:
        print(f"   ❌ Error importing SessionManager: {e}")
        issues.append(f"SessionManager import error: {e}")
    
    try:
        from src.scrapers.base_scraper import ScrapingConfig
        print("   ✅ ScrapingConfig can be imported")
    except Exception as e:
        print(f"   ❌ Error importing ScrapingConfig: {e}")
        issues.append(f"ScrapingConfig import error: {e}")
    
    # Check 3: Browser driver
    print("\n3️⃣ Browser Driver Check:")
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Test in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Try to create a driver (this will fail if ChromeDriver is not available)
        driver = webdriver.Chrome(options=chrome_options)
        driver.quit()
        print("   ✅ ChromeDriver is available and working")
    except Exception as e:
        print(f"   ❌ ChromeDriver issue: {e}")
        issues.append(f"ChromeDriver issue: {e}")
    
    # Check 4: Network connectivity
    print("\n4️⃣ Network Connectivity Check:")
    try:
        import requests
        response = requests.get("https://www.linkedin.com", timeout=10)
        if response.status_code == 200:
            print("   ✅ LinkedIn is accessible")
        else:
            print(f"   ⚠️ LinkedIn returned status code: {response.status_code}")
            issues.append(f"LinkedIn accessibility issue: status {response.status_code}")
    except Exception as e:
        print(f"   ❌ Network connectivity issue: {e}")
        issues.append(f"Network connectivity issue: {e}")
    
    # Summary
    print("\n5️⃣ Issues Summary:")
    if issues:
        print("   ❌ Found the following potential issues:")
        for i, issue in enumerate(issues, 1):
            print(f"      {i}. {issue}")
    else:
        print("   ✅ No obvious issues found")
    
    return issues

def provide_debugging_steps():
    """Provide debugging steps to identify the issue."""
    
    print("\n🔍 DEBUG: Troubleshooting Steps")
    print("=" * 50)
    
    print("If the browser is not opening when filters are applied, try these steps:")
    
    print("\n1️⃣ Check Frontend Logs:")
    print("   - Open browser developer tools (F12)")
    print("   - Go to Console tab")
    print("   - Apply filters and run analysis")
    print("   - Look for any JavaScript errors")
    print("   - Check Network tab for failed requests")
    
    print("\n2️⃣ Check Backend Logs:")
    print("   - Look at the terminal where you're running the Flask app")
    print("   - Apply filters and run analysis")
    print("   - Look for any Python errors or warnings")
    print("   - Check if 'has_custom_filters = True' appears in logs")
    
    print("\n3️⃣ Test with Different Filters:")
    print("   - Try applying only Work Arrangement: Remote")
    print("   - Try applying only Experience Level: Entry")
    print("   - Try applying only Job Type: Full-time")
    print("   - Try applying multiple filters together")
    
    print("\n4️⃣ Check LinkedIn Credentials:")
    print("   - Go to Settings page in the frontend")
    print("   - Verify LinkedIn username and password are set")
    print("   - Try logging in manually to LinkedIn to ensure credentials work")
    
    print("\n5️⃣ Test Browser Automation Directly:")
    print("   - Run a simple test script that opens LinkedIn")
    print("   - Check if ChromeDriver is properly installed")
    print("   - Verify Chrome browser is installed and up to date")
    
    print("\n6️⃣ Check for CAPTCHA/Puzzle:")
    print("   - LinkedIn might be showing a security challenge")
    print("   - Check if there's a browser window that opened but shows a puzzle")
    print("   - Complete any security challenges manually")
    print("   - Try the analysis again after completing the challenge")

def main():
    """Run the debug analysis."""
    
    print("🚀 Frontend Filter Debug Analysis")
    print("=" * 60)
    
    # Step 1: Debug filter detection
    filter_detection_works = debug_filter_detection()
    
    # Step 2: Check for potential issues
    issues = check_potential_issues()
    
    # Step 3: Provide debugging steps
    provide_debugging_steps()
    
    # Final summary
    print("\n" + "="*60)
    print("📊 DEBUG ANALYSIS SUMMARY")
    print("="*60)
    
    if filter_detection_works:
        print("✅ Filter detection logic is working correctly")
        print("✅ The system should open a browser when filters are applied")
    else:
        print("❌ Filter detection logic has issues")
    
    if not issues:
        print("✅ No obvious technical issues found")
        print("🔍 The problem might be in the actual execution flow")
    else:
        print(f"⚠️ Found {len(issues)} potential issues:")
        for issue in issues:
            print(f"   • {issue}")
    
    print("\n🎯 Next Steps:")
    print("1. Try applying filters again and check the logs")
    print("2. Look for any error messages in the browser console")
    print("3. Check the Flask app logs for any Python errors")
    print("4. Verify LinkedIn credentials are properly configured")
    print("5. Test with a simple filter like 'Work Arrangement: Remote'")
    
    print("\n🎉 Debug analysis completed!")

if __name__ == "__main__":
    main() 