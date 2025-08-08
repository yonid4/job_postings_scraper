-- ===================================
-- APPLICATIONS TABLE SCHEMA
-- ===================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create applications table
CREATE TABLE IF NOT EXISTS applications (
    application_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    job_id UUID NOT NULL,
    application_method VARCHAR(20) NOT NULL,
    applied_date TIMESTAMP WITH TIME ZONE DEFAULT now(),
    application_status VARCHAR(50) DEFAULT 'applied'::character varying,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    
    -- Constraints
    CONSTRAINT valid_application_method CHECK (
        application_method IN ('linkedin', 'company_website', 'email', 'recruiter', 'referral', 'job_board', 'other')
    ),
    CONSTRAINT valid_application_status CHECK (
        application_status IN ('applied', 'screening', 'interview', 'technical', 'final', 'offer', 'rejected', 'withdrawn', 'pending')
    ),
    
    -- Unique constraint to prevent duplicate applications
    CONSTRAINT unique_user_job_application UNIQUE (user_id, job_id)
);

-- Add foreign key constraint (requires jobs table to exist)
-- Note: This will only work if jobs table already exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'jobs') THEN
        ALTER TABLE applications ADD CONSTRAINT IF NOT EXISTS fk_applications_job_id 
            FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE;
    END IF;
END $$;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications(user_id);
CREATE INDEX IF NOT EXISTS idx_applications_job_id ON applications(job_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(application_status);
CREATE INDEX IF NOT EXISTS idx_applications_applied_date ON applications(applied_date DESC);
CREATE INDEX IF NOT EXISTS idx_applications_method ON applications(application_method);

-- Create composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_applications_user_status ON applications(user_id, application_status);
CREATE INDEX IF NOT EXISTS idx_applications_user_date ON applications(user_id, applied_date DESC);

-- Enable Row Level Security
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;

-- RLS Policies (for Supabase)
CREATE POLICY "Users can view own applications" ON applications
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own applications" ON applications
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own applications" ON applications
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own applications" ON applications
    FOR DELETE USING (auth.uid() = user_id);

-- Create trigger function for updated_at
CREATE OR REPLACE FUNCTION update_applications_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger
DROP TRIGGER IF EXISTS update_applications_updated_at ON applications;
CREATE TRIGGER update_applications_updated_at 
    BEFORE UPDATE ON applications 
    FOR EACH ROW 
    EXECUTE FUNCTION update_applications_updated_at();

-- Grant permissions
GRANT ALL ON applications TO authenticated;

-- Add comments
COMMENT ON TABLE applications IS 'Job applications submitted by users with tracking information';
COMMENT ON COLUMN applications.application_method IS 'How the user applied for the job (linkedin, company_website, etc.)';
COMMENT ON COLUMN applications.application_status IS 'Current status of the application in the hiring process';
COMMENT ON COLUMN applications.notes IS 'User notes about the application, interviews, or follow-ups';
COMMENT ON COLUMN applications.applied_date IS 'When the user actually applied for the job';