"""
Contribution Module - 活動自動分組規則（docs/21 §3.3）

初版規則（來自 2026-07-06 真實驗證的分組經驗，使用者可在前端改）：
  1. 按活動名稱關鍵詞聚類（`常態`/`檔期`/`測試`/`導流`/`曝光` 等 token + 相同前綴）。
  2. 花費占比 < 3% 的活動自動併入 `G_other`。
  3. 目標組數 5–8 組；無法規則分組時退回「花費 Top 6 + 其他」。
  4. 產出存入 `contribution_campaign_groups`（`source=auto`），使用者調整後
     `source=manual`，後續分析優先用 manual。

設計原則：純函數、無 I/O；`auto_group(...)` 接受 list[dict]（campaign summaries）
與最小占比參數，回傳 list[dict]（group dicts），由 service 層決定寫庫時機。
"""

from __future__ import annotations

import re
from typing import Any

# 關鍵詞 → 組別代碼（順序敏感：先匹配先入組）
_KEYWORD_RULES: list[tuple[str, str, str]] = [
    (r"常態|永遠|always[_\- ]?on|evergreen", "G1", "主力常態"),
    (r"影片|video|reels", "G2", "主力影片"),
    (r"檔期|活動|seasonal|event|promo", "G3", "官網檔期"),
    (r"社群|social|自投|organic", "G4", "社群自投"),
    (r"大包|大包裝|retargeting|再行銷|re[_\- ]?target|rt", "G5", "大包裝再行銷"),
    (r"測試|導流|測試導流|test", "G7", "測試導流"),
    (r"曝光|reach|品牌|brand|awareness", "G6", "曝光品牌"),
]

# 共通前綴長度（提取活動名稱前 N 個中文字元做群組，例：「OB 嚴選 - 常態 A」
# 與「OB 嚴選 - 影片 B」會以「OB 嚴選」前綴聚為一組候選）
_COMMON_PREFIX_LEN = 4

# 占比下限：低於此的活動併入 G_other
DEFAULT_MIN_SPEND_SHARE = 0.03
# 目標組數區間
TARGET_GROUPS_MIN = 5
TARGET_GROUPS_MAX = 8
# 退回方案的「Top N」組數
FALLBACK_TOP_N = 6

# 群組順序（前端顯示用；不在結果中出現的組別代碼自動略過）
_GROUP_ORDER: list[str] = ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G_other"]


def _normalize_name(name: str | None) -> str:
    return (name or "").strip()


def _match_keyword(name: str) -> tuple[str, str] | None:
    """依關鍵詞規則回傳 (group_key, group_name)；無匹配回 None。"""
    for pattern, gk, gn in _KEYWORD_RULES:
        if re.search(pattern, name, re.IGNORECASE):
            return gk, gn
    return None


def _common_prefix(names: list[str]) -> str | None:
    """回傳所有名稱共有的前 N 個中文字元；不足 N 字回 None。"""
    cleaned = [_normalize_name(n) for n in names if _normalize_name(n)]
    if len(cleaned) < 2:
        return None
    first = cleaned[0]
    if len(first) < _COMMON_PREFIX_LEN:
        return None
    candidate = first[:_COMMON_PREFIX_LEN]
    if all(n.startswith(candidate) for n in cleaned):
        return candidate
    return None


