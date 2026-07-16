"""Landing pages helpers for GA4 insights."""

from __future__ import annotations

from ._shared import *


def get_landing_pages(db, *, user: User, property_id: str, days: int = 7, key_event: str | None = None):
    if key_event and not LANDING_PAGE_KEY_EVENT_PATTERN.match(key_event):
        raise ValueError(f"Invalid key_event: {key_event}")

    start_date, end_date = _service_attr("_trailing_period", _trailing_period)(days)

    # 2026-07-10 與使用者確認：主查詢的「轉換次數」「轉換率」改用 GA4
    # 官方 keyEvents / sessionKeyEventRate；帶 key_event 時改用該事件的
    # 動態指標（GA4 Data API 支援 "keyEvents:{event}" 這種冒號後綴語法）。
    key_events_metric = f"keyEvents:{key_event}" if key_event else "keyEvents"
    key_event_rate_metric = f"sessionKeyEventRate:{key_event}" if key_event else "sessionKeyEventRate"

    data, error = GA4Service.get_analytics(
        user=user, property_id=property_id, start_date=start_date, end_date=end_date,
        metrics=["sessions", "engagementRate", "bounceRate", key_events_metric, key_event_rate_metric],
        dimensions=["landingPage"], db=db,
    )
    if error:
        raise RuntimeError(error)
    rows = (data or {}).get("rows", [])

    # 關鍵事件分項統計：pivot landingPage × eventName，供前端下拉與明細
    # （查詢失敗不影響主表格，只是分項/下拉暫缺，同模組既有的容錯慣例）。
    key_events_breakdown: dict[str, dict[str, int]] = {}
    available_key_events: set[str] = set()
    breakdown_data, breakdown_error = GA4Service.get_analytics(
        user=user, property_id=property_id, start_date=start_date, end_date=end_date,
        metrics=["keyEvents"], dimensions=["landingPage", "eventName"], db=db,
    )
    if not breakdown_error:
        for row in (breakdown_data or {}).get("rows", []):
            page = row.get("landingPage", "")
            event_name = row.get("eventName", "")
            count = row.get("keyEvents", 0)
            if not event_name or not count:
                continue
            key_events_breakdown.setdefault(page, {})[event_name] = count
            available_key_events.add(event_name)
    else:
        logger.warning("[GA4Insights] landing page key-events breakdown failed %s: %s", property_id, breakdown_error)

    rule_rows = repository.list_landing_page_rules(db, property_id=property_id)
    rules = [
        {"category": r.category, "match_type": r.match_type, "pattern": r.pattern, "priority": r.priority}
        for r in rule_rows
    ]

    enriched = []
    for row in rows:
        landing_page = row.get("landingPage", "")
        sessions = row.get("sessions", 0)
        key_events_count = row.get(key_events_metric, 0)
        session_key_event_rate = row.get(key_event_rate_metric, 0.0)
        category = _facade_attr("classify_landing_page", classify_landing_page)(landing_page, rules)
        enriched.append({
            "landingPage": landing_page,
            "sessions": sessions,
            "engagementRate": row.get("engagementRate", 0.0),
            "bounceRate": row.get("bounceRate", 0.0),
            "conversions": key_events_count,
            # 舊「次數比」口徑保留供回溯相容；前端不再以此欄顯示「轉換率」，
            # 主顯示改用下面的 session_key_event_rate（去重占比，見 5 節）。
            "conversion_rate": (key_events_count / sessions) if sessions else 0.0,
            "session_key_event_rate": session_key_event_rate,
            "category": category,
            "key_events_breakdown": key_events_breakdown.get(landing_page, {}),
            "is_high_traffic_low_conversion": False,
        })

    # 「高流量低轉換」改在同分類內計算（第 5 波刻意的語意變更），且改依
    # session_key_event_rate（去重占比）判定，不再用次數比。文章頁天生
    # 低轉換是常態，混排會讓商品頁的問題頁被稀釋而漏標、文章頁整批被誤
    # 標。四分位需要足夠樣本數，同既有規則：該分類樣本 <4 不標記。
    by_category: dict[str, list[dict]] = {}
    for row in enriched:
        by_category.setdefault(row["category"], []).append(row)
    for category_rows in by_category.values():
        if len(category_rows) >= 4:
            session_p75 = _percentile(sorted(r["sessions"] for r in category_rows), 0.75)
            rate_p25 = _percentile(sorted(r["session_key_event_rate"] for r in category_rows), 0.25)
            for row in category_rows:
                row["is_high_traffic_low_conversion"] = (
                    row["sessions"] >= session_p75 and row["session_key_event_rate"] <= rate_p25
                )

    category_counts = {category: len(category_rows) for category, category_rows in by_category.items()}

    # snapshot kind：全部事件維持 "landing_page"；指定事件加後綴各自獨立
    # 存放、AI 解讀互不覆寫（同第 4 波渠道維度切換前例）。
    kind = "landing_page" if not key_event else f"landing_page:{key_event}"

    payload = {
        "start_date": start_date,
        "end_date": end_date,
        "days": days,
        "key_event": key_event,
        "landing_pages": enriched,
        "category_counts": category_counts,
        "available_key_events": sorted(available_key_events),
        "session_key_event_rate_definition": LANDING_PAGE_SESSION_KEY_EVENT_RATE_DEFINITION,
        "key_events_count_definition": LANDING_PAGE_KEY_EVENTS_COUNT_DEFINITION,
    }
    return repository.upsert_snapshot(
        db, property_id=property_id, kind=kind, date=end_date, payload=payload, fetched_by=user.id,
    )


def list_landing_page_rules(db, *, property_id: str):
    return repository.list_landing_page_rules(db, property_id=property_id)


def upsert_landing_page_rule(
    db, *, rule_id: str | None, user_id: str, property_id: str,
    category: str, match_type: str, pattern: str, priority: int,
):
    if rule_id:
        row = repository.get_landing_page_rule(db, rule_id)
        if not row:
            return None
        row.property_id = property_id
        row.category = category
        row.match_type = match_type
        row.pattern = pattern
        row.priority = priority
        row.updated_at = datetime.utcnow()
        db.add(row)
        return row
    return repository.create_landing_page_rule(
        db,
        property_id=property_id,
        category=category,
        match_type=match_type,
        pattern=pattern,
        priority=priority,
        created_by=user_id,
    )


def delete_landing_page_rule(db, *, rule_id: str) -> bool:
    return repository.delete_landing_page_rule(db, rule_id)
