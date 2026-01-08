# 🚀 MediaCloud Azure Deployment Guide
*Step-by-step deployment for Azure Student Account*

## 📋 What We'll Deploy

Your MediaCloud project has:
- **Frontend**: Angular app (Static Web App)
- **Backend**: Python Flask API (Container Instance)
- **Database**: MongoDB (Cosmos DB)
- **Storage**: File uploads (Blob Storage)

## 🎯 Azure Services We'll Use (All Free Tier)

1. **Azure Static Web Apps** - Frontend hosting (FREE)
2. **Azure Container Instances** - Backend API (FREE tier available)
3. **Azure Cosmos DB** - MongoDB database (FREE tier: 1000 RU/s)
4. **Azure Blob Storage** - File storage (FREE tier: 5GB)

---

## 🛠️ STEP 1: Prepare Your Project

### 1.1 Create Production Build Files

First, let's prepare your project for deployment:

```bash
# Navigate to your project
cd mediacloud-mvp

# Build the Angular frontend for production
cd frontend
npm run build
cd ..

# Create deployment files for backend
cd backend
```

### 1.2 Create Backend Dockerfile

Create `backend/Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 5001

# Run the application
CMD ["python", "app.py"]
```

### 1.3 Update Backend for Production

Create `backend/.env.production`:
```env
# These will be set in Azure
MONGO_URI=
JWT_SECRET_KEY=
AZURE_STORAGE_CONNECTION_STRING=
```

---

## 🌐 STEP 2: Set Up Azure Account & CLI

### 2.1 Install Azure CLI

**Windows:**
```bash
# Download and install from: https://aka.ms/installazurecliwindows
# Or use winget:
winget install -e --id Microsoft.AzureCLI
```

**Mac:**
```bash
brew install azure-cli
```

**Linux:**
```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

### 2.2 Login to Azure

```bash
# Login to your Azure account
az login

# Verify your subscription
az account show

# Set your subscription (if you have multiple)
az account set --subscription "Azure for Students"
```

---

## 📦 STEP 3: Create Azure Resources

### 3.1 Create Resource Group

```bash
# Create a resource group (like a folder for all your resources)
az group create \
  --name mediacloud-rg \
  --location "East US"
```

### 3.2 Create Cosmos DB (MongoDB)

```bash
# Create Cosmos DB account with MongoDB API
az cosmosdb create \
  --name mediacloud-cosmos \
  --resource-group mediacloud-rg \
  --kind MongoDB \
  --server-version 4.2 \
  --default-consistency-level Session \
  --enable-free-tier true

# Create database
az cosmosdb mongodb database create \
  --account-name mediacloud-cosmos \
  --resource-group mediacloud-rg \
  --name mediacloud

# Get connection string (save this!)
az cosmosdb keys list \
  --name mediacloud-cosmos \
  --resource-group mediacloud-rg \
  --type connection-strings
```

### 3.3 Create Storage Account

```bash
# Create storage account for file uploads
az storage account create \
  --name mediacloudstore \
  --resource-group mediacloud-rg \
  --location "East US" \
  --sku Standard_LRS \
  --kind StorageV2

# Get connection string (save this!)
az storage account show-connection-string \
  --name mediacloudstore \
  --resource-group mediacloud-rg
```

### 3.4 Create Container Registry

```bash
# Create container registry for your backend
az acr create \
  --name mediacloudregistry \
  --resource-group mediacloud-rg \
  --sku Basic \
  --admin-enabled true

# Get login credentials
az acr credential show --name mediacloudregistry
```

---

## 🐳 STEP 4: Deploy Backend (Container)

### 4.1 Build and Push Docker Image

```bash
# Navigate to backend directory
cd backend

# Login to container registry
az acr login --name mediacloudregistry

# Build and push image
docker build -t mediacloudregistry.azurecr.io/mediacloud-backend:latest .
docker push mediacloudregistry.azurecr.io/mediacloud-backend:latest
```

### 4.2 Create Container Instance

```bash
# Get your connection strings from previous steps
MONGO_URI="your-cosmos-connection-string"
STORAGE_CONNECTION="your-storage-connection-string"
JWT_SECRET="your-super-secret-key-here"

# Create container instance
az container create \
  --name mediacloud-backend \
  --resource-group mediacloud-rg \
  --image mediacloudregistry.azurecr.io/mediacloud-backend:latest \
  --registry-login-server mediacloudregistry.azurecr.io \
  --registry-username mediacloudregistry \
  --registry-password "your-registry-password" \
  --dns-name-label mediacloud-api \
  --ports 5001 \
  --environment-variables \
    MONGO_URI="$MONGO_URI" \
    JWT_SECRET_KEY="$JWT_SECRET" \
    AZURE_STORAGE_CONNECTION_STRING="$STORAGE_CONNECTION" \
  --cpu 1 \
  --memory 1.5

