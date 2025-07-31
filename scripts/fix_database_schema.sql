-- Database Schema Fix Script
-- This script updates the foreign key constraints to reference user_profiles instead of users

-- Step 1: Drop existing foreign key constraints
ALTER TABLE job_searches DROP CONSTRAINT IF EXISTS job_searches_user_id_fkey;
ALTER TABLE jobs DROP CONSTRAINT IF EXISTS jobs_user_id_fkey;
ALTER TABLE applications DROP CONSTRAINT IF EXISTS applications_user_id_fkey;

-- Step 2: Add new foreign key constraints referencing auth.users(id)
ALTER TABLE job_searches ADD CONSTRAINT job_searches_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

ALTER TABLE jobs ADD CONSTRAINT jobs_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

ALTER TABLE applications ADD CONSTRAINT applications_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

-- Step 3: Update job_searches table to use TEXT[] for keywords
-- First, create a temporary column
ALTER TABLE job_searches ADD COLUMN keywords_array TEXT[];

-- Update the temporary column with the existing keywords data
UPDATE job_searches SET keywords_array = ARRAY[keywords] WHERE keywords IS NOT NULL;

-- Drop the old column and rename the new one
ALTER TABLE job_searches DROP COLUMN keywords;
ALTER TABLE job_searches RENAME COLUMN keywords_array TO keywords;

-- Step 4: Verify the changes
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name IN ('job_searches', 'jobs', 'applications', 'user_profiles')
ORDER BY table_name, ordinal_position;

-- Step 5: Check foreign key constraints
SELECT 
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM 
    information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
      AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY' 
    AND tc.table_name IN ('job_searches', 'jobs', 'applications'); 