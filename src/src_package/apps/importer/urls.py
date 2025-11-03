from django.urls import path
from .views import ImportUploadView, ImportStatusView


urlpatterns = [
    # POST /importer/ -> Upload CSV file and queue Celery task
    path("", ImportUploadView.as_view(), name="importer-upload"),
    # GET /importer/<task_id>/ -> Poll status and errors
    path("/<str:task_id>", ImportStatusView.as_view(), name="importer-status")
]