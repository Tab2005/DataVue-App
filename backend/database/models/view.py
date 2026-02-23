# backend/database/models/view.py
"""SavedView、PageTitle ORM 模型"""

import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, text

from database.base import Base


class SavedView(Base):
    """
    已儲存的指標檢視（MetricsManager 使用）。
    可為個人（user_id）或團隊共享（team_id）。
    """
    __tablename__ = "saved_views"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    metrics = Column(String, nullable=False)  # JSON array as string: '["spend","roas",...]'

    # Ownership: EITHER user_id OR team_id (mutually exclusive)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    team_id = Column(String, ForeignKey("teams.id"), nullable=True, index=True)

    # Who created it (for team views, track the creator)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))


class PageTitle(Base):
    """
    GSC 頁面標題快取。
    儲存已抓取的 <title> 標籤，避免重複 HTTP 請求。
    """
    __tablename__ = "page_titles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    url = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=True)
    fetched_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))
