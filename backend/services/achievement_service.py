from sqlalchemy.orm import Session
from models import User, UserAchievement, Word

ACHIEVEMENTS_CONFIG = {
    "streak": {
        "title": "Streak Legend",
        "icon": "🔥",
        "tiers": [3, 7, 30, 100],
        "unit": "kun"
    },
    "vocabulary": {
        "title": "Vocabulary Titan",
        "icon": "📚",
        "tiers": [50, 100, 500, 1000],
        "unit": "so'z"
    },
    "mastery": {
        "title": "Master of Wisdom",
        "icon": "🎓",
        "tiers": [10, 50, 200, 500],
        "unit": "o'rganildi"
    },
    "xp_legend": {
        "title": "XP Legend",
        "icon": "💎",
        "tiers": [1000, 5000, 20000, 50000],
        "unit": "XP"
    }
}


def check_achievements(db: Session, user_id: int):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return []

    unlocked = [a.achievement_id for a in db.query(UserAchievement).filter_by(user_id=user_id).all()]
    new_unlocked = []

    stats = {
        "streak":     user.streak,
        "vocabulary": db.query(Word).filter_by(user_id=user_id).count(),
        "mastery":    db.query(Word).filter_by(user_id=user_id, box=5).count(),
        "xp_legend":  user.total_xp,
    }

    for aid, config in ACHIEVEMENTS_CONFIG.items():
        current_val = stats.get(aid, 0)
        for tier in config["tiers"]:
            tier_id = f"{aid}_{tier}"
            if tier_id not in unlocked and current_val >= tier:
                _unlock(db, user_id, tier_id, new_unlocked)

    if new_unlocked:
        db.commit()

    return new_unlocked


def _unlock(db, user_id, aid, list_to_add):
    ua = UserAchievement(user_id=user_id, achievement_id=aid)
    db.add(ua)
    list_to_add.append(aid)


def get_all_achievements(db: Session, user_id: int):
    user = db.query(User).filter_by(id=user_id).first()
    unlocked_ids = [a.achievement_id for a in db.query(UserAchievement).filter_by(user_id=user_id).all()]

    stats = {
        "streak":     user.streak,
        "vocabulary": db.query(Word).filter_by(user_id=user_id).count(),
        "mastery":    db.query(Word).filter_by(user_id=user_id, box=5).count(),
        "xp_legend":  user.total_xp,
    }

    res = []
    for aid, config in ACHIEVEMENTS_CONFIG.items():
        current_val = stats.get(aid, 0)

        current_tier_idx = -1
        for i, tier in enumerate(config["tiers"]):
            if f"{aid}_{tier}" in unlocked_ids:
                current_tier_idx = i

        next_tier_idx = current_tier_idx + 1
        is_max = next_tier_idx >= len(config["tiers"])
        target_val = config["tiers"][next_tier_idx] if not is_max else config["tiers"][-1]
        progress_pct = min(100, int((current_val / target_val) * 100)) if target_val > 0 else 0

        res.append({
            "id":           aid,
            "title":        config["title"],
            "icon":         config["icon"],
            "current_val":  current_val,
            "target_val":   target_val,
            "unit":         config["unit"],
            "progress_pct": progress_pct,
            "level":        current_tier_idx + 1,
            "is_max":       is_max,
            "unlocked":     current_tier_idx >= 0,
        })
    return res
