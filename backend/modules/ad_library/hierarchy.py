"""
Ad Library - 階層樹組裝（docs/74 第一節）

把 `ad_library_campaigns` / `ad_library_adsets` / `ad_library_items` 三張表的列
組成「行銷活動 → 廣告組合 → 廣告」的巢狀 dict。純函數、不碰 DB，方便單元測試。

上層設定可能缺漏（docs/74 上線前抓的舊資料、或行銷活動／廣告組合撞到抓取上限），
此時依廣告上的 campaign_id / adset_id 補一個佔位節點（`settings_available=False`），
名稱沿用廣告列上的 campaign_name / adset_name，成效則由底下廣告加總。
"""

from __future__ import annotations

from typing import Any, Iterable

from .currency import to_major_unit
from .repository import STATUS_GROUPS

AD_TEXT_PREVIEW_CHARS = 120


def _metrics(row) -> dict[str, Any]:
    return {
        "impressions": row.impressions or 0,
        "reach": row.reach or 0,
        "clicks": row.clicks or 0,
        "spend": row.spend or 0.0,
        "ctr": row.ctr or 0.0,
    }


def _sum_metrics(children: Iterable[dict]) -> dict[str, Any]:
    """佔位節點用：由子節點加總。reach 無法加總（會重複計算），一律為 None。"""
    impressions = clicks = 0
    spend = 0.0
    for child in children:
        m = child["metrics"]
        impressions += m["impressions"] or 0
        clicks += m["clicks"] or 0
        spend += m["spend"] or 0.0
    return {
        "impressions": impressions,
        "reach": None,
        "clicks": clicks,
        "spend": spend,
        "ctr": (clicks / impressions * 100) if impressions else 0.0,
    }


def _budget_fields(row) -> dict[str, Any]:
    return {
        "currency": row.currency,
        "daily_budget": to_major_unit(row.daily_budget, row.currency),
        "lifetime_budget": to_major_unit(row.lifetime_budget, row.currency),
    }


def _thumbnail(media: list | None) -> dict | None:
    for m in media or []:
        if m.get("asset_id") or m.get("fb_url"):
            return {"kind": m.get("kind") or "image", "asset_id": m.get("asset_id"), "fb_url": m.get("fb_url")}
    return None


def _first(values: list | None, limit: int | None = None) -> str | None:
    if not values:
        return None
    text = values[0]
    if limit and len(text) > limit:
        return text[:limit] + "…"
    return text


def ad_node(item) -> dict[str, Any]:
    return {
        "id": item.id,
        "ad_id": item.ad_id,
        "name": item.ad_name,
        "effective_status": item.effective_status,
        "media_type": item.media_type,
        "primary_text": _first(item.primary_texts, AD_TEXT_PREVIEW_CHARS),
        "headline": _first(item.headlines),
        "variant_count": max(len(item.primary_texts or []), len(item.headlines or []), len(item.media or [])),
        "thumbnail": _thumbnail(item.media),
        "copy_key": getattr(item, "copy_key", None),
        "media_key": getattr(item, "media_key", None),
        "metrics": _metrics(item),
    }


def adset_node(adset, ads: list[dict]) -> dict[str, Any]:
    return {
        "id": adset.id,
        "adset_id": adset.adset_id,
        "name": adset.name,
        "settings_available": True,
        "status": adset.status,
        "effective_status": adset.effective_status,
        "optimization_goal": adset.optimization_goal,
        "billing_event": adset.billing_event,
        "bid_strategy": adset.bid_strategy,
        "bid_amount": to_major_unit(adset.bid_amount, adset.currency),
        "destination_type": adset.destination_type,
        "is_dynamic_creative": adset.is_dynamic_creative,
        **_budget_fields(adset),
        "targeting_summary": adset.targeting_summary or {},
        "start_time": adset.start_time,
        "end_time": adset.end_time,
        "metrics": _metrics(adset),
        "ads": ads,
    }


def _placeholder_adset(adset_id: str | None, name: str | None, ads: list[dict]) -> dict[str, Any]:
    return {
        "id": None,
        "adset_id": adset_id,
        "name": name,
        "settings_available": False,
        "effective_status": None,
        "metrics": _sum_metrics(ads),
        "ads": ads,
    }


