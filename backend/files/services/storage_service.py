"""
Storage service for managing user storage quotas and tracking storage usage.
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction

from ..models import UserStorage


class StorageQuotaExceeded(ValidationError):
    """Exception raised when storage quota is exceeded."""

    pass


class StorageService:
    """Service for managing user storage quotas and usage tracking."""

    @classmethod
    def get_storage_limit(cls):
        """Get storage limit from Django settings."""
        return getattr(settings, "STORAGE_QUOTA_PER_USER", 10485760)  # 10MB default

    @classmethod
    def format_file_size(cls, size_bytes):
        """
        Convert file size from bytes to human-readable format.

        Args:
            size_bytes (int): File size in bytes

        Returns:
            str: Formatted file size (e.g., "1.5 MB", "500 KB")
        """
        if size_bytes == 0:
            return "0 Bytes"

        size_names = ["Bytes", "KB", "MB", "GB", "TB"]
        import math

        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"

    @classmethod
    def check_storage_quota(cls, user_id, file_size):
        """
        Check if user has enough storage quota for the file.

        Args:
            user_id (str): User identifier
            file_size (int): Size of file to be uploaded in bytes

        Returns:
            bool: True if quota allows the upload

        Raises:
            StorageQuotaExceeded: If quota would be exceeded
        """
        storage, _ = UserStorage.objects.get_or_create(user_id=user_id)

        storage_limit = cls.get_storage_limit()
        if storage.original_storage_used + file_size > storage_limit:
            current_usage_formatted = cls.format_file_size(storage.original_storage_used)
            limit_formatted = cls.format_file_size(storage_limit)
            file_size_formatted = cls.format_file_size(file_size)
            raise StorageQuotaExceeded(
                f"Storage quota exceeded. Current usage: {current_usage_formatted}, "
                f"Limit: {limit_formatted}, File size: {file_size_formatted}"
            )

        return True

    @classmethod
    @transaction.atomic
    def update_storage(cls, user_id, size, original_only=False, subtract=False):
        """
        Atomically update user storage usage.

        Args:
            user_id (str): User identifier
            size (int): File size in bytes
            original_only (bool): If True, only update original_storage_used
            subtract (bool): If True, subtract from storage instead of adding
        """
        storage, _ = UserStorage.objects.select_for_update().get_or_create(user_id=user_id)

        multiplier = -1 if subtract else 1
        size_change = size * multiplier

        # Always update original storage (before deduplication)
        storage.original_storage_used += size_change

        # Only update total storage if not a reference (actual file storage)
        if not original_only:
            storage.total_storage_used += size_change

        storage.save()

    @classmethod
    def get_storage_stats(cls, user_id):
        """
        Get storage statistics for a user.

        Args:
            user_id (str): User identifier

        Returns:
            dict: Storage statistics including usage and savings
        """
        storage, _ = UserStorage.objects.get_or_create(user_id=user_id)

        return {
            "user_id": user_id,
            "total_storage_used": storage.total_storage_used,
            "original_storage_used": storage.original_storage_used,
            "quota_limit": cls.get_storage_limit(),
            "quota_remaining": cls.get_storage_limit() - storage.original_storage_used,
            "quota_usage_percentage": (storage.original_storage_used / cls.get_storage_limit())
            * 100,
        }

    @classmethod
    def get_all_storage_stats(cls):
        """
        Get storage statistics for all users.

        Returns:
            list: List of storage statistics for all users
        """
        storages = UserStorage.objects.all()
        return [cls.get_storage_stats(storage.user_id) for storage in storages]
