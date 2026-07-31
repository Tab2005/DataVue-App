"""ga4 shared snapshots: immutable share-link copies (docs/61)

Revision ID: 20260731_ga4_shared_snapshots
Revises: 20260731_fb_ads_analytics_ai_snapshots
Create Date: 2026-07-31 00:00:00.000000

分享連結原本掛在 `ga4_insights_snapshots.share_token` 上，而那張表每次 GET
報表都會被 upsert 覆寫，導致已分享的連結內容靜默變動、AI 解讀消失
（docs/59 P0-1）。本 migration 建立 `ga4_shared_snapshots` 存放不可變副本，
並把既有的分享連結搬過去，讓已經發出去的連結繼續可用。

刻意**不刪除**舊的 `share_token` 欄位：保留可回滾的餘地，且不破壞任何既有
資料。新程式碼只讀新表，舊欄位自然停用。
"""

from alembic import op
import sqlalchemy as sa


revision = "20260731_ga4_shared_snapshots"
down_revision = "20260731_fb_ads_analytics_ai_snapshots"
branch_labels = None
depends_on = None


TABLE = "ga4_shared_snapshots"
SOURCE_TABLE = "ga4_insights_snapshots"


def _table_exists(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _existing_indexes(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _table_exists(inspector, TABLE):
        op.create_table(
            TABLE,
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("source_snapshot_id", sa.String(), nullable=True),
            sa.Column("property_id", sa.String(length=50), nullable=False),
            sa.Column("kind", sa.String(length=80), nullable=False),
            sa.Column("date", sa.String(length=10), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=False),
            sa.Column("ai_summary", sa.Text(), nullable=True),
            sa.Column("ai_summary_generated_at", sa.DateTime(), nullable=True),
            sa.Column("share_token", sa.String(length=64), nullable=False),
            sa.Column("created_by", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        inspector = sa.inspect(bind)

    existing = _existing_indexes(inspector, TABLE) if _table_exists(inspector, TABLE) else set()
    if "ix_ga4_shared_snapshots_share_token" not in existing:
        op.create_index("ix_ga4_shared_snapshots_share_token", TABLE, ["share_token"], unique=True)
    if "ix_ga4_shared_snapshots_property_id" not in existing:
        op.create_index("ix_ga4_shared_snapshots_property_id", TABLE, ["property_id"], unique=False)
    if "ix_ga4_shared_snapshots_source_snapshot_id" not in existing:
        op.create_index("ix_ga4_shared_snapshots_source_snapshot_id", TABLE, ["source_snapshot_id"], unique=False)

    _backfill_existing_share_links(bind)


def _backfill_existing_share_links(bind) -> None:
    """把既有的分享連結搬進新表，讓已經發出去的連結繼續可用。

    以 `share_token` 判斷是否已搬過，重跑本 migration 不會重複插入。
    來源列的 payload/ai_summary 就是目前的內容——搬過去之後才真正凍結，
    在此之前它們本來就會隨 upsert 變動，這裡沒有辦法也不需要回溯還原。

    讀寫都走 SQLAlchemy Core 的 typed selectable：`payload` 是 JSON 欄位，
    Postgres 會回傳已解析的 dict、SQLite 回傳字串，用 raw SQL 直接搬會在其中
    一邊壞掉，交給 dialect 處理才兩邊都對。
    """
    import uuid

    inspector = sa.inspect(bind)
    if not _table_exists(inspector, SOURCE_TABLE):
        return

    source_columns = {col["name"] for col in inspector.get_columns(SOURCE_TABLE)}
    if "share_token" not in source_columns:
        return

    source = sa.table(
        SOURCE_TABLE,
        sa.column("id", sa.String),
        sa.column("property_id", sa.String),
        sa.column("kind", sa.String),
        sa.column("date", sa.String),
        sa.column("payload", sa.JSON),
        sa.column("ai_summary", sa.Text),
        sa.column("ai_summary_generated_at", sa.DateTime),
        sa.column("share_token", sa.String),
        sa.column("fetched_by", sa.String),
    )
    target = sa.table(
        TABLE,
        sa.column("id", sa.String),
        sa.column("source_snapshot_id", sa.String),
        sa.column("property_id", sa.String),
        sa.column("kind", sa.String),
        sa.column("date", sa.String),
        sa.column("payload", sa.JSON),
        sa.column("ai_summary", sa.Text),
        sa.column("ai_summary_generated_at", sa.DateTime),
        sa.column("share_token", sa.String),
        sa.column("created_by", sa.String),
    )

    rows = bind.execute(
        sa.select(
            source.c.id, source.c.property_id, source.c.kind, source.c.date,
            source.c.payload, source.c.ai_summary, source.c.ai_summary_generated_at,
            source.c.share_token, source.c.fetched_by,
        ).where(source.c.share_token.isnot(None))
    ).mappings().all()
    if not rows:
        return

    already = {row[0] for row in bind.execute(sa.select(target.c.share_token)).all()}

    pending = [
        {
            "id": f"gss_{uuid.uuid4().hex[:12]}",
            "source_snapshot_id": row["id"],
            "property_id": row["property_id"],
            "kind": row["kind"],
            "date": row["date"],
            "payload": row["payload"],
            "ai_summary": row["ai_summary"],
            "ai_summary_generated_at": row["ai_summary_generated_at"],
            "share_token": row["share_token"],
            "created_by": row["fetched_by"],
        }
        for row in rows
        if row["share_token"] not in already
    ]
    if pending:
        bind.execute(target.insert(), pending)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if _table_exists(inspector, TABLE):
        op.drop_table(TABLE)
