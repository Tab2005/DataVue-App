"""Pure Facebook Ads action parsing and formatting helpers."""

from __future__ import annotations


def process_actions(data):
    """
    Parses 'actions' and 'action_values' lists into a dictionary.
    e.g. actions: [{'action_type': 'purchase', 'value': '10'}] -> {'purchase': 10}
    """
    result = {}

    # Process Counts
    if "actions" in data:
        for item in data["actions"]:
            result[item["action_type"]] = float(item["value"])

    # Process Values (Revenue)
    # We append '_val' suffix for distinction, e.g. 'purchase_val'
    if "action_values" in data:
        for item in data["action_values"]:
            result[f"{item['action_type']}_val"] = float(item["value"])

    return result


def get_video_action_value(row, field_name):
    """
    Helper to extract video action values from Facebook API response.
    Video actions are returned as a list: [{'action_type': 'video_view', 'value': '100'}]
    """
    try:
        action_list = row.get(field_name, [])
        if action_list and isinstance(action_list, list) and len(action_list) > 0:
            return float(action_list[0].get("value", 0))
        return 0
    except (TypeError, ValueError, IndexError):
        return 0


def calculate_change(current, previous):
    """
    Returns string percentage change. e.g. "+15.0%", "-1.2%", or "0%"
    """
    if previous == 0:
        return "+0%" if current == 0 else "+100%" # Simplified infinity handling

    change = ((current - previous) / previous) * 100
    sign = "+" if change > 0 else ""
    return f"{sign}{change:.2f}%"


