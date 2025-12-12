from sqlalchemy import create_engine, Column, String, DateTime, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError, ProgrammingError
import os

# Default to SQLite for local development
SQLITE_DATABASE_URL = "sqlite:///./facebook_dashboard.db"

# Check if DATABASE_URL env var is set (e.g., by Zeabur/Render)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # PostgreSQL Configuration
    # Use pg8000 (Pure Python Driver) to avoid C-extension segfaults in Docker
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+pg8000://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+pg8000://", 1)
    
    engine = create_engine(DATABASE_URL)
    print(f"✅ Database connected: PostgreSQL (via pg8000).")
else:
    # SQLite Configuration (Local)
    engine = create_engine(
        SQLITE_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    print(f"ℹ️ Database connected: SQLite (Local Mode).")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    google_id = Column(String, primary_key=True, index=True)
    email = Column(String, nullable=True)
    fb_access_token = Column(String, nullable=True)
    fb_app_id = Column(String, nullable=True)
    fb_app_secret = Column(String, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)

from sqlalchemy import inspect

def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Auto-Migration: Add 'token_expires_at' if missing
    try:
        inspector = inspect(engine)
        # Check if table exists first (sanity check)
        if inspector.has_table("users"):
            columns = inspector.get_columns("users")
            column_names = [c["name"] for c in columns]
            
            if "token_expires_at" not in column_names:
                print("⚠️ Column 'token_expires_at' missing. Migrating database...")
                try:
                    with engine.connect() as conn:
                        # Use explicit transaction for DDL
                        with conn.begin():
                            # Determine dialect for correct type
                            dialect = engine.dialect.name
                            col_type = "TIMESTAMP" if dialect == "postgresql" else "DATETIME"
                            
                            conn.execute(text(f"ALTER TABLE users ADD COLUMN token_expires_at {col_type}"))
                    print(f"✅ Migration successful: Added 'token_expires_at' column ({col_type}).")
                except Exception as migration_err:
                    print(f"❌ Migration Failed: {migration_err}")
    except Exception as e:
        print(f"❌ Database Check Failed: {e}")
