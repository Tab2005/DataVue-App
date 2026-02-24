"""fix_integrations_migration_compat

修復 20260223_p3_integrations_indexes.py 中的 SQLite-only 資料遷移語法。
使用 Python uuid 模組生成 UUID，確保在 SQLite 和 PostgreSQL 均可正常執行。

原問題：舊腳本使用 randomblob() / hex() / json_object() 等 SQLite 專用函式，
在 PostgreSQL 執行 alembic upgrade head 時報錯：
  sqlalchemy.exc.OperationalError: function randomblob(integer) does not exist

修復策略：在 Python 層生成 UUID（uuid.uuid4()），並以 text() 執行 INSERT，
完全繞開方言差異。

涵蓋 provider：
  - facebook    (fb_access_token, token_expires_at, fb_app_id, fb_app_secret)
  - gsc         (gsc_access_token, gsc_refresh_token, gsc_expires_at)
  - ga4         (ga4_access_token, ga4_refresh_token, ga4_expires_at)
  - ai_zeabur   (zeabur_api_key, ai_provider, ai_model)
  - ai_gemini   (gemini_api_key, ai_model)

Revision ID: 20260224_fix_integrations_migration_compat
Revises: 0303de3f01eb
Create Date: 2026-02-24
"""
from __future__ import annotations

import uuid
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Callable, Any

from alembic import op
from sqlalchemy import text

# revision identifiers
revision = "20260224_fix_integrations_migration_compat"
down_revision = "0303de3f01eb"
branch_labels = None
depends_on = None

logger = logging.getLogger("alembic.migration")


# ─────────────────────────────────────────────────────────────────────────────
# 工具函式
# ─────────────────────────────────────────────────────────────────────────────

def _get_now_iso() -> str:
    """回傳 UTC 時間 ISO 字串，SQLite / PostgreSQL 均可直接 INSERT 至 DateTime 欄位。"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _migrate_tokens(
    conn,
    provider: str,
    access_token_col: str,
    refresh_token_col: Optional[str] = None,
    expiry_col: Optional[str] = None,
    extra_data_builder: Optional[Callable[..., Any]] = None,
) -> int:
    """
    將 users 表中的 Token 欄位遷移至 user_integrations 表（跨方言相容版本）。

    Args:
        conn             : SQLAlchemy Connection
        provider         : 整合提供方名稱
        access_token_col : users 表中 access token 欄位名稱
        refresh_token_col: users 表中 refresh token 欄位名稱（可選）
        expiry_col       : users 表中 token 過期時間欄位名稱（可選）
        extra_data_builder: 接受 row dict，回傳 extra_data dict 的函式（可選）

    Returns:
        已遷移的資料筆數
    """
    select_cols = ["id", access_token_col]
    if refresh_token_col:
        select_cols.append(refresh_token_col)
    if expiry_col:
        select_cols.append(expiry_col)

    select_sql = (
        f"SELECT {', '.join(select_cols)} FROM users "
        f"WHERE {access_token_col} IS NOT NULL"
    )

    try:
        rows = conn.execute(text(select_sql)).fetchall()
    except Exception as exc:
        logger.warning(
            "[%s] 查詢 users 表遇到錯誤（欄位可能不存在，跳過此 provider）：%s",
            provider,
            exc,
        )
        return 0

    migrated_count = 0
    now = _get_now_iso()

    for row in rows:
        row_dict = dict(row._mapping)
        user_id = row_dict["id"]
        access_token = row_dict[access_token_col]
        refresh_token = row_dict.get(refresh_token_col) if refresh_token_col else None
        token_expiry = row_dict.get(expiry_col) if expiry_col else None

        # ── 重複檢查：若已存在則跳過（冪等保護）────────────────────────────
        existing = conn.execute(
            text(
                "SELECT id FROM user_integrations "
                "WHERE user_id = :user_id AND provider = :provider"
            ),
            {"user_id": user_id, "provider": provider},
        ).fetchone()

        if existing:
            logger.debug(
                "[%s] 跳過已存在的整合（user_id=%s）", provider, user_id
            )
            continue

        # ── 建立 extra_data JSON 字串 ──────────────────────────────────────
        extra_data_str: Optional[str] = None
        if extra_data_builder:
            try:
                extra_dict = extra_data_builder(row_dict)
                extra_data_str = json.dumps(extra_dict, ensure_ascii=False)
            except Exception as exc:
                logger.debug("[%s] extra_data_builder 失敗：%s", provider, exc)
                extra_data_str = "{}"

        conn.execute(
            text("""
                INSERT INTO user_integrations
                    (id, user_id, provider, access_token, refresh_token,
                     token_expiry, extra_data, created_at, updated_at)
                VALUES
                    (:id, :user_id, :provider, :access_token, :refresh_token,
                     :token_expiry, :extra_data, :created_at, :updated_at)
            """),
            {
                "id": str(uuid.uuid4()),   # ✅ Python 層 UUID，跨 DB 相容
                "user_id": user_id,
                "provider": provider,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_expiry": token_expiry,
                "extra_data": extra_data_str,
                "created_at": now,
                "updated_at": now,
            },
        )
        migrated_count += 1

    logger.info("[%s] 已遷移 %d 筆整合資料", provider, migrated_count)
    return migrated_count


# ─────────────────────────────────────────────────────────────────────────────
# Alembic upgrade / downgrade
# ─────────────────────────────────────────────────────────────────────────────

def upgrade() -> None:
    conn = op.get_bind()
    total = 0

    # 1. Facebook Token
    total += _migrate_tokens(
        conn,
        provider="facebook",
        access_token_col="fb_access_token",
        expiry_col="token_expires_at",
        extra_data_builder=lambda r: {
            "app_id": r.get("fb_app_id") or "",
            "app_secret": r.get("fb_app_secret") or "",
        },
    )

    # 2. Google Search Console Token
    total += _migrate_tokens(
        conn,
        provider="gsc",
        access_token_col="gsc_access_token",
        refresh_token_col="gsc_refresh_token",
        expiry_col="gsc_expires_at",
        extra_data_builder=lambda r: {},
    )

    # 3. Google Analytics 4 Token
    total += _migrate_tokens(
        conn,
        provider="ga4",
        access_token_col="ga4_access_token",
        refresh_token_col="ga4_refresh_token",
        expiry_col="ga4_expires_at",
        extra_data_builder=lambda r: {},
    )

    # 4. Zeabur AI Key
    total += _migrate_tokens(
        conn,
        provider="ai_zeabur",
        access_token_col="zeabur_api_key",
        extra_data_builder=lambda r: {
            "ai_provider": r.get("ai_provider") or "zeabur",
            "ai_model": r.get("ai_model") or "gemini-2.5-flash",
        },
    )

    # 5. Gemini AI Key
    total += _migrate_tokens(
        conn,
        provider="ai_gemini",
        access_token_col="gemini_api_key",
        extra_data_builder=lambda r: {
            "ai_model": r.get("ai_model") or "gemini-2.5-flash",
        },
    )

    logger.info("Token 遷移完成，共遷移 %d 筆資料至 user_integrations", total)


def downgrade() -> None:
    """
    回滾：刪除此次 Python-level 遷移所插入的整合資料。
    注意：此操作不可恢復原始 Token 欄位內容，請謹慎執行。
    """
    conn = op.get_bind()
    conn.execute(
        text(
            "DELETE FROM user_integrations "
            "WHERE provider IN ('facebook', 'gsc', 'ga4', 'ai_zeabur', 'ai_gemini')"
        )
    )
    logger.info("已回滾 user_integrations 中的 Token 遷移資料")
