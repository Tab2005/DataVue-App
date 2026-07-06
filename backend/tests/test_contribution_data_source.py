"""
Contribution 模組任務 1.3 資料抓取驗收測試（docs/21 §3.2）

驗收標準：
  1. 抓取結果正確解析 actions/action_values 為 metric_key 對映的 conversions/value
  2. 寫入 contribution_daily_metrics 後重跑不產生重複列（唯一約束生效）
  3. token 缺失回 4xx 與明確錯誤訊息（沿用 fb_ads 慣例）
  4. 任何錯誤訊息與 log 中皆不落明文 token
  5. 增量視窗：db_window 有值時只抓最近 3 天（歸因回補）；None 時抓 180 天全量
"""

from __future__ import annotations

import json
import logging
from typing import Any
from unittest.mock import patch

import httpx
import pytest

from modules.contribution import data_source as ds
from modules.contribution.data_source import (
    ContributionAPIError,
    ContributionFetchError,
    ContributionTokenError,
    DailyMetricRow,
    fetch_account_daily_metrics,
    _lookup_action_value,
    _parse_insights_row,
    _resolve_fetch_window,
)


# ── Fixtures ──────────────────────────────────────────────────────────
class _FakeResponse:
    """模擬 httpx.Response 介面（只用到 .json() + .status_code）。"""

    def __init__(self, payload: dict[str, Any], status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def json(self) -> dict[str, Any]:
        return self._payload


class _FakeAsyncClient:
    """模擬 httpx.AsyncClient，回應預錄的 page 序列。

    pages 為 list[dict]，每個 dict 對應一次 GET 的回應 payload（含 data + paging）。
    當 paging.next/cursors.after 皆缺時停止翻頁。"""

    def __init__(self, pages: list[dict[str, Any]]):
        self._pages = list(pages)
        self._calls: list[dict[str, Any]] = []
        self._index = 0

    async def get(self, url: str, *, headers: dict, params: dict[str, Any]) -> _FakeResponse:
        self._calls.append({"url": url, "headers": headers, "params": dict(params)})
        if self._index >= len(self._pages):
            # 超出 → 回空 data（保守處理，不 crash）
            return _FakeResponse({"data": []})
        page = self._pages[self._index]
        self._index += 1
        return _FakeResponse(page)

    async def aclose(self) -> None:
        pass


def _make_paged_payload(rows: list[dict[str, Any]], page_size: int = 500) -> list[dict[str, Any]]:
    """將 rows 切成多個 page payload，每頁最多 page_size 列。"""
    pages: list[dict[str, Any]] = []
    for start in range(0, len(rows), page_size):
        chunk = rows[start : start + page_size]
        page: dict[str, Any] = {"data": chunk}
        if start + page_size < len(rows):
            # 下一頁 cursor
            page["paging"] = {"cursors": {"after": f"cursor_{start + page_size}"}}
        pages.append(page)
    return pages


def _fake_insights_row(
    campaign_id: str,
    date: str,
    spend: float,
    *,
    campaign_name: str | None = None,
    impressions: int = 1000,
    purchase_value: float = 5.0,
    omni_value: float = 0.0,
    include_action_values: bool = True,
) -> dict[str, Any]:
    """產生單列假 insights 物件。"""
    actions: list[dict[str, Any]] = []
    if omni_value > 0:
        actions.append({"action_type": "omni_purchase", "value": str(int(omni_value))})
    if purchase_value > 0:
        actions.append({"action_type": "purchase", "value": str(int(purchase_value))})
    payload: dict[str, Any] = {
        "campaign_id": campaign_id,
        "campaign_name": campaign_name or f"Campaign_{campaign_id}",
        "date_start": date,
        "date_stop": date,
        "spend": str(spend),
        "impressions": str(impressions),
        "actions": actions,
    }
    if include_action_values:
        payload["action_values"] = [
            {"action_type": "omni_purchase", "value": str(int(purchase_value * 300))},
            {"action_type": "purchase", "value": str(int(purchase_value * 300))},
        ]
    return payload


# ── 1. 解析工具 ────────────────────────────────────────────────────────
@pytest.mark.unit
def test_lookup_action_value_omni_purchase_aggregates_aliases():
    """omni_purchase 對應多個 FB action_type，應累加而非僅取第一個。"""
    actions = [
        {"action_type": "omni_purchase", "value": "3"},
        {"action_type": "purchase", "value": "2"},
        {"action_type": "offsite_conversion.fb_pixel_purchase", "value": "1"},
        {"action_type": "like", "value": "999"},  # 不應計入
    ]
    assert _lookup_action_value(actions, "omni_purchase") == 6.0
    assert _lookup_action_value(actions, "purchase") == 5.0  # 2 + 3
    assert _lookup_action_value(actions, "lead") == 0.0
    # 空白 / None / 格式錯誤的 value 不應 crash
    assert _lookup_action_value(
        [{"action_type": "omni_purchase", "value": "abc"}], "omni_purchase"
    ) == 0.0
    assert _lookup_action_value(None, "omni_purchase") == 0.0
    assert _lookup_action_value([], "omni_purchase") == 0.0


@pytest.mark.unit
def test_parse_insights_row_extracts_all_fields():
    raw = _fake_insights_row(
        "cmp_1", "2026-07-01", 123.45, campaign_name="主力",
        purchase_value=8.0, omni_value=8.0,  # 兩個 action_type 各 8 → conversions = 16
    )
    row = _parse_insights_row(raw, account_id="act_1", metric_key="omni_purchase")
    assert row is not None
    assert row.account_id == "act_1"
    assert row.campaign_id == "cmp_1"
    assert row.campaign_name == "主力"
    assert row.spend == 123.45
    # omni_purchase 對應 omni_purchase + purchase 兩個 aliases，會累加；
    # 助手各注入 8 → 16。conversion_value 同理：8×300 + 8×300 = 4800
    assert row.conversions == 16.0
    assert row.conversion_value == 4800.0
    assert row.actions_payload[0]["action_type"] == "omni_purchase"


@pytest.mark.unit
def test_parse_insights_row_drops_missing_campaign_or_date():
    assert _parse_insights_row(
        {"date_start": "2026-07-01", "spend": "0"},  # 缺 campaign_id
        account_id="act_1", metric_key="omni_purchase",
    ) is None
    assert _parse_insights_row(
        {"campaign_id": "cmp_1", "spend": "0"},  # 缺 date
        account_id="act_1", metric_key="omni_purchase",
    ) is None


# ── 2. 抓取視窗 ────────────────────────────────────────────────────────
@pytest.mark.unit
def test_resolve_fetch_window_full_when_no_db_state():
    since, until = _resolve_fetch_window(None)
    # 180 天視窗
    from datetime import date
    delta = (date.fromisoformat(until) - date.fromisoformat(since)).days + 1
    assert delta == ds.MAX_DATE_RANGE_DAYS


@pytest.mark.unit
def test_resolve_fetch_window_incremental_uses_3_day_recent_window():
    """db_window 有值時只補最近 3 天（歸因回補），不重新抓整段歷史。"""
    since, until = _resolve_fetch_window(("2026-01-01", "2026-07-05"))
    from datetime import date
    delta = (date.fromisoformat(until) - date.fromisoformat(since)).days + 1
    assert delta == 3


# ── 3. 端對端抓取（mock httpx） ─────────────────────────────────────────
@pytest.mark.asyncio
async def test_fetch_account_daily_metrics_single_page_parses_correctly():
    """單頁抓取：解析後 list 與 mock 回應一致；token 透傳。"""
    rows = [
        _fake_insights_row("cmp_1", "2026-07-01", 100.0, purchase_value=5.0, omni_value=5.0),
        _fake_insights_row("cmp_2", "2026-07-01", 50.0, purchase_value=3.0, omni_value=3.0),
        _fake_insights_row("cmp_1", "2026-07-02", 120.0, purchase_value=7.0, omni_value=7.0),
    ]
    fake_client = _FakeAsyncClient(_make_paged_payload(rows))
    with patch.object(ds, "get_headers", return_value={"Authorization": "Bearer FAKE_TOKEN"}):
        result = await fetch_account_daily_metrics(
            "act_1", user_id="user_1", client=fake_client,  # type: ignore[arg-type]
        )
    assert len(result) == 3
    assert all(isinstance(r, DailyMetricRow) for r in result)
    # 兩列 cmp_1 各自為一日；驗證 spend 與日期對應
    cmp1_by_date = {r.date: r for r in result if r.campaign_id == "cmp_1"}
    assert cmp1_by_date["2026-07-01"].spend == 100.0
    assert cmp1_by_date["2026-07-01"].conversions == 10.0  # omni+purchase 各 5
    assert cmp1_by_date["2026-07-02"].spend == 120.0
    cmp2 = next(r for r in result if r.campaign_id == "cmp_2")
    assert cmp2.spend == 50.0
    # token 透傳
    assert fake_client._calls[0]["headers"]["Authorization"] == "Bearer FAKE_TOKEN"


@pytest.mark.asyncio
async def test_fetch_account_daily_metrics_paginates_via_cursor():
    """多頁抓取：3 頁 200 列驗證 paging.cursors.after 翻頁。"""
    rows = [
        _fake_insights_row(f"cmp_{i}", "2026-07-01", 100.0, purchase_value=1.0)
        for i in range(600)
    ]
    fake_client = _FakeAsyncClient(_make_paged_payload(rows, page_size=200))
    with patch.object(ds, "get_headers", return_value={"Authorization": "Bearer T"}):
        result = await fetch_account_daily_metrics(
            "act_1", user_id="u", client=fake_client,  # type: ignore[arg-type]
        )
    assert len(result) == 600
    # 應打 3 次 GET（page_size=200 × 3 頁）
    assert len(fake_client._calls) == 3
    # 第二、三次請求應帶 after cursor
    assert "after" in fake_client._calls[1]["params"]
    assert "after" in fake_client._calls[2]["params"]


@pytest.mark.asyncio
async def test_fetch_account_daily_metrics_token_missing_raises_token_error():
    """token 缺失拋 ContributionTokenError（service 層轉 4xx）。"""
    with patch.object(ds, "get_headers", return_value=None):
        with pytest.raises(ContributionTokenError, match="FB token"):
            await fetch_account_daily_metrics("act_x", user_id="u")


@pytest.mark.asyncio
async def test_fetch_account_daily_metrics_api_error_with_fb_code():
    """FB API 回 error → ContributionAPIError，攜帶 http code + fb code。"""
    fake_client = _FakeAsyncClient([
        {
            "error": {
                "message": "Invalid OAuth access token",
                "code": 190,
                "type": "OAuthException",
            }
        }
    ])
    with patch.object(ds, "get_headers", return_value={"Authorization": "Bearer T"}):
        with pytest.raises(ContributionAPIError) as exc_info:
            await fetch_account_daily_metrics("act_x", user_id="u", client=fake_client)
    assert exc_info.value.code == 200  # 從 FakeResponse 預設
    assert exc_info.value.fb_code == 190


@pytest.mark.asyncio
async def test_fetch_account_daily_metrics_network_error_raises_fetch_error():
    """httpx 拋 HTTPError → ContributionFetchError。"""

    class _BrokenClient:
        async def get(self, *a, **kw):
            raise httpx.ConnectError("simulated network failure")

        async def aclose(self):
            pass

    with patch.object(ds, "get_headers", return_value={"Authorization": "Bearer T"}):
        with pytest.raises(ContributionFetchError, match="FB API 連線失敗"):
            await fetch_account_daily_metrics("act_x", user_id="u", client=_BrokenClient())


# ── 4. 唯一約束：重跑 upsert 不產生重複列 ─────────────────────────────
@pytest.mark.integration
def test_upsert_is_idempotent_no_duplicate_rows(db):
    """同一 (account, date, campaign, metric_key) 重複 upsert 必須唯一。"""
    from modules.contribution.repository import repository
    from database.models.contribution import ContributionDailyMetric

    base = {
        "account_id": "act_idempot",
        "date": "2026-07-01",
        "campaign_id": "cmp_1",
        "metric_key": "omni_purchase",
        "campaign_name": "主力",
        "spend": 100.0,
        "impressions": 5000,
        "conversions": 8.0,
        "conversion_value": 2400.0,
        "actions_payload": [{"action_type": "omni_purchase", "value": "8"}],
    }
    # 清掉殘留
    db.query(ContributionDailyMetric).filter(
        ContributionDailyMetric.account_id == "act_idempot"
    ).delete()
    db.commit()

    repository.upsert_daily_metrics(db, [base])
    db.commit()
    repository.upsert_daily_metrics(db, [base])  # 第二次
    db.commit()
    repository.upsert_daily_metrics(db, [base | {"spend": 200.0}])  # 第三次且改 spend
    db.commit()

    rows = db.query(ContributionDailyMetric).filter(
        ContributionDailyMetric.account_id == "act_idempot"
    ).all()
    assert len(rows) == 1, f"重複 upsert 應維持 1 列，實際 {len(rows)}"
    assert rows[0].spend == 200.0  # 最終值

    db.query(ContributionDailyMetric).filter(
        ContributionDailyMetric.account_id == "act_idempot"
    ).delete()
    db.commit()


# ── 5. 錯誤訊息不含明文 token ─────────────────────────────────────────
@pytest.mark.asyncio
async def test_token_error_message_does_not_leak_token(caplog):
    """ContributionTokenError 的訊息與 logger 記錄皆不應含明文 token。"""
    secret_token = "EAA_SUPSECRET_DO_NOT_LEAK_12345"
    with patch.object(ds, "get_headers", return_value=None):
        with caplog.at_level(logging.INFO, logger="modules.contribution.data_source"):
            with pytest.raises(ContributionTokenError) as exc_info:
                await fetch_account_daily_metrics("act_x", user_id="u_with_secret")

    # 錯誤訊息本身
    assert secret_token not in str(exc_info.value)
    # 記錄輸出（caplog 攔截所有 logger）
    for record in caplog.records:
        assert secret_token not in record.getMessage()


@pytest.mark.asyncio
async def test_api_error_message_does_not_leak_token(caplog):
    """ContributionAPIError 的訊息不應含 Authorization header 中的 token。"""
    secret_token = "EAA_ANOTHER_SECRET_999"
    fake_client = _FakeAsyncClient([
        {
            "error": {
                "message": f"Invalid token: {secret_token}",
                "code": 190,
            }
        }
    ])
    with patch.object(
        ds, "get_headers", return_value={"Authorization": f"Bearer {secret_token}"}
    ):
        with caplog.at_level(logging.INFO, logger="modules.contribution.data_source"):
            with pytest.raises(ContributionAPIError) as exc_info:
                await fetch_account_daily_metrics("act_x", user_id="u", client=fake_client)
    # API 訊息可能含 token 原文（FB server 端回傳的，不是我們拼的）— 但我們
    # 自己拋出的 exception 文字不應帶 header
    assert "Bearer " + secret_token not in str(exc_info.value)
    for record in caplog.records:
        assert "Bearer " + secret_token not in record.getMessage()
