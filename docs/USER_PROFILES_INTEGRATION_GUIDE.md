# User Profiles Integration Guide

This guide provides comprehensive instructions for integrating the new `user_profiles` table with your existing Supabase database and Flask application.

## Overview

The User Profiles Integration adds a new `user_profiles` table to store detailed user information for job matching and analysis. This integration provides:

- **Detailed User Profiles**: Store experience, education, skills, and preferences
- **Job Analysis Integration**: Use profile data to enhance job matching algorithms
- **Profile Completion Tracking**: Monitor profile completion status
- **API Endpoints**: RESTful API for profile management
- **Flask Integration**: Seamless integration with existing Flask routes

## Database Schema

### User Profiles Table

The `user_profiles` table includes the following fields:

```sql
CREATE TABLE user_profiles (
    profile_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    years_of_experience INTEGER NOT NULL CHECK (years_of_experience >= 0),
    experience_level TEXT NOT NULL CHECK (experience_level IN ('entry', 'junior', 'mid', 'senior', 'lead', 'executive')),
    education_level TEXT NOT NULL CHECK (education_level IN ('high_school', 'associates', 'bachelors', 'masters', 'phd', 'other')),
    field_of_study TEXT,
    skills_technologies TEXT[] DEFAULT '{}',
    work_arrangement_preference TEXT NOT NULL DEFAULT 'any' CHECK (work_arrangement_preference IN ('any', 'remote', 'hybrid', 'on_site')),
    preferred_locations TEXT[] DEFAULT '{}',
    salary_min INTEGER CHECK (salary_min >= 0),
    salary_max INTEGER CHECK (salary_max >= 0),
    salary_currency TEXT NOT NULL DEFAULT 'USD',
    profile_completed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT salary_range_check CHECK (
        (salary_min IS NULL AND salary_max IS NULL) OR
        (salary_min IS NOT NULL AND salary_max IS NOT NULL AND salary_min <= salary_max)
    ),
    CONSTRAINT unique_user_profile UNIQUE (user_id)
);
```

### Key Features

- **One-to-One Relationship**: Each user has exactly one profile
- **Automatic Profile Creation**: Profiles are created automatically when users register
- **Profile Completion Tracking**: Automatic detection of complete profiles
- **Row Level Security**: Users can only access their own profiles
- **Validation Constraints**: Database-level validation for data integrity

## Setup Instructions

### Step 1: Database Setup

1. **Access your Supabase Dashboard**
   - Go to https://supabase.com/dashboard
   - Select your project

2. **Run the SQL Schema**
   - Navigate to **SQL Editor**
   - Copy and paste the contents of `docs/user_profiles_schema.sql`
   - Click **Run** to execute the schema

3. **Verify Table Creation**
   - Go to **Table Editor**
   - Verify that `user_profiles` table exists
   - Check that RLS policies are enabled

### Step 2: Environment Configuration

Ensure your `.env` file includes the required Supabase credentials:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Authentication Mode
TESTING_MODE=false

# Flask Configuration
FLASK_SECRET_KEY=your-secret-key-change-this
```

### Step 3: Run Setup Script

Execute the setup script to verify the integration:

```bash
python scripts/setup_user_profiles.py
```

This script will:
- Check environment variables
- Test database connection
- Verify table access
- Create a sample profile
- Test Flask integration

### Step 4: Test the Integration

Run the comprehensive test suite:

```bash
python tests/test_user_profiles_integration.py
```

## API Endpoints

### Profile Management

#### GET /api/profile
Get the current user's profile.

**Response:**
```json
{
    "success": true,
    "profile": {
        "profile_id": "uuid",
        "user_id": "uuid",
        "years_of_experience": 3,
        "experience_level": "mid",
        "education_level": "bachelors",
        "field_of_study": "Computer Science",
        "skills_technologies": ["Python", "JavaScript", "React"],
        "work_arrangement_preference": "remote",
        "preferred_locations": ["San Francisco, CA"],
        "salary_min": 80000,
        "salary_max": 150000,
        "salary_currency": "USD",
        "profile_completed": true,
        "created_at": "2024-01-01T12:00:00Z",
        "updated_at": "2024-01-01T12:00:00Z"
    }
}
```

#### PUT /api/profile
Update the current user's profile.

**Request Body:**
```json
{
    "years_of_experience": 3,
    "experience_level": "mid",
    "education_level": "bachelors",
    "field_of_study": "Computer Science",
    "skills_technologies": ["Python", "JavaScript", "React"],
    "work_arrangement_preference": "remote",
    "preferred_locations": ["San Francisco, CA"],
    "salary_min": 80000,
    "salary_max": 150000
}
```

### Analysis Data

#### GET /api/profile/analysis-data
Get profile data needed for job analysis.

**Response:**
```json
{
    "success": true,
    "analysis_data": {
        "experience_level": "mid",
        "skills_technologies": ["Python", "JavaScript", "React"],
        "work_arrangement_preference": "remote",
        "preferred_locations": ["San Francisco, CA"],
        "salary_min": 80000,
        "salary_max": 150000,
        "years_of_experience": 3,
        "education_level": "bachelors",
        "field_of_study": "Computer Science"
    }
}
```

### Profile Status

#### GET /api/profile/completion-status
Check if user profile is complete.

**Response:**
```json
{
    "success": true,
    "profile_completed": true
}
```

### Profile Options

#### GET /api/profile/options
Get available options for profile fields.

**Response:**
```json
{
    "success": true,
    "options": {
        "experience_levels": ["entry", "junior", "mid", "senior", "lead", "executive"],
        "education_levels": ["high_school", "associates", "bachelors", "masters", "phd", "other"],
        "work_arrangements": ["any", "remote", "hybrid", "on_site"]
    }
}
```

## Flask Integration

### Profile Page

The profile page (`/profile`) now uses the new API endpoints:

- **Dynamic Loading**: Profile data is loaded via API calls
- **Real-time Updates**: Changes are saved immediately
- **Completion Tracking**: Shows profile completion status
- **Validation**: Client and server-side validation

### Job Analysis Integration

The job analysis system now uses profile data:

```python
# Get profile data for analysis
analysis_data = db_manager.profiles.get_analysis_data(user['user_id'])

