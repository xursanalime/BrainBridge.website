import sqlite3

db_path = '/home/xursanalime/Downloads/BrainBridge.website-main/backend/brainbridge.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE users ADD COLUMN spelling_count INTEGER DEFAULT 0 NOT NULL")
    print("Added spelling_count column")
except sqlite3.OperationalError:
    print("spelling_count column already exists")

try:
    cursor.execute("ALTER TABLE users ADD COLUMN ai_sentence_count INTEGER DEFAULT 0 NOT NULL")
    print("Added ai_sentence_count column")
except sqlite3.OperationalError:
    print("ai_sentence_count column already exists")

conn.commit()
conn.close()
