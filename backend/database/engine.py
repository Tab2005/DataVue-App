# backend/database/engine.py
"""
資料庫引擎、SessionLocal、get_db 依賴。
統一管理 SQLite（開發）/ PostgreSQL（生產）兩種連線模式。
"""

import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/ 根目錄


def _to_sqlite_url(abs_path: str) -> str:
    """將絕對路徑轉為 SQLAlchemy SQLite URL（統一使用正斜線）"""
    return "sqlite:///" + abs_path.replace("\\", "/")


def _normalize_sqlite_url(url: str) -> str:
    """將相對 SQLite URL 解析為以 backend/ 為基準的絕對路徑"""
    if not url or not url.startswith("sqlite:///"):
        return url

    if ":/" in url[10:] or url.startswith("sqlite:////"):
        return url

    rel = url[len("sqlite:///"):].lstrip("./")
    rel_norm = rel.replace("\\", "/")
    if rel_norm.startswith("backend/"):
        rel_norm = rel_norm[len("backend/"):]

    abs_path = os.path.join(BASE_DIR, rel_norm)
    return _to_sqlite_url(os.path.abspath(abs_path))


def _env_int(name: str, default: int, minimum: int = 0) -> int:
    try:
        return max(minimum, int(os.getenv(name, str(default))))
    except (TypeError, ValueError):
        return max(minimum, default)


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


SQLITE_DATABASE_URL = _normalize_sqlite_url("sqlite:///./facebook_dashboard.db")
DATABASE_URL = os.getenv("DATABASE_URL")


def get_engine():
    """建立並回傳資料庫引擎（自動判斷 SQLite / PostgreSQL）"""
    url = os.getenv("DATABASE_URL")

    if url and (url.startswith("postgresql://") or url.startswith("postgres://")):
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        # 每個 HTTP 請求實際會開 2-3 條 session（auth 依賴鏈與端點各自
        # Depends 不同的 get_db，FastAPI 依賴快取不共用），一次頁面載入
        # 4-6 個併發請求就可能耗盡過小的池子；池等待發生在 threadpool
        # （端點已改 def / to_thread）不會凍結 loop，但仍推高尾延遲。
        pool_size = _env_int("DB_POOL_SIZE", 5, minimum=1)
        max_overflow = _env_int("DB_MAX_OVERFLOW", 10, minimum=0)
        pool_timeout = _env_int("DB_POOL_TIMEOUT", 30, minimum=1)
        pool_recycle = _env_int("DB_POOL_RECYCLE", 1800, minimum=30)
        pool_pre_ping = _env_bool("DB_POOL_PRE_PING", True)
        # 鎖/語句等待上限（保險絲）：psycopg2 等待資料庫鎖「沒有預設 timeout」，
        # 一個在 event loop 上直接執行的同步查詢若等到永遠不釋放的鎖，整個
        # backend 會無限凍結且無任何錯誤日誌（2026-07-08 事故第二型態：/health
        # 連續 2.5 分鐘以上無回應、app log 全靜默）。設定 lock_timeout 後任何
        # 鎖等待最多 15 秒即拋錯，statement_timeout 兜底 60 秒防失控長查詢
        # （上限需容納啟動時的 Alembic migration 與報表彙總查詢）。
        lock_timeout_ms = _env_int("DB_LOCK_TIMEOUT_MS", 15000, minimum=1000)
        statement_timeout_ms = _env_int("DB_STATEMENT_TIMEOUT_MS", 60000, minimum=5000)
        return create_engine(
            url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            pool_pre_ping=pool_pre_ping,
            pool_use_lifo=True,
            connect_args={
                "options": (
                    f"-c lock_timeout={lock_timeout_ms} "
                    f"-c statement_timeout={statement_timeout_ms}"
                )
            },
        )

    sqlite_url = os.getenv("SQLITE_DATABASE_URL") or SQLITE_DATABASE_URL
    return create_engine(sqlite_url, connect_args={"check_same_thread": False})


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def check_db_connection() -> bool:
    """驗證資料庫連線是否正常"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        safe_url = str(engine.url).split("@")[-1] if "@" in str(engine.url) else "Database"
        logger.error(f"Database connection failed: {safe_url}. Error: {e}")
        return False


def get_db():
    """FastAPI 依賴注入：提供資料庫 Session，結束後自動關閉"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if check_db_connection():
    safe_url = str(engine.url).split("@")[-1] if "@" in str(engine.url) else "Database"
    logger.info(f"Database connected successfully: {safe_url}")
else:
    logger.warning("Database connection failed during initialization. Check logs.")