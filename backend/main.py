import sys
print("🚀 Starting Main Application...", file=sys.stderr)
from fastapi import FastAPI, HTTPException, Depends, status
print("✅ FastAPI imported", file=sys.stderr)
import os
print(f"📂 Current Debug Dir: {os.getcwd()}", file=sys.stderr)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from auth import TokenManager
import alembic.config
import alembic.command

# Robust Imports with Error Handling
try:
    from database import init_db, engine, SessionLocal, User, Team
    DB_STATUS = "OK"
except Exception as e:
    print(f"❌ DATABASE IMPORT ERROR: {e}", file=sys.stderr)
    DB_STATUS = f"ERROR: {e}"
    # Mock objects to prevent NameError later
    engine = None
    SessionLocal = None
    User = None
    def init_db(): pass

from datetime import datetime, timezone

try:
    from services import FacebookService
except Exception as e:
    print(f"❌ SERVICES IMPORT ERROR: {e}", file=sys.stderr)

import os
from dotenv import load_dotenv
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# Import Routers
from routers import users, teams, invites, admin, auth
from dependencies import get_current_team, get_db
from contextlib import asynccontextmanager
from fix_admin_permission import promote_to_superuser

# Initialize Database
# Load environment variables FIRST
load_dotenv()

# Initialize Database with Error Handling
try:
    # AUTO MIGRATION FOR ZEABUR
    # Run alembic upgrade head programmatically
    print("Running Database Migrations...")
    alembic_cfg = alembic.config.Config("alembic.ini")
    alembic.command.upgrade(alembic_cfg, "head")
    print("Database Migrations Applied.")
except Exception as e:
    print(f"Database Migration/Initialization Failed: {str(e)}")


app = FastAPI()

# Register Routers
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(teams.router, prefix="/api/teams", tags=["teams"]) # Team Management
app.include_router(invites.router, prefix="/api", tags=["invites"]) # Invites (Root api prefix for /invites)
app.include_router(admin.router) # Admin Router (prefix defined in router)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["*"],  # Wildcard is not allowed with allow_credentials=True
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "https://facebook-dashboard-web-app.zeabur.app" # Production URL if known, adding placeholder
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    """Health check endpoint to verify service status and DB connection."""
    db_info = "Unknown"
    if engine:
        db_info = "PostgreSQL" if "postgresql" in str(engine.url) else "SQLite"
    
    return {
        "status": "online", 
        "database_status": DB_STATUS,
        "database_type": db_info,
        "message": "Backend is running (Safe Mode) with User Management"
    }

# --- Google Token Verification ---
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
security = HTTPBearer()

def verify_google_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        # Debug: Check Client ID
        if not GOOGLE_CLIENT_ID:
            print("CRITICAL: GOOGLE_CLIENT_ID is missing from env!", file=sys.stderr, flush=True)

        # print(f"🔐 Verifying Token: {token[:10]}... ClientID: {GOOGLE_CLIENT_ID}", file=sys.stderr)
        
        # Add clock skew tolerance (e.g., 60 seconds) to handle local time discrepancies
        id_info = id_token.verify_oauth2_token(token, google_requests.Request(), GOOGLE_CLIENT_ID, clock_skew_in_seconds=60)
        userid = id_info['sub']
        return userid
    except ValueError as e:
        print(f"Token Verification Failed: {e}", file=sys.stderr, flush=True)
        # Also print to stdout for safety
        print(f"Token Verification Failed: {e}", flush=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
# ---------------------------------

from typing import Optional

class ExchangeRequest(BaseModel):
    app_id: str
    app_secret: str
    short_token: str
    team_id: Optional[str] = None

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI"}

@app.post("/api/auth/exchange-token")
def exchange_token_endpoint(request: ExchangeRequest, user_id: str = Depends(verify_google_token)):
    success, message = TokenManager.exchange_for_long_lived_token(
        request.app_id, 
        request.app_secret, 
        request.short_token,
        user_id, # Pass user_id
        team_id=request.team_id # Pass team_id
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message}

@app.get("/api/auth/token-status")
def get_token_status(user_id: str = Depends(verify_google_token)):
    """Check the expiration status of the user's Facebook token."""
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.google_id == user_id).first()
        
        if not user or not user.token_expires_at:
             return {
                 "expires_at": None,
                 "days_remaining": None,
                 "is_expired": False
             }
        
        now = datetime.now(timezone.utc)
        expires_at = user.token_expires_at
        
        # Ensure timezone awareness compatibility
        if expires_at.tzinfo is None:
             expires_at = expires_at.replace(tzinfo=timezone.utc)
             
        delta = expires_at - now
        days_remaining = delta.days
        
        return {
            "expires_at": expires_at.isoformat(),
            "days_remaining": days_remaining,
            "is_expired": days_remaining < 0
        }
    except Exception as e:
        print(f"Error checking token status: {e}")
        # Return DB error details for debugging
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
    finally:
        session.close()

