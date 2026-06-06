# NotifyPro — Background Notification System

A production-ready notification queue built with Django + Celery + Redis.

## Problem it solves
Without background tasks, sending emails blocks the API response —
users wait 2-3 seconds. NotifyPro queues all notifications, keeping
API response time under 50ms regardless of email load.

## Features
- Background email queue with Celery
- Automatic retry on failure (3 attempts, 60s delay)
- Scheduled daily reports via Celery Beat
- Real-time task monitoring with Flower dashboard
- Full notification history with status tracking

## Tech Stack
Django · DRF · Celery · Redis · PostgreSQL · Flower

## Quick Start
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Redis
sudo service redis-server start

# 3. Run all services
python manage.py runserver          # Terminal 1
celery -A notifypro worker -l info  # Terminal 2
celery -A notifypro beat -l info    # Terminal 3
celery -A notifypro flower          # Terminal 4 → localhost:5555
```

## API Endpoints
POST /api/users/register/   — Register + triggers welcome email
GET  /api/notifications/    — Notification history

## Monitoring
Flower Dashboard: http://localhost:5555
Live task monitoring, worker status, retry failed tasks