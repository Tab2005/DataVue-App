"""merge all migration heads

Revision ID: 20260331_merge_all_heads
Revises: 20260331_add_weekly_reports, fe8441e71f69
Create Date: 2026-03-31 17:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260331_merge_all_heads'
down_revision = ('20260331_add_weekly_reports', 'fe8441e71f69')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
