"""
Admin routes — BrainBridge v3.1
==================================
Yaxshilanishlar:
- Audit logging (kim nimani o'zgartirdi)
- Input validation kuchaytirildi
- Statistika kengaytirildi
- Logging qo'shildi
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from sqlalchemy import func

from db import get_db
from models import User
from routes.auth import current_user

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger("brainbridge.admin")


# ── Admin dependency ──────────────────────────────────────────────────────────

def require_admin(user=Depends(current_user)):
    if not getattr(user, "is_admin", False):
        logger.warning("Unauthorized admin access attempt: user_id=%s", user.id)
        raise HTTPException(403, "Admin huquqi talab qilinadi.")
    return user


# ── Schemas ───────────────────────────────────────────────────────────────────

class UpdateUserIn(BaseModel):
    coins:    Optional[int]  = None
    total_xp: Optional[int]  = None
    is_admin: Optional[bool] = None

    @field_validator("coins")
    @classmethod
    def validate_coins(cls, v):
        if v is not None and (v < 0 or v > 999999):
            raise ValueError("coins 0–999999 oralig'ida bo'lishi kerak.")
        return v

    @field_validator("total_xp")
    @classmethod
    def validate_xp(cls, v):
        if v is not None and (v < 0 or v > 9999999):
            raise ValueError("total_xp 0–9999999 oralig'ida bo'lishi kerak.")
        return v


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/stats")
def admin_stats(admin=Depends(require_admin), db: Session = Depends(get_db)):
    """Platform statistikasi."""
    now = datetime.now(timezone.utc)
    today     = now.replace(hour=0, minute=0, second=0, microsecond=0)
    this_week = today - timedelta(days=7)
    this_month = today.replace(day=1)

    total_users   = db.query(func.count(User.id)).scalar() or 0
    new_today     = db.query(func.count(User.id)).filter(User.created_at >= today).scalar() or 0
    new_week      = db.query(func.count(User.id)).filter(User.created_at >= this_week).scalar() or 0
    new_month     = db.query(func.count(User.id)).filter(User.created_at >= this_month).scalar() or 0
    total_coins   = db.query(func.sum(User.coins)).scalar() or 0
    total_xp      = db.query(func.sum(User.total_xp)).scalar() or 0
    admin_count   = db.query(func.count(User.id)).filter(User.is_admin == True).scalar() or 0

    logger.info("Admin stats accessed: admin_id=%s", admin.id)
    return {
        "ok":           True,
        "total_users":  total_users,
        "admin_count":  admin_count,
        "new_today":    new_today,
        "new_week":     new_week,
        "new_month":    new_month,
        "total_coins":  total_coins,
        "total_xp":     total_xp,
    }


@router.get("/users")
def admin_users(
    limit:  int = 100,
    offset: int = 0,
    search: str = "",
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Foydalanuvchilar ro'yxati — pagination va qidiruv bilan."""
    q = db.query(User)
    if search:
        q = q.filter(User.email.ilike(f"%{search}%"))
    total = q.count()
    users = q.order_by(User.id.desc()).offset(offset).limit(min(limit, 200)).all()

    result = [
        {
            "id":         u.id,
            "email":      u.email,
            "full_name":  u.full_name,
            "coins":      u.coins,
            "total_xp":   u.total_xp,
            "streak":     u.streak,
            "is_admin":   getattr(u, "is_admin", False),
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]
    return {"ok": True, "users": result, "total": total, "limit": limit, "offset": offset}


@router.post("/users/{user_id}/update")
def admin_update_user(
    user_id: int,
    body: UpdateUserIn,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Foydalanuvchi ma'lumotlarini yangilash — audit log bilan."""
    if user_id == admin.id and body.is_admin is False:
        raise HTTPException(400, "O'zingizni adminlikdan olib tashlay olmaysiz.")

    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(404, "Foydalanuvchi topilmadi.")

    changes = {}
    if body.coins is not None and u.coins != body.coins:
        changes["coins"] = {"old": u.coins, "new": body.coins}
        u.coins = body.coins
    if body.total_xp is not None and u.total_xp != body.total_xp:
        changes["total_xp"] = {"old": u.total_xp, "new": body.total_xp}
        u.total_xp = body.total_xp
    if body.is_admin is not None and u.is_admin != body.is_admin:
        changes["is_admin"] = {"old": u.is_admin, "new": body.is_admin}
        u.is_admin = body.is_admin

    db.commit()

    if changes:
        logger.info(
            "Admin update: admin_id=%s target_user_id=%s changes=%s",
            admin.id, user_id, changes,
        )

    return {"ok": True, "message": "Muvaffaqiyatli yangilandi.", "changes": changes}


@router.delete("/users/{user_id}")
def admin_delete_user(
    user_id: int,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    if user_id == admin.id:
        raise HTTPException(400, "O'zingizni o'chira olmaysiz.")

    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(404, "Foydalanuvchi topilmadi.")

    email = u.email
    db.delete(u)
    db.commit()

    logger.warning("Admin delete: admin_id=%s deleted_user_id=%s email=%s", admin.id, user_id, email)
    return {"ok": True, "message": "O'chirildi."}
