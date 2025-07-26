# Tests Directory

This directory contains comprehensive test suites for the Job Application Automation System.

## Contents

### **Core System Tests**
- `test_basic.py` - Basic system functionality tests
- `test_enhanced_linkedin_scraper.py` - Enhanced LinkedIn scraper tests
- `test_linkedin_scraper.py` - Basic LinkedIn scraper tests
- `test_linkedin_fixes.py` - LinkedIn scraper fix tests
- `test_linkedin_date_filter.py` - Date filtering functionality tests
- `test_linkedin_duplicate_detection.py` - Duplicate detection tests
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
- `test_google_sheets.py` - Google Sheets integration tests
- `test_job_tracking_system.py` - Job tracking system tests
- `test_duplicate_detection.py` - Duplicate detection tests
- `test_url_extraction.py` - URL extraction tests
- `test_search_extraction.py` - Search extraction tests
- `test_real_job.py` - Real job processing tests
- `test_scraping_foundation.py` - Scraping foundation tests

## Running Tests

### Run All Tests
```bash
python -m pytest tests/
```

### Run Specific Test Categories
```bash
# LinkedIn scraper tests
python -m pytest tests/test_linkedin_*.py

# Integration tests
python -m pytest tests/test_integration.py

# Filter tests
python -m pytest tests/test_*filter*.py

# Component tests
python -m pytest tests/test_qualification_system.py tests/test_resume_system.py
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
- Individual component functionality
- Isolated testing of specific features
- Fast execution

### **Integration Tests**
- End-to-end workflow testing
- Component interaction testing
- Real-world scenario validation

### **Filter Tests**
- LinkedIn filter application testing
- Filter detection logic validation
- Browser automation verification

## Notes

- Tests require proper configuration and credentials
- Some tests may require browser automation
- Integration tests may take longer to run
- Use `--tb=short` for shorter tracebacks 