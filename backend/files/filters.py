"""
Filters for file management API.
"""

import django_filters

from .models import File


class FileFilter(django_filters.FilterSet):
    """
    Filter for file queries with comprehensive search and filtering options.

    Provides filtering by:
    - search: filename (case-insensitive)
    - file_type: MIME type (e.g., application/pdf)
    - min_size, max_size: file size in bytes
    - start, end: upload datetime (ISO 8601)
    """

    search = django_filters.CharFilter(
        field_name="original_filename",
        lookup_expr="icontains",
        help_text="Search in filename (case-insensitive)",
    )

    file_type = django_filters.CharFilter(
        field_name="file_type",
        lookup_expr="icontains",
        help_text="Filter by file type (MIME type, partial match)",
    )

    min_size = django_filters.NumberFilter(
        field_name="size", lookup_expr="gte", help_text="Minimum file size in bytes"
    )

    max_size = django_filters.NumberFilter(
        field_name="size", lookup_expr="lte", help_text="Maximum file size in bytes"
    )

    # Date range filters (renamed to start/end)
    start = django_filters.DateTimeFilter(
        field_name="uploaded_at",
        lookup_expr="date__gte",
        help_text="Filter files uploaded after this date (ISO format)",
    )

    end = django_filters.DateTimeFilter(
        field_name="uploaded_at",
        lookup_expr="date__lte",
        help_text="Filter files uploaded before this date (ISO format)",
    )

    class Meta:
        model = File
        fields = ["search", "file_type", "min_size", "max_size", "start", "end"]
