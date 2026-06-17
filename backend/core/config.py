"""
Core Configuration Module
集中管理所有環境變數和應用設定

使用方式:
    from core.config import settings
    
    print(settings.GOOGLE_CLIENT_ID)
    print(settings.DATABASE_URL)
"""

import os
from typing import Optional
from functools import lru_cache
from dotenv import load_dotenv
from pathlib import Path

# 確保環境變數已載入
load_dotenv()


class Settings:
    """
    應用程式設定類別
    所有環境變數集中在此管理
    """
    
    # === 必要設定 ===
    @property
    def GOOGLE_CLIENT_ID(self) -> str:
        return os.getenv("GOOGLE_CLIENT_ID", "")
    
    @property
    def GOOGLE_CLIENT_SECRET(self) -> str:
        return os.getenv("GOOGLE_CLIENT_SECRET", "")
    
    @property
    def ENCRYPTION_KEY(self) -> str:
        return os.getenv("ENCRYPTION_KEY", "")
    
    # === 資料庫設定 ===
    @property
    def DATABASE_URL(self) -> Optional[str]:
        """PostgreSQL 連線字串，若未設定則使用 SQLite"""
        return os.getenv("DATABASE_URL")
    
    @property
    def is_postgres(self) -> bool:
        """是否使用 PostgreSQL"""
        return self.DATABASE_URL is not None
    
    # === Super Admin 設定 ===
    @property
    def SUPER_ADMIN_EMAIL(self) -> str:
        """超級管理員 Email（支援逗號分隔多個）"""
        return os.getenv("SUPER_ADMIN_EMAIL", "")
    
    @property
    def super_admin_emails(self) -> list[str]:
        """解析後的超級管理員 Email 列表"""
        raw = self.SUPER_ADMIN_EMAIL
        if not raw:
            return []
        return [e.strip().lower() for e in raw.split(",") if e.strip()]
    
    # === AI 服務設定 ===
    @property
    def ZEABUR_AI_HUB_API_KEY(self) -> Optional[str]:
        return os.getenv("ZEABUR_AI_HUB_API_KEY")
    
    @property
    def GOOGLE_AI_API_KEY(self) -> Optional[str]:
        return (
            os.getenv("GOOGLE_AI_API_KEY") 
            or os.getenv("GOOGLE_API_KEY") 
            or os.getenv("ZEABUR_AI_HUB_API_KEY")
        )

    @property
    def OPENROUTER_API_KEY(self) -> Optional[str]:
        return (
            os.getenv("OPENROUTER_API_KEY")
            or os.getenv("ZEABUR_AI_HUB_API_KEY")
        )
    
    # === 應用設定 ===
    @property
    def ENV(self) -> str:
        """環境：development / production"""
        return os.getenv("ENV", "development")
    
    @property
    def is_development(self) -> bool:
        return self.ENV == "development"
    
    @property
    def is_production(self) -> bool:
        return self.ENV == "production"
    
    # === LINE Messaging API ===
    @property
    def LINE_CHANNEL_ACCESS_TOKEN(self) -> Optional[str]:
        return os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    
    @property
    def LINE_CHANNEL_SECRET(self) -> Optional[str]:
        return os.getenv("LINE_CHANNEL_SECRET")
    
    @property
    def LINE_BOT_QR_URL(self) -> Optional[str]:
        """LINE 官方帳號 QR Code 或加友連結"""
        return os.getenv("LINE_BOT_QR_URL")
    
    # === URL 設定 ===
    @property
    def FRONTEND_URL(self) -> str:
        """前端網址，用於發送通知中的連結"""
        return os.getenv("FRONTEND_URL", "http://localhost:3000")

    # === Meta Andromeda Storage ===
    @property
    def META_ANDROMEDA_STORAGE_BACKEND(self) -> str:
        """支援 filesystem / s3_compatible"""
        return os.getenv("META_ANDROMEDA_STORAGE_BACKEND", "filesystem")

    @property
    def META_ANDROMEDA_STORAGE_ROOT(self) -> str:
        """Meta Andromeda 素材實際落檔根目錄"""
        configured = os.getenv("META_ANDROMEDA_STORAGE_ROOT")
        if configured:
            return configured
        backend_root = Path(__file__).resolve().parent.parent
        return str(backend_root / "storage" / "meta_andromeda")

    @property
    def META_ANDROMEDA_STORAGE_PUBLIC_BASE_URL(self) -> Optional[str]:
        """
        若未來有靜態檔案代理或 CDN，可提供公開 base URL。
        例如 https://assets.example.com/meta-andromeda
        """
        return os.getenv("META_ANDROMEDA_STORAGE_PUBLIC_BASE_URL")

    @property
    def META_ANDROMEDA_STORAGE_KEY_PREFIX(self) -> str:
        return os.getenv("META_ANDROMEDA_STORAGE_KEY_PREFIX", "meta-andromeda")

    @property
    def META_ANDROMEDA_STORAGE_S3_BUCKET(self) -> Optional[str]:
        return os.getenv("META_ANDROMEDA_STORAGE_S3_BUCKET")

    @property
    def META_ANDROMEDA_STORAGE_S3_REGION(self) -> Optional[str]:
        return os.getenv("META_ANDROMEDA_STORAGE_S3_REGION")

    @property
    def META_ANDROMEDA_STORAGE_S3_ENDPOINT_URL(self) -> Optional[str]:
        return os.getenv("META_ANDROMEDA_STORAGE_S3_ENDPOINT_URL")

    @property
    def META_ANDROMEDA_STORAGE_S3_ACCESS_KEY_ID(self) -> Optional[str]:
        return os.getenv("META_ANDROMEDA_STORAGE_S3_ACCESS_KEY_ID")

    @property
    def META_ANDROMEDA_STORAGE_S3_SECRET_ACCESS_KEY(self) -> Optional[str]:
        return os.getenv("META_ANDROMEDA_STORAGE_S3_SECRET_ACCESS_KEY")

    # === Meta Andromeda Scoring Runtime ===
    @property
    def META_ANDROMEDA_SCORING_PROVIDER(self) -> str:
        """
        auto / heuristic / openrouter
        auto: 有 OpenRouter 金鑰時走 OpenRouter，否則走 heuristic fallback
        """
        return os.getenv("META_ANDROMEDA_SCORING_PROVIDER", "auto").lower()

    @property
    def META_ANDROMEDA_SCORING_MODEL(self) -> str:
        return os.getenv("META_ANDROMEDA_SCORING_MODEL", "deepseek/deepseek-v4-flash")

    @property
    def META_ANDROMEDA_SCORING_MODEL_VERSION(self) -> str:
        return os.getenv("META_ANDROMEDA_SCORING_MODEL_VERSION", "cand_v2026_06_05_a")

    @property
    def META_ANDROMEDA_SCORING_ALLOW_FALLBACK(self) -> bool:
        return os.getenv("META_ANDROMEDA_SCORING_ALLOW_FALLBACK", "true").lower() in {"1", "true", "yes", "on"}

    @property
    def META_ANDROMEDA_SCORE_TIMEOUT_SECONDS(self) -> float:
        return float(os.getenv("META_ANDROMEDA_SCORE_TIMEOUT_SECONDS", "20"))

    @property
    def META_ANDROMEDA_SCORE_MAX_ATTEMPTS(self) -> int:
        return max(1, int(os.getenv("META_ANDROMEDA_SCORE_MAX_ATTEMPTS", "3")))

    @property
    def META_ANDROMEDA_SCORE_RETRY_DELAY_SECONDS(self) -> float:
        return max(0.0, float(os.getenv("META_ANDROMEDA_SCORE_RETRY_DELAY_SECONDS", "5")))

    @property
    def META_ANDROMEDA_SCORE_LOCAL_ASYNC_FALLBACK(self) -> bool:
        return os.getenv("META_ANDROMEDA_SCORE_LOCAL_ASYNC_FALLBACK", "true").lower() in {"1", "true", "yes", "on"}

    @property
    def META_ANDROMEDA_QUEUE_HOST(self) -> str:
        """
        auto / apscheduler / local_async / database_queue / external_webhook / redis_stream
        database_queue 代表 web 端只入列，由獨立 worker host 週期性掃描 queued records。
        """
        return os.getenv("META_ANDROMEDA_QUEUE_HOST", "auto").lower()

    @property
    def META_ANDROMEDA_QUEUE_SWEEP_INTERVAL_SECONDS(self) -> float:
        return max(1.0, float(os.getenv("META_ANDROMEDA_QUEUE_SWEEP_INTERVAL_SECONDS", "5")))

    @property
    def META_ANDROMEDA_EXTERNAL_QUEUE_ENDPOINT(self) -> Optional[str]:
        return os.getenv("META_ANDROMEDA_EXTERNAL_QUEUE_ENDPOINT")

    @property
    def META_ANDROMEDA_EXTERNAL_QUEUE_TOKEN(self) -> Optional[str]:
        return os.getenv("META_ANDROMEDA_EXTERNAL_QUEUE_TOKEN")

    @property
    def META_ANDROMEDA_EXTERNAL_QUEUE_TIMEOUT_SECONDS(self) -> float:
        return max(1.0, float(os.getenv("META_ANDROMEDA_EXTERNAL_QUEUE_TIMEOUT_SECONDS", "10")))

    @property
    def META_ANDROMEDA_EXTERNAL_QUEUE_SIGNING_SECRET(self) -> Optional[str]:
        return os.getenv("META_ANDROMEDA_EXTERNAL_QUEUE_SIGNING_SECRET")

    @property
    def META_ANDROMEDA_EXTERNAL_WORKER_SHARED_SECRET(self) -> Optional[str]:
        return os.getenv("META_ANDROMEDA_EXTERNAL_WORKER_SHARED_SECRET")

    @property
    def META_ANDROMEDA_EXTERNAL_WORKER_TOKEN(self) -> Optional[str]:
        return os.getenv("META_ANDROMEDA_EXTERNAL_WORKER_TOKEN")

    @property
    def META_ANDROMEDA_REDIS_STREAM_KEY(self) -> str:
        return os.getenv("META_ANDROMEDA_REDIS_STREAM_KEY", "meta_andromeda:score_queue")

    @property
    def META_ANDROMEDA_REDIS_STREAM_GROUP(self) -> str:
        return os.getenv("META_ANDROMEDA_REDIS_STREAM_GROUP", "meta_andromeda_workers")

    @property
    def META_ANDROMEDA_REDIS_STREAM_CONSUMER(self) -> str:
        return os.getenv("META_ANDROMEDA_REDIS_STREAM_CONSUMER", "datavue-consumer")

    @property
    def META_ANDROMEDA_REDIS_STREAM_BATCH_SIZE(self) -> int:
        return max(1, int(os.getenv("META_ANDROMEDA_REDIS_STREAM_BATCH_SIZE", "20")))

    @property
    def META_ANDROMEDA_REDIS_STREAM_RECLAIM_IDLE_MS(self) -> int:
        return max(1000, int(os.getenv("META_ANDROMEDA_REDIS_STREAM_RECLAIM_IDLE_MS", "30000")))

    @property
    def META_ANDROMEDA_REDIS_STREAM_RECLAIM_BATCH_SIZE(self) -> int:
        return max(1, int(os.getenv("META_ANDROMEDA_REDIS_STREAM_RECLAIM_BATCH_SIZE", "20")))
    
    # === 驗證方法 ===
    def validate_required(self) -> list[str]:
        """驗證必要環境變數，回傳缺少的變數名稱列表"""
        required = ["GOOGLE_CLIENT_ID", "ENCRYPTION_KEY"]
        missing = []
        for var in required:
            if not getattr(self, var):
                missing.append(var)
        return missing


@lru_cache()
def get_settings() -> Settings:
    """取得設定單例"""
    return Settings()


# 全域設定實例
settings = get_settings()
