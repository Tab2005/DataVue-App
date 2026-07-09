"""
Contribution Module - Dependencies

模組存取控制：contribution 採 module-only access（同 Meta Andromeda 現行模式），
不分細項權限。require_contribution_module 為本模組所有端點的共用依賴。

帳號層級授權（docs/27 任務 1.3）：contribution 讀寫本地快取表（daily metrics /
groups / snapshots），不像 fb_ads 有「用自己 token 打 Meta API」的隱性授權
門檻——任何有模組權限的使用者原本可用任意 account_id 讀到其他團隊帳號的
快取資料。`verify_account_access_or_403` / `verify_snapshot_account_access_or_404`
補上這層檢查，沿用 `/api/ad-accounts`（routers/facebook.py）的可視範圍判斷
邏輯（見 `modules.fb_ads.accounts_service.resolve_accessible_account_ids`）。

刻意不對 `POST /data/refresh` 套用同一檢查：該端點本來就一律用「呼叫者自己
的」FB token 抓資料（不接受 team token override），Meta 自己的帳號權限已是
等同 fb_ads 的隱性門檻；且該端點刻意不持有 request-scoped DB session 以避免
在等待 Meta API 期間佔用連線池（2026-07-08 事故教訓），而 `team=Depends(
get_current_team)` 會transitively 拉入一個貫穿整個請求生命週期的 session，
重新引入同一類風險，故不在此端點加上 team 依賴。
"""

import asyncio
import logging

from fastapi import Depends, HTTPException, status

from modules.auth.dependencies import get_current_team, get_current_user, require_module
from modules.fb_ads.accounts_service import resolve_accessible_account_ids

logger = logging.getLogger(__name__)


def get_current_contribution_user(user=Depends(get_current_user)):
    """Re-export current user dependency for module-local usage."""
    return user


require_contribution_module = require_module("contribution")
# 本模組所有操作（讀取分組、發起分析、編輯分組、補抓資料）皆需模組存取權；
# 細項權限留待第 2 波依使用回饋再拆分（見 docs/21 第 3.5 節）。
require_contribution_operate = require_contribution_module


async def ensure_account_access(account_id: str, *, team, user) -> None:
    """驗證 `account_id` 在目前 team context 下對 `user` 可視；不可視則 403。

    Async 版本，供本身已是 `async def` 的端點（如 POST /analyses）直接
    `await` 呼叫；同步 `def` 端點請用 `verify_account_access_or_403`。
    """
    accessible_ids, error = await resolve_accessible_account_ids(user, team)
    if error or account_id not in accessible_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"無權存取廣告帳戶 {account_id}",
        )


def verify_account_access_or_403(account_id: str, *, team, user) -> None:
    """`ensure_account_access` 的同步包裝。

    用於 account_id 為顯式 query/body 參數的端點（campaigns / groups
    GET+PUT / analyses 列表）。這些端點目前是同步 `def`（Starlette 於
    threadpool 執行緒呼叫、無 running event loop），用 `asyncio.run` 執行
    內部的 async 授權查詢，不影響 router.py 既有的 sync/async 分工慣例。
    """
    asyncio.run(ensure_account_access(account_id, team=team, user=user))


def verify_snapshot_account_access_or_404(
    account_id: str, *, team, user, snapshot_id: str
) -> None:
    """同 `verify_account_access_or_403`，但用於 snapshot_id 為路徑參數的
    端點（GET /analyses/{id}、PUT .../ai-summary）——未授權時回 404（而非
    403）並使用與「snapshot 不存在」相同的訊息，避免探測者能用狀態碼或
    訊息差異判斷特定 snapshot_id 是否存在（docs/27 任務 1.3）。
    """
    accessible_ids, error = asyncio.run(resolve_accessible_account_ids(user, team))
    if error or account_id not in accessible_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"snapshot {snapshot_id} 不存在",
        )


__all__ = [
    "ensure_account_access",
    "get_current_contribution_user",
    "get_current_team",
    "require_contribution_module",
    "require_contribution_operate",
    "verify_account_access_or_403",
    "verify_snapshot_account_access_or_404",
]
