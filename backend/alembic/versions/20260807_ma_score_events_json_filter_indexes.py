"""expression indexes for meta_andromeda_score_events JSON filter columns

Revision ID: 20260807_ma_score_events_json_filter_indexes
Revises: 20260807_ma_score_events_indexes
Create Date: 2026-08-07

審核佇列列表（repository.list_review_queue）用「來源」篩選
（source=analytics/score_lab）比對 request_context.observed_creative_id、
用「引擎」篩選（scoring_engine=ai/heuristic）比對
lineage.scoring_mode、backtest 排除比對 lineage.scoring_purpose——這三個
都是 JSON 欄位路徑，前一支 migration 補的 status/created_at/roas_band
索引完全幫不上忙：只要查詢條件混進其中任何一個，PostgreSQL 還是得整表
掃描評估，這正是「不篩選時正常、一篩選來源就逾時（>30000ms）」的根因。

PostgreSQL 的 json 型別（本專案 JSON 欄位在 PostgreSQL 上的預設對應型別）
沒有註冊 btree operator class，無法直接對 `column -> 'key'`（回傳
json/jsonb）建 index；但 `column ->> 'key'`（回傳 text）可以正常建立
btree expression index。repository.list_review_queue 已同步改用
.as_string()（對應 ->>）取代裸的 ["key"]（對應 ->），這裡建立對應的
expression index。

只在 PostgreSQL 執行：SQLite 的 json_extract 語法與運算子類別限制不同，
且本機開發規模的 SQLite DB 用不到這個優化。
"""

from alembic import op
import sqlalchemy as sa


revision = "20260807_ma_score_events_json_filter_indexes"
down_revision = "20260807_ma_score_events_indexes"
branch_labels = None
depends_on = None


TABLE = "meta_andromeda_score_events"
INDEXES = [
    (
        "ix_ma_score_events_request_context_observed_creative_id",
        "(request_context ->> 'observed_creative_id')",
    ),
    (
        "ix_ma_score_events_lineage_scoring_mode",
        "(lineage ->> 'scoring_mode')",
    ),
    (
        "ix_ma_score_events_lineage_scoring_purpose",
        "(lineage ->> 'scoring_purpose')",
    ),
]


def _existing_index_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {idx["name"] for idx in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    inspector = sa.inspect(bind)
    if TABLE not in inspector.get_table_names():
        return
    existing = _existing_index_names(inspector, TABLE)
    for index_name, expression in INDEXES:
        if index_name not in existing:
            op.execute(f'CREATE INDEX "{index_name}" ON {TABLE} ({expression})')


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    inspector = sa.inspect(bind)
    if TABLE not in inspector.get_table_names():
        return
    existing = _existing_index_names(inspector, TABLE)
    for index_name, _expression in INDEXES:
        if index_name in existing:
            op.execute(f'DROP INDEX "{index_name}"')
