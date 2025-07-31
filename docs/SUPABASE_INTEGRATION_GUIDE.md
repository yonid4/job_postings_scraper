# Supabase Database Integration Guide

This guide provides comprehensive instructions for integrating Supabase database with the Job Automation System, including authentication, data management, and deployment considerations.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Database Schema](#database-schema)
4. [Setup Instructions](#setup-instructions)
5. [Authentication Modes](#authentication-modes)
6. [API Reference](#api-reference)
7. [Deployment Guide](#deployment-guide)
8. [Troubleshooting](#troubleshooting)

## Overview

The Supabase integration provides:

- **User Authentication**: Email/password registration with email verification
- **Database Storage**: Secure storage for jobs, applications, and search history
- **Row Level Security**: Users can only access their own data
- **Real-time Updates**: Live data synchronization
- **Scalable Architecture**: Built for production deployment

## Prerequisites

### Required Software
- Python 3.8+
- Supabase account and project
- Git

### Required Dependencies
```bash
pip install -r requirements_supabase.txt
```

## Database Schema

### Tables Structure

#### 1. users
```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    linkedin_credentials TEXT,
    subscription_status TEXT DEFAULT 'free',
    search_preferences JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 2. jobs
```sql
CREATE TABLE jobs (
    job_id UUID PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    job_title TEXT NOT NULL,
    company_name TEXT NOT NULL,
    location TEXT NOT NULL,
    salary_range TEXT,
    job_description TEXT,
    job_url TEXT,
    linkedin_url TEXT,
    date_posted TIMESTAMP WITH TIME ZONE,
    date_found TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    work_arrangement TEXT,
    experience_level TEXT,
    job_type TEXT,
    gemini_evaluation TEXT,
    gemini_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 3. applications
```sql
CREATE TABLE applications (
    application_id UUID PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    job_id UUID REFERENCES jobs(job_id) ON DELETE CASCADE,
    application_method TEXT NOT NULL,
    applied_date TIMESTAMP WITH TIME ZONE NOT NULL,
    application_status TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 4. job_searches
```sql
CREATE TABLE job_searches (
    search_id UUID PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    keywords TEXT[] NOT NULL,
    location TEXT,
    filters JSONB,
    results_count INTEGER DEFAULT 0,
    search_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Row Level Security (RLS) Policies

Enable RLS on all tables and add the following policies:

#### User Profiles Table
```sql
-- Users can only read their own profile
CREATE POLICY "Users can view own profile" ON user_profiles
    FOR SELECT USING (auth.uid() = user_id);

-- Users can update their own profile
CREATE POLICY "Users can update own profile" ON user_profiles
    FOR UPDATE USING (auth.uid() = user_id);

-- Users can insert their own profile
CREATE POLICY "Users can insert own profile" ON user_profiles
    FOR INSERT WITH CHECK (auth.uid() = user_id);
```

#### Jobs Table
```sql
-- Users can only access their own jobs
CREATE POLICY "Users can view own jobs" ON jobs
    FOR ALL USING (auth.uid() = user_id);
```

#### Applications Table
```sql
-- Users can only access their own applications
CREATE POLICY "Users can view own applications" ON applications
    FOR ALL USING (auth.uid() = user_id);
```

#### Job Searches Table
```sql
-- Users can only access their own searches
CREATE POLICY "Users can view own searches" ON job_searches
    FOR ALL USING (auth.uid() = user_id);
```

## Setup Instructions

### Step 1: Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Note your project URL and anon key

### Step 2: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here

# Authentication Mode
TESTING_MODE=false

# Flask Configuration
FLASK_SECRET_KEY=your-secret-key-change-this

# Other existing variables...
```

### Step 3: Run Setup Script

```bash
python scripts/setup_supabase_integration.py
```

This script will:
- Check environment variables
- Test database connection
- Verify table access
- Create sample user (in testing mode)

### Step 4: Start the Application

```bash
python frontend/app_supabase.py
```

## Authentication Modes

### Testing Mode (`TESTING_MODE=true`)

- No email verification required
- Users can login immediately after registration
- Useful for development and testing
- Auto-creates sample users

### Production Mode (`TESTING_MODE=false`)

- Email verification required
- Users must verify email before login
- Secure for production deployment
- Follows best security practices

## API Reference

### Authentication Endpoints

#### Register User
```http
POST /auth/register
Content-Type: application/x-www-form-urlencoded

email=user@example.com&password=password123&full_name=John Doe
```

#### Login User
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

email=user@example.com&password=password123
```

#### Logout User
```http
GET /auth/logout
```

#### Verify Email
```http
GET /auth/verify-email/<token>
```

### Database Operations

#### Create Job
```python
from src.data.supabase_manager import SupabaseManager

db_manager = SupabaseManager(supabase_url, supabase_key)
job_data = {
    'user_id': 'user-uuid',
    'job_title': 'Software Engineer',
    'company_name': 'Tech Corp',
    'location': 'San Francisco, CA'
}

success, message, job = db_manager.jobs.create_job(job_data)
```

#### Get User Jobs
```python
jobs = db_manager.jobs.get_user_jobs(user_id, limit=50)
```

#### Create Application
```python
application_data = {
    'user_id': 'user-uuid',
    'job_id': 'job-uuid',
    'application_method': 'manual',
    'applied_date': datetime.now().isoformat(),
    'application_status': 'applied'
}

success, message, application = db_manager.applications.create_application(application_data)
```

## Deployment Guide

### Local Development

1. Set `TESTING_MODE=true`
2. Run setup script
3. Start Flask app
4. Access at `http://localhost:5000`

### Production Deployment

1. Set `TESTING_MODE=false`
2. Configure email provider in Supabase
3. Set up proper SSL certificates
4. Use production-grade WSGI server
5. Configure environment variables securely

### Environment Variables for Production

```bash
# Required
SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here
TESTING_MODE=false
FLASK_SECRET_KEY=your-very-secure-secret-key

# Optional but recommended
LOG_LEVEL=INFO
FLASK_ENV=production
```

### Security Considerations

1. **Environment Variables**: Never commit `.env` files
2. **Secret Keys**: Use strong, unique secret keys
3. **Email Verification**: Always enable in production
4. **HTTPS**: Use SSL/TLS in production
5. **Rate Limiting**: Implement API rate limiting
6. **Input Validation**: Validate all user inputs

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed
```
Error: Failed to initialize Supabase client
```
**Solution**: Check your `SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`

#### 2. RLS Policy Violation
```
Error: new row violates row-level security policy
```
**Solution**: Ensure RLS policies are correctly configured

#### 3. Email Verification Not Working
```
Error: Email verification failed
```
**Solution**: 
- Check email provider configuration in Supabase
- Verify `TESTING_MODE` setting
- Check email templates

#### 4. Authentication Errors
```
Error: User not authenticated
```
**Solution**: 
- Ensure user is logged in
- Check session configuration
- Verify authentication flow

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Check

Test system health:

```bash
curl http://localhost:5000/api/health
```

Expected response:
```json
{
    "status": "healthy",
    "database": "connected",
    "authentication": "connected",
    "timestamp": "2024-01-01T12:00:00"
}
```

## Migration from Existing System

### Step 1: Backup Existing Data
```bash
# Export existing data to JSON
python scripts/export_data.py
```

### Step 2: Import to Supabase
```bash
# Import data to Supabase
python scripts/import_to_supabase.py
```

### Step 3: Update Application
```bash
# Switch to Supabase-enabled app
cp frontend/app_supabase.py frontend/app.py
```

### Step 4: Test Migration
```bash
# Run migration tests
python tests/test_migration.py
```

## Performance Optimization

### Database Indexes
```sql
-- Add indexes for better performance
CREATE INDEX idx_jobs_user_id ON jobs(user_id);
CREATE INDEX idx_applications_user_id ON applications(user_id);
CREATE INDEX idx_job_searches_user_id ON job_searches(user_id);
CREATE INDEX idx_jobs_date_found ON jobs(date_found DESC);
```

### Connection Pooling
```python
# Configure connection pooling
app.config['SUPABASE_POOL_SIZE'] = 10
app.config['SUPABASE_MAX_OVERFLOW'] = 20
```

### Caching
```python
# Implement caching for frequently accessed data
from functools import lru_cache

@lru_cache(maxsize=128)
def get_user_profile(user_id):
    # Cache user profile data
    pass
```

## Monitoring and Logging

### Application Logs
```python
import logging
from src.utils.logger import JobAutomationLogger

logger = JobAutomationLogger()
logger.info("User registered successfully")
logger.error("Database connection failed")
```

### Database Monitoring
- Monitor query performance in Supabase dashboard
- Set up alerts for connection issues
- Track user activity and growth

### Error Tracking
```python
# Integrate with error tracking service
import sentry_sdk
sentry_sdk.init(dsn="your-sentry-dsn")
```

## Support and Resources

### Documentation
- [Supabase Documentation](https://supabase.com/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Python Supabase Client](https://supabase.com/docs/reference/python)

### Community
- [Supabase Discord](https://discord.supabase.com)
- [Flask Community](https://flask.palletsprojects.com/community/)

### Issues and Feedback
- Report bugs in the project repository
- Submit feature requests
- Contribute to the codebase

---

**Note**: This integration provides a solid foundation for a production-ready job automation system. Always test thoroughly in a staging environment before deploying to production. 