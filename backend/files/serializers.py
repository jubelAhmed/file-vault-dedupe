from rest_framework import serializers

from .models import File


class FileUploadSerializer(serializers.ModelSerializer):
    """Serializer for file uploads with deduplication support."""

    reference_count = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    is_duplicate = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = [
            "id",
            "file",
            "original_filename",
            "file_type",
            "size",
            "uploaded_at",
            "user_id",
            "file_hash",
            "reference_count",
            "is_reference",
            "original_file",
            "file_url",
            "is_duplicate",
        ]
        read_only_fields = [
            "id",
            "file_hash",
            "uploaded_at",
            "user_id",
            "is_reference",
            "original_file",
            "reference_count",
            "file_url",
            "is_duplicate",
        ]

    def get_reference_count(self, obj):
        """Get the number of references to this file."""
        return obj.reference_count

    def get_file_url(self, obj):
        """Get the URL to access the file."""
        actual_file = obj.get_actual_file()
        if actual_file:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(actual_file.url)
            return actual_file.url
        return None

    def get_is_duplicate(self, obj):
        """Check if this file is a duplicate (reference)."""
        return obj.is_reference


class FileListSerializer(serializers.ModelSerializer):
    """Simplified serializer for file listing."""

    file_url = serializers.SerializerMethodField()
    is_duplicate = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = [
            "id",
            "original_filename",
            "file_type",
            "size",
            "uploaded_at",
            "file_url",
            "is_duplicate",
        ]

    def get_file_url(self, obj):
        """Get the URL to access the file."""
        actual_file = obj.get_actual_file()
        if actual_file:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(actual_file.url)
            return actual_file.url
        return None

    def get_is_duplicate(self, obj):
        """Check if this file is a duplicate (reference)."""
        return obj.is_reference


class StorageStatsSerializer(serializers.Serializer):
    """Serializer for user storage statistics."""

    user_id = serializers.CharField()
    total_storage_used = serializers.IntegerField()
    original_storage_used = serializers.IntegerField()
    quota_limit = serializers.IntegerField()
    quota_remaining = serializers.IntegerField()
    quota_usage_percentage = serializers.FloatField()


class DeduplicationStatsSerializer(serializers.Serializer):
    """Serializer for deduplication statistics."""

    total_files = serializers.IntegerField()
    original_files = serializers.IntegerField()
    reference_files = serializers.IntegerField()
    deduplication_ratio = serializers.FloatField()
    total_original_storage = serializers.IntegerField()
    total_actual_storage = serializers.IntegerField()
    storage_savings = serializers.IntegerField()
    savings_percentage = serializers.FloatField()
