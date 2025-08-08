-- ===================================
-- JOB SEARCHES TABLE SCHEMA
-- ===================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create job_searches table
CREATE TABLE IF NOT EXISTS job_searches (
    search_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    keywords TEXT[], -- Array of search keywords
    location VARCHAR(255),
    filters JSONB, -- JSON object containing search filters
    results_count INTEGER DEFAULT 0,
    search_date TIMESTAMP WITH TIME ZONE DEFAULT now(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    
    -- Constraints
    CONSTRAINT valid_results_count CHECK (
        results_count >= 0
    )
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_job_searches_user_id ON job_searches(user_id);
CREATE INDEX IF NOT EXISTS idx_job_searches_search_date ON job_searches(search_date DESC);
CREATE INDEX IF NOT EXISTS idx_job_searches_results_count ON job_searches(results_count);
CREATE INDEX IF NOT EXISTS idx_job_searches_location ON job_searches(location);

-- Create composite index for common queries
CREATE INDEX IF NOT EXISTS idx_job_searches_user_date ON job_searches(user_id, search_date DESC);

-- Create GIN index for JSONB filters column for efficient JSON queries
CREATE INDEX IF NOT EXISTS idx_job_searches_filters_gin ON job_searches USING GIN (filters);

-- Create GIN index for keywords array for efficient array searches
CREATE INDEX IF NOT EXISTS idx_job_searches_keywords_gin ON job_searches USING GIN (keywords);

-- Enable Row Level Security
ALTER TABLE job_searches ENABLE ROW LEVEL SECURITY;

-- RLS Policies (for Supabase)
CREATE POLICY "Users can view own searches" ON job_searches
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own searches" ON job_searches
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own searches" ON job_searches
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own searches" ON job_searches
    FOR DELETE USING (auth.uid() = user_id);

-- Grant permissions
GRANT ALL ON job_searches TO authenticated;

-- Add comments
COMMENT ON TABLE job_searches IS 'History of job searches performed by users with filters and results';
COMMENT ON COLUMN job_searches.keywords IS 'Array of search keywords used in the job search';
COMMENT ON COLUMN job_searches.filters IS 'JSONB containing search filters (work arrangement, experience level, job type, date posted, etc.)';
COMMENT ON COLUMN job_searches.results_count IS 'Number of job results found for this search';
COMMENT ON COLUMN job_searches.search_date IS 'When the search was performed';

-- Example of filters JSONB structure:
/*
{
  "work_arrangement": "remote",
  "experience_level": "mid",
  "job_type": "full-time",
  "date_posted": "past_week",
  "salary_min": 80000,
  "salary_max": 120000,
  "company_size": "startup"
}
*/