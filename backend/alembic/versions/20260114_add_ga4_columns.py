"""add_ga4_columns

Revision ID: 20260114_add_ga4_columns
Revises: 20260106_add_permissions_tables
Create Date: 2026-01-14

This migration adds the missing GA4 (Google Analytics 4) columns to the users table.
These columns are required for the GA4 integration feature.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260114_add_ga4_columns'
down_revision = '20260106'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add GA4 columns to users table."""
    bind = op.get_bind()
    
    # Check if columns already exist (safe migration)
    from sqlalchemy import inspect
    inspector = inspect(bind)
    existing_columns = [c['name'] for c in inspector.get_columns('users')]
    
    # GA4 columns
    if 'ga4_access_token' not in existing_columns:
        op.add_column('users', sa.Column('ga4_access_token', sa.String(), nullable=True))
    
    if 'ga4_refresh_token' not in existing_columns:
        op.add_column('users', sa.Column('ga4_refresh_token', sa.String(), nullable=True))
    
    if 'ga4_expires_at' not in existing_columns:
        op.add_column('users', sa.Column('ga4_expires_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Remove GA4 columns from users table."""
    op.drop_column('users', 'ga4_expires_at')
    op.drop_column('users', 'ga4_refresh_token')
    op.drop_column('users', 'ga4_access_token')
