# Google Sheets Integration Setup Guide

This guide will walk you through setting up Google Sheets integration for the Job Application Automation System.

## Prerequisites

- Google account with access to Google Cloud Console
- Python environment with required dependencies installed
- Google Sheets API credentials JSON file

## Step 1: Google Cloud Console Setup

### 1.1 Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" at the top of the page
3. Click "New Project"
4. Enter a project name (e.g., "Job Automation System")
5. Click "Create"

### 1.2 Enable Google Sheets API

1. In your new project, go to "APIs & Services" > "Library"
2. Search for "Google Sheets API"
3. Click on "Google Sheets API"
4. Click "Enable"

### 1.3 Create Service Account

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "Service Account"
3. Fill in the service account details:
   - **Name**: `job-automation-sheets`
   - **Description**: `Service account for job automation Google Sheets integration`
4. Click "Create and Continue"
5. Skip the optional steps (click "Done")

### 1.4 Generate JSON Key

1. In the service accounts list, click on your new service account
2. Go to the "Keys" tab
3. Click "Add Key" > "Create new key"
4. Select "JSON" format
5. Click "Create"
6. The JSON file will download automatically - save it securely

## Step 2: Google Sheets Setup

### 2.1 Create a Google Sheet

1. Go to [Google Sheets](https://sheets.google.com/)
2. Create a new spreadsheet
3. Name it something like "Job Applications Tracker"

### 2.2 Share with Service Account

1. Click the "Share" button in the top right
2. Add the service account email (found in your JSON credentials file)
3. Give it "Editor" permissions
4. Click "Send" (no need to send notification)

### 2.3 Get Spreadsheet ID

The spreadsheet ID is in the URL:
```
https://docs.google.com/spreadsheets/d/SPREADSHEET_ID_HERE/edit
```

Copy the `SPREADSHEET_ID_HERE` part.

## Step 3: Environment Configuration

### 3.1 Create .env File

Create a `.env` file in your project root with the following content:

```bash
# Google Sheets API Configuration
GOOGLE_SHEETS_CREDENTIALS_PATH=path/to/your/credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=your-spreadsheet-id-here

# Email Configuration (optional)
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# System Configuration
LOG_LEVEL=INFO
DEBUG_MODE=false
```

### 3.2 Update the Values

Replace the placeholder values:
- `path/to/your/credentials.json`: Full path to your downloaded JSON credentials file
- `your-spreadsheet-id-here`: The spreadsheet ID you copied earlier

Example:
```bash
GOOGLE_SHEETS_CREDENTIALS_PATH=/Users/yourname/Downloads/job-automation-sheets-abc123.json
GOOGLE_SHEETS_SPREADSHEET_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
```

## Step 4: Test the Integration

### 4.1 Run the Test Script

```bash
python test_google_sheets.py
```

This will:
- Test the connection to Google Sheets
- Create sample worksheets if they don't exist
- Write sample data to verify everything works

### 4.2 Expected Output

If everything is configured correctly, you should see:
```
🧪 Testing Google Sheets Integration
==================================================
📋 Initializing Google Sheets Manager...
🔗 Testing connection...
✅ Connection successful!

📝 Creating sample job listing...
📊 Writing job listing to Google Sheets...
✅ Job listing written successfully!

📝 Creating sample application...
📊 Writing application to Google Sheets...
✅ Application written successfully!

🔄 Testing status update...
✅ Status updated successfully!

📖 Testing application retrieval...
✅ Retrieved 1 applications from Google Sheets

🎉 Google Sheets integration test completed successfully!
```

## Step 5: Verify in Google Sheets

After running the test, check your Google Sheet. You should see:

### Applications Worksheet
- Headers: Date Applied, Job Title, Company, Location, etc.
- Sample application data

### Job Listings Worksheet
- Headers: Date Scraped, Job Title, Company, Location, etc.
- Sample job listing data

## Troubleshooting

### Common Issues

#### 1. "Credentials file not found"
- **Solution**: Check the path in your `.env` file
- Make sure the JSON file exists at the specified location

#### 2. "Spreadsheet ID not found"
- **Solution**: Verify the spreadsheet ID in your `.env` file
- Make sure you copied the correct ID from the URL

#### 3. "Permission denied"
- **Solution**: Ensure the service account email has "Editor" access to the spreadsheet
- Check that you shared the spreadsheet with the correct email

#### 4. "API not enabled"
- **Solution**: Make sure Google Sheets API is enabled in your Google Cloud project

#### 5. "Service account not found"
- **Solution**: Verify the service account exists and the JSON file is valid
- Re-download the JSON key if necessary

### Debug Mode

To get more detailed error information, set `DEBUG_MODE=true` in your `.env` file and check the logs in `logs/job_automation.log`.

## Security Best Practices

1. **Never commit credentials**: The `.env` file is already in `.gitignore`
2. **Secure storage**: Store your JSON credentials file in a secure location
3. **Limited permissions**: The service account only needs access to the specific spreadsheet
4. **Regular rotation**: Consider rotating your service account keys periodically

## Next Steps

Once Google Sheets integration is working:

1. **Customize the schema**: Modify the column headers in `GoogleSheetsManager` if needed
2. **Add more worksheets**: Create additional worksheets for different types of data
3. **Set up automation**: Integrate with the main application to automatically write data
4. **Add formatting**: Use Google Sheets API to add colors, formatting, and formulas

## API Reference

The `GoogleSheetsManager` class provides these main methods:

- `write_application(application)`: Write an application record
- `write_job_listing(job_listing)`: Write a job listing
- `update_application_status(application_id, status)`: Update application status
- `get_applications(limit)`: Retrieve applications from the sheet
- `test_connection()`: Test the API connection

For more details, see the class documentation in `src/data/google_sheets_manager.py`. 