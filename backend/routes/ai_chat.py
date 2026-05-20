"""
AI Chat routes — BrainBot v3.1
=================================
Yaxshilanishlar:
- Umumiy GeminiClient ishlatiladi (async httpx)
- Logging kuchaytirildi
- Input validation qo'shildi
- Error handling yaxshilandi
"""
import logging
import json
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from db import get_db
from routes.auth import current_user
from models import AIChatSession, AIChatMessage
import services.gemini_client as gemini

router = APIRouter(prefix="/ai", tags=["ai-chat"])
logger = logging.getLogger("brainbridge.ai_chat")

AI_ERROR_MESSAGE = "AI vaqtincha ishlamayapti, keyinroq urinib ko'ring."

# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are BrainBot — a friendly and encouraging English teacher for Uzbek learners. "
    "You are integrated into the BrainBridge language learning platform.\n\n"
    "Your priorities are: correct grammar and usage, clear explanations, and helpful examples.\n"
    "Always answer in the language used by the user, especially Uzbek when the user writes in Uzbek.\n\n"
    "Your specialties:\n"
    "1. Grammar and usage — explain errors clearly with short, simple examples\n"
    "2. Corrections — show the wrong phrase and the corrected version\n"
    "3. Writing support — help with sentences, emails, stories, and messages\n"
    "4. Vocabulary — explain word meaning, collocations, and example usage\n\n"
    "Language rules:\n"
    "- Be respectful, patient, and encouraging\n"
    "- Use clear Uzbek when the user writes in Uzbek\n"
    "- Use short sentences and simple language for explanations\n"
    "- Provide at least one corrected version when the user asks for writing help\n"
    "- Avoid long, technical descriptions unless necessary"
)


# ── Schemas ───────────────────────────────────────────────────────────────────

class CreateChatIn(BaseModel):
    name: Optional[str] = "Yangi suhbat"