def campaign_node(campaign, adsets: list[dict]) -> dict[str, Any]:
    return {
        "id": campaign.id,
        "campaign_id": campaign.campaign_id,
        "name": campaign.name,
        "settings_available": True,
        "objective": campaign.objective,
        "status": campaign.status,
        "effective_status": campaign.effective_status,
        "buying_type": campaign.buying_type,
        "bid_strategy": campaign.bid_strategy,
        "smart_promotion_type": campaign.smart_promotion_type,
        # 預算設在行銷活動層＝CBO（Advantage+ 行銷活動預算）
        "budget_level": "campaign" if (campaign.daily_budget or campaign.lifetime_budget) else "adset",
        **_budget_fields(campaign),
        "special_ad_categories": campaign.special_ad_categories or [],
        "start_time": campaign.start_time,
        "stop_time": campaign.stop_time,
        "metrics": _metrics(campaign),
        "adsets": adsets,
    }


def _placeholder_campaign(campaign_id: str | None, name: str | None, objective: str | None, adsets: list[dict]) -> dict[str, Any]:
    return {
        "id": None,
        "campaign_id": campaign_id,
        "name": name,
        "settings_available": False,
        "objective": objective,
        "effective_status": None,
        "metrics": _sum_metrics(adsets),
        "adsets": adsets,
    }


def sort_by_spend(nodes: list[dict]) -> list[dict]:
    return sorted(nodes, key=lambda n: (n["metrics"]["spend"] or 0.0), reverse=True)


def _status_matches(effective_status: str | None, status: str | None) -> bool:
    if not status:
        return True
    if status in STATUS_GROUPS:
        return effective_status in STATUS_GROUPS[status]
    grouped = {s for group in STATUS_GROUPS.values() for s in group}
    return effective_status not in grouped


def build_tree(campaigns, adsets, items, *, status: str | None = None) -> list[dict[str, Any]]:
    """組出行銷活動清單（各自含 adsets → ads），依花費由高到低排序。

    status（active / paused / other）只篩行銷活動層，底下的廣告組合與廣告
    全部保留並各自帶狀態，方便看「投放中的活動裡有哪些組合被暫停」。
    """
    # 廣告依 adset_id 分組；缺 adset_id 的廣告依 campaign_id 歸到「未分組」佔位組合
    ads_by_adset: dict[str, list] = {}
    orphan_ads_by_campaign: dict[str | None, list] = {}
    campaign_names: dict[str | None, tuple[str | None, str | None]] = {}
    for item in items:
        campaign_names.setdefault(item.campaign_id, (item.campaign_name, item.objective))
        if item.adset_id:
            ads_by_adset.setdefault(item.adset_id, []).append(item)
        else:
            orphan_ads_by_campaign.setdefault(item.campaign_id, []).append(item)

    adsets_by_campaign: dict[str | None, list[dict]] = {}
    for adset in adsets:
        ads = ads_by_adset.pop(adset.adset_id, [])
        campaign_id = adset.campaign_id or (ads[0].campaign_id if ads else None)
        node = adset_node(adset, sort_by_spend([ad_node(a) for a in ads]))
        adsets_by_campaign.setdefault(campaign_id, []).append(node)

    # 有廣告但沒有廣告組合設定 → 佔位廣告組合
    for adset_id, ads in ads_by_adset.items():
        nodes = sort_by_spend([ad_node(a) for a in ads])
        adsets_by_campaign.setdefault(ads[0].campaign_id, []).append(
            _placeholder_adset(adset_id, ads[0].adset_name, nodes)
        )
    for campaign_id, ads in orphan_ads_by_campaign.items():
        nodes = sort_by_spend([ad_node(a) for a in ads])
        adsets_by_campaign.setdefault(campaign_id, []).append(_placeholder_adset(None, None, nodes))

    tree: list[dict] = []
    for campaign in campaigns:
        adset_nodes = adsets_by_campaign.pop(campaign.campaign_id, [])
        if _status_matches(campaign.effective_status, status):
            tree.append(campaign_node(campaign, sort_by_spend(adset_nodes)))

    # 有廣告組合／廣告但沒有行銷活動設定 → 佔位行銷活動（狀態未知，只在 other 或不篩時出現）
    if _status_matches(None, status):
        for campaign_id, adset_nodes in adsets_by_campaign.items():
            name, objective = campaign_names.get(campaign_id, (None, None))
            tree.append(_placeholder_campaign(campaign_id, name, objective, sort_by_spend(adset_nodes)))

    return sort_by_spend(tree)
