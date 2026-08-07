"""meta_andromeda_score_events indexes for status/created_at/roas_band

Revision ID: 20260807_ma_score_events_indexes
Revises: 20260731_ga4_shared_snapshot_revoked_at
Create Date: 2026-08-07

審核佇列列表查詢（repository.list_review_queue）用 status/roas_band 篩選、
created_at 排序，但這三個欄位過去都沒有索引，meta_andromeda_score_events
表隨評分/觀測匯入持續增長後，每次查詢都得全表掃描——這是「評估紀錄頁面
偶發請求逾時（>30000ms）」的成因之一（另一半是原本在 Python 端而非 SQL
層做分頁的問題，已在 repository.list_review_queue 內另外修復）。

用 inspector 檢查索引是否已存在再建立，讓這支 migration 在任何環境重跑
都安全；不用 try/except 包 create_index——PostgreSQL 上一條語句失敗會讓
整個交易變成 aborted，後續語句（包含其他索引與 alembic_version 更新）會
連帶失敗（見 20260223_p3_integrations_indexes.py 的教訓）。
"""

from alembic import op
import sqlalchemy as sa


revision = "20260807_ma_score_events_indexes"
down_revision = "20260731_ga4_shared_snapshot_revoked_at"
branch_labels = None
depends_on = None


TABLE = "meta_andromeda_score_events"
INDEXES = [
    ("ix_meta_andromeda_score_events_status", ["status"]),
    ("ix_meta_andromeda_score_events_created_at", ["created_at"]),
    ("ix_meta_andromeda_score_events_roas_band", ["roas_band"]),
]


def _existing_index_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {idx["name"] for idx in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if TABLE not in inspector.get_table_names():
        return
    existing = _existing_index_names(inspector, TABLE)
    for index_name, columns in INDEXES:
        if index_name not in existing:
            op.create_index(index_name, TABLE, columns, unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if TABLE not in inspector.get_table_names():
        return
    existing = _existing_index_names(inspector, TABLE)
    for index_name, _columns in INDEXES:
        if index_name in existing:
            op.drop_index(index_name, table_name=TABLE)
