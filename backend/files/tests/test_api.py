"""
Test cases for File API endpoints.
"""

import tempfile
import uuid

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from ..models import File


@override_settings(
    MEDIA_ROOT=tempfile.mkdtemp(),
    STORAGE_QUOTA_PER_USER=1024,  # 1KB for testing
    RATE_LIMIT_CALLS=100,  # High limit for testing
    RATE_LIMIT_WINDOW=1,
    CELERY_TASK_ALWAYS_EAGER=True,  # Run Celery tasks synchronously in tests
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class FileAPITestCase(APITestCase):
    """Test File API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user_id = "testuser123"
        self.other_user_id = "otheruser456"
        self.headers = {"UserId": self.user_id}
        self.other_headers = {"UserId": self.other_user_id}

        # Create test files
        self.small_file = SimpleUploadedFile("small.txt", b"Hello", content_type="text/plain")
        self.large_file = SimpleUploadedFile(
            "large.txt",
            b"X" * 2000,
            content_type="text/plain",  # 2KB file
        )
        self.image_file = SimpleUploadedFile(
            "test.jpg", b"fake_image_data", content_type="image/jpeg"
        )

    def test_file_upload_success(self):
        """Test successful file upload."""
        response = self.client.post(
            "/api/files/", {"file": self.small_file}, format="multipart", HTTP_UserId=self.user_id
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        self.assertEqual(response.data["message"], "File uploaded successfully")

        # Verify file was created
        file_obj = File.objects.get(user_id=self.user_id)
        self.assertEqual(file_obj.original_filename, "small.txt")
        self.assertEqual(file_obj.file_type, "text/plain")
        self.assertEqual(file_obj.size, 5)
        self.assertEqual(file_obj.user_id, self.user_id)

    def test_file_upload_missing_userid_header(self):
        """Test file upload without UserId header."""
        response = self.client.post("/api/files/", {"file": self.small_file}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.json())
        self.assertEqual(response.json()["error"], "UserId header is required")

    def test_file_upload_invalid_userid_format(self):
        """Test file upload with invalid UserId format."""
        response = self.client.post(
            "/api/files/",
            {"file": self.small_file},
            format="multipart",
            HTTP_UserId="ab",  # Too short
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.json())
        self.assertEqual(response.json()["error"], "Invalid UserId format")

    def test_file_upload_no_file(self):
        """Test file upload without file."""
        response = self.client.post("/api/files/", {}, format="multipart", HTTP_UserId=self.user_id)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "No file provided")

    def test_file_upload_storage_quota_exceeded(self):
        """Test file upload exceeding storage quota."""
        # First upload should succeed
        response1 = self.client.post(
            "/api/files/", {"file": self.small_file}, format="multipart", HTTP_UserId=self.user_id
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Second upload should fail due to quota
        response2 = self.client.post(
            "/api/files/", {"file": self.large_file}, format="multipart", HTTP_UserId=self.user_id
        )

        self.assertEqual(response2.status_code, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        self.assertIn("error", response2.data)
        self.assertEqual(response2.data["error"], "Storage quota exceeded")

    def test_file_upload_invalid_file_type(self):
        """Test file upload with invalid file type."""
        invalid_file = SimpleUploadedFile(
            "test.exe", b"executable_data", content_type="application/x-executable"
        )

        response = self.client.post(
            "/api/files/", {"file": invalid_file}, format="multipart", HTTP_UserId=self.user_id
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "File validation failed")

    def test_file_upload_invalid_filename(self):
        """Test file upload with invalid filename."""
        invalid_file = SimpleUploadedFile(
            "../../../etc/passwd", b"malicious_content", content_type="text/plain"
        )

        response = self.client.post(
            "/api/files/", {"file": invalid_file}, format="multipart", HTTP_UserId=self.user_id
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "File validation failed")

    def test_file_list_success(self):
        """Test successful file listing."""
        # Upload a file first
        self.client.post(
            "/api/files/", {"file": self.small_file}, format="multipart", HTTP_UserId=self.user_id
        )

        response = self.client.get("/api/files/", HTTP_UserId=self.user_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)

        file_data = response.data["results"][0]
        self.assertIn("id", file_data)
        self.assertIn("original_filename", file_data)
        self.assertIn("file_type", file_data)
        self.assertIn("size", file_data)
        self.assertIn("uploaded_at", file_data)
        self.assertIn("file_url", file_data)
        self.assertIn("is_duplicate", file_data)

    def test_file_list_user_isolation(self):
        """Test that users only see their own files."""
        # Upload file for user1
        self.client.post(
            "/api/files/", {"file": self.small_file}, format="multipart", HTTP_UserId=self.user_id
        )

        # Upload file for user2
        other_file = SimpleUploadedFile("other.txt", b"Other content", content_type="text/plain")
        self.client.post(
            "/api/files/", {"file": other_file}, format="multipart", HTTP_UserId=self.other_user_id
        )

        # Check user1 only sees their file
        response1 = self.client.get("/api/files/", HTTP_UserId=self.user_id)
        self.assertEqual(response1.data["count"], 1)
        self.assertEqual(response1.data["results"][0]["original_filename"], "small.txt")

        # Check user2 only sees their file
        response2 = self.client.get("/api/files/", HTTP_UserId=self.other_user_id)
        self.assertEqual(response2.data["count"], 1)
        self.assertEqual(response2.data["results"][0]["original_filename"], "other.txt")

    def test_file_list_missing_userid(self):
        """Test file list without UserId header."""
        response = self.client.get("/api/files/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.json())
        self.assertEqual(response.json()["error"], "UserId header is required")

    def test_file_list_empty(self):
        """Test file list when user has no files."""
        response = self.client.get("/api/files/", HTTP_UserId=self.user_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(len(response.data["results"]), 0)

    def test_file_delete_success(self):
        """Test successful file deletion."""
        # Upload a file first
        upload_response = self.client.post(
            "/api/files/", {"file": self.small_file}, format="multipart", HTTP_UserId=self.user_id
        )
        file_id = upload_response.data["data"]["id"]

        # Delete the file
        response = self.client.delete(f"/api/files/{file_id}/", HTTP_UserId=self.user_id)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIn("message", response.data)
        self.assertEqual(response.data["message"], "File deleted successfully")

        # Verify file was deleted
        self.assertFalse(File.objects.filter(id=file_id).exists())

    def test_file_delete_nonexistent(self):
        """Test deletion of non-existent file."""
        fake_id = str(uuid.uuid4())
        response = self.client.delete(f"/api/files/{fake_id}/", HTTP_UserId=self.user_id)

        # Non-existent file should return 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_file_delete_other_user_file(self):
        """Test deletion of another user's file."""
        # Upload file for user1
        upload_response = self.client.post(
            "/api/files/", {"file": self.small_file}, format="multipart", HTTP_UserId=self.user_id
        )
        file_id = upload_response.data["data"]["id"]

        # Try to delete with user2 - should return 404 because user2 can't see user1's files
        response = self.client.delete(f"/api/files/{file_id}/", HTTP_UserId=self.other_user_id)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_file_delete_missing_userid(self):
        """Test file deletion without UserId header."""
        fake_id = str(uuid.uuid4())
        response = self.client.delete(f"/api/files/{fake_id}/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.json())
        self.assertEqual(response.json()["error"], "UserId header is required")

    def test_file_deduplication(self):
        """Test file deduplication functionality."""
        # Upload same file for two users
        file_content = b"Identical content"
        file1 = SimpleUploadedFile("file1.txt", file_content, content_type="text/plain")
        file2 = SimpleUploadedFile("file2.txt", file_content, content_type="text/plain")

        # Upload for user1
        response1 = self.client.post(
            "/api/files/", {"file": file1}, format="multipart", HTTP_UserId=self.user_id
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response1.data["data"]["is_duplicate"])

        # Upload for user2 (should be deduplicated)
        response2 = self.client.post(
            "/api/files/", {"file": file2}, format="multipart", HTTP_UserId=self.other_user_id
        )
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response2.data["data"]["is_duplicate"])

    def test_storage_stats_success(self):
        """Test storage statistics endpoint."""
        # Upload a file first
        self.client.post(
            "/api/files/", {"file": self.small_file}, format="multipart", HTTP_UserId=self.user_id
        )

        response = self.client.get("/api/files/storage_stats/", HTTP_UserId=self.user_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("user_id", response.data)
        self.assertIn("total_storage_used", response.data)
        self.assertIn("original_storage_used", response.data)
        self.assertIn("quota_limit", response.data)
        self.assertIn("quota_remaining", response.data)
        self.assertIn("quota_usage_percentage", response.data)

        self.assertEqual(response.data["user_id"], self.user_id)
        # total_storage_used should be > 0 after first upload
        self.assertGreater(response.data["total_storage_used"], 0)
        # quota_remaining and usage should be based on original_storage_used
        limit = response.data["quota_limit"]
        original_used = response.data["original_storage_used"]
        self.assertEqual(response.data["quota_remaining"], limit - original_used)
        self.assertAlmostEqual(
            response.data["quota_usage_percentage"], (original_used / limit) * 100, places=4
        )

    def test_storage_stats_missing_userid(self):
        """Test storage stats without UserId header."""
        response = self.client.get("/api/files/storage_stats/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.json())
        self.assertEqual(response.json()["error"], "UserId header is required")

    def test_deduplication_stats_success(self):
        """Test deduplication statistics endpoint."""
        response = self.client.get("/api/files/deduplication_stats/", HTTP_UserId=self.user_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_files", response.data)
        self.assertIn("original_files", response.data)
        self.assertIn("reference_files", response.data)
        self.assertIn("deduplication_ratio", response.data)
        self.assertIn("total_original_storage", response.data)
        self.assertIn("total_actual_storage", response.data)
        self.assertIn("storage_savings", response.data)
        self.assertIn("savings_percentage", response.data)

    def test_file_types_success(self):
        """Test file types endpoint."""
        # Upload files of different types
        response1 = self.client.post(
            "/api/files/", {"file": self.small_file}, format="multipart", HTTP_UserId=self.user_id
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED, "First file upload failed")

        # Create a valid text file instead of fake image to avoid content validation issues
        pdf_file = SimpleUploadedFile(
            "test.pdf",
            b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 0\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF",
            content_type="application/pdf",
        )
        response2 = self.client.post(
            "/api/files/", {"file": pdf_file}, format="multipart", HTTP_UserId=self.user_id
        )
        self.assertEqual(
            response2.status_code, status.HTTP_201_CREATED, "Second file upload failed"
        )

        response = self.client.get("/api/files/file_types/", HTTP_UserId=self.user_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("file_types", response.data)
        self.assertIn("count", response.data)
        self.assertEqual(response.data["count"], 2, f"Expected 2 file types, got {response.data}")
        self.assertIn("text/plain", response.data["file_types"])
        self.assertIn("application/pdf", response.data["file_types"])

    def test_file_types_missing_userid(self):
        """Test file types without UserId header."""
        response = self.client.get("/api/files/file_types/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.json())
        self.assertEqual(response.json()["error"], "UserId header is required")

    def test_health_check(self):
        """Test health check endpoint (no UserId required)."""
        response = self.client.get("/health/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("status", response.data)
        self.assertIn("service", response.data)
        self.assertIn("version", response.data)
        self.assertEqual(response.data["status"], "healthy")
        self.assertEqual(response.data["service"], "file-vault-dedupe")

    def test_file_list_pagination(self):
        """Test file list pagination."""
        # Upload multiple files
        for i in range(5):
            file_obj = SimpleUploadedFile(
                f"file{i}.txt", f"Content {i}".encode(), content_type="text/plain"
            )
            self.client.post(
                "/api/files/", {"file": file_obj}, format="multipart", HTTP_UserId=self.user_id
            )

        response = self.client.get("/api/files/", HTTP_UserId=self.user_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 5)
        self.assertEqual(len(response.data["results"]), 5)
        self.assertIsNone(response.data["next"])
        self.assertIsNone(response.data["previous"])

    def test_file_list_ordering(self):
        """Test file list ordering."""
        # Upload files with different timestamps
        file1 = SimpleUploadedFile("file1.txt", b"Content 1", content_type="text/plain")
        file2 = SimpleUploadedFile("file2.txt", b"Content 2", content_type="text/plain")

        self.client.post(
            "/api/files/", {"file": file1}, format="multipart", HTTP_UserId=self.user_id
        )

        self.client.post(
            "/api/files/", {"file": file2}, format="multipart", HTTP_UserId=self.user_id
        )

        response = self.client.get("/api/files/", HTTP_UserId=self.user_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should be ordered by uploaded_at descending (newest first)
        self.assertEqual(response.data["results"][0]["original_filename"], "file2.txt")
        self.assertEqual(response.data["results"][1]["original_filename"], "file1.txt")

    def test_very_large_filename(self):
        """Test upload with very large filename."""
        large_filename = "a" * 300  # Exceeds max length
        large_file = SimpleUploadedFile(large_filename, b"Content", content_type="text/plain")

        response = self.client.post(
            "/api/files/", {"file": large_file}, format="multipart", HTTP_UserId=self.user_id
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_empty_file(self):
        """Test upload of empty file."""
        empty_file = SimpleUploadedFile("empty.txt", b"", content_type="text/plain")

        response = self.client.post(
            "/api/files/", {"file": empty_file}, format="multipart", HTTP_UserId=self.user_id
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["size"], 0)

    def test_file_with_special_characters(self):
        """Test upload with special characters in filename."""
        special_file = SimpleUploadedFile(
            "file with spaces & symbols!.txt", b"Content", content_type="text/plain"
        )

        response = self.client.post(
            "/api/files/", {"file": special_file}, format="multipart", HTTP_UserId=self.user_id
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data["data"]["original_filename"], "file with spaces & symbols!.txt"
        )

    def test_invalid_uuid_in_url(self):
        """Test accessing file with invalid UUID."""
        response = self.client.delete("/api/files/invalid-uuid/", HTTP_UserId=self.user_id)

        # Invalid UUID should return 404 (which is better than 500)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_malformed_userid_header(self):
        """Test with malformed UserId header."""
        response = self.client.get("/api/files/", HTTP_UserId="")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.json())

    def test_userid_with_special_characters(self):
        """Test with UserId containing special characters."""
        special_user_id = "user@domain.com"
        response = self.client.get("/api/files/", HTTP_UserId=special_user_id)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.json())
        self.assertEqual(response.json()["error"], "Invalid UserId format")

    def test_concurrent_uploads_same_file(self):
        """Test concurrent uploads of the same file."""
        file_content = b"Identical content"
        file1 = SimpleUploadedFile("file1.txt", file_content, content_type="text/plain")
        file2 = SimpleUploadedFile("file2.txt", file_content, content_type="text/plain")

        # Simulate concurrent uploads (in real scenario, these would be parallel)
        response1 = self.client.post(
            "/api/files/", {"file": file1}, format="multipart", HTTP_UserId=self.user_id
        )

        response2 = self.client.post(
            "/api/files/", {"file": file2}, format="multipart", HTTP_UserId=self.user_id
        )

        # Both should succeed, second should be deduplicated
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response1.data["data"]["is_duplicate"])
        self.assertTrue(response2.data["data"]["is_duplicate"])

    def test_complete_file_lifecycle(self):
        """Test complete file lifecycle: upload, list, download, delete."""
        # 1. Upload file
        file_obj = SimpleUploadedFile(
            "lifecycle.txt", b"File lifecycle test", content_type="text/plain"
        )

        upload_response = self.client.post(
            "/api/files/", {"file": file_obj}, format="multipart", HTTP_UserId=self.user_id
        )

        self.assertEqual(upload_response.status_code, status.HTTP_201_CREATED)
        file_id = upload_response.data["data"]["id"]

        # 2. List files
        list_response = self.client.get("/api/files/", HTTP_UserId=self.user_id)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data["count"], 1)

        # 3. Check storage stats
        stats_response = self.client.get("/api/files/storage_stats/", HTTP_UserId=self.user_id)
        self.assertEqual(stats_response.status_code, status.HTTP_200_OK)
        self.assertGreater(stats_response.data["total_storage_used"], 0)

        # 4. Delete file
        delete_response = self.client.delete(f"/api/files/{file_id}/", HTTP_UserId=self.user_id)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

        # 5. Verify file is gone
        final_list_response = self.client.get("/api/files/", HTTP_UserId=self.user_id)
        self.assertEqual(final_list_response.data["count"], 0)

    def test_multi_user_deduplication_workflow(self):
        """Test deduplication across multiple users."""
        file_content = b"Shared content"

        # User1 uploads file
        file1 = SimpleUploadedFile("shared.txt", file_content, content_type="text/plain")
        response1 = self.client.post(
            "/api/files/", {"file": file1}, format="multipart", HTTP_UserId=self.user_id
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response1.data["data"]["is_duplicate"])

        # User2 uploads same file
        file2 = SimpleUploadedFile("shared.txt", file_content, content_type="text/plain")
        response2 = self.client.post(
            "/api/files/", {"file": file2}, format="multipart", HTTP_UserId=self.other_user_id
        )
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response2.data["data"]["is_duplicate"])

        # Check deduplication stats
        dedup_response = self.client.get(
            "/api/files/deduplication_stats/", HTTP_UserId=self.user_id
        )
        self.assertEqual(dedup_response.status_code, status.HTTP_200_OK)
        self.assertEqual(dedup_response.data["total_files"], 2)
        self.assertEqual(dedup_response.data["original_files"], 1)
        self.assertEqual(dedup_response.data["reference_files"], 1)

        # User1 deletes their file (original file with references)
        file_id1 = response1.data["data"]["id"]
        delete_response = self.client.delete(f"/api/files/{file_id1}/", HTTP_UserId=self.user_id)
        # Should return 400 because original file has references
        self.assertEqual(delete_response.status_code, status.HTTP_400_BAD_REQUEST)

        # User2's file should still exist
        list_response = self.client.get("/api/files/", HTTP_UserId=self.other_user_id)
        self.assertEqual(list_response.data["count"], 1)

    def test_storage_quota_enforcement_workflow(self):
        """Test storage quota enforcement across multiple uploads."""
        with override_settings(STORAGE_QUOTA_PER_USER=100):  # 100 bytes limit
            # Upload small file
            small_file = SimpleUploadedFile("small.txt", b"Hi", content_type="text/plain")
            response1 = self.client.post(
                "/api/files/", {"file": small_file}, format="multipart", HTTP_UserId=self.user_id
            )
            self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

            # Try to upload large file
            large_file = SimpleUploadedFile("large.txt", b"X" * 200, content_type="text/plain")
            response2 = self.client.post(
                "/api/files/", {"file": large_file}, format="multipart", HTTP_UserId=self.user_id
            )
            self.assertEqual(response2.status_code, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

            # Delete small file
            file_id = response1.data["data"]["id"]
            delete_response = self.client.delete(f"/api/files/{file_id}/", HTTP_UserId=self.user_id)
            self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

            # Now large file should upload successfully
            response3 = self.client.post(
                "/api/files/", {"file": large_file}, format="multipart", HTTP_UserId=self.user_id
            )
            self.assertEqual(response3.status_code, status.HTTP_201_CREATED)

    def test_views_error_handling(self):
        """Test views error handling edge cases."""
        from unittest.mock import patch

        # Test file upload with service error
        with patch("files.views.DeduplicationService.handle_file_upload") as mock_service:
            mock_service.side_effect = Exception("Service error")

            file_obj = SimpleUploadedFile("test.txt", b"content", content_type="text/plain")

            response = self.client.post(
                "/api/files/", {"file": file_obj}, format="multipart", HTTP_UserId=self.user_id
            )

            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn("error", response.data)

    def test_storage_stats_error_handling(self):
        """Test storage stats error handling."""
        from unittest.mock import patch

        with patch("files.views.StorageService.get_storage_stats") as mock_service:
            mock_service.side_effect = Exception("Service error")

            response = self.client.get("/api/files/storage_stats/", HTTP_UserId=self.user_id)

            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn("error", response.data)

    def test_deduplication_stats_error_handling(self):
        """Test deduplication stats error handling."""
        from unittest.mock import patch

        with patch("files.views.DeduplicationService.get_deduplication_stats") as mock_service:
            mock_service.side_effect = Exception("Service error")

            response = self.client.get("/api/files/deduplication_stats/", HTTP_UserId=self.user_id)

            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn("error", response.data)

    def test_file_types_error_handling(self):
        """Test file types error handling."""
        from unittest.mock import patch

        with patch("files.views.File.objects.filter") as mock_filter:
            mock_filter.side_effect = Exception("Database error")

            response = self.client.get("/api/files/file_types/", HTTP_UserId=self.user_id)

            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn("error", response.data)
