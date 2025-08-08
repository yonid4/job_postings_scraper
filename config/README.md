# Config Directory

This directory contains configuration files and credentials for the AI Job Qualification Screening System.

## Contents

### **Configuration Files**
- `settings.json` - Main application configuration and user profile defaults

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
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# AI Configuration
GEMINI_API_KEY=your_gemini_api_key

# Flask Configuration
FLASK_SECRET_KEY=your-secret-key-change-this

# Testing Mode (Development)
TESTING_MODE=true
```

### **2. Supabase Setup**
The system uses Supabase for:
- User authentication and profiles
- Job data storage and tracking
- Application status management
- Resume and file storage
- Real-time data synchronization

### **3. Application Settings**
The `settings.json` file contains:
- User profile defaults and preferences
- AI analysis configuration
- Scraping behavior settings
- System performance parameters

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