# backend/database/models/contribution.py
"""MMM 廣告活動貢獻衡量模組 ORM models（docs/21 任務 1.1）

三張資料表：
  - ContributionDailyMetric：活動每日數據快取（Meta Insights level=campaign, time_increment=1）
  - ContributionCampaignGroup：活動分組設定（auto 規則建議 / manual 使用者調整）
  - ContributionSnapshot：分析結果快照（queued/processing/completed/failed，背景任務狀態輪詢）

與 Meta Andromeda 的共用邊界僅限「模式」（模組骨架、require_module 權限、背景任務 +
狀態輪詢、TokenManager 取 token）；引擎與資料表互不共用（見 docs/21 第一章）。
"""

import uuid
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, text
from sqlalchemy.orm import relationship

from database.base import Base


class ContributionDailyMetric(Base):
    """活動每日數據快照（FB Insights campaign-level daily）。

    唯一約束 (account_id, date, campaign_id, metric_key) 確保重抓時 upsert 不產生重複列。
    actions_payload 保留完整原始 actions 陣列，未來換 y 變數（GA4/CRM 訂單）時不需重抓。"""

    __tablename__ = "contribution_daily_metrics"
    __table_args__ = (
        UniqueConstraint(
            "account_id",
            "date",
            "campaign_id",
            "metric_key",
            name="uq_contribution_daily_metrics_account_date_campaign_metric",
        ),
    )

    id = Column(String, primary_key=True, default=lambda: f"cda_{uuid.uuid4().hex[:12]}")
    account_id = Column(String(120), nullable=False, index=True)
    date = Column(String(10), nullable=False)
    campaign_id = Column(String(120), nullable=False, index=True)
    campaign_name = Column(String, nullable=True)
    spend = Column(Float, nullable=True)
    impressions = Column(Integer, nullable=True)
    conversions = Column(Float, nullable=True)
    conversion_value = Column(Float, nullable=True)
    metric_key = Column(String(50), nullable=False, default="omni_purchase")
    actions_payload = Column(JSON, nullable=True)
    fetched_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))


class ContributionCampaignGroup(Base):
    """活動分組設定：把共線嚴重的單活動聚為組別，MMM 在組別層級估計貢獻。

    source='auto' 由 grouping.py 規則建議產生；使用者於前端調整後覆寫為 'manual'，
    後續分析優先採用 manual 分組（見 docs/21 第 3.3 節）。"""

    __tablename__ = "contribution_campaign_groups"

    id = Column(String, primary_key=True, default=lambda: f"cgr_{uuid.uuid4().hex[:12]}")
    account_id = Column(String(120), nullable=False, index=True)
    group_key = Column(String(50), nullable=False)
    group_name = Column(String(120), nullable=False)
    campaign_ids = Column(JSON, nullable=False, default=list)
    source = Column(String(20), nullable=False, default="auto")
    updated_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))

    updater = relationship("User")


class ContributionSnapshot(Base):
    """單次 MMM 分析的結果快照與狀態。

    status 流轉：queued → processing → completed / failed（同 Andromeda 評分模式，
    前端輪詢 GET /analyses/{id}）。results 永遠以「中位數 + min/max 範圍」呈現，
    不存單點；diagnostics 含共線性警告、R²、Poisson 天花板與資料量檢查。"""

    __tablename__ = "contribution_snapshots"

    id = Column(String, primary_key=True, default=lambda: f"csn_{uuid.uuid4().hex[:12]}")
    account_id = Column(String(120), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="queued", index=True)
    date_start = Column(String(10), nullable=False)
    date_end = Column(String(10), nullable=False)
    config = Column(JSON, nullable=False, default=dict)
    results = Column(JSON, nullable=True)
    diagnostics = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    runtime_job_id = Column(String(120), nullable=True, index=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))
    completed_at = Column(DateTime, nullable=True)

    creator = relationship("User")
