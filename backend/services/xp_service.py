from datetime import datetime, timezone
from sqlalchemy.orm import Session
from models import User

def _check_resets(db: Session, user: User):
    """Check and apply daily/monthly XP resets if the date has changed."""
    now = datetime.now(timezone.utc)

    if not user.last_xp_reset:
        user.last_xp_reset = now
        user.daily_xp = 0
        user.monthly_xp = 0
        user.daily_reviews = 0
        db.commit()
        return

    last = user.last_xp_reset
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)

    changed = False
    # Daily reset
    if now.date() > last.date():
        user.daily_xp = 0
        user.daily_reviews = 0
        changed = True

    # Monthly reset
    if now.year > last.year or now.month > last.month:
        user.monthly_xp = 0
        changed = True

    if changed:
        user.last_xp_reset = now
        db.commit()

def ensure_resets(db: Session, user: User):
    """Public helper: ensure daily/monthly counters are current."""
    _check_resets(db, user)

def add_xp(db: Session, user: User, amount: int):
    """Add XP to user and handle daily/monthly resets if needed."""
    _check_resets(db, user)

    user.total_xp   += amount
    user.daily_xp   += amount
    user.monthly_xp += amount

    coins_earned = max(1, amount // 10)
    user.coins = (getattr(user, 'coins', 0) or 0) + coins_earned

    db.commit()
    db.refresh(user)
    return user
