#!/bin/bash
# Automated deployment script - requires GitHub token

set -e

echo "🚀 Automated Deployment Script"
echo "================================"
echo ""

# Check for GitHub token
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ GITHUB_TOKEN environment variable not set"
    echo ""
    echo "To use this script:"
    echo "  export GITHUB_TOKEN=your_token_here"
    echo "  ./auto_deploy.sh"
    exit 1
fi

REPO_NAME="ukraine-event-intelligence"
GITHUB_USER=$(curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user | grep -o '"login":"[^"]*' | cut -d'"' -f4)

if [ -z "$GITHUB_USER" ]; then
    echo "❌ Invalid GitHub token"
    exit 1
fi

echo "✅ Authenticated as: $GITHUB_USER"
echo ""

# Check if repo exists
REPO_URL="https://github.com/$GITHUB_USER/$REPO_NAME"
REPO_EXISTS=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: token $GITHUB_TOKEN" "https://api.github.com/repos/$GITHUB_USER/$REPO_NAME")

if [ "$REPO_EXISTS" = "404" ]; then
    echo "📦 Creating GitHub repository..."
    curl -X POST \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        https://api.github.com/user/repos \
        -d "{\"name\":\"$REPO_NAME\",\"description\":\"Automated Urban Planning Event Intelligence Platform for Ukraine\",\"public\":true}" > /dev/null
    echo "✅ Repository created: $REPO_URL"
else
    echo "✅ Repository already exists: $REPO_URL"
fi

# Set remote
if git remote | grep -q origin; then
    git remote set-url origin "https://$GITHUB_TOKEN@github.com/$GITHUB_USER/$REPO_NAME.git"
else
    git remote add origin "https://$GITHUB_TOKEN@github.com/$GITHUB_USER/$REPO_NAME.git"
fi

# Push code
echo ""
echo "⬆️  Pushing code to GitHub..."
git push -u origin main

echo ""
echo "✅ Code pushed successfully!"
echo ""
echo "📍 Repository: $REPO_URL"
echo ""
echo "📋 Next: Deploy to Vercel"
echo "   1. Go to: https://vercel.com/new"
echo "   2. Import: $REPO_URL"
echo "   3. Root Directory: frontend"
echo "   4. Add environment variables"
echo "   5. Deploy!"





