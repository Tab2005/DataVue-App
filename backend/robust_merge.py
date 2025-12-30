import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)

EMAIL = "tabchen2005@gmail.com"

with engine.connect() as conn:
    print(f"Searching for users with email: {EMAIL}")
    
    users = conn.execute(text("SELECT id, google_id, name FROM users WHERE email = :email"), {"email": EMAIL}).fetchall()
    
    if len(users) < 2:
        print(f"❌ Found {len(users)} users. Nothing to merge.")
        exit(0)
    
    # Identify which one has teams
    data_user = None
    empty_user = None
    
    for u in users:
        uid = u[0]
        team_count = conn.execute(text("SELECT COUNT(*) FROM teams WHERE owner_id = :id"), {"id": uid}).scalar()
        member_count = conn.execute(text("SELECT COUNT(*) FROM team_members WHERE user_id = :id"), {"id": uid}).scalar()
        
        if team_count > 0 or member_count > 0:
            print(f"Found DATA user: ID={uid}, Name={u[2]}, Teams={team_count}, Memberships={member_count}")
            data_user = u
        else:
            print(f"Found EMPTY user: ID={uid}, Name={u[2]}")
            empty_user = u
            
    if not data_user or not empty_user:
        print("❌ Could not clearly identify a data user and an empty user to merge.")
        exit(1)
        
    print(f"\nMerging EMPTY user {empty_user[0]} into DATA user {data_user[0]}...")
    
    # Perform the merge
    # Step 1: Get the current google_id from the empty user (this is the one used for login)
    current_active_google_id = empty_user[1]
    
    # Step 2: Delete sessions/access for empty user
    conn.execute(text("DELETE FROM user_module_access WHERE user_id = :id"), {"id": empty_user[0]})
    conn.execute(text("DELETE FROM users WHERE id = :id"), {"id": empty_user[0]})
    
    # Step 3: Map the active google_id to the data user
    conn.execute(text("UPDATE users SET google_id = :gid, name = :name WHERE id = :uid"), 
                 {"gid": current_active_google_id, "name": "Tab Chen", "uid": data_user[0]})
    
    conn.commit()
    print("✅ RECOVERY SUCCESSFUL! Data user now associated with current Google ID.")
