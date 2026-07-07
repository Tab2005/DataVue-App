"""
Meta Andromeda Worker Process Entry Point (docs/24 Wave 2)

獨立於 web API process 之外執行 Meta Andromeda 的評分/觀測匯入負載，避免
評分工作佔用 web process 的 event loop（docs/24 問題一根因）。

啟動方式（與 main.py 共用同一個 image/repo）：
    SERVICE_ROLE=worker python worker_main.py

只掛載一個 /healthz endpoint 供 PaaS 健康檢查使用，不掛任何業務 router——
評分/觀測匯入的實際處理都在 lifespan 啟動的 AsyncIOScheduler 排程 job 裡
執行（stream consumer / reclaim / db queue sweeper，見 core/scheduler.py）。
"""

import logging
import os
import time

from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

# 若部署時忘了設定 SERVICE_ROLE，這裡強制補上 worker——這支程式的存在意義
# 就是只做 worker 的事，不應該意外用 all/web 的角色邏輯跑起來。
os.environ.setdefault("SERVICE_ROLE", "worker")

from core.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

START_TIME = time.time()

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from core.config import settings

if settings.SERVICE_ROLE != "worker":
    logger.warning(
        "worker_main.py 啟動但 SERVICE_ROLE=%s（非 worker）。請確認部署設定 SERVICE_ROLE=worker，"
        "否則週報排程/Meta Andromeda 排程的角色分流會與預期不符。",
        settings.SERVICE_ROLE,
    )


def _run_minimal_worker_startup() -> None:
    """比照 core.startup.run_startup_tasks()，但只做 worker 需要的部分。

    不重複跑 migrations/權限種子/super admin 同步——那些是 web service 的
    職責，兩邊都跑會有 race 風險（例如同時執行 alembic upgrade）；worker
    只需要確保 DB 連得上、Meta Andromeda 種子資料存在、快取失效監聽已啟動。
    """
    from core.security import validate_encryption_key as check_key
    from database import SessionLocal, check_db_connection

    if not check_key():
        logger.critical("Encryption key validation failed. Worker 將無法解密使用者儲存的 API 金鑰。")

    if not check_db_connection():
        logger.warning("Worker database connection check failed on startup; scheduler jobs 會各自重試。")

    try:
        from modules.meta_andromeda.repository import repository

        db = SessionLocal()
        try:
            repository.ensure_seed_data(db)
            logger.info("Meta Andromeda seed data verified/initialized (worker).")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to seed Meta Andromeda data on worker startup: {e}")

    try:
        from modules.meta_andromeda.cache_invalidation import start_invalidation_listener

        start_invalidation_listener()
    except Exception as e:
        logger.warning(f"Failed to start Meta Andromeda cache invalidation listener (worker): {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 DataVue Meta Andromeda worker starting...")

    _run_minimal_worker_startup()

    from core.scheduler import start_scheduler, stop_scheduler

    try:
        scheduler_status = await start_scheduler()
        logger.info(f"⏰ Worker scheduler bootstrap finished: {scheduler_status}")
    except Exception as e:
        logger.error(f"Failed to start worker scheduler: {e}", exc_info=True)

    yield

    logger.info("👋 DataVue Meta Andromeda worker shutting down...")
    # wait=True：讓正在跑的評分/匯入 job 有機會跑完才真正關閉排程器，換取比較
    # 優雅的滾動部署（見 core/scheduler.py::stop_scheduler 的說明）。
    stop_scheduler(wait=True)


app = FastAPI(
    title="DataVue Meta Andromeda Worker",
    description=(
        "Background worker process for Meta Andromeda scoring/observation-import "
        "(docs/24 Wave 2). No business routers mounted here."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.get("/healthz")
async def healthz():
    """供 Zeabur/Docker 健康檢查使用；同時回報 scheduler 是否真的在跑，
    方便從外部快速判斷「worker 是不是忘了設定 SERVICE_ROLE=worker」這類誤部署。
    """
    from core.scheduler import get_scheduler_status
    from database import check_db_connection

    scheduler_status = get_scheduler_status()
    db_ok = check_db_connection()

    body = {
        "status": "ok" if (scheduler_status.get("running") and db_ok) else "degraded",
        "service_role": settings.SERVICE_ROLE,
        "uptime_seconds": int(time.time() - START_TIME),
        "scheduler": scheduler_status,
        "database": "ok" if db_ok else "error",
    }

    try:
        from redis_cache import get_redis_client

        redis = get_redis_client()
        if redis:
            redis.ping()
            body["redis"] = "ok"
        else:
            body["redis"] = "not_configured"
    except Exception as e:
        body["redis"] = f"error: {e}"

    if body["status"] != "ok":
        return JSONResponse(status_code=503, content=body)
    return body


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    logger.info("🚀 Manually starting Uvicorn server for Meta Andromeda worker...")
    uvicorn.run("worker_main:app", host="0.0.0.0", port=port, reload=False)
