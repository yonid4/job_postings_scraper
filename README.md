# AI Job Qualification Screening System

A comprehensive Python-based AI-powered system that analyzes job listings and provides intelligent qualification recommendations for job applications.

## 🎯 Overview

This system helps job seekers efficiently evaluate job opportunities by:
- **AI-Powered Analysis**: Uses Google Gemini AI to analyze job requirements and candidate qualifications
- **Smart Qualification Scoring**: Provides detailed reasoning and confidence scores for job matches
- **Supabase Integration**: Secure user authentication and cloud data storage with row-level security
- **Enhanced LinkedIn Scraping**: Advanced scraping with filter support, CAPTCHA handling, and anti-detection measures
- **Resume Processing**: Analyzes resumes and cover letters for better matching
- **Professional Job Tracker**: Comprehensive application tracking system similar to Simplify
- **Web Interface**: User-friendly Flask-based frontend for job management
- **Emergency Performance Optimization**: Ultra-fast job loading with aggressive caching

## 🏗️ Project Structure

```
autoApply-bot/
├── 📁 src/                    # Core source code
│   ├── 📁 ai/                # AI qualification analysis
│   │   └── qualification_analyzer.py
│   ├── 📁 auth/              # Authentication and user management
│   │   ├── auth_context.py
│   │   ├── flask_integration.py
│   │   ├── profile_integration.py
│   │   └── supabase_auth_manager.py
│   ├── 📁 config/            # Configuration management
│   │   ├── config_manager.py
│   │   ├── applicant_profile.py
│   │   └── production_config.py
│   ├── 📁 data/              # Data models and storage
│   │   ├── models.py
│   │   ├── supabase_manager.py
│   │   ├── resume_manager.py
│   │   ├── job_tracker.py
│   │   ├── emergency_queries.py
│   │   └── user_profile_manager.py
│   ├── 📁 scrapers/          # Job site scrapers
│   │   ├── base_scraper.py
│   │   ├── linkedin_scraper_enhanced.py
│   │   ├── linkedin_api_scraper.py
│   │   └── example_scraper.py
│   ├── 📁 utils/             # Utility functions
│   │   ├── logger.py
│   │   ├── session_manager.py
│   │   ├── job_link_processor.py
│   │   ├── captcha_handler.py
│   │   └── search_strategy_manager.py
│   ├── 📁 debug/             # Performance monitoring
│   │   └── performance_profiler.py
│   └── __init__.py
├── 📁 frontend/              # Web application interface
│   ├── 📁 templates/         # HTML templates
│   ├── 📁 config/            # Frontend configuration
│   ├── 📁 data/              # Frontend data storage
│   ├── 📁 uploads/           # File uploads (resumes, etc.)
│   ├── app_supabase.py       # Main Flask application
│   ├── auth_routes.py        # Authentication routes
│   ├── profile_routes.py     # Profile management routes
│   ├── resume_routes.py      # Resume processing routes
│   └── run.py                # Frontend runner
├── 📁 tests/                 # Comprehensive test suites
│   ├── test_*.py             # Unit and integration tests
│   └── README.md             # Test documentation
├── 📁 config/                # Configuration files
│   ├── settings.json         # Application settings
│   ├── *.json                # API credentials
│   └── README.md             # Config documentation
├── 📁 data/                  # Legacy data storage (migrated to Supabase)
├── 📁 docs/                  # Documentation
│   ├── *.md                  # Feature guides and summaries
│   └── ACTIVE_CONTEXT.md     # Current development context
├── 📁 logs/                  # Application logs
├── 📁 sessions/              # Browser session data
├── 📁 flask_session/         # Web session data
├── 📁 examples/              # Usage examples
├── main.py                   # Main application entry point
├── requirements.txt          # Python dependencies
├── env.template              # Environment variables template
├── package.json              # Node.js dependencies (if any)
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Clone the repository
git clone <repository-url>
cd autoApply-bot

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup Database
Before running the application, you need to set up the database schema in your Supabase project:

```bash
# Navigate to the database migrations folder
cd database_migrations

# Execute the SQL files in your Supabase SQL editor or using psql
# Run them in this order to respect foreign key dependencies:
```

**Required Database Tables** (execute in order):
1. `jobs_schema.sql` - Core jobs table with AI evaluation data
2. `user_profiles_schema.sql` - User profile information and preferences
3. `user_resume_schema.sql` - Resume storage and processing data
4. `job_searches_schema.sql` - Search history and filters
5. `applications_schema.sql` - Job application tracking
6. `job_favorites_schema.sql` - User favorite job bookmarks

**Database Setup Options:**
- **Supabase Dashboard**: Copy and paste each SQL file content into your Supabase project's SQL editor
- **Command Line**: Use `psql` to execute the files if you have direct database access
- **Application**: The system includes automatic database migration capabilities

### 3. Configure Credentials
```bash
# Copy environment template
cp env.template .env

