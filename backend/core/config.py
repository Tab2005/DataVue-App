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
    
    # === 服務角色（docs/24 Wave 2：Meta Andromeda worker process 拆分）===
    @property
    def SERVICE_ROLE(self) -> str:
        """
        web | worker | all（預設）。

        - all：單機開發預設，行為與拆分前完全一致——Meta Andromeda 評分/匯入
          與 API 同一個 process（Wave 1 的 to_thread 化已確保不會卡住 event loop）。
        - web：只處理 HTTP 請求，不在本 process 註冊/執行 Meta Andromeda 的
          排程 job（stream consumer/reclaim/db queue sweeper/週報閉環）；
          評分與觀測匯入一律經 Redis stream 派工給 worker process。
        - worker：不掛業務 router，只執行 Meta Andromeda 相關排程 job；透過
          backend/worker_main.py 啟動。
        """
        return os.getenv("SERVICE_ROLE", "all").strip().lower()

    @property
    def is_web_role(self) -> bool:
        return self.SERVICE_ROLE == "web"

    @property
    def is_worker_role(self) -> bool:
        return self.SERVICE_ROLE == "worker"

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
        return os.getenv("META_ANDROMEDA_SCORING_MODEL", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free")

    @property
    def META_ANDROMEDA_SCORING_MODEL_VERSION(self) -> str:
        return os.getenv("META_ANDROMEDA_SCORING_MODEL_VERSION", "cand_v2026_06_05_a")

    @property
    def META_ANDROMEDA_SCORING_ALLOW_FALLBACK(self) -> bool:
        return os.getenv("META_ANDROMEDA_SCORING_ALLOW_FALLBACK", "true").lower() in {"1", "true", "yes", "on"}

    @property
    def META_ANDROMEDA_SCORE_TIMEOUT_SECONDS(self) -> float:
        return float(os.getenv("META_ANDROMEDA_SCORE_TIMEOUT_SECONDS", "90"))

    @property
    def META_ANDROMEDA_SCORE_MAX_ATTEMPTS(self) -> int:
        return max(1, int(os.getenv("META_ANDROMEDA_SCORE_MAX_ATTEMPTS", "3")))

    @property
    def META_ANDROMEDA_STRUCTURED_OUTPUT_ENABLED(self) -> bool:
        """優先以 OpenRouter response_format=json_schema 取得結構化輸出，失敗才退回
        regex 解析（docs/20 P2-2）。預設開啟——失敗會優雅退回現有 regex 路徑，風險低。"""
        return os.getenv("META_ANDROMEDA_STRUCTURED_OUTPUT_ENABLED", "true").lower() in {"1", "true", "yes", "on"}

    @property
    def META_ANDROMEDA_SELF_CONSISTENCY_ENABLED(self) -> bool:
        """對高價值請求（事後補評/回測）取樣 N 次取中位數，而非互動式 Score Lab 單次評分
        （docs/20 P2-2）。預設關閉——會讓這類請求的 AI 呼叫量與延遲乘以 N 倍，須明確啟用。"""
        return os.getenv("META_ANDROMEDA_SELF_CONSISTENCY_ENABLED", "false").lower() in {"1", "true", "yes", "on"}

    @property
    def META_ANDROMEDA_SELF_CONSISTENCY_SAMPLES(self) -> int:
        return max(1, int(os.getenv("META_ANDROMEDA_SELF_CONSISTENCY_SAMPLES", "3")))

    @property
    def META_ANDROMEDA_SCORE_RETRY_DELAY_SECONDS(self) -> float:
        return max(0.0, float(os.getenv("META_ANDROMEDA_SCORE_RETRY_DELAY_SECONDS", "5")))

    @property
    def META_ANDROMEDA_SCORE_MAX_CONCURRENCY(self) -> int:
        return max(1, int(os.getenv("META_ANDROMEDA_SCORE_MAX_CONCURRENCY", "2")))

    @property
    def META_ANDROMEDA_OBSERVATION_MAX_CONCURRENCY(self) -> int:
        return max(1, int(os.getenv("META_ANDROMEDA_OBSERVATION_MAX_CONCURRENCY", "5")))

    @property
    def META_ANDROMEDA_STALE_PROCESSING_MINUTES(self) -> int:
        return max(5, int(os.getenv("META_ANDROMEDA_STALE_PROCESSING_MINUTES", "30")))

    @property
    def META_ANDROMEDA_UPLOAD_MAX_BYTES(self) -> int:
        return max(1, int(os.getenv("META_ANDROMEDA_UPLOAD_MAX_BYTES", str(15 * 1024 * 1024))))

    @property
    def META_ANDROMEDA_OBSERVED_DOWNLOAD_MAX_BYTES(self) -> int:
        return max(1, int(os.getenv("META_ANDROMEDA_OBSERVED_DOWNLOAD_MAX_BYTES", str(20 * 1024 * 1024))))

    @property
    def META_ANDROMEDA_ALLOWED_MEDIA_HOSTS(self) -> list[str]:
        raw = os.getenv(
            "META_ANDROMEDA_ALLOWED_MEDIA_HOSTS",
            "cdn.example.com,fbcdn.net,scontent.xx.fbcdn.net,lookaside.fbsbx.com",
        )
        return [item.strip().lower() for item in raw.split(",") if item.strip()]

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
    def META_ANDROMEDA_WEEKLY_LOOP_ENABLED(self) -> bool:
        """每帳戶每週自動跑 drift report -> 校準資料集 sync -> 校準管線（docs/20 P2-6）。
        新 profile 仍需人工 promote，這個排程本身不會改變任何生效中的評分行為，預設開啟。"""
        return os.getenv("META_ANDROMEDA_WEEKLY_LOOP_ENABLED", "true").lower() in {"1", "true", "yes", "on"}

    @property
    def META_ANDROMEDA_WEEKLY_LOOP_DAY_OF_WEEK(self) -> str:
        return os.getenv("META_ANDROMEDA_WEEKLY_LOOP_DAY_OF_WEEK", "mon")

    @property
    def META_ANDROMEDA_WEEKLY_LOOP_HOUR(self) -> int:
        return max(0, min(23, int(os.getenv("META_ANDROMEDA_WEEKLY_LOOP_HOUR", "3"))))

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

    # ── Contribution（MMM 貢獻分析）殭屍 snapshot 回收（docs/27 任務 2.2）──
    # apscheduler 為 in-memory date-trigger：server 在 job 執行前重啟、或
    # scheduler/local fallback 皆不可用（503 路徑）都會留下永久卡在
    # queued/processing 的 snapshot，前端輪詢無限轉圈。定期掃描並標為 failed。
    @property
    def CONTRIBUTION_STALE_QUEUED_MINUTES(self) -> int:
        return max(1, int(os.getenv("CONTRIBUTION_STALE_QUEUED_MINUTES", "10")))

    @property
    def CONTRIBUTION_STALE_PROCESSING_MINUTES(self) -> int:
        # 分析實測耗時 45-90 秒（docs/21 任務 1.2 效能驗收）；30 分鐘是足夠的
        # 安全倍數，避免誤殺仍在執行中的正常分析。
        return max(5, int(os.getenv("CONTRIBUTION_STALE_PROCESSING_MINUTES", "30")))

    @property
    def CONTRIBUTION_STALE_SWEEP_INTERVAL_SECONDS(self) -> float:
        return max(60.0, float(os.getenv("CONTRIBUTION_STALE_SWEEP_INTERVAL_SECONDS", "900")))

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
