"""
Hash service for calculating file hashes with memory-efficient chunked processing.
"""

import hashlib


class HashService:
    """Service for calculating file hashes using SHA-256 algorithm."""

    CHUNK_SIZE = 8192  # 8KB chunks for memory efficiency

    @classmethod
    def calculate_sha256(cls, file_obj):
        """
        Calculate SHA-256 hash of a file using chunked processing.

        Args:
            file_obj: Django UploadedFile or file-like object

        Returns:
            str: Hexadecimal representation of SHA-256 hash

        Note:
            Resets file pointer to beginning after calculation
        """
        hasher = hashlib.sha256()

        # Process file in chunks to avoid memory issues with large files
        for chunk in file_obj.chunks(chunk_size=cls.CHUNK_SIZE):
            hasher.update(chunk)

        # Reset file pointer to beginning for potential reuse
        file_obj.seek(0)

        return hasher.hexdigest()

    @classmethod
    def calculate_sha256_from_path(cls, file_path):
        """
        Calculate SHA-256 hash from file path.

        Args:
            file_path: Path to the file

        Returns:
            str: Hexadecimal representation of SHA-256 hash
        """
        hasher = hashlib.sha256()

        with open(file_path, "rb") as f:
            while chunk := f.read(cls.CHUNK_SIZE):
                hasher.update(chunk)

        return hasher.hexdigest()
