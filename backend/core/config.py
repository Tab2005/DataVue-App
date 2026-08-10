"""
Core Configuration Module
集中管理所有環境變數和應用設定

使用方式:
    from core.config import settings

    print(settings.GOOGLE_CLIENT_ID)
    print(settings.DATABASE_URL)
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 確保環境變數已載入（.env 內容併入 os.environ，供下方 BaseSettings 建構時讀取）
load_dotenv()


class Settings(BaseSettings):
    """
    應用程式設定類別
    所有環境變數集中在此管理

    docs/07_audits_and_reviews/CODE_REVIEW_ACTION_PLAN_2026-07-01.md P1-3：
    改用 Pydantic BaseSettings 取得型別驗證與轉換。與舊版純 property + os.getenv()
    的差異：舊版每次存取都即時重新讀 os.environ，這裡改成建構時讀一次並存成欄位——
    測試若要在測試中途覆寫設定，須改用 monkeypatch.setattr(settings, "FIELD", value)
    直接改欄位值（validate_assignment=True 讓型別轉換/正規化/clamp 邏輯在重新賦值時
    仍會套用），而不是 monkeypatch.setenv()（那只會改 os.environ，不會反映到已建構
    好的欄位上）。
    """

    model_config = SettingsConfigDict(
        case_sensitive=True,
        extra="ignore",
        validate_assignment=True,
    )

    # === 必要設定 ===
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    ENCRYPTION_KEY: str = ""

    # === 資料庫設定 ===
    DATABASE_URL: Optional[str] = None
    """PostgreSQL 連線字串，若未設定則使用 SQLite"""

    @property
    def is_postgres(self) -> bool:
        """是否使用 PostgreSQL"""
        return self.DATABASE_URL is not None

    # === Super Admin 設定 ===
    SUPER_ADMIN_EMAIL: str = ""
    """超級管理員 Email（支援逗號分隔多個）"""

    @property
    def super_admin_emails(self) -> list[str]:
        """解析後的超級管理員 Email 列表"""
        raw = self.SUPER_ADMIN_EMAIL
        if not raw:
            return []
        return [e.strip().lower() for e in raw.split(",") if e.strip()]

    # === AI 服務設定 ===
    ZEABUR_AI_HUB_API_KEY: Optional[str] = None

    GOOGLE_AI_API_KEY_ENV: Optional[str] = Field(default=None, validation_alias="GOOGLE_AI_API_KEY")
    GOOGLE_API_KEY_ENV: Optional[str] = Field(default=None, validation_alias="GOOGLE_API_KEY")

    @property
    def GOOGLE_AI_API_KEY(self) -> Optional[str]:
        return self.GOOGLE_AI_API_KEY_ENV or self.GOOGLE_API_KEY_ENV or self.ZEABUR_AI_HUB_API_KEY

    OPENROUTER_API_KEY_ENV: Optional[str] = Field(default=None, validation_alias="OPENROUTER_API_KEY")

    @property
    def OPENROUTER_API_KEY(self) -> Optional[str]:
        return self.OPENROUTER_API_KEY_ENV or self.ZEABUR_AI_HUB_API_KEY

    # === 應用設定 ===
    ENV: str = "development"
    """環境：development / production"""

    @property
    def is_development(self) -> bool:
        return self.ENV == "development"

    @property
    def is_production(self) -> bool:
        return self.ENV == "production"

    # === 服務角色（docs/24 Wave 2：Meta Andromeda worker process 拆分）===
    SERVICE_ROLE: str = "all"
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

    @property
    def is_web_role(self) -> bool:
        return self.SERVICE_ROLE == "web"

    @property
    def is_worker_role(self) -> bool:
        return self.SERVICE_ROLE == "worker"

    # === LINE Messaging API ===
    LINE_CHANNEL_ACCESS_TOKEN: Optional[str] = None
    LINE_CHANNEL_SECRET: Optional[str] = None
    LINE_BOT_QR_URL: Optional[str] = None
    """LINE 官方帳號 QR Code 或加友連結"""

    # === URL 設定 ===
    FRONTEND_URL: str = "http://localhost:3000"
    """前端網址，用於發送通知中的連結"""

    # === Meta Andromeda Storage ===
    META_ANDROMEDA_STORAGE_BACKEND: str = "filesystem"
    """支援 filesystem / s3_compatible"""

    META_ANDROMEDA_STORAGE_ROOT: Optional[str] = None
    """Meta Andromeda 素材實際落檔根目錄；未設定時於 model_post_init 填入預設值"""

    META_ANDROMEDA_STORAGE_PUBLIC_BASE_URL: Optional[str] = None
    """
    若未來有靜態檔案代理或 CDN，可提供公開 base URL。
    例如 https://assets.example.com/meta-andromeda
    """

    META_ANDROMEDA_STORAGE_KEY_PREFIX: str = "meta-andromeda"
    META_ANDROMEDA_STORAGE_S3_BUCKET: Optional[str] = None
    META_ANDROMEDA_STORAGE_S3_REGION: Optional[str] = None
    META_ANDROMEDA_STORAGE_S3_ENDPOINT_URL: Optional[str] = None
    META_ANDROMEDA_STORAGE_S3_ACCESS_KEY_ID: Optional[str] = None
    META_ANDROMEDA_STORAGE_S3_SECRET_ACCESS_KEY: Optional[str] = None

    def model_post_init(self, __context) -> None:
        if not self.META_ANDROMEDA_STORAGE_ROOT:
            backend_root = Path(__file__).resolve().parent.parent
            self.META_ANDROMEDA_STORAGE_ROOT = str(backend_root / "storage" / "meta_andromeda")

    # === Meta Andromeda Scoring Runtime ===
    META_ANDROMEDA_SCORING_PROVIDER: str = "auto"
    """
    auto / heuristic / openrouter
    auto: 有 OpenRouter 金鑰時走 OpenRouter，否則走 heuristic fallback
    """

    META_ANDROMEDA_SCORING_MODEL: str = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"
    META_ANDROMEDA_SCORING_MODEL_VERSION: str = "cand_v2026_06_05_a"
    META_ANDROMEDA_SCORING_ALLOW_FALLBACK: bool = True
    META_ANDROMEDA_SCORE_TIMEOUT_SECONDS: float = 90.0
    META_ANDROMEDA_SCORE_MAX_ATTEMPTS: int = 3

    META_ANDROMEDA_STRUCTURED_OUTPUT_ENABLED: bool = True
    """優先以 OpenRouter response_format=json_schema 取得結構化輸出，失敗才退回
    regex 解析（docs/20 P2-2）。預設開啟——失敗會優雅退回現有 regex 路徑，風險低。"""

    META_ANDROMEDA_SELF_CONSISTENCY_ENABLED: bool = False
    """對高價值請求（事後補評/回測）取樣 N 次取中位數，而非互動式 Score Lab 單次評分
    （docs/20 P2-2）。預設關閉——會讓這類請求的 AI 呼叫量與延遲乘以 N 倍，須明確啟用。"""

    META_ANDROMEDA_SELF_CONSISTENCY_SAMPLES: int = 3
    META_ANDROMEDA_SCORE_RETRY_DELAY_SECONDS: float = 5.0
    META_ANDROMEDA_SCORE_MAX_CONCURRENCY: int = 2
    META_ANDROMEDA_OBSERVATION_MAX_CONCURRENCY: int = 5
    META_ANDROMEDA_STALE_PROCESSING_MINUTES: int = 30
    META_ANDROMEDA_UPLOAD_MAX_BYTES: int = 15 * 1024 * 1024
    META_ANDROMEDA_OBSERVED_DOWNLOAD_MAX_BYTES: int = 20 * 1024 * 1024

    META_ANDROMEDA_ALLOWED_MEDIA_HOSTS_RAW: str = Field(
        default="cdn.example.com,fbcdn.net,scontent.xx.fbcdn.net,lookaside.fbsbx.com",
        validation_alias="META_ANDROMEDA_ALLOWED_MEDIA_HOSTS",
    )

    @property
    def META_ANDROMEDA_ALLOWED_MEDIA_HOSTS(self) -> list[str]:
        return [item.strip().lower() for item in self.META_ANDROMEDA_ALLOWED_MEDIA_HOSTS_RAW.split(",") if item.strip()]

    META_ANDROMEDA_SCORE_LOCAL_ASYNC_FALLBACK: bool = True

    META_ANDROMEDA_QUEUE_HOST: str = "auto"
    """
    auto / apscheduler / local_async / database_queue / external_webhook / redis_stream
    database_queue 代表 web 端只入列，由獨立 worker host 週期性掃描 queued records。
    """

    META_ANDROMEDA_QUEUE_SWEEP_INTERVAL_SECONDS: float = 5.0
    META_ANDROMEDA_EXTERNAL_QUEUE_ENDPOINT: Optional[str] = None

    META_ANDROMEDA_WEEKLY_LOOP_ENABLED: bool = True
    """每帳戶每週自動跑 drift report -> 校準資料集 sync -> 校準管線（docs/20 P2-6）。
    新 profile 仍需人工 promote，這個排程本身不會改變任何生效中的評分行為，預設開啟。"""

    META_ANDROMEDA_WEEKLY_LOOP_DAY_OF_WEEK: str = "mon"
    META_ANDROMEDA_WEEKLY_LOOP_HOUR: int = 3

    META_ANDROMEDA_EXTERNAL_QUEUE_TOKEN: Optional[str] = None
    META_ANDROMEDA_EXTERNAL_QUEUE_TIMEOUT_SECONDS: float = 10.0
    META_ANDROMEDA_EXTERNAL_QUEUE_SIGNING_SECRET: Optional[str] = None
    META_ANDROMEDA_EXTERNAL_WORKER_SHARED_SECRET: Optional[str] = None
    META_ANDROMEDA_INTERNAL_WORKER_BASE_URL: Optional[str] = None
    META_ANDROMEDA_INTERNAL_WORKER_TIMEOUT_SECONDS: float = 10.0
    META_ANDROMEDA_INTERNAL_WORKER_SHARED_SECRET: Optional[str] = None
    META_ANDROMEDA_INTERNAL_WORKER_TOKEN: Optional[str] = None

    # ── Contribution（MMM 貢獻分析）殭屍 snapshot 回收（docs/27 任務 2.2）──
    # apscheduler 為 in-memory date-trigger：server 在 job 執行前重啟、或
    # scheduler/local fallback 皆不可用（503 路徑）都會留下永久卡在
    # queued/processing 的 snapshot，前端輪詢無限轉圈。定期掃描並標為 failed。
    CONTRIBUTION_STALE_QUEUED_MINUTES: int = 10
    CONTRIBUTION_STALE_PROCESSING_MINUTES: int = 30
    """分析實測耗時 45-90 秒（docs/21 任務 1.2 效能驗收）；30 分鐘是足夠的
    安全倍數，避免誤殺仍在執行中的正常分析。"""
    CONTRIBUTION_STALE_SWEEP_INTERVAL_SECONDS: float = 900.0

    META_ANDROMEDA_EXTERNAL_WORKER_TOKEN: Optional[str] = None

    META_ANDROMEDA_REDIS_STREAM_KEY: str = "meta_andromeda:score_queue"
    META_ANDROMEDA_REDIS_STREAM_GROUP: str = "meta_andromeda_workers"
    META_ANDROMEDA_REDIS_STREAM_CONSUMER: str = "datavue-consumer"
    META_ANDROMEDA_REDIS_STREAM_BATCH_SIZE: int = 20
    META_ANDROMEDA_REDIS_STREAM_RECLAIM_IDLE_MS: int = 30000
    META_ANDROMEDA_REDIS_STREAM_RECLAIM_BATCH_SIZE: int = 20

    # === 正規化 / clamp 驗證器（延續舊版 property 內的 .lower()/.strip()/max()/min()）===

    @field_validator("SERVICE_ROLE", "META_ANDROMEDA_SCORING_PROVIDER", "META_ANDROMEDA_QUEUE_HOST", mode="before")
    @classmethod
    def _normalize_lower(cls, v) -> str:
        return str(v).strip().lower()

    @field_validator(
        "META_ANDROMEDA_SCORE_MAX_ATTEMPTS",
        "META_ANDROMEDA_SCORE_MAX_CONCURRENCY",
        "META_ANDROMEDA_OBSERVATION_MAX_CONCURRENCY",
        "META_ANDROMEDA_SELF_CONSISTENCY_SAMPLES",
        "META_ANDROMEDA_REDIS_STREAM_BATCH_SIZE",
        "META_ANDROMEDA_REDIS_STREAM_RECLAIM_BATCH_SIZE",
        "META_ANDROMEDA_UPLOAD_MAX_BYTES",
        "META_ANDROMEDA_OBSERVED_DOWNLOAD_MAX_BYTES",
        "CONTRIBUTION_STALE_QUEUED_MINUTES",
        mode="after",
    )
    @classmethod
    def _floor_at_1(cls, v: int) -> int:
        return max(1, v)

    @field_validator(
        "META_ANDROMEDA_STALE_PROCESSING_MINUTES", "CONTRIBUTION_STALE_PROCESSING_MINUTES", mode="after"
    )
    @classmethod
    def _floor_at_5(cls, v: int) -> int:
        return max(5, v)

    @field_validator("META_ANDROMEDA_REDIS_STREAM_RECLAIM_IDLE_MS", mode="after")
    @classmethod
    def _floor_at_1000(cls, v: int) -> int:
        return max(1000, v)

    @field_validator("META_ANDROMEDA_WEEKLY_LOOP_HOUR", mode="after")
    @classmethod
    def _clamp_hour(cls, v: int) -> int:
        return max(0, min(23, v))

    @field_validator("META_ANDROMEDA_SCORE_RETRY_DELAY_SECONDS", mode="after")
    @classmethod
    def _floor_at_0_0(cls, v: float) -> float:
        return max(0.0, v)

    @field_validator(
        "META_ANDROMEDA_QUEUE_SWEEP_INTERVAL_SECONDS",
        "META_ANDROMEDA_EXTERNAL_QUEUE_TIMEOUT_SECONDS",
        "META_ANDROMEDA_INTERNAL_WORKER_TIMEOUT_SECONDS",
        mode="after",
    )
    @classmethod
    def _floor_at_1_0(cls, v: float) -> float:
        return max(1.0, v)

    @field_validator("CONTRIBUTION_STALE_SWEEP_INTERVAL_SECONDS", mode="after")
    @classmethod
    def _floor_at_60_0(cls, v: float) -> float:
        return max(60.0, v)

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
