"""Channel group rules for GA4 insights (docs/44)."""

from __future__ import annotations

from datetime import datetime

from ._shared import *

CHANNEL_GROUP_MATCH_TYPES = ("exact", "prefix", "contains")


def list_channel_group_rules(db, *, property_id: str, channel_dimension: str | None = None):
    return repository.list_channel_group_rules(db, property_id=property_id, channel_dimension=channel_dimension)


def upsert_channel_group_rule(
    db, *, rule_id: str | None, user_id: str, property_id: str,
    channel_dimension: str, group_label: str, match_type: str, pattern: str, priority: int,
):
    if channel_dimension not in CHANNEL_DIMENSION_MAP:
        raise ValueError(f"Unsupported channel_dimension: {channel_dimension}")
    if match_type not in CHANNEL_GROUP_MATCH_TYPES:
        raise ValueError(f"Unsupported match_type: {match_type}")

    if rule_id:
        row = repository.get_channel_group_rule(db, rule_id)
        if not row:
            return None
        row.property_id = property_id
        row.channel_dimension = channel_dimension
        row.group_label = group_label
        row.match_type = match_type
        row.pattern = pattern
        row.priority = priority
        row.updated_at = datetime.utcnow()
        db.add(row)
        return row
    return repository.create_channel_group_rule(
        db,
        property_id=property_id,
        channel_dimension=channel_dimension,
        group_label=group_label,
        match_type=match_type,
        pattern=pattern,
        priority=priority,
        created_by=user_id,
    )


def delete_channel_group_rule(db, *, rule_id: str) -> bool:
    return repository.delete_channel_group_rule(db, rule_id)


def list_channel_groups(db, *, property_id: str, channel_dimension: str):
    """依 group_label 去重列出某維度底下已定義的分組，供前端「自訂分組」
    下拉選單使用（docs/43：新增規則後自動出現在下拉裡，不用另外維護選單）。"""
    rules = repository.list_channel_group_rules(db, property_id=property_id, channel_dimension=channel_dimension)
    counts: dict[str, int] = {}
    for rule in rules:
        counts[rule.group_label] = counts.get(rule.group_label, 0) + 1
    return [
        {"group_label": label, "rule_count": count}
        for label, count in sorted(counts.items())
    ]


def get_channel_group_match_conditions(db, *, property_id: str, channel_dimension: str, group_label: str):
    """回傳某個分組底下全部規則的 (match_type, pattern)，供組 OR 篩選用
    （docs/44 步驟 4）。同一分組的規則全部都會生效（OR），不是只取第一條——
    跟到達頁/商品分類規則「依 priority 取第一個比對成功」的分類語意不同，
    這裡的 priority 只用來決定「同一原始值符合多條規則時算哪一組」。"""
    rules = repository.list_channel_group_rules(db, property_id=property_id, channel_dimension=channel_dimension)
    return [(rule.match_type, rule.pattern) for rule in rules if rule.group_label == group_label]
