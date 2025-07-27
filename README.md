# AI Job Qualification Screening System

A comprehensive Python-based AI-powered system that analyzes job listings and provides intelligent qualification recommendations for job applications.

## 🎯 Overview

This system helps job seekers efficiently evaluate job opportunities by:
- **AI-Powered Analysis**: Uses Google Gemini AI to analyze job requirements and candidate qualifications
- **Smart Qualification Scoring**: Provides detailed reasoning and confidence scores for job matches
- **Google Sheets Integration**: Tracks applications and analysis results in cloud storage
- **Web Interface**: User-friendly Flask-based frontend for job management
- **Resume Processing**: Analyzes resumes and cover letters for better matching

## 🏗️ Project Structure

```
autoApply-bot/
├── 📁 src/                    # Core source code
│   ├── 📁 ai/                # AI qualification analysis
│   │   └── qualification_analyzer.py
│   ├── 📁 config/            # Configuration management
│   │   ├── config_manager.py
│   │   ├── applicant_profile.py
│   │   └── production_config.py
│   ├── 📁 data/              # Data models and storage
│   │   ├── models.py
│   │   └── google_sheets_manager.py
│   ├── 📁 scrapers/          # Job site scrapers (LinkedIn, etc.)
│   │   ├── base_scraper.py
│   │   ├── linkedin_scraper_enhanced.py
│   │   └── example_scraper.py
│   ├── 📁 automation/        # Application automation logic
│   ├── 📁 utils/             # Utility functions
│   │   ├── logger.py
│   │   ├── session_manager.py
│   │   └── job_link_processor.py
│   └── __init__.py
├── 📁 frontend/              # Web application interface
│   ├── 📁 templates/         # HTML templates
│   ├── 📁 config/            # Frontend configuration
│   ├── 📁 data/              # Frontend data storage
│   ├── 📁 uploads/           # File uploads (resumes, etc.)
│   ├── app.py                # Flask application
│   └── run.py                # Frontend runner
├── 📁 tests/                 # Comprehensive test suites
│   ├── test_*.py             # Unit and integration tests
│   └── README.md             # Test documentation
├── 📁 demos/                 # Demonstration scripts
│   ├── demo_*.py             # Feature demonstrations
│   └── README.md             # Demo documentation
├── 📁 scripts/               # Utility scripts and tools
│   ├── run_*.py              # Production scripts
│   ├── debug_*.py            # Debug tools
│   └── README.md             # Script documentation
├── 📁 config/                # Configuration files
│   ├── settings.json         # Application settings
│   ├── *.json                # API credentials
│   └── README.md             # Config documentation
├── 📁 data/                  # Data storage and samples
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

### 2. Configure Credentials
```bash
# Copy environment template
cp env.template .env

# Edit .env with your credentials
nano .env
```

**Required Environment Variables:**
- `LINKEDIN_USERNAME` - LinkedIn email
- `LINKEDIN_PASSWORD` - LinkedIn password
- `GEMINI_API_KEY` - Google Gemini API key for AI analysis
- `GOOGLE_SHEETS_CREDENTIALS_PATH` - Path to Google Sheets service account JSON
- `GOOGLE_SHEETS_SPREADSHEET_ID` - Your Google Sheets spreadsheet ID

**Optional Configuration:**
- `APPLICANT_*` - Personal information and preferences
- `AUTO_APPLY_*` - Automation settings
- `DELAY_*` - Timing configurations

### 3. Run the Application

#### Web Interface (Recommended)
```bash
# Start the Flask web interface
python scripts/start_frontend.py

# Or run directly
cd frontend
python run.py
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

### **Smart Job Processing**
- **Job Link Processing**: Analyzes individual job URLs
- **Resume Matching**: Compares candidate skills with job requirements
- **Experience Alignment**: Evaluates years of experience and background
- **Skills Analysis**: Identifies skill gaps and matches

### **Data Management**
- **Google Sheets Integration**: Cloud-based application tracking
- **Structured Data Models**: Comprehensive job and application data
- **Export Capabilities**: Multiple export formats
- **Search History**: Track and analyze job search patterns

### **Web Interface**
- **User-Friendly Dashboard**: Modern Flask-based web application
- **Job Management**: View, analyze, and track job applications
- **Profile Management**: Update personal information and preferences
- **Results Visualization**: Clear presentation of AI analysis results

### **Automation Capabilities**
- **Batch Processing**: Analyze multiple job links at once
- **Status Tracking**: Monitor application progress
- **Duplicate Detection**: Prevents duplicate analyses
- **Session Management**: Persistent login and data

## 🔧 Configuration

### **Environment Variables** (`.env`)
```bash
# AI Configuration
GEMINI_API_KEY=your_gemini_api_key

# Google Sheets
GOOGLE_SHEETS_CREDENTIALS_PATH=path/to/credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id

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
- AI qualification system implementation
- Google Sheets integration guide
- LinkedIn scraper documentation
- Filter system implementation

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
- Valid API credentials (Gemini, Google Sheets)

### **Performance Optimization**
- Session reuse and caching
- Rate limiting for API calls
- Resource cleanup
- Error recovery mechanisms

### **Scalability Features**
- Modular component design
- Configurable batch processing
- Efficient data storage
- Optimized AI analysis

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
- **Google Sheets Access**: Verify your service account has proper permissions
- **LinkedIn Login**: Check if your credentials are correct and account is not locked
- **AI Analysis Failures**: Review the logs for specific error messages

### **Debugging**
- Check `logs/` directory for detailed error logs
- Use debug scripts in `scripts/debug_*.py`
- Enable DEBUG logging in environment variables

---

**Built with ❤️ for intelligent job searching and application optimization**

*This system helps you make informed decisions about job opportunities using advanced AI analysis.* 