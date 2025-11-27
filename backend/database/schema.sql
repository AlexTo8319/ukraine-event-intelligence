-- Create events table
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

-- Create index on URL for fast duplicate checking
CREATE INDEX IF NOT EXISTS idx_events_url ON events(url);

-- Create index on event_date for efficient filtering
CREATE INDEX IF NOT EXISTS idx_events_date ON events(event_date);

-- Create index on category for filtering
CREATE INDEX IF NOT EXISTS idx_events_category ON events(category);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_events_updated_at BEFORE UPDATE ON events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

