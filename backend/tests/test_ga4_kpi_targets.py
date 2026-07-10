"""
GA4 KPI 目標追蹤驗證（docs/22 第 3 波，選配）

涵蓋：
- `_kpi_period_bounds`：月/季期間起訖日換算（含年末邊界）
- `compute_kpi_pacing`：達成率 vs 時間進度的 ahead/on_track/behind 分級、
  no_target 退化情況、projected_final_value 線性外推
- `get_kpi_targets_with_pacing`：組裝 GA4 實際值 + pacing，GA4 查詢失敗時
  標記 data_unavailable 而非整批失敗
- repository 的 upsert（同 key 更新而非新增）/list/delete
- 新增端點的路由/驗證契約（GET/PUT/DELETE /kpi-targets）
"""
from datetime import date
from unittest.mock import MagicMock

import pytest

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


# ─── _kpi_period_bounds ─────────────────────────────────────────────
@pytest.mark.unit
def test_kpi_period_bounds_month():
    from modules.ga4.insights_service import GA4InsightsService

    start, end = GA4InsightsService._kpi_period_bounds("month", "2026-07")
    assert start == date(2026, 7, 1)
    assert end == date(2026, 7, 31)


@pytest.mark.unit
def test_kpi_period_bounds_month_december_edge():
    from modules.ga4.insights_service import GA4InsightsService

    start, end = GA4InsightsService._kpi_period_bounds("month", "2026-12")
    assert start == date(2026, 12, 1)
    assert end == date(2026, 12, 31)


@pytest.mark.unit
def test_kpi_period_bounds_quarter():
    from modules.ga4.insights_service import GA4InsightsService

    start, end = GA4InsightsService._kpi_period_bounds("quarter", "2026-Q3")
    assert start == date(2026, 7, 1)
    assert end == date(2026, 9, 30)


@pytest.mark.unit
def test_kpi_period_bounds_quarter_q4_edge():
    from modules.ga4.insights_service import GA4InsightsService

    start, end = GA4InsightsService._kpi_period_bounds("quarter", "2026-Q4")
    assert start == date(2026, 10, 1)
    assert end == date(2026, 12, 31)


# ─── compute_kpi_pacing ─────────────────────────────────────────────
@pytest.mark.unit
def test_compute_kpi_pacing_ahead():
    from modules.ga4.insights_service import GA4InsightsService

    result = GA4InsightsService.compute_kpi_pacing(
        target_value=100, period_type="month", period_key="2026-07",
        actual_value=60, today=date(2026, 7, 16),
    )
    # time_progress = 16/31 ≈ 0.516；achievement_rate 0.6 >= 0.516+0.05 → ahead
    assert result["status"] == "ahead"
    assert result["achievement_rate"] == pytest.approx(0.6)
    assert result["time_progress"] == pytest.approx(16 / 31)
    assert result["projected_final_value"] == pytest.approx(60 / (16 / 31))


@pytest.mark.unit
def test_compute_kpi_pacing_behind():
    from modules.ga4.insights_service import GA4InsightsService

    result = GA4InsightsService.compute_kpi_pacing(
        target_value=100, period_type="month", period_key="2026-07",
        actual_value=40, today=date(2026, 7, 16),
    )
    assert result["status"] == "behind"


@pytest.mark.unit
def test_compute_kpi_pacing_on_track():
    from modules.ga4.insights_service import GA4InsightsService

    result = GA4InsightsService.compute_kpi_pacing(
        target_value=100, period_type="month", period_key="2026-07",
        actual_value=52, today=date(2026, 7, 16),
    )
    assert result["status"] == "on_track"


@pytest.mark.unit
def test_compute_kpi_pacing_no_target_when_target_value_zero():
    from modules.ga4.insights_service import GA4InsightsService

    result = GA4InsightsService.compute_kpi_pacing(
        target_value=0, period_type="month", period_key="2026-07",
        actual_value=40, today=date(2026, 7, 16),
    )
    assert result["status"] == "no_target"
    assert result["achievement_rate"] is None


@pytest.mark.unit
def test_compute_kpi_pacing_clamps_time_progress_after_period_end():
    from modules.ga4.insights_service import GA4InsightsService

    result = GA4InsightsService.compute_kpi_pacing(
        target_value=100, period_type="month", period_key="2026-07",
        actual_value=90, today=date(2026, 9, 1),
    )
    assert result["time_progress"] == pytest.approx(1.0)


