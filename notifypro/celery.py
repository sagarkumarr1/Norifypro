import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notifypro.settings')

app = Celery('notifypro')
app.config_from_object('django.conf:settings', namespace='CELERY')

# All apps  tasks.py automatic load 
app.autodiscover_tasks()