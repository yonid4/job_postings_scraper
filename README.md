# Job Application Automation System

A comprehensive Python-based web automation tool that scrapes job listings and automatically applies to positions with AI-powered qualification analysis.

## 🏗️ Project Structure

```
autoApply-bot/
├── 📁 src/                    # Core source code
│   ├── 📁 scrapers/          # Job site scrapers (LinkedIn, etc.)
│   ├── 📁 automation/        # Application automation logic
│   ├── 📁 data/             # Data management and storage
│   ├── 📁 config/           # Configuration management
│   ├── 📁 ai/               # AI qualification analysis
│   └── 📁 utils/            # Utility functions
├── 📁 frontend/              # Web application interface
│   ├── 📁 templates/        # HTML templates
│   ├── 📁 static/           # CSS, JS, images
│   └── app.py               # Flask application
├── 📁 tests/                 # Comprehensive test suites
│   ├── test_*.py            # Unit and integration tests
│   └── README.md            # Test documentation
├── 📁 demos/                 # Demonstration scripts
│   ├── demo_*.py            # Feature demonstrations
│   └── README.md            # Demo documentation
├── 📁 scripts/               # Utility scripts and tools
│   ├── run_*.py             # Production scripts
│   ├── debug_*.py           # Debug tools
│   └── README.md            # Script documentation
├── 📁 config/                # Configuration files
│   ├── settings.json        # Application settings
│   ├── *.json               # API credentials
│   └── README.md            # Config documentation
├── 📁 data/                  # Data storage and samples
│   ├── sample_*.txt         # Sample data files
│   └── README.md            # Data documentation
├── 📁 docs/                  # Documentation
│   ├── *.md                 # Feature guides and summaries
│   └── ACTIVE_CONTEXT.md    # Current development context
├── 📁 logs/                  # Application logs
├── 📁 sessions/              # Browser session data
├── 📁 flask_session/         # Web session data
├── 📁 examples/              # Usage examples
├── 📁 .venv/                 # Python virtual environment
├── main.py                   # Main application entry point
├── requirements.txt          # Python dependencies
├── env.template              # Environment variables template
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

Required credentials:
- `LINKEDIN_USERNAME` - LinkedIn email
- `LINKEDIN_PASSWORD` - LinkedIn password
- `OPENAI_API_KEY` - OpenAI API key
- `GOOGLE_SHEETS_CREDENTIALS_FILE` - Google Sheets API credentials

### 3. Run the Application
```bash
# Start the web interface
python scripts/start_frontend.py

# Or run production scraper
python scripts/run_production_scraper.py

# Or run job analysis
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

# Integration tests
python -m pytest tests/test_integration.py

# Filter tests
python -m pytest tests/test_*filter*.py
```

## 🎯 Key Features

### **Intelligent Job Scraping**
- **LinkedIn Integration**: Advanced scraper with filter support
- **Filter Detection**: Automatically uses browser automation when filters are applied
- **Session Management**: Persistent sessions for efficient scraping
- **Anti-Detection**: Stealth techniques to avoid blocking

### **AI-Powered Analysis**
- **Qualification Scoring**: AI analysis of job fit
- **Resume Matching**: Skills and experience alignment
- **Customizable Thresholds**: Adjustable qualification criteria
- **Detailed Reasoning**: AI explanations for recommendations

### **Automation Capabilities**
- **Easy Apply**: Automated application submission
- **Form Filling**: Intelligent form completion
- **Status Tracking**: Application progress monitoring
- **Duplicate Detection**: Prevents duplicate applications

### **Data Management**
- **Google Sheets Integration**: Cloud-based data storage
- **Export Capabilities**: Multiple export formats
- **Search History**: Track and analyze search patterns
- **Favorites System**: Save and organize job listings

## 🔧 Configuration

### **Application Settings** (`config/settings.json`)
- Scraping parameters
- AI analysis settings
- User profile defaults
- System preferences

### **Environment Variables** (`.env`)
- API credentials
- Database connections
- External service configurations

## 📊 Monitoring & Logs

### **Application Logs** (`logs/`)
- Error tracking
- Performance metrics
- Debug information
- User activity logs

### **Session Data** (`sessions/`)
- Browser session cookies
- Authentication tokens
- Persistent login data

## 🛠️ Development

### **Code Organization**
- **Modular Design**: Separate components for different functionalities
- **Type Hints**: Comprehensive type annotations
- **Error Handling**: Robust error management
- **Logging**: Detailed logging for debugging

### **Testing Strategy**
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **Filter Tests**: LinkedIn filter functionality validation
- **Performance Tests**: System performance validation

## 📚 Documentation

### **Feature Guides** (`docs/`)
- LinkedIn scraper implementation
- AI qualification system
- Google Sheets integration
- Filter system documentation

### **API Documentation**
- Component interfaces
- Configuration options
- Usage examples
- Troubleshooting guides

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

### **Requirements**
- Python 3.9+
- Chrome browser
- Stable internet connection
- Valid API credentials

### **Performance Optimization**
- Session reuse
- Rate limiting
- Resource cleanup
- Error recovery

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the documentation in `docs/`
2. Review existing issues
3. Create a new issue with detailed information
4. Include logs and error messages

---

**Built with ❤️ for efficient job searching and application automation** 