import asyncio
from backend.db import SessionLocal
from backend.models import User, Deck, DeckWord, Word
from backend.services.auth_service import create_access_token
from fastapi.testclient import TestClient
from backend.main import app

def run_test():
    db = SessionLocal()
    # Get first user
    user = db.query(User).first()
    if not user:
        print("No user found")
        return
        
    token = create_access_token({"sub": str(user.id)})
    print(f"Token created for user {user.email}")
    
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to add deck 1
    resp = client.post("/api/decks/1/add", headers=headers)
    print("Response Status:", resp.status_code)
    print("Response JSON:", resp.json())
    
run_test()
