"""
Ad Library - AI 分析的脈絡準備（docs/75）

- `fit_context`：脈絡 JSON 超過字數上限時，依花費由低到高刪去廣告並加註，
  再移除沒有被引用的 contents 代號。
- `serialize` / `context_hash`：決定送給模型的實際字串與雜湊（判斷資料是否已更新）。
- `is_error_output`：AIService 以文字回報錯誤（不拋例外），據此把結果標為 failed。

純函數、不碰 DB 與網路。
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

MAX_CONTEXT_CHARS = 60_000
DEFAULT_MODEL = "deepseek/deepseek-v4-flash"
REPORT_TYPE = "ad_library_campaign"
PROMPT_CONTEXT = "廣告文案庫：單一行銷活動的結構與文案／素材測試分析"

# modules/ai_hub/service.py 以文字回報錯誤的固定開頭／片段
_ERROR_MARKERS = ("Error: No valid API Key", "[System Error during Analysis:")


def serialize(context: dict[str, Any]) -> str:
    return json.dumps(context, ensure_ascii=False, separators=(",", ":"), sort_keys=True, default=str)


def context_hash(context: dict[str, Any]) -> str:
    return hashlib.sha256(serialize(context).encode("utf-8")).hexdigest()


def _all_ads(context: dict) -> list[tuple[float, int, int]]:
    """[(spend, adset_index, ad_index)]"""
    out = []
    for si, adset in enumerate(context.get("adsets") or []):
        for ai, ad in enumerate(adset.get("ads") or []):
            out.append(((ad.get("metrics") or {}).get("spend") or 0.0, si, ai))
    return out


def _referenced_refs(context: dict) -> set[str]:
    refs: set[str] = set()
    for adset in context.get("adsets") or []:
        for ad in adset.get("ads") or []:
            for values in (ad.get("copy") or {}).values():
                refs.update(values)
            refs.update(ad.get("media") or [])
            refs.update(r["ref"] for r in ad.get("asset_results") or [])
    for group in context.get("comparisons") or []:
        refs.update(group.get("fixed_refs") or [])
        for variant in group.get("variants") or []:
            refs.update(variant.get("refs") or [])
    return refs


def fit_context(context: dict[str, Any], max_chars: int = MAX_CONTEXT_CHARS) -> dict[str, Any]:
    """回傳不超過 max_chars 的脈絡副本（盡量保留高花費廣告）。"""
    if len(serialize(context)) <= max_chars:
        return context
    fitted = copy.deepcopy(context)
    total_ads = len(_all_ads(fitted))
    removed = 0
    while len(serialize(fitted)) > max_chars:
        ads = sorted(_all_ads(fitted))
        if not ads:
            break
        # 每輪刪掉剩餘廣告的 10%（至少 1 則），避免逐則重算序列化太慢
        batch = ads[: max(1, len(ads) // 10)]
        by_adset: dict[int, set[int]] = {}
        for _spend, si, ai in batch:
            by_adset.setdefault(si, set()).add(ai)
        for si, indexes in by_adset.items():
            ads_list = fitted["adsets"][si]["ads"]
            fitted["adsets"][si]["ads"] = [ad for i, ad in enumerate(ads_list) if i not in indexes]
        removed += len(batch)
        keep = _referenced_refs(fitted)
        fitted["contents"] = {ref: c for ref, c in (fitted.get("contents") or {}).items() if ref in keep}
    if removed:
        fitted.setdefault("notes", []).append(
            f"為控制分析資料量，已省略花費最低的 {removed} 則廣告（共 {total_ads} 則）；比對組的數字仍包含這些廣告。"
        )
    return fitted


def is_error_output(text: str) -> bool:
    stripped = (text or "").strip()
    if not stripped:
        return True
    return stripped.startswith(_ERROR_MARKERS[0]) or _ERROR_MARKERS[1] in stripped
