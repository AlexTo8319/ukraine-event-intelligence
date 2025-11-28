#!/bin/bash
# Simple migration helper - opens Supabase SQL Editor with instructions

echo "🚀 Database Migration Helper"
echo "============================"
echo ""
echo "Since Supabase doesn't allow automated SQL execution for security,"
echo "you need to run the migration manually (takes 2 minutes)."
echo ""
echo "📋 STEP 1: Open Supabase SQL Editor"
echo "   URL: https://supabase.com/dashboard/project/qjuaqnhwpwmywgshghpq/sql"
echo ""
echo "📋 STEP 2: Copy this SQL:"
echo "----------------------------------------"
cat backend/database/schema_update.sql
echo "----------------------------------------"
echo ""
echo "📋 STEP 3: Paste into SQL Editor and click 'Run'"
echo ""
echo "📋 STEP 4: Verify migration:"
echo "   python3 backend/database/verify_migration.py"
echo ""
echo "Opening Supabase dashboard..."
open "https://supabase.com/dashboard/project/qjuaqnhwpwmywgshghpq/sql" 2>/dev/null || \
  echo "   (Please open the URL manually in your browser)"
