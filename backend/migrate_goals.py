import sqlite3
import os

db_path = "brainbridge.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN goal_reviews INTEGER DEFAULT 10")
        cursor.execute("ALTER TABLE users ADD COLUMN goal_sentences INTEGER DEFAULT 3")
        cursor.execute("ALTER TABLE users ADD COLUMN goal_xp INTEGER DEFAULT 50")
        conn.commit()
        print("Migration successful: Added goal columns.")
    except sqlite3.OperationalError as e:
        print(f"Migration skipped or failed: {e}")
    conn.close()
else:
    print("DB not found")
