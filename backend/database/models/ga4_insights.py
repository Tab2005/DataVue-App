"""GA4 insights module ORM models (docs/22 wave 1)."""

import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, text
from sqlalchemy.orm import relationship

from database.base import Base


class GA4InsightsSnapshot(Base):
    __tablename__ = "ga4_insights_snapshots"
    __table_args__ = (
        UniqueConstraint("property_id", "kind", "date", name="uq_ga4_insights_snapshots_property_kind_date"),
    )

    id = Column(String, primary_key=True, default=lambda: f"gis_{uuid.uuid4().hex[:12]}")
    property_id = Column(String(50), nullable=False, index=True)
    # String(80)：第 5 波「landing_page:{key_event}」kind 後綴可能是長事件名，
    # String(30) 裝不下，2026-07-10 migration 放寬（無損 ALTER）。
    kind = Column(String(80), nullable=False)
    date = Column(String(10), nullable=False)
    payload = Column(JSON, nullable=False, default=dict)
    ai_summary = Column(Text, nullable=True)
    ai_summary_generated_at = Column(DateTime, nullable=True)
    # ⚠️ 已停用（docs/61）：分享連結改掛在 `GA4SharedSnapshot` 的不可變副本上。
    # 這個欄位當初（docs/39）把 token 掛在會被 upsert 覆寫的工作快照上，導致
    # 已分享的連結內容靜默變動、AI 解讀消失（docs/59 P0-1）。欄位保留只為了
    # 可回滾與不破壞既有資料，migration 已把值搬進新表；**新程式碼不要再讀寫
    # 它**，要分享請走 `insights/sharing.py::create_share_link`。
    share_token = Column(String(64), nullable=True, unique=True, index=True)
    fetched_by = Column(String, ForeignKey("users.id"), nullable=True)
    fetched_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    fetcher = relationship("User")


