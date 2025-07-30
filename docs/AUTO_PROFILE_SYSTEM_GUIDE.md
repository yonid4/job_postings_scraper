# Automatic User Profile Creation System Guide

This guide explains how to set up and use the automatic user profile creation system that integrates with Supabase Auth.

## Overview

The system automatically creates user profiles whenever a new user registers through Supabase Auth. It uses a **database trigger approach** for reliability and performance.

### Key Features

- ✅ **Automatic Profile Creation**: Profiles are created automatically when users register
- ✅ **Default Values**: Sensible defaults for new profiles
- ✅ **Comprehensive Logging**: Detailed logs for debugging
- ✅ **Error Handling**: Robust error handling with structured responses
- ✅ **Testing Support**: Both testing and production modes
- ✅ **Profile Management**: Complete CRUD operations for profiles

## Architecture

```
User Registration Flow:
1. User fills registration form on frontend
2. Frontend calls Supabase Auth signup
3. Supabase creates user in auth.users table
4. Database trigger fires automatically
5. Trigger creates profile in user_profiles table
6. User gets both auth account and profile
```

## Database Schema

### User Profiles Table

```sql
CREATE TABLE public.user_profiles (
    profile_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    years_of_experience INTEGER DEFAULT 0,
    experience_level TEXT DEFAULT 'entry',
    education_level TEXT DEFAULT 'bachelors',
    field_of_study TEXT,
    skills_technologies TEXT[],
    work_arrangement_preference TEXT DEFAULT 'any',
    preferred_locations TEXT[],
    salary_min INTEGER,
    salary_max INTEGER,
    salary_currency TEXT DEFAULT 'USD',
    profile_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);
```

### Default Values

When a new user registers, their profile is created with these defaults:

- `years_of_experience`: 0
- `experience_level`: "entry"
- `education_level`: "bachelors"
- `work_arrangement_preference`: "any"
- `profile_completed`: false

## Setup Instructions

### 1. Environment Variables

Ensure these environment variables are set in your `.env` file:

```bash
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
TESTING_MODE=true  # Set to false for production
```

### 2. Database Setup

Run the setup script to create the database schema and triggers:

```bash
python scripts/setup_auto_profile_creation.py
```

This script will:
- Create the `user_profiles` table
- Create the trigger function
- Create the trigger on `auth.users`
- Verify the setup
- Test the trigger functionality

### 3. Testing the System

Run the comprehensive test suite:

```bash
python scripts/test_auto_profile_system.py
```

This will test:
- Database trigger functionality
- Python backend integration
- Profile creation and management
- Error handling
- Complete user flow

## Usage Examples

### Basic Profile Management

```python
from src.data.auto_profile_manager import AutoProfileManager
from supabase import create_client

# Initialize
client = create_client(supabase_url, service_role_key)
profile_manager = AutoProfileManager(client, testing_mode=True)

# Create profile manually (if needed)
result = profile_manager.create_profile_automatically(user_id)
if result.success:
    print(f"Profile created: {result.profile_id}")
else:
    print(f"Error: {result.error_details}")

# Get user profile
profile = profile_manager.get_profile(user_id)
if profile:
    print(f"Experience: {profile['years_of_experience']} years")
    print(f"Level: {profile['experience_level']}")

# Update profile
updates = {
    "years_of_experience": 3,
    "experience_level": "mid",
    "education_level": "masters"
}
result = profile_manager.update_profile(user_id, updates)
```

### Integration with Auth System

```python
from src.auth.profile_integration import ProfileAuthIntegration

# Initialize integration
integration = ProfileAuthIntegration(client, testing_mode=True)

# Handle user registration
user_data = {"email": "user@example.com", "full_name": "John Doe"}
result = integration.handle_user_registration(user_id, user_data)

# Verify user profile
has_profile, profile_info = integration.verify_user_profile(user_id)
if has_profile:
    print(f"Profile complete: {profile_info['is_complete']}")

# Get complete user data
user_data = integration.get_user_profile_data(user_id)
print(f"Email: {user_data['email']}")
print(f"Profile complete: {user_data['profile_complete']}")
```

### Profile Completion Status

```python
# Check profile completion
is_complete, details = profile_manager.get_profile_completion_status(user_id)
print(f"Complete: {is_complete}")
print(f"Completion: {details['completion_percentage']}%")
print(f"Missing fields: {details['missing_fields']}")
```

## API Reference

### AutoProfileManager

#### `create_profile_automatically(user_id: str) -> ProfileCreationResult`

Creates a profile with default values for a user.

**Parameters:**
- `user_id`: The user ID from Supabase Auth

**Returns:**
- `ProfileCreationResult` with success status and details

#### `get_profile(user_id: str) -> Optional[Dict[str, Any]]`

Retrieves a user's profile.

**Parameters:**
- `user_id`: The user ID

**Returns:**
- Profile data dictionary or None if not found

#### `update_profile(user_id: str, updates: Dict[str, Any]) -> ProfileCreationResult`

Updates a user's profile.

**Parameters:**
- `user_id`: The user ID
- `updates`: Dictionary of fields to update

