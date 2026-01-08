# 📸 MediaCloud - Google Photos Style Media Storage

A modern, full-stack media storage application built with Angular and Flask, featuring Google Photos-inspired design and Azure cloud integration.

## ✨ Features

- **🎨 Google Photos UI**: Clean, modern dark theme interface
- **📱 Responsive Design**: Works on desktop, tablet, and mobile
- **🔐 User Authentication**: Secure JWT-based login system
- **📤 File Upload**: Support for photos, videos, and audio files
- **☁️ Cloud Storage**: Azure Blob Storage integration
- **📊 Storage Tracking**: Real-time quota monitoring with visual indicators
- **🗂️ Media Management**: Organize by type, favorites, and trash
- **🎵 Audio Player**: Built-in audio playback with controls
- **🔍 Search**: Find media by filename
- **♻️ Trash System**: Soft delete with recovery options

## 🏗️ Architecture

### Frontend (Angular 15+)
- **Framework**: Angular with TypeScript
- **Styling**: Bootstrap 5 + Custom CSS with design tokens
- **State Management**: RxJS Observables
- **Authentication**: JWT token-based auth with guards
- **HTTP**: Interceptors for token attachment and error handling

### Backend (Python Flask)
- **Framework**: Flask with Flask-JWT-Extended
- **Database**: MongoDB (via PyMongo)
- **Storage**: Azure Blob Storage
- **Authentication**: JWT tokens with bcrypt password hashing
- **API**: RESTful endpoints with CORS support

### Cloud Infrastructure (Azure)
- **Frontend Hosting**: Azure Static Web Apps
- **Backend Hosting**: Azure Container Instances
- **Database**: Azure Cosmos DB (MongoDB API)
- **File Storage**: Azure Blob Storage
- **Container Registry**: Azure Container Registry

## 🚀 Quick Start

### Prerequisites
- Node.js 16+ and npm
- Python 3.9+
- MongoDB (local) or Azure Cosmos DB
- Azure Storage Account (optional for local development)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR-USERNAME/mediacloud-mvp.git
   cd mediacloud-mvp
   ```

2. **Set up Backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   
   # Create .env file
   echo "MONGO_URI=mongodb://localhost:27017/mediacloud" > .env
   echo "JWT_SECRET_KEY=your-secret-key-here" >> .env
   echo "AZURE_STORAGE_CONNECTION_STRING=your-connection-string" >> .env
   
   # Run the backend
   python app.py
   ```

3. **Set up Frontend**
   ```bash
   cd frontend
   npm install
   npm start
   ```

4. **Access the application**
   - Frontend: http://localhost:4200
   - Backend API: http://localhost:5001

## 🌐 Deployment

### Deploy to Azure
Follow our comprehensive deployment guides:

1. **[Azure Deployment Guide](AZURE_DEPLOYMENT_GUIDE.md)** - Complete Azure setup
2. **[Deployment Checklist](DEPLOYMENT_CHECKLIST.md)** - Step-by-step checklist
3. **[GitHub Upload Guide](GITHUB_UPLOAD_GUIDE.md)** - Upload project to GitHub

### Quick Deploy Commands
```bash
# Set up Azure resources
./deploy-scripts/setup-azure-resources.sh

# Deploy backend
./deploy-scripts/deploy-backend.sh

# Deploy frontend
./deploy-scripts/deploy-frontend.sh
```

## 📁 Project Structure

```
mediacloud-mvp/
├── frontend/                 # Angular application
│   ├── src/
│   │   ├── app/
│   │   │   ├── core/        # Services, guards, interceptors
│   │   │   ├── pages/       # Components (login, register, home)
│   │   │   └── ...
│   │   ├── styles.css       # Global styles with design tokens
│   │   └── ...
│   ├── package.json
│   └── angular.json
├── backend/                  # Flask API
│   ├── models/              # Database models
│   ├── routes/              # API endpoints
│   ├── services/            # Business logic
│   ├── utils/               # Utilities
│   ├── app.py              # Main application
│   ├── requirements.txt
│   └── Dockerfile
├── deploy-scripts/          # Deployment automation
├── .kiro/                   # Kiro IDE specifications
└── docs/                    # Documentation
```

## 🔧 Configuration

### Environment Variables

**Backend (.env)**
```env
MONGO_URI=mongodb://localhost:27017/mediacloud
JWT_SECRET_KEY=your-super-secret-jwt-key
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;...
```

**Frontend (environment.ts)**
```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:5001/api'
};
```

## 🎨 Design System

MediaCloud uses a comprehensive design token system for consistent theming:

- **Typography**: Roboto and Google Sans fonts
- **Colors**: Neutral dark theme with accessible contrast ratios
- **Components**: Google Photos-inspired UI components
- **Responsive**: Mobile-first responsive design

## 🧪 Testing

### Frontend Tests
```bash
cd frontend
npm test                    # Unit tests
npm run e2e                # End-to-end tests
```

### Backend Tests
```bash
cd backend
python -m pytest          # Run all tests
python -m pytest tests/test_auth_endpoints.py  # Specific test file
```

## 📊 API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user (requires JWT)

### Media Management
- `POST /api/media/upload` - Upload media file (requires JWT)
- `GET /api/media` - Get media list with filters (requires JWT)
- `GET /api/media/storage` - Get storage usage summary (requires JWT)
- `PATCH /api/media/:id/favorite` - Toggle favorite status (requires JWT)
- `PATCH /api/media/:id/trash` - Move to/from trash (requires JWT)
- `DELETE /api/media/:id` - Permanently delete media (requires JWT)

### Health & Admin
- `GET /health` - Health check endpoint
- `POST /api/admin/storage/reconcile` - Reconcile storage usage (admin)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support & Troubleshooting

### Common Issues
- **Backend won't start**: Check MongoDB connection and environment variables
- **Frontend build errors**: Ensure Node.js version is 16+ and run `npm install`
- **Upload fails**: Verify Azure Storage connection string is configured
- **CORS errors**: Ensure backend CORS is configured for localhost:4200
- **Database errors**: Check MongoDB is running and accessible

### Get Help
- **Documentation**: Check our comprehensive guides in this repository
- **Issues**: Report bugs or request features via GitHub Issues
- **Azure Support**: Available with student subscription

## 🏆 Acknowledgments

- **Design Inspiration**: Google Photos for the clean, modern interface
- **Icons**: Bootstrap Icons for consistent iconography
- **Fonts**: Google Fonts (Roboto, Google Sans)
- **Cloud Platform**: Microsoft Azure for reliable hosting

---

**Built with ❤️ using Angular, Flask, and Azure**

🔗 **Live Demo**: [Your deployed app URL]
📧 **Contact**: [Your email]
🐙 **GitHub**: [Your GitHub profile]