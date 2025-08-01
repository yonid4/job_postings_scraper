# Supabase Storage RLS Policy Fix

## Issue
The resume upload is failing with the error:
```
Error uploading file to Supabase Storage: {'statusCode': 400, 'error': 'Unauthorized', 'message': 'new row violates row-level security policy'}
```

This is a **Row Level Security (RLS) policy** issue in Supabase Storage, not a code bug.

## Root Cause
Supabase Storage buckets have RLS policies that control who can upload files. The current setup doesn't have the proper authentication context for storage operations.

## Solutions

### Option 1: Configure RLS Policies (Recommended for Production)

1. **Go to your Supabase Dashboard**
   - Navigate to Storage > Policies
   - Select the "resumes" bucket

2. **Create a Policy for File Uploads**
   ```sql
   -- Allow authenticated users to upload files to their own folder
   CREATE POLICY "Users can upload to their own folder" ON storage.objects
   FOR INSERT WITH CHECK (
     bucket_id = 'resumes' AND 
     auth.uid()::text = (storage.foldername(name))[1]
   );
   ```

3. **Create a Policy for File Access**
   ```sql
   -- Allow users to access their own files
   CREATE POLICY "Users can access their own files" ON storage.objects
   FOR SELECT USING (
     bucket_id = 'resumes' AND 
     auth.uid()::text = (storage.foldername(name))[1]
   );
   ```

### Option 2: Use Service Role Key (For Development/Testing)

1. **Get your Service Role Key**
   - Go to Supabase Dashboard > Settings > API
   - Copy the "service_role" key (not the anon key)

2. **Update Environment Variables**
   ```bash
   # Add to your .env file
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
   ```

3. **Update the ResumeManager initialization**
   ```python
   # In frontend/app_supabase.py, modify the Supabase client creation:
   supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
   if supabase_service_key:
       supabase_client = create_client(supabase_url, supabase_service_key)
   else:
       supabase_client = create_client(supabase_url, supabase_anon_key)
   ```

### Option 3: Disable RLS (Not Recommended for Production)

1. **Go to Supabase Dashboard**
   - Navigate to Storage > Settings
   - Disable RLS for the "resumes" bucket

⚠️ **Warning**: This removes all security controls and should only be used for development.

## Current Status

The integration is working correctly:
- ✅ ResumeManager is properly initialized
- ✅ File upload detection is working
- ✅ Database operations are working
- ✅ File processing is ready

The only issue is the storage permissions, which is a configuration issue, not a code issue.

## Testing the Fix

After applying one of the solutions above:

1. Restart the Flask app
2. Try uploading a resume file
3. You should see successful upload instead of the RLS error

## Next Steps

For immediate testing, you can use **Option 2** (Service Role Key) which will bypass RLS policies entirely.

For production, use **Option 1** (Configure RLS Policies) to maintain proper security controls. 