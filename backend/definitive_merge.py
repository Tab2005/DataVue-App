import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)

with engine.connect() as conn:
    print("🚀 Starting Definitive Recovery...")
    
    # 1. Find all users
    users = conn.execute(text("SELECT id, email, name, google_id FROM users")).fetchall()
    
    data_user = None
    all_users_by_email = {}
    
    for u in users:
        uid, email, name, gid = u
        print(f"Checking {email} ({uid})...")
        team_count = conn.execute(text("SELECT COUNT(*) FROM teams WHERE owner_id = :id"), {"id": uid}).scalar()
        member_count = conn.execute(text("SELECT COUNT(*) FROM team_members WHERE user_id = :id"), {"id": uid}).scalar()
        
        if team_count > 0 or member_count > 0:
            print(f"  -> DATA USER FOUND! (Email={email}, Name={name})")
            data_user = u
        
        if email not in all_users_by_email:
            all_users_by_email[email] = []
        all_users_by_email[email].append(u)

    if not data_user:
        print("❌ CRITICAL: No user found who owns any teams or memberships!")
        exit(1)
        
    email = data_user[1]
    potential_new_logins = [u for u in all_users_by_email.get(email, []) if u[0] != data_user[0]]
    
    if not potential_new_logins:
        print(f"❌ No other users found with email {email}. Searching for ANY recently created user...")
        # Fallback: Find the most recently created user if no email match
        potential_new_logins = conn.execute(text("SELECT id, email, name, google_id FROM users WHERE id != :id ORDER BY created_at DESC LIMIT 1"), {"id": data_user[0]}).fetchall()

    if not potential_new_logins:
        print("❌ Could not find a new login user to merge from.")
        exit(1)
        
    new_login_user = potential_new_logins[0]
    print(f"Merging NEW login {new_login_user[1]} ({new_login_user[0]}) into DATA user {data_user[1]} ({data_user[0]})")
    
    # Perform the merge
    current_google_id = new_login_user[3]
    
    # Step 1: Cleanup new login
    conn.execute(text("DELETE FROM user_module_access WHERE user_id = :id"), {"id": new_login_user[0]})
    conn.execute(text("DELETE FROM users WHERE id = :id"), {"id": new_login_user[0]})
    
    # Step 2: Update data user
    conn.execute(text("UPDATE users SET google_id = :gid WHERE id = :uid"), {"gid": current_google_id, "uid": data_user[0]})
    
    conn.commit()
    print("✅ DATA RESTORED. The user's original account now has the new Google identity.")
