"""
Validators for file uploads and user input.
"""

import mimetypes
import os

from django.core.exceptions import ValidationError

# Try to import python-magic for content-based validation
try:
    import magic

    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False


class FileValidator:
    """Validators for file uploads."""

    # Maximum file size (10MB as per planning)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes

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

    # Allowed file types (allow-list approach for security)
    # Only these extensions are permitted - everything else is rejected by default
    ALLOWED_EXTENSIONS = {
        "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".ico", ".svg"],
        "document": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt"],
        "spreadsheet": [".xls", ".xlsx", ".csv", ".ods"],
        "presentation": [".ppt", ".pptx", ".odp"],
        "archive": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
        "video": [".mp4", ".avi", ".mov", ".wmv", ".flv", ".mkv", ".webm"],
        "audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"],
        "data": [".json", ".xml", ".yaml", ".yml"],
        "code": [".md", ".log"],
    }

    # MIME type mappings for content validation
    # Maps file extensions to their expected MIME types
    EXPECTED_MIME_TYPES = {
        # Images
        ".jpg": ["image/jpeg"],
        ".jpeg": ["image/jpeg"],
        ".png": ["image/png"],
        ".gif": ["image/gif"],
        ".bmp": ["image/bmp", "image/x-ms-bmp"],
        ".webp": ["image/webp"],
        ".ico": ["image/x-icon", "image/vnd.microsoft.icon"],
        ".svg": ["image/svg+xml"],
        # Documents
        ".pdf": ["application/pdf"],
        ".doc": ["application/msword"],
        ".docx": ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
        ".txt": ["text/plain"],
        ".rtf": ["application/rtf", "text/rtf"],
        ".odt": ["application/vnd.oasis.opendocument.text"],
        # Spreadsheets
        ".xls": ["application/vnd.ms-excel"],
        ".xlsx": ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"],
        ".csv": ["text/csv", "text/plain", "application/csv"],
        ".ods": ["application/vnd.oasis.opendocument.spreadsheet"],
        # Presentations
        ".ppt": ["application/vnd.ms-powerpoint"],
        ".pptx": ["application/vnd.openxmlformats-officedocument.presentationml.presentation"],
        ".odp": ["application/vnd.oasis.opendocument.presentation"],
        # Archives
        ".zip": ["application/zip", "application/x-zip-compressed"],
        ".rar": ["application/x-rar-compressed", "application/vnd.rar"],
        ".7z": ["application/x-7z-compressed"],
        ".tar": ["application/x-tar"],
        ".gz": ["application/gzip", "application/x-gzip"],
        ".bz2": ["application/x-bzip2"],
        # Video
        ".mp4": ["video/mp4"],
        ".avi": ["video/x-msvideo"],
        ".mov": ["video/quicktime"],
        ".wmv": ["video/x-ms-wmv"],
        ".flv": ["video/x-flv"],
        ".mkv": ["video/x-matroska"],
        ".webm": ["video/webm"],
        # Audio
        ".mp3": ["audio/mpeg"],
        ".wav": ["audio/wav", "audio/x-wav"],
        ".flac": ["audio/flac"],
        ".aac": ["audio/aac"],
        ".ogg": ["audio/ogg"],
        ".m4a": ["audio/mp4", "audio/x-m4a"],
        # Data
        ".json": ["application/json", "text/plain"],
        ".xml": ["application/xml", "text/xml"],
        ".yaml": ["text/yaml", "text/x-yaml", "application/x-yaml", "text/plain"],
        ".yml": ["text/yaml", "text/x-yaml", "application/x-yaml", "text/plain"],
        # Code
        ".md": ["text/markdown", "text/plain"],
        ".log": ["text/plain"],
    }

    @classmethod
    def validate_file_size(cls, file_obj):
        """
        Validate file size against maximum allowed size.

        Args:
            file_obj: Django UploadedFile object

        Raises:
            ValidationError: If file size exceeds limit
        """
        if file_obj.size > cls.MAX_FILE_SIZE:
            file_size_formatted = cls.format_file_size(file_obj.size)
            max_size_formatted = cls.format_file_size(cls.MAX_FILE_SIZE)
            raise ValidationError(
                f"File size ({file_size_formatted}) exceeds maximum allowed size "
                f"({max_size_formatted})"
            )

    @classmethod
    def validate_file_extension(cls, filename):
        """
        Validate file extension against allowed list (allow-list approach).

        Uses an allow-list security model: only explicitly allowed extensions
        are permitted. Everything else is rejected by default.

        Args:
            filename (str): Name of the file

        Raises:
            ValidationError: If file extension is not in the allowed list
        """
        _, ext = os.path.splitext(filename.lower())

        # Build set of all allowed extensions
        allowed_extensions = set()
        for category_extensions in cls.ALLOWED_EXTENSIONS.values():
            allowed_extensions.update(category_extensions)

        # Reject if not in allow-list
        if ext not in allowed_extensions:
            raise ValidationError(
                f"File extension '{ext}' is not supported. "
                f"Allowed extensions: {', '.join(sorted(allowed_extensions))}"
            )

    @classmethod
    def validate_file_content(cls, file_obj):
        """
        Validate file content matches its extension (detect file type spoofing).

        This prevents attacks where malicious files are renamed with safe extensions
        (e.g., malware.exe renamed to malware.png).

        Uses multiple detection methods:
        1. python-magic (libmagic) - reads file signature/magic numbers
        2. Django's content_type from upload
        3. Fallback to extension-based validation

        Args:
            file_obj: Django UploadedFile object

        Raises:
            ValidationError: If file content doesn't match its extension
        """
        # Skip validation for empty files
        if file_obj.size == 0:
            return

        _, ext = os.path.splitext(file_obj.name.lower())

        # Get expected MIME types for this extension
        expected_mimes = cls.EXPECTED_MIME_TYPES.get(ext, [])

        if not expected_mimes:
            # No MIME validation defined for this extension, skip content check
            return

        detected_mime = None

        # Method 1: Use python-magic if available (most reliable)
        if MAGIC_AVAILABLE:
            try:
                # Read first 2048 bytes for magic number detection
                file_obj.seek(0)
                file_start = file_obj.read(2048)
                file_obj.seek(0)  # Reset to start

                # Detect MIME type from content
                detected_mime = magic.from_buffer(file_start, mime=True)

            except Exception:
                # If magic fails, fall through to other methods
                pass

        # Method 2: Use Django's content_type from upload (less reliable)
        if not detected_mime and hasattr(file_obj, "content_type"):
            detected_mime = file_obj.content_type

        # Method 3: Fallback to mimetypes library (least reliable)
        if not detected_mime:
            detected_mime, _ = mimetypes.guess_type(file_obj.name)

        # Validate detected MIME type
        if detected_mime:
            # Normalize MIME type (remove parameters like charset)
            detected_mime = detected_mime.split(";")[0].strip().lower()

            # Check if detected MIME matches expected MIME types
            if detected_mime not in expected_mimes:
                raise ValidationError(
                    f"File content type mismatch: '{file_obj.name}' appears to be "
                    f"'{detected_mime}' but has extension '{ext}'. "
                    f"Expected types: {', '.join(expected_mimes)}. "
                    f"This may indicate a malicious file."
                )

    @classmethod
    def validate_filename(cls, filename):
        """
        Validate filename for security and compatibility.

        Args:
            filename (str): Name of the file

        Raises:
            ValidationError: If filename is invalid
        """
        if not filename or not filename.strip():
            raise ValidationError("Filename cannot be empty")

        # Check for path traversal attempts
        if ".." in filename or "/" in filename or "\\" in filename:
            raise ValidationError("Filename contains invalid characters")

        # Check filename length
        if len(filename) > 255:
            raise ValidationError("Filename is too long (maximum 255 characters)")

        # Check for reserved names (Windows)
        reserved_names = {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        }

        name_without_ext = os.path.splitext(filename)[0].upper()
        if name_without_ext in reserved_names:
            raise ValidationError(f"Filename '{filename}' is reserved and not allowed")

    @classmethod
    def validate_file(cls, file_obj):
        """
        Comprehensive file validation with content verification.

        Performs multiple security checks:
        1. File size validation
        2. Filename validation (path traversal, reserved names)
        3. Extension validation (allow-list)
        4. Content validation (prevents file type spoofing)

        Args:
            file_obj: Django UploadedFile object

        Raises:
            ValidationError: If file fails any validation
        """
        cls.validate_file_size(file_obj)
        cls.validate_filename(file_obj.name)
        cls.validate_file_extension(file_obj.name)
        cls.validate_file_content(file_obj)  # Content-based validation
