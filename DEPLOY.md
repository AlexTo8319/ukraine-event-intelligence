# Deployment Guide

## Quick Deploy to Vercel (Recommended)

### Option 1: Deploy via Vercel CLI (Fastest)

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel:**
   ```bash
   vercel login
   ```

3. **Deploy from frontend directory:**
   ```bash
   cd frontend
   vercel
   ```

4. **Set Environment Variables:**
   After deployment, go to Vercel Dashboard → Your Project → Settings → Environment Variables
   
   Add these:
   - `NEXT_PUBLIC_SUPABASE_URL` = `https://qjuaqnhwpwmywgshghpq.supabase.co`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY` = `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFqdWFxbmh3cHdteXdnc2hnaHBxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQyNDI5MjcsImV4cCI6MjA3OTgxODkyN30.vXQkZf4ERzyaqdCDouRtBUHXJY-6XSJaZrlK4WyRrik`

5. **Redeploy:**
   ```bash
   vercel --prod
   ```

### Option 2: Deploy via GitHub (Automatic)

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin YOUR_GITHUB_REPO_URL
   git push -u origin main
   ```

2. **Connect to Vercel:**
   - Go to https://vercel.com
   - Click "New Project"
   - Import your GitHub repository
   - Set Root Directory to: `frontend`
   - Add environment variables (same as above)
   - Click "Deploy"

3. **Automatic Deployments:**
   - Every push to main branch = production deployment
   - Every push to other branches = preview deployment

### Option 3: Deploy to Netlify

1. **Install Netlify CLI:**
   ```bash
   npm install -g netlify-cli
   ```

2. **Build and Deploy:**
   ```bash
   cd frontend
   npm run build
   netlify deploy --prod --dir=.next
   ```

3. **Set Environment Variables:**
   - Go to Netlify Dashboard → Site Settings → Environment Variables
   - Add the same variables as Vercel

## Environment Variables Needed

For all platforms, set these environment variables:

- `NEXT_PUBLIC_SUPABASE_URL` = `https://qjuaqnhwpwmywgshghpq.supabase.co`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` = `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFqdWFxbmh3cHdteXdnc2hnaHBxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQyNDI5MjcsImV4cCI6MjA3OTgxODkyN30.vXQkZf4ERzyaqdCDouRtBUHXJY-6XSJaZrlK4WyRrik`

## Post-Deployment

After deployment, your site will be live at:
- Vercel: `https://your-project.vercel.app`
- Netlify: `https://your-project.netlify.app`

The dashboard will automatically show all 22 events from your Supabase database!

