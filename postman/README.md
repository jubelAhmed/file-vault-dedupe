# Postman API Collection

This directory contains Postman collections and environment files for testing the File Vault Dedupe API.

## Files

- **File-Vault-Dedupe-API.postman_collection.json** - Complete API collection with all endpoints
- **File-Vault-Dedupe-Environment.postman_environment.json** - Environment variables for local development

## Usage

### Import into Postman

1. Open Postman
2. Click **Import** button
3. Select both files:
   - `File-Vault-Dedupe-API.postman_collection.json`
   - `File-Vault-Dedupe-Environment.postman_environment.json`
4. Select the environment from the dropdown in Postman

### Environment Variables

The environment file includes:
- `base_url` - API base URL (default: `http://localhost:8000`)
- `user_id` - Default user ID for testing
- `user_id_2` - Second user ID for cross-user testing
- `file_id` - File ID (auto-populated after upload)

### Quick Start

1. Make sure the backend server is running: `python manage.py runserver`
2. Select the "File Vault Dedupe Environment" in Postman
3. Start with the "Health Check" endpoint to verify the server is running
4. Use the "Upload File" endpoint to test file uploads
5. Explore other endpoints in the collection

## Endpoints Included

- Health Check
- File Upload
- List Files
- Get File Details
- Delete File
- Storage Statistics
- Deduplication Statistics
- File Types
- Search by Keyword
- Index Statistics

## Notes

- All endpoints require the `UserId` header except the Health Check endpoint
- Update the `base_url` in the environment if your server runs on a different port
- The collection includes pre-request scripts for automatic file generation in tests

