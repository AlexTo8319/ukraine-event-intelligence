-- SQL Script to enable DELETE permissions for anon users
-- Run this in Supabase SQL Editor (Dashboard > SQL Editor)

-- Option 1: Allow deletes for anon users (less secure, but simpler)
DROP POLICY IF EXISTS "Allow delete for anon" ON events;
CREATE POLICY "Allow delete for anon" ON events
    FOR DELETE
    USING (true);

-- Verify the policy was created
SELECT * FROM pg_policies WHERE tablename = 'events';



