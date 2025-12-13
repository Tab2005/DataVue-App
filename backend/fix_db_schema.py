from database import engine, SessionLocal, User
from sqlalchemy import text
import sys

def fix_schema():
    print("🔧 Checking Database Schema...")
    with engine.connect() as conn:
        # Check if is_super_admin exists
        try:
            conn.execute(text("SELECT is_super_admin FROM users LIMIT 1"))
            print("✅ 'is_super_admin' column exists.")
        except Exception:
            print("⚠️ 'is_super_admin' column MISSING. Adding it...")
            try:
                # SQLite syntax for adding column
                conn.execute(text("ALTER TABLE users ADD COLUMN is_super_admin BOOLEAN DEFAULT 0"))
                conn.commit()
                print("✅ Added 'is_super_admin' column.")
            except Exception as e:
                print(f"❌ Failed to add column: {e}")
                return

def promote_super_admin():
    db = SessionLocal()
    try:
        email = "tabchen2005@gmail.com"
        user = db.query(User).filter(User.email == email).first()
        if user:
            print(f"👤 Found user: {user.name} ({user.id})")
            if not user.is_super_admin:
                user.is_super_admin = True
                db.commit()
                print(f"🚀 Promoted {email} to SUPER ADMIN successfully!")
            else:
                print(f"ℹ️ {email} is already a Super Admin.")
        else:
            print(f"❌ User {email} not found in DB.")
            # List all users to help debug
            users = db.query(User).all()
            print("--- Available Users ---")
            for u in users:
                print(f"- {u.email} ({u.name})")
    except Exception as e:
        print(f"❌ Promotion failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_schema()
    promote_super_admin()
