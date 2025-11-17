from django.db import models
from django.core.exceptions import ValidationError
import uuid
import os

def file_upload_path(instance, filename):
    """Generate file path for new file upload with UUID-based naming"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('uploads', filename)

class File(models.Model):
    """
    Stores file metadata and handles deduplication through references.
    Supports cross-user deduplication while maintaining user isolation.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # File storage
    file = models.FileField(upload_to=file_upload_path, null=True, blank=True)
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100)  # MIME type
    size = models.BigIntegerField()  # File size in bytes
    
    # User tracking
    user_id = models.CharField(max_length=255)
    
    # Deduplication fields
    file_hash = models.CharField(max_length=64)  # SHA-256
    is_reference = models.BooleanField(default=False)
    original_file = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.CASCADE,
        related_name='references'
    )
    
    # Metadata
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'file_uploads'
        ordering = ['-uploaded_at']
        indexes = [
            # User-based queries (most common)
            models.Index(fields=['user_id', 'uploaded_at'], name='idx_user_uploaded'),
            models.Index(fields=['user_id', 'file_type'], name='idx_user_filetype'),
            models.Index(fields=['user_id', 'size'], name='idx_user_size'),
            models.Index(fields=['user_id', 'original_filename'], name='idx_user_filename'),
            
            # Deduplication (critical - every upload)
            models.Index(fields=['file_hash', 'is_reference'], name='idx_hash_ref'),
            
            # Statistics queries
            models.Index(fields=['is_reference'], name='idx_is_reference'),
        ]
    
    def __str__(self):
        return f"{self.original_filename} ({self.user_id})"
    
    @property
    def reference_count(self):
        """Get the number of references to this file"""
        if self.is_reference:
            return self.original_file.references.count() if self.original_file else 0
        return self.references.count()
    
    def get_actual_file(self):
        """Get the actual file object, handling references"""
        if self.is_reference and self.original_file:
            return self.original_file.file
        return self.file


class UserStorage(models.Model):
    """
    Tracks storage usage per user for quota enforcement.
    Maintains both actual storage used and original storage (before deduplication).
    """
    user_id = models.CharField(max_length=255, unique=True, primary_key=True)
    total_storage_used = models.BigIntegerField(default=0)  # Actual bytes used (with deduplication)
    original_storage_used = models.BigIntegerField(default=0)  # Without deduplication
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_storage'
        verbose_name = 'User Storage'
        verbose_name_plural = 'User Storage Records'
    
    def __str__(self):
        return f"{self.user_id}: {self.total_storage_used} bytes"
    
    @property
    def storage_savings(self):
        """Calculate storage savings from deduplication"""
        return self.original_storage_used - self.total_storage_used
    
    @property
    def savings_percentage(self):
        """Calculate percentage of storage saved"""
        if self.original_storage_used == 0:
            return 0.0
        return (self.storage_savings / self.original_storage_used) * 100


class FileSearchIndex(models.Model):
    """
    Index for finding files based on keywords extracted from file content.
    
    This model enables content-based file search by storing keywords extracted
    from file content (PDF, DOCX, TXT, etc.) and maintaining relationships to
    files that contain those keywords.
    
    Usage:
        - Keywords are extracted from file content during upload
        - Search by keyword to find all files containing that keyword
        - Supports user-filtered search results
    """
    keyword = models.CharField(max_length=255, unique=True, db_index=True)
    files = models.ManyToManyField(
        'File',
        related_name='search_keywords',
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'file_search_index'
        verbose_name = 'File Search Index'
        verbose_name_plural = 'File Search Indexes'
        ordering = ['keyword']
        indexes = [
            models.Index(fields=['keyword'], name='idx_search_keyword'),
        ]
    
    def __str__(self):
        return f"{self.keyword} ({self.files.count()} files)"
    
    def clean(self):
        """Normalize keyword before saving"""
        if self.keyword:
            self.keyword = self.keyword.lower().strip()
            if not self.keyword:
                raise ValidationError({'keyword': 'Keyword cannot be empty'})
    
    def save(self, *args, **kwargs):
        """Override save to ensure keyword is normalized"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def file_count(self):
        """Get the number of files associated with this keyword"""
        return self.files.count()
    
    def get_files_for_user(self, user_id):
        """
        Get files containing this keyword, filtered by user_id.
        
        This method finds all files that contain the keyword in their content,
        restricted to files belonging to the specified user.
        
        Args:
            user_id: User ID to filter files by
            
        Returns:
            QuerySet of File instances containing this keyword for the user
        """
        return self.files.filter(user_id=user_id)
    
    @classmethod
    def find_files_by_keyword(cls, keyword, user_id=None):
        """
        Find files that contain the given keyword in their content.
        
        This is the main method for content-based file search. It looks up
        files based on keywords extracted from their content.
        
        Args:
            keyword: Keyword to search for (will be normalized to lowercase)
            user_id: Optional user ID to filter results by user
            
        Returns:
            QuerySet of File instances containing the keyword
        """
        keyword = keyword.lower().strip()
        if not keyword:
            return File.objects.none()
        
        try:
            search_index = cls.objects.filter(keyword=keyword).first()
            if not search_index:
                return File.objects.none()
            
            files = search_index.files.all()
            if user_id:
                files = files.filter(user_id=user_id)
            
            return files
        except Exception:
            return File.objects.none()
    
    def is_orphaned(self):
        """
        Check if this keyword has no associated files (orphaned).
        
        Returns:
            bool: True if keyword has no files, False otherwise
        """
        return self.files.count() == 0
