import os
from celery import Celery


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "notifypro.settings"
)

app = Celery("notifypro")

app.config_from_object(
    "django.conf:settings",
    namespace="CELERY"
)

# Automatically discover tasks.py files
app.autodiscover_tasks()

# Optional: debugging task
@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")