**Returns:**
- `ProfileCreationResult` with operation details

#### `get_profile_completion_status(user_id: str) -> Tuple[bool, Dict[str, Any]]`

Gets the completion status of a user's profile.

**Parameters:**
- `user_id`: The user ID

**Returns:**
- Tuple of (is_complete, completion_details)

### ProfileAuthIntegration

#### `handle_user_registration(user_id: str, user_data: Dict[str, Any]) -> ProfileCreationResult`

Handles automatic profile creation during user registration.

#### `verify_user_profile(user_id: str) -> Tuple[bool, Dict[str, Any]]`

Verifies that a user has a profile and gets its status.

#### `get_user_profile_data(user_id: str) -> Optional[Dict[str, Any]]`

Gets complete user data including auth and profile information.

#### `update_user_profile(user_id: str, updates: Dict[str, Any]) -> ProfileCreationResult`

Updates a user's profile with validation and logging.

## Profile Fields

### Required Fields (for completion)

- `years_of_experience`: Integer
- `experience_level`: One of ["entry", "junior", "mid", "senior", "lead", "executive"]
- `education_level`: One of ["high_school", "associates", "bachelors", "masters", "phd", "other"]

### Optional Fields

- `field_of_study`: String
- `skills_technologies`: Array of strings
- `work_arrangement_preference`: One of ["any", "remote", "hybrid", "on_site"]
- `preferred_locations`: Array of strings
- `salary_min`: Integer
- `salary_max`: Integer
- `salary_currency`: String (default: "USD")

## Error Handling

The system provides comprehensive error handling:

### Common Error Types

1. **Profile Already Exists**: When trying to create a duplicate profile
2. **User Not Found**: When the auth user doesn't exist
3. **Invalid Data**: When profile data doesn't pass validation
4. **Database Errors**: When database operations fail

### Error Response Format

```python
ProfileCreationResult(
    success=False,
    message="Error description",
    user_id="user_id",
    error_details="Detailed error information"
)
```

## Logging

The system provides detailed logging for debugging:

### Log Levels

- **INFO**: Normal operations (profile creation, updates)
- **WARNING**: Non-critical issues (profile already exists)
- **ERROR**: Critical issues (database errors, validation failures)
- **DEBUG**: Detailed information (in testing mode)

### Log Format

```
2024-01-15 10:30:45 - src.data.auto_profile_manager - INFO - Creating automatic profile for user: 123e4567-e89b-12d3-a456-426614174000
```

## Testing

### Testing Mode

Set `TESTING_MODE=true` in your environment for:
- Enhanced logging
- Immediate profile creation
- Detailed error messages

### Test Scripts

1. **Setup Test**: `scripts/setup_auto_profile_creation.py`
2. **System Test**: `scripts/test_auto_profile_system.py`

### Manual Testing

```python
# Test profile creation
result = profile_manager.create_profile_automatically(test_user_id)
assert result.success

# Test profile retrieval
profile = profile_manager.get_profile(test_user_id)
assert profile is not None
assert profile['years_of_experience'] == 0
```

## Troubleshooting

### Common Issues

1. **Profile Not Created Automatically**
   - Check if the database trigger exists
   - Verify the trigger function is working
   - Check logs for error messages

2. **Permission Errors**
   - Ensure service role key has admin privileges
   - Check RLS policies are correctly set

3. **Validation Errors**
   - Verify profile data matches expected format
   - Check enum values are correct

### Debug Steps

1. Check environment variables are set correctly
2. Run the setup script to verify database schema
3. Run the test script to identify issues
4. Check logs for detailed error messages
5. Verify Supabase client has correct permissions

## Production Deployment

### Environment Setup

1. Set `TESTING_MODE=false`
2. Use production Supabase credentials
3. Ensure service role key has necessary permissions

### Monitoring

1. Monitor profile creation logs
2. Track profile completion rates
3. Monitor error rates and types
4. Set up alerts for critical failures

### Backup Strategy

1. Regular database backups
2. Profile data export functionality
3. Recovery procedures for data loss

## Security Considerations

1. **Row Level Security**: All profile operations respect RLS policies
2. **Input Validation**: All profile data is validated before saving
3. **Error Handling**: Sensitive information is not exposed in error messages
4. **Audit Logging**: All operations are logged for security monitoring

## Performance Considerations

1. **Database Indexes**: User ID is indexed for fast lookups
2. **Trigger Efficiency**: Database triggers are optimized for performance
3. **Connection Pooling**: Supabase client handles connection management
4. **Caching**: Consider caching frequently accessed profile data

## Future Enhancements

1. **Profile Templates**: Pre-defined profile templates for different roles
2. **Bulk Operations**: Batch profile creation and updates
3. **Profile Analytics**: Track profile completion trends
4. **Integration APIs**: REST APIs for external integrations
5. **Profile Migration**: Tools for migrating existing user data

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review the test scripts for examples
3. Check the logs for detailed error information
4. Verify your Supabase project configuration

## Changelog

### Version 1.0.0
- Initial implementation
- Database trigger-based automatic profile creation
- Comprehensive Python backend integration
- Full testing suite
- Complete documentation 