# Create user profile object
user_profile = UserProfile(
    years_of_experience=analysis_data.get('years_of_experience', 0),
    experience_level=analysis_data.get('experience_level', 'entry'),
    additional_skills=analysis_data.get('skills_technologies', []),
    preferred_locations=analysis_data.get('preferred_locations', []),
    salary_min=analysis_data.get('salary_min'),
    salary_max=analysis_data.get('salary_max'),
    remote_preference=analysis_data.get('work_arrangement_preference', 'any')
)
```

## Data Models

### UserProfile Class

```python
@dataclass
class UserProfile:
    """User profile data model."""
    profile_id: str
    user_id: str
    years_of_experience: int
    experience_level: ExperienceLevel
    education_level: EducationLevel
    field_of_study: Optional[str] = None
    skills_technologies: Optional[List[str]] = None
    work_arrangement_preference: WorkArrangement = WorkArrangement.ANY
    preferred_locations: Optional[List[str]] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: str = "USD"
    profile_completed: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

### Enums

```python
class ExperienceLevel(Enum):
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"

class EducationLevel(Enum):
    HIGH_SCHOOL = "high_school"
    ASSOCIATES = "associates"
    BACHELORS = "bachelors"
    MASTERS = "masters"
    PHD = "phd"
    OTHER = "other"

class WorkArrangement(Enum):
    ANY = "any"
    REMOTE = "remote"
    HYBRID = "hybrid"
    ON_SITE = "on_site"
```

## UserProfileManager Class

The `UserProfileManager` class provides all profile-related operations:

### Key Methods

- `create_profile(user_id, profile_data)` - Create new user profile
- `get_profile(user_id)` - Retrieve user's profile
- `update_profile(user_id, updates)` - Update profile fields
- `get_complete_user_data(user_id)` - Join users + profiles data
- `is_profile_complete(user_id)` - Check if profile has required fields
- `get_analysis_data(user_id)` - Get profile data for job analysis
- `validate_profile_data(profile_data)` - Validate profile data

### Profile Completion Logic

A profile is considered complete when all required fields are filled:

- Years of experience
- Experience level
- Education level
- Skills and technologies (non-empty array)
- Work arrangement preference

## Error Handling

### Common Error Scenarios

1. **Profile Not Found**
   ```json
   {
       "success": false,
       "error": "Profile not found"
   }
   ```

2. **Profile Incomplete**
   ```json
   {
       "success": false,
       "error": "Please complete your profile before analyzing jobs"
   }
   ```

3. **Validation Errors**
   ```json
   {
       "success": false,
       "error": "Invalid experience level"
   }
   ```

4. **Database Errors**
   ```json
   {
       "success": false,
       "error": "Database not available"
   }
   ```

## Security Considerations

### Row Level Security (RLS)

All profile operations are protected by RLS policies:

```sql
-- Users can only view their own profile
CREATE POLICY "Users can view own profile" ON user_profiles
    FOR SELECT USING (auth.uid() = user_id);

-- Users can update their own profile
CREATE POLICY "Users can update own profile" ON user_profiles
    FOR UPDATE USING (auth.uid() = user_id);
```

### Authentication Requirements

All profile API endpoints require authentication:

