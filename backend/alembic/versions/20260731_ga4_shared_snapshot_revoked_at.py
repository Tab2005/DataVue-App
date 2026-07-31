"""ga4 shared snapshots revoked_at column (docs/63)

Revision ID: 20260731_ga4_shared_snapshot_revoked_at
Revises: 20260731_ga4_shared_snapshots
Create Date: 2026-07-31 00:00:00.000000

分享連結原本一旦產生就永久有效，誤發給錯的人之後沒有任何補救手段
（docs/59 P1-3）。加上 `revoked_at` 支援撤銷：非 null 代表已收回，公開端點
一律當作不存在。

用軟刪除而非 DELETE——這是安全治理功能，「什麼內容曾經被公開出去、何時收
回」本身就是要留下來的紀錄。純新增 nullable 欄位，既有資料不受影響。
"""

from alembic import op
import sqlalchemy as sa


revision = "20260731_ga4_shared_snapshot_revoked_at"
down_revision = "20260731_ga4_shared_snapshots"
branch_labels = None
depends_on = None


TABLE = "ga4_shared_snapshots"
COLUMN = "revoked_at"


def _table_exists(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _existing_columns(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {col["name"] for col in inspector.get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not _table_exists(inspector, TABLE):
        return
    if COLUMN not in _existing_columns(inspector, TABLE):
        op.add_column(TABLE, sa.Column(COLUMN, sa.DateTime(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not _table_exists(inspector, TABLE):
        return
    if COLUMN in _existing_columns(inspector, TABLE):
        op.drop_column(TABLE, COLUMN)