def auto_group(
    campaigns: list[dict[str, Any]],
    *,
    min_spend_share: float = DEFAULT_MIN_SPEND_SHARE,
) -> list[dict[str, Any]]:
    """依規則產生 auto 分組結果。

    參數：
      campaigns: list of dict，必含 keys `campaign_id` / `campaign_name` / `spend`。
                 spend 為該活動在分析期間的總花費；零或負值視為無花費。
      min_spend_share: 低於此占比的活動併入 G_other（預設 3%）。

    回傳：list of group dict，每個 dict 含 keys
      `group_key` / `group_name` / `campaign_ids` / `source`。
      `source` 固定為 'auto'。
    """
    # 防呆：空清單或全部零花費 → 一個 G_other 空組
    if not campaigns:
        return [
            {
                "group_key": "G_other",
                "group_name": "其他",
                "campaign_ids": [],
                "source": "auto",
            }
        ]

    # 按 spend 由大到小排序（已由 caller 保證則略過）
    sorted_camps = sorted(
        campaigns, key=lambda c: float(c.get("spend") or 0.0), reverse=True
    )
    total_spend = sum(float(c.get("spend") or 0.0) for c in sorted_camps)
    if total_spend <= 0:
        return [
            {
                "group_key": "G_other",
                "group_name": "其他",
                "campaign_ids": [str(c["campaign_id"]) for c in sorted_camps],
                "source": "auto",
            }
        ]

    # Step 1：分桶（按關鍵詞 + 共同前綴）
    buckets: dict[str, dict[str, Any]] = {}
    for c in sorted_camps:
        cid = str(c.get("campaign_id"))
        name = _normalize_name(c.get("campaign_name"))
        matched = _match_keyword(name)
        if matched is not None:
            gk, gn = matched
        else:
            # 嘗試以共同前綴聚類（同一品牌的子活動）
            prefix = _common_prefix([name])
            if prefix:
                gk = f"G_prefix_{prefix}"
                gn = f"前綴 {prefix}"
            else:
                gk = "G_other"
                gn = "其他"
        bucket = buckets.setdefault(
            gk, {"group_key": gk, "group_name": gn, "campaign_ids": []}
        )
        bucket["campaign_ids"].append(cid)

    # Step 2：低占比小活動併入 G_other（不論原本分到哪）
    g_other = buckets.setdefault(
        "G_other", {"group_key": "G_other", "group_name": "其他", "campaign_ids": []}
    )
    final: dict[str, dict[str, Any]] = {}
    for gk, b in buckets.items():
        kept_ids: list[str] = []
        for cid in b["campaign_ids"]:
            spend = _lookup_spend(cid, sorted_camps)
            share = spend / total_spend
            if share < min_spend_share:
                g_other["campaign_ids"].append(cid)
            else:
                kept_ids.append(cid)
        if kept_ids:
            final[gk] = {
                "group_key": gk,
                "group_name": b["group_name"],
                "campaign_ids": kept_ids,
            }

    # 若所有活動都低於門檻，強制將花費最大者升為 G1 以保證至少一組
    if not final:
        top = sorted_camps[0]
        final["G1"] = {
            "group_key": "G1",
            "group_name": "主力（自動）",
            "campaign_ids": [str(top["campaign_id"])],
        }
        g_other["campaign_ids"] = [
            str(c["campaign_id"]) for c in sorted_camps if c["campaign_id"] != top["campaign_id"]
        ]

    if g_other["campaign_ids"]:
        final["G_other"] = g_other

    # Step 3：組數收斂至 [TARGET_GROUPS_MIN, TARGET_GROUPS_MAX]
    final_list = list(final.values())
    if len(final_list) > TARGET_GROUPS_MAX:
        # 將花費最小的組別（不含 G_other）併入 G_other
        final_list = sorted(final_list, key=lambda g: _group_spend(g, sorted_camps), reverse=True)
        head = final_list[: TARGET_GROUPS_MAX - 1]
        tail = final_list[TARGET_GROUPS_MAX - 1 :]
        other_ck = {c for g in tail for c in g["campaign_ids"]}
        g_other = next(
            (g for g in head if g["group_key"] == "G_other"),
            {"group_key": "G_other", "group_name": "其他", "campaign_ids": []},
        )
        g_other["campaign_ids"] = sorted(other_ck | set(g_other["campaign_ids"]))
        if not g_other["campaign_ids"]:
            head = [g for g in head if g["group_key"] != "G_other"]
        else:
            head = [g for g in head if g["group_key"] != "G_other"] + [g_other]
        final_list = head
    elif 0 < len(final_list) < TARGET_GROUPS_MIN:
        # 組數過少：嘗試以前綴細分最大組
        final_list = _split_largest_by_prefix(final_list, sorted_camps)

    # 依既定順序排序；非預期 group_key 維持原順序
    final_list = _sort_groups(final_list)

    # 標 source
    for g in final_list:
        g["source"] = "auto"
    return final_list


def _lookup_spend(campaign_id: str, campaigns: list[dict[str, Any]]) -> float:
    for c in campaigns:
        if str(c.get("campaign_id")) == campaign_id:
            return float(c.get("spend") or 0.0)
    return 0.0


def _group_spend(group: dict[str, Any], campaigns: list[dict[str, Any]]) -> float:
    return sum(_lookup_spend(cid, campaigns) for cid in group["campaign_ids"])


