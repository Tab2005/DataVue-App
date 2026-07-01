# run_migration.py
import os
import sys

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

# Add backend to sys.path to allow alembic to import models etc.
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from database import DATABASE_URL, engine


PRE_META_ANDROMEDA_BASELINE = "403dfb0cfbd4"
LEGACY_SENTINEL_TABLES = {
    "users",
    "teams",
    "team_members",
    "team_invites",
    "weekly_reports",
    "report_schedules",
    "saved_views",
    "page_titles",
}


def _build_alembic_config() -> Config:
    alembic_cfg = Config("alembic.ini")
    if DATABASE_URL:
        url = DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        alembic_cfg.set_main_option("sqlalchemy.url", url)
    return alembic_cfg


def _should_stamp_legacy_database() -> bool:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    if not LEGACY_SENTINEL_TABLES.issubset(existing_tables):
        return False

    if "meta_andromeda_score_events" in existing_tables:
        return False

    if "alembic_version" not in existing_tables:
        return True

    with engine.connect() as conn:
        version = conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).scalar()
        if version in (None, ""):
            return True

        # 若 alembic_version 中記錄為舊版，但實際資料表中已存在 "modules" (即已被 init_db 或手動建表)，
        # 我們直接將其 Stamp 至 PRE_META_ANDROMEDA_BASELINE 基線，避免 alembic upgrade 執行舊遷移產生 DuplicateTable 錯誤。
        legacy_revisions = {
            "fe8441e71f69",
            "20260106",
            "20260223_p3_integrations_indexes",
            "20260224_fix_integrations_migration_compat",
            "0303de3f01eb",
            "230a10d75894_add_saved_views_table",
            "20260331_add_weekly_reports",
            "20260331_merge_all_heads"
        }
        if version in legacy_revisions and "modules" in existing_tables:
            return True

    return False


def _ensure_alembic_version_column_capacity() -> None:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    if "alembic_version" not in existing_tables:
        # 2026-07-01 修復：全新資料庫此時 alembic_version 表尚不存在，
        # 若在此直接 return，Alembic 接下來會自動以預設寬度
        # VARCHAR(32) 建立這張表。但本專案有多支 migration 使用超過
        # 32 字元的自訂 revision id（例如
        # "20260224_fix_integrations_migration_compat"，44 字元），
        # 寫入時會因欄位過窄直接報錯
        # (psycopg2.errors.StringDataRightTruncation)，導致整條
        # migration 鏈（PostgreSQL 預設整批在同一交易內執行）全部回滾。
        # 已用全新 PostgreSQL 18 資料庫實測重現並確認此修復可解決：
        # 提前以足夠寬度手動建表，讓 Alembic 直接沿用既有的表。
        if engine.dialect.name == "postgresql":
            with engine.begin() as conn:
                conn.execute(text(
                    "CREATE TABLE alembic_version ("
                    "version_num VARCHAR(128) NOT NULL, "
                    "CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)"
                    ")"
                ))
        return

    columns = inspector.get_columns("alembic_version")
    version_col = next((col for col in columns if col["name"] == "version_num"), None)
    if not version_col:
        return

    current_type = version_col["type"]
    current_length = getattr(current_type, "length", None)
    if current_length is not None and current_length >= 128:
        return

    dialect = engine.dialect.name
    with engine.begin() as conn:
        if dialect == "postgresql":
            conn.execute(text("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(128)"))
        elif dialect == "sqlite":
            return
        else:
            try:
                conn.execute(text("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(128)"))
            except Exception:
                pass


def _stamp_legacy_database(alembic_cfg: Config) -> None:
    print(
        "Detected existing legacy DataVue schema without Alembic version metadata. "
        f"Stamping baseline revision {PRE_META_ANDROMEDA_BASELINE} before upgrade."
    )
    command.stamp(alembic_cfg, PRE_META_ANDROMEDA_BASELINE)


def run_upgrade():
    alembic_cfg = _build_alembic_config()
    _ensure_alembic_version_column_capacity()

    if _should_stamp_legacy_database():
        _stamp_legacy_database(alembic_cfg)

    command.upgrade(alembic_cfg, "head")
    print("Migration upgrade successful.")


if __name__ == "__main__":
    try:
        run_upgrade()
    except Exception as e:
        print(f"Error running migration: {e}")
        sys.exit(1)
