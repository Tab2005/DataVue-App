from backend.database import SessionLocal, Team
from datetime import datetime

db = SessionLocal()
teams = db.query(Team).all()

print(f"{'Team Name':<20} | {'Token Expires At'}")
print("-" * 40)
for team in teams:
    expires = team.token_expires_at
    print(f"{team.name:<20} | {expires}")

db.close()
