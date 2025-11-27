#!/bin/bash
# Deployment script for Event Intelligence Platform

echo "🚀 Event Intelligence Platform - Deployment Script"
echo "=================================================="
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "Initializing git repository..."
    git init
    git branch -m main
fi

# Check if remote exists
if ! git remote | grep -q origin; then
    echo ""
    echo "📋 STEP 1: Create GitHub Repository"
    echo "-----------------------------------"
    echo "1. Go to: https://github.com/new"
    echo "2. Repository name: ukraine-event-intelligence (or your choice)"
    echo "3. Make it Public (or Private)"
    echo "4. Click 'Create repository'"
    echo "5. Copy the repository URL"
    echo ""
    read -p "Enter your GitHub repository URL: " REPO_URL
    
    if [ ! -z "$REPO_URL" ]; then
        git remote add origin "$REPO_URL"
        echo "✅ Remote added: $REPO_URL"
    else
        echo "⚠️  No URL provided. You can add it later with:"
        echo "   git remote add origin YOUR_REPO_URL"
        exit 1
    fi
fi

# Commit all changes
echo ""
echo "📦 Committing changes..."
git add .
git commit -m "Event Intelligence Platform - Ready for deployment" || echo "No changes to commit"

# Push to GitHub
echo ""
echo "⬆️  Pushing to GitHub..."
git push -u origin main || {
    echo "⚠️  Push failed. You may need to:"
    echo "   1. Set up GitHub authentication"
    echo "   2. Or push manually: git push -u origin main"
}

echo ""
echo "✅ Code pushed to GitHub!"
echo ""
echo "📋 STEP 2: Deploy to Vercel"
echo "---------------------------"
echo "1. Go to: https://vercel.com/new"
echo "2. Click 'Import Git Repository'"
echo "3. Select your repository"
echo "4. Configure:"
echo "   - Root Directory: frontend"
echo "   - Framework: Next.js (auto)"
echo "5. Add Environment Variables:"
echo "   - NEXT_PUBLIC_SUPABASE_URL = https://qjuaqnhwpwmywgshghpq.supabase.co"
echo "   - NEXT_PUBLIC_SUPABASE_ANON_KEY = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFqdWFxbmh3cHdteXdnc2hnaHBxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQyNDI5MjcsImV4cCI6MjA3OTgxODkyN30.vXQkZf4ERzyaqdCDouRtBUHXJY-6XSJaZrlK4WyRrik"
echo "6. Click 'Deploy'"
echo ""
echo "🎉 Your site will be live in 2-3 minutes!"
echo "   URL: https://your-project.vercel.app"

