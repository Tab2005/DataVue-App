from database import SessionLocal, User, Team
import sys

def check_data():
    db = SessionLocal()
    try:
        print("🔍 Checking Database Data...")
        
        # Check User
        email = "tabchen2005@gmail.com"
        user = db.query(User).filter(User.email == email).first()
        if user:
            print(f"👤 User: {user.name} ({user.email})")
            print(f"   Role: {user.role}")
            print(f"   SuperAdmin: {user.is_super_admin}")
        else:
            print(f"❌ User {email} NOT FOUND.")

        # Check Teams
        teams = db.query(Team).all()
        print(f"🏢 Total Teams: {len(teams)}")
        for t in teams:
            print(f"   - {t.name} (ID: {t.id}, Owner: {t.owner_id})")

    except Exception as e:
        print(f"❌ Error during check: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_data()
