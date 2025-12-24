from database import SessionLocal, User, UserRole

def check_users():
    db = SessionLocal()
    with open("token_status.txt", "w", encoding="utf-8") as f:
        users = db.query(User).all()
        f.write(f"Found {len(users)} users.\n")
        for u in users:
            has_token = "YES" if u.fb_access_token else "NO"
            f.write(f"User: {u.google_id} (Role: {u.role}) - Has Token: {has_token}\n")

        from database import Team
        teams = db.query(Team).all()
        f.write(f"Found {len(teams)} teams.\n")
        for t in teams:
            has_token = "YES" if t.fb_access_token else "NO"
            try:
                f.write(f"Team: {t.name} (Owner: {t.owner_id}) - Has Token: {has_token}\n")
            except:
                f.write(f"Team: {t.id} - Has Token: {has_token}\n")
    db.close()
    db.close()

if __name__ == "__main__":
    check_users()
