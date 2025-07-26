# LinkedIn Scraper Guide

This guide explains how to use the LinkedIn scraper component of the Job Application Automation System.

## Overview

The LinkedIn scraper (`LinkedInScraper`) is a comprehensive web scraping tool designed to extract job listings from LinkedIn search results. It includes:

- **Respectful scraping** with rate limiting and delays
- **Anti-detection measures** to avoid being blocked
- **Comprehensive error handling** for robust operation
- **Data parsing** to extract structured job information
- **Statistics tracking** for monitoring performance

## Features

### 🔍 Job Data Extraction
- Job title and company name
- Location and job type
- Salary information (when available)
- Experience level classification
- Remote work type detection
- Posted date parsing
- Job description preview

### 🛡️ Anti-Detection Measures
- Random user agent rotation
- WebDriver property masking
- Headless browser operation
- Configurable delays between requests
- Respect for robots.txt (when configured)

### 📊 Data Processing
- Automatic parsing of job types (full-time, part-time, contract, etc.)
- Experience level classification (entry, junior, mid, senior, executive)
- Remote work type detection (remote, hybrid, on-site)
- Salary range extraction and normalization
- Date parsing for posted times

## Installation Requirements

### Dependencies
```bash
pip install selenium webdriver-manager fake-useragent
```

### Chrome Browser
The scraper requires Chrome browser to be installed on your system. The `webdriver-manager` package will automatically download the appropriate ChromeDriver version.

## Basic Usage

### Using Context Manager (Recommended)

```python
from src.scrapers.linkedin_scraper import LinkedInScraper
from src.config.config_manager import ScrapingSettings

# Configure scraping settings
scraping_settings = ScrapingSettings(
    delay_min=2.0,
    delay_max=4.0,
    max_jobs_per_session=50,
    timeout=30
)

# Use context manager for automatic cleanup
with LinkedInScraper(scraping_settings) as scraper:
    # Scrape jobs from LinkedIn search URL
    search_url = "https://www.linkedin.com/jobs/search/?keywords=python%20developer&location=Remote"
    job_listings = scraper.scrape_jobs_from_url(search_url, max_jobs=10)
    
    # Process results
    for job in job_listings:
        print(f"Found: {job.title} at {job.company}")
```

### Manual Setup and Cleanup

```python
from src.scrapers.linkedin_scraper import LinkedInScraper

# Create scraper instance
scraper = LinkedInScraper()

try:
    # Set up WebDriver
    scraper.setup_driver()
    
    # Scrape jobs
    search_url = "https://www.linkedin.com/jobs/search/?keywords=software%20engineer"
    job_listings = scraper.scrape_jobs_from_url(search_url, max_jobs=5)
    
    # Process results
    print(f"Scraped {len(job_listings)} jobs")
    
finally:
    # Clean up resources
    scraper.cleanup()
```

## Configuration

### ScrapingSettings

The scraper accepts a `ScrapingSettings` object for configuration:

```python
from src.config.config_manager import ScrapingSettings

settings = ScrapingSettings(
    delay_min=1.0,           # Minimum delay between requests (seconds)
    delay_max=3.0,           # Maximum delay between requests (seconds)
    max_jobs_per_session=100, # Maximum jobs to process per session
    user_agent_rotation=True, # Enable user agent rotation
    respect_robots_txt=True,  # Respect robots.txt files
    timeout=30,              # Request timeout (seconds)
    retry_attempts=3         # Number of retry attempts on failure
)
```

### Default Settings

If no settings are provided, the scraper uses these defaults:
- `delay_min`: 1.0 seconds
- `delay_max`: 3.0 seconds
- `max_jobs_per_session`: 100
- `user_agent_rotation`: True
- `respect_robots_txt`: True
- `timeout`: 30 seconds
- `retry_attempts`: 3

## LinkedIn Search URLs

### URL Structure
LinkedIn job search URLs follow this pattern:
```
https://www.linkedin.com/jobs/search/?keywords={keywords}&location={location}&f_JT={job_type}&f_E={experience}&f_WT={work_type}
```

### Common Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `keywords` | `python developer` | Job search keywords |
| `location` | `San Francisco` | Job location |
| `f_JT` | `F` | Job type (F=Full-time, P=Part-time, C=Contract, T=Temporary, I=Internship) |
| `f_E` | `1` | Experience level (1=Entry, 2=Associate, 3=Mid-Senior, 4=Director, 5=Executive) |
| `f_WT` | `2` | Work type (1=On-site, 2=Remote, 3=Hybrid) |

### Sample URLs

```python
# Python developer jobs in San Francisco
url1 = "https://www.linkedin.com/jobs/search/?keywords=python%20developer&location=San%20Francisco%20Bay%20Area&f_JT=F"

# Remote software engineer jobs
url2 = "https://www.linkedin.com/jobs/search/?keywords=software%20engineer&location=Remote&f_JT=F&f_WT=2"

# Entry-level data scientist jobs
url3 = "https://www.linkedin.com/jobs/search/?keywords=data%20scientist&f_E=1&f_JT=F"
```

## Data Models

### JobListing Object

The scraper returns `JobListing` objects with the following attributes:

```python
job = JobListing(
    title="Senior Python Developer",
    company="Tech Corp",
    location="San Francisco, CA",
    job_url="https://www.linkedin.com/jobs/view/123456",
    job_site="linkedin",
    description="Job description...",
    salary_min=80000,
    salary_max=120000,
    job_type=JobType.FULL_TIME,
    experience_level=ExperienceLevel.SENIOR,
    remote_type=RemoteType.HYBRID,
    posted_date=datetime.now()
)
```

