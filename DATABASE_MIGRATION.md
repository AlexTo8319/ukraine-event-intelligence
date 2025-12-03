# Database Migration Guide

## Adding New Fields to Events Table

To add the new fields (`event_time`, `target_audience`, `registration_url`) to your Supabase database:

### Step 1: Open Supabase SQL Editor

1. Go to: https://supabase.com/dashboard
2. Select your project: `qjuaqnhwpwmywgshghpq`
3. Click on **SQL Editor** in the left sidebar
4. Click **New Query**

### Step 2: Run the Migration SQL

Copy and paste this SQL into the editor:

```sql
-- Migration: Add new fields to events table
-- Add new columns
ALTER TABLE events 
ADD COLUMN IF NOT EXISTS event_time TIME,
ADD COLUMN IF NOT EXISTS target_audience TEXT,
ADD COLUMN IF NOT EXISTS registration_url TEXT;

-- Add index on registration_url for faster lookups
CREATE INDEX IF NOT EXISTS idx_events_registration_url ON events(registration_url) WHERE registration_url IS NOT NULL;

-- Add comments for documentation
COMMENT ON COLUMN events.event_time IS 'Time of the event (HH:MM format)';
COMMENT ON COLUMN events.target_audience IS 'Target audience (e.g., Donors, Government Officials, Architects)';
COMMENT ON COLUMN events.registration_url IS 'Direct link to event registration page';
COMMENT ON COLUMN events.url IS 'Source URL where event information was found';
COMMENT ON COLUMN events.summary IS '1-2 sentence description of the event';
```

### Step 3: Execute

Click **Run** or press `Ctrl+Enter` (or `Cmd+Enter` on Mac)

### Step 4: Verify

Run this query to verify the new columns exist:

```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'events'
ORDER BY ordinal_position;
```

You should see:
- `event_time` (TIME, nullable)
- `target_audience` (TEXT, nullable)
- `registration_url` (TEXT, nullable)

## Notes

- Existing events will have `NULL` values for these new fields
- The research agent will populate these fields for new events going forward
- Old events can be updated manually if needed




