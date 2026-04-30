import sqlite3
import os

db_path = "/home/xursanalime/Downloads/BrainBridge.website-main/brainbridge.db"

if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT")
        print("Column avatar_url added to users table.")
    except sqlite3.OperationalError as e:
        print(f"Column avatar_url might already exist: {e}")
            
    conn.commit()
    conn.close()
    print("Database update attempt finished.")
