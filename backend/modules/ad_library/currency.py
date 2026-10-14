"""
Ad Library - 預算金額換算（docs/74）

Marketing API 的 daily_budget / lifetime_budget / bid_amount 以帳號幣別的
「最小單位」回傳，換算倍數依 Meta 公布的幣別 offset：
https://developers.facebook.com/docs/marketing-api/currencies

offset 為 1 的幣別（含 TWD、JPY、KRW）不除以 100，其餘幣別除以 100。
"""

from __future__ import annotations

# 2026-10-14 對照 Meta 官方幣別表，offset 為 1 的幣別
OFFSET_ONE_CURRENCIES = frozenset({
    "CLP", "COP", "CRC", "HUF", "ISK", "IDR", "JPY", "KRW", "PYG", "TWD", "VND",
})


def currency_offset(currency: str | None) -> int:
    return 1 if (currency or "").upper() in OFFSET_ONE_CURRENCIES else 100


def to_major_unit(amount: int | None, currency: str | None) -> float | None:
    """最小單位 → 一般金額；None 保持 None（例如 ABO 時行銷活動沒有預算）。"""
    if amount is None:
        return None
    return amount / currency_offset(currency)