```python
@profile_bp.route('', methods=['GET'])
@login_required
def get_profile():
    # Only authenticated users can access
```

## Performance Optimization

### Database Indexes

The schema includes optimized indexes:

```sql
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_user_profiles_experience_level ON user_profiles(experience_level);
CREATE INDEX idx_user_profiles_work_arrangement ON user_profiles(work_arrangement_preference);
CREATE INDEX idx_user_profiles_skills ON user_profiles USING GIN(skills_technologies);
CREATE INDEX idx_user_profiles_locations ON user_profiles USING GIN(preferred_locations);
CREATE INDEX idx_user_profiles_completed ON user_profiles(profile_completed);
```

### Caching Strategy

Consider implementing caching for frequently accessed profile data:

```python
# Example caching implementation
def get_profile_with_cache(user_id: str) -> Optional[UserProfile]:
    cache_key = f"profile:{user_id}"
    
    # Check cache first
    cached_profile = cache.get(cache_key)
    if cached_profile:
        return cached_profile
    
    # Get from database
    profile = db_manager.profiles.get_profile(user_id)
    if profile:
        cache.set(cache_key, profile, timeout=3600)  # 1 hour
    
    return profile
```

## Migration Guide

### From Existing Profile System

If you have an existing profile system, follow these steps:

1. **Backup Existing Data**
   ```bash
   # Export existing profile data
   python scripts/export_existing_profiles.py
   ```

2. **Run Migration Script**
   ```bash
   # Migrate to new profile system
   python scripts/migrate_profiles.py
   ```

3. **Update Application Code**
   - Replace old profile references with new API calls
   - Update form handling to use new endpoints
   - Test all profile-related functionality

### Data Migration Example

```python
def migrate_user_profile(old_profile_data):
    """Migrate old profile data to new format."""
    
    # Map old fields to new format
    new_profile_data = {
        'years_of_experience': old_profile_data.get('experience_years', 0),
        'experience_level': map_experience_level(old_profile_data.get('level')),
        'education_level': map_education_level(old_profile_data.get('education')),
        'field_of_study': old_profile_data.get('field_of_study'),
        'skills_technologies': old_profile_data.get('skills', []),
        'work_arrangement_preference': map_work_arrangement(old_profile_data.get('remote_preference')),
        'preferred_locations': old_profile_data.get('locations', []),
        'salary_min': old_profile_data.get('salary_min'),
        'salary_max': old_profile_data.get('salary_max')
    }
    
    return new_profile_data
```

## Troubleshooting

### Common Issues

1. **Profile Not Created Automatically**
   - Check if the trigger function exists in the database
   - Verify RLS policies are correctly configured
   - Check user registration flow

2. **API Endpoints Not Working**
   - Verify Flask routes are registered
   - Check authentication middleware
   - Ensure database connection is working

3. **Profile Completion Not Detected**
   - Check the completion logic in the database trigger
   - Verify all required fields are being set
   - Test with a complete profile

4. **Job Analysis Not Using Profile Data**
   - Ensure profile is complete before analysis
   - Check that analysis data is being retrieved correctly
   - Verify profile data is being passed to analysis functions

### Debug Commands

```bash
# Test database connection
python scripts/test_supabase_connection.py

# Test user profiles specifically
python tests/test_user_profiles_integration.py

# Check profile completion
curl -X GET "http://localhost:5000/api/profile/completion-status" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get profile data
curl -X GET "http://localhost:5000/api/profile" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Best Practices

### Profile Data Management

1. **Always Validate Input**
   ```python
   is_valid, error_message = db_manager.profiles.validate_profile_data(data)
   if not is_valid:
       return jsonify({'success': False, 'error': error_message}), 400
   ```

2. **Handle Missing Profiles Gracefully**
   ```python
   profile = db_manager.profiles.get_profile(user_id)
   if not profile:
       # Create default profile or redirect to profile completion
       return redirect(url_for('profile'))
   ```

3. **Use Profile Completion for Feature Gates**
   ```python
   if not db_manager.profiles.is_profile_complete(user_id):
       flash("Please complete your profile to use this feature")
       return redirect(url_for('profile'))
   ```

### Performance Optimization

1. **Cache Frequently Accessed Data**
2. **Use Database Indexes Effectively**
3. **Implement Pagination for Large Datasets**
4. **Optimize API Response Size**

### Security Best Practices

1. **Always Validate User Permissions**
2. **Use RLS Policies for Data Access**
3. **Sanitize Input Data**
4. **Log Security Events**

## Conclusion

The User Profiles Integration provides a robust foundation for storing and managing user qualification data. By following this guide, you can successfully integrate the new profile system with your existing application and enhance your job matching capabilities.

For additional support or questions, refer to the test files and setup scripts provided in this integration. 