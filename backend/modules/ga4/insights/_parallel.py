"""把彼此無資料相依的 GA4 查詢並行化（docs/65 / docs/59 P1-2）。

各洞察模組一次載入會打出好幾支 GA4 查詢，過去是一支接一支 await 完的，
冷快取的首次載入就是這些 round-trip 相加。

**這個模組唯一需要小心的事**：worker thread 絕對不可以碰請求的 SQLAlchemy
Session 或 ORM 物件。Session 不是 thread-safe，而 `GA4Client.get_credentials`
在 token 快過期時會 `db.commit()`——那會把整個請求 Session 當下所有待寫入的
東西一起送出去，commit 後 ORM 屬性過期還會讓下一次屬性讀取變成 SELECT。

所以呼叫端要先在請求執行緒用 `resolve_ga4_credentials()` 把憑證解析好（該刷新
的刷新、該回寫的回寫，就這一次），再把 `credentials` 傳給並行的 `get_analytics`。
`get_analytics` 收到 credentials 就跳過 `get_credentials`，worker thread 上的
呼叫路徑因此完全不含 Session 存取——這是結構性保證，不是「小心不要碰」的約定。
"""

from __future__ import annotations

import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

from ..client import GA4Client

logger = logging.getLogger(__name__)


def _max_workers() -> int:
    try:
        value = int(os.getenv("GA4_INSIGHTS_MAX_PARALLEL_QUERIES", "8"))
    except (TypeError, ValueError):
        return 8
    return max(1, value)


_executor: ThreadPoolExecutor | None = None
_executor_lock = threading.Lock()


def _get_executor() -> ThreadPoolExecutor:
    """模組層級共用單一 pool。

    每次請求現開 pool 在高並發下會爆執行緒；共用 pool 的 worker 上限就是保護。
    這些 task 彼此不互等，pool 滿了只會退化成排隊（＝並行化之前的循序行為），
    不會死鎖。端點本身是同步 def、跑在 FastAPI 的 threadpool 上，我們的 pool
    不會巢狀在自己裡面。
    """
    global _executor
    if _executor is None:
        with _executor_lock:
            if _executor is None:
                _executor = ThreadPoolExecutor(
                    max_workers=_max_workers(), thread_name_prefix="ga4-insights",
                )
    return _executor


def run_parallel(tasks: dict[str, Callable[[], Any]]) -> dict[str, Any]:
    """同時執行 tasks 裡的每個 callable，回傳 {名稱: 回傳值}。

    ⚠️ 每個 callable 都在 worker thread 上跑，不可以碰請求的 Session 或 ORM
    物件（理由見模組 docstring）。GA4 查詢請先 `resolve_ga4_credentials()`，
    再把 credentials 傳進 `get_analytics`。

    task 拋出的例外會原樣往外傳（在第一個取結果時），不會被吞成 None——
    呼叫端既有的錯誤處理才不會因為並行化而失效。
    """
    if not tasks:
        return {}
    # 只有一支查詢時不值得進 pool，直接在當前執行緒跑。
    if len(tasks) == 1:
        (name, task), = tasks.items()
        return {name: task()}

    executor = _get_executor()
    futures = {name: executor.submit(task) for name, task in tasks.items()}
    results: dict[str, Any] = {}
    error: BaseException | None = None
    for name, future in futures.items():
        try:
            results[name] = future.result()
        except BaseException as exc:  # noqa: BLE001 — 原樣轉拋，只是先收完其他 future
            # 先把所有 future 收乾淨再拋，避免有 task 還在跑就離開，
            # 也避免「一支失敗就看不到其他支的例外」。
            if error is None:
                error = exc
    if error is not None:
        raise error
    return results


def resolve_ga4_credentials(user, db):
    """在**請求執行緒**上把 GA4 憑證解析好，供後續並行查詢共用。

    這是唯一會碰 `db`（可能 refresh token 並回寫）的地方，刻意只做一次。
    取不到憑證時回傳 None——後續的 `get_analytics` 會走原本的路徑，得到跟
    並行化之前一模一樣的「No GA4 credentials found」錯誤，行為不變。
    """
    try:
        return GA4Client.get_credentials(user, db)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[GA4Insights] resolve credentials failed: %s", exc)
        return None
