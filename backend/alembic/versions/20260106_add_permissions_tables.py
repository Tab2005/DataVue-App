"""add_permissions_tables

Revision ID: 20260106
Revises: fe8441e71f69
Create Date: 2026-01-06 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260106'
down_revision = 'fe8441e71f69'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create modules table
    op.create_table(
        'modules',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('key', sa.String(50), nullable=False, unique=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )

    # Create permissions table
    op.create_table(
        'permissions',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('module_id', sa.String(), sa.ForeignKey('modules.id'), nullable=False),
        sa.Column('key', sa.String(100), nullable=False, unique=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )

    # Create roles table
    op.create_table(
        'roles',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('key', sa.String(50), nullable=False, unique=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('scope', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )

    # Create role_permissions table
    op.create_table(
        'role_permissions',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('role_id', sa.String(), sa.ForeignKey('roles.id'), nullable=False),
        sa.Column('permission_id', sa.String(), sa.ForeignKey('permissions.id'), nullable=False)
    )

    # Create user_module_access table
    op.create_table(
        'user_module_access',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('team_id', sa.String(), sa.ForeignKey('teams.id'), nullable=True),
        sa.Column('module_id', sa.String(), sa.ForeignKey('modules.id'), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )

    # Create user_permissions table
    op.create_table(
        'user_permissions',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('team_id', sa.String(), sa.ForeignKey('teams.id'), nullable=True),
        sa.Column('permission_id', sa.String(), sa.ForeignKey('permissions.id'), nullable=False),
        sa.Column('granted', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('granted_at', sa.DateTime(), nullable=True),
        sa.Column('granted_by', sa.String(), sa.ForeignKey('users.id'), nullable=True)
    )


def downgrade() -> None:
    op.drop_table('user_permissions')
    op.drop_table('user_module_access')
    op.drop_table('role_permissions')
    op.drop_table('roles')
    op.drop_table('permissions')
    op.drop_table('modules')
