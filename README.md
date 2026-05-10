# Apartment Expenses

FastAPI app for shared apartment expenses.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

API docs:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/api/health
```

## Email

Copy `.env.example` to `.env` and fill SMTP values. If SMTP is not configured, scheduled reminders do not mark bills as sent and no email is attempted.
