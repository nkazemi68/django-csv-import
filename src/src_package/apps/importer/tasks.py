import csv
import os

from celery import shared_task
from django.utils import timezone
from .models import ImportTask
from .services.import_csv_service import ImportService
import logging, os

logger = logging.getLogger(__name__)


@shared_task(queue='import', bind=True)
def process_csv(self, file_path, import_task_id=None, batch_size=1000):
    file_path = os.path.abspath(file_path)
    logger.info("Task started. checking file_path: %s", file_path)
    logger.info("Worker sees dir listing: %s", os.listdir(os.path.dirname(file_path)) if os.path.isdir(
        os.path.dirname(file_path)) else "dir-not-exist")
    import_task = None
    if import_task_id:
        try:
            import_task = ImportTask.objects.get(id=import_task_id)
        except ImportTask.DoesNotExist:
            import_task = None
    if not import_task:
        # try to lookup by task_id column using celery's id
        try:
            import_task = ImportTask.objects.get(task_id=self.request.id)
        except ImportTask.DoesNotExist:
            import_task = None

    if import_task:
        import_task.status = ImportTask.StatusChoices.PROCESSING
        import_task.save()

    # Ensure file exists
    if not os.path.exists(file_path):
        logger.error("File not found in worker: %s", file_path)
        if import_task:
            import_task.status = ImportTask.StatusChoices.FAILURE
            import_task.errors = [{"line": None, "message": f"file not found: {file_path}"}]
            import_task.finished_at = timezone.now()
            import_task.save()
        return {"created": 0, "errors": [{"line": None, "message": "file not found"}]}

    service = ImportService()
    total_created = 0
    total_errors = []
    processed = 0
    current_batch = []
    current_lineno = 1

    with open(file_path, newline='', encoding='utf-8') as books_csv:
        reader = csv.DictReader(books_csv)
        for row in reader:
            current_lineno += 1
            normalized = {k.strip(): (v.strip() if v is not None else "") for k, v in row.items()}
            normalized["_lineno"] = current_lineno
            current_batch.append(normalized)
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

        # last batch
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

    # finalize ImportTask
    if import_task:
        import_task.processed = total_created
        import_task.total = processed
        import_task.errors = total_errors
        import_task.status = ImportTask.StatusChoices.SUCCESS
        import_task.finished_at = timezone.now()
        import_task.save()

    return {"created": total_created, "errors": total_errors}
