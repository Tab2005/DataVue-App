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

# --- Encryption Key Startup Check ---
from auth import get_encryption_key
try:
    from cryptography.fernet import Fernet
    test_key = get_encryption_key()
    Fernet(test_key)
    print(f"[OK] Encryption Key validated successfully (starts with {test_key[:5]}...)", file=sys.stderr)
except Exception as e:
    print(f"❌ CRITICAL ENCRYPTION KEY ERROR: {e}", file=sys.stderr)
# -----------------------------------------

print("Starting Main Application...", file=sys.stderr)
from fastapi import FastAPI, HTTPException, Depends, status
print("[OK] FastAPI imported", file=sys.stderr)
print(f"[INFO] Current Dir: {os.getcwd()}", file=sys.stderr)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from auth import TokenManager
# Robust Imports with Error Handling
try:
    import alembic.config
    import alembic.command
except Exception as e:
    print(f"⚠️ ALEMBIC IMPORT ERROR: {e}", file=sys.stderr)
    alembic = None

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
from routers import users
from routers import teams
from routers import invites
from routers import admin
from routers import ai
from routers import saved_views
try:
    from routers import gsc
except Exception as e:
    print(f"CRITICAL: Failed to import GSC router: {e}", file=sys.stderr)
    gsc = None

try:
    from routers import permissions
except Exception as e:
    print(f"CRITICAL: Failed to import Permissions router: {e}", file=sys.stderr)
    permissions = None
import auth
from dependencies import get_current_team, get_db, require_module

# ...

# Include Routers



# ... (imports)


from contextlib import asynccontextmanager

# Initialize Database
# Load environment variables FIRST
load_dotenv()

# Initialize Database with Error Handling
try:
    # AUTO MIGRATION FOR ZEABUR
    # Run alembic upgrade head programmatically
    print("Running Database Migrations...")
    try:
        alembic_cfg = alembic.config.Config("alembic.ini")
        alembic.command.upgrade(alembic_cfg, "head")
        print("Database Migrations Applied.")
    except Exception as alembic_err:
        print(f"⚠️ Alembic Migration Warning (continuing with fallback): {alembic_err}")
    
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

    # --- PATCH: Auto-patch Users table for GSC ---
    try:
        if inspector.has_table("users"):
            user_columns = [c["name"] for c in inspector.get_columns("users")]
            print(f"DEBUG: Current Users Columns: {user_columns}")
            
            for col, col_type in [("gsc_access_token", "VARCHAR"), ("gsc_refresh_token", "VARCHAR"), ("gsc_expires_at", "TIMESTAMP")]:
                if col not in user_columns:
                    print(f"⚠️ Schema Drift: Adding '{col}' to users table...")
                    with engine.connect() as conn:
                        conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {col_type}"))
                        conn.commit()
    except Exception as e:
        print(f"⚠️ User Schema Patching Warning: {e}")

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

# --- Register Routers ---
# GSC Router
if gsc:
    app.include_router(gsc.router)
    print("[OK] GSC Router registered", file=sys.stderr)

# Permissions Router
if permissions:
    app.include_router(permissions.router)
    print("[OK] Permissions Router registered", file=sys.stderr)

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
    try:
        error_dump = f"GLOBAL ERROR: {str(exc)}\n\nTraceback:\n{traceback.format_exc()}"
        with open("debug_global_error.log", "w", encoding="utf-8") as f:
            f.write(error_dump)
    except:
        pass
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
app.include_router(gsc.router) # /api/gsc


