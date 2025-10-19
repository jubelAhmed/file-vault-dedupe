# Abnormal File Vault - Architecture & Planning

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer (DRF)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ File Upload  │  │ File Search  │  │  Statistics  │     │
│  │   ViewSet    │  │   ViewSet    │  │    Views     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     Middleware Layer                         │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │  Rate Limiter        │  │  User Extraction     │        │
│  │  (Redis/Memory)      │  │  (UserId Header)     │        │
│  └──────────────────────┘  └──────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     Service Layer                            │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────┐ │
│  │  Deduplication   │  │  Storage Quota   │  │  Search  │ │
│  │    Service       │  │     Service      │  │  Service │ │
│  └──────────────────┘  └──────────────────┘  └──────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  File  │  │  UserStorage │  │  FileSystem  │     │
│  │    Model     │  │     Model    │  │   (Media)    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                    SQLite Database                           │
└─────────────────────────────────────────────────────────────┘
```

## 2. Database Design (Django Models)

### 2.1 File Model
```python
class File(models.Model):
    """
    Stores file metadata and handles deduplication through references
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    
    # File storage
    file = models.FileField(upload_to='uploads/', null=True, blank=True)
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100)  # MIME type
    size = models.BigIntegerField()  # File size in bytes
    
    # User tracking
    user_id = models.CharField(max_length=255, db_index=True)
    
    # Deduplication
    file_hash = models.CharField(max_length=64, db_index=True)  # SHA-256
    is_reference = models.BooleanField(default=False)
    original_file = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.CASCADE,
        related_name='references'
    )
    
    # Metadata
    uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'file_uploads'
        indexes = [
            models.Index(fields=['user_id', 'uploaded_at']),
            models.Index(fields=['user_id', 'file_type']),
            models.Index(fields=['file_hash']),
        ]
```

### 2.2 UserStorage Model
```python
class UserStorage(models.Model):
    """
    Tracks storage usage per user for quota enforcement
    """
    user_id = models.CharField(max_length=255, unique=True, primary_key=True)
    total_storage_used = models.BigIntegerField(default=0)  # Actual bytes used
    original_storage_used = models.BigIntegerField(default=0)  # Without dedup
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_storage'
```

### 2.3 Database Indexes Strategy
- **user_id**: Fast filtering by user
- **file_hash**: Quick duplicate detection
- **uploaded_at**: Time-based filtering
- **Composite indexes**: user_id + uploaded_at, user_id + file_type for common queries

## 3. Serializer Planning

### 3.1 FileUploadSerializer
```python
class FileUploadSerializer(serializers.ModelSerializer):
    reference_count = serializers.SerializerMethodField()
    
    class Meta:
        model = File
        fields = [
            'id', 'file', 'original_filename', 'file_type', 
            'size', 'uploaded_at', 'user_id', 'file_hash',
            'reference_count', 'is_reference', 'original_file'
        ]
        read_only_fields = [
            'id', 'file_hash', 'uploaded_at', 'user_id',
            'is_reference', 'original_file'
        ]
    
    def get_reference_count(self, obj):
        if obj.is_reference:
            return obj.original_file.references.count()
        return obj.references.count()
```

### 3.2 StorageStatsSerializer
```python
class StorageStatsSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    total_storage_used = serializers.IntegerField()
    original_storage_used = serializers.IntegerField()
    storage_savings = serializers.IntegerField()
    savings_percentage = serializers.FloatField()
```

## 4. Deduplication Strategy

### 4.1 Algorithm Flow
```
1. Calculate SHA-256 hash of uploaded file
2. Check if hash exists for ANY user in database
3. If exists:
   - Create reference record (is_reference=True)
   - Point to original file
   - Don't save physical file
   - Update original_storage_used only
4. If new:
   - Save physical file
   - Create original record (is_reference=False)
   - Update both total_storage_used and original_storage_used
```

### 4.2 Implementation Approach
```python
def handle_file_upload(user_id, uploaded_file):
    # Calculate hash
    file_hash = calculate_sha256(uploaded_file)
    
    # Check for existing file with same hash (any user)
    existing_file = File.objects.filter(
        file_hash=file_hash,
        is_reference=False
    ).first()
    
    if existing_file:
        # Create reference
        new_file = File.objects.create(
            original_filename=uploaded_file.name,
            file_type=uploaded_file.content_type,
            size=uploaded_file.size,
            user_id=user_id,
            file_hash=file_hash,
            is_reference=True,
            original_file=existing_file,
            file=existing_file.file  # Reference same file path
        )
        # Update only original_storage_used
        update_storage(user_id, original_only=True, size=uploaded_file.size)
    else:
        # Save new file
        new_file = File.objects.create(
            file=uploaded_file,
            original_filename=uploaded_file.name,
            file_type=uploaded_file.content_type,
            size=uploaded_file.size,
            user_id=user_id,
            file_hash=file_hash,
            is_reference=False
        )
        # Update both counters
        update_storage(user_id, original_only=False, size=uploaded_file.size)
    
    return new_file
```

### 4.3 Deletion Strategy
```python
def handle_file_deletion(file_obj):
    if file_obj.is_reference:
        # Just delete reference record
        # Update original_storage_used
        update_storage(file_obj.user_id, subtract=True, 
                      original_only=True, size=file_obj.size)
        file_obj.delete()
    else:
        # Check if any references exist
        ref_count = file_obj.references.count()
        if ref_count == 0:
            # Delete physical file
            file_obj.file.delete()
            # Update both counters
            update_storage(file_obj.user_id, subtract=True,
                          original_only=False, size=file_obj.size)
        else:
            # Don't delete physical file, just mark
            # Transfer ownership to first reference
            # Or implement reference transfer logic
            pass
```

## 5. Search & Filtering Planning

### 5.1 FilterSet Configuration
```python
class FileUploadFilter(filters.FilterSet):
    search = filters.CharFilter(
        field_name='original_filename', 
        lookup_expr='icontains'
    )
    file_type = filters.CharFilter(field_name='file_type', lookup_expr='exact')
    min_size = filters.NumberFilter(field_name='size', lookup_expr='gte')
    max_size = filters.NumberFilter(field_name='size', lookup_expr='lte')
    start_date = filters.IsoDateTimeFilter(
        field_name='uploaded_at', 
        lookup_expr='gte'
    )
    end_date = filters.IsoDateTimeFilter(
        field_name='uploaded_at', 
        lookup_expr='lte'
    )
    
    class Meta:
        model = File
        fields = ['search', 'file_type', 'min_size', 'max_size', 
                  'start_date', 'end_date']
```

### 5.2 Query Optimization
- Use `select_related('original_file')` for joins
- Add `only()` to limit fields in large datasets
- Implement pagination (PageNumberPagination)
- Database indexes on filtered fields

### 5.3 Large Dataset Handling
```python
class FileUploadViewSet(viewsets.ModelViewSet):
    pagination_class = PageNumberPagination
    
    def get_queryset(self):
        queryset = File.objects.filter(
            user_id=self.request.user_id
        ).select_related('original_file')
        
        # Apply filters
        return FileUploadFilter(
            self.request.GET, 
            queryset=queryset
        ).qs
```

## 6. Large File Handling Strategy

### 6.1 Chunked Upload (Future Enhancement)
- Current implementation: Standard Django file upload
- Recommendation: For files > 5MB, implement chunked upload
- Use `request.upload_handlers` to customize upload behavior

### 6.2 Memory Management
```python
# Calculate hash in chunks to avoid memory issues
def calculate_sha256(file_obj):
    hasher = hashlib.sha256()
    for chunk in file_obj.chunks(chunk_size=8192):
        hasher.update(chunk)
    file_obj.seek(0)  # Reset file pointer
    return hasher.hexdigest()
```

### 6.3 Storage Optimization
- Store files with UUID-based names to avoid collisions
- Use `upload_to` callable for dynamic paths
- Consider file compression for text files (future)

## 7. Rate Limiting Implementation

### 7.1 Simple Memory-Based (Development)
```python
from collections import defaultdict
from time import time

class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.calls = defaultdict(list)  # {user_id: [timestamps]}
        self.MAX_CALLS = 2
        self.TIME_WINDOW = 1  # seconds
    
    def __call__(self, request):
        user_id = request.headers.get('UserId')
        if not user_id:
            return JsonResponse({'error': 'UserId header required'}, 
                              status=401)
        
        now = time()
        user_calls = self.calls[user_id]
        
        # Remove old calls outside window
        user_calls[:] = [t for t in user_calls if now - t < self.TIME_WINDOW]
        
        if len(user_calls) >= self.MAX_CALLS:
            return JsonResponse({'error': 'Call Limit Reached'}, status=429)
        
        user_calls.append(now)
        request.user_id = user_id
        
        return self.get_response(request)
```

### 7.2 Redis-Based (Production)
```python
# Using django-ratelimit or custom Redis implementation
from django_ratelimit.decorators import ratelimit

@ratelimit(key='header:UserId', rate='2/s', method='ALL')
def view_function(request):
    pass
```

## 8. Storage Quota Implementation

### 8.1 Pre-Upload Check
```python
def check_storage_quota(user_id, file_size):
    STORAGE_LIMIT = 10 * 1024 * 1024  # 10MB in bytes
    
    storage, _ = UserStorage.objects.get_or_create(user_id=user_id)
    
    if storage.total_storage_used + file_size > STORAGE_LIMIT:
        raise StorageQuotaExceeded("Storage Quota Exceeded")
    
    return True
```

### 8.2 Atomic Updates
```python
from django.db import transaction

@transaction.atomic
def update_storage(user_id, size, original_only=False, subtract=False):
    storage, _ = UserStorage.objects.select_for_update().get_or_create(
        user_id=user_id
    )
    
    multiplier = -1 if subtract else 1
    
    storage.original_storage_used += (size * multiplier)
    
    if not original_only:
        storage.total_storage_used += (size * multiplier)
    
    storage.save()
```

## 9. API Endpoints Structure

```
files/
├── views.py
│   ├── FileUploadViewSet (list, create, retrieve, destroy)
│   ├── storage_stats (GET)
│   └── file_types (GET)
├── serializers.py
├── filters.py
├── services/
│   ├── deduplication_service.py
│   ├── storage_service.py
│   └── hash_service.py
├── middleware/
│   └── rate_limit_middleware.py
└── utils/
    └── validators.py
```

## 10. Configuration Settings

```python
# settings.py

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Storage Settings
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

# Rate Limiting
RATE_LIMIT_CALLS = 2
RATE_LIMIT_WINDOW = 1  # seconds

# Storage Quota
STORAGE_QUOTA_PER_USER = 10 * 1024 * 1024  # 10MB

# Pagination
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ]
}
```

## 11. Testing Strategy

### Key Test Cases:
1. **Deduplication**: Upload same file twice, verify only one physical copy
2. **Rate Limiting**: Make 3 rapid requests, verify 3rd is blocked
3. **Storage Quota**: Upload files until quota exceeded
4. **Search**: Test each filter parameter and combinations
5. **Deletion**: Verify reference counting and physical file deletion
6. **Concurrent Uploads**: Test race conditions with transactions

## 12. Docker Configuration

```yaml
# docker-compose.yml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./media:/app/media
      - ./db.sqlite3:/app/db.sqlite3
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings
```

## 13. Performance Considerations

1. **Database**: Add indexes on frequently queried fields
2. **File Storage**: Use UUID-based filenames to avoid collisions
3. **Hash Calculation**: Chunk-based processing for large files
4. **Caching**: Consider caching file_types list
5. **Query Optimization**: Use select_related and prefetch_related
6. **Pagination**: Limit result sets for large queries

## 14. Security Considerations

1. **File Validation**: Check MIME types and file extensions
2. **Path Traversal**: Sanitize filenames
3. **User Isolation**: Always filter by user_id
4. **Rate Limiting**: Prevent abuse
5. **File Size Limits**: Prevent DoS attacks