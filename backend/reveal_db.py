import os
from dotenv import load_dotenv

# Mimic main.py
load_dotenv()
db_url = os.getenv("DATABASE_URL")
cwd = os.getcwd()

print(f"CWD: {cwd}")
print(f"Active DATABASE_URL: {db_url}")
if db_url:
    print(f"DB URL Type: {'PostgreSQL' if 'postgre' in db_url else 'SQLite' if 'sqlite' in db_url else 'Other'}")
    # Reveal enough to identify but hide credentials if possible
    parts = db_url.split("@")
    if len(parts) > 1:
        print(f"DB Host: {parts[1]}")
    else:
        print(f"DB String: {db_url[:20]}...")
else:
    print("Active DATABASE_URL: None (Fallback to default)")
