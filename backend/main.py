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
    from core.watchdog import start_watchdog

    try:
        # 事故診斷工具（2026-07-08）：loop 凍結時自動傾印全 thread 堆疊
        # + 每分鐘記錄 RSS 曲線，詳 core/watchdog.py
        start_watchdog()
    except Exception as e:
        logger.error(f"Failed to start watchdog: {e}", exc_info=True)

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
            "error_type": "unhandled_exception",
            "details": str(exc)
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
from modules.contribution import router as contribution_router
from modules.ga4.insights_router import router as ga4_insights_router

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
app.include_router(ga4_insights_router, prefix="/api/ga4/insights", tags=["ga4_insights"])

# AI & Features
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(saved_views.router)
app.include_router(reports.router)
app.include_router(line.router)
app.include_router(meta_andromeda_router, prefix="/api/meta-andromeda", tags=["meta_andromeda"])
app.include_router(contribution_router, prefix="/api/contribution", tags=["contribution"])

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
from modules.auth.dependencies import require_super_admin

# 2026-07-02 修復（P0-2）：git commit 僅於啟動時計算一次存入 module 級變數，
# 避免公開的 /health 端點每次探活都 fork 子行程執行 `git rev-parse`。
_GIT_COMMIT = "unknown"
try:
    import subprocess
    _GIT_COMMIT = subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
    ).decode().strip()
except Exception:
    _GIT_COMMIT = os.getenv("ZEABUR_GIT_COMMIT_SHA") or os.getenv("COMMIT_REF") or "unknown"


@app.get("/health", tags=["system"])
async def health_check():
    """
    公開健康檢查端點（供 Load Balancer、Zeabur、Docker 使用，無需認證）。

    僅回傳存活/就緒必要資訊，不含任何 API 金鑰、使用者統計等內部組態。
    需要除錯用的詳細資訊請改用 /health/detail（限 Super Admin）。

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
        "commit": _GIT_COMMIT,
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
async def health_check_legacy():
    """健康檢查端點（舊路徑，向後相容）。"""
    return await health_check()


@app.get("/health/detail", tags=["system"])
async def health_detail(_admin: bool = Depends(require_super_admin())):
    """
    授權版健康檢查端點（限 Super Admin）。

    在 /health 的基礎欄位之上，附加內部除錯資訊：各 AI 供應商 API 金鑰長度、
    資料庫中持有金鑰的用戶數、Meta Andromeda scoring provider 設定。
    這些資訊過去曾直接暴露在無需認證的 /health，屬組態外洩，故收斂至此。
    """
    from database import SessionLocal
    from core.config import settings

    base = await health_check()
    if isinstance(base, JSONResponse):
        import json
        health_status = json.loads(base.body)
        status_code = base.status_code
    else:
        health_status = base
        status_code = 200

    google_key = os.getenv("GOOGLE_AI_API_KEY") or ""
    google_key_alt = os.getenv("GOOGLE_API_KEY") or ""
    openrouter_key = os.getenv("OPENROUTER_API_KEY") or ""
    zeabur_key = os.getenv("ZEABUR_AI_HUB_API_KEY") or ""

    # 統計資料庫中有金鑰的用戶數
    db_users_with_gemini_key_count = 0
    db_users_with_openrouter_key_count = 0
    try:
        temp_session = SessionLocal()
        try:
            from database.models.user import User
            db_users_with_gemini_key_count = temp_session.query(User).filter(
                User.gemini_api_key.isnot(None),
                User.gemini_api_key != ""
            ).count()
            db_users_with_openrouter_key_count = temp_session.query(User).filter(
                User.openrouter_api_key.isnot(None),
                User.openrouter_api_key != ""
            ).count()
        finally:
            temp_session.close()
    except Exception:
        pass

    health_status["ai_config_debug"] = {
        "GOOGLE_AI_API_KEY_len": len(google_key),
        "GOOGLE_API_KEY_len": len(google_key_alt),
        "OPENROUTER_API_KEY_len": len(openrouter_key),
        "ZEABUR_AI_HUB_API_KEY_len": len(zeabur_key),
        "settings_GOOGLE_AI_API_KEY_len": len(settings.GOOGLE_AI_API_KEY or "") if settings.GOOGLE_AI_API_KEY else 0,
        "settings_OPENROUTER_API_KEY_len": len(settings.OPENROUTER_API_KEY or "") if settings.OPENROUTER_API_KEY else 0,
        "db_users_with_gemini_key_count": db_users_with_gemini_key_count,
        "db_users_with_openrouter_key_count": db_users_with_openrouter_key_count,
        "META_ANDROMEDA_SCORING_PROVIDER": settings.META_ANDROMEDA_SCORING_PROVIDER,
    }

    if status_code != 200:
        return JSONResponse(status_code=status_code, content=health_status)
    return health_status


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Manually starting Uvicorn server...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)