# Edit .env with your credentials
nano .env
```

**Required Environment Variables:**
- `SUPABASE_URL` - Your Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Supabase anonymous key
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key (for admin operations)
- `GEMINI_API_KEY` - Google Gemini API key for AI analysis


**Optional Configuration:**
- `APPLICANT_*` - Personal information and preferences
- `AUTO_APPLY_*` - Automation settings
- `DELAY_*` - Timing configurations
- `TESTING_MODE` - Set to true for development (bypasses email verification)

### 4. Run the Application

#### Web Interface (Recommended)
```bash
# Start the Flask web interface
cd frontend
python run.py

# Or run directly
python app_supabase.py
```

#### Command Line Interface
```bash
# Run the main application
python main.py

# Run production scraper
python scripts/run_production_scraper.py

# Run job analysis
python scripts/run_job_analysis.py
```

## 🧪 Testing

### Run All Tests
```bash
python -m pytest tests/
```

### Run Specific Test Categories
```bash
# LinkedIn scraper tests
python -m pytest tests/test_linkedin_*.py

# AI qualification tests
python -m pytest tests/test_qualification_*.py

# Authentication tests
python -m pytest tests/test_auth_*.py

# Integration tests
python -m pytest tests/test_integration.py

# Filter tests
python -m pytest tests/test_*filter*.py
```

## 🎯 Key Features

### **AI-Powered Job Analysis**
- **Google Gemini Integration**: Advanced AI analysis using Google's latest model
- **Qualification Scoring**: Intelligent assessment of job-candidate fit
- **Detailed Reasoning**: AI explanations for qualification decisions
- **Confidence Metrics**: Probability scores for job matches
- **Customizable Thresholds**: Adjustable qualification criteria

### **Enhanced LinkedIn Scraping**
- **Persistent Sessions**: Maintains browser sessions for consistent scraping
- **Advanced Filtering**: Supports date posted, work arrangement, experience level, and job type filters
- **CAPTCHA Handling**: Automatic detection and user-friendly manual completion
- **Anti-Detection Measures**: Stealth techniques to avoid detection
- **Interface Detection**: Works with both old and new LinkedIn interfaces
- **Search Strategy Management**: Intelligent selection of scraping methods

### **Supabase Integration**
- **User Authentication**: Secure email/password registration with email verification
- **Profile Management**: Automatic profile creation and management
- **Cloud Storage**: Secure storage for jobs, applications, and search history
- **Row Level Security**: Users can only access their own data
- **Real-time Updates**: Live data synchronization
- **User Profiles**: Complete profile management with skills, experience, and preferences

### **Professional Job Tracker**
- **Application Status Tracking**: Complete lifecycle management from application to offer
- **Enhanced Analytics Dashboard**: Application funnel visualization and response rate analysis
- **Advanced Filtering System**: Multi-criteria filtering with quick filters and bulk operations
- **Status-Based Color Coding**: Professional color system for application statuses
- **Bulk Operations**: Mass status updates and job management
- **Application Timeline**: Visual progress through application stages
- **Response Rate Analytics**: Company-specific response metrics
- **Interview Pipeline**: Track interview stages and scheduling

### **Resume Processing**
- **AI-Powered Analysis**: Analyzes resume content for skill extraction
- **Cover Letter Generation**: Creates personalized cover letters
- **Skill Matching**: Compares resume skills with job requirements
- **Experience Alignment**: Evaluates years of experience and background
- **Supabase Storage**: Secure cloud storage for resume files

### **Smart Job Processing**
- **Job Link Processing**: Analyzes individual job URLs
- **Resume Matching**: Compares candidate skills with job requirements
- **Experience Alignment**: Evaluates years of experience and background
- **Skills Analysis**: Identifies skill gaps and matches
- **Duplicate Detection**: Prevents duplicate job applications

### **Data Management**

- **Supabase Database**: Primary data storage with real-time sync
- **Structured Data Models**: Comprehensive job and application data
- **Export Capabilities**: Multiple export formats
- **Search History**: Track and analyze job search patterns
- **Job Favorites**: Save and manage favorite job listings

### **Web Interface**
- **User-Friendly Dashboard**: Modern Flask-based web application
- **Job Management**: View, analyze, and track job applications
- **Profile Management**: Update personal information and preferences
- **Results Visualization**: Clear presentation of AI analysis results
- **Authentication**: Secure login and registration system
- **Emergency Performance**: Ultra-fast job loading with aggressive caching
- **Professional Job Tracker**: Comprehensive application tracking system

### **Emergency Performance Optimization**
- **Ultra-Fast Loading**: <2 second job page load times
- **Aggressive Caching**: Intelligent caching for performance
- **Memory Optimization**: Efficient memory usage and monitoring
- **Performance Profiling**: Real-time performance monitoring
- **Emergency Routes**: Optimized routes for critical performance scenarios

### **Automation Capabilities**
- **Batch Processing**: Analyze multiple job links at once
- **Status Tracking**: Monitor application progress
- **Duplicate Detection**: Prevents duplicate analyses
- **Session Management**: Persistent login and data
- **Application Tracking**: Complete application lifecycle management

## 🔧 Configuration

### **Environment Variables** (`.env`)
```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here

