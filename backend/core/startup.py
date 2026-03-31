"""
Core Startup Module
應用程式啟動邏輯 - 環境驗證、資料庫初始化、Schema 修補、權限種子等

此模組整合了所有啟動時需要執行的邏輯，讓 main.py 保持簡潔。

使用方式:
    from core.startup import run_startup_tasks
    
    # 在應用程式啟動時呼叫
    run_startup_tasks()
"""

import os
import sys
import logging

# Configure Logger
logger = logging.getLogger(__name__)


# ============================================================
# Environment Validation
# ============================================================

REQUIRED_ENV_VARS = [
    "GOOGLE_CLIENT_ID",
    "ENCRYPTION_KEY",
]

OPTIONAL_ENV_VARS = [
    "DATABASE_URL",
]


def validate_environment():
    """Validate that all required environment variables are set."""
    missing = []
    for var in REQUIRED_ENV_VARS:
        value = os.getenv(var)
        if not value or value.strip() == "":
            missing.append(var)
    
    if missing:
        logger.error("-" * 60)
        logger.error("CRITICAL: Missing required environment variables:")
        for var in missing:
            logger.error(f"   - {var}")
        logger.error("-" * 60)
        logger.error("Please set these in your .env file or environment.")
        # Don't exit to allow graceful degradation
    
    # Warn about optional
    for var in OPTIONAL_ENV_VARS:
        if not os.getenv(var):
            logger.warning(f"Optional env var '{var}' not set (using defaults)")


def validate_encryption_key():
    """Validate the encryption key is properly configured."""
    from core.security import get_encryption_key, validate_encryption_key as check_key
    
    if check_key():
        key = get_encryption_key()
        logger.info(f"Encryption key validated (length={len(key)})")
        return True
    else:
        logger.error("ENCRYPTION KEY VALIDATION FAILED")
        return False


# ============================================================
# Database Initialization
# ============================================================

def run_migrations():
    """
    Run Alembic database migrations.
    Robust version for automated PaaS deployments (Zeabur).
    """
    try:
        import alembic
        import alembic.config
        import alembic.command
        import os

        # Get absolute path to alembic.ini relative to this file
        # This file is in backend/core/startup.py, alembic.ini is in backend/alembic.ini
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ini_path = os.path.join(base_dir, "alembic.ini")

        if not os.path.exists(ini_path):
            logger.warning(f"alembic.ini not found at {ini_path}. Skipping migrations.")
            return False

        logger.info(f"Running Database Migrations using config at {ini_path}...")
        
        # Create config and ensure script_location is absolute
        alembic_cfg = alembic.config.Config(ini_path)
        
        # Explicitly set script_location to avoid relative path issues on Zeabur
        alembic_dir = os.path.join(base_dir, "alembic")
        alembic_cfg.set_main_option("script_location", alembic_dir)
        
        # Override sqlalchemy.url from environment if available
        # This is already handled in env.py, but we can also set it here
        from database import DATABASE_URL
        if DATABASE_URL:
            # Ensure postgresql:// protocol for SQLAlchemy 2.0+
            url = DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            alembic_cfg.set_main_option("sqlalchemy.url", url)

        # Run the upgrade
        alembic.command.upgrade(alembic_cfg, "head")
        logger.info("✅ Database Migrations completed successfully")
        return True
    except Exception as e:
        logger.error("-" * 60)
        logger.error(f"❌ Alembic Migration CRITICAL ERROR: {e}")
        import traceback
        logger.error(traceback.format_exc())
        logger.error("-" * 60)
        # We don't exit(1) here to allow the app to try to start in degraded mode
        return False


