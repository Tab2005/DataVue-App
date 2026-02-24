# backend/database/base.py
"""宣告 SQLAlchemy DeclarativeBase，供所有 ORM 模型繼承"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()
