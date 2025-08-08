-- ===================================
-- USER PROFILES TABLE SCHEMA
-- ===================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create user_profiles table
CREATE TABLE IF NOT EXISTS user_profiles (
    profile_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    years_of_experience INTEGER,
    experience_level TEXT DEFAULT ''::text,
    education_level TEXT DEFAULT ''::text,
    field_of_study TEXT,
    skills_technologies TEXT[], -- Array of skills
    work_arrangement_preference TEXT DEFAULT 'any'::text,
    preferred_locations TEXT[], -- Array of preferred locations
    salary_min INTEGER,
    salary_max INTEGER,
    salary_currency TEXT DEFAULT 'USD'::text,
    score_threshold INTEGER DEFAULT 70,
    job_limit INTEGER DEFAULT 25,
    profile_completed BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    
    -- Constraints
    CONSTRAINT valid_salary_range_profiles CHECK (
        salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max
    ),
    CONSTRAINT valid_years_experience CHECK (
        years_of_experience IS NULL OR years_of_experience >= 0
    ),
    CONSTRAINT valid_work_arrangement_preference CHECK (
        work_arrangement_preference IN ('any', 'remote', 'hybrid', 'onsite')
    ),
    CONSTRAINT valid_score_threshold CHECK (
        score_threshold IS NULL OR (score_threshold >= 0 AND score_threshold <= 100)
    ),
    CONSTRAINT valid_job_limit CHECK (
        job_limit IS NULL OR (job_limit >= 1 AND job_limit <= 100)
    )
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_profile_completed ON user_profiles(profile_completed);
CREATE INDEX IF NOT EXISTS idx_user_profiles_experience_level ON user_profiles(experience_level);
CREATE INDEX IF NOT EXISTS idx_user_profiles_work_arrangement ON user_profiles(work_arrangement_preference);
CREATE INDEX IF NOT EXISTS idx_user_profiles_score_threshold ON user_profiles(score_threshold);
CREATE INDEX IF NOT EXISTS idx_user_profiles_job_limit ON user_profiles(job_limit);

-- Enable Row Level Security
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- RLS Policies (for Supabase)
CREATE POLICY "Users can view own profile" ON user_profiles
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own profile" ON user_profiles
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own profile" ON user_profiles
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own profile" ON user_profiles
    FOR DELETE USING (auth.uid() = user_id);

-- Create trigger function for updated_at
CREATE OR REPLACE FUNCTION update_user_profiles_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger
DROP TRIGGER IF EXISTS update_user_profiles_updated_at ON user_profiles;
CREATE TRIGGER update_user_profiles_updated_at 
    BEFORE UPDATE ON user_profiles 
    FOR EACH ROW 
    EXECUTE FUNCTION update_user_profiles_updated_at();

-- Grant permissions
GRANT ALL ON user_profiles TO authenticated;

-- Add comments
COMMENT ON TABLE user_profiles IS 'User profile information including skills, experience, and job preferences';
COMMENT ON COLUMN user_profiles.skills_technologies IS 'Array of user skills and technologies';
COMMENT ON COLUMN user_profiles.preferred_locations IS 'Array of preferred work locations';
COMMENT ON COLUMN user_profiles.score_threshold IS 'Minimum AI qualification score (0-100) for job recommendations';
COMMENT ON COLUMN user_profiles.job_limit IS 'Maximum number of jobs to process/display per search session (1-100)';
COMMENT ON COLUMN user_profiles.profile_completed IS 'Boolean flag indicating if profile setup is complete';