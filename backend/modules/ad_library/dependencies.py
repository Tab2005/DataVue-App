"""
Ad Library - 模組權限與帳號層級授權（docs/73）

- 模組權限：`ad_library`，module-only access，不分細項權限。
- 帳號層級授權：沿用 `resolve_accessible_account_ids`（同 fb_ads／contribution），
  帳號類端點未授權回 403；以 id 查詢的端點（job / item / media）未授權回 404，
  與「不存在」同訊息，避免洩漏存在性。
"""

from __future__ import annotations

import asyncio

from fastapi import HTTPException, status

from modules.auth.dependencies import require_module
from modules.fb_ads.accounts_service import resolve_accessible_account_ids

require_ad_library_module = require_module("ad_library")


async def accessible_account_ids(user, team) -> set[str]:
    ids, error = await resolve_accessible_account_ids(user, team)
    return set() if error else ids


def verify_account_access_or_403(account_id: str, *, team, user) -> None:
    """同步端點（threadpool 執行緒，無 running loop）用。"""
    if account_id not in asyncio.run(accessible_account_ids(user, team)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"無權存取廣告帳戶 {account_id}",
        )


def verify_resource_access_or_404(account_id: str, *, team, user, not_found_detail: str) -> None:
    if account_id not in asyncio.run(accessible_account_ids(user, team)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found_detail)


def resolve_token_scope(user, team) -> dict:
    """決定抓取廣告時要用哪個 token，與 resolve_accessible_account_ids 相同規則：
    owner 或無團隊 → 使用者自己的 token（strict），owner 失敗時退回團隊 token；
    非 owner 團隊成員 → 團隊 token。
    """
    is_owner = bool(team) and str(team.owner_id) == str(user.id)
    token_team_id = team.id if (team and not is_owner) else None
    return {
        "token_team_id": token_team_id,
        "strict_token": token_team_id is None,
        "fallback_team_id": team.id if (team and is_owner) else None,
    }
