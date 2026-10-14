"""Ad Library module ORM models (docs/73, docs/74)."""

import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    Index,
    UniqueConstraint,
    text,
)

from database.base import Base


class AdLibraryItem(Base):
    """自家廣告帳號的單支廣告文案快取（docs/73）。

    以 (account_id, ad_id) 為 upsert key；文案欄位一律存成字串陣列，
    以容納輪播與動態創意（asset_feed_spec）的多組文案。
    """

    __tablename__ = "ad_library_items"
    __table_args__ = (
        UniqueConstraint("account_id", "ad_id", name="uq_ad_library_items_account_ad"),
        Index("ix_ad_library_items_adset_copy", "account_id", "adset_id", "copy_key"),
        Index("ix_ad_library_items_adset_media", "account_id", "adset_id", "media_key"),
    )

    id = Column(String, primary_key=True, default=lambda: f"ali_{uuid.uuid4().hex[:12]}")
    account_id = Column(String(64), nullable=False, index=True)
    ad_id = Column(String(64), nullable=False)
    ad_name = Column(String, nullable=True)
    campaign_id = Column(String(64), nullable=True)
    campaign_name = Column(String, nullable=True)
    adset_id = Column(String(64), nullable=True)
    adset_name = Column(String, nullable=True)
    objective = Column(String(64), nullable=True)
    effective_status = Column(String(32), nullable=True, index=True)
    page_id = Column(String(64), nullable=True)
    media_type = Column(String(20), nullable=False, default="image")
    primary_texts = Column(JSON, nullable=False, default=list)
    headlines = Column(JSON, nullable=False, default=list)
    descriptions = Column(JSON, nullable=False, default=list)
    cta_types = Column(JSON, nullable=False, default=list)
    link_url = Column(Text, nullable=True)
    # [{kind: image|video_thumbnail, fb_url, image_hash, asset_id}]
    media = Column(JSON, nullable=False, default=list)
    preview_link = Column(Text, nullable=True)
    search_text = Column(Text, nullable=True)
    # docs/74 第二節：文案／素材指紋組合，用於比對同組內的文案測試與素材測試
    copy_key = Column(String(64), nullable=True)
    media_key = Column(String(64), nullable=True)
    impressions = Column(BigInteger, nullable=False, default=0)
    reach = Column(BigInteger, nullable=False, default=0)
    clicks = Column(BigInteger, nullable=False, default=0)
    spend = Column(Float, nullable=False, default=0.0)
    ctr = Column(Float, nullable=False, default=0.0)
    ad_created_at = Column(DateTime, nullable=True)
    ad_updated_at = Column(DateTime, nullable=True)
    first_seen_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    last_seen_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    fetched_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class AdLibraryRefreshJob(Base):
    """廣告文案庫刷新任務（docs/73），供前端輪詢進度與防止同帳號重複刷新。"""

    __tablename__ = "ad_library_refresh_jobs"

    id = Column(String, primary_key=True, default=lambda: f"alj_{uuid.uuid4().hex[:12]}")
    account_id = Column(String(64), nullable=False, index=True)
    team_id = Column(String, ForeignKey("teams.id"), nullable=True)
    requested_by = Column(String, ForeignKey("users.id"), nullable=False)
    # queued | running | succeeded | partial | failed
    status = Column(String(20), nullable=False, default="queued", index=True)
    ads_fetched = Column(Integer, nullable=False, default=0)
    campaigns_fetched = Column(Integer, nullable=False, default=0, server_default="0")
    adsets_fetched = Column(Integer, nullable=False, default=0, server_default="0")
    # docs/74 第 3 階段：已抓取元件成效的動態素材廣告數
    asset_insights_ads = Column(Integer, nullable=False, default=0, server_default="0")
    media_stored = Column(Integer, nullable=False, default=0)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)


