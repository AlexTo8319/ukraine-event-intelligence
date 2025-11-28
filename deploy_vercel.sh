#!/bin/bash
# Vercel deployment script using API

set -e

echo "🚀 Vercel Deployment Script"
echo "============================"
echo ""

if [ -z "$VERCEL_TOKEN" ]; then
    echo "❌ VERCEL_TOKEN environment variable not set"
    echo ""
    echo "To use this script:"
    echo "  1. Go to: https://vercel.com/account/tokens"
    echo "  2. Create a new token"
    echo "  3. Run: export VERCEL_TOKEN=your_token_here"
    echo "  4. Run: ./deploy_vercel.sh"
    exit 1
fi

PROJECT_NAME="ukraine-event-intelligence"
REPO_URL="https://github.com/AlexTo8319/ukraine-event-intelligence"

echo "📦 Deploying to Vercel..."
echo ""

# Check if project exists
PROJECT_EXISTS=$(curl -s -H "Authorization: Bearer $VERCEL_TOKEN" "https://api.vercel.com/v9/projects/$PROJECT_NAME" | grep -o '"name"' || echo "")

if [ -z "$PROJECT_EXISTS" ]; then
    echo "Creating Vercel project..."
    curl -X POST \
        -H "Authorization: Bearer $VERCEL_TOKEN" \
        -H "Content-Type: application/json" \
        "https://api.vercel.com/v9/projects" \
        -d "{
            \"name\": \"$PROJECT_NAME\",
            \"gitRepository\": {
                \"type\": \"github\",
                \"repo\": \"AlexTo8319/ukraine-event-intelligence\"
            },
            \"rootDirectory\": \"frontend\"
        }" > /dev/null 2>&1
    echo "✅ Project created"
else
    echo "✅ Project exists"
fi

# Add environment variables
echo "Setting environment variables..."

curl -X POST \
    -H "Authorization: Bearer $VERCEL_TOKEN" \
    -H "Content-Type: application/json" \
    "https://api.vercel.com/v9/projects/$PROJECT_NAME/env" \
    -d "{
        \"key\": \"NEXT_PUBLIC_SUPABASE_URL\",
        \"value\": \"https://qjuaqnhwpwmywgshghpq.supabase.co\",
        \"type\": \"encrypted\",
        \"target\": [\"production\", \"preview\"]
    }" > /dev/null 2>&1

curl -X POST \
    -H "Authorization: Bearer $VERCEL_TOKEN" \
    -H "Content-Type: application/json" \
    "https://api.vercel.com/v9/projects/$PROJECT_NAME/env" \
    -d "{
        \"key\": \"NEXT_PUBLIC_SUPABASE_ANON_KEY\",
        \"value\": \"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFqdWFxbmh3cHdteXdnc2hnaHBxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQyNDI5MjcsImV4cCI6MjA3OTgxODkyN30.vXQkZf4ERzyaqdCDouRtBUHXJY-6XSJaZrlK4WyRrik\",
        \"type\": \"encrypted\",
        \"target\": [\"production\", \"preview\"]
    }" > /dev/null 2>&1

echo "✅ Environment variables set"

# Trigger deployment
echo "Triggering deployment..."
DEPLOYMENT=$(curl -X POST \
    -H "Authorization: Bearer $VERCEL_TOKEN" \
    -H "Content-Type: application/json" \
    "https://api.vercel.com/v13/deployments" \
    -d "{
        \"name\": \"$PROJECT_NAME\",
        \"gitSource\": {
            \"type\": \"github\",
            \"repo\": \"AlexTo8319/ukraine-event-intelligence\",
            \"ref\": \"main\"
        },
        \"projectSettings\": {
            \"rootDirectory\": \"frontend\"
        }
    }" 2>/dev/null)

echo ""
echo "✅ Deployment triggered!"
echo ""
echo "Check status at: https://vercel.com/dashboard"


