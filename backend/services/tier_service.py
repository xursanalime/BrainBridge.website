"""
Tier Service — BrainBridge v3.1
=================================
Tarif rejalari va limitlar.
"""

TIERS = {
    "free": {
        "name": "Bepul",
        "price": 0,
        "max_words": 500,
        "ai_chat": False,
        "sentence_builder": False,
        "super_memory": False,
        "features": ["Leitner algoritmi", "Yozish va Quiz testlar", "Leaderboard"],
    },
    "pro": {
        "name": "Pro",
        "price": 29900,  # so'm/oy
        "max_words": 5000,
        "ai_chat": True,
        "sentence_builder": True,
        "super_memory": True,
        "features": [
            "Barcha Bepul xususiyatlar",
            "AI BrainBot chat",
            "Sentence Builder (AI gap tekshirish)",
            "Super Memory (Mnemonika)",
            "5000 ta so'z limiti",
        ],
    },
    "premium": {
        "name": "Premium",
        "price": 49900,  # so'm/oy
        "max_words": -1,  # cheksiz
        "ai_chat": True,
        "sentence_builder": True,
        "super_memory": True,
        "features": [
            "Barcha Pro xususiyatlar",
            "Cheksiz so'z limiti",
            "Ustuvor AI javoblar",
            "Premium badge",
        ],
    },
}


def get_tier(tier_id: str) -> dict:
    """Tarif ma'lumotlarini qaytarish."""
    if tier_id not in TIERS:
        return TIERS["free"]
    return TIERS[tier_id]


def get_all_tiers() -> list[dict]:
    """Barcha tariflarni qaytarish."""
    return [{"id": k, **v} for k, v in TIERS.items()]
