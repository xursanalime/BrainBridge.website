import sqlite3
import os

db_path = "brainbridge.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all users
    cursor.execute("SELECT id FROM users")
    users = cursor.fetchall()
    
    for (user_id,) in users:
        # Calculate XP based on word boxes
        # Box 1 = 10, Box 2 = 20, etc.
        cursor.execute("SELECT box FROM words WHERE user_id = ?", (user_id,))
        words = cursor.fetchall()
        
        calculated_xp = sum(box * 10 for (box,) in words)
        
        # Update user's total_xp if it's currently 0
        cursor.execute("UPDATE users SET total_xp = ? WHERE id = ? AND total_xp = 0", (calculated_xp, user_id))
        
        if calculated_xp > 0:
            print(f"User {user_id}: Seeded {calculated_xp} XP based on existing words.")
            
    conn.commit()
    conn.close()
    print("XP Seeding completed.")
else:
    print("DB not found")
