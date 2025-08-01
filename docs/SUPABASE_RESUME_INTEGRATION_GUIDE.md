# Supabase Resume Management Integration Guide

This guide explains the integration of the existing resume management system with Supabase Storage and database, providing cloud-based resume storage and processing capabilities.

## Overview

The resume management system has been enhanced to work with Supabase while maintaining all existing functionality. The key changes are:

- **Storage**: Files are now stored in Supabase Storage buckets instead of local filesystem
- **Database**: Resume metadata is stored in Supabase PostgreSQL database
- **Processing**: Lazy processing remains the same, but files are downloaded from storage for processing
- **API**: All existing method signatures are preserved for backward compatibility

## Database Schema

### User Resume Table

The `user_resume` table stores resume metadata and processing status:

```sql
CREATE TABLE user_resume (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,           -- Public URL for file access
    storage_path TEXT,                 -- Internal storage path for management
    file_hash TEXT NOT NULL,
    is_processed BOOLEAN DEFAULT FALSE,
    processed_data JSONB,              -- AI-processed resume data
    processing_error TEXT,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    file_size INTEGER,
    file_type TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

-- Indexes for performance
CREATE INDEX idx_user_resume_user_id ON user_resume(user_id);
CREATE INDEX idx_user_resume_file_hash ON user_resume(file_hash);
CREATE INDEX idx_user_resume_uploaded_at ON user_resume(uploaded_at);
```

### Storage Bucket

The `resumes` bucket stores the actual files with the following structure:
```
resumes/
├── {user_id}/
│   ├── {timestamp}_{filename}
│   └── {timestamp}_{filename}
└── {user_id}/
    └── {timestamp}_{filename}
```

## Key Components

### 1. ResumeManager (Modified)

The `ResumeManager` class has been updated to work with Supabase:

```python
# Old initialization
resume_manager = ResumeManager(db_path, upload_folder, ai_client)

# New initialization
resume_manager = ResumeManager(
    supabase_client=supabase_client,
    bucket_name="resumes",
    ai_client=ai_client
)
```

#### Key Changes:

- **Constructor**: Now accepts `supabase_client` and `bucket_name` instead of `db_path` and `upload_folder`
- **File Upload**: Files are uploaded to Supabase Storage with path format `{user_id}/{timestamp}_{filename}`
- **Database Operations**: All database operations use Supabase syntax
- **File Processing**: Files are downloaded from storage to temporary location for processing
- **Cleanup**: Automatic cleanup of temporary files and old storage files

#### Preserved Methods:

All existing method signatures remain the same:
- `upload_resume(user_id, file_path, filename)`
- `ensure_resume_processed(user_id)`
- `get_resume_status(user_id)`
- `get_latest_user_resume(user_id)`
- `get_resume_by_hash(user_id, file_hash)`

### 2. ResumeProcessor (Unchanged)

The `ResumeProcessor` class remains unchanged and works with any file path, including temporary downloaded files.

### 3. Resume Model (Enhanced)

The `Resume` model now includes a `storage_path` field:

```python
@dataclass
class Resume:
    # ... existing fields ...
    file_path: str = ""  # Public URL for file access
    storage_path: Optional[str] = None  # Internal storage path for management
    # ... rest of fields ...
```

## File Storage Flow

### Upload Process

1. **File Upload**: User uploads file via Flask endpoint
2. **Temporary Storage**: File is saved to temporary location
3. **Supabase Upload**: File is uploaded to Supabase Storage bucket
4. **Database Record**: Resume metadata is stored in database
5. **Cleanup**: Temporary file is deleted
6. **Response**: Success/error response returned to user

### Processing Process

1. **Status Check**: Check if resume is already processed
2. **Download**: Download file from Supabase Storage to temporary location
3. **Process**: Process file with AI (if available)
4. **Update Database**: Store processed data and update status
5. **Cleanup**: Delete temporary file
6. **Return**: Return processed data or None

## API Endpoints

### Resume Upload
```
POST /resume/upload
Content-Type: multipart/form-data

Form data:
- file: Resume file (PDF or DOCX)
```

### Resume Status
```
GET /resume/status
```

### Resume Processing
```
POST /resume/process
```

