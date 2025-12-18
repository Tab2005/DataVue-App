"""add_team_token_expires_at

Revision ID: fe8441e71f69
Revises: 230a10d75894
Create Date: 2025-12-18 13:34:28.881840

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fe8441e71f69'
down_revision = '230a10d75894'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('teams', sa.Column('token_expires_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('teams', 'token_expires_at')
