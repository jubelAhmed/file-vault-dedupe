# File Vault Dedupe

A full-stack file management system with intelligent deduplication, content search, and storage quota management. Built with Django REST Framework and React.

## 🚀 Technology Stack

### Backend
- Django 4.x (Python web framework)
- Django REST Framework (API development)
- SQLite (Development database)
- Gunicorn (WSGI HTTP Server)
- WhiteNoise (Static file serving)

### Frontend
- React 18 with TypeScript
- TanStack Query (React Query) for data fetching
- Axios for API communication
- Tailwind CSS for styling
- Heroicons for UI elements

### Infrastructure
- Docker and Docker Compose
- Local file storage with volume mounting

## 📋 Prerequisites

Before you begin, ensure you have installed:
- Docker (20.10.x or higher) and Docker Compose (2.x or higher)
- Node.js (18.x or higher) - for local development
- Python (3.9 or higher) - for local development

## 🛠️ Installation & Setup

### Using Docker (Recommended)

```bash
docker-compose up --build
```

This will start:
- **Redis** - Message broker for Celery (port 6379)
- **Backend** - Django API server (port 8000)
- **Celery** - Background worker for file indexing
- **Frontend** - React application (port 3000)

All services are automatically configured and connected.

### Local Development Setup

#### Backend Setup
1. **Create and activate virtual environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create necessary directories**
   ```bash
   mkdir -p media staticfiles data
   ```
4. **Create Environment File**
    Create `.env`:
   ```
   # Rate Limiting Configuration
   MAX_CALLS=10         # Maximum calls per time window
   TIME_WINDOW=1        # Time window in seconds
   
   # Storage Configuration
   STORAGE_QUOTA_PER_USER=10485760  # 10MB per user
   ```
   
   **Note**: Rate limiting uses Django's cache framework. For development, it uses `LocMemCache` (in-memory). For production, configure Redis or Memcached in `settings.py` for multi-container deployments.

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Start the development server**
   ```bash
   python manage.py runserver
   ```

#### Testing and Coverage

1. **Run all tests**
   ```bash
   cd backend
   source venv/bin/activate
   python manage.py test files.tests
   ```

2. **Run specific test files**
   ```bash
   # Test models and serializers
   python manage.py test files.tests.test_models
   
   # Test API endpoints
   python manage.py test files.tests.test_api
   
   # Test filtering functionality
   python manage.py test files.tests.test_filters
   
   # Test rate limiting
   python manage.py test files.tests.test_rate_limiting
   
   # Test services and utilities
   python manage.py test files.tests.test_services
   ```

3. **Run tests with coverage**
   ```bash
   # Install coverage if not already installed
   pip install coverage
   
   # Run tests with coverage
   coverage run --source='.' manage.py test files.tests
   
   # Generate coverage report
   coverage report
   
   # Generate HTML coverage report
   coverage html
   ```

4. **View coverage report**
   ```bash
   # Open HTML report in browser
   open htmlcov/index.html
   ```

5. **Test categories**
   - **Models**: File and UserStorage model functionality
   - **API**: CRUD operations, user isolation, stats endpoints
   - **Filters**: Search, file type, size, and date filtering
   - **Rate Limiting**: Per-user rate limiting enforcement
   - **Services**: Hash, storage, and deduplication services

#### Frontend Setup
1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Create environment file**
   Create `.env.local`:
   ```
   REACT_APP_API_URL=http://localhost:8000/api
   ```

3. **Start development server**
   ```bash
   npm start
   ```

## 🌐 Accessing the Application

- Frontend Application: http://localhost:3000
- Backend API: http://localhost:8000/api

## 📝 API Documentation

### File Management Endpoints

#### List Files
- **GET** `/api/files/`
- Returns a list of all uploaded files
- Response includes file metadata (name, size, type, upload date)

#### Upload File
- **POST** `/api/files/`
- Upload a new file
- Request: Multipart form data with 'file' field
- Returns: File metadata including ID and upload status

#### Get File Details
- **GET** `/api/files/<file_id>/`
- Retrieve details of a specific file
- Returns: Complete file metadata

#### Delete File
- **DELETE** `/api/files/<file_id>/`
- Remove a file from the system
- Returns: 204 No Content on success

#### Download File
- Access file directly through the file URL provided in metadata

## 🗄️ Project Structure

```
file-vault-dedupe/
├── backend/                # Django backend
│   ├── files/             # Main application
│   │   ├── models.py      # Data models
│   │   ├── views.py       # API views
│   │   ├── urls.py        # URL routing
│   │   └── serializers.py # Data serialization
│   ├── core/              # Project settings
│   └── requirements.txt   # Python dependencies
├── frontend/              # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── services/      # API services
│   │   └── types/         # TypeScript types
│   └── package.json      # Node.js dependencies
├── postman/               # Postman API collections
│   ├── File-Vault-Dedupe-API.postman_collection.json
│   └── File-Vault-Dedupe-Environment.postman_environment.json
└── docker-compose.yml    # Docker composition (includes Redis, Backend, Celery, Frontend)
```

## 🔧 Development Features

- Hot reloading for both frontend and backend
- React Query DevTools for debugging data fetching
- TypeScript for better development experience
- Tailwind CSS for rapid UI development

## 🐛 Troubleshooting

1. **Port Conflicts**
   ```bash
   # If ports 3000 or 8000 are in use, modify docker-compose.yml or use:
   # Frontend: npm start -- --port 3001
   # Backend: python manage.py runserver 8001
   ```

2. **File Upload Issues**
   - Maximum file size: 10MB
   - Ensure proper permissions on media directory
   - Check network tab for detailed error messages

3. **Database Issues**
   ```bash
   # Reset database
   rm backend/data/db.sqlite3
   python manage.py migrate
   ```

## 🎯 Key Features

- **Intelligent Deduplication**: Automatically detects and eliminates duplicate files across all users, saving storage space
- **Content-Based Search**: Search files by keywords extracted from their content (PDF, DOCX, XLSX, TXT, and more)
- **Storage Quota Management**: Per-user storage limits with real-time tracking and statistics
- **Async Processing**: Background file indexing using Celery for non-blocking uploads
- **Security First**: File validation, content-type checking, rate limiting, and user isolation
- **RESTful API**: Comprehensive API with filtering, pagination, and search capabilities

## 📚 Documentation

- [API Documentation](backend/API_ENDPOINTS.md) - Complete API reference
- [Celery Setup Guide](backend/CELERY_SETUP.md) - Background task processing setup
- [Postman Collection](postman/) - API testing collections

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the MIT License.

## 👤 Author

**Jubel Ahmed** 

