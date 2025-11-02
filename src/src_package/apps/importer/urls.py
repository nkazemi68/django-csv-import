from django.urls import path
from .views import ImportUploadView, ImportStatusView


urlpatterns = [
    path("", ImportUploadView.as_view(), name="importer-upload"),
    path("/<str:task_id>", ImportStatusView.as_view(), name="importer-status")
]