"""
Test cases for file filtering functionality.
"""

import tempfile

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
)
class FileFilterTestCase(APITestCase):
    """Test file filtering functionality."""

    def setUp(self):
        self.client = APIClient()
        self.user_id = "testuser123"

    def test_file_list_search(self):
        """Test file list search functionality."""
        # Upload files with different names
        file1 = SimpleUploadedFile("document.txt", b"Content 1", content_type="text/plain")
        file2 = SimpleUploadedFile("image.jpg", b"Content 2", content_type="image/jpeg")

        self.client.post(
            "/api/files/", {"file": file1}, format="multipart", HTTP_UserId=self.user_id
        )
        self.client.post(
            "/api/files/", {"file": file2}, format="multipart", HTTP_UserId=self.user_id
        )

        # Search for document
        response = self.client.get("/api/files/?search=document", HTTP_UserId=self.user_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["original_filename"], "document.txt")

    def test_file_list_filter_by_type(self):
        """Test file list filtering by file type."""
        # Upload files of different types
        file1 = SimpleUploadedFile("doc.txt", b"Content 1", content_type="text/plain")
        file2 = SimpleUploadedFile("img.jpg", b"Content 2", content_type="image/jpeg")

        self.client.post(
            "/api/files/", {"file": file1}, format="multipart", HTTP_UserId=self.user_id
        )
        self.client.post(
            "/api/files/", {"file": file2}, format="multipart", HTTP_UserId=self.user_id
        )

        # Filter by text/plain
        response = self.client.get("/api/files/?file_type=text/plain", HTTP_UserId=self.user_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["file_type"], "text/plain")

    def test_file_list_filter_by_size(self):
        """Test file list filtering by size."""
        # Upload files of different sizes
        small_file = SimpleUploadedFile("small.txt", b"Hi", content_type="text/plain")
        large_file = SimpleUploadedFile("large.txt", b"X" * 100, content_type="text/plain")

        self.client.post(
            "/api/files/", {"file": small_file}, format="multipart", HTTP_UserId=self.user_id
        )
        self.client.post(
            "/api/files/", {"file": large_file}, format="multipart", HTTP_UserId=self.user_id
        )

        # Filter by minimum size
        response = self.client.get("/api/files/?min_size=50", HTTP_UserId=self.user_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertGreaterEqual(response.data["results"][0]["size"], 50)

    def test_file_list_filter_by_date_start(self):
        """Test filtering by start (date__gte - date only, ignoring time)."""
        from datetime import timedelta

        from django.utils import timezone

        # Create three files with controlled timestamps
        f1 = SimpleUploadedFile("old.txt", b"A", content_type="text/plain")
        f2 = SimpleUploadedFile("mid.txt", b"BB", content_type="text/plain")
        f3 = SimpleUploadedFile("new.txt", b"CCC", content_type="text/plain")

        self.client.post("/api/files/", {"file": f1}, format="multipart", HTTP_UserId=self.user_id)
        self.client.post("/api/files/", {"file": f2}, format="multipart", HTTP_UserId=self.user_id)
        self.client.post("/api/files/", {"file": f3}, format="multipart", HTTP_UserId=self.user_id)

        # Adjust uploaded_at for deterministic filtering
        files = list(File.objects.filter(user_id=self.user_id).order_by("uploaded_at"))
        now = timezone.now()
        files[0].uploaded_at = now - timedelta(days=3)
        files[0].save(update_fields=["uploaded_at"])
        files[1].uploaded_at = now - timedelta(days=2)
        files[1].save(update_fields=["uploaded_at"])
        files[2].uploaded_at = now - timedelta(days=1)
        files[2].save(update_fields=["uploaded_at"])

        # Test with date only (date__gte ignores time)
        start_date = (now - timedelta(days=2)).date()
        start = start_date.strftime("%Y-%m-%d")
        response = self.client.get(f"/api/files/?start={start}", HTTP_UserId=self.user_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include files from day 2 and day 1 (last two)
        self.assertEqual(response.data["count"], 2)

    def test_file_list_filter_by_date_end(self):
        """Test filtering by end (date__lte - date only, ignoring time)."""
        from datetime import timedelta

        from django.utils import timezone

        files = list(File.objects.filter(user_id=self.user_id).order_by("uploaded_at"))
        if len(files) < 3:
            # seed if needed
            self.client.post(
                "/api/files/",
                {"file": SimpleUploadedFile("a.txt", b"A", content_type="text/plain")},
                format="multipart",
                HTTP_UserId=self.user_id,
            )
            self.client.post(
                "/api/files/",
                {"file": SimpleUploadedFile("b.txt", b"B", content_type="text/plain")},
                format="multipart",
                HTTP_UserId=self.user_id,
            )
            self.client.post(
                "/api/files/",
                {"file": SimpleUploadedFile("c.txt", b"C", content_type="text/plain")},
                format="multipart",
                HTTP_UserId=self.user_id,
            )
            files = list(File.objects.filter(user_id=self.user_id).order_by("uploaded_at"))

        now = timezone.now()
        files[0].uploaded_at = now - timedelta(days=3)
        files[0].save(update_fields=["uploaded_at"])
        files[1].uploaded_at = now - timedelta(days=2)
        files[1].save(update_fields=["uploaded_at"])
        files[2].uploaded_at = now - timedelta(days=1)
        files[2].save(update_fields=["uploaded_at"])

        # Test with date only (date__lte ignores time)
        end_date = (now - timedelta(days=1)).date()
        end = end_date.strftime("%Y-%m-%d")
        response = self.client.get(f"/api/files/?end={end}", HTTP_UserId=self.user_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include files from day 3, day 2, and day 1 (all three, since end is inclusive)
        self.assertEqual(response.data["count"], 3)

    def test_file_list_filter_by_date_start_end(self):
        """Test filtering by both start and end (date range - date only, ignoring time)."""
        from datetime import timedelta

        from django.utils import timezone

        files = list(File.objects.filter(user_id=self.user_id).order_by("uploaded_at"))
        if len(files) < 3:
            # seed if needed
            self.client.post(
                "/api/files/",
                {"file": SimpleUploadedFile("x.txt", b"X", content_type="text/plain")},
                format="multipart",
                HTTP_UserId=self.user_id,
            )
            self.client.post(
                "/api/files/",
                {"file": SimpleUploadedFile("y.txt", b"YY", content_type="text/plain")},
                format="multipart",
                HTTP_UserId=self.user_id,
            )
            self.client.post(
                "/api/files/",
                {"file": SimpleUploadedFile("z.txt", b"ZZZ", content_type="text/plain")},
                format="multipart",
                HTTP_UserId=self.user_id,
            )
            files = list(File.objects.filter(user_id=self.user_id).order_by("uploaded_at"))

        now = timezone.now()
        files[0].uploaded_at = now - timedelta(days=3)
        files[0].save(update_fields=["uploaded_at"])
        files[1].uploaded_at = now - timedelta(days=2)
        files[1].save(update_fields=["uploaded_at"])
        files[2].uploaded_at = now - timedelta(days=1)
        files[2].save(update_fields=["uploaded_at"])

        # Test with date range (date__gte and date__lte ignore time)
        start_date = (now - timedelta(days=2)).date()
        end_date = (now - timedelta(days=1)).date()
        start = start_date.strftime("%Y-%m-%d")
        end = end_date.strftime("%Y-%m-%d")
        response = self.client.get(f"/api/files/?start={start}&end={end}", HTTP_UserId=self.user_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include files from day 2 and day 1 (both inclusive)
        self.assertEqual(response.data["count"], 2)

    def test_file_list_filter_combination_all(self):
        """Test combination of all filters producing a single result."""
        # Seed diverse files (using smaller sizes to avoid quota issues)
        f_txt_small = SimpleUploadedFile("report.txt", b"P" * 50, content_type="text/plain")
        f_txt_large = SimpleUploadedFile("report_big.txt", b"P" * 200, content_type="text/plain")
        f_other = SimpleUploadedFile("notes.md", b"N" * 100, content_type="text/markdown")
        self.client.post(
            "/api/files/", {"file": f_txt_small}, format="multipart", HTTP_UserId=self.user_id
        )
        self.client.post(
            "/api/files/", {"file": f_txt_large}, format="multipart", HTTP_UserId=self.user_id
        )
        self.client.post(
            "/api/files/", {"file": f_other}, format="multipart", HTTP_UserId=self.user_id
        )

        # Apply filters to match only report_big.txt (200 bytes)
        query = "/api/files/?search=big&file_type=text/plain&min_size=150&max_size=250"
        response = self.client.get(query, HTTP_UserId=self.user_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["original_filename"], "report_big.txt")

    def test_file_list_filter_date_only_ignores_time(self):
        """Test that date filters work on date only, ignoring time component."""

        from django.utils import timezone

        # Create files on the same date but different times
        f1 = SimpleUploadedFile("morning.txt", b"Morning", content_type="text/plain")
        f2 = SimpleUploadedFile("afternoon.txt", b"Afternoon", content_type="text/plain")
        f3 = SimpleUploadedFile("evening.txt", b"Evening", content_type="text/plain")

        self.client.post("/api/files/", {"file": f1}, format="multipart", HTTP_UserId=self.user_id)
        self.client.post("/api/files/", {"file": f2}, format="multipart", HTTP_UserId=self.user_id)
        self.client.post("/api/files/", {"file": f3}, format="multipart", HTTP_UserId=self.user_id)

        # Set all files to the same date but different times
        files = list(File.objects.filter(user_id=self.user_id).order_by("uploaded_at"))
        target_date = timezone.now().date()

        files[0].uploaded_at = timezone.make_aware(
            timezone.datetime.combine(
                target_date, timezone.datetime.min.time().replace(hour=9)
            )  # 9 AM
        )
        files[0].save(update_fields=["uploaded_at"])

        files[1].uploaded_at = timezone.make_aware(
            timezone.datetime.combine(
                target_date, timezone.datetime.min.time().replace(hour=14)
            )  # 2 PM
        )
        files[1].save(update_fields=["uploaded_at"])

        files[2].uploaded_at = timezone.make_aware(
            timezone.datetime.combine(
                target_date, timezone.datetime.min.time().replace(hour=20)
            )  # 8 PM
        )
        files[2].save(update_fields=["uploaded_at"])

        # Filter by the target date - should get all 3 files regardless of time
        date_str = target_date.strftime("%Y-%m-%d")
        response = self.client.get(
            f"/api/files/?start={date_str}&end={date_str}", HTTP_UserId=self.user_id
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include all 3 files since they're all on the same date
        self.assertEqual(response.data["count"], 3)
