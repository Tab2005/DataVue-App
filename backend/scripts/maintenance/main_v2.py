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
# Core Endpoints
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


@app.get("/api/auth/token-status")
async def get_token_status(
    team_id: str = None,
):
    """Check the expiration status of the user's OR team's Facebook token."""
    from fastapi import Depends
    from dependencies import get_current_user
    from database import SessionLocal, User, Team
    from datetime import datetime, timezone
    
    # This is a placeholder - full implementation should use proper dependencies
    return {"message": "Use /api/auth/token-status endpoint from auth module"}


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    import uvicorn
    print("🚀 STARTING UVICORN SERVER...", file=sys.stderr)
    uvicorn.run("main_v2:app", host="0.0.0.0", port=8000, reload=True)
