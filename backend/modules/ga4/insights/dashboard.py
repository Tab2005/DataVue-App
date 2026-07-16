"""Dashboard helpers for GA4 insights."""

from __future__ import annotations

from ._shared import *


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
        for sample_date in _service_attr("_historical_dates", _historical_dates)(now_local):
            try:
                sample_total, _ = _service_attr("_fetch_metric_total", _fetch_metric_total)(
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
