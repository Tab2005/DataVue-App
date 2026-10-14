"""
Ad Library - 動態素材元件成效解析（docs/74 第 3 階段）

`/{ad_id}/insights?breakdowns=<x>_asset` 每列回傳一個元件與其成效，例如：
  {"body_asset": {"text": "...", "id": "6051732675652"}, "impressions": "100", ...}
  {"image_asset": {"hash": "...", "url": "...", "id": "6051732672052"}, ...}

把回傳列轉成可對回 `ad_library_contents` 的元件（以 fingerprint.py 相同規則算
指紋）。純函數、不碰 DB 與網路。

已知限制：
- Meta 只開放 impressions / clicks / spend / reach / actions / action_values，
  CTR 由 clicks / impressions 自行計算。
- video_asset 的回傳欄位官方文件沒有寫明；只認 `video_id`，取不到就略過該列，
  不以 asset id 猜測。
"""

from __future__ import annotations

from typing import Any

from .fingerprint import normalize_text, text_fingerprint

# breakdown → (元件 kind, 該廣告需要有哪種內容才值得查)
BREAKDOWNS: dict[str, str] = {
    "body_asset": "primary_text",
    "title_asset": "headline",
    "description_asset": "description",
    "image_asset": "image",
    "video_asset": "video",
}
INSIGHT_FIELDS = "impressions,clicks,spend,reach"


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


def breakdowns_for_ad(item: dict[str, Any]) -> list[str]:
    """只查這則廣告實際有的元件類型，省下沒必要的 API 呼叫。"""
    media = item.get("media") or []
    wanted = []
    if item.get("primary_texts"):
        wanted.append("body_asset")
    if item.get("headlines"):
        wanted.append("title_asset")
    if item.get("descriptions"):
        wanted.append("description_asset")
    if any(m.get("kind") == "image" for m in media):
        wanted.append("image_asset")
    if any(m.get("kind") == "video_thumbnail" for m in media):
        wanted.append("video_asset")
    return wanted


def _component(breakdown: str, asset: dict) -> dict | None:
    kind = BREAKDOWNS[breakdown]
    if kind in ("primary_text", "headline", "description"):
        text = normalize_text(asset.get("text"))
        if not text:
            return None
        return {"kind": kind, "fingerprint": text_fingerprint(text), "text_value": text}
    if kind == "image":
        image_hash = asset.get("hash")
        if not image_hash:
            return None
        return {"kind": "image", "fingerprint": f"img:{image_hash}", "image_hash": image_hash}
    video_id = asset.get("video_id")
    if not video_id:
        return None
    return {"kind": "video", "fingerprint": f"vid:{video_id}", "video_id": str(video_id)}


def parse_asset_rows(breakdown: str, rows: list[dict]) -> tuple[list[dict], int]:
    """回傳 (元件成效清單, 無法識別而略過的列數)；同一元件多列時加總。"""
    merged: dict[str, dict] = {}
    skipped = 0
    for row in rows or []:
        asset = row.get(breakdown)
        component = _component(breakdown, asset) if isinstance(asset, dict) else None
        if component is None:
            skipped += 1
            continue
        entry = merged.setdefault(component["fingerprint"], {
            **component,
            "fb_asset_id": str(asset.get("id")) if asset.get("id") else None,
            "impressions": 0,
            "reach": 0,
            "clicks": 0,
            "spend": 0.0,
        })
        entry["impressions"] += _to_int(row.get("impressions"))
        # reach 跨列無法加總（會重複計算），取最大值作為下限
        entry["reach"] = max(entry["reach"], _to_int(row.get("reach")))
        entry["clicks"] += _to_int(row.get("clicks"))
        entry["spend"] += _to_float(row.get("spend"))
    return list(merged.values()), skipped
