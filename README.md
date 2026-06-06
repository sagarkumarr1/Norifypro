# NotifyPro — Background Notification System

> A production-ready background notification queue that keeps your API fast while handling email delivery reliably in the background.

---

## The Problem

Most beginner projects send emails **synchronously** — the API waits for the email to be sent before returning a response. This means users wait 2–5 seconds on every registration.

**NotifyPro solves this.** The API responds in under 50ms. Email delivery happens in the background via Celery workers, completely invisible to the user.

---

## Features

- **Background email queue** — Emails are processed by Celery workers, never blocking the API
- **Automatic retry logic** — Failed emails retry up to 3 times with a 60-second delay between attempts
- **Scheduled tasks** — Daily reports auto-generate at midnight via Celery Beat
- **Failed notification recovery** — A periodic task retries all failed notifications every 30 minutes
- **Real-time monitoring** — Flower dashboard shows live task status, worker health, and task history
- **Full notification history** — Every notification is logged with status (pending → sent / failed)
- **Interactive API docs** — Swagger UI available out of the box

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend Framework | Django 6.0.6 + Django REST Framework |
| Task Queue | Celery 5.6.3 |
| Message Broker | Redis 8.0.0 |
| Database | PostgreSQL (production) / SQLite (development) |
| Task Monitoring | Flower 2.0.1 |
| API Documentation | drf-spectacular (Swagger UI) |
| Static Files | Whitenoise |
| Deployment | Render |

---

## Architecture

```
User Request
     │
     ▼
Django API (responds in ~50ms)
     │
     ├──► PostgreSQL (saves user)
     │
     └──► Redis Queue (drops task here)
               │
               ▼
         Celery Worker (picks up task)
               │
               ├──► Sends email via Gmail SMTP
               ├──► Updates notification status in DB
               └──► Retries on failure (max 3 times)

Celery Beat (runs on schedule)
     ├──► Daily report at midnight
     └──► Retry failed notifications every 30 min
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/users/register/` | Register user + trigger welcome email |
| `GET` | `/api/docs/` | Swagger UI — interactive API docs |
| `GET` | `/api/redoc/` | ReDoc — alternative API docs |
| `GET` | `/admin/` | Django admin panel |

### Register Example

**Request:**
```bash
curl -X POST https://norifypro.onrender.com/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "sagar",
    "email": "sagar@example.com",
    "password": "yourpassword"
  }'
```

**Response:**
```json
{
  "message": "Registration successful! Welcome email is being sent.",
  "user_id": 1,
  "email": "sagar@example.com"
}
```

The API responds immediately. The welcome email is delivered in the background.

---

## Local Setup

### Prerequisites

- Python 3.10+
- Redis installed and running
- Gmail account with App Password enabled

### 1. Clone the repository

```bash
git clone https://github.com/sagarkumarr1/notifypro.git
cd notifypro
```

### 2. Create virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your values:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_URL=                        # Leave empty for SQLite in development
REDIS_URL=redis://localhost:6379/0
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-16-digit-app-password
DEFAULT_FROM_EMAIL=your-gmail@gmail.com
```

> **Gmail App Password:** Go to Google Account → Security → 2-Step Verification → App Passwords → Generate one for "NotifyPro"

### 5. Run database migrations

```bash
python manage.py migrate
```

### 6. Create admin superuser

```bash
python manage.py createsuperuser
```

### 7. Start all services (4 terminals)

```bash
# Terminal 1 — Django development server
python manage.py runserver

# Terminal 2 — Celery worker (use --pool=solo on Windows)
celery -A notifypro worker --loglevel=info --pool=solo

# Terminal 3 — Celery Beat scheduler
celery -A notifypro beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# Terminal 4 — Flower monitoring dashboard
celery -A notifypro flower --port=5555 --basic_auth=admin:notifypro123
```

| Service | URL |
|---------|-----|
| Django API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/api/docs/ |
| Django Admin | http://localhost:8000/admin/ |
| Flower Dashboard | http://localhost:5555 |

---

## Scheduled Tasks

| Task | Schedule | Description |
|------|----------|-------------|
| `send_daily_report` | Every day at midnight | Logs new users, sent/failed notifications |
| `retry_failed_notifications` | Every 30 minutes | Retries up to 10 failed notifications |

---

## Notification Flow

```
Registration API called
        │
        ▼
User created in PostgreSQL
        │
        ▼
send_welcome_email.apply_async() — task queued in Redis
        │
        ▼
Celery worker picks up task
        │
        ├── Creates Notification record (status: pending)
        ├── Sends email via Gmail SMTP
        ├── Updates status → sent ✅
        │
        └── On failure:
              ├── Updates status → failed ❌
              ├── Logs error message
              └── Retries up to 3 times (60s delay each)
```

---

## Project Structure

```
notifypro/
├── notifypro/
│   ├── settings.py       # All configuration via environment variables
│   ├── celery.py         # Celery app configuration
│   ├── urls.py           # Root URL configuration + Swagger
│   └── __init__.py       # Celery app loaded on startup
│
├── users/
│   ├── models.py         # Custom User model (email as USERNAME_FIELD)
│   ├── views.py          # RegisterView with Swagger docs
│   ├── urls.py           # /api/users/ routes
│   └── admin.py          # CustomUserAdmin
│
├── notifications/
│   ├── models.py         # Notification model with status tracking
│   ├── tasks.py          # Celery tasks — email, daily report, retry
│   └── admin.py          # NotificationAdmin with filters + search
│
├── build.sh              # Render build script
├── Procfile              # Render process definitions
├── requirements.txt      # All dependencies with pinned versions
└── .env.example          # Environment variable template
```

---

## Deployment (Render)

This project is deployed on [Render](https://render.com) using:

- **Web Service** — Django + Gunicorn
- **Redis** — Render managed Redis
- **PostgreSQL** — Render managed PostgreSQL

**Live URL:** https://norifypro.onrender.com

**API Docs:** https://norifypro.onrender.com/api/docs/

> Note: The Celery worker requires a paid background worker service on Render. For local testing, run the worker locally pointed at the Render Redis external URL.

---

## What I Learned Building This

- How Celery's task queue works with Redis as a broker
- Why background tasks matter for API performance
- Implementing retry logic with exponential backoff
- Scheduled tasks using Celery Beat with a database scheduler
- Real-time task monitoring with Flower
- Production deployment with environment-based configuration

---

## Author

**Sagar Kumar**
- GitHub: [@sagarkumarr1](https://github.com/sagarkumarr1)
- LinkedIn: [linkedin.com/in/imsagar07](https://linkedin.com/in/imsagar07)
- Email: sagarkumar844122@gmail.com