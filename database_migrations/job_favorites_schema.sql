-- ===================================
-- JOB FAVORITES TABLE SCHEMA
-- ===================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create job_favorites table
CREATE TABLE IF NOT EXISTS job_favorites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    job_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    
    -- Unique constraint to prevent duplicate favorites
    CONSTRAINT unique_user_job_favorite UNIQUE (user_id, job_id)
);

-- Add foreign key constraint (requires jobs table to exist)
-- Note: This will only work if jobs table already exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'jobs') THEN
        ALTER TABLE job_favorites ADD CONSTRAINT IF NOT EXISTS fk_job_favorites_job_id 
            FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE;
    END IF;
END $$;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_job_favorites_user_id ON job_favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_job_favorites_job_id ON job_favorites(job_id);
CREATE INDEX IF NOT EXISTS idx_job_favorites_created_at ON job_favorites(created_at DESC);

-- Create composite index for common queries
CREATE INDEX IF NOT EXISTS idx_job_favorites_user_created ON job_favorites(user_id, created_at DESC);

-- Enable Row Level Security
ALTER TABLE job_favorites ENABLE ROW LEVEL SECURITY;

-- RLS Policies (for Supabase)
CREATE POLICY "Users can view own favorites" ON job_favorites
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own favorites" ON job_favorites
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own favorites" ON job_favorites
    FOR DELETE USING (auth.uid() = user_id);

-- Grant permissions
GRANT ALL ON job_favorites TO authenticated;

-- Add comments
COMMENT ON TABLE job_favorites IS 'User favorite job postings for quick access and bookmarking';
COMMENT ON COLUMN job_favorites.user_id IS 'Reference to the user who favorited the job';
COMMENT ON COLUMN job_favorites.job_id IS 'Reference to the favorited job posting';
COMMENT ON COLUMN job_favorites.created_at IS 'When the job was added to favorites';