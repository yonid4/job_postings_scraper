# AI Job Qualification Screening System

A Python-based AI-powered system that analyzes job descriptions against user qualifications and saves qualifying jobs to Supabase.

## 🚀 Project Overview

This system helps job seekers efficiently screen job opportunities by:
- **Job Link Processing**: Extracting job information from user-provided URLs
- **AI Qualification Analysis**: Using Google Gemini to analyze job descriptions against user qualifications
- **Smart Scoring**: Providing 0-100 qualification scores with detailed reasoning

- **User Review**: Allowing manual override of AI recommendations
- **Customizable AI Logic**: Easy to implement your own analysis algorithms

## 📋 Features

### Phase 1: Core System (Current)
- ✅ Configuration management with user profiles
- ✅ AI-powered qualification analysis using Google Gemini
- ✅ Job link processing for multiple job sites

- ✅ Comprehensive logging and error handling
- ✅ Type hints and comprehensive documentation
- ✅ Customizable AI analysis logic

### Phase 2: Enhanced AI Analysis (Next)
- 🔄 Advanced qualification scoring algorithms
- 🔄 Skills matching and transferability analysis
- 🔄 Experience level alignment
- 🔄 Education requirements analysis

### Phase 3: User Interface (Planned)
- 🔄 Web-based job link input interface
- 🔄 Qualification review dashboard
- 🔄 Manual override capabilities
- 🔄 Batch processing interface

### Phase 4: Advanced Features (Planned)
- 🔄 Multi-user support
- 🔄 Advanced analytics and reporting
- 🔄 Email notifications
- 🔄 Integration with job application platforms

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.9 or higher
- pip (Python package installer)
- Git
- Google Gemini API key

### 1. Clone the Repository
```bash
git clone <repository-url>
cd autoApply-bot
```

### 2. Set Up Python Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root:
```bash
# Google Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here


```

### 5. Configure User Profile
Edit `config/settings.json` to set your qualification profile:
```json
{
  "user_profile": {
    "years_of_experience": 3,
    "has_college_degree": true,
    "field_of_study": "Computer Science",
    "experience_level": "mid",
    "additional_skills": ["Python", "JavaScript", "React"],
    "preferred_locations": ["San Francisco, CA", "New York, NY"],
    "salary_min": 80000,
    "salary_max": 150000
  }
}
```

### 6. Verify Installation
```bash
python main.py
```

You should see output similar to:
```
============================================================
AI Job Qualification Screening System
============================================================
✅ Logging system initialized
✅ Configuration loaded successfully
   - User experience: 3 years
   - Education: Yes
   - AI model: gemini-1.5-pro
   - Qualification threshold: 70
🚀 AI Job Qualification Screening System v2.0.0 initialized successfully!

🎯 Running System Demonstration:
📊 Demonstrating Data Models:
   ✅ Created job listing: Software Engineer at Tech Corp
   ✅ Created qualification result for Software Engineer
      Score: 85, Status: qualified
   ✅ Created scraping session: 25 jobs found, 15 qualified
...
```

## 📁 Project Structure

```
autoApply-bot/
├── src/
│   ├── ai/                    # AI qualification analysis
│   │   ├── __init__.py
│   │   └── qualification_analyzer.py  # Customizable AI logic
│   ├── config/                # Configuration management
│   │   ├── __init__.py
│   │   ├── config_manager.py
│   │   ├── applicant_profile.py
│   │   └── production_config.py
│   ├── data/                  # Data models and storage
│   │   ├── __init__.py
│   │   ├── models.py

│   ├── scrapers/              # Web scraping (legacy)
│   │   ├── __init__.py
│   │   ├── base_scraper.py
│   │   ├── linkedin_scraper.py
│   │   └── example_scraper.py
│   └── utils/                 # Utility functions
│       ├── __init__.py
│       ├── logger.py
│       └── job_link_processor.py
├── config/                    # Configuration files
│   └── settings.json
├── data/                      # Local data storage
├── logs/                      # Application logs
├── tests/                     # Unit tests
├── main.py                    # Main application entry point
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🔧 Configuration

### User Profile Settings
The system uses your qualification profile to analyze job matches:

- **Years of Experience**: Your total professional experience
- **Education**: College degree status and field of study
- **Experience Level**: Entry, Junior, Mid, Senior
- **Additional Skills**: Technologies, tools, and certifications
- **Preferred Locations**: Cities or regions you're interested in
- **Salary Range**: Your expected compensation range

### AI Settings
Configure the AI analysis behavior:

- **Model**: Google Gemini model to use (gemini-1.5-pro recommended)
- **Qualification Threshold**: Minimum score (0-100) to consider qualified
- **Max Tokens**: Maximum response length from AI
- **Temperature**: Response creativity (lower = more consistent)



## 🚀 Usage

### Basic Usage
```python
from main import JobQualificationSystem

