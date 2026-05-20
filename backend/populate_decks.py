import os
import sys

# Configure environment path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import SessionLocal, init_db
from models import Deck, DeckWord

def populate():
    init_db()
    db = SessionLocal()

    # 1. IELTS Top 100
    d1 = db.query(Deck).filter(Deck.title == "IELTS Top 100").first()
    if not d1:
        d1 = Deck(
            title="IELTS Top 100",
            description="IELTS imtihoni uchun eng zarur 100 ta akademik so'z.",
            is_premium=False,
            icon="🎓"
        )
        db.add(d1)
        db.commit()
        db.refresh(d1)
        
        words = [
            ("accommodate", "joylashtirmoq, moslashtirmoq"),
            ("ambiguous", "mubham, noaniq"),
            ("benevolent", "xayrixoh, mehribon"),
            ("comprehensive", "har tomonlama, keng qamrovli"),
            ("deteriorate", "yomonlashmoq"),
            ("elicit", "keltirib chiqarmoq"),
            ("fluctuate", "tebranib turmoq, o'zgarib turmoq"),
            ("hierarchy", "iyerarxiya, bo'ysunish tartibi"),
            ("implement", "amalga oshirmoq"),
            ("jeopardize", "xavf ostiga qo'ymoq")
        ] # qisqa demo uchun 10 ta
        for w, t in words:
            db.add(DeckWord(deck_id=d1.id, word=w, translation=t))

    # 2. IT & Dasturlash
    d2 = db.query(Deck).filter(Deck.title == "IT & Dasturlash").first()
    if not d2:
        d2 = Deck(
            title="IT & Dasturlash",
            description="Dasturchilar va IT mutaxassislari uchun kasbiy ingliz tili.",
            is_premium=True,
            icon="💻"
        )
        db.add(d2)
        db.commit()
        db.refresh(d2)
        
        words = [
            ("deploy", "ishga tushirmoq (serverda)"),
            ("debug", "xatolarni to'g'irlamoq"),
            ("inherit", "meros olmoq (OOP)"),
            ("variable", "o'zgaruvchi"),
            ("framework", "ishchi ramka"),
            ("query", "so'rov"),
            ("authentication", "haqiqiylikni tekshirish"),
            ("agile", "chaqqon (metodologiya)")
        ]
        for w, t in words:
            db.add(DeckWord(deck_id=d2.id, word=w, translation=t))
            
    db.commit()
    db.close()
    print("Decks populated successfully!")

if __name__ == "__main__":
    populate()
