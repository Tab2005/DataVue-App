# backend/database/models/user.py
"""User ORM 模型及相關枚舉"""

import uuid
import enum
from sqlalchemy import Column, String, Boolean, DateTime, Enum as SAEnum, text

from database.base import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


class User(Base):
    __tablename__ = "users"

    # UUID Primary Key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Auth & Identity
    google_id = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, nullable=True)

    # Super Admin Flag (Platform Owner)
    is_super_admin = Column(Boolean, default=False)

    # Facebook Tokens (Encrypted)
    fb_access_token = Column(String, nullable=True)
    fb_app_id = Column(String, nullable=True)
    fb_app_secret = Column(String, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)

    # Google Search Console (GSC) Integration
    gsc_access_token = Column(String, nullable=True)
    gsc_refresh_token = Column(String, nullable=True)
    gsc_expires_at = Column(DateTime, nullable=True)

    # Google Analytics 4 (GA4) Integration
    ga4_access_token = Column(String, nullable=True)
    ga4_refresh_token = Column(String, nullable=True)
    ga4_expires_at = Column(DateTime, nullable=True)

    # AI Integration (Encrypted API Keys)
    zeabur_api_key = Column(String, nullable=True)
    gemini_api_key = Column(String, nullable=True)
    ai_provider = Column(String, nullable=True, default="zeabur")
    ai_model = Column(String, nullable=True, default="gemini-2.5-flash")
    line_user_id = Column(String, nullable=True, index=True)

    # Role Based Access Control (Legacy / Default Team Role)
    role = Column(SAEnum(UserRole), default=UserRole.VIEWER)
    status = Column(SAEnum(UserStatus), default=UserStatus.ACTIVE)

    # Metadata
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))

    def __repr__(self):
        return f"<User {self.email}>"