def _split_largest_by_prefix(
    groups: list[dict[str, Any]],
    campaigns: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """組數過少時，把最大組依名稱共同前綴拆成 2 組。"""
    if not groups:
        return groups
    biggest = max(groups, key=lambda g: _group_spend(g, campaigns))
    if len(biggest["campaign_ids"]) < 2:
        return groups
    name_by_id = {
        str(c["campaign_id"]): _normalize_name(c.get("campaign_name"))
        for c in campaigns
    }
    members = [(cid, name_by_id.get(cid, "")) for cid in biggest["campaign_ids"]]
    # 嘗試尋找可區分子集的前綴：取所有名稱的第一個 token（常見格式：品牌 - 系列）
    tokens: dict[str, list[str]] = {}
    for cid, name in members:
        if not name:
            continue
        # 取「-」或「_」分隔的第一段；中文名直接取前 2 字
        parts = re.split(r"[\-_|/]", name, maxsplit=1)
        token = parts[0].strip()[:2] if parts else name[:2]
        tokens.setdefault(token, []).append(cid)
    if len(tokens) < 2:
        return groups
    # 取兩個最大子集
    top_two = sorted(tokens.values(), key=len, reverse=True)[:2]
    if min(len(t) for t in top_two) < 1:
        return groups
    new_groups = [g for g in groups if g is not biggest]
    for idx, cids in enumerate(top_two, start=1):
        new_groups.append(
            {
                "group_key": f"{biggest['group_key']}_{idx}",
                "group_name": f"{biggest['group_name']}（{idx}）",
                "campaign_ids": cids,
            }
        )
    # 漏網的活動仍放回原組
    leftover = [cid for cid in biggest["campaign_ids"] if cid not in {c for t in top_two for c in t}]
    if leftover:
        new_groups.append(
            {
                "group_key": f"{biggest['group_key']}_misc",
                "group_name": f"{biggest['group_name']}（其他）",
                "campaign_ids": leftover,
            }
        )
    return new_groups


def _sort_groups(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """依既定組別順序排序，未知 group_key 維持原順序接在尾端。"""
    order_index = {k: i for i, k in enumerate(_GROUP_ORDER)}
    return sorted(groups, key=lambda g: (order_index.get(g["group_key"], 999), g["group_key"]))


def validate_manual_groups(
    existing_campaign_ids: set[str],
    submitted_groups: list[dict[str, Any]],
) -> tuple[list[str], list[str]]:
    """驗證使用者手動提交的 groups 合法性。

    規則（拋 422 由 router 翻譯）：
      1. group_key 不可為空、不可重複。
      2. campaign_ids 不可為空、不可包含不屬於該帳戶的活動 ID。
      3. 全部 submitted campaign_ids 必須 == existing_campaign_ids（不丟失、不新增）。

    回傳 (errors, missing_ids)：
      errors 為人類可讀錯誤訊息 list；missing_ids 為存在但未分配的 campaign_id。
    """
    errors: list[str] = []
    missing = set(existing_campaign_ids)

    seen_keys: set[str] = set()
    submitted_ids: set[str] = set()
    for g in submitted_groups:
        gk = (g.get("group_key") or "").strip()
        gn = (g.get("group_name") or "").strip()
        cids = [str(x) for x in (g.get("campaign_ids") or [])]
        if not gk:
            errors.append("group_key 不可為空")
            continue
        if gk in seen_keys:
            errors.append(f"group_key 重複：{gk}")
        seen_keys.add(gk)
        if not gn:
            errors.append(f"group_name 不可為空（{gk}）")
        if not cids:
            errors.append(f"campaign_ids 不可為空（{gk}）")
        for cid in cids:
            if cid not in existing_campaign_ids:
                errors.append(f"活動 {cid} 不屬於此帳戶")
            elif cid in submitted_ids:
                errors.append(f"活動 {cid} 同時出現在多個組別中")
            submitted_ids.add(cid)
            missing.discard(cid)

    if missing:
        errors.append(f"以下活動未分配：{sorted(missing)}")

    return errors, sorted(missing)


__all__ = [
    "DEFAULT_MIN_SPEND_SHARE",
    "auto_group",
    "validate_manual_groups",
]
