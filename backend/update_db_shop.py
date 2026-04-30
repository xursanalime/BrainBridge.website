import sqlite3

def update_db():
    conn = sqlite3.connect("../brainbridge.db")
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN coins INTEGER DEFAULT 0 NOT NULL")
        print("Added coins column to users table.")
    except sqlite3.OperationalError as e:
        print(f"Skipping coins: {e}")

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN streak_freezes INTEGER DEFAULT 0 NOT NULL")
        print("Added streak_freezes column to users table.")
    except sqlite3.OperationalError as e:
        print(f"Skipping streak_freezes: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_db()
