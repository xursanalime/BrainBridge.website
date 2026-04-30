from datetime import datetime, timezone
from sqlalchemy.orm import Session
from models import User

def add_xp(db: Session, user: User, amount: int):
    """Add XP to user and handle daily/monthly resets if needed."""
    now = datetime.now(timezone.utc)
    
    # 1) Handle resets
    if not user.last_xp_reset:
        user.last_xp_reset = now
        user.daily_xp = 0
        user.monthly_xp = 0
        user.daily_reviews = 0
        user.daily_sentences = 0
    else:
        last = user.last_xp_reset
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
            
        # Daily reset
        if now.date() > last.date():
            user.daily_xp = 0
            user.daily_reviews = 0
            user.daily_sentences = 0
        
        # Monthly reset
        if now.year > last.year or now.month > last.month:
            user.monthly_xp = 0
            
        user.last_xp_reset = now

    # 2) Add XP and Coins (1 coin per 10 XP)
    user.total_xp += amount
    user.daily_xp += amount
    user.monthly_xp += amount
    
    coins_earned = max(1, amount // 10)
    user.coins = (getattr(user, 'coins', 0) or 0) + coins_earned
    
    db.commit()
    db.refresh(user)
    return user
