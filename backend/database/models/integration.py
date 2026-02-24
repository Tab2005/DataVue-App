# backend/database/models/integration.py
"""
UserIntegration ORM 模型

將第三方服務整合 Token（Facebook、GSC、GA4、AI）
從 User 表中分離，實現單一職責原則。

遷移策略：
  1. 建立此模型後執行 alembic revision --autogenerate
  2. 執行 alembic upgrade head
  3. 執行資料遷移腳本將現有 User Token 複製至此表（scripts/migrate_tokens.py）
  4. 確認資料無誤後，再透過 Alembic 移除 User 表的 Token 欄位
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    UniqueConstraint,
    Index,
)

from database.base import Base


class UserIntegration(Base):
    """
    使用者第三方服務整合快照。

    provider 值（預定義）：
      'facebook'  - Facebook Ads Access Token
      'gsc'       - Google Search Console OAuth Token
      'ga4'       - Google Analytics 4 OAuth Token
      'ai_zeabur' - Zeabur AI Hub API Key
      'ai_gemini' - Google Gemini API Key
    """

    __tablename__ = "user_integrations"

    # ── 主鍵 ──────────────────────────────────────────────────────────────
    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # ── 外鍵 ──────────────────────────────────────────────────────────────
    user_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── 服務提供者識別 ──────────────────────────────────────────────────────
    #   facebook | gsc | ga4 | ai_zeabur | ai_gemini
    provider = Column(String(50), nullable=False)

    # ── Token 欄位（Fernet 加密儲存）─────────────────────────────────────
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expiry = Column(DateTime, nullable=True)

    # ── 額外 Provider 設定（JSON）────────────────────────────────────────
    #   facebook: {"app_id": ..., "app_secret": ..., "default_account_id": ...}
    #   gsc/ga4: {"scope": ..., "token_uri": ...}
    #   ai_zeabur/ai_gemini: {"model": ..., "max_tokens": ...}
    extra_data = Column(JSON, nullable=True, default=dict)

    # ── 稽核時間戳 ─────────────────────────────────────────────────────────
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # ── 約束與索引 ─────────────────────────────────────────────────────────
    __table_args__ = (
        # 每位使用者對每個服務只有一筆整合紀錄
        UniqueConstraint("user_id", "provider", name="uq_user_integration_provider"),
        # 複合查詢索引（最常用的查詢模式：user_id + provider）
        Index("ix_user_integrations_lookup", "user_id", "provider"),
    )

    def __repr__(self) -> str:
        return f"<UserIntegration user={self.user_id!r} provider={self.provider!r}>"
