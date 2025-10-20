from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from rest_framework.exceptions import APIException


from .models import File
from .serializers import (
    FileUploadSerializer, 
    FileListSerializer, 
    StorageStatsSerializer,
    DeduplicationStatsSerializer
)
from .services.deduplication_service import DeduplicationService
from .services.storage_service import StorageService, StorageQuotaExceeded
from .utils.validators import FileValidator
from .filters import FileFilter


class FileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for file management with deduplication support.
    
    Provides CRUD operations for files with automatic deduplication,
    storage quota management, and user isolation.
    """
    
    queryset = File.objects.all()  # Required for DRF router
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = FileFilter
    ordering_fields = ['uploaded_at', 'size', 'original_filename']
    ordering = ['-uploaded_at']
    search_fields = ['original_filename', 'file_type', "size", "uploaded_at"]
    
    def get_queryset(self):
        """Filter files by user_id from middleware."""
        if hasattr(self.request, 'user_id'):
            return File.objects.filter(user_id=self.request.user_id).select_related('original_file')
        return File.objects.none()
    
    def get_object(self):
        """Override to handle 404 properly for user-isolated files."""
        try:
            return super().get_object()
        except Exception:
            from rest_framework.exceptions import NotFound
            raise NotFound("File not found")
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return FileListSerializer
        return FileUploadSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Upload a new file with deduplication support.
        
        Expected request format:
        - Multipart form data with 'file' field
        - UserId header (handled by middleware)
        """
        # Get file from request
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response(
                {'error': 'No file provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file
        try:
            FileValidator.validate_file(file_obj)
        except Exception as e:
            return Response(
                {'error': 'File validation failed', 'details': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check storage quota
        try:
            StorageService.check_storage_quota(request.user_id, file_obj.size)
        except StorageQuotaExceeded as e:
            return Response(
                {'error': 'Storage quota exceeded', 'details': str(e)}, 
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            )
        
        # Handle file upload with deduplication
        # TODO: Future enhancement - Move to background job processing (Celery/Django Background Tasks)
        # This will improve performance for large files and provide better user experience
        # with async processing and status tracking
        try:
            file_instance = DeduplicationService.handle_file_upload(
                request.user_id, file_obj
            )
            
            # Serialize response
            serializer = self.get_serializer(file_instance, context={'request': request})
            
            return Response(
                {
                    'message': 'File uploaded successfully',
                    'data': serializer.data
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response(
                {'error': 'File upload failed', 'details': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete a file with proper reference counting.
        """
        try:
            file_instance = self.get_object()
            DeduplicationService.handle_file_deletion(file_instance)
            
            return Response(
                {'message': 'File deleted successfully'}, 
                status=status.HTTP_204_NO_CONTENT
            )
            
        except ValueError as e:
            return Response(
                {'error': 'Cannot delete file', 'details': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            if isinstance(e, APIException):
                raise
            return Response(
                {'error': 'File deletion failed', 'details': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def storage_stats(self, request):
        """
        Get storage statistics for the current user.
        
        Returns:
            - Total storage used (with deduplication)
            - Original storage used (without deduplication)
            - Storage savings and percentage
            - Quota information
        """
        try:
            stats = StorageService.get_storage_stats(request.user_id)
            serializer = StorageStatsSerializer(stats)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': 'Failed to get storage stats', 'details': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def deduplication_stats(self, request):
        """
        Get system-wide deduplication statistics.
        
        Returns:
            - Total files, original files, reference files
            - Deduplication ratio
            - Storage savings across the system
        """
        try:
            stats = DeduplicationService.get_deduplication_stats()
            serializer = DeduplicationStatsSerializer(stats)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': 'Failed to get deduplication stats', 'details': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def file_types(self, request):
        """
        Get list of unique file types for the current user.
        
        Returns:
            List of unique MIME types used by the user
        """
        try:
            file_types = File.objects.filter(
                user_id=request.user_id
            ).values_list('file_type', flat=True).distinct()
            
            return Response({
                'file_types': list(file_types),
                'count': len(file_types)
            })
        except Exception as e:
            return Response(
                {'error': 'Failed to get file types', 'details': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Health check view
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Simple health check endpoint that doesn't require UserId header.
    """
    return Response({
        'status': 'healthy',
        'service': 'abnormal-file-hub',
        'version': '1.0.0'
    })