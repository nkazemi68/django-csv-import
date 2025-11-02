import os
import time
import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from rest_framework import status
from django.conf import settings
from django.core.files.storage import default_storage
from .serializers import ImportUploadSerializer, ImportTaskSerializer
from .models import ImportTask
from .tasks import process_csv
import logging
logger = logging.getLogger(__name__)


class ImportUploadView(APIView):
    def post(self, request, *args, **kwargs):
        ser = ImportUploadSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=400)

        # default_storage in dockerfile uses filesystem at MEDIA_ROOT by default
        f = ser.validated_data["file"]
        filename = f"importer/{uuid.uuid4().hex}_{f.name}"
        saved_path = default_storage.save(filename, f)
        if hasattr(default_storage, "path"):
            saved_abs_path = default_storage.path(saved_path)  # preferred (FileSystemStorage)
        else:
            # fallback: use MEDIA_ROOT
            saved_abs_path = os.path.abspath(os.path.join(settings.MEDIA_ROOT, saved_path))

        while True:
            try:
                with open(saved_abs_path, "rb") as fh:
                    fh.read(1)
                    break
            except Exception:
                time.sleep(0.05)

        logger.info("SAVED_PATH (relative): %s", saved_path)
        logger.info("SAVED_PATH (absolute): %s", saved_abs_path)
        print("SAVED_PATH:", saved_abs_path)

        import_task = ImportTask.objects.create(task_id="", status=ImportTask.StatusChoices.PENDING)
        async_result = process_csv.delay(saved_abs_path, import_task.id)
        import_task.task_id = async_result.id
        import_task.save()
        return Response({"task_id": async_result.id}, status=202)


class ImportStatusView(APIView):
    def get(self, request, task_id, *args, **kwargs):
        try:
            import_task = ImportTask.objects.get(task_id=task_id)
        except ImportTask.DoesNotExist:
            return Response({"detail": "not found"}, status=404)

        ser = ImportTaskSerializer(import_task, context={'request': request})
        return Response(ser.data, status=200)
