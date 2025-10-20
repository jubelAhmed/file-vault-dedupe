# Files App Test Suite

This directory contains comprehensive test cases for the Files app, organized into 5 focused test files for simplicity and clarity.

## Test Structure

### 📁 Test Files

- **`test_models.py`** - Tests for models and serializers
  - File and UserStorage model functionality
  - Model properties and methods
  - Serializer functionality and edge cases

- **`test_api.py`** - Tests for API endpoints, views, and workflows
  - File upload/download/delete operations
  - User isolation and permissions
  - Storage and deduplication stats endpoints
  - Health check endpoint
  - View error handling
  - Complete file lifecycle workflows
  - Multi-user deduplication scenarios
  - Storage quota enforcement workflows
  - Edge cases and error conditions

- **`test_filters.py`** - Tests for filtering functionality
  - Search by filename
  - Filter by file type, size, date range
  - Date-only filtering (ignores time component)
  - Combined filter operations

- **`test_rate_limiting.py`** - Tests for rate limiting
  - Per-user rate limiting
  - Rate limit enforcement
  - Skip paths (health check)

- **`test_services.py`** - Tests for service layer and utilities
  - Hash, storage, and deduplication services
  - Service error handling
  - Service functionality validation
  - File validators and middleware

## 🧪 Running Tests

### Run All Tests
```bash
python manage.py test files.tests
```

### Run Specific Test File
```bash
python manage.py test files.tests.test_models
python manage.py test files.tests.test_api
python manage.py test files.tests.test_filters
python manage.py test files.tests.test_services
python manage.py test files.tests.test_rate_limiting
```

### Run Specific Test Class
```bash
python manage.py test files.tests.test_models.FileModelTestCase
python manage.py test files.tests.test_api.FileAPITestCase
```

### Run Specific Test Method
```bash
python manage.py test files.tests.test_models.FileModelTestCase.test_file_creation
```

## 📊 Coverage

Current test coverage: **97%**

To run coverage analysis:
```bash
coverage run --source='.' manage.py test files.tests
coverage report --include="files/*"
```

## 🎯 Test Categories

### Unit Tests
- Model functionality (`test_models.py`)
- Service layer (`test_services.py`)
- Individual API endpoints (`test_api.py`)

### Integration Tests
- Complete workflows (`test_integration.py`)
- Cross-component interactions
- End-to-end scenarios

### Edge Case Tests
- Error conditions (`test_edge_cases.py`)
- Invalid inputs
- Boundary conditions

### Performance Tests
- Rate limiting (`test_rate_limiting.py`)
- Concurrent operations
- Large file handling

## 🔧 Test Configuration

Tests use Django's test framework with:
- **Test Database**: Automatically created and destroyed
- **File Storage**: Temporary directories for file uploads
- **Settings Override**: Custom settings for testing (quota limits, rate limits)
- **Mocking**: Used for external dependencies and error simulation

## 📝 Test Data

Tests create realistic test data:
- Multiple user IDs for isolation testing
- Various file types and sizes
- Controlled timestamps for date filtering
- Edge case filenames and content

## 🚀 Best Practices

1. **Isolation**: Each test is independent and can run in any order
2. **Cleanup**: Tests clean up after themselves
3. **Realistic Data**: Uses realistic file sizes, types, and user scenarios
4. **Error Testing**: Comprehensive error condition coverage
5. **Documentation**: Clear test names and docstrings explain what each test does

## 🔍 Debugging Tests

To debug failing tests:
```bash
# Run with verbose output
python manage.py test files.tests -v 2

# Run with debugger
python manage.py test files.tests --debug-mode

# Run specific failing test
python manage.py test files.tests.test_api.FileAPITestCase.test_file_upload_success
```
