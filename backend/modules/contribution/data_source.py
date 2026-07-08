"""
Contribution Module - Meta Insights 每日抓取（docs/21 §3.2 / 任務 1.3）

复用 `modules/fb_ads/_base.py` 的 `BASE_URL` 與 `get_headers()`（TokenManager
解密，支援 user/team token 與 fallback），不自建 token 邏輯。

抓取流程：
  GET /{account_id}/insights?level=campaign&time_increment=1
     &fields=campaign_id,campaign_name,spend,impressions,actions,action_values
     &time_range={since:...,until:...}&limit=500
  → 逐頁 cursor 翻頁（paging.cursors.after + paging.next）
  → 逐頁 sleep 300ms 避免 rate limit（沿用 fb_ads 風格）
  → 解析 actions/action_values 為 metric_key 對映，產出 list[dict] 交給
    service 層呼叫 repository.upsert_daily_metrics() 落庫

錯誤處理（沿用 fb_ads 慣例）：
  - token 缺失 → ContributionTokenError（service 層轉 4xx）
  - token 過期 / 權限不足 → ContributionAPIError（含原始 code/message）
  - 網路錯誤 → ContributionFetchError（500）
  - 任何錯誤訊息與 log 中皆不落明文 token
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Awaitable, Callable

import httpx

from modules.fb_ads._base import BASE_URL, TIMEOUT, get_headers

logger = logging.getLogger(__name__)

# FB Marketing API 單頁上限 500 筆；180 天 × 數十個活動 ≪ 500，多為 1 頁
PAGE_LIMIT = 500
# 逐頁 sleep 避免 rate limit（沿用 fb_ads 風格）
INTER_PAGE_SLEEP_SEC = 0.3
# API 抓取最大回溯天數（Meta 對 insights level=campaign 的實際限制）
MAX_DATE_RANGE_DAYS = 180
# 預設轉換指標（無 metric_key 覆寫時使用），對應 FB actions 內 omni_purchase
DEFAULT_METRIC_KEY = "omni_purchase"

# FB API 欄位（單一請求抓齊每日 campaign-level spend/imp/conversions/value）
INSIGHTS_FIELDS = (
    "campaign_id,campaign_name,spend,impressions,actions,action_values"
)


# ── 例外 ──────────────────────────────────────────────────────────────
class ContributionDataSourceError(Exception):
    """Base exception，service 層依 type 轉 4xx/5xx。"""


class ContributionTokenError(ContributionDataSourceError):
    """使用者／團隊 token 缺失或解密失敗（4xx）。"""


class ContributionAPIError(ContributionDataSourceError):
    """FB API 回應包含 error（權限不足、查詢無效等，4xx/5xx 視原始 code）。"""

    def __init__(self, message: str, *, code: int | None = None, fb_code: int | None = None):
        self.code = code
        self.fb_code = fb_code
        super().__init__(message)


class ContributionFetchError(ContributionDataSourceError):
    """網路層錯誤（httpx 拋出，5xx）。"""


# ── 結果模型 ──────────────────────────────────────────────────────────
@dataclass
class DailyMetricRow:
    """單一 (campaign, date) 的每日指標；對應 contribution_daily_metrics 一列。"""

    account_id: str
    date: str  # YYYY-MM-DD
    campaign_id: str
    campaign_name: str | None
    spend: float
    impressions: int
    conversions: float
    conversion_value: float
    metric_key: str
    actions_payload: list[dict[str, Any]] = field(default_factory=list)
    action_values_payload: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """供 repository.upsert_daily_metrics() 寫入；JSON-safe（list / 原生型別）。"""
        return {
            "account_id": self.account_id,
            "date": self.date,
            "campaign_id": self.campaign_id,
            "campaign_name": self.campaign_name,
            "spend": self.spend,
            "impressions": self.impressions,
            "conversions": self.conversions,
            "conversion_value": self.conversion_value,
            "metric_key": self.metric_key,
            "actions_payload": self.actions_payload,
        }


# ── 解析工具 ──────────────────────────────────────────────────────────
# 計算「指定 metric_key 在 actions 陣列中對應的數值」；
# 若該 action_type 不存在則回傳 0.0（保持欄位 schema 穩定）。
_ACTION_TYPE_ALIASES: dict[str, list[str]] = {
    # 預設「omni_purchase」對應 purchase + omni_purchase 兩種 FB action type，
    # 不同廣告帳號/活動可能用不同事件名；本對映沿用既有 fb_ads 模組慣例。
    "omni_purchase": ["omni_purchase", "purchase", "offsite_conversion.fb_pixel_purchase"],
    "purchase": ["purchase", "omni_purchase"],
    "lead": ["lead", "offsite_conversion.fb_pixel_lead"],
    "complete_registration": ["complete_registration"],
    "add_to_cart": ["add_to_cart", "offsite_conversion.fb_pixel_add_to_cart"],
}


def _lookup_action_value(actions: list[dict[str, Any]], metric_key: str) -> float:
    """從 FB actions 陣列查找 metric_key 對應的 value；找不到回 0.0。"""
    aliases = _ACTION_TYPE_ALIASES.get(metric_key, [metric_key])
    allowed = set(aliases)
    total = 0.0
    for entry in actions or []:
        action_type = entry.get("action_type")
        if action_type in allowed:
            try:
                total += float(entry.get("value", 0) or 0)
            except (TypeError, ValueError):
                continue
    return total


def _normalize_date(date_str: str | None) -> str | None:
    """FB time_increment=1 的 date_start/date_stop 為 YYYY-MM-DD；防呆保留。"""
    if not date_str:
        return None
    # FB 回傳的時間皆為 YYYY-MM-DD；如格式異常直接傳回原值供後續診斷
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except (TypeError, ValueError):
        return date_str


def _parse_insights_row(
    raw: dict[str, Any],
    *,
    account_id: str,
    metric_key: str,
) -> DailyMetricRow | None:
    """解析單一 insights 物件為 DailyMetricRow；無 campaign_id 則丟棄。"""
    campaign_id = raw.get("campaign_id")
    if not campaign_id:
        return None
    date_str = _normalize_date(raw.get("date_start"))
    if not date_str:
        return None
    actions = raw.get("actions") or []
    action_values = raw.get("action_values") or []
    try:
        spend = float(raw.get("spend") or 0.0)
        impressions = int(raw.get("impressions") or 0)
    except (TypeError, ValueError):
        spend = 0.0
        impressions = 0
    return DailyMetricRow(
        account_id=account_id,
        date=date_str,
        campaign_id=str(campaign_id),
        campaign_name=raw.get("campaign_name"),
        spend=spend,
        impressions=impressions,
        conversions=_lookup_action_value(actions, metric_key),
        conversion_value=_lookup_action_value(action_values, metric_key),
        metric_key=metric_key,
        actions_payload=list(actions),
        action_values_payload=list(action_values),
    )


# ── 增量抓取視窗 ──────────────────────────────────────────────────────
def _resolve_fetch_window(
    db_window: tuple[str, str] | None,
    *,
    attribution_recency_days: int = 3,
) -> tuple[str, str]:
    """決定本次抓取的 [since, until]。

    db_window 為 None → 抓「近 MAX_DATE_RANGE_DAYS 天」全量初始化。
    db_window 為 (existing_start, existing_end) → 只補最近 attribution_recency_days
    天（歸因回補窗口）以降低 API 呼叫量，同時保留長歷史以供後續分析使用。

    until 永遠為「昨天」（歸因資料通常有 1 天延遲；抓今天資料會被回補覆蓋）。
    """
    today = date.today()
    yesterday = today - timedelta(days=1)
    if db_window is None:
        start = yesterday - timedelta(days=MAX_DATE_RANGE_DAYS - 1)
    else:
        _existing_start, _existing_end = db_window
        start = yesterday - timedelta(days=attribution_recency_days - 1)
    return start.isoformat(), yesterday.isoformat()


# ── 主要抓取 API ──────────────────────────────────────────────────────
async def fetch_account_daily_metrics(
    account_id: str,
    *,
    user_id: str,
    team_id: str | None = None,
    db_window: tuple[str, str] | None = None,
    metric_key: str = DEFAULT_METRIC_KEY,
    client: httpx.AsyncClient | None = None,
    since_until: tuple[str, str] | None = None,
    on_rows: Callable[[list[DailyMetricRow]], Awaitable[None]] | None = None,
) -> list[DailyMetricRow]:
    """從 FB Marketing API 抓取指定帳戶的每日活動指標。

    參數：
      account_id: 'act_xxx' 格式
      user_id, team_id: TokenManager 解密用
      db_window: 已存在資料的 (min_date, max_date)；None 表示首次全量抓取
      metric_key: 目標轉換事件（預設 omni_purchase）
      client: 注入用的 httpx client（測試用）
      since_until: 明確指定 [since, until]，優先於 db_window 推導的視窗；
        供輕量 probe 呼叫使用（避免強制走 180 天全量視窗導致同步阻塞逾時）
      on_rows: 逐頁回呼（async）。提供時每解析完一頁即呼叫一次並「不再」把列
        累積於記憶體，回傳值為空 list——全量 180 天抓取時所有列（含每列完整
        actions_payload）一次堆在記憶體曾把 backend 推到 2GB 併發整台機器
        資源耗盡（2026-07-08 事故），背景抓取一律應以此參數邊抓邊寫。

    回傳：list[DailyMetricRow]（on_rows=None 時），service 層負責寫入
    contribution_daily_metrics；提供 on_rows 時回傳空 list。
    """
    # get_headers 內部走同步 SQLAlchemy session（TokenManager），若直接呼叫會
    # 佔用事件迴圈執行緒；用 to_thread 丟到 threadpool，避免與其他請求爭搶
    # DB 連線池時卡死整個 event loop（同一類根因見本檔案上方 refresh_data
    # 的 Depends(get_db) 修法）。
    headers = await asyncio.to_thread(get_headers, user_id, team_id, allow_fallback=True)
    if not headers:
        # 不在錯誤訊息中帶任何 token 字串
        raise ContributionTokenError("FB token 缺失或解密失敗，請重新授權")

    since, until = since_until if since_until else _resolve_fetch_window(db_window)
    url = f"{BASE_URL}/{account_id}/insights"
    params: dict[str, Any] = {
        "level": "campaign",
        "time_increment": "1",
        "fields": INSIGHTS_FIELDS,
        "time_range": json_compat({"since": since, "until": until}),
        "limit": PAGE_LIMIT,
    }

    rows: list[DailyMetricRow] = []
    fetched = 0
    after: str | None = None
    page = 0
    owns_client = client is None
    if owns_client:
        client = httpx.AsyncClient(timeout=TIMEOUT)

    try:
        while True:
            page += 1
            page_params = dict(params)
            if after:
                page_params["after"] = after
            try:
                response = await client.get(url, headers=headers, params=page_params)
            except httpx.HTTPError as exc:
                raise ContributionFetchError(
                    f"FB API 連線失敗（page={page}）: {type(exc).__name__}"
                ) from exc

            try:
                payload = response.json()
            except ValueError as exc:
                raise ContributionAPIError(
                    f"FB API 回應非 JSON（page={page}, http={response.status_code}）"
                ) from exc

            if "error" in payload:
                err = payload["error"] or {}
                raise ContributionAPIError(
                    err.get("message", "FB API error"),
                    code=response.status_code,
                    fb_code=err.get("code"),
                )

            page_rows: list[DailyMetricRow] = []
            for raw in payload.get("data") or []:
                row = _parse_insights_row(
                    raw, account_id=account_id, metric_key=metric_key
                )
                if row is not None:
                    page_rows.append(row)
            fetched += len(page_rows)
            if on_rows is not None:
                await on_rows(page_rows)
            else:
                rows.extend(page_rows)

            # 翻頁：FB 使用 cursor-based paging，paging.next 為下一頁完整 URL，
            # 也可改用 paging.cursors.after 自組參數；兩者並用以下一頁是否存在
            # 為主訊號，after 為備援（避免漏接）。
            paging = payload.get("paging") or {}
            cursors = paging.get("cursors") or {}
            next_after = cursors.get("after")
            next_url = paging.get("next")
            if not (next_url or next_after):
                break
            after = next_after
            await asyncio.sleep(INTER_PAGE_SLEEP_SEC)
    finally:
        if owns_client:
            await client.aclose()

    logger.info(
        "[Contribution] Fetched %d daily-metric rows for %s (%s..%s, %d page(s))",
        fetched,
        account_id,
        since,
        until,
        page,
    )
    return rows


# ── 工具：JSON-safe 字串（time_range 需為 {"since":..,"until":..}） ─────
def json_compat(obj: Any) -> str:
    """將 dict 序列化成 JSON 字串供 params 使用；FB API 接受 JSON 編碼值。"""
    import json

    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
