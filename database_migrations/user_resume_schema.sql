-- ===================================
-- USER RESUME TABLE SCHEMA
-- ===================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create user_resume table
CREATE TABLE IF NOT EXISTS user_resume (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    is_processed BOOLEAN DEFAULT false,
    processed_data JSONB,
    processing_error TEXT,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    processed_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    file_size INTEGER,
    file_type TEXT,
    is_active BOOLEAN DEFAULT true,
    
    -- Constraints
    CONSTRAINT valid_file_size CHECK (
        file_size IS NULL OR file_size > 0
    ),
    CONSTRAINT valid_file_type CHECK (
        file_type IS NULL OR file_type IN ('pdf', 'doc', 'docx', 'txt')
    ),
    CONSTRAINT unique_user_file_hash UNIQUE (user_id, file_hash)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_resume_user_id ON user_resume(user_id);
CREATE INDEX IF NOT EXISTS idx_user_resume_is_active ON user_resume(is_active);
CREATE INDEX IF NOT EXISTS idx_user_resume_is_processed ON user_resume(is_processed);
CREATE INDEX IF NOT EXISTS idx_user_resume_file_hash ON user_resume(file_hash);
CREATE INDEX IF NOT EXISTS idx_user_resume_uploaded_at ON user_resume(uploaded_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_resume_file_type ON user_resume(file_type);

-- Create composite index for common queries
CREATE INDEX IF NOT EXISTS idx_user_resume_user_active ON user_resume(user_id, is_active);

-- Enable Row Level Security
ALTER TABLE user_resume ENABLE ROW LEVEL SECURITY;

-- RLS Policies (for Supabase)
CREATE POLICY "Users can view own resume" ON user_resume
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own resume" ON user_resume
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own resume" ON user_resume
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own resume" ON user_resume
    FOR DELETE USING (auth.uid() = user_id);

-- Grant permissions
GRANT ALL ON user_resume TO authenticated;

-- Add comments
COMMENT ON TABLE user_resume IS 'User uploaded resumes with processing status and extracted data';
COMMENT ON COLUMN user_resume.processed_data IS 'JSONB containing extracted resume data (skills, experience, education, etc.)';
COMMENT ON COLUMN user_resume.file_hash IS 'Hash of file content to prevent duplicate uploads';
COMMENT ON COLUMN user_resume.storage_path IS 'Path to file in cloud storage (e.g., Supabase Storage)';
COMMENT ON COLUMN user_resume.is_processed IS 'Boolean indicating if AI has processed this resume';
COMMENT ON COLUMN user_resume.is_active IS 'Boolean indicating if this is the currently active resume';
COMMENT ON COLUMN user_resume.last_used_at IS 'Timestamp when this resume was last used for job analysis';