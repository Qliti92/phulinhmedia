import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "phulinhmedia.settings")

app = Celery("phulinhmedia")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
