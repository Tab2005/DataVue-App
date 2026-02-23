"""merge ga4 and integrations heads

Revision ID: 0303de3f01eb
Revises: 20260114_add_ga4_columns, 20260223_p3_integrations_indexes
Create Date: 2026-02-23 15:52:58.067356

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0303de3f01eb'
down_revision = ('20260114_add_ga4_columns', '20260223_p3_integrations_indexes')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
