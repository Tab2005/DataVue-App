"""Channels helpers for GA4 insights."""

from __future__ import annotations

from ._shared import *


def _get_attribution_model(db, *, user: User, property_id: str) -> str:
    """回傳正規化後的歸因模式（"data_driven" / "last_click" / "unknown"）。

    查詢失敗或設定不在白名單內一律回退 "unknown"，不能讓這個輔助查詢
    影響渠道對照卡片本身的可用性（同模組既有容錯慣例）。
    """
    snapshot = repository.get_latest_snapshot(
        db, property_id=property_id, kind=ATTRIBUTION_SETTINGS_KIND, date=ATTRIBUTION_SETTINGS_DATE,
    )
    if snapshot and (datetime.utcnow() - snapshot.fetched_at) < timedelta(hours=ATTRIBUTION_SETTINGS_CACHE_HOURS):
        return snapshot.payload.get("attribution_model", "unknown")

    try:
        raw_model, error = GA4Client.get_attribution_settings(user, property_id, db)
        if error:
            raise RuntimeError(error)
        model = ATTRIBUTION_MODEL_MAP.get(raw_model, "unknown")
    except Exception as exc:
        logger.warning("[GA4Insights] get_attribution_settings failed for %s: %s", property_id, exc)
        # 查詢失敗時寧可回傳上一次快取到的值，也不要直接判 unknown（設定極少變動）。
        return snapshot.payload.get("attribution_model", "unknown") if snapshot else "unknown"

    repository.upsert_snapshot(
        db, property_id=property_id, kind=ATTRIBUTION_SETTINGS_KIND, date=ATTRIBUTION_SETTINGS_DATE,
        payload={"attribution_model": model, "raw_model": raw_model}, fetched_by=user.id,
    )
    return model


def get_channels(
    db, *, user: User, property_id: str, days: int = 7,
    dimension: str = CHANNEL_DEFAULT_DIMENSION,
):
    if dimension not in CHANNEL_DIMENSION_MAP:
        raise ValueError(f"Unsupported channel dimension: {dimension}")
    session_dim, first_user_dim = CHANNEL_DIMENSION_MAP[dimension]
    start_date, end_date = _service_attr("_trailing_period", _trailing_period)(days)

    session_data, error = GA4Service.get_analytics(
        user=user, property_id=property_id, start_date=start_date, end_date=end_date,
        metrics=[CHANNEL_METRIC], dimensions=[session_dim], db=db,
    )
    if error:
        raise RuntimeError(error)
    first_user_data, error = GA4Service.get_analytics(
        user=user, property_id=property_id, start_date=start_date, end_date=end_date,
        metrics=[CHANNEL_METRIC], dimensions=[first_user_dim], db=db,
    )
    if error:
        raise RuntimeError(error)

    session_by_channel = {
        row[session_dim]: row.get(CHANNEL_METRIC, 0)
        for row in (session_data or {}).get("rows", [])
    }
    first_user_by_channel = {
        row[first_user_dim]: row.get(CHANNEL_METRIC, 0)
        for row in (first_user_data or {}).get("rows", [])
    }

    channels = sorted(set(session_by_channel) | set(first_user_by_channel))
    rows = []
    for channel in channels:
        closing = session_by_channel.get(channel, 0)
        assisting = first_user_by_channel.get(channel, 0)
        if closing > 0 and (closing + assisting) >= _get_channel_min_sample():
            ratio = assisting / closing
            if ratio > 1.3:
                tag = "assist"
            elif ratio < 0.7:
                tag = "close"
            else:
                tag = "balanced"
        else:
            ratio = assisting / closing if closing > 0 else None
            tag = "insufficient_data"
        rows.append({
            "channel": channel,
            "closing_conversions": closing,
            "assisting_conversions": assisting,
            "ratio": ratio,
            "tag": tag,
        })

    total_row_count = len(rows)
    # docs/34 第四波：標籤（assist/close/balanced）只反映渠道自身「開發 vs
    # 收單」的內部角色，不反映它在全站訂單裡的份量；無論是否截斷都依
    # （收單＋開發）轉換數降冪排序，量級大的渠道排最前面，避免使用者掃視
    # 表格時把小量渠道的角色標籤誤讀成「主要訂單來源」。
    total_closing_conversions = sum(r["closing_conversions"] for r in rows)
    rows = sorted(rows, key=lambda r: r["closing_conversions"] + r["assisting_conversions"], reverse=True)
    # 高基數保護：來源/媒介/廣告活動的列數可能遠多於管道群組，只留前 20
    # 列，payload 註記截斷與原始總列數。
    truncated = total_row_count > CHANNEL_TOP_N
    if truncated:
        rows = rows[:CHANNEL_TOP_N]

    # kind 命名：預設維度沿用既有 "daily_channel"（向後相容既有快照與 AI
    # 解讀）；其餘維度加後綴各自獨立存放，互不覆寫
    # （"daily_channel:source_medium" 27 字元 < String(30) 上限）。
    kind = "daily_channel" if dimension == CHANNEL_DEFAULT_DIMENSION else f"daily_channel:{dimension}"

    payload = {
        "start_date": start_date,
        "end_date": end_date,
        "days": days,
        "dimension": dimension,
        "channels": rows,
        "truncated": truncated,
        "total_row_count": total_row_count,
        "total_closing_conversions": total_closing_conversions,
        "attribution_model": _service_attr("_get_attribution_model", _get_attribution_model)(db, user=user, property_id=property_id),
    }
    return repository.upsert_snapshot(
        db, property_id=property_id, kind=kind, date=end_date, payload=payload, fetched_by=user.id,
    )
