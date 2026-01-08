# 📤 How to Upload MediaCloud to GitHub (Step-by-Step)

## 🎯 What is GitHub?
GitHub is like Google Drive for code. It stores your project online so you can:
- Access it from anywhere
- Share it with others
- Deploy it to Azure automatically
- Keep track of changes

---

## 🛠️ Method 1: Using GitHub Desktop (Easiest for Beginners)

### Step 1: Download GitHub Desktop
1. Go to https://desktop.github.com/
2. Click "Download for Windows" (or Mac)
3. Install it like any other program
4. Open GitHub Desktop

### Step 2: Create GitHub Account
1. Go to https://github.com
2. Click "Sign up"
3. Choose a username (like: `yourname-dev`)
4. Use your email and create a password
5. Verify your email

### Step 3: Sign in to GitHub Desktop
1. Open GitHub Desktop
2. Click "Sign in to GitHub.com"
3. Enter your GitHub username and password
4. Click "Sign in"

### Step 4: Create New Repository
1. In GitHub Desktop, click "Create a New Repository on your hard drive"
2. Fill in:
   - **Name**: `mediacloud-mvp`
   - **Description**: `My MediaCloud project - Google Photos style media storage`
   - **Local path**: Choose where to save (like Desktop)
   - **Initialize with README**: ✅ Check this
   - **Git ignore**: Choose "Node" from dropdown
   - **License**: Choose "MIT License"
3. Click "Create repository"

### Step 5: Copy Your Project Files
1. Open the new folder that was created (should be empty except for README)
2. Copy ALL your MediaCloud files into this folder:
   ```
   From: X:\Kiro\Cloud Media\mediacloud-mvp\
   To: C:\Users\YourName\Desktop\mediacloud-mvp\
   ```
3. Copy everything: frontend folder, backend folder, all files

### Step 6: Commit and Push
1. Go back to GitHub Desktop
2. You'll see all your files listed on the left
3. In the bottom left:
   - **Summary**: Type "Initial commit - MediaCloud project"
   - **Description**: Type "Added complete MediaCloud application with Angular frontend and Flask backend"
4. Click "Commit to main"
5. Click "Publish repository" (top right)
6. Make sure "Keep this code private" is UNCHECKED (for Azure deployment)
7. Click "Publish repository"

🎉 **Done! Your project is now on GitHub!**

---

## 🛠️ Method 2: Using Command Line (For Advanced Users)

### Step 1: Install Git
**Windows:**
1. Download from https://git-scm.com/download/win
2. Install with default settings

**Mac:**
```bash
# Install using Homebrew
brew install git
```

### Step 2: Configure Git
```bash
# Set your name and email (use your GitHub account email)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Step 3: Create Repository on GitHub
1. Go to https://github.com
2. Click the "+" icon (top right)
3. Click "New repository"
4. Fill in:
   - **Repository name**: `mediacloud-mvp`
   - **Description**: `MediaCloud - Google Photos style media storage`
   - **Public** (not private - needed for Azure)
   - **Add README**: ✅ Check
   - **Add .gitignore**: Choose "Node"
   - **License**: MIT License
5. Click "Create repository"

### Step 4: Clone and Upload
```bash
# Navigate to where you want the project
cd Desktop

# Clone the empty repository
git clone https://github.com/YOUR-USERNAME/mediacloud-mvp.git

# Copy your project files into the cloned folder
# (Copy all files from your current mediacloud-mvp folder)

# Navigate into the project
cd mediacloud-mvp

# Add all files
git add .

# Commit the files
git commit -m "Initial commit - MediaCloud project"