class RenameChatIn(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Suhbat nomi bo'sh bo'lmasligi kerak.")
        return v[:100]


class SendMessageIn(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Xabar bo'sh bo'lmasligi kerak.")
        if len(v) > 4000:
            raise ValueError("Xabar 4000 belgidan oshmasligi kerak.")
        return v


class ExtractWordsIn(BaseModel):
    image_b64: Optional[str] = None
    text:      Optional[str] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_session(db: Session, session_id: int, user_id: int) -> AIChatSession:
    s = db.query(AIChatSession).filter_by(id=session_id, user_id=user_id).first()
    if not s:
        raise HTTPException(404, "Chat topilmadi.")
    return s


def _serialize_session(s: AIChatSession) -> dict:
    return {
        "id":         s.id,
        "name":       s.name,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


def _serialize_message(m: AIChatMessage) -> dict:
    return {
        "id":         m.id,
        "session_id": m.session_id,
        "role":       m.role,
        "content":    m.content,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/chats")
def list_chats(db: Session = Depends(get_db), user=Depends(current_user)):
    sessions = (
        db.query(AIChatSession)
        .filter_by(user_id=user.id)
        .order_by(AIChatSession.updated_at.desc())
        .all()
    )
    return [_serialize_session(s) for s in sessions]


@router.post("/chats", status_code=201)
def create_chat(body: CreateChatIn, db: Session = Depends(get_db), user=Depends(current_user)):
    s = AIChatSession(user_id=user.id, name=(body.name or "Yangi suhbat")[:100])
    db.add(s)
    db.commit()
    db.refresh(s)
    logger.info("New chat session: user_id=%s session_id=%s", user.id, s.id)
    return _serialize_session(s)


@router.patch("/chats/{session_id}")
def rename_chat(
    session_id: int,
    body: RenameChatIn,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    s = _get_session(db, session_id, user.id)
    s.name = body.name
    db.commit()
    return _serialize_session(s)


@router.delete("/chats/{session_id}")
def delete_chat(session_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    s = _get_session(db, session_id, user.id)
    db.delete(s)
    db.commit()
    return {"ok": True}


@router.get("/chats/{session_id}/messages")
def get_messages(session_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    s = _get_session(db, session_id, user.id)
    return [_serialize_message(m) for m in s.messages]


@router.post("/chats/{session_id}/send")
async def send_message(
    session_id: int,
    body: SendMessageIn,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    s = _get_session(db, session_id, user.id)

    # Foydalanuvchi xabarini saqlash
    user_msg = AIChatMessage(session_id=s.id, role="user", content=body.content)
    db.add(user_msg)
    db.commit()

    # So'nggi 20 xabar kontekst sifatida
    history = [
        {"role": m.role, "content": m.content}
        for m in s.messages[-20:]
    ]

    # AI javob (async)
    ai_text = await gemini.generate_text(
        prompt="",  # history orqali uzatiladi
        history=history,
        model="flash_25",
        system_prompt=SYSTEM_PROMPT,
    )

    if not ai_text:
        logger.warning("AI chat failed: session_id=%s user_id=%s", session_id, user.id)
        ai_text = AI_ERROR_MESSAGE

    # Chat nomini birinchi xabardan avtomatik hosil qilish
    if len(s.messages) <= 2 and s.name == "Yangi suhbat":
        words = body.content.strip().split()[:6]
        s.name = " ".join(words)[:80] or "Yangi suhbat"

    ai_msg = AIChatMessage(session_id=s.id, role="assistant", content=ai_text)
    db.add(ai_msg)
    db.commit()
    db.refresh(s)

    return {
        "user_message":      _serialize_message(user_msg),
        "assistant_message": _serialize_message(ai_msg),
        "session_name":      s.name,
    }


# ── Word extraction ───────────────────────────────────────────────────────────

@router.post("/extract-words")
async def extract_words(body: ExtractWordsIn, user=Depends(current_user)):
    """Rasm yoki matndan inglizcha so'zlarni chiqarish."""
    if not gemini.is_available:
        raise HTTPException(503, "AI xizmati hozir mavjud emas.")

    if body.image_b64:
        prompt = (
            "Extract all English words from this base64-encoded image. "
            "For each word, provide the Uzbek translation. "
            "Respond ONLY with a JSON array, no markdown:\n"
            '[{"word": "example", "translation": "misol"}, ...]\n\n'
            f"Image (base64): data:image/jpeg;base64,{body.image_b64}"
        )
    elif body.text:
        if len(body.text) > 5000:
            raise HTTPException(400, "Matn 5000 belgidan oshmasligi kerak.")
        prompt = (
            "Extract all notable English vocabulary words from this text that a learner should study. "
            "Provide Uzbek translations. "
            "Respond ONLY with a JSON array, no markdown:\n"
            '[{"word": "example", "translation": "misol"}, ...]\n\n'
            f"Text: {body.text}"
        )
    else:
        raise HTTPException(400, "image_b64 yoki text kerak.")

    try:
        raw_text = await gemini.generate_text(
            prompt=prompt,
            model="flash_25",
            temperature=0.1,
            max_tokens=900,
        )
        if not raw_text:
            raise HTTPException(503, AI_ERROR_MESSAGE)

        raw = re.sub(r"^```(?:json)?\s*", "", raw_text)
        raw = re.sub(r"\s*```$", "", raw).strip()
        # Array ni qidirish
        arr_match = re.search(r"\[[\s\S]*\]", raw)
        if arr_match:
            raw = arr_match.group(0)

        words = json.loads(raw)
        if not isinstance(words, list):
            raise ValueError("Not a list")

        result = [
            {
                "word":        str(w.get("word", "")).strip(),
                "translation": str(w.get("translation", "")).strip(),
            }
            for w in words
            if w.get("word") and w.get("translation")
        ]
        logger.info("Words extracted: user_id=%s count=%d", user.id, len(result))
        return {"words": result}

    except json.JSONDecodeError as exc:
        logger.error("Word extraction JSON error: %s", exc)
        raise HTTPException(500, "AI javobi noto'g'ri formatda.")
    except Exception as exc:
        logger.error("Word extraction error: %s", exc)
        raise HTTPException(503, AI_ERROR_MESSAGE)
