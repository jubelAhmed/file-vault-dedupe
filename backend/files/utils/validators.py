"""
Validators for file uploads and user input.
"""
import os
from django.core.exceptions import ValidationError


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
    
    # Allowed file types (can be expanded)
    ALLOWED_EXTENSIONS = {
        'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
        'document': ['.pdf', '.doc', '.docx', '.txt', '.rtf'],
        'spreadsheet': ['.xls', '.xlsx', '.csv'],
        'presentation': ['.ppt', '.pptx'],
        'archive': ['.zip', '.rar', '.7z', '.tar', '.gz'],
        'video': ['.mp4', '.avi', '.mov', '.wmv', '.flv'],
        'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg'],
    }
    
    # Dangerous file types to block
    BLOCKED_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js',
        '.jar', '.app', '.deb', '.rpm', '.msi', '.dmg'
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
        Validate file extension against allowed and blocked lists.
        
        Args:
            filename (str): Name of the file
            
        Raises:
            ValidationError: If file extension is not allowed or is blocked
        """
        _, ext = os.path.splitext(filename.lower())
        
        if ext in cls.BLOCKED_EXTENSIONS:
            raise ValidationError(
                f"File extension '{ext}' is not allowed for security reasons"
            )
        
        # Check if extension is in any allowed category
        allowed_extensions = set()
        for category_extensions in cls.ALLOWED_EXTENSIONS.values():
            allowed_extensions.update(category_extensions)
        
        if ext not in allowed_extensions:
            raise ValidationError(
                f"File extension '{ext}' is not supported. "
                f"Allowed extensions: {', '.join(sorted(allowed_extensions))}"
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
        if '..' in filename or '/' in filename or '\\' in filename:
            raise ValidationError("Filename contains invalid characters")
        
        # Check filename length
        if len(filename) > 255:
            raise ValidationError("Filename is too long (maximum 255 characters)")
        
        # Check for reserved names (Windows)
        reserved_names = {
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        }
        
        name_without_ext = os.path.splitext(filename)[0].upper()
        if name_without_ext in reserved_names:
            raise ValidationError(f"Filename '{filename}' is reserved and not allowed")
    
    @classmethod
    def validate_file(cls, file_obj):
        """
        Comprehensive file validation.
        
        Args:
            file_obj: Django UploadedFile object
            
        Raises:
            ValidationError: If file fails any validation
        """
        cls.validate_file_size(file_obj)
        cls.validate_filename(file_obj.name)
        cls.validate_file_extension(file_obj.name)
