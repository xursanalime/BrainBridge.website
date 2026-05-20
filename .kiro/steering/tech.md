# BrainBridge — Tech Stack

## Backend

- **Runtime**: Python 3.11
- **Framework**: FastAPI 0.111 with async support
- **Server**: Uvicorn (with `[standard]` extras)
- **ORM**: SQLAlchemy 2.0 (declarative base via `DeclarativeBase`)
- **Database**: PostgreSQL in production (psycopg2-binary); SQLite for local dev (auto-detected from `DATABASE_URL`)
- **Auth**: JWT via `python-jose` — short-lived access tokens (15 min) + httpOnly refresh cookies (7 days); PBKDF2-SHA256 password hashing with per-user salt
- **AI**: Google Gemini API via async `httpx` (`gemini-2.0-flash` for JSON tasks, `gemini-2.5-flash` for chat)
- **Validation**: Pydantic v2 with `EmailStr` and `field_validator`
- **Google OAuth**: `google-auth` + `httpx`
- **Config**: `python-dotenv` — env vars loaded from `backend/.env`
- **Logging**: stdlib `logging.config.dictConfig` — rotating file handler at `backend/logs/app.log` (10 MB, 5 backups) + stdout

## Frontend

- **Vanilla JS** — no framework, no build step
- **Single HTML file** (`frontend/index.html`) with all UI; `frontend/js/app.js` contains all client logic (~3000+ lines)
- **CSS**: single `frontend/css/style.css`
- **API calls**: custom `api()` helper using `fetch`, Bearer token from `localStorage`, auto-refresh on 401
- **Emoji rendering**: custom Apple emoji PNG map (`/img/emojis/`) via `ap()` helper

## Key Libraries (requirements.txt)

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy==2.0.30
psycopg2-binary==2.9.9
python-jose[cryptography]==3.3.0
python-multipart==0.0.9
pydantic[email]==2.7.1
python-dotenv==1.0.1
google-auth==2.29.0
httpx==0.27.0
requests==2.31.0
```

## Deployment

- **Primary**: Railway — Docker build (`Dockerfile`), health check at `/api/health`
- **Alternative**: Vercel — `api/index.py` entry point, routes `/api/*` to FastAPI, static files served from `frontend/`
- **Process**: `Procfile` — `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (from backend/)
cd backend && uvicorn main:app --reload --port 8080

# Run via Docker
docker build -t brainbridge .
docker run -p 8080:8080 --env-file backend/.env brainbridge

# Database migrations (manual column additions handled automatically by init_db)
cd backend && python update_db.py

# Seed vocabulary decks
cd backend && python populate_decks.py

# Check DB state
cd backend && python check_db.py
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | Postgres or SQLite URL |
| `SECRET_KEY` | Yes | JWT signing secret |
| `ENV` | No | `development` or `production` |
| `PORT` | No | Server port (default 8080) |
| `ALLOWED_ORIGINS` | No | Comma-separated CORS origins |
| `GEMINI_API_KEY` | No | Enables AI features |
| `GOOGLE_CLIENT_ID` | No | Enables Google OAuth |
| `GOOGLE_CLIENT_SECRET` | No | Enables Google OAuth |
| `SMTP_HOST/PORT/USER/PASS` | No | Enables password reset emails |
