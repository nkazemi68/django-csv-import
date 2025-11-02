from django.db import models
from django.utils.translation import gettext_lazy as _


class Book(models.Model):
    title = models.CharField(max_length=512)
    author = models.CharField(max_length=256, blank=True, null=True)
    isbn = models.CharField(max_length=128, unique=True)
    publication_year = models.IntegerField(null=True, blank=True)
    created_at = models. DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["isbn"], name="idx_book_isbn"),
            models.Index(fields=["publication_year"], name="idx_book_pubyear"),
        ]
        ordering = ["-id"]

    def __str__(self):
        return f"{self.title} ({self.isbn})"


class ImportTask(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', _('در انتظار')
        PROCESSING = 'PROCESSING', _('در حال اجرا')
        SUCCESS = 'SUCCESS', _('موفق')
        FAILURE = 'FAILURE', _('خطا')

    task_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, choices=StatusChoices, default=StatusChoices.PENDING)
    errors = models.JSONField(default=list, blank=True)
    total = models.IntegerField(null=True, blank=True)
    processed = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["task_id"], name="idx_task_id"),
        ]

    def __str__(self):
        return f"ImpotTask {self.task_id} - {self.status}"