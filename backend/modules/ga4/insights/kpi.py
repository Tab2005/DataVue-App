"""Kpi helpers for GA4 insights."""

from __future__ import annotations

from ._shared import *


def save_ai_summary(db, *, snapshot_id: str, ai_summary: str):
    return repository.update_ai_summary(db, snapshot_id=snapshot_id, ai_summary=ai_summary)


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
    start, end = _service_attr("_kpi_period_bounds", _kpi_period_bounds)(period_type, period_key)
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


def get_kpi_targets_with_pacing(db, *, user: User, property_id: str) -> list[dict]:
    today = (datetime.utcnow() + timedelta(hours=8)).date()
    targets = repository.list_kpi_targets(db, property_id=property_id)
    results = []
    for target in targets:
        api_metric = SUPPORTED_METRICS.get(target.metric_key, target.metric_key)
        start, end = _service_attr("_kpi_period_bounds", _kpi_period_bounds)(target.period_type, target.period_key)
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

        pacing = _service_attr("compute_kpi_pacing", compute_kpi_pacing)(
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


def delete_kpi_target(db, *, target_id: str) -> bool:
    return repository.delete_kpi_target(db, target_id)
