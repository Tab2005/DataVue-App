"""Snapshot share-link helpers for GA4 insights (docs/39 + docs/61)."""

from __future__ import annotations

from ._shared import *


def create_share_link(db, *, snapshot_id: str):
    """凍結目前的來源快照並回傳帶 `share_token` 的副本（docs/61）。

    docs/39 原本把 `share_token` 直接掛在工作快照上，而工作快照每次 GET 都會
    被 upsert 覆寫（payload 換新、ai_summary 重設為 None），造成已分享出去的
    連結內容靜默變動、AI 解讀消失（docs/59 P0-1）。改成分享的當下複製一份
    不可變副本，token 掛在副本上，連結內容就永久凍結在分享當下的樣子。

    重複點擊的語意：**內容沒變就沿用同一個 token**（比對來源的 payload 與
    ai_summary），內容變了就凍結一份新的。兩者都必要——
    - 沿用：使用者連點兩下、或同一份畫面重新開分享，不該每次都產生新連結
    - 新凍結：重新載入分頁拿到新數據後再按分享，該分享的是眼前這份，不是
      早上那份（否則只是把「內容會變」換成「分享到舊資料」，一樣誤導）

    回傳 `None` 代表來源快照不存在，由 router 轉成 404。
    """
    source = repository.get_snapshot_by_id(db, snapshot_id)
    if not source:
        return None

    latest = repository.get_latest_shared_snapshot_for_source(db, source_snapshot_id=snapshot_id)
    if latest is not None and latest.payload == source.payload and latest.ai_summary == source.ai_summary:
        return latest

    return repository.create_shared_snapshot(db, source=source)


def get_snapshot_by_share_token(db, token: str):
    return repository.get_shared_snapshot_by_token(db, token)
