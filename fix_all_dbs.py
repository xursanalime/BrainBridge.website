import sqlite3
import os

def fix_db(db_path):
    print(f"Checking {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check users table
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "tier_expires_at" not in columns:
        print("  Adding tier_expires_at to users...")
        cursor.execute("ALTER TABLE users ADD COLUMN tier_expires_at DATETIME")
    
    if "is_admin" not in columns:
        print("  Adding is_admin to users...")
        cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")

    # Check words table (SM-2 columns)
    cursor.execute("PRAGMA table_info(words)")
    columns = [row[1] for row in cursor.fetchall()]
    if "ease_factor" not in columns:
        print("  Adding ease_factor to words...")
        cursor.execute("ALTER TABLE words ADD COLUMN ease_factor FLOAT DEFAULT 2.5")
    if "interval" not in columns:
        print("  Adding interval to words...")
        cursor.execute("ALTER TABLE words ADD COLUMN interval INTEGER DEFAULT 0")
    if "repetitions" not in columns:
        print("  Adding repetitions to words...")
        cursor.execute("ALTER TABLE words ADD COLUMN repetitions INTEGER DEFAULT 0")

    conn.commit()
    conn.close()

for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(".db"):
            fix_db(os.path.join(root, file))