# Push to GitHub
git push origin main
```

---

## 🛠️ Method 3: Using GitHub Web Interface (Upload Files)

### Step 1: Create Repository
1. Go to https://github.com
2. Click "New repository"
3. Name it `mediacloud-mvp`
4. Make it **Public**
5. Click "Create repository"

### Step 2: Upload Files
1. Click "uploading an existing file"
2. **Drag and drop** your entire `mediacloud-mvp` folder
3. Or click "choose your files" and select everything
4. Wait for upload (might take a few minutes)
5. Add commit message: "Initial MediaCloud project upload"
6. Click "Commit changes"

⚠️ **Note**: This method has file size limits and might not work for large projects.

---

## 📁 What Your GitHub Repository Should Look Like

After upload, your GitHub repo should have this structure:
```
mediacloud-mvp/
├── README.md
├── .gitignore
├── LICENSE
├── AZURE_DEPLOYMENT_GUIDE.md
├── DEPLOYMENT_CHECKLIST.md
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── models/
│   ├── routes/
│   └── services/
├── frontend/
│   ├── package.json
│   ├── angular.json
│   ├── src/
│   └── dist/ (if built)
└── deploy-scripts/
    ├── setup-azure-resources.sh
    ├── deploy-backend.sh
    └── deploy-frontend.sh
```

---

## 🔧 Create .gitignore File (Important!)

Create a file called `.gitignore` in your project root:

```gitignore
# Dependencies
node_modules/
__pycache__/
*.pyc
venv/
env/

# Build outputs
dist/
build/
*.egg-info/

# Environment files
.env
.env.local
.env.production

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Temporary files
temp/
tmp/

# Azure deployment files (optional)
.azure/

# Database files
*.db
*.sqlite

# Uploads (will be in Azure Blob Storage)
uploads/
```

---

## 🎉 Verify Your Upload

### Check Your Repository
1. Go to `https://github.com/YOUR-USERNAME/mediacloud-mvp`
2. You should see all your files
3. Click around to make sure everything uploaded

### Test Clone (Optional)
```bash
# Test that others can download your project
git clone https://github.com/YOUR-USERNAME/mediacloud-mvp.git test-download
cd test-download
# Check if all files are there
```

---

## 🚀 Connect to Azure Static Web Apps

Now that your code is on GitHub, you can use it for Azure deployment:

### Option 1: During Azure Static Web App Creation
```bash
az staticwebapp create \
  --name mediacloud-frontend \
  --resource-group mediacloud-rg \
  --source https://github.com/YOUR-USERNAME/mediacloud-mvp \
  --location "East US 2" \
  --branch main \
  --app-location "/frontend" \
  --output-location "dist/mediacloud-frontend"
```

### Option 2: Link Existing Static Web App
1. Go to Azure Portal
2. Find your Static Web App
3. Go to "Deployment" → "GitHub"
4. Connect your GitHub account
5. Select your repository: `mediacloud-mvp`
6. Set build details:
   - **Branch**: `main`
   - **App location**: `/frontend`
   - **Output location**: `dist/mediacloud-frontend`

---

## 🔄 Making Updates Later

When you want to update your project:

### Using GitHub Desktop:
1. Make changes to your local files
2. Open GitHub Desktop
3. Review changes
4. Add commit message
5. Click "Commit to main"
6. Click "Push origin"

### Using Command Line:
```bash
# After making changes
git add .
git commit -m "Updated feature X"
git push origin main
```

### Using Web Interface:
1. Go to your GitHub repository
2. Click on the file you want to edit
3. Click the pencil icon (Edit)
4. Make changes
5. Scroll down and commit changes

---

## 🆘 Troubleshooting

### "Repository already exists"
- Choose a different name like `mediacloud-mvp-v2`
- Or delete the existing empty repository first

### "File too large"
- Check if you have `node_modules` folder (should be in .gitignore)
- Remove large files like videos or databases
- Use Git LFS for large files

### "Permission denied"
- Make sure you're signed in to GitHub
- Check if repository is public (needed for free Azure deployment)

### "Nothing to commit"
- Make sure you copied files to the right folder
- Check that files aren't being ignored by .gitignore

---

## 🎯 Next Steps

After uploading to GitHub:
1. ✅ Your code is safely stored online
2. ✅ You can share the link with others
3. ✅ You can deploy to Azure using GitHub integration
4. ✅ Azure will automatically redeploy when you push changes

**Your GitHub repository URL**: `https://github.com/YOUR-USERNAME/mediacloud-mvp`

Now you can use this repository for Azure deployment with automatic updates! 🚀