# Base Scraper Interface Guide

## Overview

The `BaseScraper` class provides a comprehensive, standardized interface for implementing job site scrapers. It includes built-in error handling, rate limiting, logging, and session management to ensure robust and respectful web scraping.

## Key Features

### 🔧 **Built-in Functionality**
- **Rate Limiting**: Configurable delays and request frequency limits
- **Error Handling**: Comprehensive error tracking and recovery
- **Logging**: Integrated logging with performance metrics
- **Session Management**: Automatic session tracking and cleanup
- **Configuration Validation**: Built-in config validation
- **Performance Monitoring**: Request counting and timing metrics

### 🛡️ **Anti-Detection Measures**
- Random delays between requests
- User agent rotation support
- Proxy support (configurable)
- Respectful scraping practices
- Robots.txt compliance

### 📊 **Data Structures**
- `ScrapingResult`: Encapsulates scraping operation results
- `ScrapingConfig`: Comprehensive configuration management
- Performance metrics and warnings tracking

## Core Components

### BaseScraper Class

The main abstract class that all scrapers must inherit from:

```python
class BaseScraper(ABC):
    def __init__(self, config: ScrapingConfig) -> None:
        # Initialize with validated configuration
        
    @abstractmethod
    def scrape_jobs(self, keywords: List[str], location: str, **kwargs) -> ScrapingResult:
        # Main scraping method - MUST be implemented
        
    @abstractmethod
    def get_job_details(self, job_url: str) -> Optional[JobListing]:
        # Get detailed job information - MUST be implemented
        
    @abstractmethod
    def build_search_url(self, keywords: List[str], location: str, **kwargs) -> str:
        # Build search URL - MUST be implemented
        
    @abstractmethod
    def extract_job_listings_from_page(self, page_content: Any) -> List[JobListing]:
        # Extract jobs from page - MUST be implemented
        
    @abstractmethod
    def extract_job_details_from_page(self, page_content: Any, job_url: str) -> Optional[JobListing]:
        # Extract job details from page - MUST be implemented
```

### ScrapingConfig Class

Comprehensive configuration for scraper behavior:

```python
@dataclass
class ScrapingConfig:
    # Rate limiting
    delay_min: float = 1.0
    delay_max: float = 3.0
    max_requests_per_minute: int = 20
    
    # Timeouts
    page_load_timeout: int = 30
    element_wait_timeout: int = 10
    request_timeout: int = 15
    
    # Behavior settings
    max_jobs_per_session: int = 100
    respect_robots_txt: bool = True
    retry_failed_requests: bool = True
    max_retries: int = 3
    
    # Anti-detection
    use_random_delays: bool = True
    rotate_user_agents: bool = True
    use_proxy: bool = False
    
    # Site-specific settings
    site_name: str = ""
    base_url: str = ""
    search_url_template: str = ""
```

### ScrapingResult Class

Result encapsulation with comprehensive metadata:

```python
@dataclass
class ScrapingResult:
    success: bool
    jobs: List[JobListing]
    session: ScrapingSession
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    warnings: List[str] = field(default_factory=list)
    performance_metrics: Optional[Dict[str, float]] = None
```

## Implementation Guide

### 1. Basic Scraper Structure

```python
from src.scrapers.base_scraper import BaseScraper, ScrapingConfig, ScrapingResult
from src.data.models import JobListing

class MyJobSiteScraper(BaseScraper):
    def __init__(self, config: ScrapingConfig):
        super().__init__(config)
        # Initialize any site-specific attributes
        
    def scrape_jobs(self, keywords: List[str], location: str, **kwargs) -> ScrapingResult:
        # Start session
        self.session = self.start_session(keywords, location)
        
        try:
            # Build search URL
            search_url = self.build_search_url(keywords, location, **kwargs)
            
            # Navigate to search page
            page_content = self._get_page_content(search_url)
            
            # Extract job listings
            jobs = self.extract_job_listings_from_page(page_content)
            
            # Update session
            self.session.jobs_found = len(jobs)
            self.session.jobs_processed = len(jobs)
            
            return ScrapingResult(
                success=True,
                jobs=jobs,
                session=self.session,
                metadata={"search_url": search_url}
            )
            
        except Exception as e:
            self.handle_error(e, "job scraping", search_url if 'search_url' in locals() else "")
            return ScrapingResult(
                success=False,
                jobs=[],
                session=self.session,
                error_message=str(e)
            )
        finally:
            self.finish_session()
    
    def get_job_details(self, job_url: str) -> Optional[JobListing]:
        try:
            self.rate_limit()  # Apply rate limiting
            page_content = self._get_page_content(job_url)
            return self.extract_job_details_from_page(page_content, job_url)
        except Exception as e:
            self.handle_error(e, "job details extraction", job_url)
            return None
    
    def build_search_url(self, keywords: List[str], location: str, **kwargs) -> str:
        # Implement URL building logic for your job site
        pass
    
    def extract_job_listings_from_page(self, page_content: Any) -> List[JobListing]:
        # Implement job extraction logic
        pass
    
    def extract_job_details_from_page(self, page_content: Any, job_url: str) -> Optional[JobListing]:
        # Implement job details extraction logic
        pass
```

