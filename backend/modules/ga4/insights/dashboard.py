"""Dashboard helpers for GA4 insights."""

from __future__ import annotations

from ._shared import *
from ._parallel import resolve_ga4_credentials, run_parallel

# docs/50：「轉換」卡片個別關鍵事件拆分，下拉選單最多列出（「全部關鍵事件」以外）
# 這麼多個依當日次數排序的個別事件，避免關鍵事件數量不可預期地把基線查詢量推高。
MAX_CONVERSION_EVENTS = 5


def _compute_metric_baseline(
    *, user: User, property_id: str, api_metric: str, now_local: datetime, current_hour: int, db, observed: float,
) -> tuple[dict | None, bool]:
    """依 8 週歷史同星期幾抓 `api_metric` 的基線區間，並判斷 `observed` 是否異常。

    docs/65：8 個取樣日彼此無關，並行抓。這裡是整個當日儀表板最大的循序鏈——
    一次刷新最多會算 8 組基線（全部關鍵事件＋最多 5 個個別事件＋2 個非轉換
    指標），每組 8 個取樣日，也就是最壞 64 次循序查詢。docs/59 的呼叫點統計
    看不到它，因為這些查詢藏在 `_fetch_metric_total` 底下。

    單一取樣失敗維持既有容錯——只跳過該筆、不影響其他取樣，所以例外在 task
    內就吃掉，不讓它中斷整組。
    """
    fetch_metric_total = _service_attr("_fetch_metric_total", _fetch_metric_total)
    sample_dates = _service_attr("_historical_dates", _historical_dates)(now_local)
    # 憑證在請求執行緒解析（該刷新的刷新、該回寫的回寫），worker thread 只拿結果。
    credentials = resolve_ga4_credentials(user, db)

    def _make_sample_task(sample_date: str):
        def _sample():
            try:
                sample_total, _ = fetch_metric_total(
                    user=user,
                    property_id=property_id,
                    date_value=sample_date,
                    api_metric=api_metric,
                    db=None,
                    credentials=credentials,
                    by_hour=True,
                    current_hour=current_hour,
                )
            except Exception:
                logger.warning("[GA4Insights] dashboard baseline sample failed %s %s", property_id, sample_date)
                return None
            return sample_total
        return _sample

    sampled = run_parallel({date: _make_sample_task(date) for date in sample_dates})
    # 依歷史日期順序收集，讓 samples 的內容不受完成先後影響。
    samples: list[float] = [sampled[date] for date in sample_dates if sampled[date] is not None]
    expected = build_expected_range(samples, "medium")
    is_anomaly = bool(expected and (observed < expected["low"] or observed > expected["high"]))
    return expected, is_anomaly


