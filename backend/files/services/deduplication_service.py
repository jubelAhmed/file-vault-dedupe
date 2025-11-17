"""
Deduplication service for handling file deduplication across users.
"""

from django.db import transaction

from ..models import File
from .hash_service import HashService
from .storage_service import StorageService


class DeduplicationService:
    """Service for handling file deduplication logic."""

    @classmethod
    @transaction.atomic
    def handle_file_upload(cls, user_id, uploaded_file):
        """
        Handle file upload with deduplication logic.

        Args:
            user_id (str): User identifier
            uploaded_file: Django UploadedFile object

        Returns:
            File: Created File instance (either original or reference)
        """
        # Calculate file hash
        file_hash = HashService.calculate_sha256(uploaded_file)

        # Check for existing file with same hash (any user)
        existing_file = File.objects.filter(file_hash=file_hash, is_reference=False).first()

        if existing_file:
            # Create reference to existing file
            new_file = cls._create_file_reference(user_id, uploaded_file, file_hash, existing_file)
            # Update only original storage (no actual storage used)
            StorageService.update_storage(user_id, uploaded_file.size, original_only=True)
        else:
            # Create new original file
            new_file = cls._create_original_file(user_id, uploaded_file, file_hash)
            # Update both storage counters
            StorageService.update_storage(user_id, uploaded_file.size, original_only=False)

        return new_file

    @classmethod
    def _create_file_reference(cls, user_id, uploaded_file, file_hash, original_file):
        """
        Create a file reference pointing to an existing file.

        Args:
            user_id (str): User identifier
            uploaded_file: Django UploadedFile object
            file_hash (str): SHA-256 hash of the file
            original_file (File): Original file instance

        Returns:
            File: Created reference file instance
        """
        return File.objects.create(
            original_filename=uploaded_file.name,
            file_type=uploaded_file.content_type,
            size=uploaded_file.size,
            user_id=user_id,
            file_hash=file_hash,
            is_reference=True,
            original_file=original_file,
            # Do not set file for references; physical storage is tracked on the original file only
            file=None,
        )

    @classmethod
    def _create_original_file(cls, user_id, uploaded_file, file_hash):
        """
        Create a new original file (not a reference).

        Args:
            user_id (str): User identifier
            uploaded_file: Django UploadedFile object
            file_hash (str): SHA-256 hash of the file

        Returns:
            File: Created original file instance
        """
        return File.objects.create(
            file=uploaded_file,
            original_filename=uploaded_file.name,
            file_type=uploaded_file.content_type,
            size=uploaded_file.size,
            user_id=user_id,
            file_hash=file_hash,
            is_reference=False,
        )

    @classmethod
    @transaction.atomic
    def handle_file_deletion(cls, file_obj):
        """
        Handle file deletion with proper reference counting.

        Args:
            file_obj (File): File instance to delete

        Returns:
            bool: True if deletion was successful
        """
        if file_obj.is_reference:
            # Delete reference record only
            StorageService.update_storage(
                file_obj.user_id, file_obj.size, original_only=True, subtract=True
            )
            file_obj.delete()
            return True
        else:
            # Check if any references exist
            ref_count = file_obj.references.count()
            if ref_count == 0:
                # No references, safe to delete physical file
                if file_obj.file:
                    file_obj.file.delete()
                StorageService.update_storage(
                    file_obj.user_id, file_obj.size, original_only=False, subtract=True
                )
                file_obj.delete()
                return True
            else:
                # References exist, cannot delete physical file
                # This is a business logic decision - could implement
                # reference transfer or just prevent deletion
                raise ValueError(
                    f"Cannot delete file with {ref_count} references. "
                    "All references must be deleted first."
                )

    @classmethod
    def get_deduplication_stats(cls):
        """
        Get deduplication statistics across all files.

        Returns:
            dict: Deduplication statistics
        """
        from django.db.models import Sum

        total_files = File.objects.count()
        original_files = File.objects.filter(is_reference=False).count()
        reference_files = File.objects.filter(is_reference=True).count()

        # Total storage if there were NO deduplication (count every user's file)
        total_original_storage = File.objects.aggregate(total=Sum("size"))["total"] or 0

        # Actual storage on disk (only original, non-reference files occupy space)
        total_actual_storage = (
            File.objects.filter(is_reference=False).aggregate(total=Sum("size"))["total"] or 0
        )

        storage_savings = max(total_original_storage - total_actual_storage, 0)
        savings_percentage = (
            (storage_savings / total_original_storage * 100) if total_original_storage > 0 else 0
        )

        return {
            "total_files": total_files,
            "original_files": original_files,
            "reference_files": reference_files,
            "deduplication_ratio": reference_files / total_files if total_files > 0 else 0,
            "total_original_storage": total_original_storage,
            "total_actual_storage": total_actual_storage,
            "storage_savings": storage_savings,
            "savings_percentage": savings_percentage,
        }
