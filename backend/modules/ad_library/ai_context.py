"""
Ad Library - 給 AI 用的精簡脈絡（docs/74 第 4 階段第 12 步）

原則（docs/74「/ai-context 輸出原則」）：
- 以行銷活動為單位輸出；不指定行銷活動時只回各行銷活動摘要，避免單次資料過大。
- 文案與素材只在 `contents` 字典列一次，廣告以短代號參照（P1 主要文字、H1 標題、
  D1 說明、I1 圖片、V1 影片），不讓同一段文案在多則廣告重複出現。
- 廣告組合只帶 targeting 摘要；預算換算成一般金額並附幣別。
- 附上比對組（素材測試／文案測試／重複投放）與成效歸屬前提。

純函數、不碰 DB。
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .comparisons import ATTRIBUTION_NOTE, build_comparisons
from .currency import to_major_unit

SCHEMA_VERSION = 1
MAX_ADS_PER_CAMPAIGN = 300
REF_PREFIX = {"primary_text": "P", "headline": "H", "description": "D", "image": "I", "video": "V"}
TEXT_KINDS = ("primary_text", "headline", "description")

ASSET_RESULTS_NOTE = (
    "asset_results 為 Meta 依元件拆分的動態素材成效，可直接比較同一則廣告內各元件；"
    "Meta 只提供曝光、點擊、花費、觸及，ctr 為 clicks ÷ impressions × 100。"
)
COMPARISON_SCOPE_NOTE = (
    "只有 comparisons[] 內的組（固定一個變因）與 asset_results 可以下勝負結論；"
    "其他廣告之間文案與素材都不同（或為素材無法識別的商品目錄廣告），只能排序描述，不能判斷優劣原因。"
)
MISSING_SETTINGS_NOTE = "部分行銷活動或廣告組合的設定尚未抓取（settings_available=false），請勿推論其設定。"
METRICS_NOTE = "成效為帳號建立以來的累計數字（date_preset=maximum），spend 為帳號幣別的一般金額。"


def _metrics(impressions, clicks, spend, reach=None) -> dict[str, Any]:
    impressions = int(impressions or 0)
    clicks = int(clicks or 0)
    out = {
        "impressions": impressions,
        "clicks": clicks,
        "spend": round(float(spend or 0.0), 2),
        "ctr": round(clicks / impressions * 100, 2) if impressions else 0.0,
    }
    if reach is not None:
        out["reach"] = int(reach or 0)
    return out


def _row_metrics(row) -> dict[str, Any]:
    return _metrics(row.impressions, row.clicks, row.spend, row.reach)


def _budget(row) -> dict[str, Any]:
    return {
        "currency": row.currency,
        "daily_budget": to_major_unit(row.daily_budget, row.currency),
        "lifetime_budget": to_major_unit(row.lifetime_budget, row.currency),
    }


def _compact(d: dict) -> dict:
    """去掉 None 與空集合，縮小輸出。"""
    return {k: v for k, v in d.items() if v not in (None, [], {}, "")}


class _RefTable:
    """content_id → 短代號（P1、I2…），依首次出現順序編號。"""

    def __init__(self, contents: dict[str, Any]):
        self._contents = contents
        self._refs: dict[str, str] = {}
        self._counters: dict[str, int] = defaultdict(int)
        self.entries: dict[str, dict] = {}

    def ref(self, content_id: str) -> str | None:
        if content_id in self._refs:
            return self._refs[content_id]
        content = self._contents.get(content_id)
        if content is None:
            return None
        prefix = REF_PREFIX.get(content.kind, "X")
        self._counters[prefix] += 1
        ref = f"{prefix}{self._counters[prefix]}"
        self._refs[content_id] = ref
        entry = {"kind": content.kind}
        if content.kind in TEXT_KINDS:
            entry["text"] = content.text_value
        elif content.kind == "image":
            entry["image_hash"] = content.image_hash
        elif content.kind == "video":
            entry["video_id"] = content.video_id
        self.entries[ref] = entry
        return ref


def _campaign_settings(campaign) -> dict[str, Any]:
    return _compact({
        "campaign_id": campaign.campaign_id,
        "name": campaign.name,
        "settings_available": True,
        "objective": campaign.objective,
        "effective_status": campaign.effective_status,
        "buying_type": campaign.buying_type,
        "bid_strategy": campaign.bid_strategy,
        "smart_promotion_type": campaign.smart_promotion_type,
        "budget_level": "campaign" if (campaign.daily_budget or campaign.lifetime_budget) else "adset",
        **_budget(campaign),
        "special_ad_categories": campaign.special_ad_categories or [],
        "start_time": campaign.start_time.isoformat() if campaign.start_time else None,
        "stop_time": campaign.stop_time.isoformat() if campaign.stop_time else None,
        "metrics": _row_metrics(campaign),
    })


def _adset_settings(adset) -> dict[str, Any]:
    summary = _compact(dict(adset.targeting_summary or {}))
    if not (adset.targeting_summary or {}).get("advantage_audience"):
        summary.pop("advantage_audience", None)
    return _compact({
        "adset_id": adset.adset_id,
        "name": adset.name,
        "settings_available": True,
        "effective_status": adset.effective_status,
        "optimization_goal": adset.optimization_goal,
        "billing_event": adset.billing_event,
        "bid_strategy": adset.bid_strategy,
        "bid_amount": to_major_unit(adset.bid_amount, adset.currency),
        "destination_type": adset.destination_type,
        "is_dynamic_creative": adset.is_dynamic_creative,
        **_budget(adset),
        "targeting": summary,
        "promoted_object": adset.promoted_object,
        "metrics": _row_metrics(adset),
    })


def build_campaign_context(
    *,
    account_id: str,
    currency: str | None,
    campaign_id: str,
    campaign,
    adsets: list,
    items: list,
    links: list[tuple[str, str, int]],
    contents: dict[str, Any],
    asset_insights: list,
) -> dict[str, Any]:
    """單一行銷活動的完整脈絡。

    Args:
        campaign: AdLibraryCampaign 或 None（設定尚未抓取）
        links: [(item_id, content_id, position)]
        contents: {content_id: AdLibraryContent}
        asset_insights: [AdLibraryAssetInsight]（此行銷活動內廣告的元件成效）
    """
    notes = [METRICS_NOTE, ATTRIBUTION_NOTE, COMPARISON_SCOPE_NOTE]
    refs = _RefTable(contents)

    items = sorted(items, key=lambda i: i.spend or 0.0, reverse=True)
    truncated = len(items) > MAX_ADS_PER_CAMPAIGN
    if truncated:
        notes.append(f"此行銷活動共 {len(items)} 則廣告，只列出花費最高的 {MAX_ADS_PER_CAMPAIGN} 則。")
        items = items[:MAX_ADS_PER_CAMPAIGN]

    links_by_item: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for item_id, content_id, position in links:
        links_by_item[item_id].append((position, content_id))

    insights_by_ad: dict[str, list] = defaultdict(list)
    for insight in asset_insights:
        insights_by_ad[insight.ad_id].append(insight)

    def item_refs(item) -> dict[str, list[str]]:
        by_kind: dict[str, list[str]] = defaultdict(list)
        for _position, content_id in sorted(links_by_item.get(item.id, [])):
            ref = refs.ref(content_id)
            if ref:
                by_kind[contents[content_id].kind].append(ref)
        return by_kind

    ad_entries: dict[str, dict] = {}
    for item in items:
        by_kind = item_refs(item)
        entry = _compact({
            "ad_id": item.ad_id,
            "name": item.ad_name,
            "effective_status": item.effective_status,
            "media_type": item.media_type,
            "copy": _compact({k: by_kind.get(k) for k in TEXT_KINDS}),
            "media": by_kind.get("image", []) + by_kind.get("video", []),
            "cta": item.cta_types or [],
            "link_url": item.link_url,
            "metrics": _row_metrics(item),
        })
        results = []
        for insight in sorted(insights_by_ad.get(item.ad_id, []), key=lambda i: i.impressions or 0, reverse=True):
            ref = refs.ref(insight.content_id)
            if ref:
                results.append({"ref": ref, **_metrics(insight.impressions, insight.clicks, insight.spend)})
        if results:
            entry["asset_results"] = results
        ad_entries[item.id] = entry

    adset_nodes: dict[str | None, dict] = {}
    for adset in adsets:
        adset_nodes[adset.adset_id] = {**_adset_settings(adset), "ads": []}
    for item in items:
        node = adset_nodes.get(item.adset_id)
        if node is None:
            node = adset_nodes[item.adset_id] = {
                "adset_id": item.adset_id, "name": item.adset_name, "settings_available": False, "ads": [],
            }
        node["ads"].append(ad_entries[item.id])

    if campaign is None or any(not n.get("settings_available") for n in adset_nodes.values()):
        notes.append(MISSING_SETTINGS_NOTE)
    if asset_insights:
        notes.append(ASSET_RESULTS_NOTE)

    comparisons = []
    for scope in ("adset", "campaign"):
        result = build_comparisons(items, scope=scope)
        for group in result["groups"]:
            if scope == "campaign" and _single_adset(group):
                continue  # 已在廣告組合範圍列過
            comparisons.append(_comparison_entry(group, ad_entries))

    campaign_node = (
        _campaign_settings(campaign)
        if campaign is not None
        else _compact({
            "campaign_id": campaign_id,
            "name": items[0].campaign_name if items else None,
            "objective": items[0].objective if items else None,
            "settings_available": False,
        })
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "account": _compact({"account_id": account_id, "currency": currency}),
        "campaign": campaign_node,
        "adsets": sorted(
            adset_nodes.values(),
            key=lambda n: (n.get("metrics") or _sum_ads(n["ads"]))["spend"],
            reverse=True,
        ),
        "contents": refs.entries,
        "comparisons": comparisons,
        "notes": notes,
    }


def _sum_ads(ads: list[dict]) -> dict[str, Any]:
    return _metrics(
        sum(a["metrics"]["impressions"] for a in ads),
        sum(a["metrics"]["clicks"] for a in ads),
        sum(a["metrics"]["spend"] for a in ads),
    )


def _single_adset(group: dict) -> bool:
    adsets = {ad.get("adset_id") for v in group["variants"] for ad in v["ads"]}
    return len(adsets) <= 1


def _comparison_entry(group: dict, ad_entries: dict[str, dict]) -> dict[str, Any]:
    """把 comparisons.py 的組轉成以 ref 表示的精簡版本。"""
    relation = group["relation"]

    def refs_of(ad_row_id: str, dimension: str) -> list[str]:
        entry = ad_entries.get(ad_row_id) or {}
        if dimension == "copy":
            return [r for k in TEXT_KINDS for r in (entry.get("copy") or {}).get(k, [])]
        return list(entry.get("media") or [])

    first_ad = group["variants"][0]["ads"][0]["id"]
    if relation == "media_test":
        fixed, variable = refs_of(first_ad, "copy"), "media"
    elif relation == "copy_test":
        fixed, variable = refs_of(first_ad, "media"), "copy"
    else:
        fixed, variable = refs_of(first_ad, "copy") + refs_of(first_ad, "media"), None

    variants = []
    for v in group["variants"]:
        variant = {"ad_ids": [a["ad_id"] for a in v["ads"]], "metrics": _metrics(
            v["metrics"]["impressions"], v["metrics"]["clicks"], v["metrics"]["spend"]
        )}
        if variable:
            variant["refs"] = refs_of(v["ads"][0]["id"], variable)
        variants.append(variant)

    scope = group["scope"]
    return {
        "relation": relation,
        "scope": {"level": scope["level"], "id": scope["id"], "name": scope["name"]},
        "fixed_refs": fixed,
        "variants": variants,
    }


def build_account_summary(*, account_id: str, currency: str | None, tree: list[dict], items: list) -> dict[str, Any]:
    """不指定行銷活動時：各行銷活動的摘要與比對組數量，讓 AI（或使用者）挑要深入的行銷活動。"""
    comparison_counts: dict[str | None, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for scope in ("adset", "campaign"):
        for group in build_comparisons(items, scope=scope)["groups"]:
            if scope == "campaign" and _single_adset(group):
                continue
            campaign_id = group["variants"][0]["ads"][0]["campaign_id"]
            comparison_counts[campaign_id][group["relation"]] += 1

    campaigns = []
    for node in tree:
        metrics = node["metrics"]
        campaigns.append(_compact({
            "campaign_id": node.get("campaign_id"),
            "name": node.get("name"),
            "settings_available": node.get("settings_available"),
            "objective": node.get("objective"),
            "effective_status": node.get("effective_status"),
            "budget_level": node.get("budget_level"),
            "currency": node.get("currency"),
            "daily_budget": node.get("daily_budget"),
            "lifetime_budget": node.get("lifetime_budget"),
            "adset_count": len(node["adsets"]),
            "ad_count": sum(len(s["ads"]) for s in node["adsets"]),
            "metrics": _metrics(metrics["impressions"], metrics["clicks"], metrics["spend"], metrics.get("reach")),
            "comparisons": dict(comparison_counts.get(node.get("campaign_id"), {})),
        }))
    return {
        "schema_version": SCHEMA_VERSION,
        "account": _compact({"account_id": account_id, "currency": currency}),
        "campaigns": campaigns,
        "notes": [METRICS_NOTE, "請以 campaign_id 呼叫 /ai-context 取得單一行銷活動的完整脈絡。"],
    }
