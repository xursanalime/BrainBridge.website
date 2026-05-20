"""
BrainBridge — main.py (Professional Production Version)
========================================================
Yaxshilanishlar:
- Structured logging (loguru o'rniga standart logging.config)
- CORS — faqat ruxsat etilgan domenlar
- Rate limiting — IP + endpoint asosida
- Security headers — kuchaytirilgan
- Health check — DB holati bilan
- Lifespan — startup/shutdown
- DB log fayli — papkaga ajratilgan
"""
import sys
import os
import logging
import logging.config
import time
from contextlib import asynccontextmanager
from collections import defaultdict, deque

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))

# ── Logging konfiguratsiyasi ─────────────────────────────────────────────────
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "detailed": {
            "format": "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "detailed",
            "filename": os.path.join(LOG_DIR, "app.log"),
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "encoding": "utf-8",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"],
    },
    "loggers": {
        "brainbridge": {"level": "DEBUG", "propagate": True},
        "uvicorn.access": {"level": "WARNING"},
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("brainbridge.main")

# ── FastAPI ──────────────────────────────────────────────────────────────────
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import text

from db import init_db, get_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 BrainBridge v3.1.1 starting up...")
    init_db()
    logger.info("✅ Database initialized")
    yield
    logger.info("🛑 BrainBridge shutting down")


app = FastAPI(
    title="BrainBridge API",
    version="3.1.1",
    description="Ingliz so'zlarini aqlli o'rganing",
    lifespan=lifespan,
    docs_url="/api/docs" if os.getenv("ENV") != "production" else None,
    redoc_url=None,
)

# ── CORS — faqat ruxsat etilgan domenlar ────────────────────────────────────
_ALLOWED_ORIGINS_ENV = os.getenv("ALLOWED_ORIGINS", "")
if _ALLOWED_ORIGINS_ENV:
    _ORIGINS = [o.strip() for o in _ALLOWED_ORIGINS_ENV.split(",") if o.strip()]
else:
    # Development uchun default
    _ORIGINS = [
        "http://localhost:5000",
        "http://localhost:3000",
        "http://127.0.0.1:5000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# ── Rate Limiting (IP asosida, deque bilan) ──────────────────────────────────
_rate_store: dict[str, deque] = defaultdict(lambda: deque())
RATE_LIMIT     = 150   # max API so'rovlar per daqiqa
RATE_WINDOW    = 60    # soniya
AUTH_LIMIT     = 20    # auth endpoint'lar uchun qattiqroq limit
AUTH_WINDOW    = 300   # 5 daqiqa

@app.middleware("http")
async def rate_limit_and_security(request: Request, call_next):
    path = request.url.path
    client_ip = (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or (request.client.host if request.client else "unknown")
    )
    now = time.time()

    # API so'rovlarni rate limit qilish
    if path.startswith("/api"):
        # Auth endpoint'lar — qattiqroq limit
        if path in ("/api/auth/login", "/api/auth/register", "/api/auth/forgot-password"):
            bucket = f"auth:{client_ip}"
            window, limit = AUTH_WINDOW, AUTH_LIMIT
        else:
            bucket = f"api:{client_ip}"
            window, limit = RATE_WINDOW, RATE_LIMIT

        q = _rate_store[bucket]
        # Eski yozuvlarni tozalash
        while q and now - q[0] > window:
            q.popleft()

        if len(q) >= limit:
            logger.warning("Rate limit exceeded: ip=%s path=%s", client_ip, path)
            return JSONResponse(
                status_code=429,
                content={"detail": "So'rovlar juda ko'p. Biroz kuting.", "retry_after": window},
                headers={"Retry-After": str(window)},
            )
        q.append(now)

    response = await call_next(request)

    # ── Security Headers ──────────────────────────────────────────────────────
    env = os.getenv("ENV", "production")
    csp_connect = "connect-src 'self' https://accounts.google.com"
    if env != "production":
        csp_connect += " http://localhost:* ws://localhost:*"

    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com "
        "https://accounts.google.com https://unpkg.com https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com "
        "https://cdnjs.cloudflare.com https://unpkg.com https://cdn.jsdelivr.net; "
        "font-src 'self' https://fonts.gstatic.com https://unpkg.com https://cdn.jsdelivr.net data:; "
        "img-src 'self' data: blob: https://lh3.googleusercontent.com; "
        f"{csp_connect}; "
        "frame-src 'self' https://accounts.google.com; "
        "object-src 'none'; "
        "base-uri 'self';"
    )
    response.headers["X-Content-Type-Options"]    = "nosniff"
    response.headers["X-Frame-Options"]           = "DENY"
    response.headers["X-XSS-Protection"]          = "1; mode=block"
    response.headers["Referrer-Policy"]           = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"]        = "camera=(), microphone=(), geolocation=()"

    if env == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response


# ── Routers ──────────────────────────────────────────────────────────────────
from routes import auth, words, reset, google_auth, stats, admin, decks
from routes import sentences, ai_chat, payments, super_memory

app.include_router(auth.router,          prefix="/api")
app.include_router(reset.router,         prefix="/api")
app.include_router(google_auth.router,   prefix="/api")
app.include_router(words.router,         prefix="/api")
app.include_router(stats.router,         prefix="/api")
app.include_router(admin.router,         prefix="/api")
app.include_router(decks.router,         prefix="/api")
app.include_router(sentences.router,     prefix="/api")
app.include_router(ai_chat.router,      prefix="/api")
app.include_router(payments.router,     prefix="/api")
app.include_router(super_memory.router)  # Already has /api/super-memory prefix


# ── Health check — DB bilan ──────────────────────────────────────────────────
@app.get("/api/health", tags=["system"])
def health():
    """Health check — DB ulanishi ham tekshiriladi."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        logger.error("Health check DB error: %s", exc)
        db_status = "error"

    return {
        "ok": db_status == "connected",
        "version": "3.1.1",
        "db": db_status,
        "env": os.getenv("ENV", "production"),
    }


# ── Static files ─────────────────────────────────────────────────────────────
frontend = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
avatars_dir = os.path.join(uploads_dir, "avatars")
os.makedirs(avatars_dir, exist_ok=True)

app.mount("/api/uploads", StaticFiles(directory=uploads_dir), name="uploads")

_NO_CACHE = {"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}

if os.path.isdir(frontend):
    @app.get("/admin", include_in_schema=False)
    def admin_page():
        resp = FileResponse(os.path.join(frontend, "admin.html"), media_type="text/html")
        for k, v in _NO_CACHE.items():
            resp.headers[k] = v
        return resp

    @app.get("/", include_in_schema=False)
    @app.head("/", include_in_schema=False)
    def root():
        resp = FileResponse(os.path.join(frontend, "index.html"), media_type="text/html")
        for k, v in _NO_CACHE.items():
            resp.headers[k] = v
        return resp

    app.mount("/", StaticFiles(directory=frontend, html=False), name="frontend")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    reload = os.getenv("ENV", "production") != "production"
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=reload)
