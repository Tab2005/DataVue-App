import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)

with engine.connect() as conn:
    print("--- COMPLETE USER/DATA MAPPING ---")
    users = conn.execute(text("SELECT id, email, name, google_id, last_login FROM users ORDER BY last_login DESC")).fetchall()
    
    for u in users:
        uid, email, name, gid, last_login = u
        team_count = conn.execute(text("SELECT COUNT(*) FROM teams WHERE owner_id = :id"), {"id": uid}).scalar()
        member_count = conn.execute(text("SELECT COUNT(*) FROM team_members WHERE user_id = :id"), {"id": uid}).scalar()
        print(f"User: {name} | Email: {email}")
        print(f"  ID: {uid}")
        print(f"  GoogleID: {gid}")
        print(f"  Last Login: {last_login}")
        print(f"  Data: {team_count} Teams, {member_count} Memberships")
        print("-" * 30)
    
    print("\n--- TEAMS ---")
    teams = conn.execute(text("SELECT id, name, owner_id FROM teams")).fetchall()
    for t in teams:
        print(f"Team: {t[1]} (ID: {t[0]}) Owner: {t[2]}")
    
    print("--- END ---")
