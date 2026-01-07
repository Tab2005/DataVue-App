"""
Facebook Dashboard Web App - Backend Entry Point (Modular Version)

此版本使用模組化架構，將啟動邏輯、業務端點、Debug 端點分離到獨立模組。

檔案結構:
    main.py              - 應用程式入口（本檔案）
    core/startup.py      - 啟動邏輯
    routers/facebook.py  - Facebook 業務端點
    routers/debug.py     - Debug 端點
    routers/*.py         - 其他 Router

目標：保持 main.py 在 200 行以內
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

# ============================================================
# Startup Tasks
# ============================================================

from core.startup import run_startup_tasks

# Run all startup tasks (env validation, DB init, migrations, etc.)
try:
    run_startup_tasks()
except Exception as e:
    print(f"❌ Startup failed: {e}", file=sys.stderr)

# ============================================================
# Application Setup
# ============================================================

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    print("🚀 Application starting...")
    yield
    print("👋 Application shutting down...")


app = FastAPI(
    title="Facebook Dashboard API",
    description="Multi-platform analytics dashboard for Facebook Ads, GSC, and more",
    version="2.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Exception Handlers
# ============================================================

from fastapi import HTTPException
from fastapi.responses import JSONResponse
import traceback
from exceptions import AppException


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "detail": exc.detail}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    print(f"Unhandled exception: {exc}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# ============================================================
# Router Registration
# ============================================================

from routers import users, teams, invites, admin, ai, saved_views, gsc
from routers import facebook, debug

# Core Feature Routers
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(teams.router, prefix="/api/teams", tags=["teams"])
app.include_router(invites.router, prefix="/api", tags=["invites"])
app.include_router(admin.router)  # /api/admin
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(saved_views.router)  # /api/saved-views
app.include_router(gsc.router)  # /api/gsc

# Business Routers
app.include_router(facebook.router)  # /api/ad-accounts, /api/dashboard-data, /api/analytics

# Debug Router (consider disabling in production)
app.include_router(debug.router)  # /api/debug/*

# ============================================================
# Auth Endpoints (required for token management)
# ============================================================

from pydantic import BaseModel
from typing import Optional
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from datetime import datetime, timezone

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
security = HTTPBearer()

def verify_google_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify Google OAuth token and return user's google_id."""
    token = credentials.credentials
    try:
        id_info = id_token.verify_oauth2_token(
            token, google_requests.Request(), GOOGLE_CLIENT_ID, clock_skew_in_seconds=60
        )
        return id_info['sub']
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {e}")


class ExchangeRequest(BaseModel):
    app_id: str
    app_secret: str
    short_token: str
    team_id: Optional[str] = None


@app.post("/api/auth/exchange-token")
def exchange_token_endpoint(request: ExchangeRequest, user_id: str = Depends(verify_google_token)):
    """Exchange short-lived token for long-lived token."""
    from auth import TokenManager
    
    success, message = TokenManager.exchange_for_long_lived_token(
        request.app_id, 
        request.app_secret, 
        request.short_token,
        user_id,
        team_id=request.team_id
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message}


@app.get("/api/auth/token-status")
def get_token_status(team_id: Optional[str] = None, user_id: str = Depends(verify_google_token)):
    """Check the expiration status of the user's OR team's Facebook token."""
    from database import SessionLocal, User, Team
    
    session = SessionLocal()
    try:
        target = None
        
        if team_id:
            target = session.query(Team).filter(Team.id == team_id).first()
        else:
            target = session.query(User).filter(User.google_id == user_id).first()
        
        # Check if token exists
        token_exists = False
        if target and hasattr(target, 'fb_access_token') and target.fb_access_token:
            token_exists = len(str(target.fb_access_token)) > 10
        
        if not target or not target.token_expires_at:
            return {
                "expires_at": None,
                "days_remaining": None,
                "is_expired": False,
                "token_exists": token_exists
            }
        
        now = datetime.now(timezone.utc)
        expires_at = target.token_expires_at
        
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
             
        delta = expires_at - now
        days_remaining = delta.days
        
        return {
            "expires_at": expires_at.isoformat(),
            "days_remaining": days_remaining,
            "is_expired": days_remaining < 0,
            "token_exists": token_exists
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
    finally:
        session.close()



# ============================================================
# Health Check
# ============================================================

@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    db_info = "Unknown"
    try:
        db_url = os.getenv("DATABASE_URL", "")
        if "postgresql" in db_url.lower():
            db_info = "PostgreSQL"
        else:
            db_info = "SQLite"
    except:
        pass
    
    return {
        "status": "ok",
        "version": "2.0.0",
        "database_type": db_info,
        "message": "Backend is running (Modular Version)"
    }


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    import uvicorn
    print("🚀 STARTING UVICORN SERVER...", file=sys.stderr)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
