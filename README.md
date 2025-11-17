# File Vault Dedupe

A production-ready file management platform featuring intelligent cross-user deduplication, content-based search, and comprehensive storage management. Built with Django REST Framework backend and React TypeScript frontend.

## Overview

File Vault Dedupe solves the problem of storage waste by automatically detecting duplicate files across all users. When multiple users upload the same file, only one copy is stored on disk while all users maintain access. The system also provides powerful content-based search capabilities, allowing users to find files by searching within their content, not just filenames.

## Core Features

### 🔄 Intelligent Deduplication
- **SHA-256 Hash-Based Detection**: Identifies duplicate files with cryptographic precision
- **Cross-User Deduplication**: Shares storage across all users while maintaining data isolation
- **Reference System**: Creates lightweight references instead of storing duplicate files
- **Automatic Cleanup**: Safely removes files only when all references are deleted

### 🔍 Content-Based Search
- **Keyword Extraction**: Automatically extracts searchable keywords from file content
- **Multi-Format Support**: Indexes text from PDF, DOCX, XLSX, PPTX, TXT, CSV, JSON, XML, and more
- **Fast Search**: Query files by keywords found within their content
- **User-Isolated Results**: Search results respect user boundaries

### 💾 Storage Management
- **Per-User Quotas**: Configurable storage limits per user
- **Real-Time Tracking**: Monitor storage usage and savings
- **Deduplication Statistics**: View system-wide storage savings
- **Quota Enforcement**: Prevents uploads that exceed limits

### ⚡ Asynchronous Processing
- **Celery Integration**: Background file indexing for non-blocking uploads
- **Redis Message Broker**: Reliable task queue management
- **Content Extraction**: Automatic text extraction and keyword indexing
- **Search Index Maintenance**: Automatic cleanup on file deletion

### 🔒 Security & Performance
- **File Validation**: Size limits, extension checking, and content-type verification
- **Rate Limiting**: Per-user API rate limiting to prevent abuse
- **User Isolation**: Complete data separation between users
- **Database Indexing**: Optimized queries for fast performance

## Technology Stack

**Backend:**
- Django 4.x with Django REST Framework
- Celery for asynchronous task processing
- Redis for message brokering and caching
- SQLite (development) / PostgreSQL (production-ready)
- Gunicorn for production deployment

**Frontend:**
- React 18 with TypeScript
- TanStack Query for efficient data fetching
- Axios for HTTP requests
- Tailwind CSS for modern UI

**Infrastructure:**
- Docker & Docker Compose for containerization
- GitHub Actions for CI/CD
- WhiteNoise for static file serving

## Quick Start

### Prerequisites
- Docker 20.10+ and Docker Compose 2.x+
- (Optional) Python 3.12+ and Node.js 18+ for local development

### Docker Setup (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd file-vault-dedupe

# Start all services
docker-compose up --build
```

This starts:
- **Redis** (port 6379) - Message broker for Celery
- **Backend API** (port 8000) - Django REST API
- **Celery Worker** - Background task processor
- **Frontend** (port 3000) - React application

Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api
- Health Check: http://localhost:8000/health/

### Local Development

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file (.env)
cat > .env << EOF
DJANGO_SECRET_KEY=your-secret-key-here
MAX_CALLS=10
TIME_WINDOW=1
STORAGE_QUOTA_PER_USER=10485760
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
EOF

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file (.env.local)
echo "REACT_APP_API_URL=http://localhost:8000/api" > .env.local

# Start development server
npm start
```

## API Usage

### Authentication
All API requests require a `UserId` header for user identification:

```bash
curl -H "UserId: user123" http://localhost:8000/api/files/
```

### Key Endpoints

**File Operations:**
- `GET /api/files/` - List files (supports filtering and search)
- `POST /api/files/` - Upload file
- `GET /api/files/{id}/` - Get file details
- `DELETE /api/files/{id}/` - Delete file

**Search:**
- `GET /api/files/search/?keyword=contract` - Search files by content keyword
- `GET /api/files/search/?keywords=contract,agreement` - Multi-keyword search

**Statistics:**
- `GET /api/files/storage_stats/` - User storage statistics
- `GET /api/files/deduplication_stats/` - System-wide deduplication stats
- `GET /api/files/index_stats/` - Search index statistics

**Filtering:**
- `GET /api/files/?search=filename` - Search by filename
- `GET /api/files/?file_type=application/pdf` - Filter by file type
- `GET /api/files/?min_size=1000&max_size=5000` - Filter by size range
- `GET /api/files/?start=2024-01-01&end=2024-12-31` - Filter by date range

See [API Documentation](backend/API_ENDPOINTS.md) for complete reference.

## Testing

```bash
cd backend

# Run all tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html

# Run specific test suite
python manage.py test files.tests.test_api
python manage.py test files.tests.test_services
```

Test coverage: **97%+**

## Project Structure

```
file-vault-dedupe/
├── backend/
│   ├── core/                    # Django project settings
│   │   ├── settings.py           # Configuration
│   │   ├── celery.py             # Celery setup
│   │   └── middleware/           # Custom middleware
│   ├── files/                    # Main application
│   │   ├── models.py             # Data models (File, UserStorage, FileSearchIndex)
│   │   ├── views.py              # API endpoints
│   │   ├── serializers.py        # Data serialization
│   │   ├── services/             # Business logic
│   │   │   ├── deduplication_service.py
│   │   │   ├── search_service.py
│   │   │   ├── storage_service.py
│   │   │   └── content_extraction_service.py
│   │   ├── tasks.py              # Celery tasks
│   │   └── tests/                # Test suite
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/            # React components
│   │   ├── services/             # API client
│   │   └── types/                # TypeScript definitions
│   └── package.json
├── postman/                       # API testing collections
├── .github/workflows/             # CI/CD pipelines
└── docker-compose.yml             # Container orchestration
```

## Configuration

### Environment Variables

**Backend (.env):**
- `DJANGO_SECRET_KEY` - Django secret key (required)
- `MAX_CALLS` - Rate limit: max requests per window (default: 10)
- `TIME_WINDOW` - Rate limit: time window in seconds (default: 1)
- `STORAGE_QUOTA_PER_USER` - Storage quota in bytes (default: 10MB)
- `CELERY_BROKER_URL` - Redis connection URL
- `CELERY_RESULT_BACKEND` - Redis result backend URL

**Frontend (.env.local):**
- `REACT_APP_API_URL` - Backend API URL

## Supported File Types for Content Search

The system can extract and index text content from:
- **Documents**: PDF, DOC, DOCX, ODT
- **Spreadsheets**: XLS, XLSX, ODS, CSV
- **Presentations**: PPT, PPTX, ODP
- **Text Files**: TXT, XML, HTML, RTF, JSON, YAML

Files are automatically indexed in the background after upload.

## CI/CD

GitHub Actions workflow automatically:
- Runs tests on push/PR
- Generates coverage reports
- Validates code quality

See `.github/workflows/backend.yml` for details.

## Documentation

- [API Endpoints Reference](backend/API_ENDPOINTS.md)
- [Celery Setup Guide](backend/CELERY_SETUP.md)

## License

This project is open source and available under the MIT License.

## Author

**Jubel Ahmed**

---

Built with ❤️ using Django, React, and modern DevOps practices.
