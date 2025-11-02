import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src_package.settings")

app = Celery("src_package")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()