### 2. Configuration Setup

```python
def create_my_scraper() -> MyJobSiteScraper:
    config = ScrapingConfig(
        site_name="my_job_site",
        base_url="https://myjobsite.com",
        delay_min=2.0,
        delay_max=5.0,
        max_requests_per_minute=15,
        max_jobs_per_session=50,
        respect_robots_txt=True,
        use_random_delays=True,
        log_level="INFO"
    )
    
    return MyJobSiteScraper(config)
```

### 3. Usage Example

```python
# Create scraper
scraper = create_my_scraper()

# Scrape jobs
result = scraper.scrape_jobs(
    keywords=["python", "developer"],
    location="Remote",
    experience_level="senior"
)

if result.success:
    print(f"Found {len(result.jobs)} jobs")
    
    # Get details for first job
    if result.jobs:
        details = scraper.get_job_details(result.jobs[0].job_url)
        if details:
            print(f"Job title: {details.title}")
            print(f"Company: {details.company}")
            print(f"Salary: ${details.salary_min:,} - ${details.salary_max:,}")
else:
    print(f"Scraping failed: {result.error_message}")

# Cleanup
scraper.cleanup()
```

## Built-in Features

### Rate Limiting

The base scraper automatically handles rate limiting:

```python
# Apply rate limiting between requests
self.rate_limit()

# Rate limiting is also applied automatically in:
# - scrape_jobs()
# - get_job_details()
# - extract_job_listings_from_page()
```

### Error Handling

Comprehensive error handling with context:

```python
try:
    # Your scraping logic
    pass
except Exception as e:
    self.handle_error(e, "context description", url)
    # Error is logged and session error count is incremented
```

### Session Management

Automatic session tracking:

```python
# Start session (called automatically in scrape_jobs)
self.session = self.start_session(keywords, location)

# Session tracks:
# - Jobs found/processed
# - Errors encountered
# - Performance metrics
# - Duration

# Finish session (called automatically)
self.finish_session()
```

### Performance Monitoring

Built-in performance tracking:

```python
# Get performance metrics
metrics = scraper.get_performance_metrics()
print(f"Requests: {metrics['requests_count']}")
print(f"Duration: {metrics['total_duration']:.2f}s")
print(f"Jobs found: {metrics['jobs_found']}")
print(f"Errors: {metrics['errors_encountered']}")
```

## Utility Functions

### Text Processing

```python
from src.scrapers import sanitize_text, extract_salary_range, is_valid_url

# Clean text from web pages
clean_text = sanitize_text("  Hello   World  ")  # "Hello World"

# Extract salary information
min_sal, max_sal = extract_salary_range("$50,000 - $80,000")  # (50000, 80000)

# Validate URLs
is_valid = is_valid_url("https://example.com")  # True
```

### Retry Logic

```python
# Retry operations with exponential backoff
result = self.retry_operation(
    self._get_page_content,
    url,
    max_retries=3
)
```

## Best Practices

### 1. Respectful Scraping
- Always use rate limiting
- Respect robots.txt
- Use appropriate delays
- Don't overwhelm servers

### 2. Error Handling
- Always wrap scraping logic in try/catch
- Use `self.handle_error()` for logging
- Provide meaningful error messages
- Implement retry logic for transient failures

### 3. Configuration
- Validate all configuration parameters
- Use reasonable defaults
- Document configuration options
- Test with different config values

### 4. Logging
- Use appropriate log levels
- Include context in log messages
- Log performance metrics
- Track errors and warnings

### 5. Testing
- Test with various input combinations
- Test error conditions
- Test rate limiting behavior
- Test configuration validation

## Example Implementation

See `src/scrapers/example_scraper.py` for a complete example implementation that demonstrates all the features and best practices.

## Testing

Use the provided test framework:

```python
# Run foundation tests
python3 tests/test_scraping_foundation.py

# Test your specific scraper
python3 tests/test_my_scraper.py
```

## Integration

The base scraper integrates seamlessly with the existing system:

- **Configuration**: Uses the existing config management system
- **Logging**: Integrates with the centralized logging system
- **Data Models**: Uses the existing JobListing and ScrapingSession models
- **Google Sheets**: Results can be exported to Google Sheets
- **Main Application**: Works with the main automation system

This foundation provides everything needed to build robust, maintainable job scrapers that follow best practices and integrate well with the overall system. 