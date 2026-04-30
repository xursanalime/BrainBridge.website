from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List

from db import get_db
from routes.auth import current_user
from services import word_service
from services.xp_service import add_xp

router = APIRouter(prefix="/words", tags=["words"])


class AddIn(BaseModel):
    raw: str


class SingleWordIn(BaseModel):
    word: str
    translation: str


class BulkWordItem(BaseModel):
    word: str
    translation: str


class BulkIn(BaseModel):
    words: List[BulkWordItem]


class UpdateIn(BaseModel):
    word:        Optional[str] = None
    translation: Optional[str] = None


class ReviewIn(BaseModel):
    correct: bool


# ── Words ─────────────────────────────────────────────────────────────────────

@router.get("")
def list_words(
    box:    Optional[int] = Query(None),
    search: str           = Query(""),
    sort:   str           = Query("date"),
    limit:  int           = Query(200),
    db: Session = Depends(get_db),
    user=Depends(current_user)
):
    words = word_service.get_words(db, user.id, box, search, sort)
    return {"words": words[:limit], "total": len(words)}


@router.get("/list")
def list_words_alt(
    box:    Optional[int] = Query(None),
    search: str           = Query(""),
    sort:   str           = Query("date"),
    db: Session = Depends(get_db),
    user=Depends(current_user)
):
    return word_service.get_words(db, user.id, box, search, sort)


@router.post("")
def add_single(body: SingleWordIn, db: Session = Depends(get_db), user=Depends(current_user)):
    raw = f"{body.word} - {body.translation}"
    try:
        res = word_service.add_words(db, user.id, raw)
        add_xp(db, user, 5) # Adding a word
        return res
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/bulk")
def add_bulk(body: BulkIn, db: Session = Depends(get_db), user=Depends(current_user)):
    raw = "\n".join(f"{item.word} - {item.translation}" for item in body.words)
    try:
        res = word_service.add_words(db, user.id, raw)
        # 5 XP per word in bulk
        count = len(body.words)
        add_xp(db, user, 5 * count)
        return res
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/add")
def add_raw(body: AddIn, db: Session = Depends(get_db), user=Depends(current_user)):
    try:
        res = word_service.add_words(db, user.id, body.raw)
        add_xp(db, user, 5) 
        return res
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/stats")
def stats(db: Session = Depends(get_db), user=Depends(current_user)):
    s = word_service.get_stats(db, user.id)
    return {
        "total":    s["total"],
        "due":      s["due"],
        "mastered": s["mastered"],
        "streak":   s["streak"],
        "boxes":    s["box_dist"],
    }


@router.get("/due")
def due(db: Session = Depends(get_db), user=Depends(current_user)):
    words = word_service.get_due_words(db, user.id)
    return [word_service._serialize(w) for w in words]


@router.post("/{word_id}/review")
def review(word_id: int, body: ReviewIn, db: Session = Depends(get_db), user=Depends(current_user)):
    try:
        result = word_service.advance(db, user.id, word_id, body.correct)
        user.daily_reviews = (getattr(user, 'daily_reviews', 0) or 0) + 1
        if body.correct:
            add_xp(db, user, 10) # XP for correct review
        result["new_box"] = result["box"]
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.put("/{word_id}")
@router.patch("/{word_id}")
def update(word_id: int, body: UpdateIn, db: Session = Depends(get_db), user=Depends(current_user)):
    try:
        return word_service.update_word(db, user.id, word_id, body.word, body.translation)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.delete("/{word_id}")
def delete(word_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    try:
        word_service.delete_word(db, user.id, word_id)
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(404, str(e))


# ── Tests ─────────────────────────────────────────────────────────────────────

class WriteIn(BaseModel):
    word_id: int
    answer:  str


class QuizIn(BaseModel):
    word_id: int
    chosen:  str
    mode:    str = "uz2en"


@router.post("/write")
def write_test(body: WriteIn, db: Session = Depends(get_db), user=Depends(current_user)):
    try:
        res = word_service.submit_write(db, user.id, body.word_id, body.answer)
        if res.get("correct"):
            add_xp(db, user, 10)
        return res
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/quiz/{word_id}")
def quiz_get(word_id: int, mode: str = "uz2en", db: Session = Depends(get_db), user=Depends(current_user)):
    try:
        return word_service.get_quiz(db, user.id, word_id, mode)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/quiz")
def quiz_submit(body: QuizIn, db: Session = Depends(get_db), user=Depends(current_user)):
    try:
        res = word_service.submit_quiz(db, user.id, body.word_id, body.chosen, body.mode)
        if res.get("correct"):
            add_xp(db, user, 10)
        return res
    except ValueError as e:
        raise HTTPException(404, str(e))
