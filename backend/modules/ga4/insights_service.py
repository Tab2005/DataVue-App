"""GA4 insights wave-1 service helpers."""

from __future__ import annotations

import asyncio
import logging
import os
import re
import smtplib
from datetime import date, datetime, timedelta
from email.message import EmailMessage
from statistics import median

from database import User
from ga4_service import GA4Service
from services.line_service import send_line_push_message

from .anomaly import build_expected_range, evaluate_anomaly
from .client import GA4Client
from .repository import repository

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


class GA4InsightsService:
    @staticmethod
    def list_rules(db, *, user_id: str, property_id: str | None = None):
        return repository.list_rules(db, created_by=user_id, property_id=property_id)

    @staticmethod
    def create_rule(db, *, user_id: str, payload: dict):
        payload = {**payload, "created_by": user_id}
        return repository.create_rule(db, **payload)

    @staticmethod
    def update_rule(db, *, rule_id: str, user_id: str, payload: dict):
        row = repository.get_rule(db, rule_id)
        if not row or row.created_by != user_id:
            return None
        for key, value in payload.items():
            setattr(row, key, value)
        row.updated_at = datetime.utcnow()
        db.add(row)
        return row

    @staticmethod
    def delete_rule(db, *, rule_id: str, user_id: str):
        row = repository.get_rule(db, rule_id)
        if not row or row.created_by != user_id:
            return False
        return repository.delete_rule(db, rule_id)

    @staticmethod
    def list_events(db, *, user_id: str, property_id: str | None = None, page: int = 1, page_size: int = 20):
        return repository.list_events(
            db,
            property_id=property_id,
            created_by=user_id,
            page=page,
            page_size=page_size,
        )

    @staticmethod
    def acknowledge_event(db, *, event_id: str, user_id: str):
        row = repository.get_event(db, event_id)
        if not row or row.rule.creator.id != user_id:
            return None
        return repository.acknowledge_event(db, event_id=event_id, user_id=user_id)

    @staticmethod
    def _format_metric_value(metric_key: str, value: float) -> str:
        if metric_key in {"purchase_revenue", "purchaseRevenue"}:
            return f"{value:,.2f}"
        return f"{value:,.0f}"

    @staticmethod
    def build_alert_message(*, property_label: str, metric_key: str, observed: float, expected_low: float, expected_high: float) -> str:
        metric_label = METRIC_LABELS.get(metric_key, metric_key)
        return (
            f"⚠️ GA4 異常（{property_label}）\n"
            f"{metric_label} 今日累計 {GA4InsightsService._format_metric_value(metric_key, observed)}，"
            f"低於/高於預期區間 {GA4InsightsService._format_metric_value(metric_key, expected_low)}"
            f"~{GA4InsightsService._format_metric_value(metric_key, expected_high)}（過去 8 週同時段基線）\n"
            f"可能方向：檢查廣告投放是否中斷 / 網站追蹤碼 / 檔期效應\n"
            f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/ga4-insights"
        )

    @staticmethod
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

    @staticmethod
    def _historical_dates(now_local: datetime, weeks: int = 8) -> list[str]:
        return [
            (now_local.date() - timedelta(days=7 * offset)).isoformat()
            for offset in range(1, weeks + 1)
        ]

    @staticmethod
    async def _send_email_if_possible(email_to: str, subject: str, body: str) -> bool:
        host = os.getenv("SMTP_HOST", "").strip()
        port = int(os.getenv("SMTP_PORT", "587"))
        username = os.getenv("SMTP_USERNAME", "").strip()
        password = os.getenv("SMTP_PASSWORD", "").strip()
        from_email = os.getenv("SMTP_FROM_EMAIL", username).strip()
        if not host or not from_email or not email_to:
            return False

        def _send():
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = from_email
            msg["To"] = email_to
            msg.set_content(body)
            with smtplib.SMTP(host, port, timeout=10) as smtp:
                smtp.starttls()
                if username:
                    smtp.login(username, password)
                smtp.send_message(msg)

        try:
            await asyncio.to_thread(_send)
            return True
        except Exception:
            logger.exception("[GA4Insights] email notification failed")
            return False

    @staticmethod
    async def evaluate_rule(db, rule, *, now_local: datetime | None = None):
        now_local = now_local or datetime.utcnow() + timedelta(hours=8)
        user = db.query(User).filter(User.id == rule.created_by).first()
        if not user:
            return {"status": "skipped", "reason": "user_not_found"}

        api_metric = SUPPORTED_METRICS.get(rule.metric_key)
        if not api_metric:
            return {"status": "skipped", "reason": "unsupported_metric"}

        target_date = now_local.date().isoformat() if rule.check_frequency == "hourly" else (now_local.date() - timedelta(days=1)).isoformat()
        current_hour = now_local.hour if rule.check_frequency == "hourly" else None
        observed, raw_rows = GA4InsightsService._fetch_metric_total(
            user=user,
            property_id=rule.property_id,
            date_value=target_date,
            api_metric=api_metric,
            db=db,
            by_hour=rule.check_frequency == "hourly",
            current_hour=current_hour,
        )

        snapshot_kind = "intraday_hourly" if rule.check_frequency == "hourly" else "daily_totals"
        snapshot_payload = {
            "metric_totals": {rule.metric_key: observed},
            "rows": raw_rows,
            "current_hour": current_hour,
            "check_frequency": rule.check_frequency,
        }
        repository.upsert_snapshot(
            db,
            property_id=rule.property_id,
            kind=snapshot_kind,
            date=target_date,
            payload=snapshot_payload,
            fetched_by=user.id,
        )

        samples: list[float] = []
        for sample_date in GA4InsightsService._historical_dates(now_local):
            try:
                sample_total, _ = GA4InsightsService._fetch_metric_total(
                    user=user,
                    property_id=rule.property_id,
                    date_value=sample_date,
                    api_metric=api_metric,
                    db=db,
                    by_hour=rule.check_frequency == "hourly",
                    current_hour=current_hour,
                )
            except Exception:
                logger.warning("[GA4Insights] skip baseline sample %s %s", rule.property_id, sample_date)
                continue
            samples.append(sample_total)

        result = evaluate_anomaly(observed=observed, samples=samples, sensitivity=rule.sensitivity)
        if not result or not result["is_anomaly"]:
            return {"status": "ok", "observed": observed, "samples": len(samples)}

        if repository.get_recent_event_for_rule(db, rule_id=rule.id, cooldown_hours=rule.cooldown_hours):
            return {"status": "cooled_down", "observed": observed}

        message = GA4InsightsService.build_alert_message(
            property_label=rule.property_id,
            metric_key=rule.metric_key,
            observed=observed,
            expected_low=result["low"],
            expected_high=result["high"],
        )
        notified_channels = {}
        if rule.notify_line and user.line_user_id:
            notified_channels["line"] = await send_line_push_message(user.line_user_id, message)
        if rule.notify_email and user.email:
            notified_channels["email"] = await GA4InsightsService._send_email_if_possible(
                user.email,
                f"GA4 異常通知 {rule.property_id}",
                message,
            )
        repository.create_event(
            db,
            rule_id=rule.id,
            severity=result["severity"],
            direction=result["direction"],
            observed_value=observed,
            expected_low=result["low"],
            expected_high=result["high"],
            message=message,
            notified_channels=notified_channels,
        )
        return {"status": "alerted", "severity": result["severity"], "direction": result["direction"]}

    # ─── 第 2 波：當日儀表板（3.2 節） ──────────────────────────────
    @staticmethod
    def _fetch_intraday_dashboard_payload(*, user: User, property_id: str, db, now_local: datetime | None = None) -> dict:
        now_local = now_local or datetime.utcnow() + timedelta(hours=8)
        today = now_local.date().isoformat()
        current_hour = now_local.hour

        data, error = GA4Service.get_analytics(
            user=user,
            property_id=property_id,
            start_date=today,
            end_date=today,
            metrics=DASHBOARD_METRICS,
            dimensions=["hour", "sessionDefaultChannelGroup"],
            db=db,
        )
        if error:
            raise RuntimeError(error)
        rows = (data or {}).get("rows", [])

        hourly_totals: dict[int, dict[str, float]] = {}
        cumulative_totals = {metric: 0.0 for metric in DASHBOARD_METRICS}
        for row in rows:
            hour_value = int(row.get("hour", 0))
            bucket = hourly_totals.setdefault(hour_value, {metric: 0.0 for metric in DASHBOARD_METRICS})
            for metric in DASHBOARD_METRICS:
                value = float(row.get(metric, 0) or 0)
                bucket[metric] += value
                if hour_value <= current_hour:
                    cumulative_totals[metric] += value

        hourly_totals_list = [
            {"hour": f"{hour:02d}", **values} for hour, values in sorted(hourly_totals.items())
        ]

        baseline: dict[str, dict | None] = {}
        is_anomaly: dict[str, bool] = {}
        for metric in DASHBOARD_METRICS:
            samples: list[float] = []
            for sample_date in GA4InsightsService._historical_dates(now_local):
                try:
                    sample_total, _ = GA4InsightsService._fetch_metric_total(
                        user=user,
                        property_id=property_id,
                        date_value=sample_date,
                        api_metric=metric,
                        db=db,
                        by_hour=True,
                        current_hour=current_hour,
                    )
                except Exception:
                    logger.warning("[GA4Insights] dashboard baseline sample failed %s %s", property_id, sample_date)
                    continue
                samples.append(sample_total)
            expected = build_expected_range(samples, "medium")
            baseline[metric] = expected
            observed = cumulative_totals[metric]
            is_anomaly[metric] = bool(expected and (observed < expected["low"] or observed > expected["high"]))

        return {
            "date": today,
            "current_hour": current_hour,
            "channel_breakdown": rows,
            "hourly_totals": hourly_totals_list,
            "cumulative_totals": cumulative_totals,
            "baseline": baseline,
            "is_anomaly": is_anomaly,
        }

    @staticmethod
    def _refresh_dashboard_snapshot(db, *, user: User, property_id: str):
        payload = GA4InsightsService._fetch_intraday_dashboard_payload(user=user, property_id=property_id, db=db)
        return repository.upsert_snapshot(
            db,
            property_id=property_id,
            kind=DASHBOARD_KIND,
            date=payload["date"],
            payload=payload,
            fetched_by=user.id,
        )

    @staticmethod
    def get_dashboard(db, *, user: User, property_id: str):
        """讀快取；首次造訪（job 尚未跑過）時同步抓一次做 bootstrap（3.2 節）。"""
        today = (datetime.utcnow() + timedelta(hours=8)).date().isoformat()
        snapshot = repository.get_latest_snapshot(db, property_id=property_id, kind=DASHBOARD_KIND, date=today)
        if not snapshot:
            snapshot = GA4InsightsService._refresh_dashboard_snapshot(db, user=user, property_id=property_id)
        return snapshot

    @staticmethod
    def refresh_dashboard(db, *, user: User, property_id: str):
        """手動刷新，每 property 10 分鐘一次的 rate limit（3.2 節）。"""
        today = (datetime.utcnow() + timedelta(hours=8)).date().isoformat()
        existing = repository.get_latest_snapshot(db, property_id=property_id, kind=DASHBOARD_KIND, date=today)
        if existing:
            elapsed = datetime.utcnow() - existing.fetched_at
            if elapsed < timedelta(minutes=DASHBOARD_REFRESH_COOLDOWN_MINUTES):
                return existing, False
        snapshot = GA4InsightsService._refresh_dashboard_snapshot(db, user=user, property_id=property_id)
        return snapshot, True

    # ─── 第 2 波：Realtime 心跳（3.2 節，即打即查、不進快取） ──────────
    @staticmethod
    def get_realtime(*, user: User, property_id: str, db) -> dict:
        creds = GA4Client.get_credentials(user, db)
        if not creds:
            raise RuntimeError("No GA4 credentials found")

        total_response = GA4Client.run_realtime_report(creds, property_id, [], ["activeUsers", "eventCount"])
        total_active_users = 0
        total_events = 0
        if total_response.rows:
            total_active_users = int(total_response.rows[0].metric_values[0].value or 0)
            total_events = int(total_response.rows[0].metric_values[1].value or 0)

        breakdown_response = GA4Client.run_realtime_report(
            creds, property_id, ["unifiedScreenName"], ["activeUsers"], limit=10
        )
        by_screen = [
            {
                "screen_name": row.dimension_values[0].value or "(not set)",
                "active_users": int(row.metric_values[0].value or 0),
            }
            for row in breakdown_response.rows
        ]

        return {
            "window_minutes": REALTIME_WINDOW_MINUTES,
            "active_users": total_active_users,
            "event_count": total_events,
            "by_screen": by_screen,
        }

    # ─── 共用：daily snapshot 的期間計算（昨日往前 N 天，避免當日資料未完整） ──
    @staticmethod
    def _trailing_period(days: int, *, now_local: datetime | None = None) -> tuple[str, str]:
        now_local = now_local or datetime.utcnow() + timedelta(hours=8)
        end_date = now_local.date() - timedelta(days=1)
        start_date = end_date - timedelta(days=max(days, 1) - 1)
        return start_date.isoformat(), end_date.isoformat()

    # ─── docs/34 第一波：歸因模式揭露（唯讀查詢 + 24 小時快取） ─────────
    @staticmethod
    def _get_attribution_model(db, *, user: User, property_id: str) -> str:
        """回傳正規化後的歸因模式（"data_driven" / "last_click" / "unknown"）。

        查詢失敗或設定不在白名單內一律回退 "unknown"，不能讓這個輔助查詢
        影響渠道對照卡片本身的可用性（同模組既有容錯慣例）。
        """
        snapshot = repository.get_latest_snapshot(
            db, property_id=property_id, kind=ATTRIBUTION_SETTINGS_KIND, date=ATTRIBUTION_SETTINGS_DATE,
        )
        if snapshot and (datetime.utcnow() - snapshot.fetched_at) < timedelta(hours=ATTRIBUTION_SETTINGS_CACHE_HOURS):
            return snapshot.payload.get("attribution_model", "unknown")

        try:
            raw_model, error = GA4Client.get_attribution_settings(user, property_id, db)
            if error:
                raise RuntimeError(error)
            model = ATTRIBUTION_MODEL_MAP.get(raw_model, "unknown")
        except Exception as exc:
            logger.warning("[GA4Insights] get_attribution_settings failed for %s: %s", property_id, exc)
            # 查詢失敗時寧可回傳上一次快取到的值，也不要直接判 unknown（設定極少變動）。
            return snapshot.payload.get("attribution_model", "unknown") if snapshot else "unknown"

        repository.upsert_snapshot(
            db, property_id=property_id, kind=ATTRIBUTION_SETTINGS_KIND, date=ATTRIBUTION_SETTINGS_DATE,
            payload={"attribution_model": model, "raw_model": raw_model}, fetched_by=user.id,
        )
        return model

    # ─── 第 2/4 波：渠道主攻/助攻對照（3.3 節；第 4 波加維度切換） ─────
    @staticmethod
    def get_channels(
        db, *, user: User, property_id: str, days: int = 7,
        dimension: str = CHANNEL_DEFAULT_DIMENSION,
    ):
        if dimension not in CHANNEL_DIMENSION_MAP:
            raise ValueError(f"Unsupported channel dimension: {dimension}")
        session_dim, first_user_dim = CHANNEL_DIMENSION_MAP[dimension]
        start_date, end_date = GA4InsightsService._trailing_period(days)

        session_data, error = GA4Service.get_analytics(
            user=user, property_id=property_id, start_date=start_date, end_date=end_date,
            metrics=[CHANNEL_METRIC], dimensions=[session_dim], db=db,
        )
        if error:
            raise RuntimeError(error)
        first_user_data, error = GA4Service.get_analytics(
            user=user, property_id=property_id, start_date=start_date, end_date=end_date,
            metrics=[CHANNEL_METRIC], dimensions=[first_user_dim], db=db,
        )
        if error:
            raise RuntimeError(error)

        session_by_channel = {
            row[session_dim]: row.get(CHANNEL_METRIC, 0)
            for row in (session_data or {}).get("rows", [])
        }
        first_user_by_channel = {
            row[first_user_dim]: row.get(CHANNEL_METRIC, 0)
            for row in (first_user_data or {}).get("rows", [])
        }

        channels = sorted(set(session_by_channel) | set(first_user_by_channel))
        rows = []
        for channel in channels:
            closing = session_by_channel.get(channel, 0)
            assisting = first_user_by_channel.get(channel, 0)
            if closing > 0 and (closing + assisting) >= CHANNEL_MIN_SAMPLE:
                ratio = assisting / closing
                if ratio > 1.3:
                    tag = "assist"
                elif ratio < 0.7:
                    tag = "close"
                else:
                    tag = "balanced"
            else:
                ratio = assisting / closing if closing > 0 else None
                tag = "insufficient_data"
            rows.append({
                "channel": channel,
                "closing_conversions": closing,
                "assisting_conversions": assisting,
                "ratio": ratio,
                "tag": tag,
            })

        # 高基數保護：來源/媒介/廣告活動的列數可能遠多於管道群組，依（收單＋
        # 開發）轉換數排序只留前 20 列，payload 註記截斷與原始總列數。
        total_row_count = len(rows)
        truncated = total_row_count > CHANNEL_TOP_N
        if truncated:
            rows = sorted(
                rows, key=lambda r: r["closing_conversions"] + r["assisting_conversions"], reverse=True
            )[:CHANNEL_TOP_N]

        # kind 命名：預設維度沿用既有 "daily_channel"（向後相容既有快照與 AI
        # 解讀）；其餘維度加後綴各自獨立存放，互不覆寫
        # （"daily_channel:source_medium" 27 字元 < String(30) 上限）。
        kind = "daily_channel" if dimension == CHANNEL_DEFAULT_DIMENSION else f"daily_channel:{dimension}"

        payload = {
            "start_date": start_date,
            "end_date": end_date,
            "days": days,
            "dimension": dimension,
            "channels": rows,
            "truncated": truncated,
            "total_row_count": total_row_count,
            "attribution_model": GA4InsightsService._get_attribution_model(db, user=user, property_id=property_id),
        }
        return repository.upsert_snapshot(
            db, property_id=property_id, kind=kind, date=end_date, payload=payload, fetched_by=user.id,
        )

    # ─── 第 2/5 波：到達頁分析（3.4 節；第 5 波加分類篩選＋關鍵事件口徑） ──
    @staticmethod
    def get_landing_pages(db, *, user: User, property_id: str, days: int = 7, key_event: str | None = None):
        if key_event and not LANDING_PAGE_KEY_EVENT_PATTERN.match(key_event):
            raise ValueError(f"Invalid key_event: {key_event}")

        start_date, end_date = GA4InsightsService._trailing_period(days)

        # 2026-07-10 與使用者確認：主查詢的「轉換次數」「轉換率」改用 GA4
        # 官方 keyEvents / sessionKeyEventRate；帶 key_event 時改用該事件的
        # 動態指標（GA4 Data API 支援 "keyEvents:{event}" 這種冒號後綴語法）。
        key_events_metric = f"keyEvents:{key_event}" if key_event else "keyEvents"
        key_event_rate_metric = f"sessionKeyEventRate:{key_event}" if key_event else "sessionKeyEventRate"

        data, error = GA4Service.get_analytics(
            user=user, property_id=property_id, start_date=start_date, end_date=end_date,
            metrics=["sessions", "engagementRate", "bounceRate", key_events_metric, key_event_rate_metric],
            dimensions=["landingPage"], db=db,
        )
        if error:
            raise RuntimeError(error)
        rows = (data or {}).get("rows", [])

        # 關鍵事件分項統計：pivot landingPage × eventName，供前端下拉與明細
        # （查詢失敗不影響主表格，只是分項/下拉暫缺，同模組既有的容錯慣例）。
        key_events_breakdown: dict[str, dict[str, int]] = {}
        available_key_events: set[str] = set()
        breakdown_data, breakdown_error = GA4Service.get_analytics(
            user=user, property_id=property_id, start_date=start_date, end_date=end_date,
            metrics=["keyEvents"], dimensions=["landingPage", "eventName"], db=db,
        )
        if not breakdown_error:
            for row in (breakdown_data or {}).get("rows", []):
                page = row.get("landingPage", "")
                event_name = row.get("eventName", "")
                count = row.get("keyEvents", 0)
                if not event_name or not count:
                    continue
                key_events_breakdown.setdefault(page, {})[event_name] = count
                available_key_events.add(event_name)
        else:
            logger.warning("[GA4Insights] landing page key-events breakdown failed %s: %s", property_id, breakdown_error)

        rule_rows = repository.list_landing_page_rules(db, property_id=property_id)
        rules = [
            {"category": r.category, "match_type": r.match_type, "pattern": r.pattern, "priority": r.priority}
            for r in rule_rows
        ]

        enriched = []
        for row in rows:
            landing_page = row.get("landingPage", "")
            sessions = row.get("sessions", 0)
            key_events_count = row.get(key_events_metric, 0)
            session_key_event_rate = row.get(key_event_rate_metric, 0.0)
            category = classify_landing_page(landing_page, rules)
            enriched.append({
                "landingPage": landing_page,
                "sessions": sessions,
                "engagementRate": row.get("engagementRate", 0.0),
                "bounceRate": row.get("bounceRate", 0.0),
                "conversions": key_events_count,
                # 舊「次數比」口徑保留供回溯相容；前端不再以此欄顯示「轉換率」，
                # 主顯示改用下面的 session_key_event_rate（去重占比，見 5 節）。
                "conversion_rate": (key_events_count / sessions) if sessions else 0.0,
                "session_key_event_rate": session_key_event_rate,
                "category": category,
                "key_events_breakdown": key_events_breakdown.get(landing_page, {}),
                "is_high_traffic_low_conversion": False,
            })

        # 「高流量低轉換」改在同分類內計算（第 5 波刻意的語意變更），且改依
        # session_key_event_rate（去重占比）判定，不再用次數比。文章頁天生
        # 低轉換是常態，混排會讓商品頁的問題頁被稀釋而漏標、文章頁整批被誤
        # 標。四分位需要足夠樣本數，同既有規則：該分類樣本 <4 不標記。
        by_category: dict[str, list[dict]] = {}
        for row in enriched:
            by_category.setdefault(row["category"], []).append(row)
        for category_rows in by_category.values():
            if len(category_rows) >= 4:
                session_p75 = _percentile(sorted(r["sessions"] for r in category_rows), 0.75)
                rate_p25 = _percentile(sorted(r["session_key_event_rate"] for r in category_rows), 0.25)
                for row in category_rows:
                    row["is_high_traffic_low_conversion"] = (
                        row["sessions"] >= session_p75 and row["session_key_event_rate"] <= rate_p25
                    )

        category_counts = {category: len(category_rows) for category, category_rows in by_category.items()}

        # snapshot kind：全部事件維持 "landing_page"；指定事件加後綴各自獨立
        # 存放、AI 解讀互不覆寫（同第 4 波渠道維度切換前例）。
        kind = "landing_page" if not key_event else f"landing_page:{key_event}"

        payload = {
            "start_date": start_date,
            "end_date": end_date,
            "days": days,
            "key_event": key_event,
            "landing_pages": enriched,
            "category_counts": category_counts,
            "available_key_events": sorted(available_key_events),
            "session_key_event_rate_definition": LANDING_PAGE_SESSION_KEY_EVENT_RATE_DEFINITION,
            "key_events_count_definition": LANDING_PAGE_KEY_EVENTS_COUNT_DEFINITION,
        }
        return repository.upsert_snapshot(
            db, property_id=property_id, kind=kind, date=end_date, payload=payload, fetched_by=user.id,
        )

    # ─── 第 5 波：到達頁分類規則 CRUD ──────────────────────────────────
    @staticmethod
    def list_landing_page_rules(db, *, property_id: str):
        return repository.list_landing_page_rules(db, property_id=property_id)

    @staticmethod
    def upsert_landing_page_rule(
        db, *, rule_id: str | None, user_id: str, property_id: str,
        category: str, match_type: str, pattern: str, priority: int,
    ):
        if rule_id:
            row = repository.get_landing_page_rule(db, rule_id)
            if not row:
                return None
            row.property_id = property_id
            row.category = category
            row.match_type = match_type
            row.pattern = pattern
            row.priority = priority
            row.updated_at = datetime.utcnow()
            db.add(row)
            return row
        return repository.create_landing_page_rule(
            db,
            property_id=property_id,
            category=category,
            match_type=match_type,
            pattern=pattern,
            priority=priority,
            created_by=user_id,
        )

    @staticmethod
    def delete_landing_page_rule(db, *, rule_id: str) -> bool:
        return repository.delete_landing_page_rule(db, rule_id)

    # ─── 第 2/6 波：商品分析（3.4 節；第 6 波加分類篩選＋官方口徑） ────
    @staticmethod
    def get_items(db, *, user: User, property_id: str, days: int = 7):
        start_date, end_date = GA4InsightsService._trailing_period(days)

        data, error = GA4Service.get_analytics(
            user=user, property_id=property_id, start_date=start_date, end_date=end_date,
            metrics=ITEM_METRICS_WITH_OFFICIAL_RATES, dimensions=["itemName"], db=db,
        )
        used_fallback_conversion_metrics = False
        if error:
            logger.warning(
                "[GA4Insights] items official rate metrics failed %s: %s; falling back to local ratios",
                property_id, error,
            )
            data, error = GA4Service.get_analytics(
                user=user, property_id=property_id, start_date=start_date, end_date=end_date,
                metrics=ITEM_METRICS_FALLBACK, dimensions=["itemName"], db=db,
            )
            if error:
                raise RuntimeError(error)
            used_fallback_conversion_metrics = True
        rows = (data or {}).get("rows", [])

        # 瀏覽成長比較固定用「近 7 天 vs 前 7 天」（3.4 節），與 days 參數（表格期間）無關
        recent_start, recent_end = GA4InsightsService._trailing_period(7)
        prior_end = (datetime.strptime(recent_start, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        prior_start = (datetime.strptime(recent_start, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")

        recent_data, _ = GA4Service.get_analytics(
            user=user, property_id=property_id, start_date=recent_start, end_date=recent_end,
            metrics=["itemsViewed"], dimensions=["itemName"], db=db,
        )
        prior_data, _ = GA4Service.get_analytics(
            user=user, property_id=property_id, start_date=prior_start, end_date=prior_end,
            metrics=["itemsViewed"], dimensions=["itemName"], db=db,
        )
        recent_views = {row["itemName"]: row.get("itemsViewed", 0) for row in (recent_data or {}).get("rows", [])}
        prior_views = {row["itemName"]: row.get("itemsViewed", 0) for row in (prior_data or {}).get("rows", [])}

        # 商品主要分類：itemName × itemCategory，同商品多分類時取瀏覽量最高者
        # （查詢失敗只記警告、不中斷主表格，同第 5 波分項查詢容錯慣例）。
        # `category_breakdown_error` 進 payload：讓前端能分辨「查詢真的失敗」
        # 跟「GA4 本來就沒有 item_category 資料（網站未回傳）」，否則兩種情況
        # 在畫面上都是一片「未分類」，使用者無從判斷是系統問題還是自家網站
        # 的 GA4/GTM 電子商務事件沒有設定商品分類。
        category_by_item: dict[str, str] = {}
        best_views_by_item: dict[str, int] = {}
        breakdown_data, breakdown_error = GA4Service.get_analytics(
            user=user, property_id=property_id, start_date=start_date, end_date=end_date,
            metrics=["itemsViewed"], dimensions=["itemName", "itemCategory"], db=db,
        )
        if not breakdown_error:
            for row in (breakdown_data or {}).get("rows", []):
                item_name = row.get("itemName", "")
                item_category = row.get("itemCategory") or "(not set)"
                views = row.get("itemsViewed", 0)
                if item_name not in best_views_by_item or views > best_views_by_item[item_name]:
                    best_views_by_item[item_name] = views
                    category_by_item[item_name] = item_category
        else:
            logger.warning("[GA4Insights] items category breakdown failed %s: %s", property_id, breakdown_error)

        # 第 7 波：GA4 的 itemCategory 是權威來源，只在 GA4 回報 "(not set)"
        # 時才用自訂規則補分類（見 classify_item_category 的優先順序說明）。
        item_category_rule_rows = repository.list_item_category_rules(db, property_id=property_id)
        item_category_rules = [
            {"category": r.category, "match_type": r.match_type, "pattern": r.pattern, "priority": r.priority}
            for r in item_category_rule_rows
        ]

        enriched = []
        for row in rows:
            item_name = row.get("itemName")
            views = row.get("itemsViewed", 0)
            add_to_cart = row.get("itemsAddedToCart", 0)
            purchased = row.get("itemsPurchased", 0)
            # 舊件數比（同一使用者重複瀏覽/加購會重複計）保留供回溯，前端不再顯示為主要欄位。
            add_to_cart_rate = (add_to_cart / views) if views else 0.0
            if used_fallback_conversion_metrics:
                cart_to_view_rate = add_to_cart_rate
                purchase_to_view_rate = (purchased / views) if views else 0.0
            else:
                cart_to_view_rate = row.get("cartToViewRate", 0.0)
                purchase_to_view_rate = row.get("purchaseToViewRate", 0.0)
            recent = recent_views.get(item_name, 0)
            prior = prior_views.get(item_name, 0)
            growth_rate = ((recent - prior) / prior) if prior else (1.0 if recent > 0 else 0.0)
            item_category, item_category_source = classify_item_category(
                item_name, category_by_item.get(item_name), item_category_rules
            )
            enriched.append({
                **row,
                "add_to_cart_rate": add_to_cart_rate,
                "cart_to_view_rate": cart_to_view_rate,
                "purchase_to_view_rate": purchase_to_view_rate,
                "views_growth_rate": growth_rate,
                "views_recent_7d": recent,
                "views_prior_7d": prior,
                "item_category": item_category,
                "item_category_source": item_category_source,
                "is_potential": False,
            })

        category_counts: dict[str, int] = {}
        for row in enriched:
            category_counts[row["item_category"]] = category_counts.get(row["item_category"], 0) + 1

        # 潛力標記維持「全店相對」，用全體中位數（刻意決策，與第 5 波到達頁
        # 的同分類判定不同：itemCategory 高基數下單分類樣本常 <4，且潛力語意
        # 本就是跨分類比較「誰在全店裡值得加碼」，不強求跟到達頁一致）。
        if len(enriched) >= 4:
            growth_median = median(r["views_growth_rate"] for r in enriched)
            cart_rate_median = median(r["cart_to_view_rate"] for r in enriched)
            views_median = median(r["itemsViewed"] for r in enriched)
            for row in enriched:
                row["is_potential"] = (
                    row["views_growth_rate"] > growth_median
                    and row["cart_to_view_rate"] > cart_rate_median
                    and row["itemsViewed"] < views_median
                )

        payload = {
            "start_date": start_date,
            "end_date": end_date,
            "days": days,
            "items": enriched,
            "category_counts": category_counts,
            "used_fallback_conversion_metrics": used_fallback_conversion_metrics,
            "category_breakdown_error": breakdown_error,
            "cart_to_view_rate_definition": ITEM_CART_TO_VIEW_RATE_DEFINITION,
            "purchase_to_view_rate_definition": ITEM_PURCHASE_TO_VIEW_RATE_DEFINITION,
        }
        return repository.upsert_snapshot(
            db, property_id=property_id, kind="item", date=end_date, payload=payload, fetched_by=user.id,
        )

    # ─── 第 7 波：商品分類補充規則 CRUD ────────────────────────────────
    @staticmethod
    def list_item_category_rules(db, *, property_id: str):
        return repository.list_item_category_rules(db, property_id=property_id)

    @staticmethod
    def upsert_item_category_rule(
        db, *, rule_id: str | None, user_id: str, property_id: str,
        category: str, match_type: str, pattern: str, priority: int,
    ):
        if rule_id:
            row = repository.get_item_category_rule(db, rule_id)
            if not row:
                return None
            row.property_id = property_id
            row.category = category
            row.match_type = match_type
            row.pattern = pattern
            row.priority = priority
            row.updated_at = datetime.utcnow()
            db.add(row)
            return row
        return repository.create_item_category_rule(
            db,
            property_id=property_id,
            category=category,
            match_type=match_type,
            pattern=pattern,
            priority=priority,
            created_by=user_id,
        )

    @staticmethod
    def delete_item_category_rule(db, *, rule_id: str) -> bool:
        return repository.delete_item_category_rule(db, rule_id)

    # ─── 第 2 波任務 2.4：AI 白話解讀持久化 ───────────────────────────
    @staticmethod
    def save_ai_summary(db, *, snapshot_id: str, ai_summary: str):
        return repository.update_ai_summary(db, snapshot_id=snapshot_id, ai_summary=ai_summary)

    # ─── 第 3 波：KPI 目標追蹤（選配，docs/22 5 節） ───────────────────
    @staticmethod
    def _kpi_period_bounds(period_type: str, period_key: str) -> tuple[date, date]:
        """把 `period_type`/`period_key` 轉成該期間的起訖日（含頭尾）。"""
        if period_type == "month":
            year_str, month_str = period_key.split("-")
            year, month = int(year_str), int(month_str)
            start = date(year, month, 1)
            end = date(year, month + 1, 1) - timedelta(days=1) if month < 12 else date(year, 12, 31)
            return start, end
        if period_type == "quarter":
            year_str, quarter_str = period_key.split("-Q")
            year, quarter = int(year_str), int(quarter_str)
            start_month = (quarter - 1) * 3 + 1
            start = date(year, start_month, 1)
            end_month = start_month + 2
            end = date(year, end_month + 1, 1) - timedelta(days=1) if end_month < 12 else date(year, 12, 31)
            return start, end
        raise ValueError(f"Unsupported period_type: {period_type}")

    @staticmethod
    def compute_kpi_pacing(
        *, target_value: float, period_type: str, period_key: str,
        actual_value: float, today: date | None = None,
    ) -> dict:
        """
        純函數：算「達成率 vs 時間進度」的 pacing 結果。

        - `time_progress`：期間已過去的天數比例（今天算在內），超出期間範圍會 clamp 到 [0, 1]。
        - `achievement_rate`：目前累計值 / 目標值。
        - `status`：`achievement_rate` 相對 `time_progress` 領先/落後超過
          `KPI_PACING_BUFFER`（5 個百分點）才判定 ahead/behind，否則 on_track；
          `target_value <= 0` 時無法計算比率，回傳 `no_target`。
        - `projected_final_value`：以目前這個速度線性外推到期末的預估值
          （`actual_value / time_progress`），僅供參考、非精確預測。
        """
        today = today or (datetime.utcnow() + timedelta(hours=8)).date()
        start, end = GA4InsightsService._kpi_period_bounds(period_type, period_key)
        period_length = (end - start).days + 1
        elapsed_days = max(0, min((today - start).days + 1, period_length))
        time_progress = elapsed_days / period_length if period_length else 0.0

        if not target_value or target_value <= 0:
            achievement_rate = None
            status = "no_target"
        else:
            achievement_rate = actual_value / target_value
            if achievement_rate >= time_progress + KPI_PACING_BUFFER:
                status = "ahead"
            elif achievement_rate <= time_progress - KPI_PACING_BUFFER:
                status = "behind"
            else:
                status = "on_track"

        projected_final_value = (actual_value / time_progress) if time_progress > 0 else None

        return {
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
            "time_progress": time_progress,
            "actual_value": actual_value,
            "achievement_rate": achievement_rate,
            "projected_final_value": projected_final_value,
            "status": status,
        }

    @staticmethod
    def get_kpi_targets_with_pacing(db, *, user: User, property_id: str) -> list[dict]:
        today = (datetime.utcnow() + timedelta(hours=8)).date()
        targets = repository.list_kpi_targets(db, property_id=property_id)
        results = []
        for target in targets:
            api_metric = SUPPORTED_METRICS.get(target.metric_key, target.metric_key)
            start, end = GA4InsightsService._kpi_period_bounds(target.period_type, target.period_key)
            query_end = min(end, today)

            actual_value = 0.0
            data_unavailable = False
            if query_end >= start:
                data, error = GA4Service.get_analytics(
                    user=user, property_id=property_id,
                    start_date=start.isoformat(), end_date=query_end.isoformat(),
                    metrics=[api_metric], dimensions=[], db=db,
                )
                if error:
                    logger.warning(
                        "[GA4Insights] KPI actual value fetch failed %s %s: %s",
                        property_id, target.metric_key, error,
                    )
                    data_unavailable = True
                elif data and data.get("rows"):
                    actual_value = float(data["rows"][0].get(api_metric, 0))

            pacing = GA4InsightsService.compute_kpi_pacing(
                target_value=target.target_value,
                period_type=target.period_type,
                period_key=target.period_key,
                actual_value=actual_value,
                today=today,
            )
            if data_unavailable:
                pacing["status"] = "data_unavailable"

            results.append({
                "id": target.id,
                "property_id": target.property_id,
                "metric_key": target.metric_key,
                "period_type": target.period_type,
                "period_key": target.period_key,
                "target_value": target.target_value,
                **pacing,
            })
        return results

    @staticmethod
    def upsert_kpi_target(
        db, *, user_id: str, property_id: str, metric_key: str,
        period_type: str, period_key: str, target_value: float,
    ):
        return repository.upsert_kpi_target(
            db,
            property_id=property_id,
            metric_key=metric_key,
            period_type=period_type,
            period_key=period_key,
            target_value=target_value,
            created_by=user_id,
        )

    @staticmethod
    def delete_kpi_target(db, *, target_id: str) -> bool:
        return repository.delete_kpi_target(db, target_id)
