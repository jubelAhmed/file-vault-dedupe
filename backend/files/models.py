from django.db import models
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
