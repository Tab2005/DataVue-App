from modules.ga4.dependencies import (
    require_ga4_insights_manage_alerts,
    require_ga4_insights_view,
    require_ga4_module,
)
from modules.ga4.insights_router import get_current_user


def _override_dependencies(app, user, db):
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_ga4_module] = lambda: True
    app.dependency_overrides[require_ga4_insights_view] = lambda: True
    app.dependency_overrides[require_ga4_insights_manage_alerts] = lambda: True


def test_ga4_anomaly_rule_crud_and_ack_flow(client, db, sample_user):
    _override_dependencies(client.app, sample_user, db)

    created = client.post(
        "/api/ga4/insights/anomaly-rules",
        json={
            "property_id": "123456",
            "metric_key": "conversions",
            "sensitivity": "high",
            "check_frequency": "hourly",
            "is_enabled": True,
            "notify_line": True,
            "notify_email": False,
            "cooldown_hours": 6,
        },
    )
    assert created.status_code == 201
    rule_id = created.json()["id"]

    listed = client.get("/api/ga4/insights/anomaly-rules")
    assert listed.status_code == 200
    assert listed.json()["rules"][0]["id"] == rule_id

    from database.models.ga4_insights import GA4AnomalyEvent

    event = GA4AnomalyEvent(
        rule_id=rule_id,
        severity="warning",
        direction="drop",
        observed_value=10,
        expected_low=50,
        expected_high=80,
        message="test alert",
        notified_channels={"line": True},
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    events = client.get("/api/ga4/insights/anomaly-events")
    assert events.status_code == 200
    assert events.json()["total"] == 1
    assert events.json()["unacknowledged_total"] == 1

    acked = client.patch(
        f"/api/ga4/insights/anomaly-events/{event.id}/ack",
        json={"acknowledged": True},
    )
    assert acked.status_code == 200
    assert acked.json()["acknowledged_by"] == sample_user.id

    events_after_ack = client.get("/api/ga4/insights/anomaly-events")
    assert events_after_ack.json()["total"] == 1
    assert events_after_ack.json()["unacknowledged_total"] == 0

    updated = client.put(
        f"/api/ga4/insights/anomaly-rules/{rule_id}",
        json={
            "property_id": "123456",
            "metric_key": "sessions",
            "sensitivity": "low",
            "check_frequency": "daily",
            "is_enabled": False,
            "notify_line": False,
            "notify_email": True,
            "cooldown_hours": 12,
        },
    )
    assert updated.status_code == 200
    assert updated.json()["metric_key"] == "sessions"
    assert updated.json()["check_frequency"] == "daily"

    deleted = client.delete(f"/api/ga4/insights/anomaly-rules/{rule_id}")
    assert deleted.status_code == 200
    assert deleted.json()["status"] == "deleted"


# ─── docs/52：告警規則關鍵事件拆分 ───────────────────────────────────
def test_ga4_anomaly_rule_accepts_key_event_with_conversions_metric(client, db, sample_user):
    _override_dependencies(client.app, sample_user, db)

    created = client.post(
        "/api/ga4/insights/anomaly-rules",
        json={
            "property_id": "123456",
            "metric_key": "conversions",
            "key_event": "purchase",
            "sensitivity": "high",
            "check_frequency": "hourly",
        },
    )
    assert created.status_code == 201
    assert created.json()["key_event"] == "purchase"

    # 既有規則（本次以外的 CRUD 測試）沒帶 key_event 時序列化回 None。
    listed = client.get("/api/ga4/insights/anomaly-rules")
    assert listed.status_code == 200
    assert listed.json()["rules"][0]["key_event"] == "purchase"


def test_ga4_anomaly_rule_rejects_key_event_with_non_conversions_metric(client, db, sample_user):
    _override_dependencies(client.app, sample_user, db)

    rejected = client.post(
        "/api/ga4/insights/anomaly-rules",
        json={
            "property_id": "123456",
            "metric_key": "sessions",
            "key_event": "purchase",
        },
    )
    assert rejected.status_code == 422


def test_ga4_anomaly_rule_rejects_invalid_key_event_pattern(client, db, sample_user):
    _override_dependencies(client.app, sample_user, db)

    rejected = client.post(
        "/api/ga4/insights/anomaly-rules",
        json={
            "property_id": "123456",
            "metric_key": "conversions",
            "key_event": "not a valid event!",
        },
    )
    assert rejected.status_code == 422


def test_ga4_anomaly_rule_available_key_events_endpoint(client, db, sample_user, mocker):
    _override_dependencies(client.app, sample_user, db)

    mocker.patch(
        "modules.ga4.insights_router.GA4InsightsService.list_available_key_events",
        return_value=["add_to_cart", "purchase"],
    )
    ok = client.get("/api/ga4/insights/anomaly-rules/available-key-events", params={"property_id": "123456"})
    assert ok.status_code == 200
    assert ok.json()["events"] == ["add_to_cart", "purchase"]

    mocker.patch(
        "modules.ga4.insights_router.GA4InsightsService.list_available_key_events",
        side_effect=RuntimeError("GA4 quota exceeded"),
    )
    failed = client.get("/api/ga4/insights/anomaly-rules/available-key-events", params={"property_id": "123456"})
    assert failed.status_code == 400


def test_ga4_anomaly_events_unacknowledged_total_is_independent_of_pagination(client, db, sample_user):
    _override_dependencies(client.app, sample_user, db)

    from database.models.ga4_insights import GA4AnomalyEvent, GA4AnomalyRule

    rule = GA4AnomalyRule(
        property_id="123456",
        metric_key="conversions",
        sensitivity="medium",
        check_frequency="hourly",
        created_by=sample_user.id,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    # 建立 3 則事件，其中 1 則先標記已讀，驗證 unacknowledged_total 不受分頁影響。
    for i in range(3):
        event = GA4AnomalyEvent(
            rule_id=rule.id,
            severity="warning",
            direction="drop",
            observed_value=10 + i,
            expected_low=50,
            expected_high=80,
            message=f"test alert {i}",
            notified_channels={},
        )
        db.add(event)
    db.commit()

    first_event = db.query(GA4AnomalyEvent).order_by(GA4AnomalyEvent.created_at.asc()).first()
    client.patch(f"/api/ga4/insights/anomaly-events/{first_event.id}/ack", json={"acknowledged": True})

    page1 = client.get("/api/ga4/insights/anomaly-events?page=1&page_size=2")
    assert page1.status_code == 200
    body1 = page1.json()
    assert len(body1["events"]) == 2
    assert body1["total"] == 3
    assert body1["unacknowledged_total"] == 2

    page2 = client.get("/api/ga4/insights/anomaly-events?page=2&page_size=2")
    body2 = page2.json()
    assert len(body2["events"]) == 1
    assert body2["total"] == 3
    # 未讀總數在不同分頁之間應保持一致，不會因為切頁而變動。
    assert body2["unacknowledged_total"] == 2
