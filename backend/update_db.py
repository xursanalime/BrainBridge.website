import sqlite3
import os

db_path = "/home/xursanalime/Downloads/BrainBridge.website-main/brainbridge.db"

if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    columns = [
        ("total_xp", "INTEGER DEFAULT 0"),
        ("daily_xp", "INTEGER DEFAULT 0"),
        ("monthly_xp", "INTEGER DEFAULT 0"),
        ("last_xp_reset", "DATETIME")
    ]
    
    for col_name, col_type in columns:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            print(f"Added column {col_name}")
        except sqlite3.OperationalError as e:
            print(f"Column {col_name} might already exist: {e}")
            
    conn.commit()
    conn.close()
    print("Database update attempt finished.")
