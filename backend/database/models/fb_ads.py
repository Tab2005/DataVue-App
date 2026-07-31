"""Facebook Ads module ORM models (docs/58)."""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text, text
from sqlalchemy.orm import relationship

from database.base import Base


class FbAdsAnalyticsAiSnapshot(Base):
    """成效分析頁「AI 廣告分析」的快照（docs/58）。

    跟 GA4InsightsSnapshot 不同：這裡沒有天然的 upsert key（表格資料隨篩選/
    排序/勾選指標即時變動），所以每次使用者點「開始 AI 解讀／重新解讀」都會
    建立一筆全新的快照，而不是覆蓋同一筆——分享連結一旦產生就永久凍結在
    分享當下的內容，之後重新解讀不會影響已分享出去的連結。
    """

    __tablename__ = "fb_ads_analytics_ai_snapshots"

    id = Column(String, primary_key=True, default=lambda: f"fas_{uuid.uuid4().hex[:12]}")
    account_id = Column(String(64), nullable=False, index=True)
    team_id = Column(String, ForeignKey("teams.id"), nullable=True)
    level = Column(String(20), nullable=False)  # campaign | adset | ad | account
    date_since = Column(String(10), nullable=False)
    date_until = Column(String(10), nullable=False)
    payload = Column(JSON, nullable=False, default=dict)
    ai_summary = Column(Text, nullable=True)
    ai_summary_generated_at = Column(DateTime, nullable=True)
    share_token = Column(String(64), nullable=True, unique=True, index=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    creator = relationship("User")
