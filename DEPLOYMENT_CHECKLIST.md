# 🚀 MediaCloud Deployment Checklist

## ✅ Pre-Deployment Checklist

### Prerequisites
- [ ] Azure Student Account active
- [ ] Azure CLI installed and logged in (`az login`)
- [ ] Docker Desktop installed and running
- [ ] Node.js and npm installed
- [ ] Git repository ready (optional for Static Web Apps)

### Project Preparation
- [ ] Frontend builds successfully (`npm run build`)
- [ ] Backend runs locally without errors
- [ ] All environment variables identified
- [ ] Database connection tested locally

---

## 🎯 Deployment Steps (Follow in Order)

### Step 1: Set Up Azure Resources
```bash
# Make script executable (Mac/Linux)
chmod +x deploy-scripts/setup-azure-resources.sh

# Run the setup script
./deploy-scripts/setup-azure-resources.sh
```

**📋 Save These Credentials:**
- [ ] Cosmos DB connection string
- [ ] Storage account connection string  
- [ ] Container registry credentials
- [ ] Static Web App deployment token

### Step 2: Deploy Backend
```bash
# Make script executable (Mac/Linux)
chmod +x deploy-scripts/deploy-backend.sh

# Run the backend deployment
./deploy-scripts/deploy-backend.sh
```

**🔧 You'll be prompted for:**
- [ ] MongoDB connection string (from Step 1)
- [ ] JWT secret key (create a strong password)
- [ ] Azure Storage connection string (from Step 1)

**📝 Save the backend URL:** `https://mediacloud-api.eastus.azurecontainer.io:5001`

### Step 3: Deploy Frontend
```bash
# Make script executable (Mac/Linux)
chmod +x deploy-scripts/deploy-frontend.sh

# Run the frontend deployment
./deploy-scripts/deploy-frontend.sh
```

**🔧 You'll be prompted for:**
- [ ] Backend URL (from Step 2)

**📝 Save the frontend URL:** `https://your-app.azurestaticapps.net`

---

## 🧪 Post-Deployment Testing

### Test Basic Functionality
- [ ] Frontend loads without errors
- [ ] User registration works
- [ ] User login works
- [ ] File upload works
- [ ] Media display works
- [ ] Storage quota shows correctly
- [ ] Logout works

### Test API Endpoints
```bash
# Test health endpoint
curl https://your-backend-url:5001/health

# Test CORS (should return CORS headers)
curl -H "Origin: https://your-frontend-url" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: X-Requested-With" \
     -X OPTIONS \
     https://your-backend-url:5001/api/auth/login
```

---

## 🔧 Configuration Updates

### Update CORS Settings
If you get CORS errors, update `backend/config.py`:

```python
CORS_ORIGINS = [
    'http://localhost:4200',  # Keep for local development
    'https://your-actual-frontend-url.azurestaticapps.net'  # Add your real URL
]
```

Then redeploy backend:
```bash
./deploy-scripts/deploy-backend.sh
```

### Update Environment Variables
If you need to change environment variables:

```bash
# Update container with new environment variables
az container create \
  --name mediacloud-backend \
  --resource-group mediacloud-rg \
  --image mediacloudregistry.azurecr.io/mediacloud-backend:latest \
  --environment-variables \
    MONGO_URI="new-connection-string" \
    JWT_SECRET_KEY="new-secret" \
    AZURE_STORAGE_CONNECTION_STRING="new-storage-string"
```

---

## 📊 Monitoring & Maintenance

### Check Application Health
```bash
# Backend container status
az container show --name mediacloud-backend --resource-group mediacloud-rg

# Backend logs
az container logs --name mediacloud-backend --resource-group mediacloud-rg

# Frontend deployment status
az staticwebapp show --name mediacloud-frontend --resource-group mediacloud-rg
```

### Monitor Costs
```bash
# Check current usage
az consumption usage list --top 10

# View cost analysis in portal
# https://portal.azure.com/#blade/Microsoft_Azure_CostManagement/Menu/overview
```

### Free Tier Limits
- **Static Web Apps**: 100GB bandwidth/month
- **Container Instances**: Pay per second (estimate $10-20/month for basic usage)
- **Cosmos DB**: 1000 RU/s, 25GB storage (FREE)
- **Blob Storage**: 5GB, 20,000 transactions (FREE)

---

## 🚨 Troubleshooting

### Common Issues

**Frontend won't load:**
- [ ] Check Static Web App deployment status
- [ ] Verify build completed successfully
- [ ] Check browser console for errors

**Backend API errors:**
- [ ] Check container is running: `az container show --name mediacloud-backend --resource-group mediacloud-rg`
- [ ] Check container logs: `az container logs --name mediacloud-backend --resource-group mediacloud-rg`
- [ ] Verify environment variables are set correctly

**CORS errors:**
- [ ] Update CORS_ORIGINS in backend config
- [ ] Redeploy backend after CORS update
- [ ] Clear browser cache

**Database connection errors:**
- [ ] Verify Cosmos DB connection string
- [ ] Check Cosmos DB is running in Azure portal
- [ ] Ensure IP restrictions allow container access

**File upload errors:**
- [ ] Verify Azure Storage connection string
- [ ] Check storage account exists and is accessible
- [ ] Verify container has proper permissions

### Get Help
- **Azure Portal**: https://portal.azure.com
- **Azure Documentation**: https://docs.microsoft.com/azure
- **Azure Support**: Available with student subscription

---

## 🎉 Success!

When everything is working:
- ✅ Users can register and login
- ✅ Files upload to Azure Blob Storage
- ✅ Media displays correctly
- ✅ Storage quota tracking works
- ✅ All features function as expected

**Your MediaCloud app is now live on Azure! 🚀**

Share your app: `https://your-app.azurestaticapps.net`