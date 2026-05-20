# BrainBridge — Project Structure

## Top-Level Layout

```
BrainBridge.website-main/
├── backend/          # FastAPI application (Python)
├── frontend/         # Static UI (HTML/CSS/JS, no build step)
├── api/              # Vercel serverless entry point
├── uploads/          # User-uploaded files (avatars, etc.)
├── requirements.txt  # Python dependencies
├── Dockerfile        # Docker build (used by Railway)
├── Procfile          # Process definition for Railway/Heroku
├── railway.json      # Railway deployment config
├── vercel.json       # Vercel routing config
└── .kiro/steering/   # AI steering rules
```

## Backend (`backend/`)

```
backend/
├── main.py           # FastAPI app factory, middleware, router registration, static file serving
├── db.py             # SQLAlchemy engine, SessionLocal, get_db(), init_db(), auto-migration
├── models.py         # All SQLAlchemy ORM models (single file)
├── .env              # Local environment variables (not committed)
├── brainbridge.db    # SQLite DB for local dev
├── logs/app.log      # Rotating log output
├── routes/           # FastAPI routers (one file per domain)
│   ├── auth.py       # Register, login, refresh, logout, change-password
│   ├── words.py      # CRUD + review + quiz for vocabulary words
│   ├── sentences.py  # Sentence writing session and AI grading
│   ├── ai_chat.py    # BrainBot chat sessions and messages
│   ├── stats.py      # Leaderboard, XP, user stats
│   ├── super_memory.py # Super Memory feature
│   ├── decks.py      # Pre-built vocabulary deck import
│   ├── google_auth.py # Google OAuth flow
│   ├── reset.py      # Password reset via email
│   ├── payments.py   # Payment/tier handling
│   └── admin.py      # Admin-only endpoints
└── services/         # Business logic layer (called by routes)
    ├── auth_service.py      # JWT creation/decode, password hashing, user lookup
    ├── word_service.py      # SM-2 algorithm, word CRUD, quiz generation
    ├── xp_service.py        # XP/coin award, daily/monthly reset logic
    ├── achievement_service.py # Achievement unlock checks
    ├── ai_service.py        # AI sentence grading logic
    ├── gemini_client.py     # Shared async Gemini API client (generate_json / generate_text)
    └── tier_service.py      # Freemium tier checks
```

## Frontend (`frontend/`)

```
frontend/
├── index.html        # Single-page app shell — all views as hidden divs
├── admin.html        # Separate admin panel page
├── js/
│   ├── app.js        # All client-side logic (~3000+ lines): auth, navigation, API calls, UI rendering
│   └── admin.js      # Admin panel logic
├── css/
│   └── style.css     # All styles (single file, CSS variables for theming)
└── img/
    └── emojis/       # Apple-style emoji PNGs (referenced via ap() helper in app.js)
```

## Key Architectural Patterns

**Backend**
- Routes import from `services/` — keep business logic out of route handlers
- All routes use `Depends(current_user)` for auth; `Depends(get_db)` for DB sessions
- DB session is always closed in a `finally` block via the `get_db()` generator
- New columns added to models are auto-migrated at startup via `_ensure_missing_columns()` in `db.py` — no Alembic
- All models live in `models.py`; import `Base` from there for `create_all`
- Logging uses named loggers: `logging.getLogger("brainbridge.<module>")` — never use `print()`
- AI calls always go through `gemini_client.generate_json()` or `generate_text()` — never call Gemini directly from routes

**Frontend**
- Navigation is handled by `go(page)` — shows/hides `.page` divs, triggers load functions
- All API calls go through the `api(method, path, body)` helper — handles auth headers and 401 token refresh
- DOM access uses `E(id)` shorthand for `document.getElementById(id)`
- User state stored in `TOKEN` (localStorage `bb_tok`) and `ME` (localStorage `bb_me`)
- UI text and messages are in Uzbek — maintain this convention for any new user-facing strings

**Database**
- `DATABASE_URL` starting with `sqlite` triggers SQLite mode; anything else uses PostgreSQL pool settings
- `UniqueConstraint` and `Index` are defined in `__table_args__` on the model class
- Cascade deletes are set on all child relationships (`cascade="all, delete-orphan"`)
