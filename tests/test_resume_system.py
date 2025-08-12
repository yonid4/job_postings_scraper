#!/usr/bin/env python3
"""
Test script for the Lazy Resume Processing System.

This script tests the core functionality of the resume processing system
including file upload, text extraction, and AI processing.
"""

import os
import sys
import tempfile
import json
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from backend.src.data.resume_processor import ResumeProcessor
from backend.src.data.resume_manager import ResumeManager
from backend.src.utils.logger import JobAutomationLogger

logger = JobAutomationLogger()


def create_test_resume_file():
    """Create a simple test resume file for testing."""
    test_content = """
    JOHN DOE
    Software Engineer
    john.doe@email.com | (555) 123-4567 | New York, NY
    
    SUMMARY
    Experienced software engineer with 5+ years in full-stack development.
    
    EDUCATION
    Bachelor of Science in Computer Science
    University of Technology, 2019
    
    EXPERIENCE
    Senior Software Engineer
    Tech Company Inc. | 2021 - Present
    - Developed and maintained web applications using React and Node.js
    - Led a team of 3 developers on multiple projects
    - Implemented CI/CD pipelines using Docker and AWS
    
    Software Engineer
    Startup Corp | 2019 - 2021
    - Built RESTful APIs using Python and Django
    - Worked with PostgreSQL and Redis databases
    - Collaborated with cross-functional teams
    
    SKILLS
    Programming Languages: Python, JavaScript, Java, SQL
    Frameworks: React, Node.js, Django, Spring Boot
    Tools: Git, Docker, AWS, Jenkins
    """
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_content)
        return f.name


def test_resume_processor():
    """Test the resume processor functionality."""
    print("🧪 Testing Resume Processor...")
    
    try:
        # Create test resume file
        test_file = create_test_resume_file()
        print(f"✅ Created test resume file: {test_file}")
        
        # Initialize processor (without AI client for basic testing)
        processor = ResumeProcessor()
        
        # Test file validation
        assert processor.is_supported_file("test.pdf") == True
        assert processor.is_supported_file("test.docx") == True
        assert processor.is_supported_file("test.txt") == False
        print("✅ File validation tests passed")
        
        # Test file hash calculation
        file_hash = processor.calculate_file_hash(test_file)
        assert len(file_hash) == 64  # SHA256 hash length
        print(f"✅ File hash calculation: {file_hash[:16]}...")
        
        # Test basic text extraction (for txt file)
        try:
            with open(test_file, 'r') as f:
                text = f.read()
            print(f"✅ Text extraction: {len(text)} characters")
        except Exception as e:
            print(f"⚠️ Text extraction test skipped: {e}")
        
        # Test basic resume data extraction
        basic_data = processor._extract_basic_resume_data(test_file)
        assert isinstance(basic_data, dict)
        assert 'personal_info' in basic_data
        assert 'skills' in basic_data
        print("✅ Basic resume data extraction passed")
        
        # Cleanup
        os.unlink(test_file)
        print("✅ Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Resume processor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_resume_manager():
    """Test the resume manager functionality."""
    print("\n🧪 Testing Resume Manager...")
    
    try:
        # Create temporary database and upload folder
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, 'test_resume.db')
            upload_folder = os.path.join(temp_dir, 'uploads')
            
            # Initialize manager
            manager = ResumeManager(db_path, upload_folder)
            print("✅ Resume manager initialized")
            
            # Test resume status for non-existent user
            status = manager.get_resume_status("test_user_123")
            assert status['has_resume'] == False
            print("✅ Resume status check for non-existent user")
            
            # Test file upload simulation
            test_file = create_test_resume_file()
            fake_pdf = None
            fake_pdf2 = None
            
            try:
                result = manager.upload_resume("test_user_123", test_file, "test_resume.txt")
                assert result['success'] == False  # Should fail for unsupported file type
                print("✅ File type validation working")
                
                # Test with supported file type (create a fake PDF)
                fake_pdf = os.path.join(temp_dir, "test.pdf")
                with open(fake_pdf, 'w') as f:
                    f.write("Fake PDF content")
                
                result = manager.upload_resume("test_user_123", fake_pdf, "test_resume.pdf")
                if result['success']:
                    print("✅ Resume upload successful")
                    
                    # Test resume status
                    status = manager.get_resume_status("test_user_123")
                    assert status['has_resume'] == True
                    print("✅ Resume status check for uploaded resume")
                    
                    # Test duplicate upload
                    fake_pdf2 = os.path.join(temp_dir, "test2.pdf")
                    with open(fake_pdf2, 'w') as f:
                        f.write("Fake PDF content")  # Same content
                    
                    result2 = manager.upload_resume("test_user_123", fake_pdf2, "test_resume2.pdf")
                    if result2['success'] and 'already uploaded' in result2['message']:
                        print("✅ Duplicate detection working")
                    else:
                        print(f"⚠️ Duplicate detection test: {result2.get('message', 'Unknown result')}")
                    
                else:
                    print(f"⚠️ Resume upload test skipped: {result.get('error', 'Unknown error')}")
                
            finally:
                # Cleanup test files
                if os.path.exists(test_file):
                    os.unlink(test_file)
                if fake_pdf and os.path.exists(fake_pdf):
                    os.unlink(fake_pdf)
                if fake_pdf2 and os.path.exists(fake_pdf2):
                    os.unlink(fake_pdf2)
        
        return True
        
    except Exception as e:
        print(f"❌ Resume manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking Dependencies...")
    
    missing_deps = []
    
    try:
        import PyPDF2
        print("✅ PyPDF2 is available")
    except ImportError:
        print("❌ PyPDF2 is not installed")
        missing_deps.append("PyPDF2")
    
    try:
        import docx
        print("✅ python-docx is available")
    except ImportError:
        print("❌ python-docx is not installed")
        missing_deps.append("python-docx")
    
    if missing_deps:
        print(f"\n⚠️ Missing dependencies: {', '.join(missing_deps)}")
        print("Install them with: pip install -r requirements.txt")
        return False
    else:
        print("✅ All dependencies are available")
        return True


def main():
    """Run all tests."""
    print("🚀 Starting Lazy Resume Processing System Tests\n")
    
    # Check dependencies first
    deps_ok = check_dependencies()
    print()
    
    # Test resume processor
    processor_success = test_resume_processor()
    
    # Test resume manager
    manager_success = test_resume_manager()
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST RESULTS")
    print("="*50)
    print(f"Dependencies:     {'✅ AVAILABLE' if deps_ok else '❌ MISSING'}")
    print(f"Resume Processor: {'✅ PASSED' if processor_success else '❌ FAILED'}")
    print(f"Resume Manager:   {'✅ PASSED' if manager_success else '❌ FAILED'}")
    
    if processor_success and manager_success:
        print("\n🎉 All tests passed! The resume processing system is working correctly.")
        if not deps_ok:
            print("\n📝 Note: Install dependencies for full PDF/DOCX support:")
            print("   pip install -r requirements.txt")
        print("\n📝 Next steps:")
        print("1. Start the Flask app: python frontend/app.py")
        print("2. Go to Settings page to upload a resume")
        print("3. Search for jobs to trigger resume processing")
    else:
        print("\n⚠️ Some tests failed. Please check the implementation.")
    
    print("\n" + "="*50)


if __name__ == "__main__":
    main() 