# Get the backend URL (save this!)
az container show \
  --name mediacloud-backend \
  --resource-group mediacloud-rg \
  --query ipAddress.fqdn
```

---

## 🌍 STEP 5: Deploy Frontend (Static Web App)

### 5.1 Update Frontend Configuration

Update `frontend/src/app/core/auth.service.ts` and `media.service.ts`:

```typescript
// Replace localhost with your Azure backend URL
private readonly API_BASE = 'https://mediacloud-api.eastus.azurecontainer.io:5001/api';
```

### 5.2 Rebuild Frontend

```bash
cd frontend
npm run build
```

### 5.3 Create Static Web App

```bash
# Create static web app
az staticwebapp create \
  --name mediacloud-frontend \
  --resource-group mediacloud-rg \
  --source https://github.com/yourusername/mediacloud-mvp \
  --location "East US 2" \
  --branch main \
  --app-location "/frontend" \
  --output-location "dist/mediacloud-frontend"
```

**Alternative: Manual Upload**

If you don't have GitHub integration:

```bash
# Install Static Web Apps CLI
npm install -g @azure/static-web-apps-cli

# Deploy manually
cd frontend/dist/mediacloud-frontend
swa deploy --app-location . --deployment-token "your-deployment-token"
```

---

## ⚙️ STEP 6: Configure CORS and Environment

### 6.1 Update Backend CORS

In your `backend/config.py`, update CORS origins:

```python
# Add your Static Web App URL
CORS_ORIGINS = [
    'http://localhost:4200',  # Keep for local development
    'https://your-static-web-app-url.azurestaticapps.net'
]
```

### 6.2 Redeploy Backend

```bash
cd backend
docker build -t mediacloudregistry.azurecr.io/mediacloud-backend:latest .
docker push mediacloudregistry.azurecr.io/mediacloud-backend:latest

# Restart container
az container restart \
  --name mediacloud-backend \
  --resource-group mediacloud-rg
```

---

## 🔧 STEP 7: Final Configuration

### 7.1 Set Up Custom Domain (Optional)

```bash
# Add custom domain to Static Web App
az staticwebapp hostname set \
  --name mediacloud-frontend \
  --resource-group mediacloud-rg \
  --hostname yourdomain.com
```

### 7.2 Enable HTTPS

Azure automatically provides HTTPS for both services.

### 7.3 Monitor Your Application

```bash
# Check backend logs
az container logs \
  --name mediacloud-backend \
  --resource-group mediacloud-rg

# Check Static Web App status
az staticwebapp show \
  --name mediacloud-frontend \
  --resource-group mediacloud-rg
```

---

## 🎉 STEP 8: Test Your Deployment

### 8.1 Access Your App

1. **Frontend**: `https://your-app-name.azurestaticapps.net`
2. **Backend API**: `https://mediacloud-api.eastus.azurecontainer.io:5001`

### 8.2 Test Key Features

- [ ] User registration/login
- [ ] File upload to Azure Blob Storage
- [ ] Media display and management
- [ ] Storage quota tracking

---

## 💰 Cost Monitoring

### Free Tier Limits:
- **Static Web Apps**: 100GB bandwidth/month
- **Container Instances**: 1 vCPU, 1.5GB RAM (pay-per-second)
- **Cosmos DB**: 1000 RU/s, 25GB storage
- **Blob Storage**: 5GB, 20,000 transactions

### Monitor Usage:
```bash
# Check current costs
az consumption usage list --top 10

# Set up budget alerts
az consumption budget create \
  --budget-name mediacloud-budget \
  --amount 10 \
  --resource-group mediacloud-rg
```

---

## 🚨 Troubleshooting

### Common Issues:

1. **CORS Errors**: Update backend CORS configuration
2. **Container Won't Start**: Check environment variables
3. **Database Connection**: Verify Cosmos DB connection string
4. **File Upload Fails**: Check Blob Storage connection

### Debug Commands:
```bash
# Check container status
az container show --name mediacloud-backend --resource-group mediacloud-rg

# View container logs
az container logs --name mediacloud-backend --resource-group mediacloud-rg

# Test backend health
curl https://mediacloud-api.eastus.azurecontainer.io:5001/health
```

---

## 🔄 Future Updates

### Update Backend:
```bash
cd backend
docker build -t mediacloudregistry.azurecr.io/mediacloud-backend:latest .
docker push mediacloudregistry.azurecr.io/mediacloud-backend:latest
az container restart --name mediacloud-backend --resource-group mediacloud-rg
```

### Update Frontend:
```bash
cd frontend
npm run build
# Push to GitHub (if using GitHub integration)
# Or use SWA CLI for manual deployment
```

---

## 📞 Need Help?

- **Azure Documentation**: https://docs.microsoft.com/azure
- **Azure Student Support**: https://azure.microsoft.com/support/student/
- **Stack Overflow**: Tag questions with `azure` and `mediacloud`

**Your MediaCloud app is now live on Azure! 🎉**