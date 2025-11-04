import json

from django.contrib import admin
from django.utils.html import escape
from .models import Book, ImportTask


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'author', 'isbn', 'publication_year']
    ordering = ['-id']


@admin.register(ImportTask)
class ImportTaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'task_id', 'status', 'total', 'processed', 'created_at', 'finished_at', 'errors_preview']
    ordering = ['-id']
    list_editable = ['status']

    def errors_preview(self, obj):
        errors = obj.errors or []
        if not errors:
            return "-"

        text = json.dumps(errors, ensure_ascii=False)
        preview = text[:200]
        if len(text) > 200:
            preview = preview + "..."
        return preview

    errors_preview.short_decription = "errors"