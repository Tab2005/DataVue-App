"""Shared constants and helpers for GA4 insights services."""

from __future__ import annotations

import asyncio
import logging
import os
import re
import smtplib
import sys
from datetime import date, datetime, timedelta
from email.message import EmailMessage
from statistics import median

from database import User
from ga4_service import GA4Service
from services.line_service import send_line_push_message

from ..anomaly import build_expected_range, evaluate_anomaly
from ..client import GA4Client
from ..repository import repository

logger = logging.getLogger(__name__)

METRIC_LABELS = {
    "conversions": "轉換",
    "sessions": "工作階段",
    "purchase_revenue": "營收",
    "purchaseRevenue": "營收",
}
SUPPORTED_METRICS = {
    "conversions": "conversions",
    "sessions": "sessions",
    "purchase_revenue": "purchaseRevenue",
}

# 第 2 波：當日儀表板／渠道／到達頁／商品（docs/22 3.2-3.4 節）
DASHBOARD_KIND = "intraday_dashboard"
DASHBOARD_METRICS = ["sessions", "conversions", "purchaseRevenue"]
DASHBOARD_REFRESH_COOLDOWN_MINUTES = 10
# 沿用第 1 波 evaluate_rule 已用的 "intraday_hourly" kind 是單指標的告警記帳快照，
# 與本節多指標＋渠道拆解的儀表板快照 schema 不同，故另立 DASHBOARD_KIND 避免
# upsert_snapshot 的 (property_id, kind, date) 唯一鍵互相覆寫。
REALTIME_WINDOW_MINUTES = 30
CHANNEL_METRIC = "conversions"

# 第 4 波：渠道對照維度切換（docs/22 5 節，追加）。白名單把下拉選項對映成
# 一對 GA4 維度（收單視角、開發視角），杜絕前端直傳任意 GA4 維度名。
CHANNEL_DIMENSION_MAP = {
    "default_channel_group": ("sessionDefaultChannelGroup", "firstUserDefaultChannelGroup"),
    "source_medium": ("sessionSourceMedium", "firstUserSourceMedium"),
    "source": ("sessionSource", "firstUserSource"),
    "medium": ("sessionMedium", "firstUserMedium"),
    "campaign": ("sessionCampaignName", "firstUserCampaignName"),
}
CHANNEL_DEFAULT_DIMENSION = "default_channel_group"

# docs/34 第一波：歸因模式揭露。「報表歸因模式」是 property 層級設定、極少變動，
# 用固定 sentinel date 把 (property_id, kind) 當單例快取 key，而非日期資料。
ATTRIBUTION_SETTINGS_KIND = "attribution_settings"
ATTRIBUTION_SETTINGS_DATE = "static"
ATTRIBUTION_SETTINGS_CACHE_HOURS = 24
# AttributionSettings.ReportingAttributionModel enum 名稱 → 前端顯示用的正規化值；
# 未列出的 enum（含 UNSPECIFIED）與查詢失敗一律回退 "unknown"。
ATTRIBUTION_MODEL_MAP = {
    "PAID_AND_ORGANIC_CHANNELS_DATA_DRIVEN": "data_driven",
    "PAID_AND_ORGANIC_CHANNELS_LAST_CLICK": "last_click",
    "GOOGLE_PAID_CHANNELS_LAST_CLICK": "last_click",
}
CHANNEL_TOP_N = 20
# docs/34 第三波：小樣本比例穩健化。開發+收單總量低於此門檻時，即使收單>0
# 也一律判 insufficient_data，避免單一事件把比例推向 0 或無限大的假象標籤
# （例：開發0/收單6 這種案例，比例=0.00 卻只有 6 筆轉換，統計上不具代表性）。
CHANNEL_MIN_SAMPLE = int(os.getenv("GA4_CHANNEL_MIN_SAMPLE", "10"))

