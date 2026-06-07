# NotifyPro — Background Notification System

> A production-ready background notification queue that keeps your API fast while handling email delivery reliably in the background.

---

## The Problem

Most beginner projects send emails **synchronously** — the API waits for the email to be sent before returning a response. This means users wait 2–5 seconds on every registration.

**NotifyPro solves this.** The API responds in under 50ms. Email delivery happens in the background via Celery workers, completely invisible to the user.

---

## Features

- **Background email queue** — Emails are processed by Celery workers, never blocking the API
- **Idempotency protection** — Duplicate email prevention; if a notification is already sent, it won't be sent again
- **Automatic retry logic** — Failed emails retry up to 3 times with a 60-second delay, tracking retry count and last retry timestamp
- **Scheduled tasks** — Daily reports auto-generate at midnight via Celery Beat
- **Failed notification recovery** — A periodic task retries all failed notifications every 30 minutes
- **Real-time monitoring** — Flower dashboard shows live task status, worker health, and task history
- **Full notification history** — Every notification logged with status (pending → sent / failed), retry count, error messages
- **Notification list API** — Authenticated users can retrieve their notification history
- **Interactive API docs** — Swagger UI and ReDoc available out of the box
- **10 unit tests** — Register endpoint and notification model fully tested

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend Framework | Django 6.0.6 + Django REST Framework 3.17.1 |
| Task Queue | Celery 5.6.3 |
| Message Broker | Redis 8.0.0 |
| Database | PostgreSQL (production) / SQLite (development) |
| Task Scheduler | Celery Beat 2.9.0 |
| Task Monitoring | Flower 2.0.1 |
| API Documentation | drf-spectacular 0.29.0 (Swagger + ReDoc) |
| Static Files | Whitenoise 6.12.0 |
| Deployment | Render |

---

## Architecture

```
User Request
     │
     ▼
Django API (responds in ~50ms)
     │
     ├──► PostgreSQL (saves user + notification record)
     │
     └──► Redis Queue (drops task here)
               │
               ▼
         Celery Worker (picks up task)
               │
               ├──► Idempotency check (already sent? skip)
               ├──► Sends email via Gmail SMTP
               ├──► Updates notification status → sent ✅
               └──► On failure:
                       ├── Tracks retry_count + last_retry_at
                       ├── Stores error_message in DB
                       └── Retries up to 3 times (60s delay each)

Celery Beat (runs on schedule)
     ├──► Daily report at midnight (new users, sent/failed count)
     └──► Retry failed notifications every 30 minutes
```

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/users/register/` | No | Register user + trigger welcome email |
| `GET` | `/api/notifications/` | Yes | Get notification history for logged-in user |
| `GET` | `/api/docs/` | No | Swagger UI — interactive API docs |
| `GET` | `/api/redoc/` | No | ReDoc — alternative API docs |
| `GET` | `/admin/` | Staff | Django admin panel |

### Register Example

**Request:**
```bash
curl -X POST https://norifypro.onrender.com/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "sagar",
    "email": "sagar@example.com",
    "password": "StrongPass123!"
  }'
```

**Response (201 Created):**
```json
{
  "message": "Registration successful! Welcome email is being sent.",
  "user_id": 1,
  "email": "sagar@example.com"
}
```

The API responds immediately. The welcome email is delivered in the background.

### Notification History Example

**Request:**
```bash
curl -X GET https://norifypro.onrender.com/api/notifications/ \
  -H "Authorization: Bearer <your-token>"
```

**Response:**
```json
[
  {
    "id": 1,
    "notification_type": "welcome",
    "status": "sent",
    "subject": "Welcome to NotifyPro, sagar!",
    "created_at": "2026-06-06T12:00:00Z",
    "sent_at": "2026-06-06T12:00:02Z"
  }
]
```

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
DATABASE_URL=your-postgresql-url-here
REDIS_URL=redis://localhost:6379/0
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-16-digit-app-password
DEFAULT_FROM_EMAIL=your-gmail@gmail.com
FLOWER_BASIC_AUTH=admin:notifypro123
```

> **Gmail App Password:** Google Account → Security → 2-Step Verification → App Passwords → Generate one for "NotifyPro"
>
> **DATABASE_URL:** Leave empty for SQLite in development. Add PostgreSQL URL for production.

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
| ReDoc | http://localhost:8000/api/redoc/ |
| Django Admin | http://localhost:8000/admin/ |
| Flower Dashboard | http://localhost:5555 |

### 8. Run tests

```bash
python manage.py test
```

**Expected output:**
```
Found 10 test(s).
..........
Ran 10 tests in 3.5s
OK
```

**Test coverage:**

