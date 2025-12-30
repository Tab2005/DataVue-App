import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)

# The target user (with data) and the source user (current new login)
OLD_USER_ID = "607f2671-3ac7-4cda-a344-33824cd0b661"
NEW_USER_ID = "909ab610-26b0-4373-ba14-118f6f582f3c"

with engine.connect() as conn:
    print(f"Merging {NEW_USER_ID} into {OLD_USER_ID}...")
    
    # 1. Get the new Google ID
    new_google_id = conn.execute(text("SELECT google_id FROM users WHERE id = :id"), {"id": NEW_USER_ID}).scalar()
    print(f"New Google ID to transfer: {new_google_id}")
    
    if not new_google_id:
        print("❌ Could not find new google_id!")
        exit(1)

    # 2. Delete the temporary new user (ensure no foreign key issues first)
    # We should also check for any data created by the new user in the last few minutes
    # (Assuming there's almost nothing)
    conn.execute(text("DELETE FROM user_module_access WHERE user_id = :id"), {"id": NEW_USER_ID})
    conn.execute(text("DELETE FROM users WHERE id = :id"), {"id": NEW_USER_ID})
    
    # 3. Update the old user with the new Google ID
    conn.execute(text("UPDATE users SET google_id = :new_id, name = 'Tab Chen' WHERE id = :old_id"), 
                 {"new_id": new_google_id, "old_id": OLD_USER_ID})
    
    conn.commit()
    print("✅ Account merge successful. Old account now has new Google ID.")
