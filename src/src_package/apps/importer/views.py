"""
REST API endpoints for CSV book import.

Provides:
- POST /upload/: Upload CSV and trigger async Celery task.
- GET /status/<task_id>/: Poll task progress and results.

Uses Django REST Framework with serializer validation,
file storage abstraction, and Celery for background processing.
"""

import logging
import os
import time
import uuid

from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ImportTask
from .serializers import ImportUploadSerializer, ImportTaskSerializer
from .tasks import process_csv

logger = logging.getLogger(__name__)


class ImportUploadView(APIView):
    """
    Handle CSV file upload and initiate background import.

    - Validates file via serializer.
    - Saves to MEDIA_ROOT with unique filename.
    - Ensures file is fully written (Docker volume sync).
    - Creates ImportTask and launches Celery job.
    - Returns task_id for polling.
    """
    def post(self, request, *args, **kwargs):
        """
        Upload CSV and start import task.

        Args:
            request: DRF request with 'file' in FILES.

        Returns:
            Response: 202 Accepted with Celery task_id.
        """
        serializer = ImportUploadSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning("Upload failed validation: %s", serializer.errors)
            return Response(serializer.errors, status=400)

        # default_storage in dockerfile uses filesystem at MEDIA_ROOT by default
        f = serializer.validated_data["file"]

        # Generate safe, unique filename
        filename = f"importer/{uuid.uuid4().hex}_{f.name}"

        # Save using Django's storage backend
        saved_path = default_storage.save(filename, f)
        if hasattr(default_storage, "path"):
            saved_abs_path = default_storage.path(saved_path)  # preferred (FileSystemStorage)
        else:
            # fallback: use MEDIA_ROOT
            saved_abs_path = os.path.abspath(os.path.join(settings.MEDIA_ROOT, saved_path))

        # === Ensure file is fully written (critical in Docker) ===
        while True:
            try:
                with open(saved_abs_path, "rb") as fh:
                    fh.read(1)
                    break
            except Exception:
                time.sleep(0.05)

        logger.info("SAVED_PATH (relative): %s", saved_path)
        logger.info("SAVED_PATH (absolute): %s", saved_abs_path)

        # === Create task tracker ===
        import_task = ImportTask.objects.create(status=ImportTask.StatusChoices.PENDING)

        # === Launch Celery task ===
        async_result = process_csv.delay(saved_abs_path, import_task.id)
        import_task.task_id = async_result.id
        import_task.save(update_fields=["task_id"])

        logger.info("Celery task queued: %s (ImportTask: %s)", async_result.id, import_task.id)
        return Response({"task_id": async_result.id}, status=202)


class ImportStatusView(APIView):
    """
    Retrieve real-time status of an import task.

    Polls ImportTask model updated by Celery worker.
    Returns progress, errors, and completion state.
    """
    def get(self, request, task_id, *args, **kwargs):
        """
        Get task status by Celery task_id.

        Args:
            task_id (str): Celery task identifier.

        Returns:
            Response: 200 with serialized ImportTask or 404.
        """
        try:
            import_task = ImportTask.objects.get(task_id=task_id)
        except ImportTask.DoesNotExist:
            logger.info("Status check for non-existent task: %s", task_id)
            return Response({"detail": "not found"}, status=404)

        ser = ImportTaskSerializer(import_task, context={'request': request})
        return Response(ser.data, status=200)