def _fetch_intraday_dashboard_payload(*, user: User, property_id: str, db, now_local: datetime | None = None) -> dict:
    now_local = now_local or datetime.utcnow() + timedelta(hours=8)
    today = now_local.date().isoformat()
    current_hour = now_local.hour

    # docs/65：主查詢與下面的事件拆解都是「當日 hour × 某維度」，彼此無資料
    # 相依，並行送出。credentials 在請求執行緒先解析好，worker thread 不碰 db。
    credentials = resolve_ga4_credentials(user, db)
    results = run_parallel({
        "main": lambda: GA4Service.get_analytics(
            user=user,
            property_id=property_id,
            start_date=today,
            end_date=today,
            metrics=DASHBOARD_METRICS,
            dimensions=["hour", "sessionDefaultChannelGroup"],
            credentials=credentials,
        ),
        "breakdown": lambda: GA4Service.get_analytics(
            user=user,
            property_id=property_id,
            start_date=today,
            end_date=today,
            metrics=["keyEvents"],
            dimensions=["hour", "eventName"],
            credentials=credentials,
        ),
    })

    data, error = results["main"]
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

    # docs/50 步驟 1：另開一支 hour × eventName 查詢，抓出當日實際出現的關鍵
    # 事件，依當日次數排序取前 N 大做「全部關鍵事件」以外的個別下拉選項。
    # 查詢失敗時只保留「全部關鍵事件」，不擋主要的 cumulative_totals/baseline 邏輯。
    event_hourly_totals: dict[str, dict[int, float]] = {}
    breakdown_data, breakdown_error = results["breakdown"]
    if breakdown_error:
        logger.warning("[GA4Insights] dashboard event breakdown failed %s: %s", property_id, breakdown_error)
    else:
        for row in (breakdown_data or {}).get("rows", []):
            event_name = row.get("eventName", "")
            if not event_name:
                continue
            hour_value = int(row.get("hour", 0))
            value = float(row.get("keyEvents", 0) or 0)
            bucket = event_hourly_totals.setdefault(event_name, {})
            bucket[hour_value] = bucket.get(hour_value, 0.0) + value

    event_cumulative = {
        event_name: sum(value for hour_value, value in hours.items() if hour_value <= current_hour)
        for event_name, hours in event_hourly_totals.items()
    }
    top_events = sorted(
        event_cumulative, key=lambda name: event_cumulative[name], reverse=True
    )[:MAX_CONVERSION_EVENTS]

    compute_baseline = _service_attr("_compute_metric_baseline", _compute_metric_baseline)

    conversion_events = [{"key": "__all__", "label": "全部關鍵事件"}]
    all_baseline, all_is_anomaly = compute_baseline(
        user=user, property_id=property_id, api_metric="keyEvents",
        now_local=now_local, current_hour=current_hour, db=db,
        observed=cumulative_totals["conversions"],
    )
    conversions_by_event: dict[str, dict] = {
        "__all__": {
            "cumulative_value": cumulative_totals["conversions"],
            "baseline": all_baseline,
            "is_anomaly": all_is_anomaly,
            "hourly_totals": [
                {"hour": entry["hour"], "value": entry.get("conversions", 0.0)} for entry in hourly_totals_list
            ],
        }
    }

    for event_name in top_events:
        conversion_events.append({"key": event_name, "label": event_name})
        observed = event_cumulative[event_name]
        event_baseline, event_is_anomaly = compute_baseline(
            user=user, property_id=property_id, api_metric=f"keyEvents:{event_name}",
            now_local=now_local, current_hour=current_hour, db=db,
            observed=observed,
        )
        conversions_by_event[event_name] = {
            "cumulative_value": observed,
            "baseline": event_baseline,
            "is_anomaly": event_is_anomaly,
            "hourly_totals": [
                {"hour": f"{hour_value:02d}", "value": value}
                for hour_value, value in sorted(event_hourly_totals[event_name].items())
            ],
        }

    baseline: dict[str, dict | None] = {}
    is_anomaly: dict[str, bool] = {}
    for metric in DASHBOARD_METRICS:
        if metric == "conversions":
            # 向下相容：既有欄位維持與 conversions_by_event["__all__"] 數字一致，
            # 改用 keyEvents 指標算基線（語意等同 conversions，但跟個別事件的
            # keyEvents:{event} 動態指標共用同一套查詢邏輯，避免重複打兩次 API）。
            baseline[metric] = conversions_by_event["__all__"]["baseline"]
            is_anomaly[metric] = conversions_by_event["__all__"]["is_anomaly"]
            continue
        observed = cumulative_totals[metric]
        expected, flagged = compute_baseline(
            user=user, property_id=property_id, api_metric=metric,
            now_local=now_local, current_hour=current_hour, db=db,
            observed=observed,
        )
        baseline[metric] = expected
        is_anomaly[metric] = flagged

    return {
        "date": today,
        "current_hour": current_hour,
        "channel_breakdown": rows,
        "hourly_totals": hourly_totals_list,
        "cumulative_totals": cumulative_totals,
        "baseline": baseline,
        "is_anomaly": is_anomaly,
        "conversion_events": conversion_events,
        "conversions_by_event": conversions_by_event,
    }


def _refresh_dashboard_snapshot(db, *, user: User, property_id: str):
    fetch_payload = _service_attr("_fetch_intraday_dashboard_payload", _fetch_intraday_dashboard_payload)
    payload = fetch_payload(user=user, property_id=property_id, db=db)
    return repository.upsert_snapshot(
        db,
        property_id=property_id,
        kind=DASHBOARD_KIND,
        date=payload["date"],
        payload=payload,
        fetched_by=user.id,
    )


def get_dashboard(db, *, user: User, property_id: str):
    """讀快取；首次造訪（job 尚未跑過）時同步抓一次做 bootstrap（3.2 節）。"""
    today = (datetime.utcnow() + timedelta(hours=8)).date().isoformat()
    snapshot = repository.get_latest_snapshot(db, property_id=property_id, kind=DASHBOARD_KIND, date=today)
    if not snapshot:
        snapshot = _service_attr("_refresh_dashboard_snapshot", _refresh_dashboard_snapshot)(db, user=user, property_id=property_id)
    return snapshot


def refresh_dashboard(db, *, user: User, property_id: str):
    """手動刷新，每 property 10 分鐘一次的 rate limit（3.2 節）。"""
    today = (datetime.utcnow() + timedelta(hours=8)).date().isoformat()
    existing = repository.get_latest_snapshot(db, property_id=property_id, kind=DASHBOARD_KIND, date=today)
    if existing:
        elapsed = datetime.utcnow() - existing.fetched_at
        if elapsed < timedelta(minutes=DASHBOARD_REFRESH_COOLDOWN_MINUTES):
            return existing, False
    snapshot = _service_attr("_refresh_dashboard_snapshot", _refresh_dashboard_snapshot)(db, user=user, property_id=property_id)
    return snapshot, True


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
