"""
Celery tasks for asynchronous CSV import processing.

This module defines a single shared task `process_csv` that:
- Reads a CSV file in batches.
- Delegates row processing to `ImportService`.
- Updates `ImportTask` model for progress tracking and UI feedback.
- Handles file access, errors, and logging in a worker environment.

The task is queued on 'import' for dedicated workers and supports
large files via streaming and batching.
"""

import csv
import logging
import os

from celery import shared_task
from django.utils import timezone

from .models import ImportTask
from .services.import_csv_service import ImportService

logger = logging.getLogger(__name__)


@shared_task(queue='import', bind=True)
def process_csv(self, file_path, import_task_id=None, batch_size=1000):
    """Asynchronously process a CSV file and import book records.

    Steps:
    1. Resolve and validate file path in worker filesystem.
    2. Link to ImportTask via ID or Celery task_id.
    3. Stream CSV, normalize rows, and process in batches.
    4. Update task status, counters, and errors.
    5. Return summary for potential API response.

    Args:
        self: Celery task instance (bound).
        file_path (str): Absolute path to CSV file on worker.
        import_task_id (int | None): Optional DB ID of ImportTask.
        batch_size (int): Rows per service call (tunable).

    Returns:
        Dict: Summary with created count and error list.
    """
    file_path = os.path.abspath(file_path)
    logger.info("Task started. checking file_path: %s", file_path)
    logger.info("Worker sees dir listing: %s", os.listdir(os.path.dirname(file_path)) if os.path.isdir(
        os.path.dirname(file_path)) else "dir-not-exist")

    # === Resolve ImportTask instance ===
    import_task = None
    if import_task_id:
        try:
            import_task = ImportTask.objects.get(id=import_task_id)
            logger.info("Linked to ImportTask ID: %s", import_task_id)
        except ImportTask.DoesNotExist:
            logger.warning("ImportTask ID %s not found", import_task_id)

    if not import_task:
        # Fallback: match via Celery task ID
        try:
            import_task = ImportTask.objects.get(task_id=self.request.id)
            logger.info("Linked via Celery task_id: %s", self.request.id)
        except ImportTask.DoesNotExist:
            logger.warning("No ImportTask found for Celery task_id: %s", self.request.id)

    if import_task:
        import_task.status = ImportTask.StatusChoices.PROCESSING
        import_task.save()
        logger.info("ImportTask %s marked as PROCESSING", import_task.id)

    # === Validate file existence ===
    if not os.path.exists(file_path):
        logger.error("File not found in worker: %s", file_path)

        if import_task:
            import_task.status = ImportTask.StatusChoices.FAILURE
            import_task.errors = [{"line": None, "message": f"file not found: {file_path}"}]
            import_task.finished_at = timezone.now()
            import_task.save()

        return {"created": 0, "errors": [{"line": None, "message": "file not found"}]}

    # === Initialize service and counters ===
    service = ImportService()
    total_created = 0
    total_errors = []
    processed = 0
    current_batch = []
    current_lineno = 1  # Starts after header

    with open(file_path, newline='', encoding='utf-8') as books_csv:
        reader = csv.DictReader(books_csv)
        for row in reader:
            current_lineno += 1

            # Normalize: strip whitespace, handle None
            normalized = {k.strip(): (v.strip() if v is not None else "") for k, v in row.items()}
            normalized["_lineno"] = current_lineno
            current_batch.append(normalized)

            # Process batch when full
            if len(current_batch) >= batch_size:
                res = service.import_rows(current_batch)
                total_created += res.created

                # map errors to include lineno if missing
                for e in res.errors:
                    if "line" not in e or not e.get("line"):
                        # try to pull from row if available
                        ln = e.get("row", {}).get("_lineno") if isinstance(e.get("row"), dict) else None
                        e["line"] = ln
                    total_errors.append(e)
                processed += len(current_batch)
                current_batch = []

        # === Final batch ===
        if current_batch:
            res = service.import_rows(current_batch)
            total_created += res.created
            for e in res.errors:
                if "line" not in e or not e.get("line"):
                    ln = e.get("row", {}).get("_lineno") if isinstance(e.get("row"), dict) else None
                    e["line"] = ln
                total_errors.append(e)
            processed += len(current_batch)
            current_batch = []

    # === Success: update task ===
    if import_task:
        import_task.processed = total_created
        import_task.total = processed
        import_task.errors = total_errors
        import_task.status = ImportTask.StatusChoices.SUCCESS
        import_task.finished_at = timezone.now()
        import_task.save()
        logger.info("ImportTask %s completed successfully", import_task.id)

    logger.info("CSV import finished: %s created, %s errors", total_created, len(total_errors))
    return {"created": total_created, "errors": total_errors}
