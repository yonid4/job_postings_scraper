# Production Setup Guide

This guide provides step-by-step instructions for setting up the LinkedIn Job Automation System for production use with secure credential management.

## 🚀 Quick Start

1. **Set up environment variables** (see [Environment Configuration](#environment-configuration))
2. **Install dependencies** (see [Dependencies](#dependencies))
3. **Run the production scraper** (see [Running the Scraper](#running-the-scraper))

## 📋 Prerequisites

- Python 3.9 or higher
- Chrome browser installed
- LinkedIn account
- Google Sheets API access

## 🔧 Environment Configuration

### Required Environment Variables

Set these environment variables before running the scraper:

#### LinkedIn Credentials
```bash
export LINKEDIN_USERNAME="your_email@example.com"
export LINKEDIN_PASSWORD="your_linkedin_password"
```

#### Google Sheets Configuration
```bash
export GOOGLE_SHEETS_CREDENTIALS_PATH="path/to/your/service-account.json"
export GOOGLE_SHEETS_SPREADSHEET_ID="your_spreadsheet_id"
```

### Optional Environment Variables

```bash
# Scraping configuration
export MAX_JOBS_PER_SESSION="10"          # Default: 10
export DELAY_MIN="3.0"                    # Default: 3.0 seconds
export DELAY_MAX="6.0"                    # Default: 6.0 seconds
export ELEMENT_WAIT_TIMEOUT="20"          # Default: 20 seconds
```

### Using .env File (Recommended)

Create a `.env` file in the project root:

```bash
# LinkedIn Credentials
LINKEDIN_USERNAME=your_email@example.com
LINKEDIN_PASSWORD=your_linkedin_password

# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS_PATH=auto-apply-bot-466218-5a1d69f23d44.json
GOOGLE_SHEETS_SPREADSHEET_ID=1JRbxQYOWlVLuSgv4uhfM2ljfiiBydYsD6fj_0geYRQk

# Scraping Configuration (Optional)
MAX_JOBS_PER_SESSION=10
DELAY_MIN=3.0
DELAY_MAX=6.0
ELEMENT_WAIT_TIMEOUT=20
```

**Important**: Add `.env` to your `.gitignore` file to prevent committing sensitive credentials:

```bash
echo ".env" >> .gitignore
```

## 📦 Dependencies

### Install Python Dependencies

```bash
# Activate virtual environment (if using one)
source .venv/bin/activate

# Install required packages
pip install -r requirements.txt

# Install python-dotenv for .env file support (optional but recommended)
pip install python-dotenv
```

### Chrome Browser

Ensure Chrome browser is installed on your system. The scraper uses ChromeDriver which is automatically managed by `webdriver-manager`.

## 🔐 Google Sheets Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Sheets API

### 2. Create Service Account

1. Go to "IAM & Admin" > "Service Accounts"
2. Click "Create Service Account"
3. Fill in the details:
   - **Name**: `linkedin-job-scraper`
   - **Description**: `Service account for LinkedIn job scraping`
4. Click "Create and Continue"
5. Skip role assignment (we'll do this manually)
6. Click "Done"

### 3. Generate JSON Key

1. Click on the created service account
2. Go to "Keys" tab
3. Click "Add Key" > "Create new key"
4. Select "JSON" format
5. Download the JSON file
6. Place it in your project directory (e.g., `auto-apply-bot-466218-5a1d69f23d44.json`)

### 4. Create Google Sheets

1. Go to [Google Sheets](https://sheets.google.com/)
2. Create a new spreadsheet
3. Note the spreadsheet ID from the URL: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`
4. Share the spreadsheet with your service account email (found in the JSON file)

### 5. Set Permissions

The service account needs edit permissions on the spreadsheet. The scraper will automatically create the required worksheets with proper headers.

## 🏃‍♂️ Running the Scraper

### Production Scraper

Run the production scraper with live LinkedIn data:

```bash
python3 run_production_scraper.py
```

### Demo Scraper (Sample Data)

Run the demo scraper with sample data (no credentials required):

```bash
python3 demo_comprehensive_job_extraction.py
```

## 📊 Monitoring and Logs

### Console Output

The production scraper provides comprehensive real-time monitoring:

```
🚀 Initializing Production LinkedIn Job Scraper...

============================================================
PRODUCTION CONFIGURATION SUMMARY
============================================================
✅ LinkedIn: Configured (username: your_email@...)
✅ Google Sheets: Configured (spreadsheet: 1JRbxQYOWlVLuSgv4uhfM2ljfiiBydYsD6fj_0geYRQk...)
📊 Max Jobs per Session: 10
⏱️  Delay Range: 3.0-6.0s
🕐 Element Wait Timeout: 20s
🔍 Default Keywords: python developer, software engineer
📍 Default Location: Remote
🎯 Default Experience: senior
💼 Default Job Type: full-time
============================================================

🔧 Configuration Validation:
   ✅ LinkedIn Credentials
   ✅ Google Sheets Config
   ✅ Scraping Config

🔍 Starting job search...
   Keywords: python developer, software engineer
   Location: Remote
   Max Jobs: 10
   Additional filters: {'experience_level': 'senior', 'job_type': 'full-time'}

📊 Processing 8 extracted jobs...
   ✅ Job 1: Senior Python Developer at TechCorp Inc. - EXTRACTED & WRITTEN
   ✅ Job 2: Full Stack Software Engineer at StartupXYZ - EXTRACTED & WRITTEN
   ...

📈 Extraction Summary:
   ✅ Successfully extracted: 8
   📊 Written to Google Sheets: 8
   ❌ Failed: 0

================================================================================
PRODUCTION SCRAPING SESSION REPORT
================================================================================
📅 Session Date: 2025-07-18 14:30:15
⏱️  Total Duration: 245.32 seconds

📊 Job Statistics:
   🔍 Jobs Attempted: 8
   ✅ Successfully Extracted: 8
   📝 Written to Google Sheets: 8
   ❌ Failed: 0
   📈 Extraction Success Rate: 100.0%
   📈 Write Success Rate: 100.0%

✅ No errors encountered

⚡ Performance Metrics:
   🕐 Average Time per Job: 30.67 seconds
   🚀 Jobs per Minute: 2.0
================================================================================

🎉 Production scraping completed successfully!
```

### Log Files

Logs are written to the `logs/` directory with detailed information for debugging:

- `linkedin_scraper.log` - LinkedIn scraper activities
- `google_sheets_manager.log` - Google Sheets operations
- `production_scraper.log` - Production scraper monitoring

## ⚙️ Configuration Options

### Scraping Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_JOBS_PER_SESSION` | 10 | Maximum jobs to extract per session |
| `DELAY_MIN` | 3.0 | Minimum delay between actions (seconds) |
| `DELAY_MAX` | 6.0 | Maximum delay between actions (seconds) |
| `ELEMENT_WAIT_TIMEOUT` | 20 | Element wait timeout (seconds) |

### Search Configuration

The default search parameters can be modified in `config/production_config.py`:

```python
default_keywords = ["python developer", "software engineer"]
default_location = "Remote"
default_experience_level = "senior"
default_job_type = "full-time"
```

## 🔒 Security Best Practices

### 1. Credential Management

- **Never commit credentials** to version control
- Use environment variables or `.env` files
- Rotate credentials regularly
- Use service accounts for Google Sheets access

### 2. Rate Limiting

The scraper includes built-in rate limiting to respect LinkedIn's terms:

- Random delays between actions (3-6 seconds)
- Maximum 12 requests per minute
- Conservative job limits per session

### 3. Error Handling

- Graceful failure recovery
- Comprehensive logging
- No sensitive data in logs

## 🚨 Troubleshooting

### Common Issues

#### 1. LinkedIn Authentication Failed

**Symptoms**: `LinkedIn authentication failed`

**Solutions**:
- Verify LinkedIn credentials are correct
- Check if LinkedIn requires 2FA
- Ensure account is not locked
- Try logging in manually first

#### 2. Google Sheets Connection Failed

**Symptoms**: `Google Sheets connection failed`

**Solutions**:
- Verify service account JSON file path
- Check spreadsheet ID is correct
- Ensure service account has edit permissions
- Verify Google Sheets API is enabled

#### 3. No Jobs Found

**Symptoms**: `No jobs extracted`

**Solutions**:
- Check search keywords are valid
- Verify location is accessible
- Try different search parameters
- Check LinkedIn for job availability

#### 4. Chrome Driver Issues

**Symptoms**: `WebDriver initialization failed`

**Solutions**:
- Ensure Chrome browser is installed
- Update Chrome to latest version
- Check system permissions
- Try running with `--no-sandbox` flag

### Debug Mode

Enable debug logging by setting the log level:

```bash
export LOG_LEVEL=DEBUG
python3 run_production_scraper.py
```

## 📈 Performance Optimization

### Increasing Job Limits

Start with conservative limits and gradually increase:

```bash
# Start with 5 jobs
export MAX_JOBS_PER_SESSION=5

# Increase to 10 jobs
export MAX_JOBS_PER_SESSION=10

# Increase to 25 jobs (monitor carefully)
export MAX_JOBS_PER_SESSION=25
```

### Adjusting Delays

If you encounter rate limiting, increase delays:

```bash
export DELAY_MIN=5.0
export DELAY_MAX=10.0
```

### Monitoring Performance

Track these metrics:
- **Extraction Success Rate**: Should be >90%
- **Average Time per Job**: Should be <60 seconds
- **Error Rate**: Should be <5%

## 🔄 Automation

### Scheduled Execution

Set up cron jobs for automated execution:

```bash
# Run daily at 9 AM
0 9 * * * cd /path/to/autoApply-bot && python3 run_production_scraper.py

# Run every 6 hours
0 */6 * * * cd /path/to/autoApply-bot && python3 run_production_scraper.py
```

### Continuous Monitoring

Monitor the scraper's health:

```bash
# Check if scraper is running
ps aux | grep run_production_scraper

# Check recent logs
tail -f logs/production_scraper.log

# Check Google Sheets for new data
# (Manually verify in Google Sheets interface)
```

## 📞 Support

For issues and questions:

1. Check the troubleshooting section above
2. Review logs in the `logs/` directory
3. Verify configuration is correct
4. Test with demo scraper first

## 🔄 Updates

Keep the system updated:

```bash
# Update dependencies
pip install -r requirements.txt --upgrade

# Update Chrome browser
# (Follow Chrome's update process for your OS)

# Check for code updates
git pull origin main
```

---

**Note**: This system is designed for respectful scraping with proper rate limiting. Always comply with LinkedIn's terms of service and respect website policies. 