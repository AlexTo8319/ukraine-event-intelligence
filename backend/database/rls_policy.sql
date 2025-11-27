-- Row Level Security (RLS) Policies for Events Table
-- Run this after creating the events table

-- Enable RLS on events table
ALTER TABLE events ENABLE ROW LEVEL SECURITY;

-- Policy: Allow public read access to events
-- This allows the frontend (using anon key) to read events
CREATE POLICY "Allow public read access to events"
ON events
FOR SELECT
TO anon, authenticated
USING (true);

-- Note: INSERT and UPDATE operations are restricted to service role only
-- This is the default behavior - only the backend (with service role key) can write
-- No policy is needed for INSERT/UPDATE as they will be denied by default for anon users

-- Optional: If you want to allow authenticated users to insert their own events
-- (not recommended for this use case, but included for reference)
-- CREATE POLICY "Allow authenticated users to insert events"
-- ON events
-- FOR INSERT
-- TO authenticated
-- WITH CHECK (true);