# AI Configuration
GEMINI_API_KEY=your_gemini_api_key



# Flask Configuration
FLASK_SECRET_KEY=your-secret-key-change-this

# Testing Mode (Development)
TESTING_MODE=true

# Applicant Profile
APPLICANT_FIRST_NAME=YourName
APPLICANT_EMAIL=your_email@example.com
APPLICANT_SKILLS=Python, JavaScript, React
APPLICANT_YEARS_EXPERIENCE=3

# Application Preferences
AUTO_APPLY_ENABLED=true
MAX_APPLICATIONS_PER_SESSION=5
```

### **Application Settings** (`config/settings.json`)
- AI analysis parameters
- Scraping configurations
- User profile defaults
- System preferences

## 📊 Monitoring & Logs

### **Application Logs** (`logs/`)
- Error tracking and debugging
- Performance metrics
- AI analysis results
- User activity logs

### **Session Data** (`sessions/`)
- Browser session cookies
- Authentication tokens
- Persistent login data

### **Performance Monitoring**
- Real-time performance profiling
- Memory usage tracking
- Query performance analysis
- Emergency performance alerts

## 🛠️ Development

### **Code Organization**
- **Modular Architecture**: Separate components for different functionalities
- **Type Hints**: Comprehensive type annotations throughout
- **Error Handling**: Robust error management with specific exceptions
- **Logging**: Detailed logging for debugging and monitoring

### **Testing Strategy**
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow validation
- **AI Tests**: Qualification analysis validation
- **Performance Tests**: System performance benchmarks

### **Code Quality**
- **Black**: Code formatting
- **Flake8**: Linting
- **MyPy**: Type checking
- **Pytest**: Testing framework

## 📚 Documentation

### **Feature Guides** (`docs/`)
- Supabase integration guide
- Enhanced LinkedIn scraper documentation
- CAPTCHA handling implementation
- Resume processing system
- Authentication system guide
- Emergency performance optimization
- User profile management
- Job tracker transformation guide
- Enhanced analytics dashboard guide

### **API Documentation**
- Component interfaces and usage
- Configuration options
- Troubleshooting guides
- Best practices

## 🔒 Security

### **Credential Management**
- Environment variable storage
- Secure API key handling
- Session isolation
- Access control

### **Data Protection**
- Encrypted storage
- Secure transmission
- Privacy compliance
- Audit logging

## 🚀 Production Deployment

### **System Requirements**
- Python 3.9+
- Chrome browser (for scraping)
- Stable internet connection
- Valid API credentials (Gemini, Supabase)

### **Performance Optimization**
- Session reuse and caching
- Rate limiting for API calls
- Resource cleanup
- Error recovery mechanisms
- Emergency performance optimization

### **Scalability Features**
- Modular component design
- Configurable batch processing
- Efficient data storage
- Optimized AI analysis
- Supabase cloud scaling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the coding standards
4. Add tests for new functionality
5. Ensure all tests pass (`python -m pytest`)
6. Submit a pull request with detailed description

### **Development Setup**
```bash
# Install development dependencies
pip install -r requirements.txt

# Run code formatting
black src/ tests/

# Run linting
flake8 src/ tests/

# Run type checking
mypy src/

# Run tests
python -m pytest tests/
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### **Getting Help**
1. Check the documentation in `docs/`
2. Review existing issues in the repository
3. Create a new issue with detailed information
4. Include logs and error messages

### **Common Issues**
- **API Key Issues**: Ensure your Gemini API key is valid and has sufficient quota
- **Supabase Setup**: Verify your Supabase project is properly configured
- **LinkedIn Login**: Check if your credentials are correct and account is not locked
- **CAPTCHA Challenges**: Complete manual verification when prompted
- **AI Analysis Failures**: Review the logs for specific error messages
- **Performance Issues**: Use emergency performance routes for slow loading
- **Job Tracker Issues**: Check application status updates and filter settings

### **Debugging**
- Check `logs/` directory for detailed error logs
- Use debug scripts in `scripts/debug_*.py`
- Enable DEBUG logging in environment variables
- Use emergency performance monitoring for slow queries

---

**Built with ❤️ for intelligent job searching and application optimization**

*This system helps you make informed decisions about job opportunities using advanced AI analysis and professional application tracking.* 