class AdLibraryCampaign(Base):
    """行銷活動設定快照（docs/74）。預算為帳號幣別最小單位，換算見 currency.py。"""

    __tablename__ = "ad_library_campaigns"
    __table_args__ = (
        UniqueConstraint("account_id", "campaign_id", name="uq_ad_library_campaigns_account_campaign"),
    )

    id = Column(String, primary_key=True, default=lambda: f"alc_{uuid.uuid4().hex[:12]}")
    account_id = Column(String(64), nullable=False, index=True)
    campaign_id = Column(String(64), nullable=False)
    name = Column(String, nullable=True)
    objective = Column(String(64), nullable=True)
    status = Column(String(32), nullable=True)
    effective_status = Column(String(32), nullable=True)
    buying_type = Column(String(32), nullable=True)
    bid_strategy = Column(String(64), nullable=True)
    smart_promotion_type = Column(String(64), nullable=True)
    daily_budget = Column(BigInteger, nullable=True)
    lifetime_budget = Column(BigInteger, nullable=True)
    budget_remaining = Column(BigInteger, nullable=True)
    currency = Column(String(8), nullable=True)
    special_ad_categories = Column(JSON, nullable=False, default=list)
    start_time = Column(DateTime, nullable=True)
    stop_time = Column(DateTime, nullable=True)
    created_time = Column(DateTime, nullable=True)
    updated_time = Column(DateTime, nullable=True)
    impressions = Column(BigInteger, nullable=False, default=0)
    reach = Column(BigInteger, nullable=False, default=0)
    clicks = Column(BigInteger, nullable=False, default=0)
    spend = Column(Float, nullable=False, default=0.0)
    ctr = Column(Float, nullable=False, default=0.0)
    raw = Column(JSON, nullable=True)
    first_seen_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    last_seen_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    fetched_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class AdLibraryAdset(Base):
    """廣告組合設定快照（docs/74），targeting 原樣保存並另存摘要。"""

    __tablename__ = "ad_library_adsets"
    __table_args__ = (
        UniqueConstraint("account_id", "adset_id", name="uq_ad_library_adsets_account_adset"),
        Index("ix_ad_library_adsets_account_campaign", "account_id", "campaign_id"),
    )

    id = Column(String, primary_key=True, default=lambda: f"ala_{uuid.uuid4().hex[:12]}")
    account_id = Column(String(64), nullable=False, index=True)
    adset_id = Column(String(64), nullable=False)
    campaign_id = Column(String(64), nullable=True)
    name = Column(String, nullable=True)
    status = Column(String(32), nullable=True)
    effective_status = Column(String(32), nullable=True)
    optimization_goal = Column(String(64), nullable=True)
    billing_event = Column(String(64), nullable=True)
    bid_strategy = Column(String(64), nullable=True)
    destination_type = Column(String(64), nullable=True)
    is_dynamic_creative = Column(Boolean, nullable=True)
    bid_amount = Column(BigInteger, nullable=True)
    daily_budget = Column(BigInteger, nullable=True)
    lifetime_budget = Column(BigInteger, nullable=True)
    budget_remaining = Column(BigInteger, nullable=True)
    currency = Column(String(8), nullable=True)
    targeting = Column(JSON, nullable=True)
    targeting_summary = Column(JSON, nullable=False, default=dict)
    promoted_object = Column(JSON, nullable=True)
    attribution_spec = Column(JSON, nullable=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    created_time = Column(DateTime, nullable=True)
    updated_time = Column(DateTime, nullable=True)
    impressions = Column(BigInteger, nullable=False, default=0)
    reach = Column(BigInteger, nullable=False, default=0)
    clicks = Column(BigInteger, nullable=False, default=0)
    spend = Column(Float, nullable=False, default=0.0)
    ctr = Column(Float, nullable=False, default=0.0)
    raw = Column(JSON, nullable=True)
    first_seen_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    last_seen_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    fetched_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class AdLibraryContent(Base):
    """廣告內容元件（docs/74 第二節）：文字或素材，同帳號內以 (kind, fingerprint) 去重。"""

    __tablename__ = "ad_library_contents"
    __table_args__ = (
        UniqueConstraint("account_id", "kind", "fingerprint", name="uq_ad_library_contents_account_kind_fp"),
    )

    id = Column(String, primary_key=True, default=lambda: f"alt_{uuid.uuid4().hex[:12]}")
    account_id = Column(String(64), nullable=False, index=True)
    # primary_text | headline | description | image | video
    kind = Column(String(20), nullable=False)
    fingerprint = Column(String(80), nullable=False)
    text_value = Column(Text, nullable=True)
    image_hash = Column(String(64), nullable=True)
    video_id = Column(String(64), nullable=True)
    asset_id = Column(String, nullable=True)
    first_seen_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    last_seen_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class AdLibraryAdContent(Base):
    """廣告 ↔ 內容元件的多對多關聯（docs/74）。"""

    __tablename__ = "ad_library_ad_contents"

    item_id = Column(String, ForeignKey("ad_library_items.id", ondelete="CASCADE"), primary_key=True)
    content_id = Column(
        String, ForeignKey("ad_library_contents.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    position = Column(Integer, primary_key=True, default=0)


class AdLibraryAssetInsight(Base):
    """動態素材廣告的單一元件成效（docs/74 第 3 階段）。

    來源為 `/{ad_id}/insights?breakdowns=body_asset|title_asset|...`，成效可直接
    歸給元件（一般廣告只有整則廣告的成效）。每次刷新整則廣告的列重建。
    """

    __tablename__ = "ad_library_asset_insights"
    __table_args__ = (
        UniqueConstraint("account_id", "ad_id", "content_id", name="uq_ad_library_asset_insights_account_ad_content"),
    )

    id = Column(String, primary_key=True, default=lambda: f"alx_{uuid.uuid4().hex[:12]}")
    account_id = Column(String(64), nullable=False, index=True)
    ad_id = Column(String(64), nullable=False)
    content_id = Column(
        String, ForeignKey("ad_library_contents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind = Column(String(20), nullable=False)
    # Meta 的 asset id（breakdown 回傳的 id），僅供追查
    fb_asset_id = Column(String(64), nullable=True)
    impressions = Column(BigInteger, nullable=False, default=0)
    reach = Column(BigInteger, nullable=False, default=0)
    clicks = Column(BigInteger, nullable=False, default=0)
    spend = Column(Float, nullable=False, default=0.0)
    fetched_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
