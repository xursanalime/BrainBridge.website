import sqlite3
import os

db_path = "/home/xursanalime/Downloads/BrainBridge.website-main/brainbridge.db"

if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            achievement_id VARCHAR(50) NOT NULL,
            unlocked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE (user_id, achievement_id)
        )
        """)
        print("Table user_achievements created or already exists.")
    except Exception as e:
        print(f"Error creating table: {e}")
            
    conn.commit()
    conn.close()
    print("Database update attempt finished.")
