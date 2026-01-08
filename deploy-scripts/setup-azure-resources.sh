#!/bin/bash

# MediaCloud Azure Resources Setup Script
# This creates all the Azure resources needed for deployment

set -e  # Exit on any error

echo "🚀 Setting up Azure resources for MediaCloud..."

# Configuration
RESOURCE_GROUP="mediacloud-rg"
LOCATION="East US"
COSMOS_ACCOUNT="mediacloud-cosmos"
STORAGE_ACCOUNT="mediacloudstore$(date +%s)"  # Add timestamp to ensure uniqueness
REGISTRY_NAME="mediacloudregistry$(date +%s)"  # Add timestamp to ensure uniqueness
STATIC_APP_NAME="mediacloud-frontend"

# Check if logged in to Azure
echo "📋 Checking Azure login status..."
if ! az account show > /dev/null 2>&1; then
    echo "❌ Not logged in to Azure. Please run 'az login' first."
    exit 1
fi

echo "✅ Azure login confirmed"
echo "📊 Current subscription:"
az account show --query "{Name:name, SubscriptionId:id}" -o table

# Create resource group
echo "📁 Creating resource group..."
az group create \
  --name $RESOURCE_GROUP \
  --location "$LOCATION"

echo "✅ Resource group '$RESOURCE_GROUP' created"

# Create Cosmos DB (MongoDB)
echo "🗄️  Creating Cosmos DB with MongoDB API..."
az cosmosdb create \
  --name $COSMOS_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --kind MongoDB \
  --server-version 4.2 \
  --default-consistency-level Session \
  --enable-free-tier true \
  --locations regionName="$LOCATION" failoverPriority=0 isZoneRedundant=False

# Create database
echo "📊 Creating database..."
az cosmosdb mongodb database create \
  --account-name $COSMOS_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --name mediacloud

echo "✅ Cosmos DB created"

# Create storage account
echo "💾 Creating storage account..."
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location "$LOCATION" \
  --sku Standard_LRS \
  --kind StorageV2 \
  --access-tier Hot

echo "✅ Storage account created"

# Create container registry
echo "🐳 Creating container registry..."
az acr create \
  --name $REGISTRY_NAME \
  --resource-group $RESOURCE_GROUP \
  --sku Basic \
  --admin-enabled true

echo "✅ Container registry created"

# Create Static Web App
echo "🌐 Creating Static Web App..."
az staticwebapp create \
  --name $STATIC_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --location "East US 2" \
  --sku Free

echo "✅ Static Web App created"

# Get connection strings and credentials
echo "🔑 Retrieving connection strings and credentials..."

echo ""
echo "📋 SAVE THESE CREDENTIALS - YOU'LL NEED THEM FOR DEPLOYMENT:"
echo "================================================================"

echo ""
echo "🗄️  COSMOS DB (MongoDB) CONNECTION STRING:"
az cosmosdb keys list \
  --name $COSMOS_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --type connection-strings \
  --query "connectionStrings[0].connectionString" -o tsv

echo ""
echo "💾 STORAGE ACCOUNT CONNECTION STRING:"
az storage account show-connection-string \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --query connectionString -o tsv

echo ""
echo "🐳 CONTAINER REGISTRY CREDENTIALS:"
echo "Registry Name: $REGISTRY_NAME"
az acr credential show --name $REGISTRY_NAME --query "{Username:username, Password:passwords[0].value}" -o table

echo ""
echo "🌐 STATIC WEB APP DETAILS:"
az staticwebapp show \
  --name $STATIC_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "{Name:name, DefaultHostname:defaultHostname, ResourceGroup:resourceGroup}" -o table

echo ""
echo "📝 DEPLOYMENT TOKEN (for Static Web App):"
az staticwebapp secrets list \
  --name $STATIC_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "properties.apiKey" -o tsv

echo ""
echo "================================================================"
echo "✅ All Azure resources created successfully!"
echo ""
echo "📋 NEXT STEPS:"
echo "1. Save all the credentials above"
echo "2. Update your backend configuration with the connection strings"
echo "3. Run the deployment scripts to deploy your application"
echo ""
echo "🔧 RESOURCE NAMES CREATED:"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   Cosmos DB: $COSMOS_ACCOUNT"
echo "   Storage Account: $STORAGE_ACCOUNT"
echo "   Container Registry: $REGISTRY_NAME"
echo "   Static Web App: $STATIC_APP_NAME"
echo ""
echo "💰 COST MONITORING:"
echo "   All resources are using free tiers where available"
echo "   Monitor usage at: https://portal.azure.com/#blade/Microsoft_Azure_CostManagement/Menu/overview"