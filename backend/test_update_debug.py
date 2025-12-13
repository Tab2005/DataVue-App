from database import SessionLocal, User, Team, TeamMember, UserRole
import sys

def test_manual_update():
    db = SessionLocal()
    try:
        print("🔍 Finding a Team...")
        team = db.query(Team).first()
        if not team:
            print("❌ No teams found.")
            return

        print(f"🏢 Found Team: {team.name} ({team.id})")
        
        # Test updating name
        print("✏️ Attempting to update name via ORM...")
        original_name = team.name
        team.name = f"{original_name} (Updated)"
        db.commit()
        db.refresh(team)
        print(f"✅ Success! New Name: {team.name}")
        
        # Revert
        team.name = original_name
        db.commit()
        print("🔄 Reverted name.")
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR during manual update: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_manual_update()
