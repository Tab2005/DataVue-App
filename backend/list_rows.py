import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)

with engine.connect() as conn:
    print("USERS:")
    users = conn.execute(text("SELECT id, email, name, google_id FROM users")).fetchall()
    for u in users:
        print(u)
    
    print("\nTEAMS:")
    teams = conn.execute(text("SELECT id, name, owner_id FROM teams")).fetchall()
    for t in teams:
        print(t)
    
    print("\nUSER_MODULE_ACCESS:")
    access = conn.execute(text("SELECT * FROM user_module_access")).fetchall()
    for a in access:
        print(a)
