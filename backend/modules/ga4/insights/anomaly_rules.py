"""Anomaly rules helpers for GA4 insights."""

from __future__ import annotations

from ._shared import *


def list_rules(db, *, user_id: str, property_id: str | None = None):
    return repository.list_rules(db, created_by=user_id, property_id=property_id)


def create_rule(db, *, user_id: str, payload: dict):
    payload = {**payload, "created_by": user_id}
    return repository.create_rule(db, **payload)


def update_rule(db, *, rule_id: str, user_id: str, payload: dict):
    row = repository.get_rule(db, rule_id)
    if not row or row.created_by != user_id:
        return None
    for key, value in payload.items():
        setattr(row, key, value)
    row.updated_at = datetime.utcnow()
    db.add(row)
    return row


def delete_rule(db, *, rule_id: str, user_id: str):
    row = repository.get_rule(db, rule_id)
    if not row or row.created_by != user_id:
        return False
    return repository.delete_rule(db, rule_id)


def list_events(db, *, user_id: str, property_id: str | None = None, page: int = 1, page_size: int = 20):
    return repository.list_events(
        db,
        property_id=property_id,
        created_by=user_id,
        page=page,
        page_size=page_size,
    )


def acknowledge_event(db, *, event_id: str, user_id: str):
    row = repository.get_event(db, event_id)
    if not row or row.rule.creator.id != user_id:
        return None
    return repository.acknowledge_event(db, event_id=event_id, user_id=user_id)


def build_alert_message(*, property_label: str, metric_key: str, observed: float, expected_low: float, expected_high: float) -> str:
    metric_label = METRIC_LABELS.get(metric_key, metric_key)
    return (
        f"⚠️ GA4 異常（{property_label}）\n"
        f"{metric_label} 今日累計 {_service_attr('_format_metric_value', _format_metric_value)(metric_key, observed)}，"
        f"低於/高於預期區間 {_service_attr('_format_metric_value', _format_metric_value)(metric_key, expected_low)}"
        f"~{_service_attr('_format_metric_value', _format_metric_value)(metric_key, expected_high)}（過去 8 週同時段基線）\n"
        f"可能方向：檢查廣告投放是否中斷 / 網站追蹤碼 / 檔期效應\n"
        f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/ga4-insights"
    )


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
    observed, raw_rows = _service_attr("_fetch_metric_total", _fetch_metric_total)(
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
    for sample_date in _service_attr("_historical_dates", _historical_dates)(now_local):
        try:
            sample_total, _ = _service_attr("_fetch_metric_total", _fetch_metric_total)(
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

    message = _service_attr("build_alert_message", build_alert_message)(
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
        notified_channels["email"] = await _service_attr("_send_email_if_possible", _send_email_if_possible)(
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
