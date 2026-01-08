@echo off
echo 🚀 MediaCloud GitHub Upload Script
echo ===================================
echo.

REM Check if git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Git is not installed or not in PATH
    echo Please install Git from: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo ✅ Git is installed

REM Get user input
set /p GITHUB_USERNAME="Enter your GitHub username: "
set /p REPO_NAME="Enter repository name (default: mediacloud-mvp): "
if "%REPO_NAME%"=="" set REPO_NAME=mediacloud-mvp

echo.
echo 📋 Configuration:
echo Username: %GITHUB_USERNAME%
echo Repository: %REPO_NAME%
echo.

REM Configure git user (if not already configured)
echo 🔧 Configuring Git...
git config --global user.name "%GITHUB_USERNAME%"
set /p USER_EMAIL="Enter your email: "
git config --global user.email "%USER_EMAIL%"

REM Initialize git repository
echo 📁 Initializing Git repository...
git init

REM Add all files
echo 📤 Adding files to Git...
git add .

REM Create initial commit
echo 💾 Creating initial commit...
git commit -m "Initial commit - MediaCloud project with Angular frontend and Flask backend"

REM Add remote origin
echo 🔗 Adding GitHub remote...
git remote add origin https://github.com/%GITHUB_USERNAME%/%REPO_NAME%.git

REM Set main branch
git branch -M main

echo.
echo 🎯 Ready to push to GitHub!
echo.
echo ⚠️  IMPORTANT: Make sure you have created the repository on GitHub first!
echo    1. Go to https://github.com/new
echo    2. Create a repository named: %REPO_NAME%
echo    3. Make it PUBLIC (required for free Azure deployment)
echo    4. Do NOT initialize with README (we already have one)
echo.
set /p CONTINUE="Have you created the repository on GitHub? (y/n): "

if /i "%CONTINUE%"=="y" (
    echo 🚀 Pushing to GitHub...
    git push -u origin main
    
    if %errorlevel% equ 0 (
        echo.
        echo ✅ SUCCESS! Your project is now on GitHub!
        echo 🔗 Repository URL: https://github.com/%GITHUB_USERNAME%/%REPO_NAME%
        echo.
        echo 🎉 Next steps:
        echo    1. Visit your repository: https://github.com/%GITHUB_USERNAME%/%REPO_NAME%
        echo    2. Verify all files are uploaded
        echo    3. Use this repository for Azure deployment
        echo.
    ) else (
        echo.
        echo ❌ Push failed. Common issues:
        echo    - Repository doesn't exist on GitHub
        echo    - Wrong username/repository name
        echo    - Authentication required (you may need to use GitHub Desktop or personal access token)
        echo.
        echo 💡 Alternative: Use GitHub Desktop for easier authentication
        echo    Download from: https://desktop.github.com/
    )
) else (
    echo.
    echo 📝 Please create the repository on GitHub first, then run this script again.
    echo    Go to: https://github.com/new
)

echo.
pause