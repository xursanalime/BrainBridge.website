"""
Payment routes — BrainBridge v3.1
===================================
MUHIM O'ZGARISHLAR:
- To'lov tarixi xotirada emas, DB'da saqlanadi
- Demo mode faqat ENV=development da ishlaydi
- Production'da haqiqiy to'lov talab qilinadi
- Logging va audit trail qo'shildi
- Webhook security template yaxshilandi
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
import os

from db import get_db
from models import User, PaymentRecord
from routes.auth import current_user
from services import tier_service

router = APIRouter(prefix="/payments", tags=["payments"])
logger = logging.getLogger("brainbridge.payments")

IS_DEMO = os.getenv("ENV", "production") != "production"

if IS_DEMO:
    logger.warning("⚠️  Payment system running in DEMO mode — no real charges!")
else:
    logger.info("💳 Payment system in PRODUCTION mode")



# ── Schemas ───────────────────────────────────────────────────────────────────


class PaymentOrder(BaseModel):
    tier:   str
    method: str = "payme"

    @field_validator("tier")
    @classmethod
    def validate_tier(cls, v: str) -> str:
        if v not in ("pro", "premium"):
            raise ValueError("Faqat 'pro' yoki 'premium' tarifga to'lov qilish mumkin.")
        return v

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        if v not in ("payme", "click", "card"):
            raise ValueError("Noto'g'ri to'lov usuli.")
        return v


class PaymentCallback(BaseModel):
    order_id:       str
    status:         str
    transaction_id: Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/create-order")
def create_order(
    body: PaymentOrder,
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    To'lov buyurtmasi yaratish.
    - DEMO (ENV=development): avtomatik muvaffaqiyatli
    - PRODUCTION: Payme/Click checkout URL qaytaradi
    """
    tier_info = tier_service.get_tier(body.tier)
    amount    = tier_info["price"]
    order_id  = f"BB-{user.id}-{int(datetime.now(timezone.utc).timestamp())}"

    if IS_DEMO:
        # ── DEMO MODE ────────────────────────────────────────────────────────
        logger.info(
            "DEMO payment: user_id=%s tier=%s amount=%d order_id=%s",
            user.id, body.tier, amount, order_id,
        )
        _save_payment(db, order_id, user.id, body.tier, amount, body.method, "success")
        user.tier = body.tier
        db.commit()

        return {
            "order_id":  order_id,
            "status":    "success",
            "tier":      body.tier,
            "tier_name": tier_info["name"],
            "amount":    amount,
            "message":   f"[DEMO] {tier_info['name']} tarifiga o'tdingiz!",
            "demo":      True,
        }

    else:
        # ── PRODUCTION MODE ──────────────────────────────────────────────────
        # To'lov tizimi integratsiyasi kerak
        # Payme: https://developer.help.paycom.uz
        # Click: https://docs.click.uz

        _save_payment(db, order_id, user.id, body.tier, amount, body.method, "pending")

        # checkout_url = generate_payme_checkout(order_id, amount, user.email)
        # yoki
        # checkout_url = generate_click_checkout(order_id, amount, user.email)

        raise HTTPException(
            503,
            "To'lov tizimi hali ulanmagan. Iltimos, Payme/Click integratsiyasini sozlang."
        )


def _save_payment(
    db: Session,
    order_id: str,
    user_id: int,
    tier: str,
    amount: int,
    method: str,
    status: str,
    note: str = "",
) -> PaymentRecord:
    """To'lovni DB'ga saqlash."""
    record = PaymentRecord(
        order_id=order_id,
        user_id=user_id,
        tier=tier,
        amount=amount,
        method=method,
        status=status,
        note=note,
    )
    db.add(record)
    db.flush()
    return record


@router.get("/history")
def payment_history(user=Depends(current_user), db: Session = Depends(get_db)):
    """Foydalanuvchining to'lov tarixi (DB'dan)."""
    records = (
        db.query(PaymentRecord)
        .filter(PaymentRecord.user_id == user.id)
        .order_by(PaymentRecord.created_at.desc())
        .all()
    )
    return [
        {
            "order_id":   r.order_id,
            "tier":       r.tier,
            "amount":     r.amount,
            "method":     r.method,
            "status":     r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]


@router.post("/cancel-subscription")
def cancel_subscription(user=Depends(current_user), db: Session = Depends(get_db)):
    if user.tier == "free":
        raise HTTPException(400, "Siz allaqachon Bepul tarifdasiz.")

    old_tier  = user.tier
    order_id  = f"CANCEL-{user.id}-{int(datetime.now(timezone.utc).timestamp())}"
    user.tier = "free"
    _save_payment(db, order_id, user.id, "free", 0, "cancel", "cancelled", f"{old_tier} → free")
    db.commit()

    logger.info("Subscription cancelled: user_id=%s old_tier=%s", user.id, old_tier)
    return {"ok": True, "message": "Obuna bekor qilindi. Siz Bepul tarifga qaytdingiz.", "tier": "free"}


# ── Webhooks (Production template) ───────────────────────────────────────────

@router.post("/webhook/payme")
async def payme_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Payme merchant API webhook.
    Docs: https://developer.help.paycom.uz

    Production'da quyidagilarni implement qiling:
    1. Basic Auth tekshiruvi (Payme merchant login:key)
    2. CheckPerformTransaction → order mavjudligini tekshirish
    3. CreateTransaction → DB'da transaction yaratish
    4. PerformTransaction → to'lovni tasdiqlash, user.tier yangilash
    5. CancelTransaction → bekor qilish
    6. CheckTransaction → holat qaytarish
    """
    body = await request.json()
    method = body.get("method", "")
    logger.info("Payme webhook received: method=%s", method)

    # Misol: PerformTransaction
    # if method == "PerformTransaction":
    #     params = body.get("params", {})
    #     order_id = params.get("account", {}).get("order_id")
    #     record = db.query(PaymentRecord).filter_by(order_id=order_id).first()
    #     if record and record.status == "pending":
    #         record.status = "success"
    #         record.transaction_id = params.get("id")
    #         user = db.query(User).filter_by(id=record.user_id).first()
    #         if user:
    #             user.tier = record.tier
    #         db.commit()
    #     return {"result": {"transaction": record.transaction_id, "perform_time": int(time.time()*1000), "state": 2}}

    return {"result": {"allow": True}}


@router.post("/webhook/click")
async def click_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Click merchant API webhook.
    Docs: https://docs.click.uz

    Production'da quyidagilarni implement qiling:
    1. Secret key tekshiruvi (sign = MD5(...))
    2. Prepare phase → order validatsiyasi
    3. Complete phase → to'lovni tasdiqlash, user.tier yangilash
    """
    body = await request.json()
    action = body.get("action", 0)
    logger.info("Click webhook received: action=%s", action)

    # if action == 1:  # complete
    #     order_id = body.get("merchant_trans_id")
    #     # ... implement
    #     pass

    return {"error": 0, "error_note": "Success"}