### Resume Download
```
GET /resume/download
```

### Resume Deletion
```
DELETE /resume/delete
```

## Integration Points

### 1. Flask Application

The Flask app has been updated to use the new ResumeManager:

```python
# Initialize with Supabase (if available)
try:
    supabase_client = create_client(supabase_url, supabase_anon_key)
    resume_manager = ResumeManager(
        supabase_client=supabase_client,
        bucket_name="resumes",
        ai_client=qualification_analyzer
    )
except:
    # Fallback to local storage
    resume_manager = ResumeManager(db_path, upload_folder)
```

### 2. Job Scraping Integration

Before job scraping, the system ensures resume is processed:

```python
# Use existing method - this handles lazy processing
processed_data = resume_manager.ensure_resume_processed(user_id)
if processed_data:
    # Use processed resume data for job matching
    pass
else:
    # Fall back to basic profile or show error
    pass
```

### 3. Resume Status Check

```python
# Use existing method
status = resume_manager.get_resume_status(user_id)
```

## Error Handling

### Storage Errors
- Handle Supabase Storage upload/download errors gracefully
- Fall back to basic profile if resume processing fails
- Store processing errors in database for debugging

### Network Errors
- Implement retry logic for storage operations
- Provide meaningful error messages to users
- Log all errors for debugging

## Performance Considerations

### Lazy Processing
- Resume processing only happens when needed (during job searches)
- Processed data is cached in database
- Avoid unnecessary file downloads

### Storage Optimization
- Use signed URLs for temporary file access during processing
- Implement file cleanup for old resumes
- Monitor storage usage and costs

### Caching
- Cache processed resume data in database
- Avoid re-processing already processed resumes
- Use efficient database queries with proper indexing

## Security

### Row Level Security (RLS)
The database uses RLS policies to ensure users can only access their own resumes:

```sql
-- Policy for user_resume table
CREATE POLICY "Users can only access their own resumes"
ON user_resume FOR ALL
USING (auth.uid() = user_id);
```

### Storage Security
- Files are stored in user-specific folders
- Public URLs are generated for file access
- Storage bucket has appropriate access policies

## Testing

### Test Script
Run the integration test script:

```bash
python tests/test_supabase_resume_integration.py
```

### Manual Testing
1. Upload a resume file
2. Check resume status
3. Trigger resume processing
4. Verify processed data
5. Test file download
6. Test resume deletion

## Migration from Local Storage

### Automatic Fallback
The system automatically falls back to local storage if Supabase is not configured:

```python
# Check for Supabase credentials
if supabase_url and supabase_anon_key:
    # Use Supabase
    resume_manager = ResumeManager(supabase_client, bucket_name)
else:
    # Fallback to local storage
    resume_manager = ResumeManager(db_path, upload_folder)
```

### Data Migration
To migrate existing resumes to Supabase:

1. Export existing resume data
2. Upload files to Supabase Storage
3. Update database records with new URLs
4. Verify all functionality works

## Configuration

### Environment Variables
```bash
SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### Supabase Setup
1. Create a new Supabase project
2. Create the `user_resume` table with the provided schema
3. Create a `resumes` storage bucket
4. Configure RLS policies
5. Set up environment variables

## Troubleshooting

### Common Issues

1. **Upload Fails**: Check Supabase credentials and bucket permissions
2. **Processing Fails**: Verify AI client configuration and file format
3. **Download Fails**: Check storage bucket policies and file existence
4. **Database Errors**: Verify table schema and RLS policies

### Debug Logging
Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Best Practices

1. **File Validation**: Always validate file types and sizes
2. **Error Handling**: Implement comprehensive error handling
3. **Cleanup**: Always clean up temporary files
4. **Security**: Use RLS policies and secure storage access
5. **Performance**: Implement lazy processing and caching
6. **Monitoring**: Log all operations for debugging and monitoring

## Future Enhancements

1. **File Versioning**: Support multiple resume versions per user
2. **Advanced Processing**: Enhanced AI processing with multiple models
3. **Analytics**: Track resume usage and processing statistics
4. **Integration**: Connect with job application systems
5. **Mobile Support**: Optimize for mobile file uploads 