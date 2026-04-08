"""add weekly_reports table

Revision ID: 20260331_add_weekly_reports
Revises: 20260224_fix_integrations_migration_compat
Create Date: 2026-03-31 16:40:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260331_add_weekly_reports'
down_revision = '20260224_fix_integrations_migration_compat'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'weekly_reports',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('ad_account_id', sa.String(), nullable=False),
        sa.Column('ad_account_name', sa.String(), nullable=True),
        sa.Column('date_since', sa.String(), nullable=False),
        sa.Column('date_until', sa.String(), nullable=False),
        sa.Column('date_label', sa.String(), nullable=True),
        sa.Column('breakdown', sa.String(), nullable=True),
        sa.Column('selected_metrics', sa.Text(), nullable=False),
        sa.Column('report_data', sa.Text(), nullable=True),
        sa.Column('ai_summary', sa.Text(), nullable=True),
        sa.Column('sections', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=True, server_default='draft'),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('team_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )
    op.create_index(op.f('ix_weekly_reports_team_id'), 'weekly_reports', ['team_id'], unique=False)
    op.create_index(op.f('ix_weekly_reports_user_id'), 'weekly_reports', ['user_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_weekly_reports_user_id'), table_name='weekly_reports')
    op.drop_index(op.f('ix_weekly_reports_team_id'), table_name='weekly_reports')
    op.drop_table('weekly_reports')
