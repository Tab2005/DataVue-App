import sys
import os
from dotenv import load_dotenv
# Load environment variables IMMEDIATELY
load_dotenv()

# --- Environment Variable Validation ---
# Validate required environment variables at startup for fail-fast behavior
REQUIRED_ENV_VARS = [
    "GOOGLE_CLIENT_ID",
    "ENCRYPTION_KEY",
]

# Optional but recommended variables (warn if missing)
OPTIONAL_ENV_VARS = [
    "DATABASE_URL",  # Falls back to SQLite if not set
]

def validate_environment():
    """Validate that all required environment variables are set."""
    missing = []
    for var in REQUIRED_ENV_VARS:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print("=" * 60, file=sys.stderr)
        print("CRITICAL ERROR: Missing Required Environment Variables", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        for var in missing:
            print(f"  - {var}", file=sys.stderr)
        print("", file=sys.stderr)
        print("Please set these variables in your .env file or environment.", file=sys.stderr)
        print("The server cannot start without them.", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        sys.exit(1)
    
    # Check optional variables
    for var in OPTIONAL_ENV_VARS:
        if not os.getenv(var):
            print(f"[INFO] Optional environment variable not set: {var}", file=sys.stderr)
    
    print("[OK] All required environment variables are configured.", file=sys.stderr)

# Run validation
validate_environment()
# -----------------------------------------

print("Starting Main Application...", file=sys.stderr)
from fastapi import FastAPI, HTTPException, Depends, status
print("[OK] FastAPI imported", file=sys.stderr)
print(f"[INFO] Current Dir: {os.getcwd()}", file=sys.stderr)

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
    from async_services import AsyncFacebookService
except Exception as e:
    print(f"SERVICES IMPORT ERROR: {e}", file=sys.stderr)

import os
from dotenv import load_dotenv
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# Import Routers
from routers import users, teams, invites, admin, ai, saved_views
import auth
from dependencies import get_current_team, get_db
from contextlib import asynccontextmanager

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
    
    print("Database Migrations Applied.")
    
    print("Verifying Schema Integrity...")
    # SQLALCHEMY AUTO-PATCHING (For environments where migration history is lost/broken)
    try:
        from sqlalchemy import text, inspect
        inspector = inspect(engine)
        if inspector.has_table("teams"):
            columns = [c["name"] for c in inspector.get_columns("teams")]
            print(f"DEBUG: Current Teams Columns: {columns}")
            
            # Patch 1: visible_ad_account_ids
            if "visible_ad_account_ids" not in columns:
                print("⚠️ Schema Drift Detected: Adding 'visible_ad_account_ids' to teams table...")
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE teams ADD COLUMN visible_ad_account_ids VARCHAR"))
                    conn.commit()
                print("✅ Schema Patched: visible_ad_account_ids added.")
                
            # Patch 2: fb_app_id
            if "fb_app_id" not in columns:
                 print("⚠️ Schema Drift: Adding 'fb_app_id'...")
                 with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE teams ADD COLUMN fb_app_id VARCHAR"))
                    conn.commit()
            
            # Patch 3: fb_access_token
            if "fb_access_token" not in columns:
                 print("⚠️ Schema Drift: Adding 'fb_access_token'...")
                 with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE teams ADD COLUMN fb_access_token VARCHAR"))
                    conn.commit()
            
            # Patch 4: token_expires_at
            if "token_expires_at" not in columns:
                 print("⚠️ Schema Drift: Adding 'token_expires_at'...")
                 with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE teams ADD COLUMN token_expires_at TIMESTAMP"))
                    conn.commit()
                    
    except Exception as e:
        print(f"⚠️ Schema Patching Warning: {e}")

    # --- PATCH: Auto-create saved_views table if missing ---
    try:
        from sqlalchemy import text, inspect
        inspector = inspect(engine)
        if not inspector.has_table("saved_views"):
            print("⚠️ Table 'saved_views' not found. Creating via DDL...")
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS saved_views (
                        id VARCHAR PRIMARY KEY,
                        name VARCHAR NOT NULL,
                        metrics VARCHAR NOT NULL,
                        user_id VARCHAR REFERENCES users(id),
                        team_id VARCHAR REFERENCES teams(id),
                        created_by VARCHAR REFERENCES users(id),
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_saved_views_user_id ON saved_views(user_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_saved_views_team_id ON saved_views(team_id)"))
                conn.commit()
            print("✅ Table 'saved_views' created successfully.")
        else:
            print("✅ Table 'saved_views' already exists.")
    except Exception as e:
        print(f"⚠️ saved_views Auto-Patch Warning: {e}")

    init_db() 
    
    print("Schema Verified.")
except Exception as e:
    print(f"Database Migration/Initialization Failed: {str(e)}")


app = FastAPI(
    title="Facebook Dashboard API",
    description="API for Facebook Ads Dashboard with Analytics and Team Management",
    version="1.5.0"
)

# --- Unified Exception Handlers ---
from fastapi import Request
from fastapi.responses import JSONResponse
import traceback
from exceptions import (
    AppException,
    AuthenticationError,
    AuthorizationError,
    FacebookAPIError,
    ResourceNotFoundError,
    ValidationError,
    DatabaseError
)

# Handler for custom AppException and its subclasses
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle all custom application exceptions with consistent JSON response."""
    print(f"[ERROR] {exc.error_code}: {exc.message}", file=sys.stderr)
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )

# Handler for standard HTTP exceptions
from fastapi import HTTPException
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTPException."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "error_code": "HTTP_ERROR",
            "details": {}
        }
    )

# Handler for unhandled exceptions (fallback)
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    error_msg = f"Internal server error: {str(exc)}"
    print(f"[CRITICAL] Unhandled exception: {str(exc)}", file=sys.stderr)
    traceback.print_exc()
    
    # In production, hide traceback from response
    is_dev = os.getenv("ENV", "development") == "development"
    
    content = {
        "error": error_msg if is_dev else "Internal server error",
        "error_code": "INTERNAL_ERROR",
        "details": {}
    }
    
    if is_dev:
        content["traceback"] = traceback.format_exc()
    
    return JSONResponse(
        status_code=500,
        content=content
    )
# -----------------------------------------

# --- Google Token Verification ---
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
security = HTTPBearer()

def verify_google_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        # Debug: Check Client ID
        if not GOOGLE_CLIENT_ID:
            print("CRITICAL: GOOGLE_CLIENT_ID is missing from env!", file=sys.stderr, flush=True)

        # Add clock skew tolerance (e.g., 60 seconds) to handle local time discrepancies
        id_info = id_token.verify_oauth2_token(token, google_requests.Request(), GOOGLE_CLIENT_ID, clock_skew_in_seconds=60)
        userid = id_info['sub']
        return userid
    except Exception as e:
        print(f"Token Verification Critical Error (Main): {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication Error ({type(e).__name__}): {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
# ---------------------------------

from typing import Optional

class ExchangeRequest(BaseModel):
    app_id: str
    app_secret: str
    short_token: str
    team_id: Optional[str] = None

# --- Auth Endpoints ---
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

# Include Routers
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(teams.router, prefix="/api/teams", tags=["teams"])
app.include_router(invites.router, prefix="/api", tags=["invites"])
app.include_router(admin.router) # /api/admin
app.include_router(ai.router) # /api/ai
app.include_router(saved_views.router) # /api/saved-views


@app.get("/api/auth/token-status")
def get_token_status(team_id: Optional[str] = None, user_id: str = Depends(verify_google_token)):
    """Check the expiration status of the user's OR team's Facebook token."""
    session = SessionLocal()
    try:
        target = None
        if team_id:
             target = session.query(Team).filter(Team.id == team_id).first()
        else:
             target = session.query(User).filter(User.google_id == user_id).first()
        
        if not target or not target.token_expires_at:
             return {
                 "expires_at": None,
                 "days_remaining": None,
                 "is_expired": False
             }
        
        now = datetime.now(timezone.utc)
        expires_at = target.token_expires_at
        
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

# --- Include Routers ---
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(teams.router, prefix="/api/teams", tags=["teams"]) # Team Management
app.include_router(invites.router, prefix="/api", tags=["invites"]) # Invites
app.include_router(ai.router, prefix="/api/ai", tags=["ai"]) # AI Intelligence
app.include_router(admin.router) # Admin Router (prefix defined in router)



# Middleware removed for stability


# Configure CORS
# Using Wildcard Origin with allow_credentials=False is standard for Token-based Auth (Bearer)
# This avoids complex Origin matching issues in cloud environments.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False, # Must be False to use buildcard "*"
    allow_methods=["*"],
    allow_headers=["*"],
)

# Debug Router reachability
@app.get("/api/saved-views/ping")
def saved_views_ping():
    return {"status": "pong", "message": "Saved Views Router is Active"}

# DEBUG ENDPOINT (Temporary)
@app.get("/api/debug/fix-schema")
def fix_db_schema():
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(engine)
        columns = [c["name"] for c in inspector.get_columns("teams")]
        
        result = {
            "table": "teams",
            "existing_columns": columns,
            "actions_taken": []
        }
        
        if "token_expires_at" not in columns:
            try:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE teams ADD COLUMN token_expires_at TIMESTAMP"))
                    conn.commit()
                result["actions_taken"].append("Added token_expires_at")
            except Exception as e:
                result["actions_taken"].append(f"Failed to add token_expires_at: {e}")
        else:
            result["actions_taken"].append("token_expires_at already exists")
            
        return result
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/debug/permissions")
def debug_permissions(team_id: str, token: str):
    # Manual verify to allow browser access
    try:
         id_info = id_token.verify_oauth2_token(token, google_requests.Request(), GOOGLE_CLIENT_ID, clock_skew_in_seconds=60)
         user_id = id_info['sub']
    except Exception as e:
         return {"error": f"Invalid Token: {e}"}

    session = SessionLocal()
    try:
        user = session.query(User).filter(User.google_id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        member = session.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user.id
        ).first()
        
        # Check explicit permission logic used in auth.py
        is_admin = False
        if user.is_super_admin:
            is_admin = True
        elif member and member.role == UserRole.ADMIN:
            is_admin = True
            
        return {
            "user_name": user.name,
            "google_id": user_id,
            "internal_id": user.id,
            "is_super_admin": user.is_super_admin,
            "team_id": team_id,
            "team_member_role": member.role if member else "NOT_MEMBER",
            "computed_is_admin": is_admin
        }
    finally:
        session.close()

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

@app.get("/api/ad-accounts")
async def get_ad_accounts(
    user_id: str = Depends(verify_google_token),
    team: Team = Depends(get_current_team),
    db: SessionLocal = Depends(get_db)
):
    team_id = team.id if team else None
    
    # 1. Resolve Owner Status FIRST
    current_db_user = db.query(User).filter(User.google_id == user_id).first()
    current_internal_id = current_db_user.id if current_db_user else None
    
    is_owner = False
    if team:
        is_owner = (str(team.owner_id) == str(current_internal_id))

    # 2. Determine Scope
    fetch_team_id = team_id
    if is_owner:
        fetch_team_id = None # Force User Token for Owner
        
    # Use strict_token=True for Owner to PREVENT Admin Fallback (Data Leak)
    # If Owner has no token, they should see NOTHING, not Admin's accounts.
    # Use strict_token=True for Owner to PREVENT Admin Fallback (Data Leak)
    # If Owner has no token, they should see NOTHING, not Admin's accounts.
    # CRITICAL SECURITY FIX: If team_id is None (Personal Workspace), strict_token MUST be True.
    use_strict = is_owner or (fetch_team_id is None)
    accounts, error = await AsyncFacebookService.get_all_ad_accounts(user_id, team_id=fetch_team_id, strict_token=use_strict)
    
    # 3. Fallback for Owner: If primary fetch failed (empty/error), retry with Team Token logic
    # This covers edge cases where get_user_token fails but get_team_token (Owner Fallback) works
    if (not accounts or error) and is_owner:
        print(f"DEBUG: Primary fetch failed for owner ({error}), retrying with Team Token Scope...", file=sys.stderr)
        accounts, error = await AsyncFacebookService.get_all_ad_accounts(user_id, team_id=team_id)
    
    if error:
        print(f"❌ Error from FacebookService: {error}", file=sys.stderr)
        # If both failed, return empty but don't error out entirely to allow UI to render
        return []
        
    # Team Ad Account Isolation Logic
    if team:
        # (Already calculated is_owner above)
        
        if not is_owner:
            print(f"🔒 Non-Owner Access. Whitelist: {team.visible_ad_account_ids}", file=sys.stderr)
            # Check Whitelist
            if team.visible_ad_account_ids:
                try:
                    import json
                    whitelist = json.loads(team.visible_ad_account_ids) # List of IDs
                    print(f"DEBUG: Whitelist Loaded: {whitelist}", file=sys.stderr)
                    
                    if isinstance(whitelist, list):
                        # Robust Filter: Handle act_ prefix mismatch
                        filtered_accounts = []
                        whitelist_set = set(str(x) for x in whitelist) # Ensure strings
                        
                        input_ids = [acc.get('id') for acc in accounts]
                        print(f"DEBUG: API Returned IDs: {input_ids}", file=sys.stderr)

                        for acc in accounts:
                            acc_id = str(acc.get('id', ''))
                            # 1. Exact Match
                            if acc_id in whitelist_set:
                                filtered_accounts.append(acc)
                                continue
                            
                            # 2. Try alternate format (remove or add act_)
                            # If DB has '123' and API has 'act_123' -> match
                            # If DB has 'act_123' and API has '123' -> match
                            alt_id = acc_id.replace('act_', '') if 'act_' in acc_id else f'act_{acc_id}'
                            if alt_id in whitelist_set:
                                filtered_accounts.append(acc)
                                continue
                                
                        accounts = filtered_accounts
                        print(f"DEBUG: Filtered Result Count: {len(accounts)}", file=sys.stderr)
                    else:
                        print("⚠ Whitelist is not a list. Blocking all.", file=sys.stderr)
                        accounts = []
                except Exception as e:
                    print(f"❌ Whitelist Parse Error: {e}", file=sys.stderr)
                    accounts = []
            else:
                # STRICT MODE: If no whitelist, Member sees NOTHING.
                print("🔒 No whitelist defined for team member. Access denied.", file=sys.stderr)
                accounts = []

    return accounts

@app.get("/api/dashboard-data")
async def get_dashboard_data(
    account_id: str = None, 
    days: int = 7, 
    user_id: str = Depends(verify_google_token), 
    team: Team = Depends(get_current_team)
):
    team_id = team.id if team else None
    today = datetime.now()
    if team_id:
        # Team Mode: Allow Fallback (Admin/Owner Token)
        strict = False
    else:
        # Personal Mode: STRICT (No Fallback to Admin)
        strict = True

    today = datetime.now()
    if team_id:
        # Team Mode: Allow Fallback (Admin/Owner Token)
        strict = False
    else:
        # Personal Mode: STRICT (No Fallback to Admin)
        strict = True

    if account_id:
        # Pass user_id, days, and team_id - Use async service
        insights = await AsyncFacebookService.get_account_insights(account_id, user_id, days, team_id=team_id, strict_token=strict)
        if insights:
            return {
                "source": "real",
                "account_id": account_id,
                "kpi": insights["kpi"],
                "chart_data": insights["charts"],
                "date_range": insights.get("date_range")
            }
        else:
            print(f"Dashboard Data Fetch Failed for {account_id} - Returning Zeros", file=sys.stderr)
            
            # Generate Zero Data for UI
            from datetime import timedelta
            
            zero_metric = {
                "value": "0", "previous": "(0)", "diff": "0", 
                "change": "0.0%", "is_increase": False, "raw_value": 0
            }
            zero_metric_curr = {**zero_metric, "value": "$0", "previous": "($0)"} # Currency
            zero_metric_pct = {**zero_metric, "value": "0.00%", "previous": "(0.00%)"} # Percent

            kpi_zero = {
                "impressions": zero_metric,
                "link_clicks": zero_metric,
                "ctr": zero_metric_pct,
                "cpc": zero_metric_curr,
                "spend": zero_metric_curr,
                "purchases": zero_metric,
                "add_to_cart": zero_metric,
                "roas": {**zero_metric, "value": "0.00", "previous": "(0.00)"}
            }
            
            # Generate 7 days of zero chart data
            today = datetime.now()
            chart_zero = []
            for i in range(7):
                d = today - timedelta(days=6-i)
                chart_zero.append({"name": d.strftime("%m-%d"), "value": 0})

            return {
                "source": "empty_fallback",
                "kpi": kpi_zero, 
                "chart_data": chart_zero,
                "date_range": {
                    "start": (today - timedelta(days=6)).strftime("%Y-%m-%d"), 
                    "stop": today.strftime("%Y-%m-%d")
                }
            }

    return {
        "source": "mock_fallback",
        "kpi": [],
        "chart_data": []
    }

@app.get("/api/analytics-data")
async def get_analytics_data(
    account_id: str, 
    since: str, 
    until: str, 
    level: str = "account",
    fields: str = None,  # NEW: Optional comma-separated list of metric keys
    user_id: str = Depends(verify_google_token),
    team: Team = Depends(get_current_team)
):
    """
    Endpoint for the Advanced Analytics page.
    
    Args:
        account_id: Facebook Ad Account ID
        since: Start date (YYYY-MM-DD)
        until: End date (YYYY-MM-DD)
        level: Analysis level (account/campaign/adset/ad)
        fields: Optional comma-separated list of metric keys for dynamic field selection
                Example: "spend,roas,purchases,video_p25_watched"
    """
    team_id = team.id if team else None
    
    # CRITICAL: Strict Mode
    strict = True if team_id is None else False
    
    report_data = await AsyncFacebookService.get_custom_report(
        account_id, user_id, since, until, level, 
        team_id=team_id, 
        custom_fields=fields,  # Pass dynamic fields parameter
        strict_token=strict 
    )
    
    if report_data is None:
         raise HTTPException(status_code=400, detail="Failed to fetch analytics data")
         
    return {
        "data": report_data,
        "meta": {
            "level": level,
            "period": f"{since} ~ {until}",
            "custom_fields": fields  # Include in response for debugging
        }
    }

@app.get("/api/analytics-trend")
async def get_analytics_trend_data(
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
    
     # CRITICAL: Strict Mode
    strict = True if team_id is None else False
    
    trend_data = await AsyncFacebookService.get_analytics_trend(
        account_id, user_id, since, until, prev_since, prev_until, 
        team_id=team_id,
        strict_token=strict
    )
    if trend_data is None:
         return []
    return trend_data


if __name__ == "__main__":
    import uvicorn
    print("🚀 STARTING UVICORN SERVER...", file=sys.stderr)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
