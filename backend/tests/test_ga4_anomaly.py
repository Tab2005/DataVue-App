import pytest

from modules.ga4.anomaly import build_expected_range, evaluate_anomaly


@pytest.mark.unit
def test_build_expected_range_requires_minimum_samples():
    assert build_expected_range([1, 2, 3], "medium") is None


@pytest.mark.unit
def test_build_expected_range_uses_floor_when_mad_is_zero():
    result = build_expected_range([100, 100, 100, 100], "medium")

    assert result is not None
    assert result["mad"] == 5.0
    assert result["low"] == 85.0
    assert result["high"] == 115.0


@pytest.mark.unit
def test_evaluate_anomaly_detects_warning_drop():
    result = evaluate_anomaly(observed=85, samples=[100, 110, 90, 105, 95, 100], sensitivity="high")

    assert result is not None
    assert result["is_anomaly"] is True
    assert result["direction"] == "drop"
    assert result["severity"] == "warning"


@pytest.mark.unit
def test_evaluate_anomaly_detects_critical_spike():
    result = evaluate_anomaly(observed=200, samples=[100, 102, 98, 101, 99, 100], sensitivity="high")

    assert result is not None
    assert result["is_anomaly"] is True
    assert result["direction"] == "spike"
    assert result["severity"] == "critical"


@pytest.mark.unit
def test_evaluate_anomaly_returns_normal_when_within_band():
    result = evaluate_anomaly(observed=101, samples=[100, 102, 98, 101, 99, 100], sensitivity="medium")

    assert result is not None
    assert result["is_anomaly"] is False
    assert result["direction"] == "normal"

