from datetime import UTC, date, datetime, timedelta

from exceptions import ValidationError
from modules.fb_ads.analytics_service import get_custom_report

from ..schemas import ObservedCreativeCandidate


_LIFETIME_START = date(2000, 1, 1)


def resolve_observation_window(
    window_kind: str,
    *,
    today: date | None = None,
) -> tuple[str, str]:
    current_day = today or datetime.now(UTC).date()

    if window_kind == "last_7d":
        start = current_day - timedelta(days=6)
    elif window_kind == "last_30d":
        start = current_day - timedelta(days=29)
    elif window_kind == "lifetime":
        # 限制 lifetime start 最多追溯到 3 年前 (約 1095 天)，以防 FB Graph API 報錯或 timeout (37個月限制)
        three_years_ago = current_day - timedelta(days=3 * 365)
        start = max(_LIFETIME_START, three_years_ago)
    else:
        raise ValueError(f"Unsupported observation window kind: {window_kind}")

    return start.isoformat(), current_day.isoformat()


def normalize_facebook_ad_row(
    *,
    row: dict,
    account_id: str,
    market: str,
    placement_family: str,
    primary_text: str | None,
    headline: str | None,
    cta: str | None,
    observation_window_kind: str,
    observation_window_start: str,
    observation_window_end: str,
    source_fetched_at: str,
) -> ObservedCreativeCandidate:
    media_url = row.get("image_url")
    media_type = "image" if media_url else "unknown"

    performance_snapshot = {
        "spend": float(row.get("spend", 0) or 0),
        "impressions": int(row.get("impressions", 0) or 0),
        "clicks": int(row.get("clicks", 0) or 0),
        "purchases": int(row.get("purchases", 0) or 0),
        "purchase_value": float(row.get("purchase_value", 0) or 0),
        "roas": float(row.get("roas", 0) or 0),
        "ctr": float(row.get("ctr", 0) or 0),
        "cpc": float(row.get("cpc", 0) or 0),
    }

    return ObservedCreativeCandidate(
        source_platform="facebook_ads",
        source_account_id=account_id,
        campaign_id=row.get("campaign_id"),
        adset_id=row.get("adset_id"),
        ad_id=str(row.get("ad_id") or ""),
        ad_name=row.get("name") or row.get("ad_name"),
        objective=row.get("objective"),
        placement_family=placement_family,
        market=market,
        primary_text=primary_text,
        headline=headline,
        cta=cta,
        media_url=media_url,
        media_type=media_type,
        performance_snapshot=performance_snapshot,
        observation_window_kind=observation_window_kind,
        observation_window_start=observation_window_start,
        observation_window_end=observation_window_end,
        source_fetched_at=source_fetched_at,
    )


async def fetch_observed_creative_candidate(
    *,
    account_id: str,
    ad_id: str,
    user_id: str,
    observation_window_kind: str,
    market: str,
    placement_family: str,
    primary_text: str | None,
    headline: str | None,
    cta: str | None,
    team_id: str | None = None,
    report_fetcher=None,
    since: str | None = None,
    until: str | None = None,
) -> ObservedCreativeCandidate:
    if observation_window_kind == "custom" and since and until:
        observation_window_start, observation_window_end = since, until
    else:
        observation_window_start, observation_window_end = resolve_observation_window(observation_window_kind)
    fetcher = report_fetcher or get_custom_report
    rows = await fetcher(
        account_id=account_id,
        user_id=user_id,
        since=observation_window_start,
        until=observation_window_end,
        level="ad",
        team_id=team_id,
    )
    if rows is None:
        raise ValueError("FB Ads report unavailable")

    target_row = next((row for row in rows if str(row.get("ad_id")) == str(ad_id)), None)
    if target_row is None:
        raise ValidationError(f"該廣告目前在 Facebook 尚未產生任何投放數據，無法匯入漂移診斷。")

    source_fetched_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return normalize_facebook_ad_row(
        row=target_row,
        account_id=account_id,
        market=market,
        placement_family=placement_family,
        primary_text=primary_text,
        headline=headline,
        cta=cta,
        observation_window_kind=observation_window_kind,
        observation_window_start=observation_window_start,
        observation_window_end=observation_window_end,
        source_fetched_at=source_fetched_at,
    )