# ─── get_kpi_targets_with_pacing ────────────────────────────────────
@pytest.mark.unit
def test_get_kpi_targets_with_pacing_assembles_actual_and_pacing(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService
    from modules.ga4.repository import repository

    repository.upsert_kpi_target(
        db, property_id="123456", metric_key="conversions", period_type="month",
        period_key="2026-07", target_value=100, created_by=sample_user.id,
    )
    db.commit()

    mocker.patch(
        "modules.ga4.insights_service.GA4Service.get_analytics",
        return_value=({"rows": [{"conversions": 60}]}, None),
    )

    results = GA4InsightsService.get_kpi_targets_with_pacing(db, user=sample_user, property_id="123456")

    assert len(results) == 1
    assert results[0]["actual_value"] == 60
    assert results[0]["target_value"] == 100
    assert results[0]["status"] in {"ahead", "on_track", "behind"}


@pytest.mark.unit
def test_get_kpi_targets_with_pacing_marks_data_unavailable_on_ga4_error(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService
    from modules.ga4.repository import repository

    repository.upsert_kpi_target(
        db, property_id="123456", metric_key="sessions", period_type="month",
        period_key="2026-07", target_value=1000, created_by=sample_user.id,
    )
    db.commit()

    mocker.patch(
        "modules.ga4.insights_service.GA4Service.get_analytics",
        return_value=(None, "No GA4 credentials found"),
    )

    results = GA4InsightsService.get_kpi_targets_with_pacing(db, user=sample_user, property_id="123456")

    assert results[0]["status"] == "data_unavailable"
    assert results[0]["actual_value"] == 0.0


# ─── repository ──────────────────────────────────────────────────────
@pytest.mark.unit
def test_repository_upsert_kpi_target_updates_same_key_instead_of_duplicating(db, sample_user):
    from modules.ga4.repository import repository

    first = repository.upsert_kpi_target(
        db, property_id="123456", metric_key="conversions", period_type="month",
        period_key="2026-07", target_value=100, created_by=sample_user.id,
    )
    db.commit()

    second = repository.upsert_kpi_target(
        db, property_id="123456", metric_key="conversions", period_type="month",
        period_key="2026-07", target_value=200, created_by=sample_user.id,
    )
    db.commit()

    assert second.id == first.id
    assert second.target_value == 200

    all_targets = repository.list_kpi_targets(db, property_id="123456")
    assert len(all_targets) == 1

    assert repository.delete_kpi_target(db, first.id) is True
    db.commit()
    assert repository.list_kpi_targets(db, property_id="123456") == []
    assert repository.delete_kpi_target(db, "does-not-exist") is False


# ─── router ───────────────────────────────────────────────────────────
@pytest.mark.integration
def test_kpi_targets_crud_endpoints(client, db, sample_user, mocker):
    _override_dependencies(client.app, sample_user, db)
    mocker.patch(
        "modules.ga4.insights_service.GA4Service.get_analytics",
        return_value=({"rows": [{"conversions": 60}]}, None),
    )

    created = client.put(
        "/api/ga4/insights/kpi-targets",
        json={
            "property_id": "123456",
            "metric_key": "conversions",
            "period_type": "month",
            "period_key": "2026-07",
            "target_value": 100,
        },
    )
    assert created.status_code == 200
    target_id = created.json()["id"]

    listed = client.get("/api/ga4/insights/kpi-targets", params={"property_id": "123456"})
    assert listed.status_code == 200
    targets = listed.json()["targets"]
    assert len(targets) == 1
    assert targets[0]["id"] == target_id
    assert targets[0]["actual_value"] == 60

    deleted = client.delete(f"/api/ga4/insights/kpi-targets/{target_id}")
    assert deleted.status_code == 200

    missing = client.delete(f"/api/ga4/insights/kpi-targets/{target_id}")
    assert missing.status_code == 404


@pytest.mark.integration
def test_kpi_target_payload_rejects_mismatched_period_key_format(client, db, sample_user):
    _override_dependencies(client.app, sample_user, db)

    resp = client.put(
        "/api/ga4/insights/kpi-targets",
        json={
            "property_id": "123456",
            "metric_key": "conversions",
            "period_type": "month",
            "period_key": "2026-Q3",  # 季格式套到月，應被拒絕
            "target_value": 100,
        },
    )
    assert resp.status_code == 422
