import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)

with engine.connect() as conn:
    print("--- FULL USER LIST ---")
    users = conn.execute(text("SELECT id, email, name, google_id FROM users")).fetchall()
    for i, u in enumerate(users):
        print(f"[{i}] ID: {u[0]}")
        print(f"    Email: {u[1]}")
        print(f"    Name: {u[2]}")
        print(f"    GoogleID: {u[3]}")
    print("--- END ---")
