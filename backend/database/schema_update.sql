-- Migration: Add new fields to events table
-- Run this in Supabase SQL Editor

-- Add new columns
ALTER TABLE events 
ADD COLUMN IF NOT EXISTS event_time TIME,
ADD COLUMN IF NOT EXISTS target_audience TEXT,
ADD COLUMN IF NOT EXISTS registration_url TEXT;

-- Add index on registration_url for faster lookups
CREATE INDEX IF NOT EXISTS idx_events_registration_url ON events(registration_url) WHERE registration_url IS NOT NULL;

-- Add comment for documentation
COMMENT ON COLUMN events.event_time IS 'Time of the event (HH:MM format)';
COMMENT ON COLUMN events.target_audience IS 'Target audience (e.g., Donors, Government Officials, Architects)';
COMMENT ON COLUMN events.registration_url IS 'Direct link to event registration page';
COMMENT ON COLUMN events.url IS 'Source URL where event information was found';
COMMENT ON COLUMN events.summary IS '1-2 sentence description of the event';

