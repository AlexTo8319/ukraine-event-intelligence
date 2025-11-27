# 🚀 Quick Deployment Guide

## Easiest Method: GitHub + Vercel (5 minutes)

### Step 1: Push to GitHub

```bash
cd "/Users/alextommy/Documents/UN-Habitat/Cursor AI event search"
git init
git add .
git commit -m "Event Intelligence Platform - Ukraine Focus"
```

Then create a new repository on GitHub and:
```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy to Vercel

1. **Go to:** https://vercel.com/new
2. **Click:** "Import Git Repository"
3. **Select:** Your GitHub repository
4. **Configure:**
   - **Root Directory:** `frontend` (IMPORTANT!)
   - **Framework Preset:** Next.js (auto-detected)
   - **Build Command:** `npm run build` (auto)
   - **Output Directory:** `.next` (auto)

5. **Add Environment Variables:**
   Click "Environment Variables" and add:
   
   - **Name:** `NEXT_PUBLIC_SUPABASE_URL`
   - **Value:** `https://qjuaqnhwpwmywgshghpq.supabase.co`
   
   - **Name:** `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - **Value:** `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFqdWFxbmh3cHdteXdnc2hnaHBxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQyNDI5MjcsImV4cCI6MjA3OTgxODkyN30.vXQkZf4ERzyaqdCDouRtBUHXJY-6XSJaZrlK4WyRrik`

6. **Click:** "Deploy"

### Step 3: Done! 🎉

Your site will be live at: `https://your-project.vercel.app`

It will automatically:
- ✅ Show all 22 events
- ✅ Update on every git push
- ✅ Have HTTPS
- ✅ Be accessible worldwide

---

## Alternative: Vercel CLI

If you prefer command line:

```bash
cd frontend
vercel login
vercel
# Follow prompts, add env vars when asked
```

---

## What Gets Deployed

- ✅ Frontend dashboard (Next.js)
- ✅ All 22 events from Supabase
- ✅ Category filters
- ✅ Statistics
- ✅ Responsive design

**Note:** Backend (research agent) stays local or can be deployed separately to GitHub Actions (already configured).

