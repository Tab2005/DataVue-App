from database import SessionLocal, User
from datetime import datetime, timedelta, timezone

def restore_expiry():
    session = SessionLocal()
    try:
        users = session.query(User).all()
        if not users:
            print("❌ No users found in database.")
            return

        for user in users:
            # Restore to 60 days
            new_expiry = datetime.now(timezone.utc) + timedelta(days=60)
            user.token_expires_at = new_expiry
            print(f"✅ Restored user {user.google_id} expiration to {new_expiry} (60 days left)")
        
        session.commit()
        print("🎉 Restore applied! Notification should disappear.")
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    restore_expiry()
