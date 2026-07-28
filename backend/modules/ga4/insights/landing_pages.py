"""Landing pages helpers for GA4 insights."""

from __future__ import annotations

import hashlib

from ._shared import *
from .channel_groups import get_channel_group_match_conditions


def get_landing_pages(
    db, *, user: User, property_id: str, days: int = 7, key_event: str | None = None,
    channel_dimension: str | None = None, channel_value: str | None = None,
    channel_group: str | None = None,
):
    if key_event and not LANDING_PAGE_KEY_EVENT_PATTERN.match(key_event):
        raise ValueError(f"Invalid key_event: {key_event}")

    # docs/42+44：到達頁渠道篩選。channel_value（單一精確值）與 channel_group
    # （docs/43 自訂分組，多條規則 OR 組合）互斥，兩者都需要搭配
    # channel_dimension 一起提供，避免「只給維度」這種篩選條件不完整的狀態
    # 被誤當成「有篩選」處理。
    if channel_value and channel_group:
        raise ValueError("channel_value and channel_group are mutually exclusive")
    if (channel_value or channel_group) and not channel_dimension:
        raise ValueError("channel_dimension is required when channel_value or channel_group is provided")
    if channel_dimension and not channel_value and not channel_group:
        raise ValueError("channel_dimension requires channel_value or channel_group")
    if channel_dimension and channel_dimension not in CHANNEL_DIMENSION_MAP:
        raise ValueError(f"Unsupported channel_dimension: {channel_dimension}")

    # 只取工作階段那一半（CHANNEL_DIMENSION_MAP[dim][0]），不用 firstUser 那
    # 一半：到達頁本身就是工作階段層級的概念，配「這次工作階段的渠道」才
    # 有意義，見 docs/41 的討論。GA4 Data API 的 dimensionFilter 是獨立於
    # dimensions（group by）之外的篩選條件，不需要把這個維度也放進
    # dimensions 才能篩，回傳列的形狀（一個到達頁一列）完全不受影響。
    ga4_channel_dimension = CHANNEL_DIMENSION_MAP[channel_dimension][0] if channel_dimension else None
    if channel_group:
        # docs/44：自訂分組——把該分組底下「全部」規則的比對條件轉成 OR
        # 篩選（同分組的規則都要一起生效，不是只取第一條）。分組不存在
        # （例如規則已被刪除）時，比對條件會是空 list，視為錯誤而非「查
        # 不到資料」，避免使用者誤以為這個分組本來就沒資料。
        conditions = get_channel_group_match_conditions(
            db, property_id=property_id, channel_dimension=channel_dimension, group_label=channel_group,
        )
        if not conditions:
            raise ValueError(f"Unknown channel_group: {channel_group}")
        dimension_filter = [
            (ga4_channel_dimension, match_type, pattern) for match_type, pattern in conditions
        ]
    elif channel_value:
        dimension_filter = (ga4_channel_dimension, channel_value)
    else:
        dimension_filter = None

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
        dimension_filter=dimension_filter,
    )
    if error:
        raise RuntimeError(error)
    rows = (data or {}).get("rows", [])

    # 關鍵事件分項統計：pivot landingPage × eventName，供前端下拉與明細
    # （查詢失敗不影響主表格，只是分項/下拉暫缺，同模組既有的容錯慣例）。
    # 渠道篩選也要一併帶上，否則主表格數字有篩、這裡的明細沒篩，會對不起來。
    key_events_breakdown: dict[str, dict[str, int]] = {}
    available_key_events: set[str] = set()
    breakdown_data, breakdown_error = GA4Service.get_analytics(
        user=user, property_id=property_id, start_date=start_date, end_date=end_date,
        metrics=["keyEvents"], dimensions=["landingPage", "eventName"], db=db,
        dimension_filter=dimension_filter,
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
    # 存放、AI 解讀互不覆寫（同第 4 波渠道維度切換前例）。渠道篩選比照同一
    # 套規則疊加後綴，但 channel_value/channel_group 是自由文字（例如完整
    # UTM campaign 名稱），直接串進 kind 可能撐爆 String(80) 欄位、也可能
    # 因為截斷而讓兩個不同篩選值誤判成同一筆快照，所以改用短雜湊代表這組
    # 篩選條件。自訂分組用 "chg_" 前綴、精確值篩選用 "ch_" 前綴區分兩種篩
    # 選來源，方便排查（雖然雜湊碰撞機率極低，前綴區分讓意圖更清楚）。
    kind = "landing_page"
    if key_event:
        kind += f":{key_event}"
    if channel_group:
        filter_digest = hashlib.md5(f"{channel_dimension}:group:{channel_group}".encode()).hexdigest()[:10]
        kind += f":chg_{filter_digest}"
    elif channel_dimension:
        filter_digest = hashlib.md5(f"{channel_dimension}:{channel_value}".encode()).hexdigest()[:10]
        kind += f":ch_{filter_digest}"

    payload = {
        "start_date": start_date,
        "end_date": end_date,
        "days": days,
        "key_event": key_event,
        "channel_dimension": channel_dimension,
        "channel_value": channel_value,
        "channel_group": channel_group,
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
