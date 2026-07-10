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
    fetched_by = Column(String, ForeignKey("users.id"), nullable=True)
    fetched_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    fetcher = relationship("User")


class GA4AnomalyRule(Base):
    __tablename__ = "ga4_anomaly_rules"

    id = Column(String, primary_key=True, default=lambda: f"gar_{uuid.uuid4().hex[:12]}")
    property_id = Column(String(50), nullable=False, index=True)
    metric_key = Column(String(50), nullable=False)
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
