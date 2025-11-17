# Search Indexing API Endpoints

## New Endpoints

### 1. Search by Keyword

**Endpoint:** `GET /api/files/search/`

**Description:** Search files by keyword(s) extracted from file content.

**Query Parameters:**
- `keyword` (string, optional): Single keyword to search for
- `keywords` (string, optional): Comma-separated list of keywords for OR search

**Headers:**
- `UserId` (required): User ID for user isolation

**Examples:**

```bash
# Single keyword search
curl "http://localhost:8000/api/files/search/?keyword=contract" \
  -H "UserId: user123"

# Multiple keywords (OR search)
curl "http://localhost:8000/api/files/search/?keywords=contract,agreement,invoice" \
  -H "UserId: user123"
```

**Response:**

```json
{
  "count": 2,
  "results": [
    {
      "id": "abc-123-uuid",
      "original_filename": "contract.pdf",
      "file_type": "application/pdf",
      "size": 45678,
      "uploaded_at": "2025-11-05T10:30:00Z",
      "is_reference": false,
      "reference_count": 0
    },
    {
      "id": "def-456-uuid",
      "original_filename": "agreement.docx",
      "file_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "size": 23456,
      "uploaded_at": "2025-11-05T09:15:00Z",
      "is_reference": false,
      "reference_count": 0
    }
  ]
}
```

**Status Codes:**
- `200 OK`: Success
- `400 Bad Request`: Missing keyword parameter
- `500 Internal Server Error`: Search failed

---

### 2. Index Statistics

**Endpoint:** `GET /api/files/index_stats/`

**Description:** Get statistics about the search index.

**Headers:**
- `UserId` (optional): User ID header (not used for this endpoint)

**Example:**

```bash
curl "http://localhost:8000/api/files/index_stats/"
```

**Response:**

```json
{
  "total_keywords": 1523,
  "top_keyword": {
    "keyword": "document",
    "file_count": 45
  }
}
```

**Status Codes:**
- `200 OK`: Success
- `500 Internal Server Error`: Failed to get stats

---

## Existing Endpoints (Modified)

### 3. Upload File

**Endpoint:** `POST /api/files/`

**Description:** Upload a new file (now with automatic indexing).

**Changes:** 
- After successful upload, a Celery task is automatically queued to extract and index the file content
- Upload response is immediate (indexing happens in background)

**Headers:**
- `UserId` (required): User ID

**Body:**
- `file` (file): File to upload (multipart/form-data)

**Example:**

```bash
curl -X POST http://localhost:8000/api/files/ \
  -H "UserId: user123" \
  -F "file=@document.pdf"
```

**Response:**

```json
{
  "message": "File uploaded successfully",
  "data": {
    "id": "abc-123-uuid",
    "original_filename": "document.pdf",
    "file_type": "application/pdf",
    "size": 45678,
    "uploaded_at": "2025-11-05T10:30:00Z",
    "is_reference": false,
    "file_url": "/media/uploads/abc-123.pdf"
  }
}
```

**Note:** File content indexing happens asynchronously after this response is sent.

---

## Complete API Reference

### File Management

| Method | Endpoint | Description | New/Modified |
|--------|----------|-------------|--------------|
| GET | `/api/files/` | List user's files | Existing |
| POST | `/api/files/` | Upload file | **Modified** (now triggers indexing) |
| GET | `/api/files/{id}/` | Get file details | Existing |
| DELETE | `/api/files/{id}/` | Delete file | Existing |
| GET | `/api/files/storage_stats/` | Get storage statistics | Existing |
| GET | `/api/files/deduplication_stats/` | Get deduplication statistics | Existing |
| GET | `/api/files/file_types/` | Get unique file types | Existing |

### Search & Indexing (New)

| Method | Endpoint | Description | New/Modified |
|--------|----------|-------------|--------------|
| GET | `/api/files/search/` | Search files by keyword(s) | **New** |
| GET | `/api/files/index_stats/` | Get index statistics | **New** |

---

## Python SDK Examples

### Using SearchService Directly

```python
from files.services.search_service import SearchService

# Search by single keyword
files = SearchService.search_files_by_keyword('contract', user_id='user123')
print(f"Found {len(files)} files")

# Search by multiple keywords (OR)
files = SearchService.search_files_by_keywords(
    ['contract', 'agreement', 'invoice'], 
    user_id='user123'
)

# Get statistics
stats = SearchService.get_keyword_stats()
print(f"Total keywords: {stats['total_keywords']}")
```

### Manual Task Execution

```python
from files.tasks import index_file_content_task, reindex_all_files

# Index a specific file
result = index_file_content_task.delay('file-uuid-here')

# Wait for result (blocking)
task_result = result.get()
print(task_result)
# {'status': 'completed', 'keywords_indexed': 45, ...}

# Reindex all files
reindex_all_files.delay()
```

---

## Testing with cURL

### Complete Workflow

```bash
# 1. Upload a text file
echo "This is a test contract agreement for testing purposes" > test.txt
curl -X POST http://localhost:8000/api/files/ \
  -H "UserId: testuser" \
  -F "file=@test.txt"

# 2. Wait a few seconds for indexing to complete
sleep 5

# 3. Search for keyword "contract"
curl "http://localhost:8000/api/files/search/?keyword=contract" \
  -H "UserId: testuser"

# 4. Search for multiple keywords
curl "http://localhost:8000/api/files/search/?keywords=contract,agreement,test" \
  -H "UserId: testuser"

# 5. Get index statistics
curl "http://localhost:8000/api/files/index_stats/"

# 6. Clean up - delete the file
# (Get file ID from upload response)
curl -X DELETE http://localhost:8000/api/files/{file-id}/ \
  -H "UserId: testuser"
```

