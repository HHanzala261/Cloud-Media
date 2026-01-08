#!/bin/bash

# MediaCloud Backend Deployment Script
# Run this from the project root directory

set -e  # Exit on any error

echo "🚀 Starting MediaCloud Backend Deployment to Azure..."

# Configuration
RESOURCE_GROUP="mediacloud-rg"
REGISTRY_NAME="mediacloudregistry"
CONTAINER_NAME="mediacloud-backend"
IMAGE_NAME="mediacloud-backend"
LOCATION="East US"

# Check if logged in to Azure
echo "📋 Checking Azure login status..."
if ! az account show > /dev/null 2>&1; then
    echo "❌ Not logged in to Azure. Please run 'az login' first."
    exit 1
fi

echo "✅ Azure login confirmed"

# Navigate to backend directory
cd backend

# Build Docker image
echo "🐳 Building Docker image..."
docker build -t $REGISTRY_NAME.azurecr.io/$IMAGE_NAME:latest .

# Login to Azure Container Registry
echo "🔐 Logging in to Azure Container Registry..."
az acr login --name $REGISTRY_NAME

# Push image to registry
echo "📤 Pushing image to Azure Container Registry..."
docker push $REGISTRY_NAME.azurecr.io/$IMAGE_NAME:latest

# Get registry credentials
echo "🔑 Getting registry credentials..."
REGISTRY_PASSWORD=$(az acr credential show --name $REGISTRY_NAME --query "passwords[0].value" -o tsv)

# Prompt for environment variables
echo "🔧 Please provide the following environment variables:"
read -p "MongoDB Connection String: " MONGO_URI
read -p "JWT Secret Key: " JWT_SECRET
read -p "Azure Storage Connection String: " STORAGE_CONNECTION

# Create or update container instance
echo "🚀 Deploying container instance..."
az container create \
  --name $CONTAINER_NAME \
  --resource-group $RESOURCE_GROUP \
  --image $REGISTRY_NAME.azurecr.io/$IMAGE_NAME:latest \
  --registry-login-server $REGISTRY_NAME.azurecr.io \
  --registry-username $REGISTRY_NAME \
  --registry-password "$REGISTRY_PASSWORD" \
  --dns-name-label mediacloud-api \
  --ports 5001 \
  --environment-variables \
    MONGO_URI="$MONGO_URI" \
    JWT_SECRET_KEY="$JWT_SECRET" \
    AZURE_STORAGE_CONNECTION_STRING="$STORAGE_CONNECTION" \
  --cpu 1 \
  --memory 1.5 \
  --restart-policy Always

# Get the backend URL
echo "🌐 Getting backend URL..."
BACKEND_URL=$(az container show --name $CONTAINER_NAME --resource-group $RESOURCE_GROUP --query ipAddress.fqdn -o tsv)

echo "✅ Backend deployment complete!"
echo "🔗 Backend URL: https://$BACKEND_URL:5001"
echo "🔗 Health Check: https://$BACKEND_URL:5001/health"

# Test health endpoint
echo "🏥 Testing health endpoint..."
sleep 30  # Wait for container to start
if curl -f "https://$BACKEND_URL:5001/health" > /dev/null 2>&1; then
    echo "✅ Health check passed!"
else
    echo "⚠️  Health check failed. Check container logs:"
    echo "   az container logs --name $CONTAINER_NAME --resource-group $RESOURCE_GROUP"
fi

echo "🎉 Deployment script completed!"