def format_kpi(cur, prev):
    # Helper to safely get float values
    def get_val(d, key, default=0.0):
        return float(d.get(key, default))

    # Process complex action lists
    cur_acts = process_actions(cur)
    prev_acts = process_actions(prev)

    # metrics = [] -> Changed to Dict
    metrics = {}

    def add_metric(label, key, source_key=None, is_currency=False, is_action=False, action_key=None, is_roas=False, is_percent=False, is_inverse=False):
        # 1. Get Values
        if is_action:
            c_val = cur_acts.get(action_key, 0)
            p_val = prev_acts.get(action_key, 0)
        elif is_roas:
            # ROAS is usually 'purchase_roas' list
            c_roas_list = cur.get("purchase_roas", [])
            p_roas_list = prev.get("purchase_roas", [])
            c_val = float(c_roas_list[0]["value"]) if c_roas_list else 0.0
            p_val = float(p_roas_list[0]["value"]) if p_roas_list else 0.0
        else:
            # Use source_key if provided, else key
            fetch_key = source_key if source_key else key
            c_val = get_val(cur, fetch_key)
            p_val = get_val(prev, fetch_key)

        # 2. Calculate Diff and Percent
        diff = c_val - p_val
        if p_val == 0:
            percent = 100.0 if c_val > 0 else 0.0
        else:
            percent = (diff / p_val) * 100.0

        # 3. Format Strings
        def fmt_num(n, for_display=True):
            if is_currency: 
                return f"${n:,.0f}" if for_display else n 
            if is_percent: 
                return f"{n:.2f}%" if for_display else n
            if is_roas: 
                return f"{n:.2f}" if for_display else n
            return f"{n:,.0f}" if for_display else n

        # Value Formatting
        val_str = fmt_num(c_val)

        # Prev Value (in parens)
        prev_str = f"({fmt_num(p_val)})"

        # Diff String
        diff_str = fmt_num(diff)
        if is_currency: diff_str = diff_str.replace('$-', '-$') 
        if diff > 0: diff_str = "+" + diff_str

        # Change String (Percent)
        if percent > 0:
            change_str = f"+{abs(percent):.1f}%"
        elif percent < 0:
            change_str = f"-{abs(percent):.1f}%"
        else:
            change_str = "0.0%"

        # Boolean for color (Higher is better, unless inverse)
        is_increase = (diff > 0)

        metrics[key] = {
            "label": label,
            "value": val_str,
            "previous": prev_str,
            "diff": diff_str,
            "change": change_str,
            "is_increase": is_increase,
            "raw_value": c_val
        }

    # Add Metrics (Keys must match Frontend kpiKeys)
    # Helper to calculate derived metric
    def calc_derived(numerator_key, denominator_key, multiplier=1.0, default=0.0):
        num = get_val(cur, numerator_key)
        den = get_val(cur, denominator_key)
        return (num / den * multiplier) if den > 0 else default

    def calc_derived_prev(numerator_key, denominator_key, multiplier=1.0, default=0.0):
        num = get_val(prev, numerator_key)
        den = get_val(prev, denominator_key)
        return (num / den * multiplier) if den > 0 else default

    # Base Metrics
    add_metric("Spend", "spend", is_currency=True, is_inverse=True)
    add_metric("Impressions", "impressions")
    add_metric("Link Clicks", "link_clicks", source_key="inline_link_clicks")
    add_metric("Purchases", "purchases", is_action=True, action_key="purchase")
    add_metric("Add to Cart", "add_to_cart", is_action=True, action_key="add_to_cart")

    # Derived Metrics - Manually Calculate to match Table logic

    # 1. CPM = Spend / Impressions * 1000
    cur["cpm_calc"] = calc_derived("spend", "impressions", 1000.0)
    prev["cpm_calc"] = calc_derived_prev("spend", "impressions", 1000.0)
    add_metric("CPM", "cpm", source_key="cpm_calc", is_currency=True, is_inverse=True)

    # 2. CPC = Spend / Link Clicks
    cur["cpc_calc"] = calc_derived("spend", "inline_link_clicks")
    prev["cpc_calc"] = calc_derived_prev("spend", "inline_link_clicks")
    add_metric("CPC", "cpc", source_key="cpc_calc", is_currency=True, is_inverse=True)

    # 3. CTR = Link Clicks / Impressions * 100
    cur["ctr_calc"] = calc_derived("inline_link_clicks", "impressions", 100.0)
    prev["ctr_calc"] = calc_derived_prev("inline_link_clicks", "impressions", 100.0)
    add_metric("CTR", "ctr", source_key="ctr_calc", is_percent=True)

    # 4. ROAS = Purchase Value / Spend
    # Need to get purchase value first
    cur_purch_val = cur_acts.get("purchase_val", 0)
    prev_purch_val = prev_acts.get("purchase_val", 0)
    cur_spend = get_val(cur, "spend")
    prev_spend = get_val(prev, "spend")

    cur["roas_calc"] = (cur_purch_val / cur_spend) if cur_spend > 0 else 0.0
    prev["roas_calc"] = (prev_purch_val / prev_spend) if prev_spend > 0 else 0.0
    add_metric("ROAS", "roas", source_key="roas_calc", is_roas=True) # Use customized source_key logic modification below

    # 5. CPA = Spend / Purchases
    cur_purchases = cur_acts.get("purchase", 0)
    prev_purchases = prev_acts.get("purchase", 0)

    cur["cpa_calc"] = (cur_spend / cur_purchases) if cur_purchases > 0 else 0.0
    prev["cpa_calc"] = (prev_spend / prev_purchases) if prev_purchases > 0 else 0.0
    add_metric("CPA", "cpa", source_key="cpa_calc", is_currency=True, is_inverse=True)

    # 6. Purchase Value
    # We need to add this to metrics dict manually or via helper if we want it displayed
    # The frontend asks for specific keys. If 'purchase_value' is needed in KPI cards:
    add_metric("Purchase Value", "purchase_value", is_action=True, action_key="purchase_val", is_currency=True)

    # 7. Add to Cart Value
    add_metric("ATC Value", "atc_value", is_action=True, action_key="add_to_cart_val", is_currency=True)

    # 8. Cost Per ATC
    cur_atc = cur_acts.get("add_to_cart", 0)
    prev_atc = prev_acts.get("add_to_cart", 0)
    cur["cost_per_atc_calc"] = (cur_spend / cur_atc) if cur_atc > 0 else 0.0
    prev["cost_per_atc_calc"] = (prev_spend / prev_atc) if prev_atc > 0 else 0.0
    add_metric("Cost Per ATC", "cost_per_atc", source_key="cost_per_atc_calc", is_currency=True, is_inverse=True)

    # 9. New Clicks & CTR Metrics for KPI Cards - Ensure labels match frontend registry keys
    add_metric("unique_clicks", "unique_clicks")

    # Unique CTR = unique_clicks / reach * 100
    cur["unique_ctr_calc"] = calc_derived("unique_clicks", "reach", 100.0)
    prev["unique_ctr_calc"] = calc_derived_prev("unique_clicks", "reach", 100.0)
    add_metric("unique_ctr", "unique_ctr", source_key="unique_ctr_calc", is_percent=True)

    # Outbound Clicks
    def get_ob_val(row_data):
        ob = row_data.get("outbound_clicks", [])
        if isinstance(ob, list) and ob: return float(ob[0].get("value", 0))
        return float(ob or 0)

    cur["ob_val"] = get_ob_val(cur)
    prev["ob_val"] = get_ob_val(prev)
    add_metric("outbound_clicks", "outbound_clicks", source_key="ob_val")

    # Outbound CTR = outbound_clicks / impressions * 100
    cur["ob_ctr_calc"] = (cur["ob_val"] / get_val(cur, "impressions") * 100.0) if get_val(cur, "impressions") > 0 else 0.0
    prev["ob_ctr_calc"] = (prev["ob_val"] / get_val(prev, "impressions") * 100.0) if get_val(prev, "impressions") > 0 else 0.0
    add_metric("outbound_clicks_ctr", "outbound_clicks_ctr", source_key="ob_ctr_calc", is_percent=True)

    # Link Click CTR = inline_link_clicks / impressions * 100
    cur["link_ctr_calc"] = calc_derived("inline_link_clicks", "impressions", 100.0)
    prev["link_ctr_calc"] = calc_derived_prev("inline_link_clicks", "impressions", 100.0)
    add_metric("inline_link_click_ctr", "inline_link_click_ctr", source_key="link_ctr_calc", is_percent=True)

    return metrics


