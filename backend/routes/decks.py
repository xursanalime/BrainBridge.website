import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from db import get_db
from models import Deck, DeckWord, Word, User
from routes.auth import current_user

router = APIRouter(prefix="/decks", tags=["decks"])
logger = logging.getLogger("brainbridge.decks")

# ── Schemas ───────────────────────────────────────────────────────────────────

class DeckWordOut(BaseModel):
    id: int
    word: str
    translation: str

    class Config:
        from_attributes = True

class DeckOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    icon: Optional[str] = None
    word_count: int

# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[DeckOut])
def list_decks(db: Session = Depends(get_db)):
    """Barcha tayyor lug'at to'plamlarini qaytaradi."""
    decks = db.query(Deck).all()
    result = []
    for d in decks:
        count = db.query(DeckWord).filter(DeckWord.deck_id == d.id).count()
        result.append({
            "id": d.id,
            "title": d.title,
            "description": d.description,
            "icon": d.icon,
            "word_count": count
        })
    return result

@router.post("/{deck_id}/add")
def add_deck_to_user(deck_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """To'plamdagi so'zlarni foydalanuvchi lug'atiga qo'shish."""
    deck = db.query(Deck).filter(Deck.id == deck_id).first()
    if not deck:
        raise HTTPException(status_code=404, detail="To'plam topilmadi")

    deck_words = db.query(DeckWord).filter(DeckWord.deck_id == deck_id).all()
    if not deck_words:
        raise HTTPException(status_code=400, detail="To'plam bo'sh")
        
    # Faqat yangi so'zlarni qo'shish (takrorlanmasligi uchun)
    existing_words = {w.word.lower() for w in db.query(Word).filter(Word.user_id == user.id).all()}
    
    added = 0
    for dw in deck_words:
        if dw.word.lower() not in existing_words:
            new_word = Word(
                user_id=user.id,
                word=dw.word.strip(),
                translation=dw.translation.strip(),
                box=0,
                ease_factor=2.5,
                interval=0,
                repetitions=0
            )
            db.add(new_word)
            existing_words.add(dw.word.lower())
            added += 1
            
    db.commit()
    return {"ok": True, "added": added, "total_in_deck": len(deck_words)}
