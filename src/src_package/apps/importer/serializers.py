"""
DRF serializers for CSV import API.

Handles:
- File upload validation.
- Paginated error reporting.
- Task status serialization with enriched metadata.

Custom pagination ensures large error lists (e.g., 10k+ rows)
are returned efficiently without overwhelming the response.
"""

from rest_framework import serializers
from .models import ImportTask
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class ImportUploadSerializer(serializers.Serializer):
    """Validate uploaded CSV file.

    Ensures a file is present and meets basic requirements.
    Additional validation (e.g., CSV format, headers) occurs in task.

    Attributes:
        file (FileField): The uploaded CSV file.
    """
    file = serializers.FileField(
        required=True,
        allow_empty_file=False,
        max_length=None,
        use_url=True
    )

    def validate_file(self, value):
        """Extra validation: file type and size.

        Args:
            value: UploadedFile instance.

        Returns:
            UploadedFile: Validated file.

        Raises:
            serializers.ValidationError: If not CSV or too large.
        """
        if not value.name.lower().endswith('.csv'):
            raise serializers.ValidationError("Only CSV files are allowed.")

        max_size = 100 * 1024 * 1024  # 100 MB
        if value.size > max_size:
            raise serializers.ValidationError(f"File too large. Max {max_size / (1024 * 1024)} MB.")

        return value


class ErrorsPagination(PageNumberPagination):
    """Custom paginator for import errors.

    Supports dynamic page size via query param.
    Returns rich metadata for frontend pagination controls.

    Attributes:
        page_size (int): Default errors per page.
        page_size_query_param (str): Query param to override size.
        max_page_size (int): Hard cap to prevent abuse.
    """
    page_size = 100
    page_size_query_param = 'error_page_size'
    max_page_size = 1000

    def get_paginated_response(self, data):
        """
        Build paginated response with full navigation info.

        Args:
            data: Serialized page of errors.

        Returns:
            Response: JSON with count, links, and results.
        """
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'page_size': int(self.request.query_params.get(self.page_size_query_param, self.page_size)),
            'current_page': self.page.number,
            'total_pages': self.page.paginator.num_pages,
            'results': data
        })


class ImportErrorSerializer(serializers.Serializer):
    """Serialize a single import error.

    Attributes:
        line (int | None): CSV line number (1-based, after header).
        message (str): Human-readable error description.
    """
    line = serializers.IntegerField(allow_null=True)
    message = serializers.CharField()


class ImportTaskSerializer(serializers.ModelSerializer):
    """Serialize ImportTask with paginated errors.

    - Sorts errors by line number.
    - Applies custom pagination.
    - Falls back to full list on pagination failure.

    Attributes:
        errors: Dynamic field with paginated or full error list.
    """
    errors = serializers.SerializerMethodField()

    class Meta:
        model = ImportTask
        fields = ["task_id", "status", "errors", "total", "processed", "created_at", "finished_at"]

    def get_errors(self, obj):
        """
        Return paginated or full list of errors.

        Args:
            obj (ImportTask): Task instance.

        Returns:
            dict | list: Paginated response or flat error list.
        """
        request = self.context.get('request')
        errors_list = obj.errors

        # Convert to objects for queryset-like pagination
        class ErrorObject:
            def __init__(self, line, message):
                self.line = line
                self.message = message

        # Sort by line number (handles None via 0)
        errors_list = sorted(errors_list, key=lambda x: x.get('line') or 0)

        queryset = [ErrorObject(item.get('line'), item.get('message')) for item in errors_list]

        paginator = ErrorsPagination()
        try:
            page = paginator.paginate_queryset(queryset, request)
        except Exception:
            # Fallback: return full list (non-paginated)
            serializer = ImportErrorSerializer(queryset, many=True)
            return serializer.data

        if page is not None:
            serializer = ImportErrorSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data).data

        serializer = ImportErrorSerializer(queryset, many=True)
        return serializer.data
