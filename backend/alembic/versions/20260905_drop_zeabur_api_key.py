"""drop_zeabur_api_key

移除 Zeabur AI Hub 相關欄位：`zeabur_api_key` 已隨 Zeabur AI Hub 客戶端一併下架，
比照 46c781526b51_add_openrouter_api_key 的作法，資料遷移將歷史上
ai_provider='zeabur' 的用戶改為 'openrouter'。

Revision ID: 20260905_drop_zeabur_api_key
Revises: 20260807_ma_score_events_json_filter_indexes
Create Date: 2026-09-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260905_drop_zeabur_api_key'
down_revision = '20260807_ma_score_events_json_filter_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 資料遷移：將歷史資料中 ai_provider 為 zeabur 的用戶改為 openrouter
    op.execute("UPDATE users SET ai_provider = 'openrouter' WHERE ai_provider = 'zeabur'")

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('zeabur_api_key')
        batch_op.alter_column('ai_provider', server_default='openrouter')


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('ai_provider', server_default='zeabur')
        batch_op.add_column(sa.Column('zeabur_api_key', sa.String(), nullable=True))
