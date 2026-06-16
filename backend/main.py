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
import time
import logging
from dotenv import load_dotenv

# Load environment variables FIRST
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# 記錄應用程式啟動時間（供 /health 端點計算 uptime）
START_TIME = time.time()

# Configure Logging（統一使用 core/logging.py）
from core.logging import setup_logging
setup_logging()
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

# 速率限制
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from limiter import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("🚀 DataVue Application starting...")

    from core.scheduler import start_scheduler, stop_scheduler

    try:
        scheduler_status = await start_scheduler()
        logger.info(f"⏰ Scheduler bootstrap finished: {scheduler_status}")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}", exc_info=True)

    yield

    logger.info("👋 DataVue Application shutting down...")
    stop_scheduler()



app = FastAPI(
    title="DataVue Analytics API",
    description="Multi-platform analytics dashboard for Facebook Ads, GSC, and more",
    version="2.1.0",
    lifespan=lifespan
)

# 掛載速率限制到 app
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# CORS Middleware
raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

# Regex：生產域名僅允許 HTTPS，localhost/127.0.0.1 允許 HTTP 或 HTTPS
allow_origin_regex = (
    r"https://.*\.?(tabisme\.com|zeabur\.app|sitetegy\.com)(:\d+)?$"  # 生產：僅 HTTPS
    r"|https?://localhost(:\d+)?$"                        # 本地開發：允許 HTTP
    r"|https?://127\.0\.0\.1(:\d+)?$"                    # 本地 IP
)

logger.info(f"CORS Configured: Allowed Origins={allowed_origins}, Regex={allow_origin_regex}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# GZip compression for large JSON responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ============================================================
# Exception Handlers
# ============================================================

import re

def _add_cors_headers_to_response(request: Request, response: JSONResponse) -> JSONResponse:
    origin = request.headers.get("origin")
    if not origin:
        return response
    if re.match(allow_origin_regex, origin):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    return response


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    response = JSONResponse(
        status_code=429,
        content={
            "error": "請求過於頻繁",
            "detail": "已超過速率限制，請稍後再試",
            "retry_after": getattr(exc, "retry_after", None),
        },
        headers={"Retry-After": str(getattr(exc, "retry_after", 60))},
    )
    return _add_cors_headers_to_response(request, response)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    response = JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "error_code": exc.error_code,
            "details": exc.details,
            "error_type": "app_error"
        }
    )
    return _add_cors_headers_to_response(request, response)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    response = JSONResponse(
        status_code=exc.status_code,
        content={
            "error": str(exc.detail),
            "error_code": f"HTTP_{exc.status_code}",
            "error_type": "http_error"
        }
    )
    return _add_cors_headers_to_response(request, response)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    logger.error(traceback.format_exc())
    response = JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "error_code": "INTERNAL_SERVER_ERROR",
            "error_type": "unhandled_exception"
        }
    )
    return _add_cors_headers_to_response(request, response)


# ============================================================
# Router Registration
# ============================================================

from routers import users, teams, invites, admin, ai, saved_views, gsc, permissions
from routers import facebook, debug, ga4, auth, reports, line
from routers.metrics import router as metrics_router
from modules.meta_andromeda import router as meta_andromeda_router

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
app.include_router(reports.router)
app.include_router(line.router)
app.include_router(meta_andromeda_router, prefix="/api/meta-andromeda", tags=["meta_andromeda"])

# Metrics Registry (4.6)
app.include_router(metrics_router)

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
# Health Check
# ============================================================

from datetime import datetime, timezone
from sqlalchemy import text

@app.get("/health", tags=["system"])
async def health_check():
    """
    完整健康檢查端點（供 Load Balancer、Zeabur、Docker 使用）。
    
    Returns:
        200 OK：應用正常
        503 Service Unavailable：資料庫異常
    """
    from database import SessionLocal
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": int(time.time() - START_TIME),
        "version": "2.1.0",
        "checks": {}
    }

    # 資料庫連線檢查
    db = None
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"error: {str(e)}"
    finally:
        if db:
            db.close()

    # Redis 連線檢查（選用服務，不影響整體狀態）
    try:
        from redis_cache import get_redis_client
        redis = get_redis_client()
        if redis:
            redis.ping()
            health_status["checks"]["redis"] = "ok"
        else:
            health_status["checks"]["redis"] = "not_configured"
    except Exception as e:
        health_status["checks"]["redis"] = f"error: {str(e)}"

    try:
        from core.scheduler import get_scheduler_status

        health_status["checks"]["scheduler"] = get_scheduler_status()
    except Exception as e:
        health_status["checks"]["scheduler"] = f"error: {str(e)}"

    try:
        from modules.meta_andromeda.service import MetaAndromedaService

        db = SessionLocal()
        try:
            health_status["checks"]["meta_andromeda"] = MetaAndromedaService.get_runtime_health(db)
        finally:
            db.close()
    except Exception as e:
        health_status["checks"]["meta_andromeda"] = f"error: {str(e)}"

    if health_status["status"] == "unhealthy":
        return JSONResponse(status_code=503, content=health_status)

    return health_status


@app.get("/api/health", tags=["system"])
def health_check_legacy():
    """健康檢查端點（舊路徑，向後相容）。"""
    return {
        "status": "ok",
        "version": "2.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": "DataVue Backend is healthy"
    }


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Manually starting Uvicorn server...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