class GA4SharedSnapshot(Base):
    """分享連結的**不可變副本**（docs/61；修 docs/59 P0-1）。

    `GA4InsightsSnapshot` 是「工作快照」：key 是 (property_id, kind, date)，
    每次 GET 報表都會 upsert 覆寫 payload、並把 ai_summary 重設為 None。
    docs/39 當初把 `share_token` 直接掛在那張表上，於是分享出去的連結內容會
    跟著使用者重新載入分頁而靜默變動、AI 解讀還會消失——分享出去的「快照」
    其實不是快照，而是一個會跟著動的即時視圖。

    這張表把「分享出去的東西」獨立出來：按下「產生分享連結」的當下，把來源
    快照的 payload / ai_summary **複製**成這裡的一列，token 掛在副本上。副本
    寫入後永不更新，因此連結內容永久凍結在分享當下的樣子。語意與 docs/58
    成效分析頁的 `fb_ads_analytics_ai_snapshots`（每次解讀建新快照、分享即
    凍結）一致，兩個模組不再各說各話。

    `source_snapshot_id` 只用來判斷「來源自上次分享後有沒有變」，以決定重複
    點擊要沿用舊副本還是凍結一份新的；刻意不設外鍵級聯刪除——副本的存在
    意義就是不受來源後續變動影響。
    """

    __tablename__ = "ga4_shared_snapshots"

    id = Column(String, primary_key=True, default=lambda: f"gss_{uuid.uuid4().hex[:12]}")
    source_snapshot_id = Column(String, nullable=True, index=True)
    property_id = Column(String(50), nullable=False, index=True)
    kind = Column(String(80), nullable=False)
    date = Column(String(10), nullable=False)
    payload = Column(JSON, nullable=False, default=dict)
    ai_summary = Column(Text, nullable=True)
    ai_summary_generated_at = Column(DateTime, nullable=True)
    share_token = Column(String(64), nullable=False, unique=True, index=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    creator = relationship("User")


class GA4AnomalyRule(Base):
    __tablename__ = "ga4_anomaly_rules"

    id = Column(String, primary_key=True, default=lambda: f"gar_{uuid.uuid4().hex[:12]}")
    property_id = Column(String(50), nullable=False, index=True)
    metric_key = Column(String(50), nullable=False)
    # docs/52：NULL＝全部關鍵事件（現況、預設值）；只有 metric_key=="conversions"
    # 時才有意義，才能用 keyEvents:{key_event} 動態指標拆分單一事件的異常判斷。
    key_event = Column(String(80), nullable=True)
    sensitivity = Column(String(10), nullable=False, default="medium")
    check_frequency = Column(String(20), nullable=False, default="hourly")
    is_enabled = Column(Boolean, nullable=False, default=True)
    notify_line = Column(Boolean, nullable=False, default=True)
    notify_email = Column(Boolean, nullable=False, default=False)
    cooldown_hours = Column(Integer, nullable=False, default=6)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    creator = relationship("User")


class GA4KpiTarget(Base):
    """KPI 目標（docs/22 第 3 波）：property × 指標 × 月/季目標值。"""

    __tablename__ = "ga4_kpi_targets"
    __table_args__ = (
        UniqueConstraint(
            "property_id", "metric_key", "period_type", "period_key",
            name="uq_ga4_kpi_targets_property_metric_period",
        ),
    )

    id = Column(String, primary_key=True, default=lambda: f"gkt_{uuid.uuid4().hex[:12]}")
    property_id = Column(String(50), nullable=False, index=True)
    metric_key = Column(String(50), nullable=False)
    period_type = Column(String(10), nullable=False)  # "month" | "quarter"
    period_key = Column(String(10), nullable=False)  # "2026-07" | "2026-Q3"
    target_value = Column(Float, nullable=False)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    creator = relationship("User")


class GA4LandingPageRule(Base):
    """到達頁分類規則（docs/22 第 5 波）：依 `landingPage` 路徑比對，priority 小者先比。"""

    __tablename__ = "ga4_landing_page_rules"

    id = Column(String, primary_key=True, default=lambda: f"glr_{uuid.uuid4().hex[:12]}")
    property_id = Column(String(50), nullable=False, index=True)
    category = Column(String(20), nullable=False)  # product | article | functional | other
    match_type = Column(String(10), nullable=False)  # prefix | contains（不開放 regex，避免 ReDoS）
    pattern = Column(String(200), nullable=False)
    priority = Column(Integer, nullable=False, default=0)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    creator = relationship("User")


class GA4ItemCategoryRule(Base):
    """商品分類補充規則（docs/22 第 7 波）：只在 GA4 的 itemCategory 為
    「(not set)」時當補充分類來源，依 `itemName` 比對，priority 小者先比。
    分類為自由文字（不像到達頁固定 4 類枚舉），比照商店既有分類命名。"""

    __tablename__ = "ga4_item_category_rules"

    id = Column(String, primary_key=True, default=lambda: f"gicr_{uuid.uuid4().hex[:12]}")
    property_id = Column(String(50), nullable=False, index=True)
    category = Column(String(50), nullable=False)
    match_type = Column(String(10), nullable=False)  # prefix | contains（不開放 regex，避免 ReDoS）
    pattern = Column(String(200), nullable=False)
    priority = Column(Integer, nullable=False, default=0)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    creator = relationship("User")


class GA4ChannelGroupRule(Base):
    """渠道值自訂分組規則（docs/44）：把到達頁渠道篩選的原始渠道值（例如
    `facebook / post-ads`、`facebook / cpc`）依 pattern 比對歸到同一個
    `group_label`，篩選時把同一分組底下所有規則的比對條件 OR 在一起查詢。
    規則綁定單一 `channel_dimension`（不跨維度共用，見 docs/43 定案），
    priority 小者先比——但這裡 priority 是用來決定「同一原始值符合多條規則
    時算哪一組」，不影響同一分組內多條規則要不要一起生效（OR 篩選時，同分組
    的規則全部都會生效，不是只取第一條）。"""

    __tablename__ = "ga4_channel_group_rules"

    id = Column(String, primary_key=True, default=lambda: f"gcgr_{uuid.uuid4().hex[:12]}")
    property_id = Column(String(50), nullable=False, index=True)
    channel_dimension = Column(String(30), nullable=False)  # default_channel_group | source_medium | source | medium | campaign
    group_label = Column(String(100), nullable=False)
    match_type = Column(String(10), nullable=False)  # exact | prefix | contains（不開放 regex，避免 ReDoS）
    pattern = Column(String(200), nullable=False)
    priority = Column(Integer, nullable=False, default=0)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    creator = relationship("User")


class GA4AnomalyEvent(Base):
    __tablename__ = "ga4_anomaly_events"

    id = Column(String, primary_key=True, default=lambda: f"gae_{uuid.uuid4().hex[:12]}")
    rule_id = Column(String, ForeignKey("ga4_anomaly_rules.id"), nullable=False, index=True)
    severity = Column(String(10), nullable=False)
    direction = Column(String(10), nullable=False)
    observed_value = Column(Float, nullable=False)
    expected_low = Column(Float, nullable=False)
    expected_high = Column(Float, nullable=False)
    message = Column(Text, nullable=False)
    notified_channels = Column(JSON, nullable=False, default=dict)
    acknowledged_by = Column(String, ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    rule = relationship("GA4AnomalyRule")
    acknowledger = relationship("User", foreign_keys=[acknowledged_by])
