"""
Test cases for File and UserStorage models.
"""

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from ..models import File, UserStorage


class FileModelTestCase(TestCase):
    """Test File model functionality."""

    def setUp(self):
        self.user_id = "testuser123"
        self.test_file = SimpleUploadedFile("test.txt", b"Hello World", content_type="text/plain")

    def test_file_creation(self):
        """Test basic file creation."""
        file_obj = File.objects.create(
            file=self.test_file,
            original_filename="test.txt",
            file_type="text/plain",
            size=11,
            user_id=self.user_id,
            file_hash="test_hash_123",
        )

        self.assertEqual(file_obj.original_filename, "test.txt")
        self.assertEqual(file_obj.user_id, self.user_id)
        self.assertFalse(file_obj.is_reference)
        self.assertIsNone(file_obj.original_file)

    def test_file_reference_creation(self):
        """Test file reference creation."""
        original_file = File.objects.create(
            file=self.test_file,
            original_filename="original.txt",
            file_type="text/plain",
            size=11,
            user_id="user1",
            file_hash="test_hash_123",
        )

        reference_file = File.objects.create(
            original_filename="reference.txt",
            file_type="text/plain",
            size=11,
            user_id="user2",
            file_hash="test_hash_123",
            is_reference=True,
            original_file=original_file,
        )

        self.assertTrue(reference_file.is_reference)
        self.assertEqual(reference_file.original_file, original_file)
        self.assertEqual(reference_file.reference_count, 1)

    def test_reference_count_property(self):
        """Test reference count calculation."""
        original_file = File.objects.create(
            file=self.test_file,
            original_filename="original.txt",
            file_type="text/plain",
            size=11,
            user_id="user1",
            file_hash="test_hash_123",
        )

        # Create references
        File.objects.create(
            original_filename="ref1.txt",
            file_type="text/plain",
            size=11,
            user_id="user2",
            file_hash="test_hash_123",
            is_reference=True,
            original_file=original_file,
        )

        File.objects.create(
            original_filename="ref2.txt",
            file_type="text/plain",
            size=11,
            user_id="user3",
            file_hash="test_hash_123",
            is_reference=True,
            original_file=original_file,
        )

        self.assertEqual(original_file.reference_count, 2)

    def test_get_actual_file_method(self):
        """Test get_actual_file method for references."""
        original_file = File.objects.create(
            file=self.test_file,
            original_filename="original.txt",
            file_type="text/plain",
            size=11,
            user_id="user1",
            file_hash="test_hash_123",
        )

        reference_file = File.objects.create(
            original_filename="reference.txt",
            file_type="text/plain",
            size=11,
            user_id="user2",
            file_hash="test_hash_123",
            is_reference=True,
            original_file=original_file,
        )

        self.assertEqual(reference_file.get_actual_file(), original_file.file)
        self.assertEqual(original_file.get_actual_file(), original_file.file)

    def test_model_string_representations(self):
        """Test string representation methods for models."""
        # Test File model __str__ method
        file_obj = File.objects.create(
            original_filename="test.txt",
            file_type="text/plain",
            size=100,
            user_id=self.user_id,
            file_hash="test_hash",
        )
        self.assertEqual(str(file_obj), f"test.txt ({self.user_id})")

        # Test UserStorage model __str__ method
        storage = UserStorage.objects.create(user_id=self.user_id, total_storage_used=1024)
        self.assertEqual(str(storage), f"{self.user_id}: 1024 bytes")

    def test_serializer_file_url_fallback(self):
        """Test serializer file URL fallback when no request context."""
        from ..serializers import FileListSerializer

        file_obj = File.objects.create(
            original_filename="test.txt",
            file_type="text/plain",
            size=100,
            user_id=self.user_id,
            file_hash="test_hash",
        )

        # Test without request context
        serializer = FileListSerializer(file_obj)
        self.assertIsNone(serializer.get_file_url(file_obj))

    def test_serializer_file_url_with_reference(self):
        """Test serializer file URL for reference files."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        from ..serializers import FileListSerializer

        # Create test file
        test_file = SimpleUploadedFile("original.txt", b"Hello", content_type="text/plain")

        # Create original file
        original_file = File.objects.create(
            file=test_file,
            original_filename="original.txt",
            file_type="text/plain",
            size=5,
            user_id="user1",
            file_hash="test_hash_123",
        )

        # Create reference file
        reference_file = File.objects.create(
            original_filename="reference.txt",
            file_type="text/plain",
            size=5,
            user_id="user2",
            file_hash="test_hash_123",
            is_reference=True,
            original_file=original_file,
        )

        # Test serializer for reference file
        serializer = FileListSerializer(reference_file)
        # Should return the URL of the original file, not None
        self.assertIsNotNone(serializer.get_file_url(reference_file))

        # Test serializer for original file
        serializer_original = FileListSerializer(original_file)
        self.assertIsNotNone(serializer_original.get_file_url(original_file))


class UserStorageModelTestCase(TestCase):
    """Test UserStorage model functionality."""

    def setUp(self):
        self.user_id = "testuser123"

    def test_user_storage_creation(self):
        """Test UserStorage creation."""
        storage = UserStorage.objects.create(
            user_id=self.user_id, total_storage_used=1024, original_storage_used=2048
        )

        self.assertEqual(storage.user_id, self.user_id)
        self.assertEqual(storage.total_storage_used, 1024)
        self.assertEqual(storage.original_storage_used, 2048)

    def test_storage_savings_property(self):
        """Test storage savings calculation."""
        storage = UserStorage.objects.create(
            user_id=self.user_id, total_storage_used=1024, original_storage_used=2048
        )

        self.assertEqual(storage.storage_savings, 1024)

    def test_savings_percentage_property(self):
        """Test savings percentage calculation."""
        storage = UserStorage.objects.create(
            user_id=self.user_id, total_storage_used=1024, original_storage_used=2048
        )

        self.assertEqual(storage.savings_percentage, 50.0)

    def test_savings_percentage_zero_original(self):
        """Test savings percentage when original storage is zero."""
        storage = UserStorage.objects.create(
            user_id=self.user_id, total_storage_used=0, original_storage_used=0
        )

        self.assertEqual(storage.savings_percentage, 0.0)
