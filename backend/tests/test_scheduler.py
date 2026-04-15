from datetime import datetime

import pytest

from core.scheduler import get_next_run_time, is_schedule_overdue
from database.models.report import ReportSchedule


def _build_schedule(**overrides):
    payload = {
        "id": "schedule-1",
        "name": "Weekly Report",
        "ad_account_id": "act_123",
        "ad_account_name": "Test Account",
        "selected_metrics": "[\"spend\", \"roas\"]",
        "breakdown": "campaign",
        "frequency": "weekly",
        "day_of_week": "0",
        "day_of_month": None,
        "time_of_day": "08:30",
        "is_active": True,
        "is_notify_line": False,
        "user_id": "user-1",
        "team_id": None,
        "last_run": None,
        "next_run": None,
    }
    payload.update(overrides)
    return ReportSchedule(**payload)


@pytest.mark.unit
def test_get_next_run_time_uses_weekly_schedule():
    schedule = _build_schedule()
    reference = datetime.fromisoformat("2026-04-15T10:00:00+08:00")

    next_run = get_next_run_time(schedule, reference_time=reference)

    assert next_run == datetime(2026, 4, 20, 8, 30)


@pytest.mark.unit
def test_is_schedule_overdue_when_next_run_has_passed():
    schedule = _build_schedule(next_run=datetime(2026, 4, 14, 8, 30))

    assert is_schedule_overdue(schedule, reference_time=datetime(2026, 4, 15, 9, 0)) is True


@pytest.mark.unit
def test_is_schedule_not_overdue_when_inactive_or_future():
    inactive_schedule = _build_schedule(is_active=False, next_run=datetime(2026, 4, 14, 8, 30))
    future_schedule = _build_schedule(next_run=datetime(2026, 4, 20, 8, 30))
    reference = datetime(2026, 4, 15, 9, 0)

    assert is_schedule_overdue(inactive_schedule, reference_time=reference) is False
    assert is_schedule_overdue(future_schedule, reference_time=reference) is False