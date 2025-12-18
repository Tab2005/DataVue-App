from sqlalchemy import create_engine, Column, String, DateTime, text, Enum as SAEnum, Boolean, ForeignKey, Integer
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, backref
from sqlalchemy.exc import OperationalError, ProgrammingError
import os
import uuid
import enum

# Default to SQLite for local development
SQLITE_DATABASE_URL = "sqlite:///./facebook_dashboard.db"

# Check if DATABASE_URL env var is set (e.g., by Zeabur/Render)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # PostgreSQL Configuration
    # Use psycopg2 (Standard Driver)
    print(f"DEBUG: Found DATABASE_URL, configuring PostgreSQL...", flush=True)
    try:
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        
        engine = create_engine(DATABASE_URL)
        # Test connection immediately
        with engine.connect() as connection:
            print(f"✅ Database connected successfully: PostgreSQL.", flush=True)
    except Exception as e:
        print(f"❌ DATABASE CONNECTION FAILED: {e}", flush=True)
        # Fallback to avoid crash on import, but requests will fail later
        engine = None
else:
    # SQLite Configuration (Local)
    engine = create_engine(
        SQLITE_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    print(f"Database connected: SQLite (Local Mode).")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

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
    google_id = Column(String, unique=True, index=True, nullable=True) # Unique for lookup
    email = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, nullable=True)
    
    # Super Admin Flag (Platform Owner)
    is_super_admin = Column(Boolean, default=False)

    # Facebook Tokens (Encrypted) - NOTE: In SaaS mode, tokens might move to Team level
    # But for backward compatibility or Personal scoped connection, we keep them here for now
    fb_access_token = Column(String, nullable=True)
    fb_app_id = Column(String, nullable=True)
    fb_app_secret = Column(String, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    
    # Role Based Access Control (Legacy / Default Team Role)
    role = Column(SAEnum(UserRole), default=UserRole.VIEWER)
    status = Column(SAEnum(UserStatus), default=UserStatus.ACTIVE)
    
    # Metadata
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))

class Team(Base):
    __tablename__ = "teams"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    owner_id = Column(String, nullable=True) # User ID of the team creator
    
    # Team Level Facebook Config (The core of isolation)
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
    
    # Who created it (Usually an Admin of the team)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    
    # Stats
    used_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))

class SavedView(Base):
    """
    Saved metric views for MetricsManager.
    Can be personal (user_id) or team-shared (team_id).
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

from sqlalchemy import inspect

def init_db():
    # Only create tables if using SQLite non-migrations or initial setup
    # In production, Alembic should handle this.
    Base.metadata.create_all(bind=engine)
