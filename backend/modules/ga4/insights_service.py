"""GA4 insights wave-1 service helpers."""

from __future__ import annotations

import asyncio
import logging
import os
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

# 第 3 波：KPI 目標追蹤（docs/22 5 節，選配）
KPI_PERIOD_TYPES = {"month", "quarter"}
# 進度領先/落後的緩衝帶：達成率相對「時間進度」超出 ±5 個百分點才判定 ahead/behind，
# 避免時間進度剛好卡在整數邊界時，一點點雜訊就在 on_track/ahead 之間來回跳動。
KPI_PACING_BUFFER = 0.05


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

    # ─── 第 2 波：渠道主攻/助攻對照（3.3 節） ──────────────────────────
    @staticmethod
    def get_channels(db, *, user: User, property_id: str, days: int = 7):
        start_date, end_date = GA4InsightsService._trailing_period(days)

        session_data, error = GA4Service.get_analytics(
            user=user, property_id=property_id, start_date=start_date, end_date=end_date,
            metrics=[CHANNEL_METRIC], dimensions=["sessionDefaultChannelGroup"], db=db,
        )
        if error:
            raise RuntimeError(error)
        first_user_data, error = GA4Service.get_analytics(
            user=user, property_id=property_id, start_date=start_date, end_date=end_date,
            metrics=[CHANNEL_METRIC], dimensions=["firstUserDefaultChannelGroup"], db=db,
        )
        if error:
            raise RuntimeError(error)

        session_by_channel = {
            row["sessionDefaultChannelGroup"]: row.get(CHANNEL_METRIC, 0)
            for row in (session_data or {}).get("rows", [])
        }
        first_user_by_channel = {
            row["firstUserDefaultChannelGroup"]: row.get(CHANNEL_METRIC, 0)
            for row in (first_user_data or {}).get("rows", [])
        }

        channels = sorted(set(session_by_channel) | set(first_user_by_channel))
        rows = []
        for channel in channels:
            closing = session_by_channel.get(channel, 0)
            assisting = first_user_by_channel.get(channel, 0)
            if closing > 0:
                ratio = assisting / closing
                if ratio > 1.3:
                    tag = "assist"
                elif ratio < 0.7:
                    tag = "close"
                else:
                    tag = "balanced"
            else:
                ratio = None
                tag = "insufficient_data"
            rows.append({
                "channel": channel,
                "closing_conversions": closing,
                "assisting_conversions": assisting,
                "ratio": ratio,
                "tag": tag,
            })

        payload = {"start_date": start_date, "end_date": end_date, "days": days, "channels": rows}
        return repository.upsert_snapshot(
            db, property_id=property_id, kind="daily_channel", date=end_date, payload=payload, fetched_by=user.id,
        )

    # ─── 第 2 波：到達頁分析（3.4 節） ─────────────────────────────────
    @staticmethod
    def get_landing_pages(db, *, user: User, property_id: str, days: int = 7):
        start_date, end_date = GA4InsightsService._trailing_period(days)
        data, error = GA4Service.get_analytics(
            user=user, property_id=property_id, start_date=start_date, end_date=end_date,
            metrics=["sessions", "engagementRate", "conversions", "bounceRate"],
            dimensions=["landingPage"], db=db,
        )
        if error:
            raise RuntimeError(error)
        rows = (data or {}).get("rows", [])

        enriched = []
        for row in rows:
            sessions = row.get("sessions", 0)
            conversions = row.get("conversions", 0)
            conversion_rate = (conversions / sessions) if sessions else 0.0
            enriched.append({**row, "conversion_rate": conversion_rate, "is_high_traffic_low_conversion": False})

        # 「高流量低轉換」需要足夠樣本數才能算四分位，樣本太少（<4）標記全部維持 False
        if len(enriched) >= 4:
            session_p75 = _percentile(sorted(r["sessions"] for r in enriched), 0.75)
            conv_rate_p25 = _percentile(sorted(r["conversion_rate"] for r in enriched), 0.25)
            for row in enriched:
                row["is_high_traffic_low_conversion"] = (
                    row["sessions"] >= session_p75 and row["conversion_rate"] <= conv_rate_p25
                )

        payload = {"start_date": start_date, "end_date": end_date, "days": days, "landing_pages": enriched}
        return repository.upsert_snapshot(
            db, property_id=property_id, kind="landing_page", date=end_date, payload=payload, fetched_by=user.id,
        )

    # ─── 第 2 波：商品分析（3.4 節） ───────────────────────────────────
    @staticmethod
    def get_items(db, *, user: User, property_id: str, days: int = 7):
        start_date, end_date = GA4InsightsService._trailing_period(days)
        data, error = GA4Service.get_analytics(
            user=user, property_id=property_id, start_date=start_date, end_date=end_date,
            metrics=["itemsViewed", "itemsAddedToCart", "itemsPurchased", "itemRevenue"],
            dimensions=["itemName"], db=db,
        )
        if error:
            raise RuntimeError(error)
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

        enriched = []
        for row in rows:
            item_name = row.get("itemName")
            views = row.get("itemsViewed", 0)
            add_to_cart = row.get("itemsAddedToCart", 0)
            add_to_cart_rate = (add_to_cart / views) if views else 0.0
            recent = recent_views.get(item_name, 0)
            prior = prior_views.get(item_name, 0)
            growth_rate = ((recent - prior) / prior) if prior else (1.0 if recent > 0 else 0.0)
            enriched.append({
                **row,
                "add_to_cart_rate": add_to_cart_rate,
                "views_growth_rate": growth_rate,
                "is_potential": False,
            })

        if len(enriched) >= 4:
            growth_median = median(r["views_growth_rate"] for r in enriched)
            cart_rate_median = median(r["add_to_cart_rate"] for r in enriched)
            views_median = median(r["itemsViewed"] for r in enriched)
            for row in enriched:
                row["is_potential"] = (
                    row["views_growth_rate"] > growth_median
                    and row["add_to_cart_rate"] > cart_rate_median
                    and row["itemsViewed"] < views_median
                )

        payload = {"start_date": start_date, "end_date": end_date, "days": days, "items": enriched}
        return repository.upsert_snapshot(
            db, property_id=property_id, kind="item", date=end_date, payload=payload, fetched_by=user.id,
        )

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
