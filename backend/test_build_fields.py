
import sys
import os

# Mock METRICS_REGISTRY to test logic
METRICS_REGISTRY = {
    'spend': {'source': 'direct', 'fb_field': 'spend'},
    'impressions': {'source': 'direct', 'fb_field': 'impressions'},
    'reach': {'source': 'direct', 'fb_field': 'reach'},
    'cpp': {'source': 'calculated'},
    'cost_per_unique_click': {'source': 'calculated'},
    'cost_per_inline_link_click': {'source': 'calculated'},
    'cost_per_outbound_click': {'source': 'calculated'},
    'cost_per_conversion': {'source': 'calculated'},
    'roas': {'source': 'purchase_roas', 'fb_field': 'purchase_roas'},
    'purchases': {'source': 'actions', 'action_type': 'purchase'},
    'instant_experience_open': {'source': 'direct', 'fb_field': 'instant_experience_clicks_to_open'},
    'unique_ctr': {'source': 'direct', 'fb_field': 'unique_ctr'},
}

def build_fb_fields(custom_fields: str = None) -> str:
    base_structure = ["campaign_id", "adset_id", "ad_id", "campaign_name", "adset_name", "ad_name"]
    if not custom_fields: return None
    requested_keys = [k.strip() for k in custom_fields.split(",") if k.strip()]
    fb_fields = set(base_structure)
    for key in requested_keys:
        if key not in METRICS_REGISTRY: continue
        metric = METRICS_REGISTRY[key]
        source = metric.get('source')
        if source == 'direct':
            fb_field = metric.get('fb_field')
            if fb_field: fb_fields.add(fb_field)
        elif source == 'purchase_roas': fb_fields.add("purchase_roas")
    return ",".join(fb_fields)

test_input = "impressions,link_clicks,ctr,cpc,spend,purchases,add_to_cart,roas,reach,cpm,frequency,cpp,cost_per_unique_click,cost_per_inline_link_click,cost_per_outbound_click,cost_per_conversion,clicks,unique_clicks,outbound_clicks,unique_ctr,outbound_clicks_ctr,inline_link_click_ctr,instant_experience_open,instant_experience_start,purchase_value,atc_value,view_content,initiate_checkout,add_payment_info"
print(build_fb_fields(test_input))
