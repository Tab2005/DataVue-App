from sqlalchemy import create_engine, Column, String, DateTime, text, Enum as SAEnum, Boolean, ForeignKey, Integer
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, backref
from sqlalchemy.exc import OperationalError, ProgrammingError
import os
import uuid
import enum

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _to_sqlite_url(abs_path: str) -> str:
    # SQLAlchemy/SQLite URL prefers forward slashes, including on Windows.
    return "sqlite:///" + abs_path.replace("\\", "/")


def _normalize_sqlite_url(url: str) -> str:
    """Normalize sqlite URL to always resolve relative paths from backend dir."""
    if not url or not url.startswith("sqlite:///"):
        return url

    # Already absolute
    if ":/" in url[10:] or url.startswith("sqlite:////"):
        return url

    # Extract relative path
    rel = url[len("sqlite:///"):].lstrip("./")
    
    # Tolerate legacy backend/ prefix
    rel_norm = rel.replace("\\", "/")
    if rel_norm.startswith("backend/"):
        rel_norm = rel_norm[len("backend/"):]
        
    abs_path = os.path.join(BASE_DIR, rel_norm)
    return _to_sqlite_url(os.path.abspath(abs_path))

# Default to SQLite for local development
SQLITE_DATABASE_URL = _normalize_sqlite_url("sqlite:///./facebook_dashboard.db")

# Check if DATABASE_URL env var is set (e.g., by Zeabur/Render)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    # PostgreSQL Configuration
    # Use psycopg2 (Standard Driver)
    print(f"DEBUG: Found PostgreSQL DATABASE_URL, configuring PostgreSQL...", flush=True)
    try:
        engine = create_engine(DATABASE_URL)
        # Test connection immediately
        with engine.connect() as connection:
            print(f"✅ Database connected successfully: PostgreSQL.", flush=True)
    except Exception as e:
        print(f"❌ DATABASE CONNECTION FAILED: {e}", flush=True)
        # Fallback to SQLite
        print(f"DEBUG: Falling back to SQLite...", flush=True)
        DATABASE_URL = None
        engine = create_engine(
            SQLITE_DATABASE_URL, connect_args={"check_same_thread": False}
        )
        print(f"Database connected: SQLite (Local Mode).")
elif DATABASE_URL and DATABASE_URL.startswith("sqlite://"):
    # SQLite Configuration (Local)
    DATABASE_URL = _normalize_sqlite_url(DATABASE_URL)
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
    print(f"✅ Database connected: SQLite.")
else:
    # Default to SQLite Configuration (Local)
    engine = create_engine(
        SQLITE_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    print(f"✅ Database connected: SQLite.")

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
    
    # Google Search Console (GSC) Integration
    gsc_access_token = Column(String, nullable=True)
    gsc_refresh_token = Column(String, nullable=True)
    gsc_expires_at = Column(DateTime, nullable=True)
    
    # Google Analytics 4 (GA4) Integration
    ga4_access_token = Column(String, nullable=True)
    ga4_refresh_token = Column(String, nullable=True)
    ga4_expires_at = Column(DateTime, nullable=True)
    
    # AI Integration (Encrypted API Keys)
    zeabur_api_key = Column(String, nullable=True)  # Encrypted Zeabur AI Hub API Key
    gemini_api_key = Column(String, nullable=True)  # Encrypted Google Gemini API Key
    ai_provider = Column(String, nullable=True, default="zeabur")  # Active provider: 'zeabur' or 'gemini'
    ai_model = Column(String, nullable=True, default="gemini-2.5-flash")  # Selected AI model
    
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


class PageTitle(Base):
    """
    Cached page titles for GSC pages.
    Stores fetched <title> tags to avoid repeated HTTP requests.
    """
    __tablename__ = "page_titles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    url = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=True)
    fetched_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))


# ============================================
# 權限管理系統 Models (Phase 2)
# ============================================

class Module(Base):
    """系統模組定義（FB Ads, GSC, GA4 等）"""
    __tablename__ = "modules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String(50), unique=True, nullable=False)  # 'fb_ads', 'gsc', 'ga4'
    name = Column(String(100), nullable=False)  # '廣告管理', '搜尋管理'
    description = Column(String, nullable=True)
    icon = Column(String(50), nullable=True)  # Emoji or icon class
    enabled = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))


class Permission(Base):
    """權限定義（模組:功能:動作）"""
    __tablename__ = "permissions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    module_id = Column(String, ForeignKey("modules.id"), nullable=False)
    key = Column(String(100), unique=True, nullable=False)  # 'fb_ads:analytics:view'
    name = Column(String(100), nullable=False)
    description = Column(String, nullable=True)
    category = Column(String(50), nullable=True)  # 'feature', 'admin', 'api'
    created_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))

    module = relationship("Module", backref="permissions")


class Role(Base):
    """角色定義（系統/團隊層級）"""
    __tablename__ = "roles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String(50), unique=True, nullable=False)  # 'team_owner', 'team_admin'
    name = Column(String(100), nullable=False)
    description = Column(String, nullable=True)
    scope = Column(String(20), nullable=False)  # 'system', 'team', 'personal'
    created_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))


class RolePermission(Base):
    """角色-權限關聯"""
    __tablename__ = "role_permissions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    role_id = Column(String, ForeignKey("roles.id"), nullable=False)
    permission_id = Column(String, ForeignKey("permissions.id"), nullable=False)

    role = relationship("Role", backref="role_permissions")
    permission = relationship("Permission")


class UserModuleAccess(Base):
    """使用者-模組存取權"""
    __tablename__ = "user_module_access"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    team_id = Column(String, ForeignKey("teams.id"), nullable=True)  # NULL = 個人工作區
    module_id = Column(String, ForeignKey("modules.id"), nullable=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))

    user = relationship("User", backref="module_access")
    team = relationship("Team")
    module = relationship("Module")


class UserPermission(Base):
    """使用者-權限關聯（細緻化授權/撤銷）"""
    __tablename__ = "user_permissions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    team_id = Column(String, ForeignKey("teams.id"), nullable=True)
    permission_id = Column(String, ForeignKey("permissions.id"), nullable=False)
    granted = Column(Boolean, default=True)  # TRUE=授予, FALSE=撤銷
    granted_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))
    granted_by = Column(String, ForeignKey("users.id"), nullable=True)

    user = relationship("User", foreign_keys=[user_id], backref="custom_permissions")
    permission = relationship("Permission")


from sqlalchemy import inspect

def init_db():
    # Only create tables if using SQLite non-migrations or initial setup
    # In production, Alembic should handle this.
    Base.metadata.create_all(bind=engine)