def patch_database_schema(engine):
    """Auto-patch database schema for missing columns."""
    from sqlalchemy import text, inspect
    
    try:
        inspector = inspect(engine)
        
        # Patch Teams table
        if inspector.has_table("teams"):
            columns = [c["name"] for c in inspector.get_columns("teams")]
            
            team_patches = [
                ("visible_ad_account_ids", "TEXT"),
                ("fb_app_id", "VARCHAR"),
                ("fb_access_token", "VARCHAR"),
                ("token_expires_at", "TIMESTAMP"),
            ]
            
            for col_name, col_type in team_patches:
                if col_name not in columns:
                    logger.info(f"Patching teams.{col_name}...")
                    with engine.connect() as conn:
                        conn.execute(text(f"ALTER TABLE teams ADD COLUMN {col_name} {col_type}"))
                        conn.commit()
        
        # Patch Users table
        if inspector.has_table("users"):
            columns = [c["name"] for c in inspector.get_columns("users")]
            
            user_patches = [
                ("gsc_access_token", "TEXT"),
                ("gsc_refresh_token", "TEXT"),
                ("gsc_expires_at", "TIMESTAMP"),
                ("zeabur_api_key", "VARCHAR"),
                ("gemini_api_key", "VARCHAR"),
                ("ai_provider", "VARCHAR DEFAULT 'zeabur'"),
                ("ai_model", "VARCHAR DEFAULT 'gemini-2.5-flash'"),
                # GA4 Integration
                ("ga4_access_token", "TEXT"),
                ("ga4_refresh_token", "TEXT"),
                ("ga4_expires_at", "TIMESTAMP"),
            ]
            
            for col_name, col_type in user_patches:
                if col_name not in columns:
                    logger.info(f"Patching users.{col_name}...")
                    try:
                        with engine.connect() as conn:
                            conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                            conn.commit()
                    except Exception as e:
                        logger.warning(f"Failed to add {col_name}: {e}")
        
        # Create page_titles table if missing
        if not inspector.has_table("page_titles"):
            logger.info("Creating page_titles table...")
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE page_titles (
                        id VARCHAR PRIMARY KEY,
                        url VARCHAR UNIQUE NOT NULL,
                        title VARCHAR,
                        fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.commit()
            logger.info("Table 'page_titles' created")
        
        # Create saved_views table if missing
        if not inspector.has_table("saved_views"):
            logger.info("Creating saved_views table...")
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE saved_views (
                        id VARCHAR PRIMARY KEY,
                        user_id VARCHAR NOT NULL,
                        name VARCHAR NOT NULL,
                        type VARCHAR NOT NULL,
                        config TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.commit()
            logger.info("Table 'saved_views' created")
        
        logger.info("Schema patching completed")
        return True
    except Exception as e:
        logger.warning(f"Schema Patching Warning: {e}")
        return False


def seed_permissions():
    """Seed default permissions into the database."""
    try:
        logger.info("Running Permission Seeding...")
        from scripts.seed_permissions import seed_permissions as do_seed
        do_seed()
        logger.info("Permissions seeded")
        return True
    except Exception as e:
        logger.warning(f"Permission Seeding Warning: {e}")
        return False


def sync_super_admin():
    """Sync Super Admin status based on SUPER_ADMIN_EMAIL environment variable."""
    super_admin_email = os.getenv("SUPER_ADMIN_EMAIL", "").strip()
    if not super_admin_email:
        return True
    
    try:
        from database import SessionLocal, User, UserRole
        
        emails = [e.strip().lower() for e in super_admin_email.split(",") if e.strip()]
        if not emails:
            return True
        
        session = SessionLocal()
        try:
            synced_count = 0
            for email in emails:
                user = session.query(User).filter(User.email == email).first()
                if user:
                    if not user.is_super_admin:
                        user.is_super_admin = True
                        user.role = UserRole.ADMIN
                        synced_count += 1
                        logger.info(f"Synced Super Admin: {email}")
            
            if synced_count > 0:
                session.commit()
            
            return True
        finally:
            session.close()
    except Exception as e:
        logger.warning(f"Super Admin Sync Warning: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


# ============================================================
# Main Startup Function
# ============================================================

def run_startup_tasks():
    """
    Run all startup tasks in the correct order.
    
    Returns:
        bool: True if all critical tasks succeeded
    """
    logger.info("=" * 50)
    logger.info("🚀 Running Startup Tasks...")
    logger.info("=" * 50)
    
    # 1. Validate environment
    validate_environment()
    
    # 2. Validate encryption key
    if not validate_encryption_key():
        logger.critical("Encryption key validation failed. Service cannot start.")
        sys.exit(1)
    
    # 3. Import database and check connection
    try:
        from database import engine, init_db, check_db_connection
        logger.info("Database module imported")
        
        if not check_db_connection():
            DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
            if not DEBUG_MODE:
                logger.critical("Database connection failed in production. Aborting startup.")
                sys.exit(1)
            else:
                logger.warning("Database connection failed. Continuing in local/degraded mode.")
        else:
            logger.info("Database connection verified")
    except Exception as e:
        logger.critical(f"Database initialization failed: {e}")
        return False
    
    # 4. Run migrations
    run_migrations()
    
    # 5. Patch schema (Legacy fallback, should move to Alembic)
    patch_database_schema(engine)
    
    # 6. Initialize database (dev-mode create_all)
    init_db()
    
    # 7. Seed permissions
    seed_permissions()
    
    # 8. Sync super admin
    sync_super_admin()
    
    logger.info("=" * 50)
    logger.info("✅ Startup Tasks Completed")
    logger.info("=" * 50)
    
    return True
