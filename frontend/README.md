# AI Job Qualification System - Web Frontend

A modern, user-friendly web interface for the AI Job Qualification Screening System.

## Features

- **User Profile Management**: Set your experience, education, skills, and preferences
- **Job Search Interface**: Paste LinkedIn search URLs to analyze multiple jobs
- **AI Analysis Results**: View detailed qualification scores and reasoning
- **Google Sheets Integration**: Save qualified jobs directly to your spreadsheet
- **Real-time Updates**: See analysis progress and results as they happen
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## Quick Start

### 1. Install Dependencies

```bash
pip install -r ../requirements.txt
```

### 2. Configure Your Profile

1. Start the web server:
   ```bash
   python ../start_frontend.py
   ```

2. Open http://localhost:5000 in your browser

3. Go to **Profile** and fill in your:
   - Years of experience
   - Education details
   - Technical skills
   - Location preferences
   - Salary expectations

### 3. Configure Settings

1. Go to **Settings**
2. Add your Gemini API key (get one from [Google AI Studio](https://makersuite.google.com/app/apikey))
3. Configure Google Sheets integration (optional)

### 4. Start Job Search

1. Go to **Job Search**
2. Paste LinkedIn search URLs (one per line)
3. Click "Analyze Jobs"
4. Review results and save qualified jobs

## How to Use

### Finding LinkedIn Search URLs

1. Go to [LinkedIn Jobs](https://www.linkedin.com/jobs/)
2. Search for jobs with your criteria (e.g., "Python developer", "React engineer")
3. Copy the URL from your browser
4. Paste it in the Job Search page

**Example URLs:**
- `https://www.linkedin.com/jobs/search/?keywords=python%20developer&location=San%20Francisco`
- `https://www.linkedin.com/jobs/search/?keywords=react&location=New%20York`

### Understanding Results

Each job analysis includes:

- **Qualification Score** (0-100): Overall match quality
- **AI Reasoning**: Detailed explanation of the score
- **Strengths**: What makes you a good match
- **Concerns**: Potential issues or gaps
- **Required Experience**: What the job asks for
- **Key Skills**: Technologies mentioned in the job

### Score Categories

- **80-100**: Excellent Match (Green)
- **60-79**: Good Match (Blue)
- **40-59**: Fair Match (Yellow)
- **0-39**: Poor Match (Red)

## Pages

### Dashboard
- System overview and quick access
- How-to guide and tips
- System status

### Profile
- Manage your qualifications
- Set preferences and constraints
- Real-time profile summary

### Job Search
- Input LinkedIn search URLs
- Analyze multiple jobs at once
- View detailed results

### Results
- Review all analyzed jobs
- Save qualified jobs to Google Sheets
- Detailed job information

### Settings
- Configure AI settings
- Set up Google Sheets integration
- Test connections

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# AI Settings
GEMINI_API_KEY=your_gemini_api_key_here

# Google Sheets (optional)
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id_here
GOOGLE_SHEETS_CREDENTIALS_FILE=path/to/credentials.json

# Flask Settings
SECRET_KEY=your_secret_key_here
FLASK_ENV=development
```

### Google Sheets Setup

1. Create a new Google Sheet
2. Share it with your service account email
3. Copy the spreadsheet ID from the URL
4. Add it to your settings

## Development

### Project Structure

```
frontend/
├── app.py              # Flask application
├── templates/          # HTML templates
│   ├── base.html       # Base template
│   ├── index.html      # Dashboard
│   ├── profile.html    # Profile management
│   ├── search.html     # Job search
│   ├── results.html    # Results display
│   └── settings.html   # Settings
└── README.md          # This file
```

### Running in Development

```bash
# From project root
python start_frontend.py

# Or directly
cd frontend
python app.py
```

### Customization

The frontend uses:
- **Bootstrap 5** for styling
- **Font Awesome** for icons
- **jQuery** for interactions
- **Flask** for the backend

You can customize the appearance by modifying the CSS in `templates/base.html`.

## Troubleshooting

### Common Issues

1. **"System not initialized"**
   - Check that all dependencies are installed
   - Verify your configuration files

2. **"No jobs found"**
   - Make sure you're using LinkedIn search URLs, not individual job URLs
   - Check that the URLs are accessible

3. **"AI analysis failed"**
   - Verify your Gemini API key is correct
   - Check your internet connection

4. **"Google Sheets error"**
   - Ensure the spreadsheet is shared with your service account
   - Verify the spreadsheet ID is correct

### Getting Help

- Check the system status on the dashboard
- Review the settings page for configuration issues
- Look at the browser console for JavaScript errors
- Check the Flask logs for backend errors

## Security Notes

- API keys are stored securely and not exposed in the frontend
- All form data is validated server-side
- HTTPS is recommended for production use
- Session data is encrypted

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## License

This frontend is part of the AI Job Qualification Screening System. 