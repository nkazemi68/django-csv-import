from django.db import models
from django.utils.translation import gettext_lazy as _


class Book(models.Model):
    """Represents a book entry imported from CSV.

    Stores essential book metadata, ensuring uniqueness on ISBN.
    Designed for high-volume imports with efficient querying.

    Attributes:
        title (str): The book's title (required, up to 512 characters).
        author (str | None): The book's author (optional).
        isbn (str): Unique International Standard Book Number (required).
        publication_year (int | None): Year of publication (optional).
        created_at (datetime.datetime): Timestamp when the record was created (auto-set).
    """
    title = models.CharField(max_length=512)
    author = models.CharField(max_length=256, blank=True, null=True)
    isbn = models.CharField(max_length=128, unique=True)  # Enforces uniqueness to prevent duplicates
    publication_year = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Meta options for query optimization and default ordering."""
        indexes = [
            # Index on ISBN for fast unique lookups during imports
            models.Index(fields=["isbn"], name="idx_book_isbn"),
            # Index on publication year for range queries (e.g., books by decade)
            models.Index(fields=["publication_year"], name="idx_book_pubyear"),
        ]
        ordering = ["-id"]  # Newest books first by default

    def __str__(self):
        """Human-readable representation of the book.

        Returns:
            str: Formatted string with title and ISBN.
        """
        return f"{self.title} ({self.isbn})"


class ImportTask(models.Model):
    """Tracks the lifecycle of a CSV import job.

        Used by Celery to monitor asynchronous processing. Stores status,
        progress counters, and error details in a JSON field for flexibility.

        Attributes:
            task_id (str): Unique Celery task identifier.
            status (str): Current processing state (PENDING, PROCESSING, etc.).
            errors (list[dict]): List of error dictionaries for failed rows.
            total (int | None): Total rows to process (set after initial CSV parse).
            processed (int): Number of rows handled so far.
            created_at (datetime.datetime): Timestamp when the task was queued.
            finished_at (datetime.datetime | None): Timestamp when processing completed.
        """
    class StatusChoices(models.TextChoices):
        """Choices for the task status field.

        Uses Django's TextChoices for type safety and translation support.
        """
        PENDING = 'PENDING', _('در انتظار')
        PROCESSING = 'PROCESSING', _('در حال اجرا')
        SUCCESS = 'SUCCESS', _('موفق')
        FAILURE = 'FAILURE', _('خطا')

    task_id = models.CharField(max_length=255, unique=True)  # Matches Celery's task_id for tracking
    status = models.CharField(max_length=20, choices=StatusChoices, default=StatusChoices.PENDING)
    errors = models.JSONField(default=list, blank=True)
    total = models.IntegerField(null=True, blank=True)
    processed = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Meta options for indexing."""
        indexes = [
            # Index on task_id for quick status lookups via API
            models.Index(fields=["task_id"], name="idx_task_id"),
        ]

    def __str__(self):
        """Human-readable representation of the import task.

        Returns:
            str: Formatted string with task ID and status.
        """
        return f"ImpotTask {self.task_id} - {self.status}"
