# TochiBOT — Render-ready web app

A deployable FastAPI + vanilla JS application with user registration/login, isolated task lists, persisted conversation history, and OpenAI-powered chat. It is a new web application scaffold, not an automatic merge of the legacy `TochiBot.py` CLI.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
# Set SECRET_KEY and OPENAI_API_KEY in your shell (see .env.example).
uvicorn app.main:app --reload
```

Visit http://localhost:8000. Without OPENAI_API_KEY, authentication/tasks work but chat returns a clear configuration error. The local SQLite database is for development only.

## Deploy to Render

1. Commit this project's contents to a GitHub branch/repository. Preserve any existing legacy TochiBot code; do not blindly overwrite it.
2. In Render, choose **New > Blueprint** and connect the GitHub repository containing `render.yaml`.
3. Review the **paid** Starter web service and Basic PostgreSQL plans shown in the Blueprint before approving.
4. Supply `OPENAI_API_KEY` when prompted. Render generates `SECRET_KEY` and attaches the PostgreSQL `DATABASE_URL`.
5. After the build, visit the generated `https://...onrender.com` address. Confirm `/health` returns `{"status":"ok"}`, then register, add/complete a task, send a chat message, log out and back in.

## Security and limitations

- Passwords are bcrypt-hashed; each API request uses a signed 7-day JWT; tasks/messages are scoped to the authenticated user. HTTPS is provided by Render.
- This starter does **not** yet implement email verification, password reset, OAuth, rate limiting, CSRF protection for cookie auth (tokens are in sessionStorage, not cookies), user deletion, admin tooling, database migrations, or monitoring. Add these before a broad public launch.
- Database tables are initialized automatically on startup. Use Alembic migrations before making schema changes in production.
- Chat stores message history in PostgreSQL. It sends recent history and incomplete task titles to OpenAI. Avoid entering sensitive information until you have reviewed privacy and retention requirements.
- Google Calendar, Gmail, weather, scheduled reminders, mood check-ins, and richer personal memory are **not** implemented yet. They require separate integration and security work.