### Parsed Data Types

The scraper automatically parses and classifies:

#### Job Types
- `FULL_TIME` - Full-time positions
- `PART_TIME` - Part-time positions
- `CONTRACT` - Contract positions
- `TEMPORARY` - Temporary positions
- `INTERNSHIP` - Internship positions
- `FREELANCE` - Freelance positions

#### Experience Levels
- `ENTRY` - Entry-level positions
- `JUNIOR` - Junior positions
- `MID` - Mid-level positions
- `SENIOR` - Senior positions
- `LEAD` - Lead positions
- `EXECUTIVE` - Executive positions

#### Remote Types
- `ON_SITE` - On-site work
- `REMOTE` - Remote work
- `HYBRID` - Hybrid work

## Error Handling

### Common Errors and Solutions

#### 1. WebDriver Initialization Errors
```python
# Error: ChromeDriver not found
# Solution: webdriver-manager will auto-download
from webdriver_manager.chrome import ChromeDriverManager
```

#### 2. Page Load Timeouts
```python
# Error: Page takes too long to load
# Solution: Increase timeout
settings = ScrapingSettings(timeout=60)
```

#### 3. Element Not Found
```python
# Error: LinkedIn changed their HTML structure
# Solution: Update selectors in LinkedInScraper.SELECTORS
```

#### 4. Rate Limiting
```python
# Error: Too many requests
# Solution: Increase delays
settings = ScrapingSettings(delay_min=5.0, delay_max=10.0)
```

### Error Recovery

The scraper includes built-in error recovery:

```python
# Statistics tracking
stats = scraper.get_statistics()
print(f"Jobs found: {stats['jobs_found']}")
print(f"Jobs processed: {stats['jobs_processed']}")
print(f"Jobs extracted: {stats['jobs_extracted']}")
print(f"Errors encountered: {stats['errors_encountered']}")
```

## Best Practices

### 1. Respectful Scraping
```python
# Use reasonable delays
settings = ScrapingSettings(delay_min=2.0, delay_max=5.0)

# Limit the number of jobs per session
job_listings = scraper.scrape_jobs_from_url(url, max_jobs=20)
```

### 2. Error Handling
```python
try:
    with LinkedInScraper(settings) as scraper:
        job_listings = scraper.scrape_jobs_from_url(url)
except Exception as e:
    print(f"Scraping failed: {e}")
    # Handle error appropriately
```

### 3. Resource Management
```python
# Always use context manager or manual cleanup
with LinkedInScraper() as scraper:
    # Your scraping code here
    pass  # Automatic cleanup
```

### 4. Monitoring
```python
# Track scraping statistics
stats = scraper.get_statistics()
if stats['errors_encountered'] > stats['jobs_extracted'] * 0.1:
    print("Warning: High error rate detected")
```

## Integration with Google Sheets

### Writing Scraped Jobs to Google Sheets

```python
from src.data.google_sheets_manager import GoogleSheetsManager

# Initialize Google Sheets manager
sheets_manager = GoogleSheetsManager()

# Scrape jobs
with LinkedInScraper() as scraper:
    job_listings = scraper.scrape_jobs_from_url(search_url)
    
    # Write to Google Sheets
    for job in job_listings:
        success = sheets_manager.write_job_listing(job)
        if success:
            print(f"Wrote {job.title} to Google Sheets")
```

## Testing

### Run the Test Script
```bash
python test_linkedin_scraper.py
```

### Manual Testing
```python
# Test with a small number of jobs
with LinkedInScraper() as scraper:
    test_url = "https://www.linkedin.com/jobs/search/?keywords=python&location=Remote"
    jobs = scraper.scrape_jobs_from_url(test_url, max_jobs=3)
    
    for job in jobs:
        print(f"Title: {job.title}")
        print(f"Company: {job.company}")
        print(f"Location: {job.location}")
        print("---")
```

## Troubleshooting

### Common Issues

1. **Chrome not installed**: Install Google Chrome browser
2. **Permission errors**: Ensure Chrome can be launched
3. **Network issues**: Check internet connection
4. **LinkedIn changes**: Update selectors if LinkedIn changes their HTML structure

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

with LinkedInScraper() as scraper:
    # Your scraping code
    pass
```

### Selector Updates

If LinkedIn changes their HTML structure, update the selectors in `LinkedInScraper.SELECTORS`:

```python
SELECTORS = {
    'job_cards': 'div[data-job-id]',  # Update this if needed
    'job_title': 'h3.base-search-card__title',  # Update this if needed
    # ... other selectors
}
```

## Legal and Ethical Considerations

### Terms of Service
- Review LinkedIn's Terms of Service before scraping
- Ensure compliance with their usage policies
- Consider using LinkedIn's official API for production use

### Rate Limiting
- Use reasonable delays between requests
- Don't overwhelm LinkedIn's servers
- Monitor for rate limiting responses

### Data Usage
- Only scrape publicly available job listings
- Respect robots.txt files
- Use scraped data responsibly and ethically

## Next Steps

After implementing the LinkedIn scraper:

1. **Add more job sites**: Implement scrapers for Indeed, Glassdoor, etc.
2. **Improve data quality**: Add more sophisticated parsing logic
3. **Add filtering**: Implement job filtering based on criteria
4. **Add deduplication**: Prevent duplicate job listings
5. **Add scheduling**: Automate scraping at regular intervals 