@app.get("/api/auth/token-status")
def get_token_status(team_id: Optional[str] = None, user_id: str = Depends(verify_google_token)):
    """Check the expiration status of the user's OR team's Facebook token."""
    session = SessionLocal()
    try:
        target = None
        print(f"[DEBUG] token-status called: team_id={team_id}, user_id={user_id}", file=sys.stderr)
        
        if team_id:
            target = session.query(Team).filter(Team.id == team_id).first()
            if target:
                print(f"[DEBUG] Team found: {target.name}, token_expires_at={target.token_expires_at}", file=sys.stderr)
            else:
                print(f"[DEBUG] Team NOT found for id={team_id}", file=sys.stderr)
        else:
            target = session.query(User).filter(User.google_id == user_id).first()
            if target:
                print(f"[DEBUG] User found: {target.name}, token_expires_at={target.token_expires_at}", file=sys.stderr)
            else:
                print(f"[DEBUG] User NOT found for google_id={user_id}", file=sys.stderr)
        
        # Check if token actually exists (not just expiration date)
        token_exists = False
        if target and hasattr(target, 'fb_access_token') and target.fb_access_token:
            token_exists = len(str(target.fb_access_token)) > 10  # Token should be > 10 chars
        
        print(f"[DEBUG] token_exists check: {token_exists}", file=sys.stderr)
        
        if not target or not target.token_expires_at:
            print(f"[DEBUG] Returning None - target exists: {target is not None}, has expires_at: {hasattr(target, 'token_expires_at') and target.token_expires_at if target else 'N/A'}", file=sys.stderr)
            return {
                 "expires_at": None,
                 "days_remaining": None,
                 "is_expired": False,
                 "token_exists": token_exists  # NEW: indicate if token actually exists
             }
        
        now = datetime.now(timezone.utc)
        expires_at = target.token_expires_at
        
        # Ensure timezone awareness compatibility
        if expires_at.tzinfo is None:
             expires_at = expires_at.replace(tzinfo=timezone.utc)
             
        delta = expires_at - now
        days_remaining = delta.days
        
        print(f"[DEBUG] Returning: expires_at={expires_at.isoformat()}, days_remaining={days_remaining}, token_exists={token_exists}", file=sys.stderr)
        return {
            "expires_at": expires_at.isoformat(),
            "days_remaining": days_remaining,
            "is_expired": days_remaining < 0,
            "token_exists": token_exists  # NEW: indicate if token actually exists
        }
    except Exception as e:
        print(f"Error checking token status: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
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

@app.get("/api/debug/test-auction-metrics")
async def test_auction_metrics(
    account_id: str,
    level: str = "all",  # New: test all levels by default
    user_id: str = Depends(verify_google_token),
    team: Team = Depends(get_current_team)
):
    """
    測試 auction_bid 和 auction_competitiveness 指標
    這是一個 DEBUG 端點，用於驗證 Facebook API 是否回傳這些指標
    
    Usage: 
        /api/debug/test-auction-metrics?account_id=act_XXXXX
        /api/debug/test-auction-metrics?account_id=act_XXXXX&level=ad
        /api/debug/test-auction-metrics?account_id=act_XXXXX&level=all (default)
    """
    import httpx
    
    team_id = team.id if team else None
    
    # Get token
    from auth import TokenManager
    if team_id:
        access_token = TokenManager.get_team_token(team_id)
    else:
        access_token = TokenManager.get_user_token(user_id, allow_fallback=False)
    
    if not access_token:
        return {"error": "No access token found", "team_id": team_id}
    
    # Fields to request
    base_fields = ["spend", "impressions", "auction_bid", "auction_competitiveness"]
    
    # Determine which levels to test
    levels_to_test = ["campaign", "adset", "ad"] if level == "all" else [level]
    
    results = {}
    
    async with httpx.AsyncClient() as client:
        for test_level in levels_to_test:
            # Add level-specific name field
            if test_level == "campaign":
                fields = ["campaign_name", "campaign_id"] + base_fields
            elif test_level == "adset":
                fields = ["adset_name", "adset_id"] + base_fields
            else:  # ad
                fields = ["ad_name", "ad_id"] + base_fields
            
            url = f"https://graph.facebook.com/v24.0/{account_id}/insights"
            params = {
                "level": test_level,
                "fields": ",".join(fields),
                "date_preset": "last_7d",
                "access_token": access_token
            }
            
            try:
                response = await client.get(url, params=params, timeout=30.0)
                data = response.json()
                
                # Check for errors
                if "error" in data:
                    results[test_level] = {
                        "success": False,
                        "error": data["error"].get("message", "Unknown error"),
                        "requested_fields": fields
                    }
                    continue
                
                # Parse response
                insights = data.get("data", [])
                
                # Check which fields were returned
                returned_fields = set()
                sample_row = None
                if insights:
                    sample_row = insights[0]
                    returned_fields = set(sample_row.keys())
                
                # Check if auction metrics are available
                auction_bid_available = "auction_bid" in returned_fields
                auction_competitiveness_available = "auction_competitiveness" in returned_fields
                
                results[test_level] = {
                    "success": True,
                    "total_rows": len(insights),
                    "auction_bid": {
                        "available": auction_bid_available,
                        "sample_value": sample_row.get("auction_bid") if sample_row else None
                    },
                    "auction_competitiveness": {
                        "available": auction_competitiveness_available,
                        "sample_value": sample_row.get("auction_competitiveness") if sample_row else None
                    },
                    "returned_fields": list(returned_fields),
                    "sample_data": insights[0] if insights else None
                }
            except Exception as e:
                results[test_level] = {
                    "success": False,
                    "error": str(e)
                }
    
    # Summary
    any_available = any(
        r.get("auction_bid", {}).get("available") or r.get("auction_competitiveness", {}).get("available")
        for r in results.values() if isinstance(r, dict)
    )
    
    return {
        "account_id": account_id,
        "tested_levels": levels_to_test,
        "any_auction_metrics_available": any_available,
        "results_by_level": results
    }

@app.get("/api/debug/test-ad-library")
async def test_ad_library(
    search_term: str,
    country: str = "TW",  # Taiwan by default
    user_id: str = Depends(verify_google_token),
    team: Team = Depends(get_current_team)
):
    """
    測試 Facebook Ad Library API
    搜尋指定品牌/粉絲頁的正在刊登廣告
    
    Usage: /api/debug/test-ad-library?search_term=品牌名稱
    
    參數:
        search_term: 品牌名稱或粉絲頁名稱
        country: 國家代碼 (預設 TW)
    """
    import httpx
    
    team_id = team.id if team else None
    
    # Get token
    from auth import TokenManager
    if team_id:
        access_token = TokenManager.get_team_token(team_id)
    else:
        access_token = TokenManager.get_user_token(user_id, allow_fallback=False)
    
    if not access_token:
        return {"error": "No access token found", "team_id": team_id}
    
    # Ad Library API endpoint
    url = "https://graph.facebook.com/v24.0/ads_archive"
    
    # Fields to request
    fields = [
        "id",
        "ad_creation_time",
        "ad_creative_bodies",      # 廣告文案
        "ad_creative_link_captions",
        "ad_creative_link_descriptions",
        "ad_creative_link_titles", # 廣告標題
        "ad_delivery_start_time",
        "ad_delivery_stop_time",
        "ad_snapshot_url",         # 廣告預覽連結
        "page_id",
        "page_name",               # 粉絲頁名稱
        "publisher_platforms",     # 發佈平台 (facebook, instagram)
        "impressions",             # 曝光範圍
        "spend",                   # 花費範圍
    ]
    
    params = {
        "search_terms": search_term,
        "ad_reached_countries": f"['{country}']",
        "ad_active_status": "ACTIVE",  # 只搜尋正在刊登的廣告
        "fields": ",".join(fields),
        "limit": 10,  # 最多取 10 筆
        "access_token": access_token
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=30.0)
            data = response.json()
            
            # Check for errors
            if "error" in data:
                return {
                    "success": False,
                    "search_term": search_term,
                    "country": country,
                    "error": data["error"].get("message", "Unknown error"),
                    "error_code": data["error"].get("code"),
                    "error_type": data["error"].get("type"),
                    "hint": "可能需要申請 ads_archive 權限或完成身份驗證"
                }
            
            # Parse response
            ads = data.get("data", [])
            
            # Format results
            formatted_ads = []
            for ad in ads:
                formatted_ads.append({
                    "id": ad.get("id"),
                    "page_name": ad.get("page_name"),
                    "page_id": ad.get("page_id"),
                    "ad_bodies": ad.get("ad_creative_bodies", []),  # 文案
                    "ad_titles": ad.get("ad_creative_link_titles", []),  # 標題
                    "platforms": ad.get("publisher_platforms", []),
                    "start_time": ad.get("ad_delivery_start_time"),
                    "snapshot_url": ad.get("ad_snapshot_url"),  # 預覽連結
                    "impressions": ad.get("impressions"),
                    "spend": ad.get("spend"),
                })
            
            return {
                "success": True,
                "search_term": search_term,
                "country": country,
                "total_ads_found": len(ads),
                "ads": formatted_ads,
                "paging": data.get("paging"),  # 分頁資訊
                "note": "如果沒有結果，可能是該地區不支援 Ad Library API 或需要申請 ads_archive 權限"
            }
    except Exception as e:
        return {
            "success": False,
            "search_term": search_term,
            "error": str(e)
        }

@app.get("/api/debug/check-permissions")
async def check_token_permissions(
    user_id: str = Depends(verify_google_token),
    team: Team = Depends(get_current_team)
):
    """
    檢查目前 Access Token 的權限範圍
    顯示可以存取哪些 Facebook/Instagram API
    
    Usage: /api/debug/check-permissions
    """
    import httpx
    
    team_id = team.id if team else None
    
    # Get token
    from auth import TokenManager
    if team_id:
        access_token = TokenManager.get_team_token(team_id)
        token_source = f"Team #{team_id}"
    else:
        access_token = TokenManager.get_user_token(user_id, allow_fallback=False)
        token_source = f"User {user_id}"
    
    if not access_token:
        return {"error": "No access token found", "team_id": team_id}
    
    results = {
        "token_source": token_source,
        "permissions": [],
        "pages": [],
        "instagram_accounts": [],
        "ad_accounts": []
    }
    
    async with httpx.AsyncClient() as client:
        # 1. Check permissions
        try:
            perm_resp = await client.get(
                "https://graph.facebook.com/v24.0/me/permissions",
                params={"access_token": access_token},
                timeout=15.0
            )
            perm_data = perm_resp.json()
            if "data" in perm_data:
                results["permissions"] = [
                    {
                        "permission": p.get("permission"),
                        "status": p.get("status")
                    }
                    for p in perm_data["data"]
                ]
        except Exception as e:
            results["permissions_error"] = str(e)
        
        # 2. Check Facebook Pages (managed by user)
        try:
            pages_resp = await client.get(
                "https://graph.facebook.com/v24.0/me/accounts",
                params={
                    "fields": "id,name,category,fan_count,instagram_business_account{id,username,followers_count}",
                    "access_token": access_token
                },
                timeout=15.0
            )
            pages_data = pages_resp.json()
            if "data" in pages_data:
                for page in pages_data["data"]:
                    page_info = {
                        "id": page.get("id"),
                        "name": page.get("name"),
                        "category": page.get("category"),
                        "fan_count": page.get("fan_count")
                    }
                    # Check if IG is linked
                    ig_account = page.get("instagram_business_account")
                    if ig_account:
                        page_info["instagram_linked"] = True
                        results["instagram_accounts"].append({
                            "ig_id": ig_account.get("id"),
                            "username": ig_account.get("username"),
                            "followers": ig_account.get("followers_count"),
                            "linked_page": page.get("name")
                        })
                    else:
                        page_info["instagram_linked"] = False
                    results["pages"].append(page_info)
        except Exception as e:
            results["pages_error"] = str(e)
        
        # 3. Check Ad Accounts
        try:
            ads_resp = await client.get(
                "https://graph.facebook.com/v24.0/me/adaccounts",
                params={
                    "fields": "id,name,account_status,currency",
                    "limit": 10,
                    "access_token": access_token
                },
                timeout=15.0
            )
            ads_data = ads_resp.json()
            if "data" in ads_data:
                results["ad_accounts"] = [
                    {
                        "id": acc.get("id"),
                        "name": acc.get("name"),
                        "status": acc.get("account_status"),
                        "currency": acc.get("currency")
                    }
                    for acc in ads_data["data"]
                ]
        except Exception as e:
            results["ad_accounts_error"] = str(e)
    
    # Summary
    granted_permissions = [p["permission"] for p in results["permissions"] if p.get("status") == "granted"]
    
    results["summary"] = {
        "total_permissions": len(granted_permissions),
        "granted_permissions": granted_permissions,
        "can_read_ads": "ads_read" in granted_permissions,
        "can_manage_ads": "ads_management" in granted_permissions,
        "can_read_pages": "pages_read_engagement" in granted_permissions or "pages_show_list" in granted_permissions,
        "can_read_instagram": "instagram_basic" in granted_permissions or "instagram_business_basic" in granted_permissions,
        "total_pages": len(results["pages"]),
        "total_instagram_accounts": len(results["instagram_accounts"]),
        "total_ad_accounts": len(results["ad_accounts"])
    }
    
    return results

@app.get("/api/public/test-threads")
async def test_threads_api_public(access_token: str):
    """
    公開測試 Threads API (不需登入)
    直接傳入 Access Token 作為 query 參數
    
    Usage: /api/public/test-threads?access_token=YOUR_TOKEN
    """
    import httpx
    
    if not access_token:
        return {"error": "access_token is required"}
    
    results = {
        "threads_permissions": [],
        "threads_profile": None,
        "threads_posts": [],
        "threads_insights": None,
        "errors": []
    }
    
    THREADS_API_VERSION = "v24.0"
    BASE_URL = f"https://graph.threads.net/{THREADS_API_VERSION}"
    
    async with httpx.AsyncClient() as client:
        # 1. Check Threads-specific permissions
        try:
            perm_resp = await client.get(
                "https://graph.facebook.com/v24.0/me/permissions",
                params={"access_token": access_token},
                timeout=15.0
            )
            perm_data = perm_resp.json()
            if "error" in perm_data:
                results["errors"].append(f"Permissions: {perm_data['error'].get('message', 'Unknown')}")
            elif "data" in perm_data:
                threads_perms = [
                    {"permission": p.get("permission"), "status": p.get("status")}
                    for p in perm_data["data"]
                    if "threads" in p.get("permission", "").lower()
                ]
                results["threads_permissions"] = threads_perms
        except Exception as e:
            results["errors"].append(f"Permissions check failed: {str(e)}")
        
        # 2. Get Threads User Profile
        try:
            profile_resp = await client.get(
                f"{BASE_URL}/me",
                params={
                    "fields": "id,username,name,threads_profile_picture_url,threads_biography",
                    "access_token": access_token
                },
                timeout=15.0
            )
            profile_data = profile_resp.json()
            if "error" in profile_data:
                results["errors"].append(f"Profile: {profile_data['error'].get('message', 'Unknown')}")
            else:
                results["threads_profile"] = profile_data
        except Exception as e:
            results["errors"].append(f"Profile fetch failed: {str(e)}")
        
        # 3. Get Recent Threads Posts
        try:
            posts_resp = await client.get(
                f"{BASE_URL}/me/threads",
                params={
                    "fields": "id,text,timestamp,media_type,permalink,is_quote_post",
                    "limit": 10,
                    "access_token": access_token
                },
                timeout=15.0
            )
            posts_data = posts_resp.json()
            if "error" in posts_data:
                results["errors"].append(f"Posts: {posts_data['error'].get('message', 'Unknown')}")
            elif "data" in posts_data:
                results["threads_posts"] = posts_data["data"]
        except Exception as e:
            results["errors"].append(f"Posts fetch failed: {str(e)}")
        
        # 4. Get Account Insights
        if results.get("threads_profile") and results["threads_profile"].get("id"):
            threads_user_id = results["threads_profile"]["id"]
            try:
                insights_resp = await client.get(
                    f"{BASE_URL}/{threads_user_id}/threads_insights",
                    params={
                        "metric": "views,likes,replies,reposts,quotes,followers_count",
                        "access_token": access_token
                    },
                    timeout=15.0
                )
                insights_data = insights_resp.json()
                if "error" in insights_data:
                    results["errors"].append(f"Insights: {insights_data['error'].get('message', 'Unknown')}")
                elif "data" in insights_data:
                    results["threads_insights"] = insights_data["data"]
            except Exception as e:
                results["errors"].append(f"Insights fetch failed: {str(e)}")
    
    # Summary
    results["summary"] = {
        "has_threads_basic": any(p["permission"] == "threads_basic" and p["status"] == "granted" for p in results["threads_permissions"]),
        "has_threads_insights": any(p["permission"] == "threads_manage_insights" and p["status"] == "granted" for p in results["threads_permissions"]),
        "has_threads_publish": any(p["permission"] == "threads_content_publish" and p["status"] == "granted" for p in results["threads_permissions"]),
        "profile_loaded": results["threads_profile"] is not None,
        "posts_count": len(results["threads_posts"]),
        "insights_available": results["threads_insights"] is not None,
        "total_errors": len(results["errors"])
    }
    
    return results

@app.get("/api/debug/test-threads")
async def test_threads_api(
    user_id: str = Depends(verify_google_token),
    team: Team = Depends(get_current_team)
):
    """
    測試 Threads API 權限與可用資料
    檢查 threads_basic, threads_manage_insights 等權限
    
    Usage: /api/debug/test-threads
    """
    import httpx
    
    team_id = team.id if team else None
    
    # Get token
    from auth import TokenManager
    if team_id:
        access_token = TokenManager.get_team_token(team_id)
        token_source = f"Team #{team_id}"
    else:
        access_token = TokenManager.get_user_token(user_id, allow_fallback=False)
        token_source = f"User {user_id}"
    
    if not access_token:
        return {"error": "No access token found", "team_id": team_id}
    
    results = {
        "token_source": token_source,
        "threads_permissions": [],
        "threads_profile": None,
        "threads_posts": [],
        "threads_insights": None,
        "errors": []
    }
    
    THREADS_API_VERSION = "v24.0"
    BASE_URL = f"https://graph.threads.net/{THREADS_API_VERSION}"
    
    async with httpx.AsyncClient() as client:
        # 1. Check Threads-specific permissions from graph.facebook.com
        try:
            perm_resp = await client.get(
                "https://graph.facebook.com/v24.0/me/permissions",
                params={"access_token": access_token},
                timeout=15.0
            )
            perm_data = perm_resp.json()
            if "data" in perm_data:
                # Filter only threads-related permissions
                threads_perms = [
                    {"permission": p.get("permission"), "status": p.get("status")}
                    for p in perm_data["data"]
                    if "threads" in p.get("permission", "").lower()
                ]
                results["threads_permissions"] = threads_perms
        except Exception as e:
            results["errors"].append(f"Permissions check failed: {str(e)}")
        
        # 2. Get Threads User Profile
        try:
            profile_resp = await client.get(
                f"{BASE_URL}/me",
                params={
                    "fields": "id,username,name,threads_profile_picture_url,threads_biography",
                    "access_token": access_token
                },
                timeout=15.0
            )
            profile_data = profile_resp.json()
            if "error" in profile_data:
                results["errors"].append(f"Profile: {profile_data['error'].get('message', 'Unknown error')}")
            else:
                results["threads_profile"] = profile_data
        except Exception as e:
            results["errors"].append(f"Profile fetch failed: {str(e)}")
        
        # 3. Get Recent Threads Posts
        try:
            posts_resp = await client.get(
                f"{BASE_URL}/me/threads",
                params={
                    "fields": "id,text,timestamp,media_type,permalink,is_quote_post",
                    "limit": 10,
                    "access_token": access_token
                },
                timeout=15.0
            )
            posts_data = posts_resp.json()
            if "error" in posts_data:
                results["errors"].append(f"Posts: {posts_data['error'].get('message', 'Unknown error')}")
            elif "data" in posts_data:
                results["threads_posts"] = posts_data["data"]
        except Exception as e:
            results["errors"].append(f"Posts fetch failed: {str(e)}")
        
        # 4. Get Account Insights (requires threads_manage_insights)
        if results.get("threads_profile") and results["threads_profile"].get("id"):
            threads_user_id = results["threads_profile"]["id"]
            try:
                insights_resp = await client.get(
                    f"{BASE_URL}/{threads_user_id}/threads_insights",
                    params={
                        "metric": "views,likes,replies,reposts,quotes,followers_count",
                        "access_token": access_token
                    },
                    timeout=15.0
                )
                insights_data = insights_resp.json()
                if "error" in insights_data:
                    results["errors"].append(f"Insights: {insights_data['error'].get('message', 'Unknown error')}")
                elif "data" in insights_data:
                    results["threads_insights"] = insights_data["data"]
            except Exception as e:
                results["errors"].append(f"Insights fetch failed: {str(e)}")
    
    # Summary
    results["summary"] = {
        "has_threads_basic": any(p["permission"] == "threads_basic" and p["status"] == "granted" for p in results["threads_permissions"]),
        "has_threads_insights": any(p["permission"] == "threads_manage_insights" and p["status"] == "granted" for p in results["threads_permissions"]),
        "has_threads_publish": any(p["permission"] == "threads_content_publish" and p["status"] == "granted" for p in results["threads_permissions"]),
        "profile_loaded": results["threads_profile"] is not None,
        "posts_count": len(results["threads_posts"]),
        "insights_available": results["threads_insights"] is not None,
        "total_errors": len(results["errors"])
    }
    
    return results

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

@app.get("/api/ad-accounts", dependencies=[Depends(require_module("fb_ads"))])
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

@app.get("/api/dashboard-data", dependencies=[Depends(require_module("fb_ads"))])
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

@app.get("/api/analytics-data", dependencies=[Depends(require_module("fb_ads"))])
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

@app.get("/api/analytics-trend", dependencies=[Depends(require_module("fb_ads"))])
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
