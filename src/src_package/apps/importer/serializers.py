from rest_framework import serializers
from .models import ImportTask
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class ImportUploadSerializer(serializers.Serializer):
    file = serializers.FileField()


class ErrorsPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'error_page_size'
    max_page_size = 1000

    def get_paginated_response(self, data):
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
    line = serializers.IntegerField(allow_null=True)
    message = serializers.CharField()


class ImportTaskSerializer(serializers.ModelSerializer):
    errors = serializers.SerializerMethodField()

    class Meta:
        model = ImportTask
        fields = ["task_id", "status", "errors", "total", "processed", "created_at", "finished_at"]

    def get_errors(self, obj):
        request = self.context.get('request')
        errors_list = obj.errors

        class ErrorObject:
            def __init__(self, line, message):
                self.line = line
                self.message = message

        errors_list = sorted(errors_list, key=lambda x: x.get('line') or 0)

        queryset = [ErrorObject(item.get('line'), item.get('message')) for item in errors_list]

        paginator = ErrorsPagination()
        try:
            page = paginator.paginate_queryset(queryset, request)
        except Exception:
            serializer = ImportErrorSerializer(queryset, many=True)
            return serializer.data

        if page is not None:
            serializer = ImportErrorSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data).data

        serializer = ImportErrorSerializer(queryset, many=True)
        return serializer.data