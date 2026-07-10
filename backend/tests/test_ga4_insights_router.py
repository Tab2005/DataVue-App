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

    acked = client.patch(
        f"/api/ga4/insights/anomaly-events/{event.id}/ack",
        json={"acknowledged": True},
    )
    assert acked.status_code == 200
    assert acked.json()["acknowledged_by"] == sample_user.id

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
