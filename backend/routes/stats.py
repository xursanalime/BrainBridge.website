from fastapi import APIRouter, Depends, Query, File, UploadFile, HTTPException
from pydantic import BaseModel
import shutil, os, uuid
from sqlalchemy.orm import Session
from typing import List, Optional
from db import get_db
from routes.auth import current_user
from models import User
from sqlalchemy import desc
from services import achievement_service
from services.xp_service import add_xp

router = APIRouter(prefix="/stats", tags=["stats"])

class RewardIn(BaseModel):
    action: str
    amount: int

@router.get("/leaderboard")
def get_leaderboard(
    period: str = Query("alltime", enum=["daily", "monthly", "alltime"]),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    if period == "daily":
        order_col = User.daily_xp
    elif period == "monthly":
        order_col = User.monthly_xp
    else:
        order_col = User.total_xp
    
    users = db.query(User).order_by(desc(order_col)).limit(limit).all()
    
    res = []
    for i, u in enumerate(users):
        res.append({
            "rank": i + 1,
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "xp": getattr(u, f"{period}_xp") if period != "alltime" else u.total_xp,
            "streak": u.streak,
            "avatar_url": u.avatar_url
        })
    return res

@router.get("/me")
def get_my_stats(user=Depends(current_user), db: Session = Depends(get_db)):
    # Auto check achievements
    new_achs = achievement_service.check_achievements(db, user.id)
    
    # Calculate rank
    total_users = db.query(User).count()
    rank = db.query(User).filter(User.total_xp > user.total_xp).count() + 1
    
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "total_xp": user.total_xp,
        "daily_xp": user.daily_xp,
        "monthly_xp": user.monthly_xp,
        "streak": user.streak,
        "coins": user.coins,
        "streak_freezes": user.streak_freezes,
        "rank": rank,
        "total_users": total_users,
        "avatar_url": user.avatar_url,
        "new_achievements": new_achs,
        "daily_reviews": user.daily_reviews,
        "daily_sentences": user.daily_sentences,
        "goal_reviews": user.goal_reviews,
        "goal_sentences": user.goal_sentences,
        "goal_xp": user.goal_xp
    }

class BuyItemIn(BaseModel):
    item_id: str

@router.post("/shop/buy")
def buy_item(body: BuyItemIn, user=Depends(current_user), db: Session = Depends(get_db)):
    if body.item_id == "streak_freeze":
        cost = 50
        if user.coins < cost:
            raise HTTPException(400, "Tangalar yetarli emas.")
        user.coins -= cost
        user.streak_freezes += 1
        db.commit()
        return {"message": "Streak Freeze sotib olindi!", "coins": user.coins, "streak_freezes": user.streak_freezes}
    
    raise HTTPException(400, "Noma'lum mahsulot.")

@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Fayl rasm bo'lishi kerak")
    
    # Validate size (2MB)
    MAX_SIZE = 2 * 1024 * 1024
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="Rasm hajmi 2MB dan oshmasligi kerak")
    await file.seek(0)
    
    # Save file
    ext = os.path.splitext(file.filename)[1]
    if not ext: ext = ".jpg"
    filename = f"{uuid.uuid4()}{ext}"
    
    uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "avatars"))
    os.makedirs(uploads_dir, exist_ok=True)
    filepath = os.path.join(uploads_dir, filename)
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Update DB
    user.avatar_url = f"/api/uploads/avatars/{filename}"
    db.commit()
    
    return {"avatar_url": user.avatar_url}

@router.get("/achievements")
def get_my_achievements(user=Depends(current_user), db: Session = Depends(get_db)):
    # Check for new ones first
    achievement_service.check_achievements(db, user.id)
    return achievement_service.get_all_achievements(db, user.id)
@router.post("/reward")
def give_reward(body: RewardIn, user=Depends(current_user), db: Session = Depends(get_db)):
    add_xp(db, user, body.amount)
    
    # Increment specific stats
    if body.action == "spelling_correct":
        user.spelling_count += 1
    elif body.action == "ai_sentence_correct":
        user.ai_sentence_count += 1
    
    db.commit()
    new_achs = achievement_service.check_achievements(db, user.id)
    return {"ok": True, "total_xp": user.total_xp, "new_achievements": new_achs}

class UpdateNameIn(BaseModel):
    full_name: str

@router.post("/me/name")
def update_my_name(body: UpdateNameIn, user=Depends(current_user), db: Session = Depends(get_db)):
    if not body.full_name.strip():
        raise HTTPException(400, "Ism bo'sh bo'lmasligi kerak.")
    user.full_name = body.full_name.strip()
    db.commit()
    return {"ok": True, "full_name": user.full_name}

class UpdateGoalsIn(BaseModel):
    goal_reviews: int
    goal_sentences: int
    goal_xp: int

@router.post("/me/goals")
def update_my_goals(body: UpdateGoalsIn, user=Depends(current_user), db: Session = Depends(get_db)):
    user.goal_reviews = max(1, body.goal_reviews)
    user.goal_sentences = max(1, body.goal_sentences)
    user.goal_xp = max(10, body.goal_xp)
    db.commit()
    return {"ok": True}
