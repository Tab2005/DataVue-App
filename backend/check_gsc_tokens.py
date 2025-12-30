from database import SessionLocal, User

db = SessionLocal()
users = db.query(User).all()
for u in users:
    print(f"User: {u.email}")
    print(f"  GSC Token: {'YES' if u.gsc_access_token else 'NO'}")
    print(f"  GSC Refresh: {'YES' if u.gsc_refresh_token else 'NO'}")
    print(f"  GSC Expires: {u.gsc_expires_at}")
    print()
db.close()
