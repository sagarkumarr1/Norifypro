web: gunicorn notifypro.wsgi:application
worker: celery -A notifypro worker --loglevel=info
beat: celery -A notifypro beat --loglevel=info
flower: celery -A notifypro flower --port=5555