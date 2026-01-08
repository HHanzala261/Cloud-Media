#!/bin/bash

echo "🚀 MediaCloud GitHub Upload Script"
echo "==================================="
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed"
    echo "Please install Git first:"
    echo "  Mac: brew install git"
    echo "  Linux: sudo apt-get install git"
    exit 1
fi

echo "✅ Git is installed"

# Get user input
read -p "Enter your GitHub username: " GITHUB_USERNAME
read -p "Enter repository name (default: mediacloud-mvp): " REPO_NAME
REPO_NAME=${REPO_NAME:-mediacloud-mvp}

echo ""
echo "📋 Configuration:"
echo "Username: $GITHUB_USERNAME"
echo "Repository: $REPO_NAME"
echo ""

# Configure git user (if not already configured)
echo "🔧 Configuring Git..."
git config --global user.name "$GITHUB_USERNAME"
read -p "Enter your email: " USER_EMAIL
git config --global user.email "$USER_EMAIL"

# Initialize git repository
echo "📁 Initializing Git repository..."
git init

# Add all files
echo "📤 Adding files to Git..."
git add .

# Create initial commit
echo "💾 Creating initial commit..."
git commit -m "Initial commit - MediaCloud project with Angular frontend and Flask backend"

# Add remote origin
echo "🔗 Adding GitHub remote..."
git remote add origin https://github.com/$GITHUB_USERNAME/$REPO_NAME.git

# Set main branch
git branch -M main

echo ""
echo "🎯 Ready to push to GitHub!"
echo ""
echo "⚠️  IMPORTANT: Make sure you have created the repository on GitHub first!"
echo "   1. Go to https://github.com/new"
echo "   2. Create a repository named: $REPO_NAME"
echo "   3. Make it PUBLIC (required for free Azure deployment)"
echo "   4. Do NOT initialize with README (we already have one)"
echo ""
read -p "Have you created the repository on GitHub? (y/n): " CONTINUE

if [[ $CONTINUE == "y" || $CONTINUE == "Y" ]]; then
    echo "🚀 Pushing to GitHub..."
    git push -u origin main
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ SUCCESS! Your project is now on GitHub!"
        echo "🔗 Repository URL: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
        echo ""
        echo "🎉 Next steps:"
        echo "   1. Visit your repository: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
        echo "   2. Verify all files are uploaded"
        echo "   3. Use this repository for Azure deployment"
        echo ""
    else
        echo ""
        echo "❌ Push failed. Common issues:"
        echo "   - Repository doesn't exist on GitHub"
        echo "   - Wrong username/repository name"
        echo "   - Authentication required (you may need to use GitHub Desktop or personal access token)"
        echo ""
        echo "💡 Alternative: Use GitHub Desktop for easier authentication"
        echo "   Download from: https://desktop.github.com/"
    fi
else
    echo ""
    echo "📝 Please create the repository on GitHub first, then run this script again."
    echo "   Go to: https://github.com/new"
fi

echo ""
read -p "Press Enter to continue..."