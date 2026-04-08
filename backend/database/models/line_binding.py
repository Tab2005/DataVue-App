# backend/database/models/line_binding.py
"""LineBinding ORM 模型 — 處理 LINE 帳號綁定驗證碼"""

import uuid
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, ForeignKey, text
from database.base import Base

class LineBinding(Base):
    """
    儲存臨時發行的 6 位數驗證碼，用於將 LINE User ID 連結至 DataVue 帳號。
    """
    __tablename__ = "line_bindings"

    id         = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code       = Column(String, unique=True, index=True, nullable=False) # 6位數代碼
    user_id    = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    # 過期時間 (預設 10 分鐘)
    expires_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow() + timedelta(minutes=10))
    
    created_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
