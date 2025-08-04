# Environment Setup Guide

## Overview

The AI Job Qualification System now uses environment variables for sensitive configuration including AI settings and Google Sheets credentials. This provides better security and flexibility.

## Quick Setup

### Option 1: Interactive Setup Script (Recommended)

Run the interactive setup script:

```bash
python scripts/setup_env.py
```

This will guide you through setting up all required configuration.

### Option 2: Manual Setup

1. Copy the template:
```bash
cp env.template .env
```

2. Edit the `.env` file with your credentials

## Required Configuration

### LinkedIn Credentials
```bash
LINKEDIN_USERNAME=your_email@example.com
LINKEDIN_PASSWORD=your_linkedin_password
```

### AI Configuration (Required for AI-powered qualification)
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

### Google Sheets Configuration (Required for data persistence)
```bash
GOOGLE_SHEETS_CREDENTIALS_PATH=path/to/your/credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id_here
GOOGLE_SHEETS_WORKSHEET_NAME=Qualified Jobs
```

## Optional Configuration

### AI Model Settings
```bash
# AI model to use (default: gemini-2.0-flash-lite)
GEMINI_MODEL=gemini-2.0-flash-lite

# Maximum tokens for analysis (default: 2000)
GEMINI_MAX_TOKENS=2000

# Temperature for AI responses (default: 0.1)
GEMINI_TEMPERATURE=0.1

# Analysis timeout in seconds (default: 60)
GEMINI_ANALYSIS_TIMEOUT=60

# Number of retry attempts (default: 3)
GEMINI_RETRY_ATTEMPTS=3
```

### Scraping Configuration
```bash
# Maximum jobs per session (default: 10)
MAX_JOBS_PER_SESSION=10

# Delay between actions (default: 3.0-6.0 seconds)
DELAY_MIN=3.0
DELAY_MAX=6.0

# Element wait timeout (default: 20 seconds)
ELEMENT_WAIT_TIMEOUT=20
```

### Logging Configuration
```bash
# Log level: DEBUG, INFO, WARNING, ERROR (default: INFO)
LOG_LEVEL=INFO
```

## Qualification Threshold

The qualification threshold is now **user-configurable** in the web interface:

- **Default value**: 70%
- **Range**: 0% to 100%
- **Location**: Prominently displayed at the top of the search form
- **Behavior**: 
  - 0% = Show all jobs regardless of qualification score
  - 70% = Show only jobs with qualification score ≥ 70%
  - 100% = Show only jobs with perfect qualification match

## Security Features

### Environment Variable Protection
- ✅ All sensitive credentials moved to environment variables
- ✅ `.env` file is in `.gitignore` to prevent accidental commits
- ✅ No credentials stored in version-controlled files
- ✅ Environment variables loaded dynamically at runtime

### Configuration Validation
The system validates configuration on startup:
- Checks for required credentials
- Validates API keys and file paths
- Provides clear error messages for missing configuration

## Testing Your Configuration

### Test LinkedIn Credentials
```bash
python tests/test_linkedin_credentials.py
```

### Test Google Sheets Integration
```bash
python tests/test_google_sheets.py
```

### Test AI Configuration
```bash
python tests/test_qualification_system.py
```

## Troubleshooting

### Common Issues

1. **"LinkedIn credentials not found"**
   - Ensure `LINKEDIN_USERNAME` and `LINKEDIN_PASSWORD` are set in `.env`
   - Check that the `.env` file is in the project root directory

2. **"Google Sheets not configured"**
   - Verify `GOOGLE_SHEETS_CREDENTIALS_PATH` points to a valid JSON file
   - Ensure `GOOGLE_SHEETS_SPREADSHEET_ID` is correct
   - Check that the service account has proper permissions

3. **"AI API key not found"**
   - Set `GEMINI_API_KEY` in your `.env` file
   - Verify the API key is valid and has sufficient quota

4. **"Configuration file not found"**
   - Run the setup script: `python scripts/setup_env.py`
   - Or manually create `.env` from `env.template`

### Debug Mode

Enable debug logging to troubleshoot configuration issues:

```bash
LOG_LEVEL=DEBUG
```

## Migration from Old Configuration

If you were previously using `settings.json` for credentials:

1. **Backup your current settings**:
   ```bash
   cp config/settings.json config/settings.json.backup
   ```

2. **Run the setup script**:
   ```bash
   python scripts/setup_env.py
   ```

3. **Verify configuration**:
   ```bash
   python tests/test_linkedin_credentials.py
   ```

4. **Remove sensitive data from settings.json** (already done in this update)

## Best Practices

1. **Never commit credentials** to version control
2. **Use strong passwords** for LinkedIn
3. **Rotate API keys** periodically
4. **Monitor API usage** to avoid quota limits
5. **Backup your `.env` file** securely
6. **Use different credentials** for development and production

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the logs in the `logs/` directory
3. Run the test scripts to validate configuration
4. Check the documentation in the `docs/` directory 