# Initialize the system
system = JobQualificationSystem()

# Process job links
job_links = [
    "https://linkedin.com/jobs/view/123456789",
    "https://indeed.com/viewjob?jk=abcdef123",
    "https://glassdoor.com/Job/san-francisco-software-engineer-jobs-SRCH_IL.0,13_IC1147401_KO14,31.htm"
]

# Analyze qualifications
results = system.process_job_links(job_links)

# Review results
for result in results:
    print(f"Job: {result.job_title}")
    print(f"Score: {result.qualification_score}/100")
    print(f"Status: {result.qualification_status.value}")
    print(f"Reasoning: {result.ai_reasoning}")
    print("---")
```

### Command Line Usage
```bash
# Run the demo
python main.py

# Process specific job links (future feature)
python main.py --links "url1,url2,url3"
```

## 🤖 Customizing AI Analysis

The system is designed to be easily customizable. You can implement your own analysis logic by overriding methods in the `QualificationAnalyzer` class:

### Custom Analysis Logic
```python
from src.ai.qualification_analyzer import QualificationAnalyzer

class MyCustomAnalyzer(QualificationAnalyzer):
    def custom_analysis_logic(self, request):
        """Implement your own analysis logic here."""
        # Your custom scoring algorithm
        score = self._my_custom_scoring(request)
        
        # Your custom reasoning
        reasoning = self._my_custom_reasoning(request)
        
        return AnalysisResponse(
            qualification_score=score,
            ai_reasoning=reasoning,
            # ... other fields
        )
    
    def _my_custom_scoring(self, request):
        """Your custom scoring algorithm."""
        # Example: Rule-based scoring
        score = 0
        
        # Add points for matching skills
        for skill in request.user_profile.additional_skills:
            if skill.lower() in request.job_description.lower():
                score += 15
        
        # Add points for experience match
        if str(request.user_profile.years_of_experience) in request.job_description:
            score += 20
        
        return min(100, score)
```

### Custom Prompt Engineering
```python
def _create_analysis_prompt(self, request):
    """Customize the prompt for your specific needs."""
    return f"""
    Your custom prompt here...
    
    Job: {request.job_title}
    Company: {request.company}
    Description: {request.job_description}
    
    Your custom analysis instructions...
    """
```

### Custom Response Parsing
```python
def _parse_ai_response(self, response):
    """Customize how AI responses are parsed."""
    # Your custom parsing logic
    return {
        'qualification_score': your_score_calculation,
        'ai_reasoning': your_reasoning_extraction,
        # ... other fields
    }
```



The system creates a "Qualified Jobs" worksheet with columns:
- Job Title
- Company Name
- Job URL
- Qualification Score (0-100)
- AI Reasoning
- Required Experience
- Education Requirements
- Key Skills Mentioned
- Analysis Date
- User Decision (Approved/Rejected/Pending)

## 🤖 AI Analysis Features

### Qualification Scoring
The AI provides scores from 0-100 based on:
- **90-100**: Highly Qualified - Perfect match
- **70-89**: Qualified - Good match with minor gaps
- **50-69**: Somewhat Qualified - Some relevant experience
- **30-49**: Marginally Qualified - Limited relevant experience
- **0-29**: Not Qualified - Significant mismatch

### Analysis Components
- **Experience Level Alignment**: Matches your experience to job requirements
- **Education Requirements**: Analyzes degree and field requirements
- **Skills Matching**: Identifies matching and missing skills
- **Potential Concerns**: Highlights areas that might be challenging
- **Detailed Reasoning**: Provides specific explanations for the score

## 🔒 Privacy & Security

- **No Data Storage**: Job descriptions are not permanently stored
- **API Security**: Google Gemini API calls use secure authentication
- **Local Processing**: All analysis happens locally with secure API calls
- **Configurable Logging**: Control what information is logged

## 🧪 Testing

Run the test suite:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_qualification_analyzer.py
```

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the documentation
2. Review existing issues
3. Create a new issue with detailed information

## 🔄 Version History

### v2.0.0 (Current)
- Complete system refactor to AI qualification screening
- Google Gemini integration for job analysis
- User profile management

- Job link processing for multiple sites
- Customizable AI analysis logic

### v1.0.0 (Legacy)
- Original job application automation system
- Web scraping foundation
- Application tracking
 