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
        import os
        import sys
        
        # Get absolute path to alembic.ini relative to this file
        # This file is in backend/core/startup.py, alembic.ini is in backend/alembic.ini
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Ensure base_dir (backend) is in sys.path so env.py can import database
        if base_dir not in sys.path:
            sys.path.insert(0, base_dir)

        import alembic
        import alembic.config
        import alembic.command

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

    # 2026-07-02（P0-3）：明確印出 ENV / DEBUG_MODE，方便運維從啟動日誌直接
    # 確認目前是否為生產環境、debug 端點是否有被意外掛載，不需另外進 shell 查環境變數。
    from core.config import settings
    debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
    logger.info(f"ENV={settings.ENV} | DEBUG_MODE={debug_mode}")
    if settings.is_production and debug_mode:
        logger.warning(
            "⚠️ DEBUG_MODE=true 但 ENV=production！/api/debug/* 端點將被掛載，請確認這是刻意行為。"
        )

    # 1. Validate environment
    validate_environment()
    
    # 2. Validate encryption key
    if not validate_encryption_key():
        logger.critical("Encryption key validation failed. Service cannot start.")
        sys.exit(1)
    
    # 3. Import database and check connection
    try:
        from database import init_db, check_db_connection
        logger.info("Database module imported")
        
        if not check_db_connection():
            logger.warning("=" * 60)
            logger.warning("⚠️  DATABASE CONNECTION FAILED!")
            logger.warning("The system will attempt to continue in degraded mode (likely using SQLite).")
            logger.warning("Please check your DATABASE_URL environment variable if you expect to use PostgreSQL.")
            logger.warning("=" * 60)
        else:
            logger.info("Database connection verified")
    except Exception as e:
        logger.critical(f"Database initialization failed: {e}")
        return False
    
    # 4. Run migrations unless deployment entrypoint already handled them.
    skip_startup_migrations = os.getenv("DATAVUE_SKIP_STARTUP_MIGRATIONS", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if skip_startup_migrations:
        logger.info("Skipping startup migrations because DATAVUE_SKIP_STARTUP_MIGRATIONS is enabled.")
    else:
        run_migrations()
    
    # 5. Initialize database (dev-mode create_all; production 只信任 Alembic，
    #    見 database/__init__.py::init_db() 的 dialect 分流邏輯)
    init_db()

    # 6. Seed Meta Andromeda default models and records
    try:
        from modules.meta_andromeda.repository import repository
        from database import SessionLocal
        db = SessionLocal()
        try:
            repository.ensure_seed_data(db)
            logger.info("✅ Meta Andromeda seed data verified/initialized.")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to seed Meta Andromeda data on startup: {e}")

    # 7. Seed permissions
    seed_permissions()

    # 8. Sync super admin
    sync_super_admin()
    
    logger.info("=" * 50)
    logger.info("✅ Startup Tasks Completed")
    logger.info("=" * 50)
    
    return True
