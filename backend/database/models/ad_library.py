"""Ad Library module ORM models (docs/73)."""

import uuid

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
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
    media_stored = Column(Integer, nullable=False, default=0)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
