from database import SessionLocal, User, init_db
from datetime import datetime, timedelta, timezone

def simulate_expiry():
    print("🔄 Ensuring database schema is up to date...")
    init_db() # Trigger the auto-migration logic
    
    session = SessionLocal()
    try:
        users = session.query(User).all()
        if not users:
            print("❌ No users found in database.")
            return

        for user in users:
            # Set to expire in 2 days
            new_expiry = datetime.now(timezone.utc) + timedelta(days=2)
            user.token_expires_at = new_expiry
            print(f"✅ Updated user {user.google_id} expiration to {new_expiry} (2 days left)")
        
        session.commit()
        print("🎉 Simulation applied! Please refresh the dashboard.")
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    simulate_expiry()
