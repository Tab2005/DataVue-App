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
        return os.getenv("GOOGLE_AI_API_KEY")
    
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
