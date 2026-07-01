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
    # 2026-07-01 修復：原本這裡有一段 PostgreSQL 專用的
    # `DO $$ BEGIN IF NOT EXISTS (...) THEN CREATE TYPE userrole ... END $$;`
    # 手動防呆區塊，意圖是「型別不存在才建立」。但緊接著的
    # op.create_table() 中 sa.Enum(name='userrole') 欄位會觸發 SQLAlchemy
    # 自動建立同名 ENUM type，而 Alembic 呼叫時 checkfirst=False（無條件
    # 建立，不檢查是否已存在），導致同一交易內型別被建立兩次，
    # 在全新 PostgreSQL 資料庫上直接拋錯：
    # (psycopg2.errors.DuplicateObject) type "userrole" already exists。
    # 已移除手動 DO 區塊，改為單純依賴 op.create_table() 內建的自動建立：
    # SQLAlchemy 對同一個 (schema, name) 的具名 type 在同一次 migration
    # 執行過程中會透過內部 memo 去重，所以下面 team_members 表重複引用
    # 同一個 userrole type 不會導致重複建立。已用全新 PostgreSQL 18
    # 資料庫實測重現原錯誤並驗證此修復可解決。
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
