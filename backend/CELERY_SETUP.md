# Celery Setup Guide for File Search Indexing

This guide explains how to set up and use the Celery-based file content indexing system.

## Overview

The system automatically extracts text content from uploaded files and creates a searchable keyword index. This happens asynchronously in the background using Celery workers.

### Features

- **Automatic indexing**: Files are indexed automatically after upload
- **Content extraction**: Supports PDF, DOCX, XLSX, TXT, CSV, HTML, XML, and images (OCR)
- **Keyword extraction**: Extracts and indexes individual words from file content
- **Deduplication**: Keywords are shared across files (many-to-many relationship)
- **Async processing**: Doesn't block file uploads

## Prerequisites

### 1. Redis Server

Celery requires a message broker. We use Redis.

**Install Redis:**

```bash
# macOS
brew install redis

# Ubuntu/Debian
sudo apt-get install redis-server

# CentOS/RHEL
sudo yum install redis
```

**Start Redis:**

```bash
# macOS
brew services start redis

# Linux
sudo systemctl start redis
sudo systemctl enable redis
```

**Verify Redis is running:**

```bash
redis-cli ping
# Should return: PONG
```

### 2. Python Dependencies

Install the required Python packages:

```bash
cd backend
pip install -r requirements.txt
```

### 3. Tesseract (Optional - for image OCR)

If you want to extract text from images:

```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# CentOS/RHEL
sudo yum install tesseract
```

## Configuration

### Environment Variables

Add these to your `.env` file (optional, defaults are provided):

```bash
# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=django-db

# Search Indexing Configuration
SEARCH_INDEX_MIN_WORD_LENGTH=3
SEARCH_INDEX_MAX_WORD_LENGTH=50
```

### Django Settings

The following settings are already configured in `core/settings.py`:

- Celery broker and result backend
- Search indexing parameters
- Stop words list

## Running the System

### 1. Run Database Migrations

Create the FileSearchIndex table:

```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

### 2. Start the Django Server

```bash
python manage.py runserver
```

### 3. Start the Celery Worker

In a **separate terminal**:

```bash
cd backend
celery -A core worker --loglevel=info
```

**For development with auto-reload:**

```bash
celery -A core worker --loglevel=info --pool=solo
```

**For macOS (if you get fork errors):**

```bash
celery -A core worker --loglevel=info --pool=threads
```

### 4. (Optional) Start Celery Beat (for scheduled tasks)

If you want to run periodic tasks:

```bash
celery -A core beat --loglevel=info
```

## Using the Indexing System

### Automatic Indexing

Files are automatically indexed after upload. The process:

1. User uploads a file via the API
2. File is saved and deduplicated
3. Celery task is queued: `index_file_content_task.delay(file_id)`
4. Celery worker picks up the task
5. Content is extracted from the file
6. Keywords are extracted from the content
7. FileSearchIndex entries are created/updated

### Manual Reindexing

To reindex all files in the system:

```python
from files.tasks import reindex_all_files

# Queue reindexing for all files
reindex_all_files.delay()
```

Or via Django shell:

```bash
python manage.py shell
>>> from files.tasks import reindex_all_files
>>> reindex_all_files.delay()
```

### Searching by Keywords

Use the SearchService to search for files by keywords:

```python
from files.services.search_service import SearchService

# Search by single keyword
files = SearchService.search_files_by_keyword('contract', user_id='user123')

# Search by multiple keywords (OR operation)
files = SearchService.search_files_by_keywords(['contract', 'agreement'], user_id='user123')
```

## Supported File Types

The content extraction service supports:

- **Text files**: `.txt`, `.csv`, `.html`, `.xml`
- **PDF files**: `.pdf`
- **Word documents**: `.docx`, `.doc`
- **Excel files**: `.xlsx`
- **Images** (with OCR): `.png`, `.jpg`, `.jpeg`, `.tiff`

## Monitoring

### View Celery Tasks in Admin

1. Go to Django Admin: `http://localhost:8000/admin/`
2. Navigate to "Task results" (from django-celery-results)
3. View task status, results, and errors

### Check Celery Worker Status

```bash
celery -A core inspect active
celery -A core inspect stats
```

### View Logs

Celery worker logs will show:
- Tasks being processed
- Content extraction progress
- Indexing results
- Any errors

## Troubleshooting

### Redis Connection Error

```
Error: Redis connection failed
```

**Solution**: Ensure Redis is running:
```bash
redis-cli ping
brew services start redis  # macOS
```

### Import Error: No module named 'celery'

**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

### Task Not Executing

**Solution**: Check that:
1. Redis is running
2. Celery worker is running
3. Check worker logs for errors

### File Not Being Indexed

**Possible reasons**:
1. File type not supported
2. Content extraction failed
3. No text content in file
4. Celery task failed (check logs)

**Check task result**:
```python
from django_celery_results.models import TaskResult
TaskResult.objects.latest('date_created')
```

### OCR Not Working

**Solution**: Install Tesseract:
```bash
brew install tesseract  # macOS
```

## Performance Tuning

### Multiple Workers

Run multiple worker processes for better performance:

```bash
celery -A core worker --loglevel=info --concurrency=4
```

### Task Priorities

Modify task priority in `files/tasks.py`:

```python
@shared_task(bind=True, max_retries=3, priority=5)
def index_file_content_task(self, file_id: str):
    ...
```

### Production Deployment

For production, use a process manager like Supervisor or systemd:

**Example systemd service** (`/etc/systemd/system/celery.service`):

```ini
[Unit]
Description=Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/path/to/backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/celery -A core worker --loglevel=info --logfile=/var/log/celery/worker.log --pidfile=/var/run/celery/worker.pid

[Install]
WantedBy=multi-user.target
```

## API Usage Examples

### Get Files by Keyword

To add a search endpoint, update `files/views.py`:

```python
@action(detail=False, methods=['get'])
def search(self, request):
    """Search files by keyword."""
    keyword = request.query_params.get('keyword', '').strip()
    
    if not keyword:
        return Response({'error': 'Keyword required'}, status=400)
    
    from files.services.search_service import SearchService
    
    files = SearchService.search_files_by_keyword(
        keyword, 
        user_id=request.user_id
    )
    
    serializer = self.get_serializer(files, many=True)
    return Response(serializer.data)
```

Then access via:
```bash
GET /api/files/search/?keyword=contract
```

## Additional Resources

- [Celery Documentation](https://docs.celeryproject.org/)
- [Redis Documentation](https://redis.io/documentation)
- [Django Celery Integration](https://docs.celeryproject.org/en/stable/django/first-steps-with-django.html)

