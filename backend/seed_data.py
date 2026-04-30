import sys
import os
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

# Fix path to import models and db
sys.path.insert(0, os.path.dirname(__file__))

from db import SessionLocal
from models import User, Word
from services.auth_service import hash_password

def seed():
    db = SessionLocal()
    try:
        test_users = [
            {"email": "ali@example.com", "xp": 1500, "streak": 12},
            {"email": "botir@example.com", "xp": 2800, "streak": 45},
            {"email": "nodira@example.com", "xp": 2100, "streak": 30},
            {"email": "dilshod@example.com", "xp": 900, "streak": 5},
            {"email": "malika@example.com", "xp": 3500, "streak": 88},
        ]
        
        for u_data in test_users:
            # Check if exists
            exists = db.query(User).filter_by(email=u_data["email"]).first()
            if exists:
                user = exists
            else:
                user = User(
                    email=u_data["email"],
                    password_hash=hash_password("password123"),
                    created_at=datetime.now(timezone.utc)
                )
                db.add(user)
                db.flush()
            
            # Set XP and streak
            user.total_xp = u_data["xp"]
            user.monthly_xp = u_data["xp"] // 2
            user.daily_xp = u_data["xp"] // 10
            user.streak = u_data["streak"]
            user.last_xp_reset = datetime.now(timezone.utc)
            
            # Add some words
            if db.query(Word).filter_by(user_id=user.id).count() < 5:
                words = [
                    ("Innovation", "Innovatsiya"),
                    ("Resilience", "Bardoshlilik"),
                    ("Prosperity", "Farovonlik"),
                    ("Legacy", "Meros"),
                    ("Empathy", "Hamdardlik")
                ]
                for en, uz in words:
                    w_exists = db.query(Word).filter_by(user_id=user.id, word=en).first()
                    if not w_exists:
                        word = Word(user_id=user.id, word=en, translation=uz, box=1)
                        db.add(word)
            
        db.commit()
        print("Successfully seeded 5 test accounts with XP and words.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
