import sys, os
from dotenv import load_dotenv

load_dotenv()  # .env fayldan o'zgartiruvchilarni yuklaymiz (masalan, GROQ_API_KEY)
sys.path.insert(0, os.path.dirname(__file__))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from db import init_db
from routes import auth, words, reset, google_auth, sentences, ai_chat, stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="BrainBridge", version="3.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import time
from fastapi import Request
from fastapi.responses import JSONResponse

request_counts = {}
RATE_LIMIT = 150 # max requests per minute
RATE_WINDOW = 60 # window in seconds

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    
    # Don't rate limit static files too aggressively, focus on API
    if request.url.path.startswith("/api"):
        if client_ip not in request_counts:
            request_counts[client_ip] = []
            
        request_counts[client_ip] = [t for t in request_counts[client_ip] if now - t < RATE_WINDOW]
        
        if len(request_counts[client_ip]) >= RATE_LIMIT:
            return JSONResponse(status_code=429, content={"detail": "Sorovlar juda ko'p. Iltimos biroz kuting."})
            
        request_counts[client_ip].append(now)
        
    response = await call_next(request)
    
    # Security Headers
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://accounts.google.com https://unpkg.com https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com https://unpkg.com https://cdn.jsdelivr.net; "
        "font-src 'self' https://fonts.gstatic.com https://unpkg.com https://cdn.jsdelivr.net; "
        "img-src 'self' data: https://lh3.googleusercontent.com; "
        "connect-src 'self' https://accounts.google.com; "
        "frame-src 'self' https://accounts.google.com;"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response

app.include_router(auth.router,        prefix="/api")
app.include_router(reset.router,       prefix="/api")
app.include_router(google_auth.router, prefix="/api")
app.include_router(words.router,       prefix="/api")
app.include_router(sentences.router,   prefix="/api")
app.include_router(ai_chat.router,     prefix="/api")
app.include_router(stats.router,       prefix="/api")


@app.get("/api/health")
def health():
    return {"ok": True, "version": "3.0.0"}


# Serve frontend — disk dan to'g'ridan-to'g'ri
frontend = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

# Serve uploads
uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
avatars_dir = os.path.join(uploads_dir, "avatars")
os.makedirs(avatars_dir, exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory=uploads_dir), name="uploads")

if os.path.isdir(frontend):
    # index.html — har doim yangi (kesh yo'q)
    @app.get("/", include_in_schema=False)
    @app.head("/", include_in_schema=False)
    def root():
        resp = FileResponse(os.path.join(frontend, "index.html"), media_type="text/html")
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        resp.headers["Pragma"]        = "no-cache"
        resp.headers["Expires"]       = "0"
        # Security Headers
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-XSS-Protection"] = "1; mode=block"
        resp.headers["Content-Security-Policy"] = "default-src 'self' https:; style-src 'self' 'unsafe-inline' https:; script-src 'self' 'unsafe-inline' 'unsafe-eval' https:; img-src 'self' data: https:; font-src 'self' https: data:;"
        return resp


    # Boshqa statik fayllar — html=False (index.html ni o'zi serve qilmasin)
    app.mount("/", StaticFiles(directory=frontend, html=False), name="frontend")





if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 5000))
    reload = os.getenv("ENV", "production") != "production"
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=reload)
