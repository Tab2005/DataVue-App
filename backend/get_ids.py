import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)

with engine.connect() as conn:
    print("USER_SUMMARY_START")
    users = conn.execute(text("SELECT id, email, name FROM users")).fetchall()
    for u in users:
        print(f"USER|{u[0]}|{u[1]}|{u[2]}")
    print("USER_SUMMARY_END")