---

## Integration with Frontend

### React/TypeScript Example

```typescript
// Search by keyword
const searchByKeyword = async (keyword: string, userId: string) => {
  const response = await fetch(
    `http://localhost:8000/api/files/search/?keyword=${encodeURIComponent(keyword)}`,
    {
      headers: {
        'UserId': userId
      }
    }
  );
  
  const data = await response.json();
  return data.results;
};

// Search by multiple keywords
const searchByKeywords = async (keywords: string[], userId: string) => {
  const keywordsParam = keywords.join(',');
  const response = await fetch(
    `http://localhost:8000/api/files/search/?keywords=${encodeURIComponent(keywordsParam)}`,
    {
      headers: {
        'UserId': userId
      }
    }
  );
  
  const data = await response.json();
  return data.results;
};

// Get index stats
const getIndexStats = async () => {
  const response = await fetch('http://localhost:8000/api/files/index_stats/');
  return await response.json();
};

// Usage
const files = await searchByKeyword('contract', 'user123');
console.log(`Found ${files.length} files`);

const multiFiles = await searchByKeywords(['contract', 'agreement'], 'user123');

const stats = await getIndexStats();
console.log(`Total keywords: ${stats.total_keywords}`);
```

---

## Response Formats

### File Object

```typescript
interface File {
  id: string;                // UUID
  original_filename: string; // Original filename
  file_type: string;         // MIME type
  size: number;              // Size in bytes
  uploaded_at: string;       // ISO 8601 timestamp
  is_reference: boolean;     // Is this a deduplicated reference
  reference_count: number;   // Number of references to this file
  file_url?: string;         // URL to download file
}
```

### Search Response

```typescript
interface SearchResponse {
  count: number;
  results: File[];
}
```

### Index Stats Response

```typescript
interface IndexStats {
  total_keywords: number;
  top_keyword: {
    keyword: string | null;
    file_count: number;
  };
}
```

---

## Rate Limiting

All endpoints respect the existing rate limiting configuration:

```python
RATE_LIMIT_CALLS = 2      # Max calls
RATE_LIMIT_WINDOW = 1     # Per second
```

If rate limit is exceeded, you'll receive:

```json
{
  "error": "Rate limit exceeded",
  "details": "Too many requests. Please wait before trying again."
}
```

**Status Code:** `429 Too Many Requests`

---

## CORS Configuration

Search endpoints are accessible from the configured CORS origins (same as existing endpoints):

```python
CORS_ALLOW_ALL_ORIGINS = True  # Development
CORS_ALLOWED_ORIGINS = []      # Configure for production
```

---

## Supported File Types for Indexing

| Category | MIME Type | Extensions | Extraction Method |
|----------|-----------|------------|-------------------|
| Text | text/plain | .txt | Direct read |
| Text | text/csv | .csv | Direct read |
| Text | text/html | .html | Direct read |
| Text | text/xml | .xml | Direct read |
| PDF | application/pdf | .pdf | PyPDF2 |
| Word | application/vnd.openxmlformats-officedocument.wordprocessingml.document | .docx | python-docx |
| Word | application/msword | .doc | python-docx |
| Excel | application/vnd.openxmlformats-officedocument.spreadsheetml.sheet | .xlsx | openpyxl |
| Image | image/png | .png | Tesseract OCR |
| Image | image/jpeg | .jpg, .jpeg | Tesseract OCR |
| Image | image/tiff | .tiff | Tesseract OCR |

Files of unsupported types will be uploaded successfully but won't be indexed for search.

---

## Error Handling

### Search Endpoint Errors

```json
// Missing keyword parameter
{
  "error": "Please provide either \"keyword\" or \"keywords\" parameter"
}

// Search failed
{
  "error": "Search failed",
  "details": "Error message here"
}
```

### Index Stats Errors

```json
// Failed to get stats
{
  "error": "Failed to get index stats",
  "details": "Error message here"
}
```

---

## Postman Collection

Update your existing Postman collection with these new endpoints:

```json
{
  "info": {
    "name": "Search Indexing Endpoints"
  },
  "item": [
    {
      "name": "Search by Keyword",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "UserId",
            "value": "{{userId}}"
          }
        ],
        "url": {
          "raw": "{{baseUrl}}/api/files/search/?keyword=contract",
          "host": ["{{baseUrl}}"],
          "path": ["api", "files", "search_by_keyword"],
          "query": [
            {
              "key": "keyword",
              "value": "contract"
            }
          ]
        }
      }
    },
    {
      "name": "Index Statistics",
      "request": {
        "method": "GET",
        "url": {
          "raw": "{{baseUrl}}/api/files/index_stats/",
          "host": ["{{baseUrl}}"],
          "path": ["api", "files", "index_stats"]
        }
      }
    }
  ]
}
```

---

## Next Steps

1. ✅ Endpoints are ready to use
2. Test with sample files
3. Integrate into frontend application
4. Monitor Celery logs for indexing progress
5. Check Django Admin for indexed keywords

**Need help?** See `CELERY_SETUP.md` for detailed setup instructions.

