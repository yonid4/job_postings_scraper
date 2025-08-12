#!/usr/bin/env python3
"""
Test script to verify LinkedIn credentials loading from .env file.

This script tests that the ConfigurationManager correctly loads
LinkedIn username and password from environment variables.
"""

import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from backend.src.config.config_manager import ConfigurationManager

def test_linkedin_credentials_loading():
    """Test that LinkedIn credentials are loaded from .env file."""
    print("🧪 Testing LinkedIn Credentials Loading")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = Path('.env')
    if env_file.exists():
        print(f"✅ Found .env file: {env_file.absolute()}")
    else:
        print(f"❌ .env file not found at: {env_file.absolute()}")
        print("💡 Create .env file from env.template:")
        print("   cp env.template .env")
        return False
    
    # Check environment variables directly
    username = os.getenv('LINKEDIN_USERNAME')
    password = os.getenv('LINKEDIN_PASSWORD')
    
    print(f"\n📋 Environment Variables Check:")
    print(f"   LINKEDIN_USERNAME: {'✅ Set' if username else '❌ Not set'}")
    print(f"   LINKEDIN_PASSWORD: {'✅ Set' if password else '❌ Not set'}")
    
    if not username or not password:
        print("\n⚠️  LinkedIn credentials not found in environment variables")
        print("💡 Make sure your .env file contains:")
        print("   LINKEDIN_USERNAME=your_email@example.com")
        print("   LINKEDIN_PASSWORD=your_linkedin_password")
        return False
    
    # Test ConfigurationManager
    print(f"\n🔧 Testing ConfigurationManager...")
    try:
        config_manager = ConfigurationManager()
        linkedin_settings = config_manager.get_linkedin_settings()
        
        print(f"\n📊 ConfigurationManager Results:")
        print(f"   Username loaded: {'✅ Yes' if linkedin_settings.username else '❌ No'}")
        print(f"   Password loaded: {'✅ Yes' if linkedin_settings.password else '❌ No'}")
        print(f"   Headless mode: {linkedin_settings.headless}")
        print(f"   Delay between actions: {linkedin_settings.delay_between_actions}s")
        print(f"   Max jobs per search: {linkedin_settings.max_jobs_per_search}")
        print(f"   Use date filtering: {linkedin_settings.use_date_filtering}")
        
        if linkedin_settings.username and linkedin_settings.password:
            print(f"\n🎉 LinkedIn credentials loaded successfully!")
            print(f"   Username: {linkedin_settings.username}")
            print(f"   Password: {'*' * len(linkedin_settings.password)}")
            return True
        else:
            print(f"\n❌ LinkedIn credentials not loaded properly")
            return False
            
    except Exception as e:
        print(f"\n❌ Error testing ConfigurationManager: {e}")
        return False

def main():
    """Main test function."""
    success = test_linkedin_credentials_loading()
    
    print(f"\n{'=' * 50}")
    if success:
        print("✅ LinkedIn credentials test PASSED")
        print("🚀 You can now use the LinkedIn scraper with your credentials!")
    else:
        print("❌ LinkedIn credentials test FAILED")
        print("🔧 Please check your .env file configuration")
    
    return success

if __name__ == "__main__":
    main() 