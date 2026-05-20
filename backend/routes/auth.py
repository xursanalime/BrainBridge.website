"""
Auth routes — BrainBridge v3.1
================================
Yaxshilanishlar:
- Brute-force himoya QAYTA YOQILDI (progressive lockout)
- Input validation kuchaytirildi
- Logging qo'shildi
- Password complexity check
"""
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.orm import Session

from db import get_db
from services.auth_service import (
    create_access_token, create_refresh_token, decode_token,
    get_user, get_user_by_email,
    login, register, verify_password, hash_password,
)
from services.xp_service import add_xp

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
logger = logging.getLogger("brainbridge.auth")

# ── Constants ─────────────────────────────────────────────────────────────────
MAX_FAILED_ATTEMPTS = 5
LOCK_DURATIONS = [
    (1,  timedelta(minutes=5)),
    (2,  timedelta(minutes=15)),
    (3,  timedelta(hours=1)),
    (4,  timedelta(hours=6)),
    (5,  timedelta(hours=24)),
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _get_lock_duration(failed_count: int) -> timedelta:
    """Progressive lockout — ko'p urinish = uzunroq bloklash."""
    for threshold, duration in reversed(LOCK_DURATIONS):
        if failed_count >= threshold:
            return duration
    return timedelta(minutes=1)


def _lock_message(locked_until: datetime) -> str | None:
    diff = locked_until - _now()
    total = int(diff.total_seconds())
    if total <= 0:
        return None
    h, rem = divmod(total, 3600)
    m, s   = divmod(rem, 60)
    if h >= 24:
        return f"Akkaunt {h // 24} kunga bloklangan. Ertaga urinib ko'ring."
    if h > 0:
        return f"Akkaunt {h} soat {m} daqiqaga bloklangan."
    return f"Akkaunt {m} daqiqa {s} soniyaga bloklangan."


def _apply_lock(user, db: Session) -> None:
    """Muvaffaqiyatsiz urinishni qayd etadi va kerak bo'lsa bloklaydi."""
    f = (user.failed_logins or 0) + 1
    user.failed_logins = f

    if f >= MAX_FAILED_ATTEMPTS:
        duration = _get_lock_duration(f)
        user.locked_until = _now() + duration
        logger.warning(
            "Account locked: user_id=%s email=%s failed=%d until=%s",
            user.id, user.email, f, user.locked_until,
        )
    db.commit()


def _check_lock(user) -> None:
    """Bloklangan akkauntni tekshiradi, bloklangan bo'lsa 429 qaytaradi."""
    if user.locked_permanent:
        raise HTTPException(403, "Akkaunt doimiy ravishda bloklangan. Qo'llab-quvvatlash bilan bog'laning.")

    if user.locked_until:
        lu = user.locked_until
        if lu.tzinfo is None:
            lu = lu.replace(tzinfo=timezone.utc)
        if _now() < lu:
            msg = _lock_message(lu)
            raise HTTPException(429, msg or "Akkaunt vaqtincha bloklangan.")


# ── Dependency ────────────────────────────────────────────────────────────────

def current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)):
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(401, "Token yaroqsiz yoki muddati tugagan.")
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(401, "Foydalanuvchi topilmadi.")
    return user


# ── Schemas ───────────────────────────────────────────────────────────────────

class RegisterIn(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Parol kamida 8 ta belgi bo'lsin.")
        if len(v) > 128:
            raise ValueError("Parol 128 belgidan oshmasligi kerak.")
        return v


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/register", status_code=201)
def register_route(body: RegisterIn, response: Response, db: Session = Depends(get_db)):
    if get_user_by_email(db, body.email):
        raise HTTPException(400, "Bu email allaqachon ro'yxatdan o'tgan.")

    user = register(db, body.email, body.password)
    add_xp(db, user, 50)
    logger.info("New user registered: user_id=%s", user.id)

    access_token  = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    response.set_cookie(
        key="refresh_token", value=refresh_token,
        httponly=True, secure=True, samesite="Lax",
        max_age=7 * 24 * 60 * 60,
    )
    return {"access_token": access_token, "user_id": user.id, "email": user.email}


@router.post("/login")
def login_route(
    response: Response,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = get_user_by_email(db, form.username)

    if user:
        _check_lock(user)

    ok = login(db, form.username, form.password)
    if not ok:
        if user:
            _apply_lock(user, db)
            logger.warning("Failed login attempt: email=%s", form.username)
        raise HTTPException(401, "Email yoki parol noto'g'ri.")

    # Muvaffaqiyatli kirish — hisoblagichlarni reset
    user.failed_logins = 0
    user.locked_until  = None
    db.commit()

    logger.info("User logged in: user_id=%s", user.id)

    access_token  = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    response.set_cookie(
        key="refresh_token", value=refresh_token,
        httponly=True, secure=True, samesite="Lax",
        max_age=7 * 24 * 60 * 60,
    )
    return {
        "access_token": access_token,
        "user_id":      user.id,
        "email":        user.email,
        "is_admin":     getattr(user, "is_admin", False),
        "needs_password_update": len(form.password) < 8,
    }


@router.post("/refresh")
def refresh_route(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(401, "Refresh token topilmadi.")

    user_id = decode_token(refresh_token, token_type="refresh")
    if not user_id:
        raise HTTPException(401, "Refresh token yaroqsiz yoki muddati tugagan.")

    user = get_user(db, user_id)
    if not user:
        raise HTTPException(401, "Foydalanuvchi topilmadi.")

    return {"access_token": create_access_token(user.id)}


@router.post("/logout")
def logout_route(response: Response):
    response.delete_cookie("refresh_token", httponly=True, secure=True, samesite="Lax")
    return {"message": "Chiqildi."}


@router.get("/me")
def me(user=Depends(current_user)):
    return {
        "id":       user.id,
        "email":    user.email,
        "streak":   user.streak or 0,
        "created_at": user.created_at,
        "avatar_url": user.avatar_url,
        "is_admin": getattr(user, "is_admin", False),
        "tier":     user.tier,
    }


# ── Change password ───────────────────────────────────────────────────────────

class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Yangi parol kamida 8 ta belgi bo'lsin.")
        if len(v) > 128:
            raise ValueError("Parol 128 belgidan oshmasligi kerak.")
        return v


@router.post("/change-password")
def change_password(
    body: ChangePasswordIn,
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(400, "Joriy parol noto'g'ri.")

    if body.new_password == body.current_password:
        raise HTTPException(400, "Yangi parol joriy parol bilan bir xil bo'lmasin.")

    if user.prev_password_hash and verify_password(body.new_password, user.prev_password_hash):
        raise HTTPException(400, "Oldingi parolni qayta ishlata olmaysiz.")

    # Oylik limit: max 2 ta o'zgartirish
    cur_month = _now().strftime("%Y-%m")
    if user.pw_change_month != cur_month:
        user.pw_change_count = 0
        user.pw_change_month = cur_month
    if (user.pw_change_count or 0) >= 2:
        raise HTTPException(429, "Bir oyda faqat 2 marta parol almashtirish mumkin.")

    user.prev_password_hash = user.password_hash
    user.password_hash      = hash_password(body.new_password)
    user.pw_change_count    = (user.pw_change_count or 0) + 1
    user.pw_change_month    = cur_month
    db.commit()

    remaining = 2 - user.pw_change_count
    logger.info("Password changed: user_id=%s remaining_changes=%d", user.id, remaining)
    return {
        "ok": True,
        "message": f"Parol muvaffaqiyatli o'zgartirildi. Bu oy yana {remaining} marta o'zgartirish mumkin.",
    }
