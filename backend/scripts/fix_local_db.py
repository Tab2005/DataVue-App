"""
Fix local SQLite database schema and restore super admin permissions
"""
import sqlite3
import os

DB_PATH = "facebook_dashboard.db"

def fix_database():
    print(f"Fixing database: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check existing columns in users table
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Current columns: {columns}")
    
    # Add missing AI columns if needed
    new_columns = [
        ("zeabur_api_key", "TEXT"),
        ("gemini_api_key", "TEXT"),
        ("ai_provider", "TEXT DEFAULT 'zeabur'"),
        ("ai_model", "TEXT DEFAULT 'gemini-2.5-flash'")
    ]
    
    for col_name, col_type in new_columns:
        if col_name not in columns:
            print(f"Adding column: {col_name}")
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                print(f"  Warning: {e}")
    
    # List all users
    cursor.execute("SELECT id, email, is_super_admin FROM users")
    users = cursor.fetchall()
    print(f"\nUsers in database: {len(users)}")
    for user in users:
        print(f"  ID: {user[0][:8]}..., Email: {user[1]}, is_super_admin: {user[2]}")
    
    # Fix super admin for tabchen2005@gmail.com
    cursor.execute("UPDATE users SET is_super_admin = 1 WHERE email = 'tabchen2005@gmail.com'")
    if cursor.rowcount > 0:
        print(f"\n✅ Set is_super_admin = 1 for tabchen2005@gmail.com")
    else:
        print(f"\n⚠ User tabchen2005@gmail.com not found")
    
    conn.commit()
    conn.close()
    print("\n✅ Database fix complete!")

if __name__ == "__main__":
    fix_database()
