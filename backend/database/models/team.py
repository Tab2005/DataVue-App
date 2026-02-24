# backend/database/models/team.py
"""Team、TeamMember、TeamInvite ORM 模型"""

import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Enum as SAEnum, text
from sqlalchemy.orm import relationship, backref

from database.base import Base
from database.models.user import UserRole


class Team(Base):
    __tablename__ = "teams"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    owner_id = Column(String, nullable=True)  # User ID of the team creator

    # Team Level Facebook Config
    fb_access_token = Column(String, nullable=True)
    fb_app_id = Column(String, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)

    # Ad Account Whitelist (JSON list of IDs stored as string)
    # e.g. '["act_123", "act_456"]'
    visible_ad_account_ids = Column(String, nullable=True)

    created_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))

    # Cascade Delete for Invites
    invites = relationship("TeamInvite", cascade="all, delete-orphan")


class TeamMember(Base):
    __tablename__ = "team_members"

    team_id = Column(String, ForeignKey("teams.id"), primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)

    role = Column(SAEnum(UserRole), default=UserRole.VIEWER)
    joined_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))

    # Relationships
    user = relationship("User", backref="team_memberships")
    team = relationship("Team", backref=backref("members", cascade="all, delete-orphan"))


class TeamInvite(Base):
    __tablename__ = "team_invites"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    team_id = Column(String, ForeignKey("teams.id"), nullable=False)

    # The unique code for the invite link
    code = Column(String, unique=True, index=True, nullable=False)

    # Validity
    expires_at = Column(DateTime, nullable=False)

    # Who created it
    created_by = Column(String, ForeignKey("users.id"), nullable=True)

    # Stats
    used_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))
