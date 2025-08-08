# Tests Directory

This directory contains comprehensive test suites for the AI Job Qualification Screening System with 35+ test files covering all major functionality.

## Contents

### **Core System Tests**
- `test_basic.py` - Basic system functionality tests
- `test_enhanced_linkedin_scraper.py` - Enhanced LinkedIn scraper tests
- `test_linkedin_scraper.py` - Basic LinkedIn scraper tests
- `test_linkedin_fixes.py` - LinkedIn scraper fix tests
- `test_linkedin_date_filter.py` - Date filtering functionality tests
- `test_linkedin_public_scraping.py` - Public scraping tests

### **Integration Tests**
- `test_integration.py` - System integration tests
- `test_fixed_filters.py` - Fixed filter functionality tests
- `test_filter_options_simple.py` - Simple filter option tests
- `test_all_filter_options.py` - Comprehensive filter option tests
- `test_filter_verification.py` - Filter verification tests
- `test_enhanced_linkedin_filters.py` - Enhanced filter tests
- `test_specific_filters.py` - Specific filter tests

### **Component Tests**
- `test_qualification_system.py` - AI qualification system tests
- `test_resume_system.py` - Resume processing tests
- `test_job_tracking_system.py` - Job tracking system tests
- `test_url_extraction.py` - URL extraction tests
- `test_search_extraction.py` - Search extraction tests
- `test_real_job.py` - Real job processing tests
- `test_scraping_foundation.py` - Scraping foundation tests

### **Authentication & Database Tests**
- `test_supabase_integration.py` - Supabase integration tests
- `test_supabase_resume_integration.py` - Resume storage integration tests
- `test_linkedin_credentials.py` - LinkedIn authentication tests
- `test_database_saving.py` - Database saving functionality tests
- `test_frontend_integration.py` - Frontend integration tests

### **Advanced Feature Tests**
- `test_enhanced_scoring_system.py` - Enhanced AI scoring tests
- `test_favorites_integration.py` - Job favorites functionality tests
- `test_captcha_handling.py` - CAPTCHA detection and handling tests
- `test_captcha_flow.py` - CAPTCHA workflow tests
- `test_new_linkedin_features.py` - New LinkedIn feature tests
- `test_rate_limiting_enhanced.py` - Enhanced rate limiting tests
- `test_search_optimization.py` - Search optimization tests
- `test_quota_handling.py` - API quota handling tests

### **Performance & Monitoring Tests**
- `test_scraper_instantiation.py` - Scraper initialization tests
- `test_frontend_data_sending.py` - Frontend data transmission tests

## Running Tests

### Run All Tests
```bash
python -m pytest tests/
```

### Run Specific Test Categories
```bash
# LinkedIn scraper tests
python -m pytest tests/test_linkedin_*.py

# AI qualification tests
python -m pytest tests/test_qualification_*.py tests/test_enhanced_scoring_*.py

# Authentication and database tests
python -m pytest tests/test_supabase_*.py tests/test_auth_*.py

# Filter tests
python -m pytest tests/test_*filter*.py

# CAPTCHA and rate limiting tests
python -m pytest tests/test_captcha_*.py tests/test_rate_limiting_*.py

# Integration tests
python -m pytest tests/test_integration.py tests/test_frontend_*.py

# Resume and favorites tests
python -m pytest tests/test_resume_*.py tests/test_favorites_*.py
```

### Run with Verbose Output
```bash
python -m pytest tests/ -v
```

### Run with Coverage
```bash
python -m pytest tests/ --cov=src --cov-report=html
```

## Test Categories

### **Unit Tests**
- Individual component functionality (AI analysis, resume processing)
- Isolated testing of specific features (CAPTCHA handling, rate limiting)
- Fast execution with mocked dependencies

### **Integration Tests**
- End-to-end workflow testing (job search to tracking)
- Component interaction testing (Supabase + AI + scraping)
- Real-world scenario validation
- Frontend-backend integration testing

### **Authentication Tests**
- Supabase authentication flow testing
- User registration and login validation
- Session management and security testing
- Profile creation and management testing

### **AI & Analysis Tests**
- Google Gemini integration testing
- Job qualification scoring validation
- Resume processing and skill extraction
- Enhanced scoring algorithm testing

### **Scraping Tests**
- LinkedIn scraper functionality testing
- Filter application and detection testing
- CAPTCHA handling workflow testing
- Rate limiting and anti-detection testing

### **Database Tests**
- Supabase integration and data saving
- Job tracking and application management
- Favorites and search history testing
- Data consistency and validation testing

## Test Coverage

The test suite provides comprehensive coverage of:
- **Core Functionality**: 90%+ coverage of main system features
- **Error Handling**: Comprehensive error scenario testing
- **Performance**: Load testing and optimization validation
- **Security**: Authentication and data protection testing
- **User Workflows**: Complete user journey testing

## Notes

- Tests require proper `.env` configuration with test credentials
- Some tests require active browser automation (Chrome/Selenium)
- Integration tests may take longer to run (network dependencies)
- Use `--tb=short` for shorter tracebacks
- Run tests in isolated environments to avoid data conflicts
- Some tests may require valid API keys (Gemini, Supabase) 