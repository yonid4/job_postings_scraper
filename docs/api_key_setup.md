# API Key Configuration

## Overview

The Job Application Automation System automatically loads the Google Gemini API key from your `.env` file. This provides a secure way to manage sensitive credentials without storing them in version-controlled files.

## How It Works

1. **Environment File**: The system looks for a `.env` file in the project root
2. **Automatic Loading**: When the application starts, `python-dotenv` loads all environment variables from `.env`
3. **Configuration Update**: The `ConfigurationManager` automatically updates the AI settings and LinkedIn credentials from the environment

## Setup Instructions

### 1. Create .env File

If you don't have a `.env` file, copy the template:

```bash
cp env.template .env
```

### 2. Add Your Credentials

Edit the `.env` file and add your credentials:

```bash
# LinkedIn Credentials (REQUIRED)
LINKEDIN_USERNAME=your_email@example.com
LINKEDIN_PASSWORD=your_linkedin_password

# AI Configuration (REQUIRED for AI-powered job qualification)
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### 3. Verify Configuration

Run the test script to verify your credentials are loaded correctly:

```bash
python test_linkedin_credentials.py
```

## Security Notes

- ✅ The `.env` file is already in `.gitignore` to prevent committing credentials
- ✅ API keys and LinkedIn credentials are never stored in the `settings.json` file (intentionally omitted for security)
- ✅ Environment variables are loaded dynamically at runtime
- ✅ The system falls back to rule-based analysis if no API key is provided
- ✅ LinkedIn credentials are loaded securely from environment variables

## Design Decision: No Credentials in settings.json

The `api_key`, `username`, and `password` fields are intentionally **not included** in `settings.json` for security reasons:

1. **Security**: Prevents accidental commit of sensitive credentials
2. **Clarity**: Makes it obvious that credentials come from environment variables
3. **Best Practice**: Follows the principle of separation of concerns
4. **Flexibility**: Allows different credentials for different environments (dev, staging, prod)

The configuration system automatically handles the missing fields by defaulting to empty strings, which are then overridden by the environment variables when available.

## Troubleshooting

### Credentials Not Found

If you see "credentials not loaded" errors:

1. Check that your `.env` file exists in the project root
2. Verify the `LINKEDIN_USERNAME` and `LINKEDIN_PASSWORD` variables are set correctly
3. Verify the `GEMINI_API_KEY` variable is set correctly
4. Make sure there are no extra spaces or quotes around the values
5. Restart your Python application after making changes

### Example .env File

```bash
# LinkedIn Credentials
LINKEDIN_USERNAME=your_email@example.com
LINKEDIN_PASSWORD=your_linkedin_password

# AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS_PATH=auto-apply-bot-466218-5a1d69f23d44.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id_here
```

## Code Implementation

The credential loading is handled in `src/config/config_manager.py`:

```python
# Load environment variables
load_dotenv()

def _load_from_environment(self) -> None:
    """Load configuration from environment variables."""
    # AI Settings
    if os.getenv('GEMINI_API_KEY'):
        if 'ai_settings' not in self.config:
            self.config['ai_settings'] = {}
        self.config['ai_settings']['api_key'] = os.getenv('GEMINI_API_KEY')
    
    # LinkedIn Settings
    if os.getenv('LINKEDIN_USERNAME'):
        if 'linkedin' not in self.config:
            self.config['linkedin'] = {}
        self.config['linkedin']['username'] = os.getenv('LINKEDIN_USERNAME')
    
    if os.getenv('LINKEDIN_PASSWORD'):
        if 'linkedin' not in self.config:
            self.config['linkedin'] = {}
        self.config['linkedin']['password'] = os.getenv('LINKEDIN_PASSWORD')
```

This ensures that all credentials are automatically available throughout the application without manual configuration. 