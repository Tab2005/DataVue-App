"""initial_schema

Revision ID: 0001
Revises: 
Create Date: 2024-12-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Users Table ---
    # Enum workaround for PostgreSQL (check if type exists)
    bind = op.get_bind()
    if bind.engine.name == 'postgresql':
        op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole') THEN CREATE TYPE userrole AS ENUM ('ADMIN', 'MEMBER', 'VIEWER'); END IF; END $$;")
        op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userstatus') THEN CREATE TYPE userstatus AS ENUM ('ACTIVE', 'SUSPENDED'); END IF; END $$;")

    op.create_table('users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('google_id', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('is_super_admin', sa.Boolean(), nullable=True, default=False),
        sa.Column('fb_access_token', sa.String(), nullable=True),
        sa.Column('fb_app_id', sa.String(), nullable=True),
        sa.Column('fb_app_secret', sa.String(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('role', sa.Enum('ADMIN', 'MEMBER', 'VIEWER', name='userrole'), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'SUSPENDED', name='userstatus'), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_google_id'), 'users', ['google_id'], unique=True)

    # --- Teams Table ---
    op.create_table('teams',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('owner_id', sa.String(), nullable=True),
        sa.Column('fb_access_token', sa.String(), nullable=True),
        sa.Column('fb_app_id', sa.String(), nullable=True),
        sa.Column('visible_ad_account_ids', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # --- Team Members Table ---
    op.create_table('team_members',
        sa.Column('team_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('role', sa.Enum('ADMIN', 'MEMBER', 'VIEWER', name='userrole'), nullable=True),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('team_id', 'user_id')
    )

    # --- Team Invites Table ---
    op.create_table('team_invites',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('team_id', sa.String(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('used_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_team_invites_code'), 'team_invites', ['code'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_team_invites_code'), table_name='team_invites')
    op.drop_table('team_invites')
    op.drop_table('team_members')
    op.drop_table('teams')
    op.drop_index(op.f('ix_users_google_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