# 第 3 波：KPI 目標追蹤（docs/22 5 節，選配）
KPI_PERIOD_TYPES = {"month", "quarter"}
# 進度領先/落後的緩衝帶：達成率相對「時間進度」超出 ±5 個百分點才判定 ahead/behind，
# 避免時間進度剛好卡在整數邊界時，一點點雜訊就在 on_track/ahead 之間來回跳動。
KPI_PACING_BUFFER = 0.05

# 第 5 波：到達頁分類篩選（docs/22 5 節，追加）
LANDING_PAGE_CATEGORIES = ("product", "article", "functional", "other")
# 內建預設關鍵詞啟發式：只在該 property 完全沒有自訂規則時當退回值，
# 冷啟動堪用，UI 明示「可自訂規則覆蓋」。
LANDING_PAGE_DEFAULT_KEYWORDS = {
    "product": ("/product", "/products", "/item", "/shop", "/p/"),
    "article": ("/blog", "/article", "/news", "/post"),
    "functional": (
        "/cart", "/checkout", "/login", "/register", "/search",
        "/account", "/member", "/contact", "/about",
    ),
}
# 2026-07-10 與使用者確認的轉換率口徑修正：「轉換率」欄改用 GA4 官方
# sessionKeyEventRate（至少觸發一次關鍵事件的工作階段占比，去重、≤100%），
# 「轉換次數」欄是 keyEvents 次數（同一工作階段多次觸發會重複計，可能超過工作階段數）。
LANDING_PAGE_SESSION_KEY_EVENT_RATE_DEFINITION = (
    "至少觸發一次關鍵事件的工作階段占比（GA4 工作階段關鍵事件發生率）"
)
LANDING_PAGE_KEY_EVENTS_COUNT_DEFINITION = (
    "關鍵事件總次數；同一工作階段多次觸發會重複計，可能超過工作階段數"
)
# key_event 白名單格式（GA4 事件名規則），防任意指標注入。
LANDING_PAGE_KEY_EVENT_PATTERN = re.compile(r"^[A-Za-z0-9_]{1,40}$")

# 第 6 波：商品分析篩選＋購買轉換率＋口徑對齊（docs/22 5 節，追加）
ITEM_METRICS_WITH_OFFICIAL_RATES = [
    "itemsViewed", "itemsAddedToCart", "itemsPurchased", "itemRevenue",
    "cartToViewRate", "purchaseToViewRate",
]
# 相容性保險（任務 1.4）：若 GA4 回相容性錯誤（cartToViewRate/purchaseToViewRate
# 與 itemName 無法同查），退回不含官方比率的基礎指標，改用本地件數比計算。
ITEM_METRICS_FALLBACK = ["itemsViewed", "itemsAddedToCart", "itemsPurchased", "itemRevenue"]
ITEM_CART_TO_VIEW_RATE_DEFINITION = "看過此商品的使用者中，把它加入購物車的比率（使用者去重）"
ITEM_PURCHASE_TO_VIEW_RATE_DEFINITION = "看過此商品的使用者中，購買它的比率（使用者去重）"


def _service_attr(name: str, fallback):
    facade = sys.modules.get("modules.ga4.insights_service")
    service = getattr(facade, "GA4InsightsService", None) if facade is not None else None
    return getattr(service, name, fallback)


def _facade_attr(name: str, fallback):
    facade = sys.modules.get("modules.ga4.insights_service")
    return getattr(facade, name, fallback) if facade is not None else fallback

def _get_channel_min_sample() -> int:
    facade = sys.modules.get("modules.ga4.insights_service")
    if facade is not None and hasattr(facade, "CHANNEL_MIN_SAMPLE"):
        return int(getattr(facade, "CHANNEL_MIN_SAMPLE"))
    return CHANNEL_MIN_SAMPLE


def _percentile(sorted_values: list[float], fraction: float) -> float:
    """線性插值百分位數（同 numpy 預設方法），輸入須已排序。"""
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    idx = fraction * (len(sorted_values) - 1)
    lower = int(idx)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = idx - lower
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * weight


