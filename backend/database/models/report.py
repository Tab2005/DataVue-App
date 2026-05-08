# backend/database/models/report.py
"""WeeklyReport ORM 模型 — 週報專案儲存"""

import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, text, Boolean

from database.base import Base


class WeeklyReport(Base):
    """
    週報專案。
    記錄使用者設定的條件與產生後的報表資料（JSON快照）。
    """
    __tablename__ = "weekly_reports"

    id           = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name         = Column(String, nullable=False)           # 報表名稱，e.g. "2026 W09 電商廣告週報"
    description  = Column(Text, nullable=True)              # 自訂備註
    module_type  = Column(String, default="fb_ads")         # 報表類型: fb_ads | ga4

    # --- 查詢條件（條件快照） ---
    ad_account_id   = Column(String, nullable=False)        # 廣告帳號 ID
    ad_account_name = Column(String, nullable=True)         # 帳號名稱（快照用）
    date_since      = Column(String, nullable=False)        # YYYY-MM-DD
    date_until      = Column(String, nullable=False)        # YYYY-MM-DD
    date_label      = Column(String, nullable=True)         # e.g. "2026 W09 (2/23~3/1)"
    breakdown       = Column(String, nullable=True)         # 分組依據：campaign / adset / ad / none
    selected_metrics = Column(Text, nullable=False)         # JSON array: ["spend","roas",...]

    # --- 報表資料（產生後快照） ---
    report_data  = Column(Text, nullable=True)              # JSON: { kpis, trend, table_rows, ... }
    ai_summary   = Column(Text, nullable=True)              # AI 摘要文字
    sections     = Column(Text, nullable=True)              # JSON: 自訂章節內容 [{title, content, order}]

    # --- 狀態 ---
    status       = Column(String, default="draft")          # draft | generated | archived
    share_token  = Column(String, unique=True, nullable=True, index=True) # 分享用 Token (UUID)

    # --- 擁有者 ---
    user_id      = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    team_id      = Column(String, ForeignKey("teams.id"),  nullable=True, index=True)
    created_by   = Column(String, ForeignKey("users.id"),  nullable=True)

    created_at   = Column(DateTime, default=text("CURRENT_TIMESTAMP"))
    updated_at   = Column(DateTime, default=text("CURRENT_TIMESTAMP"),
                          onupdate=text("CURRENT_TIMESTAMP"))


class ReportSchedule(Base):
    """
    週報自動化產生的排程設定。
    """
    __tablename__ = "report_schedules"

    id               = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name             = Column(String, nullable=False)        # 排程名稱
    module_type      = Column(String, default="fb_ads")      # 報表類型: fb_ads | ga4
    
    # 報表參數副本
    ad_account_id    = Column(String, nullable=False)
    ad_account_name  = Column(String, nullable=True)
    selected_metrics = Column(Text, nullable=False)         # JSON array
    breakdown        = Column(String, nullable=True)         # campaign / adset / ad / none
    
    # 排程頻率
    frequency        = Column(String, nullable=False)        # daily | weekly | monthly
    day_of_week      = Column(String, nullable=True)         # "0"-"6" (Monday-Sunday)
    day_of_month     = Column(String, nullable=True)         # "1"-"31"
    time_of_day      = Column(String, default="08:00")       # HH:MM (UTC+8)
    
    is_active        = Column(Boolean, default=True)
    is_notify_line   = Column(Boolean, default=False)
    
    # 擁有者
    user_id          = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    team_id          = Column(String, ForeignKey("teams.id"), nullable=True, index=True)
    
    # 執行記錄
    last_run         = Column(DateTime, nullable=True)
    next_run         = Column(DateTime, nullable=True)
    
    created_at       = Column(DateTime, default=text("CURRENT_TIMESTAMP"))
    updated_at       = Column(DateTime, default=text("CURRENT_TIMESTAMP"),
                              onupdate=text("CURRENT_TIMESTAMP"))

