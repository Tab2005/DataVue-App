# backend/services/report_service.py
"""
Report Generation Service
封裝週報的核心產生與計算邏輯，支援 API 調用與背景排程。
"""

import json
import logging
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from database import WeeklyReport, User

logger = logging.getLogger(__name__)

async def generate_report_content(
    db: Session,
    ad_account_id: str,
    since: str,
    until: str,
    breakdown: str,
    selected_metrics: list,
    google_id: str,
    team_id: str | None = None,
    module_type: str = "fb_ads",
):
    """
    核心報表數據產生成邏輯
    """
    if module_type == "ga4":
        from ga4_service import GA4Service
        user = db.query(User).filter(User.google_id == google_id).first()
        if not user:
            raise Exception("User not found for GA4 authentication")
            
        return await GA4Service.get_weekly_report_data(
            user=user,
            property_id=ad_account_id,
            since=since,
            until=until,
            selected_metrics=selected_metrics,
            db=db
        )

    # --- 以下為 FB 廣告邏輯 ---
    custom_fields = ",".join(selected_metrics)

    # 推算前一期日期 (Comparison Period)
    since_dt = datetime.strptime(since, '%Y-%m-%d')
    until_dt = datetime.strptime(until, '%Y-%m-%d')
    duration = (until_dt - since_dt).days + 1
    prev_until = (since_dt - timedelta(days=1)).strftime('%Y-%m-%d')
    prev_since = (since_dt - timedelta(days=duration)).strftime('%Y-%m-%d')

    # 1. 抓取資料
    from modules.fb_ads.analytics_service import get_custom_report
    from modules.fb_ads.trends_service import get_analytics_trend

    # 抓取明細 (及時段總計)
    current_rows = await get_custom_report(
        account_id=ad_account_id,
        since=since,
        until=until,
        user_id=google_id,
        level=breakdown or "campaign",
        team_id=team_id,
        custom_fields=custom_fields
    )

    # 抓取趨勢 (含對比)
    trend_data = await get_analytics_trend(
        account_id=ad_account_id,
        user_id=google_id,
        since=since,
        until=until,
        prev_since=prev_since,
        prev_until=prev_until,
        team_id=team_id,
    )

    if current_rows is None:
        raise Exception("Failed to fetch FB data")

    # 2. 數據彙整 (Aggregation)
    def _sum_metrics(rows):
        s = {
            "spend": 0.0, "impressions": 0, "clicks": 0, "link_clicks": 0, "reach": 0,
            "purchases": 0, "purchase_value": 0.0, "add_to_cart": 0, "view_content": 0,
            "initiate_checkout": 0, "add_payment_info": 0,
            "post_engagement": 0, "post_reactions": 0, "post_comments": 0, "post_shares": 0,
            "video_views": 0, "atc_value": 0.0, "messenger_replies": 0, "leads": 0
        }
        for row in rows:
            for k in s.keys():
                val = row.get(k, 0)
                if val is not None:
                    s[k] += float(val)
        
        # 計算比率指標 (Derivatives)
        s["ctr"] = (s["link_clicks"] / s["impressions"] * 100) if s["impressions"] > 0 else 0
        
        # 優先使用 clicks (全部點擊) 計算 CPC，若為 0 則改用 link_clicks (連結點擊) 確保不為 0
        if s["clicks"] > 0:
            s["cpc"] = s["spend"] / s["clicks"]
        elif s["link_clicks"] > 0:
            s["cpc"] = s["spend"] / s["link_clicks"]
        else:
            s["cpc"] = 0
            
        s["cpm"] = (s["spend"] / s["impressions"] * 1000) if s["impressions"] > 0 else 0
        s["roas"] = s["purchase_value"] / s["spend"] if s["spend"] > 0 else 0
        s["cpa"] = s["spend"] / s["purchases"] if s["purchases"] > 0 else 0
        s["cvr"] = (s["purchases"] / s["link_clicks"] * 100) if s["link_clicks"] > 0 else 0
        s["frequency"] = (s["impressions"] / s["reach"]) if s["reach"] > 0 else 0
        
        # Funnel Metrics
        s["view_to_cart"] = (s["add_to_cart"] / s["view_content"] * 100) if s["view_content"] > 0 else 0
        s["cart_conversion"] = (s["purchases"] / s["add_to_cart"] * 100) if s["add_to_cart"] > 0 else 0
        s["cart_dropoff"] = (100 - s["cart_conversion"]) if s["add_to_cart"] > 0 else 0
        s["cart_value_realization"] = (s["purchase_value"] / s["atc_value"] * 100) if s["atc_value"] > 0 else 0
        
        # Other
        s["cost_per_atc"] = s["spend"] / s["add_to_cart"] if s["add_to_cart"] > 0 else 0
        s["cost_per_lead"] = s["spend"] / s["leads"] if s["leads"] > 0 else 0
        
        return s

    summary = _sum_metrics(current_rows)
    
    # 從趨勢資料中提取前期總計
    prev_summary = {}
    if trend_data:
        p_rows = []
        for d in trend_data:
            # 建立虛擬 row 來複用 _sum_metrics 
            p_rows.append({k.replace("_prev", ""): v for k, v in d.items() if "_prev" in k})
        prev_summary = _sum_metrics(p_rows)

    return {
        "summary": summary,
        "prev_summary": prev_summary,
        "trends": trend_data or [],
        "table_data": current_rows
    }

async def trigger_manual_generate(db: Session, report_id: str, google_id: str):
    """
    手動觸發產生
    """
    report = db.query(WeeklyReport).filter(WeeklyReport.id == report_id).first()
    if not report:
        raise Exception("Report not found")

    metrics_list = json.loads(report.selected_metrics)
    
    structured_data = await generate_report_content(
        db=db,
        ad_account_id=report.ad_account_id,
        since=report.date_since,
        until=report.date_until,
        breakdown=report.breakdown,
        selected_metrics=metrics_list,
        google_id=google_id,
        team_id=report.team_id,
        module_type=getattr(report, 'module_type', 'fb_ads')
    )

    report.report_data = json.dumps(structured_data)
    report.status = "generated"
    report.updated_at = datetime.now(timezone.utc)
    db.commit()
    return report
