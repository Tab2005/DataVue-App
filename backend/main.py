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
import logging
from dotenv import load_dotenv

# Load environment variables FIRST
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

# ============================================================
# Startup Tasks
# ============================================================

from core.startup import run_startup_tasks

# Run all startup tasks (env validation, DB init, migrations, etc.)
try:
    if not run_startup_tasks():
        logger.critical("Startup tasks failed. Application may be unstable.")
except Exception as e:
    logger.error(f"Startup critical failure: {e}")

# ============================================================
# Application Setup
# ============================================================

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import traceback
from exceptions import AppException


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("🚀 DataVue Application starting...")
    yield
    logger.info("👋 DataVue Application shutting down...")


app = FastAPI(
    title="DataVue Analytics API",
    description="Multi-platform analytics dashboard for Facebook Ads, GSC, and more",
    version="2.1.0",
    lifespan=lifespan
)

# CORS Middleware
raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

# If in production, ensure common patterns are included OR log them
logger.info(f"CORS Allowed Origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"], # Ensure custom headers are visible if needed
)

# GZip compression for large JSON responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ============================================================
# Exception Handlers
# ============================================================

# ============================================================
# Exception Handlers
# ============================================================

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "error_code": exc.error_code,
            "details": exc.details,
            "error_type": "app_error"
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": str(exc.detail),
            "error_code": f"HTTP_{exc.status_code}",
            "error_type": "http_error"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "error_code": "INTERNAL_SERVER_ERROR",
            "error_type": "unhandled_exception"
        }
    )


# ============================================================
# Router Registration
# ============================================================

from routers import users, teams, invites, admin, ai, saved_views, gsc, permissions
from routers import facebook, debug, ga4, auth

# Authentication & Users
app.include_router(auth.router)
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(permissions.router)

# Collaboration & Structure
app.include_router(teams.router, prefix="/api/teams", tags=["teams"])
app.include_router(invites.router, prefix="/api", tags=["invites"])

# Business Routers (Data Sources)
app.include_router(facebook.router)
app.include_router(gsc.router)
app.include_router(ga4.router)

# AI & Features
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(saved_views.router)

# Administration
app.include_router(admin.router)
app.include_router(admin.emergency_router)

# Debug Router (Controlled by environment)
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
if DEBUG_MODE:
    logger.info("🛠️ DEBUG_MODE is enabled. Mounting debug router.")
    app.include_router(debug.router)
else:
    logger.debug("Debug router is disabled (DEBUG_MODE=false).")

# ============================================================
# Health Check (Simplified due to startup.py handling core validation)
# ============================================================

@app.get("/api/health", tags=["system"])
def health_check():
    """Health check endpoint."""
    from datetime import datetime
    return {
        "status": "ok",
        "version": "2.1.0",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "DataVue Backend is healthy"
    }


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Manually starting Uvicorn server...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
