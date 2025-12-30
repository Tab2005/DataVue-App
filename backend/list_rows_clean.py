import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)

with engine.connect() as conn:
    print("--- USERS ---")
    users = conn.execute(text("SELECT id, email, name FROM users")).fetchall()
    for u in users:
        print(f"ID: {u[0]}, Email: {u[1]}, Name: {u[2]}")
    
    print("\n--- TEAMS ---")
    teams = conn.execute(text("SELECT id, name, owner_id FROM teams")).fetchall()
    for t in teams:
        print(f"ID: {t[0]}, Name: {t[1]}, Owner: {t[2]}")
    
    print("\n--- USER_MODULE_ACCESS ---")
    # Join with Module to see the names
    access = conn.execute(text("""
        SELECT a.user_id, m.key, a.enabled 
        FROM user_module_access a 
        JOIN modules m ON a.module_id = m.id
    """)).fetchall()
    for a in access:
        print(f"User: {a[0]}, Module: {a[1]}, Enabled: {a[2]}")
