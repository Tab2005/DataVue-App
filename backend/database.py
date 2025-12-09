from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Default to SQLite for local development
SQLITE_DATABASE_URL = "sqlite:///./facebook_dashboard.db"

# Check if DATABASE_URL env var is set (e.g., by Zeabur/Render)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # PostgreSQL Configuration
    # Fix for SQLAlchemy requiring 'postgresql://' instead of 'postgres://' (common in some providers)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    engine = create_engine(DATABASE_URL)
    print(f"✅ Database connected: PostgreSQL detected.")
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

def init_db():
    Base.metadata.create_all(bind=engine)
