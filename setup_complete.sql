-- ============================================================
-- COMPLETE DATABASE SETUP SQL
-- Run this in Supabase SQL Editor
-- ============================================================
-- URL: https://supabase.com/dashboard/project/qjuaqnhwpwmywgshghpq/sql
-- ============================================================

-- Step 1: Create events table
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_title TEXT NOT NULL,
    event_date DATE NOT NULL,
    organizer TEXT,
    url TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('Legislation', 'Housing', 'Recovery', 'General')),
    is_online BOOLEAN DEFAULT FALSE,
    summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Step 2: Create indexes
CREATE INDEX IF NOT EXISTS idx_events_url ON events(url);
CREATE INDEX IF NOT EXISTS idx_events_date ON events(event_date);
CREATE INDEX IF NOT EXISTS idx_events_category ON events(category);

-- Step 3: Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Step 4: Create trigger
CREATE TRIGGER update_events_updated_at BEFORE UPDATE ON events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Step 5: Enable Row Level Security
ALTER TABLE events ENABLE ROW LEVEL SECURITY;

-- Step 6: Create RLS policy for public read access
CREATE POLICY "Allow public read access to events"
ON events
FOR SELECT
TO anon, authenticated
USING (true);

-- ============================================================
-- Setup Complete!
-- ============================================================