def classify_landing_page(path: str, rules: list[dict]) -> str:
    """
    純函數：把 `landingPage` 路徑分類成 product/article/functional/other。

    - 有自訂規則（`rules` 非空）時**只**用自訂規則：依 `priority` 升冪找第一個
      比對成功的規則，比對不到任何規則就直接歸 `other`（不退回內建關鍵詞，
      避免自訂規則與內建預設疊加造成分類邏輯難以預期）。
    - 沒有任何自訂規則時，用內建關鍵詞啟發式（冷啟動堪用值）。
    - 比對一律大小寫不敏感。
    """
    path_lower = (path or "").lower()

    if rules:
        for rule in sorted(rules, key=lambda r: r["priority"]):
            pattern = (rule["pattern"] or "").lower()
            if not pattern:
                continue
            if rule["match_type"] == "prefix" and path_lower.startswith(pattern):
                return rule["category"]
            if rule["match_type"] == "contains" and pattern in path_lower:
                return rule["category"]
        return "other"

    for category, keywords in LANDING_PAGE_DEFAULT_KEYWORDS.items():
        if any(keyword in path_lower for keyword in keywords):
            return category
    return "other"


def classify_item_category(item_name: str, ga4_category: str | None, rules: list[dict]) -> tuple[str, str]:
    """
    純函數：決定商品的最終分類與其來源（第 7 波，追加）。

    優先順序（與到達頁的「自訂規則搭配內建關鍵詞退回」設計不同，這裡是
    「GA4 權威、自訂規則補充」）：
    1. GA4 的 `itemCategory` 有值（非 `(not set)`/空字串）→ 直接採用，來源 "ga4"。
       GA4 是商店既有分類的權威資料，永遠優先，避免兩套資料互搶同一商品的分類權。
    2. GA4 沒有值時，依自訂規則（`priority` 升冪、`itemName` 比對、大小寫
       不敏感）找第一個比對成功的規則，來源 "custom_rule"。
    3. 都沒有 → `(not set)`，來源 "unset"。
    """
    if ga4_category and ga4_category != "(not set)":
        return ga4_category, "ga4"

    name_lower = (item_name or "").lower()
    for rule in sorted(rules, key=lambda r: r["priority"]):
        pattern = (rule["pattern"] or "").lower()
        if not pattern:
            continue
        if rule["match_type"] == "prefix" and name_lower.startswith(pattern):
            return rule["category"], "custom_rule"
        if rule["match_type"] == "contains" and pattern in name_lower:
            return rule["category"], "custom_rule"

    return "(not set)", "unset"


def _format_metric_value(metric_key: str, value: float) -> str:
    if metric_key in {"purchase_revenue", "purchaseRevenue"}:
        return f"{value:,.2f}"
    return f"{value:,.0f}"


def _fetch_metric_total(*, user: User, property_id: str, date_value: str, api_metric: str, db, by_hour: bool = False, current_hour: int | None = None):
    dimensions = ["hour"] if by_hour else []
    data, error = GA4Service.get_analytics(
        user=user,
        property_id=property_id,
        start_date=date_value,
        end_date=date_value,
        metrics=[api_metric],
        dimensions=dimensions,
        db=db,
    )
    if error or not data:
        raise RuntimeError(error or "GA4 data unavailable")
    rows = data.get("rows", [])
    if not by_hour:
        return float(rows[0].get(api_metric, 0)) if rows else 0.0, rows
    total = 0.0
    for row in rows:
        hour_value = int(row.get("hour", 0))
        if current_hour is not None and hour_value > current_hour:
            continue
        total += float(row.get(api_metric, 0))
    return total, rows


def _historical_dates(now_local: datetime, weeks: int = 8) -> list[str]:
    return [
        (now_local.date() - timedelta(days=7 * offset)).isoformat()
        for offset in range(1, weeks + 1)
    ]


def _trailing_period(days: int, *, now_local: datetime | None = None) -> tuple[str, str]:
    now_local = now_local or datetime.utcnow() + timedelta(hours=8)
    end_date = now_local.date() - timedelta(days=1)
    start_date = end_date - timedelta(days=max(days, 1) - 1)
    return start_date.isoformat(), end_date.isoformat()

__all__ = [name for name in globals() if not name.startswith("__")]
