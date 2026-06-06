import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notifypro.settings')

app = Celery('notifypro')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Sab apps ke tasks.py automatic load honge
app.autodiscover_tasks()