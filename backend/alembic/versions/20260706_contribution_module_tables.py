"""contribution module tables (docs/21 task 1.1)

Three tables for the MMM campaign-contribution module:
  - contribution_daily_metrics  : campaign-level daily FB Insights cache (upsert by
                                   account/date/campaign/metric_key)
  - contribution_campaign_groups: campaign grouping (auto rule-suggested / manual)
  - contribution_snapshots       : analysis run result + status (queued/processing/
                                   completed/failed), polled by the frontend

Revision ID: 20260706_contribution_module_tables
Revises: 20260703_ma_seed_profile_hotfix
Create Date: 2026-07-06 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260706_contribution_module_tables"
down_revision = "20260703_ma_seed_profile_hotfix"
branch_labels = None
depends_on = None


DAILY_METRICS_TABLE = "contribution_daily_metrics"
CAMPAIGN_GROUPS_TABLE = "contribution_campaign_groups"
SNAPSHOTS_TABLE = "contribution_snapshots"

# 顯式索引定義（與既有 meta_andromeda migration 慣例一致：列舉名稱 + 欄位，升降級對稱）。
# daily_metrics 的複合唯一約束在 SQLite 上不會自動建可查詢索引，故補一支複合索引供
# 增量補抓「已有資料的日期區間」查詢使用；PostgreSQL 的 UniqueConstraint 本身即為索引。
INDEX_DEFINITIONS = {
    DAILY_METRICS_TABLE: (
        ("ix_contribution_daily_metrics_account_id", ["account_id"]),
        ("ix_contribution_daily_metrics_campaign_id", ["campaign_id"]),
        (
            "ix_contribution_daily_metrics_account_date_campaign_metric",
            ["account_id", "date", "campaign_id", "metric_key"],
        ),
    ),
    CAMPAIGN_GROUPS_TABLE: (
        ("ix_contribution_campaign_groups_account_id", ["account_id"]),
    ),
    SNAPSHOTS_TABLE: (
        ("ix_contribution_snapshots_account_id", ["account_id"]),
        ("ix_contribution_snapshots_status", ["status"]),
        ("ix_contribution_snapshots_runtime_job_id", ["runtime_job_id"]),
    ),
}


def _table_exists(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _existing_indexes(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # 1. contribution_daily_metrics
    if not _table_exists(inspector, DAILY_METRICS_TABLE):
        op.create_table(
            DAILY_METRICS_TABLE,
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("account_id", sa.String(length=120), nullable=False),
            sa.Column("date", sa.String(length=10), nullable=False),
            sa.Column("campaign_id", sa.String(length=120), nullable=False),
            sa.Column("campaign_name", sa.String(), nullable=True),
            sa.Column("spend", sa.Float(), nullable=True),
            sa.Column("impressions", sa.Integer(), nullable=True),
            sa.Column("conversions", sa.Float(), nullable=True),
            sa.Column("conversion_value", sa.Float(), nullable=True),
            sa.Column("metric_key", sa.String(length=50), nullable=False, server_default="omni_purchase"),
            sa.Column("actions_payload", sa.JSON(), nullable=True),
            sa.Column("fetched_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "account_id",
                "date",
                "campaign_id",
                "metric_key",
                name="uq_contribution_daily_metrics_account_date_campaign_metric",
            ),
        )
        inspector = sa.inspect(bind)

    if _table_exists(inspector, DAILY_METRICS_TABLE):
        existing = _existing_indexes(inspector, DAILY_METRICS_TABLE)
        for index_name, columns in INDEX_DEFINITIONS[DAILY_METRICS_TABLE]:
            if index_name not in existing:
                op.create_index(index_name, DAILY_METRICS_TABLE, columns, unique=False)

    # 2. contribution_campaign_groups
    if not _table_exists(inspector, CAMPAIGN_GROUPS_TABLE):
        op.create_table(
            CAMPAIGN_GROUPS_TABLE,
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("account_id", sa.String(length=120), nullable=False),
            sa.Column("group_key", sa.String(length=50), nullable=False),
            sa.Column("group_name", sa.String(length=120), nullable=False),
            sa.Column("campaign_ids", sa.JSON(), nullable=False),
            sa.Column("source", sa.String(length=20), nullable=False, server_default="auto"),
            sa.Column("updated_by", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        inspector = sa.inspect(bind)

    if _table_exists(inspector, CAMPAIGN_GROUPS_TABLE):
        existing = _existing_indexes(inspector, CAMPAIGN_GROUPS_TABLE)
        for index_name, columns in INDEX_DEFINITIONS[CAMPAIGN_GROUPS_TABLE]:
            if index_name not in existing:
                op.create_index(index_name, CAMPAIGN_GROUPS_TABLE, columns, unique=False)

    # 3. contribution_snapshots
    if not _table_exists(inspector, SNAPSHOTS_TABLE):
        op.create_table(
            SNAPSHOTS_TABLE,
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("account_id", sa.String(length=120), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="queued"),
            sa.Column("date_start", sa.String(length=10), nullable=False),
            sa.Column("date_end", sa.String(length=10), nullable=False),
            sa.Column("config", sa.JSON(), nullable=False),
            sa.Column("results", sa.JSON(), nullable=True),
            sa.Column("diagnostics", sa.JSON(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("runtime_job_id", sa.String(length=120), nullable=True),
            sa.Column("created_by", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        inspector = sa.inspect(bind)

    if _table_exists(inspector, SNAPSHOTS_TABLE):
        existing = _existing_indexes(inspector, SNAPSHOTS_TABLE)
        for index_name, columns in INDEX_DEFINITIONS[SNAPSHOTS_TABLE]:
            if index_name not in existing:
                op.create_index(index_name, SNAPSHOTS_TABLE, columns, unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # 反向卸載：先刪索引、再刪表，與 upgrade 對稱。
    for table_name in (SNAPSHOTS_TABLE, CAMPAIGN_GROUPS_TABLE, DAILY_METRICS_TABLE):
        if not _table_exists(inspector, table_name):
            continue
        existing = _existing_indexes(inspector, table_name)
        for index_name, _ in reversed(INDEX_DEFINITIONS[table_name]):
            if index_name in existing:
                op.drop_index(index_name, table_name=table_name)
        op.drop_table(table_name)
