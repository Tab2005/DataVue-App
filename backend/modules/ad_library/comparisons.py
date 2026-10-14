"""
Ad Library - 文案／素材比對（docs/74 第二節）

在同一範圍（廣告組合或行銷活動）內，依廣告的 copy_key / media_key 分組：

| copy_key | media_key | 關係 |
|---|---|---|
| 相同 | 不同 | media_test 素材測試（文案固定，比較素材） |
| 不同 | 相同 | copy_test 文案測試（素材固定，比較文案） |
| 相同 | 相同 | duplicate 重複投放 |

輸出以「組」為單位：一組 = 一個固定的元素 + 兩個以上的變體，每個變體底下
可能有多則廣告（例如重複投放的廣告會落在同一個變體）。鑰匙為 None 的廣告
不參與對應面向的比對。純函數、不碰 DB。
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

from .hierarchy import ad_node

RELATIONS = ("media_test", "copy_test", "duplicate")
SCOPES = ("adset", "campaign")

# 交給前端與 AI 的成效歸屬前提（docs/74「成效歸屬的前提」）
ATTRIBUTION_NOTE = (
    "成效為廣告層級數字：文案測試／素材測試比較的是固定一個變因後的整則廣告成效，"
    "不代表能把成效拆給單一文案或素材。行銷活動範圍的比較橫跨不同廣告組合（受眾不同），"
    "差異也可能來自受眾或預算。"
)


def _sum_metrics(ads: Iterable[dict]) -> dict[str, Any]:
    impressions = clicks = 0
    spend = 0.0
    for ad in ads:
        m = ad["metrics"]
        impressions += m["impressions"] or 0
        clicks += m["clicks"] or 0
        spend += m["spend"] or 0.0
    return {
        "impressions": impressions,
        "clicks": clicks,
        "spend": spend,
        "ctr": (clicks / impressions * 100) if impressions else 0.0,
    }


def _copy_preview(item) -> dict[str, Any]:
    return {
        "primary_texts": list(item.primary_texts or []),
        "headlines": list(item.headlines or []),
        "descriptions": list(item.descriptions or []),
    }


def _media_preview(item) -> dict[str, Any]:
    media = item.media or []
    thumb = next((m for m in media if m.get("asset_id") or m.get("fb_url")), None)
    return {
        "media_type": item.media_type,
        "media_count": len(media),
        "thumbnail": (
            {"kind": thumb.get("kind") or "image", "asset_id": thumb.get("asset_id"), "fb_url": thumb.get("fb_url")}
            if thumb else None
        ),
    }


def ad_summary(item) -> dict[str, Any]:
    node = ad_node(item)
    node.update({
        "adset_id": item.adset_id,
        "adset_name": item.adset_name,
        "campaign_id": item.campaign_id,
        "campaign_name": item.campaign_name,
    })
    return node


def _variants(items: list, key_attr: str, preview) -> list[dict]:
    by_key: dict[str, list] = defaultdict(list)
    for item in items:
        by_key[getattr(item, key_attr)].append(item)
    variants = []
    for key, group in by_key.items():
        ads = sorted((ad_summary(i) for i in group), key=lambda a: a["metrics"]["spend"] or 0.0, reverse=True)
        variants.append({"key": key, "preview": preview(group[0]), "ads": ads, "metrics": _sum_metrics(ads)})
    variants.sort(key=lambda v: v["metrics"]["spend"], reverse=True)
    return variants


def _scope_info(scope: str, items: list) -> dict[str, Any]:
    first = items[0]
    if scope == "adset":
        return {"level": "adset", "id": first.adset_id, "name": first.adset_name,
                "campaign_id": first.campaign_id, "campaign_name": first.campaign_name}
    return {"level": "campaign", "id": first.campaign_id, "name": first.campaign_name}


def _groups_in_scope(scope: str, items: list) -> list[dict]:
    groups: list[dict] = []
    scope_info = _scope_info(scope, items)

    by_copy: dict[str, list] = defaultdict(list)
    by_media: dict[str, list] = defaultdict(list)
    by_both: dict[tuple[str, str], list] = defaultdict(list)
    for item in items:
        if item.copy_key:
            by_copy[item.copy_key].append(item)
        if item.media_key:
            by_media[item.media_key].append(item)
        if item.copy_key and item.media_key:
            by_both[(item.copy_key, item.media_key)].append(item)

    # 素材測試：同文案、兩種以上素材（素材鑰匙為 None 的廣告不知道素材是否相同，排除）
    for copy_key, group in by_copy.items():
        with_media = [i for i in group if i.media_key]
        if len({i.media_key for i in with_media}) >= 2:
            groups.append({
                "relation": "media_test",
                "scope": scope_info,
                "fixed": {"kind": "copy", "key": copy_key, "preview": _copy_preview(with_media[0])},
                "variants": _variants(with_media, "media_key", _media_preview),
            })

    # 文案測試：同素材、兩種以上文案
    for media_key, group in by_media.items():
        with_copy = [i for i in group if i.copy_key]
        if len({i.copy_key for i in with_copy}) >= 2:
            groups.append({
                "relation": "copy_test",
                "scope": scope_info,
                "fixed": {"kind": "media", "key": media_key, "preview": _media_preview(with_copy[0])},
                "variants": _variants(with_copy, "copy_key", _copy_preview),
            })

    # 重複投放：文案與素材都相同的兩則以上廣告（只有一個「變體」，列出各則廣告）
    for (copy_key, media_key), group in by_both.items():
        if len(group) >= 2:
            ads = sorted((ad_summary(i) for i in group), key=lambda a: a["metrics"]["spend"] or 0.0, reverse=True)
            groups.append({
                "relation": "duplicate",
                "scope": scope_info,
                "fixed": {
                    "kind": "both",
                    "key": f"{copy_key}:{media_key}",
                    "preview": {**_copy_preview(group[0]), **_media_preview(group[0])},
                },
                "variants": [{"key": media_key, "preview": None, "ads": ads, "metrics": _sum_metrics(ads)}],
            })
    return groups


def build_comparisons(items, *, scope: str = "adset", relation: str | None = None) -> dict[str, Any]:
    """依範圍分組後找出比對組，依總花費由高到低排序。"""
    by_scope: dict[str | None, list] = defaultdict(list)
    for item in items:
        scope_id = item.adset_id if scope == "adset" else item.campaign_id
        if scope_id:
            by_scope[scope_id].append(item)

    groups: list[dict] = []
    for scope_items in by_scope.values():
        if len(scope_items) >= 2:
            groups.extend(_groups_in_scope(scope, scope_items))

    counts = {r: sum(1 for g in groups if g["relation"] == r) for r in RELATIONS}
    if relation:
        groups = [g for g in groups if g["relation"] == relation]
    for g in groups:
        g["metrics"] = _sum_metrics(ad for v in g["variants"] for ad in v["ads"])
    groups.sort(key=lambda g: g["metrics"]["spend"], reverse=True)

    total = len(items)
    without_copy = sum(1 for i in items if not i.copy_key)
    without_media = sum(1 for i in items if not i.media_key)
    return {
        "scope": scope,
        "counts": counts,
        "groups": groups,
        "coverage": {"ads": total, "without_copy_key": without_copy, "without_media_key": without_media},
        "note": ATTRIBUTION_NOTE,
    }
