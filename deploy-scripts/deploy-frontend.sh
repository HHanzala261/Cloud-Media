#!/bin/bash

# MediaCloud Frontend Deployment Script
# Run this from the project root directory

set -e  # Exit on any error

echo "🚀 Starting MediaCloud Frontend Deployment to Azure..."

# Configuration
RESOURCE_GROUP="mediacloud-rg"
STATIC_APP_NAME="mediacloud-frontend"

# Check if logged in to Azure
echo "📋 Checking Azure login status..."
if ! az account show > /dev/null 2>&1; then
    echo "❌ Not logged in to Azure. Please run 'az login' first."
    exit 1
fi

echo "✅ Azure login confirmed"

# Prompt for backend URL
echo "🔧 Please provide your backend URL:"
read -p "Backend URL (e.g., https://mediacloud-api.eastus.azurecontainer.io:5001): " BACKEND_URL

# Navigate to frontend directory
cd frontend

# Update API base URL in services
echo "🔧 Updating API configuration..."

# Backup original files
cp src/app/core/auth.service.ts src/app/core/auth.service.ts.backup
cp src/app/core/media.service.ts src/app/core/media.service.ts.backup

# Update auth service
sed -i.tmp "s|private readonly API_BASE = 'http://localhost:5001/api';|private readonly API_BASE = '${BACKEND_URL}/api';|g" src/app/core/auth.service.ts
rm -f src/app/core/auth.service.ts.tmp

# Update media service  
sed -i.tmp "s|private readonly API_BASE = 'http://localhost:5001/api';|private readonly API_BASE = '${BACKEND_URL}/api';|g" src/app/core/media.service.ts
rm -f src/app/core/media.service.ts.tmp

echo "✅ API configuration updated"

# Install dependencies (if not already installed)
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Build for production
echo "🏗️  Building Angular app for production..."
npm run build

echo "✅ Build completed"

# Get deployment token
echo "🔑 Getting deployment token..."
DEPLOYMENT_TOKEN=$(az staticwebapp secrets list \
  --name $STATIC_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "properties.apiKey" -o tsv)

# Install Static Web Apps CLI if not installed
if ! command -v swa &> /dev/null; then
    echo "📦 Installing Static Web Apps CLI..."
    npm install -g @azure/static-web-apps-cli
fi

# Deploy to Static Web App
echo "🚀 Deploying to Azure Static Web Apps..."
cd dist/mediacloud-frontend

swa deploy \
  --app-location . \
  --deployment-token "$DEPLOYMENT_TOKEN" \
  --verbose

# Get the frontend URL
echo "🌐 Getting frontend URL..."
FRONTEND_URL=$(az staticwebapp show \
  --name $STATIC_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query defaultHostname -o tsv)

# Restore original files
cd ../../
mv src/app/core/auth.service.ts.backup src/app/core/auth.service.ts
mv src/app/core/media.service.ts.backup src/app/core/media.service.ts

echo "✅ Frontend deployment complete!"
echo "🔗 Frontend URL: https://$FRONTEND_URL"

# Test the deployment
echo "🧪 Testing deployment..."
sleep 10  # Wait for deployment to propagate
if curl -f "https://$FRONTEND_URL" > /dev/null 2>&1; then
    echo "✅ Frontend is accessible!"
else
    echo "⚠️  Frontend might still be deploying. Check in a few minutes."
fi

echo ""
echo "🎉 Deployment completed!"
echo "📱 Your MediaCloud app is now live at: https://$FRONTEND_URL"
echo ""
echo "🔧 Next steps:"
echo "1. Test user registration and login"
echo "2. Test file upload functionality"
echo "3. Verify all features work correctly"
echo ""
echo "📊 Monitor your app:"
echo "   Frontend: https://portal.azure.com/#resource/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/staticSites/$STATIC_APP_NAME"
echo "   Backend: https://portal.azure.com/#resource/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ContainerInstance/containerGroups/mediacloud-backend"