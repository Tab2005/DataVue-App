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

    # 已是絕對路徑
    if ":/" in url[10:] or url.startswith("sqlite:////"):
        return url

    rel = url[len("sqlite:///"):].lstrip("./")

    # 容許舊版 backend/ 前置詞
    rel_norm = rel.replace("\\", "/")
    if rel_norm.startswith("backend/"):
        rel_norm = rel_norm[len("backend/"):]

    abs_path = os.path.join(BASE_DIR, rel_norm)
    return _to_sqlite_url(os.path.abspath(abs_path))


# 預設 SQLite 路徑（本地開發）
SQLITE_DATABASE_URL = _normalize_sqlite_url("sqlite:///./facebook_dashboard.db")

# 生產環境由環境變數覆蓋
DATABASE_URL = os.getenv("DATABASE_URL")


def get_engine():
    """建立並回傳資料庫引擎（自動判斷 SQLite / PostgreSQL）"""
    url = os.getenv("DATABASE_URL")
    
    # 支援 postgres:// 和 postgresql:// 前綴（Zeabur/Heroku 常用）
    if url and (url.startswith("postgresql://") or url.startswith("postgres://")):
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return create_engine(url)

    # Fallback 至 SQLite
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


# 模組載入時驗證連線
if check_db_connection():
    safe_url = str(engine.url).split("@")[-1] if "@" in str(engine.url) else "Database"
    logger.info(f"Database connected successfully: {safe_url}")
else:
    logger.warning("Database connection failed during initialization. Check logs.")
