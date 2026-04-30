import os
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from models import User

import secrets

# Use a secure secret key from environment or generate a random one for the session
SECRET_KEY = os.getenv("SESSION_SECRET") or os.getenv("SECRET_KEY", "bb-prod-secret-7c5cfc-00d4ff-2026")
ALGORITHM  = "HS256"
ACCESS_TOKEN_EXP = 15     # 15 minutes
REFRESH_TOKEN_EXP = 60 * 24 * 7  # 7 days

def hash_password(password: str, salt: bytes = None) -> str:
    """Secure hashing using PBKDF2 with dynamic salting."""
    if salt is None:
        salt = secrets.token_bytes(16)
    iterations = 100000
    hash_hex = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, iterations).hex()
    return f"pbkdf2${iterations}${salt.hex()}${hash_hex}"

def verify_password(plain: str, hashed: str) -> bool:
    """Verify password with fallback for old hashes."""
    if hashed.startswith("pbkdf2$"):
        parts = hashed.split('$')
        if len(parts) == 4:
            iterations = int(parts[1])
            salt = bytes.fromhex(parts[2])
            expected_hash = parts[3]
            actual_hash = hashlib.pbkdf2_hmac('sha256', plain.encode(), salt, iterations).hex()
            return actual_hash == expected_hash
            
    # Fallback for old global salt PBKDF2
    if len(hashed) == 64 and not any(c in hashed for c in 'ghijklmnopqrstuvwxyz'):
        # Old PBKDF2
        old_pbkdf2 = hashlib.pbkdf2_hmac('sha256', plain.encode(), b"brainbridge-salt-2026", 100000).hex()
        if old_pbkdf2 == hashed:
            return True
        # Old SHA256
        if hashlib.sha256(plain.encode()).hexdigest() == hashed:
            return True
            
    return False

def create_access_token(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXP)
    return jwt.encode({"sub": str(user_id), "type": "access", "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_TOKEN_EXP)
    return jwt.encode({"sub": str(user_id), "type": "refresh", "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str, token_type: str = "access") -> Optional[int]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type", "access") != token_type: # default "access" for backward compatibility with old 30-day tokens
            return None
        return int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        return None



def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email.lower().strip()).first()


def register(db: Session, email: str, password: str) -> User:
    user = User(email=email.lower().strip(), password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        return None
    return user
