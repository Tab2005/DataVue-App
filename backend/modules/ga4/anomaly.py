"""Pure functions for GA4 anomaly detection."""

from __future__ import annotations

from statistics import median

SENSITIVITY_K = {"high": 2.0, "medium": 3.0, "low": 4.0}
MIN_SAMPLE_SIZE = 4


def compute_median_mad(samples: list[float]) -> tuple[float, float]:
    center = float(median(samples))
    raw_mad = float(median([abs(value - center) for value in samples]))
    mad_floor = abs(center) * 0.05
    safe_mad = max(raw_mad, mad_floor)
    return center, safe_mad


def build_expected_range(samples: list[float], sensitivity: str) -> dict | None:
    cleaned = [float(value) for value in samples if value is not None]
    if len(cleaned) < MIN_SAMPLE_SIZE:
        return None
    k = SENSITIVITY_K.get(sensitivity, SENSITIVITY_K["medium"])
    center, mad = compute_median_mad(cleaned)
    return {
        "median": center,
        "mad": mad,
        "k": k,
        "low": center - k * mad,
        "high": center + k * mad,
        "critical_low": center - 2 * k * mad,
        "critical_high": center + 2 * k * mad,
        "sample_size": len(cleaned),
    }


def evaluate_anomaly(*, observed: float, samples: list[float], sensitivity: str) -> dict | None:
    expected = build_expected_range(samples, sensitivity)
    if not expected:
        return None

    if observed < expected["low"]:
        severity = "critical" if observed < expected["critical_low"] else "warning"
        return {
            **expected,
            "observed": float(observed),
            "direction": "drop",
            "severity": severity,
            "delta": float(observed) - expected["median"],
            "is_anomaly": True,
        }
    if observed > expected["high"]:
        severity = "critical" if observed > expected["critical_high"] else "warning"
        return {
            **expected,
            "observed": float(observed),
            "direction": "spike",
            "severity": severity,
            "delta": float(observed) - expected["median"],
            "is_anomaly": True,
        }
    return {
        **expected,
        "observed": float(observed),
        "direction": "normal",
        "severity": "normal",
        "delta": float(observed) - expected["median"],
        "is_anomaly": False,
    }