| Test | File | Description |
|------|------|-------------|
| `test_register_success` | users/tests.py | Successful registration returns 201 |
| `test_register_duplicate_email` | users/tests.py | Duplicate email returns 400 |
| `test_register_duplicate_username` | users/tests.py | Duplicate username returns 400 |
| `test_register_missing_fields` | users/tests.py | Empty body returns 400 |
| `test_register_invalid_email` | users/tests.py | Invalid email format returns 400 |
| `test_register_weak_password` | users/tests.py | Weak password returns 400 |
| `test_email_stored_lowercase` | users/tests.py | Email normalized to lowercase |
| `test_notification_created_pending` | notifications/tests.py | Notification starts as pending |
| `test_notification_str` | notifications/tests.py | String representation is correct |
| `test_notification_status_update` | notifications/tests.py | Status updates correctly |

---

## Scheduled Tasks

| Task | Schedule | Description |
|------|----------|-------------|
| `send_daily_report` | Every day at midnight | Logs new users, sent/failed notification counts |
| `retry_failed_notifications` | Every 30 minutes | Resets and retries up to 10 failed notifications |

---

## Notification Lifecycle

```
POST /api/users/register/
        │
        ▼
transaction.atomic()
        ├── User created in PostgreSQL
        └── Notification record created (status: pending)
                │
                ▼ (outside transaction)
        send_welcome_email.delay(notification.id)
                │
                ▼
        Celery Worker
                │
                ├── Already sent? → Skip (idempotency)
                ├── Send email via Gmail SMTP
                ├── status → sent ✅
                │   sent_at = now()
                │
                └── On failure:
                        ├── retry_count += 1
                        ├── last_retry_at = now()
                        ├── error_message = exc
                        └── Retry (max 3 times, 60s delay)
                                │
                                └── After 3 failures:
                                        status → failed ❌
```

---

## Project Structure

```
notifypro/
├── notifypro/
│   ├── settings.py       # Environment-based config + security headers
│   ├── celery.py         # Celery app + autodiscover
│   ├── urls.py           # Root URLs + Swagger
│   └── __init__.py       # Celery loaded on startup
│
├── users/
│   ├── models.py         # Custom User (email login, db_index, lowercase save)
│   ├── serializers.py    # RegisterSerializer with full validation
│   ├── views.py          # RegisterView with transaction.atomic()
│   ├── urls.py           # /api/users/ routes
│   ├── admin.py          # CustomUserAdmin with fieldsets
│   └── tests.py          # 7 register endpoint tests
│
├── notifications/
│   ├── models.py         # Notification model (retry_count, last_retry_at, indexes)
│   ├── tasks.py          # Celery tasks (idempotency, retry tracking, daily report)
│   ├── views.py          # NotificationListView (authenticated)
│   ├── urls.py           # /api/notifications/ routes
│   ├── admin.py          # NotificationAdmin with filters + search
│   └── tests.py          # 3 notification model tests
│
├── build.sh              # Render build script (install + collectstatic + migrate)
├── Procfile              # web + worker + beat + flower
├── requirements.txt      # All dependencies with pinned versions
├── .env.example          # Environment variable template
└── .gitignore            # venv, .env, __pycache__, db.sqlite3, staticfiles
```

---

## Security

- All secrets managed via environment variables — no hardcoded credentials
- Security headers enabled: `XSS_FILTER`, `CONTENT_TYPE_NOSNIFF`, `X_FRAME_OPTIONS: DENY`
- HTTPS enforced in production: `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`
- `SESSION_COOKIE_HTTPONLY` and `CSRF_COOKIE_HTTPONLY` enabled
- Email stored and validated in lowercase to prevent duplicates
- Password validation enforced via Django's built-in validators

---

## Deployment (Render)

This project is deployed on [Render](https://render.com) using:

- **Web Service** — Django + Gunicorn
- **Redis** — Render managed Redis
- **PostgreSQL** — Render managed PostgreSQL

**Live URL:** https://norifypro.onrender.com

**API Docs:** https://norifypro.onrender.com/api/docs/

> **Note:** The Celery worker requires a paid background worker on Render's free plan. For local testing, run the worker locally pointed at the Render Redis external URL.

---

## What I Learned Building This

- How Celery's task queue decouples email delivery from API response time
- Idempotency — why preventing duplicate task execution matters in production
- `transaction.atomic()` — ensuring data consistency between user creation and notification record
- `update_fields` in Django — optimizing DB writes by updating only changed fields
- Database indexing strategy for frequently filtered fields
- Celery Beat with a database scheduler for reliable periodic tasks
- Real-time task monitoring with Flower
- Unit testing with mocks — testing Celery tasks without a real worker using `unittest.mock.patch`
- Production deployment with environment-based configuration and security headers

---

## Author

**Sagar Kumar**
- GitHub: [@sagarkumarr1](https://github.com/sagarkumarr1)
- LinkedIn: [linkedin.com/in/imsagar07](https://linkedin.com/in/imsagar07)
- Email: sagarkumar844122@gmail.com