def format_charts(data_list):
    # Format for Recharts: Daily Trend
    formatted = []
    for item in data_list:
        # date_start is "YYYY-MM-DD"
        date_str = item.get("date_start", "")[5:] # Remove Year -> "MM-DD"

        # 1. Base Metrics
        row = {
            "name": date_str, 
            "spend": float(item.get("spend", 0)),
            "impressions": int(item.get("impressions", 0)),
            "link_clicks": int(item.get("inline_link_clicks", 0)),
            "ctr": float(item.get("ctr", 0)),
            "cpc": float(item.get("cpc", 0)),
            "unique_clicks": int(item.get("unique_clicks", 0)),
            "unique_ctr": float(item.get("unique_ctr", 0)),
            "outbound_clicks_ctr": float(item.get("outbound_clicks_ctr", [{}])[0].get("value", 0) if isinstance(item.get("outbound_clicks_ctr"), list) else 0),
        }

        # 2. Actions (Purchases, ATC)
        acts = process_actions(item)
        row["purchases"] = acts.get("purchase", 0)
        row["add_to_cart"] = acts.get("add_to_cart", 0)

        # 3. ROAS
        # purchase_roas is list of {action_type: 'purchase_roas', value: '...'}
        roas_list = item.get("purchase_roas", [])
        row["roas"] = float(roas_list[0].get("value", 0)) if roas_list else 0.0

        formatted.append(row)

    # Sort by date
    formatted.sort(key=lambda x: x["name"])
    return formatted


__all__ = [
    "process_actions",
    "get_video_action_value",
    "calculate_change",
    "format_kpi",
    "format_charts",
]
