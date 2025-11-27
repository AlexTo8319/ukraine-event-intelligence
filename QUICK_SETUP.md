# 🚀 Quick Setup Guide

## ✅ Already Done
- ✅ All dependencies installed
- ✅ .env file created with your API keys
- ✅ Supabase connection verified

## 📊 Database Setup (Required)

You need to set up the database table. Choose one method:

### Method 1: Supabase Dashboard (Recommended - 2 minutes)

1. **Open SQL Editor:**
   - Go to: https://supabase.com/dashboard/project/qjuaqnhwpwmywgshghpq/sql
   - Or: Dashboard → Your Project → SQL Editor

2. **Run the SQL:**
   - Click "New Query"
   - Copy ALL the content from `setup_complete.sql` file
   - Paste into the SQL Editor
   - Click "Run" (or press Cmd/Ctrl + Enter)

3. **Verify:**
   - Go to: Table Editor
   - You should see an "events" table

### Method 2: Get Service Role Key (For Automated Setup)

If you want me to set it up automatically:

1. **Get Service Role Key:**
   - Go to: https://supabase.com/dashboard/project/qjuaqnhwpwmywgshghpq/settings/api
   - Find "service_role" key (under "Project API keys")
   - Copy it (it's a JWT token starting with "eyJ...")

2. **Update .env:**
   ```bash
   # Edit .env file and replace:
   SUPABASE_KEY=your_service_role_key_here
   ```

3. **Run setup:**
   ```bash
   python3 backend/setup_database.py
   ```

## 🧪 Test the Setup

Once database is set up:

```bash
# 1. Verify everything
cd backend
python3 verify_setup.py

# 2. Test research agent (will search and populate database)
python3 -m agent.research_agent

# 3. Start frontend dashboard
cd ../frontend
npm run dev
# Open http://localhost:3000
```

## 📝 Current Status

- ✅ Environment variables configured
- ✅ API keys set
- ✅ Dependencies installed
- ⚠️  Database setup needed (run SQL above)

## 🆘 Need Help?

If you encounter issues:
1. Check that Supabase project is active
2. Verify API keys are correct
3. Make sure SQL ran without errors
4. Check browser console for frontend errors

