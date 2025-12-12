from database import SessionLocal, User, engine
from sqlalchemy import text

def check_db():
    print(f"Checking database using engine: {engine}")
    
    # Check raw table structure
    with engine.connect() as conn:
        try:
            result = conn.execute(text("PRAGMA table_info(users)")).fetchall()
            found = False
            for row in result:
                # row is usually (cid, name, type, notnull, dflt_value, pk)
                if row[1] == 'token_expires_at':
                    found = True
                    print(f"✅ Column 'token_expires_at' found in table schema. Type: {row[2]}")
                    break
            if not found:
                print("❌ Column 'token_expires_at' NOT found in table schema!")
        except Exception as e:
            # If postgres, PRAGMA won't work, try standard SQL
            print(f"Schema check error (might be expected for PG): {e}")

    session = SessionLocal()
    try:
        users = session.query(User).all()
        print(f"Found {len(users)} users.")
        for user in users:
            print(f"User: {user.google_id}, Expires: {user.token_expires_at}")
    finally:
        session.close()

if __name__ == "__main__":
    check_db()