@app.get("/api/ad-accounts")
def get_ad_accounts(
    user_id: str = Depends(verify_google_token),
    team: Team = Depends(get_current_team)
):
    team_id = team.id if team else None
    # Pass user_id and team_id
    accounts, error = FacebookService.get_all_ad_accounts(user_id, team_id=team_id)
    if error:
        return []
    return accounts

@app.get("/api/dashboard-data")
def get_dashboard_data(
    account_id: str = None, 
    days: int = 7, 
    user_id: str = Depends(verify_google_token), 
    team: Team = Depends(get_current_team)
):
    team_id = team.id if team else None
    if account_id:
        # Pass user_id, days, and team_id
        insights = FacebookService.get_account_insights(account_id, user_id, days, team_id=team_id)
        if insights:
            return {
                "source": "real",
                "account_id": account_id,
                "kpi": insights["kpi"],
                "chart_data": insights["charts"],
                "date_range": insights.get("date_range")
            }
        else:
            print(f"❌ Dashboard Data Fetch Failed for {account_id}", file=sys.stderr)
            raise HTTPException(status_code=400, detail="Failed to fetch insights for this account")

    return {
        "source": "mock_fallback",
        "kpi": [
            {"label": "Total Followers", "value": "---", "change": "---"},
            {"label": "Engagement Rate", "value": "---", "change": "---"},
            {"label": "Impressions", "value": "---", "change": "---"},
            {"label": "Reach", "value": "---", "change": "---"},
        ],
        "chart_data": []
    }

@app.get("/api/analytics-data")
def get_analytics_data(
    account_id: str, 
    since: str, 
    until: str, 
    level: str = "account", 
    user_id: str = Depends(verify_google_token),
    team: Team = Depends(get_current_team)
):
    """
    Endpoint for the Advanced Analytics page.
    Requires account_id, custom date range (since/until), and aggregation level.
    """
    team_id = team.id if team else None
    report_data = FacebookService.get_custom_report(account_id, user_id, since, until, level, team_id=team_id)
    
    if report_data is None:
         raise HTTPException(status_code=400, detail="Failed to fetch analytics data")
         
    return {
        "data": report_data,
        "meta": {
            "level": level,
            "period": f"{since} ~ {until}"
        }
    }

@app.get("/api/analytics-trend")
def get_analytics_trend_data(
    account_id: str,
    since: str,
    until: str,
    prev_since: str = None,
    prev_until: str = None,
    user_id: str = Depends(verify_google_token),
    team: Team = Depends(get_current_team)
):
    """
    Endpoint for daily trend chart data.
    """
    team_id = team.id if team else None
    trend_data = FacebookService.get_analytics_trend(account_id, user_id, since, until, prev_since, prev_until, team_id=team_id)
    if trend_data is None:
         # Return empty list instead of 400 to avoid breaking UI if just no data
         return []
    return trend_data


if __name__ == "__main__":
    import uvicorn
    print("🚀 STARTING UVICORN SERVER...", file=sys.stderr)
    # Enable reload for development
    # Forced Reload Trigger [Timestamp: 1450]
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
