"""
Ad Library - creative 文案攤平（docs/73）

把 Graph API `/{act_id}/ads` 回傳的單支廣告（含 creative / insights）轉成
`ad_library_items` 一列的 dict。純函數、不碰 DB 與網路，方便單元測試。

文案來源優先序：
  1. 動態創意 `asset_feed_spec`：bodies / titles / descriptions /
     call_to_action_types / images / videos 全部保留成陣列
  2. `object_story_spec.link_data`（單圖、輪播 child_attachments）
  3. `object_story_spec.video_data`（影片）
  4. fallback：`creative.body` / `creative.title`
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _dedupe(values) -> list[str]:
    """去除空值與重複（保留原順序），全部轉成字串。"""
    seen: set[str] = set()
    out: list[str] = []
    for v in values:
        if v is None:
            continue
        s = str(v).strip()
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def _texts(entries) -> list[str]:
    """asset_feed_spec 的 bodies/titles/descriptions 皆為 [{text: ...}]。"""
    return _dedupe(e.get("text") for e in entries or [] if isinstance(e, dict))


def _parse_fb_datetime(value: str | None) -> datetime | None:
    """FB 時間格式 `2026-01-02T03:04:05+0800`；轉 naive UTC。"""
    if not value:
        return None
    try:
        dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        return None
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def _to_int(value) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def _to_float(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _media_entry(kind: str, fb_url: str | None, image_hash: str | None = None) -> dict | None:
    if not fb_url and not image_hash:
        return None
    return {"kind": kind, "fb_url": fb_url, "image_hash": image_hash, "asset_id": None}


def _extract_insights(ad: dict) -> dict:
    rows = (ad.get("insights") or {}).get("data") or []
    row = rows[0] if rows else {}
    return {
        "impressions": _to_int(row.get("impressions")),
        "reach": _to_int(row.get("reach")),
        "clicks": _to_int(row.get("clicks")),
        "spend": _to_float(row.get("spend")),
        "ctr": _to_float(row.get("ctr")),
    }


def normalize_ad(ad: dict[str, Any], *, account_id: str) -> dict[str, Any]:
    """把單支廣告轉成 ad_library_items 欄位 dict（不含 id / 時間戳記欄位）。"""
    creative = ad.get("creative") or {}
    story = creative.get("object_story_spec") or {}
    link_data = story.get("link_data") or {}
    video_data = story.get("video_data") or {}
    feed = creative.get("asset_feed_spec") or {}

    primary_texts: list[str] = []
    headlines: list[str] = []
    descriptions: list[str] = []
    cta_types: list[str] = []
    media: list[dict] = []
    link_url: str | None = None

    if feed:
        media_type = "dynamic"
        primary_texts = _texts(feed.get("bodies"))
        headlines = _texts(feed.get("titles"))
        descriptions = _texts(feed.get("descriptions"))
        cta_types = _dedupe(feed.get("call_to_action_types") or [])
        link_urls = _dedupe(
            (e.get("website_url") for e in feed.get("link_urls") or [] if isinstance(e, dict))
        )
        link_url = link_urls[0] if link_urls else None
        for img in feed.get("images") or []:
            entry = _media_entry("image", img.get("url"), img.get("hash"))
            if entry:
                media.append(entry)
        for vid in feed.get("videos") or []:
            entry = _media_entry("video_thumbnail", vid.get("thumbnail_url"))
            if entry:
                media.append(entry)
    elif video_data:
        media_type = "video"
        primary_texts = _dedupe([video_data.get("message")])
        headlines = _dedupe([video_data.get("title")])
        descriptions = _dedupe([video_data.get("link_description")])
        cta = video_data.get("call_to_action") or {}
        cta_types = _dedupe([cta.get("type")])
        link_url = (cta.get("value") or {}).get("link")
        entry = _media_entry(
            "video_thumbnail",
            video_data.get("image_url") or creative.get("thumbnail_url"),
            video_data.get("image_hash"),
        )
        if entry:
            media.append(entry)
    elif link_data.get("child_attachments"):
        media_type = "carousel"
        primary_texts = _dedupe([link_data.get("message")])
        children = link_data.get("child_attachments") or []
        headlines = _dedupe(c.get("name") for c in children)
        descriptions = _dedupe(c.get("description") for c in children)
        cta_types = _dedupe(
            [(link_data.get("call_to_action") or {}).get("type")]
            + [(c.get("call_to_action") or {}).get("type") for c in children]
        )
        link_url = link_data.get("link")
        for c in children:
            entry = _media_entry("image", c.get("picture"), c.get("image_hash"))
            if entry:
                media.append(entry)
    else:
        media_type = "video" if creative.get("video_id") else "image"
        primary_texts = _dedupe([link_data.get("message")])
        headlines = _dedupe([link_data.get("name")])
        descriptions = _dedupe([link_data.get("description")])
        cta_types = _dedupe([(link_data.get("call_to_action") or {}).get("type")])
        link_url = link_data.get("link")
        entry = _media_entry(
            "video_thumbnail" if media_type == "video" else "image",
            creative.get("image_url") or link_data.get("picture") or creative.get("thumbnail_url"),
            creative.get("image_hash") or link_data.get("image_hash"),
        )
        if entry:
            media.append(entry)

    # 任何型態都以 creative 頂層 body/title/CTA 補位
    if not primary_texts:
        primary_texts = _dedupe([creative.get("body")])
    if not headlines:
        headlines = _dedupe([creative.get("title")])
    if not cta_types:
        cta_types = _dedupe([creative.get("call_to_action_type")])
    if not media:
        entry = _media_entry(
            "video_thumbnail" if media_type == "video" else "image",
            creative.get("image_url") or creative.get("thumbnail_url"),
            creative.get("image_hash"),
        )
        if entry:
            media.append(entry)

    campaign = ad.get("campaign") or {}
    adset = ad.get("adset") or {}
    search_text = "\n".join(
        [ad.get("name") or "", campaign.get("name") or ""] + primary_texts + headlines + descriptions
    ).lower()

    return {
        "account_id": account_id,
        "ad_id": str(ad.get("id")),
        "ad_name": ad.get("name"),
        "campaign_id": campaign.get("id"),
        "campaign_name": campaign.get("name"),
        "adset_id": adset.get("id"),
        "adset_name": adset.get("name"),
        "objective": campaign.get("objective"),
        "effective_status": ad.get("effective_status"),
        "page_id": story.get("page_id"),
        "media_type": media_type,
        "primary_texts": primary_texts,
        "headlines": headlines,
        "descriptions": descriptions,
        "cta_types": cta_types,
        "link_url": link_url,
        "media": media,
        "preview_link": ad.get("preview_shareable_link"),
        "search_text": search_text,
        "ad_created_at": _parse_fb_datetime(ad.get("created_time")),
        "ad_updated_at": _parse_fb_datetime(ad.get("updated_time")),
        **_extract_insights(ad),
    }
