# Config Directory

This directory contains configuration files and credentials for the Job Application Automation System.

## Contents

### **Configuration Files**
- `settings.json` - Main application configuration
- `auto-apply-bot-466218-5a1d69f23d44.json` - Google Sheets API credentials

### **Template Files**
- `env.template` - Environment variables template (in root directory)

## Configuration Setup

### **1. Environment Variables**
Copy the template and configure your environment:
```bash
cp env.template .env
```

Edit `.env` with your credentials:
```env
LINKEDIN_USERNAME=your-email@example.com
LINKEDIN_PASSWORD=your-password
OPENAI_API_KEY=your-openai-api-key
GOOGLE_SHEETS_CREDENTIALS_FILE=config/auto-apply-bot-466218-5a1d69f23d44.json
```

### **2. Google Sheets Setup**
The Google Sheets credentials file enables:
- Job data storage and tracking
- Application status management
- Results export functionality

### **3. Application Settings**
The `settings.json` file contains:
- Scraping configuration
- AI analysis settings
- User profile defaults
- System preferences

## Security Notes

⚠️ **Important Security Considerations:**
- Never commit credentials to version control
- Keep API keys secure and rotate regularly
- Use environment variables for sensitive data
- Restrict access to configuration files

## File Permissions

Ensure proper file permissions:
```bash
chmod 600 config/*.json
chmod 600 .env
```

## Backup

Regularly backup your configuration:
```bash
cp config/settings.json config/settings.json.backup
cp .env .env.backup
``` 