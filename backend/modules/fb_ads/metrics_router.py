"""
Metrics Registry API Router
提供廣告指標定義的 API 端點，讓前端可動態取得指標設定。

避免前後端各自維護一份指標清單（Single Source of Truth）。
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional

from dependencies import get_current_user
from database import User

router = APIRouter(prefix="/api/metrics", tags=["Metrics"])

# ============================================================================
# 完整指標定義表（含前端顯示所需的 label、category、format 等元資料）
# ============================================================================
METRICS_REGISTRY: dict[str, dict] = {
    # --- 傳遞指標 (Delivery) ---
    "impressions": {
        "key": "impressions", "label": "曝光次數", "label_en": "Impressions",
        "category": "delivery", "type": "integer", "format": "number",
        "description": "廣告被展示的次數", "breakdown_compatible": True,
    },
    "reach": {
        "key": "reach", "label": "觸及人數", "label_en": "Reach",
        "category": "delivery", "type": "integer", "format": "number",
        "description": "看過廣告的不重複使用者數量", "breakdown_compatible": True,
    },
    "frequency": {
        "key": "frequency", "label": "頻率", "label_en": "Frequency",
        "category": "delivery", "type": "float", "format": "decimal",
        "description": "每個人平均看到廣告的次數", "breakdown_compatible": False,
    },
    "clicks": {
        "key": "clicks", "label": "點擊次數", "label_en": "Clicks",
        "category": "delivery", "type": "integer", "format": "number",
        "description": "使用者點擊廣告的次數", "breakdown_compatible": True,
    },
    "link_clicks": {
        "key": "link_clicks", "label": "連結點擊", "label_en": "Link Clicks",
        "category": "delivery", "type": "integer", "format": "number",
        "description": "使用者點擊廣告連結的次數", "breakdown_compatible": True,
    },
    "unique_clicks": {
        "key": "unique_clicks", "label": "不重複點擊", "label_en": "Unique Clicks",
        "category": "delivery", "type": "integer", "format": "number",
        "description": "點擊廣告的不重複使用者數量", "breakdown_compatible": True,
    },
    "outbound_clicks": {
        "key": "outbound_clicks", "label": "外部連結點擊", "label_en": "Outbound Clicks",
        "category": "delivery", "type": "integer", "format": "number",
        "description": "點擊到 Facebook 外部連結的次數", "breakdown_compatible": True,
    },

    # --- 成本指標 (Cost) ---
    "spend": {
        "key": "spend", "label": "花費", "label_en": "Spend",
        "category": "cost", "type": "float", "format": "currency",
        "description": "廣告投放總花費金額", "breakdown_compatible": True,
    },
    "ctr": {
        "key": "ctr", "label": "點擊率", "label_en": "CTR",
        "category": "performance", "type": "float", "format": "percentage",
        "description": "點擊次數 / 曝光次數 × 100%", "breakdown_compatible": False,
    },
    "cpc": {
        "key": "cpc", "label": "每次點擊成本", "label_en": "CPC",
        "category": "cost", "type": "float", "format": "currency",
        "description": "每次點擊的平均成本", "breakdown_compatible": False,
    },
    "cpm": {
        "key": "cpm", "label": "每千次曝光成本", "label_en": "CPM",
        "category": "cost", "type": "float", "format": "currency",
        "description": "每 1000 次曝光的平均成本", "breakdown_compatible": False,
    },
    "unique_ctr": {
        "key": "unique_ctr", "label": "不重複點擊率", "label_en": "Unique CTR",
        "category": "performance", "type": "float", "format": "percentage",
        "description": "不重複使用者點擊率", "breakdown_compatible": False,
    },
    "outbound_clicks_ctr": {
        "key": "outbound_clicks_ctr", "label": "外部連結點擊率", "label_en": "Outbound CTR",
        "category": "performance", "type": "float", "format": "percentage",
        "description": "外部連結點擊率", "breakdown_compatible": False,
    },

    # --- 轉換指標 (Conversion) ---
    "purchases": {
        "key": "purchases", "label": "購買次數", "label_en": "Purchases",
        "category": "conversion", "type": "integer", "format": "number",
        "description": "廣告帶來的購買次數", "breakdown_compatible": True,
    },
    "purchase_value": {
        "key": "purchase_value", "label": "購買金額", "label_en": "Purchase Value",
        "category": "conversion", "type": "float", "format": "currency",
        "description": "廣告帶來的購買總金額", "breakdown_compatible": True,
    },
    "roas": {
        "key": "roas", "label": "廣告投資回報率", "label_en": "ROAS",
        "category": "conversion", "type": "float", "format": "multiplier",
        "description": "廣告帶來的購買收益 / 廣告花費", "breakdown_compatible": False,
    },
    "cpa": {
        "key": "cpa", "label": "每次購買成本", "label_en": "CPA",
        "category": "cost", "type": "float", "format": "currency",
        "description": "每次購買的平均花費", "breakdown_compatible": False,
    },
    "add_to_cart": {
        "key": "add_to_cart", "label": "加入購物車", "label_en": "Add to Cart",
        "category": "conversion", "type": "integer", "format": "number",
        "description": "使用者加入購物車的次數", "breakdown_compatible": True,
    },
    "view_content": {
        "key": "view_content", "label": "瀏覽內容", "label_en": "View Content",
        "category": "conversion", "type": "integer", "format": "number",
        "description": "使用者瀏覽商品/內容頁面的次數", "breakdown_compatible": True,
    },
    "initiate_checkout": {
        "key": "initiate_checkout", "label": "開始結帳", "label_en": "Initiate Checkout",
        "category": "conversion", "type": "integer", "format": "number",
        "description": "使用者開始結帳流程的次數", "breakdown_compatible": True,
    },
    "leads": {
        "key": "leads", "label": "潛在客戶", "label_en": "Leads",
        "category": "conversion", "type": "integer", "format": "number",
        "description": "廣告帶來的潛在客戶數量", "breakdown_compatible": True,
    },
    "cost_per_lead": {
        "key": "cost_per_lead", "label": "每次潛客成本", "label_en": "Cost per Lead",
        "category": "cost", "type": "float", "format": "currency",
        "description": "每個潛在客戶的平均花費", "breakdown_compatible": False,
    },
    "cvr": {
        "key": "cvr", "label": "轉換率", "label_en": "CVR",
        "category": "performance", "type": "float", "format": "percentage",
        "description": "購買次數 / 連結點擊 × 100%", "breakdown_compatible": False,
    },

    # --- 參與指標 (Engagement) ---
    "post_engagement": {
        "key": "post_engagement", "label": "貼文互動", "label_en": "Post Engagement",
        "category": "engagement", "type": "integer", "format": "number",
        "description": "廣告貼文的總互動次數", "breakdown_compatible": True,
    },
    "post_comments": {
        "key": "post_comments", "label": "留言次數", "label_en": "Comments",
        "category": "engagement", "type": "integer", "format": "number",
        "description": "使用者留言的次數", "breakdown_compatible": True,
    },
    "post_shares": {
        "key": "post_shares", "label": "分享次數", "label_en": "Shares",
        "category": "engagement", "type": "integer", "format": "number",
        "description": "使用者分享廣告的次數", "breakdown_compatible": True,
    },
    "post_reactions": {
        "key": "post_reactions", "label": "按讚/表情", "label_en": "Reactions",
        "category": "engagement", "type": "integer", "format": "number",
        "description": "使用者對廣告的反應（讚、愛心等）次數", "breakdown_compatible": True,
    },

    "instagram_profile_visits": {
        "key": "instagram_profile_visits", "label": "IG 個人檔案瀏覽", "label_en": "IG Profile Visits",
        "category": "engagement", "type": "integer", "format": "number",
        "description": "廣告帶來的 Instagram 個人檔案瀏覽次數", "breakdown_compatible": True,
    },
    "instagram_profile_follow": {
        "key": "instagram_profile_follow", "label": "IG 追蹤數", "label_en": "IG Follows",
        "category": "engagement", "type": "integer", "format": "number",
        "description": "廣告帶來的 Instagram 新追蹤數", "breakdown_compatible": True,
    },

    # --- 影片指標 (Video) ---
    "video_views": {
        "key": "video_views", "label": "影片觀看", "label_en": "Video Views",
        "category": "video", "type": "integer", "format": "number",
        "description": "影片被觀看的次數", "breakdown_compatible": True,
    },

    "video_6_sec_views": {
        "key": "video_6_sec_views", "label": "6 秒影片觀看", "label_en": "6-Second Video Views",
        "category": "video", "type": "integer", "format": "number",
        "description": "影片被觀看至少 6 秒的次數", "breakdown_compatible": True,
    },
    "video_6_sec_view_rate": {
        "key": "video_6_sec_view_rate", "label": "6 秒觀看率", "label_en": "6-Second View Rate",
        "category": "video", "type": "float", "format": "percent",
        "description": "6 秒影片觀看 ÷ 曝光", "breakdown_compatible": False,
    },
    "cost_per_6_sec_video_view": {
        "key": "cost_per_6_sec_video_view", "label": "每次 6 秒觀看成本", "label_en": "Cost per 6-Second View",
        "category": "cost", "type": "float", "format": "currency",
        "description": "花費 ÷ 6 秒影片觀看", "breakdown_compatible": False,
    },

    # --- 訊息指標 (Messaging) ---
    "messaging_first_reply": {
        "key": "messaging_first_reply", "label": "私訊回覆", "label_en": "Messaging Replies",
        "category": "messaging", "type": "integer", "format": "number",
        "description": "使用者透過廣告傳送訊息的次數", "breakdown_compatible": True,
    },
    "messaging_conversation_started": {
        "key": "messaging_conversation_started", "label": "開始對話", "label_en": "Conversations Started",
        "category": "messaging", "type": "integer", "format": "number",
        "description": "廣告帶來的新對話數（7 天歸因）", "breakdown_compatible": True,
    },
    "messaging_welcome_message_view": {
        "key": "messaging_welcome_message_view", "label": "歡迎訊息瀏覽", "label_en": "Welcome Message Views",
        "category": "messaging", "type": "integer", "format": "number",
        "description": "使用者看到歡迎訊息的次數（漏斗第一層）", "breakdown_compatible": True,
    },
    "messaging_connections": {
        "key": "messaging_connections", "label": "訊息聯繫總數", "label_en": "Messaging Connections",
        "category": "messaging", "type": "integer", "format": "number",
        "description": "與商家建立訊息聯繫的總人數", "breakdown_compatible": True,
    },
    "messaging_depth_2": {
        "key": "messaging_depth_2", "label": "對話深度 2", "label_en": "Depth 2 Messages",
        "category": "messaging", "type": "integer", "format": "number",
        "description": "使用者在對話中傳送第 2 則訊息的次數", "breakdown_compatible": True,
    },
    "messaging_depth_3": {
        "key": "messaging_depth_3", "label": "對話深度 3", "label_en": "Depth 3 Messages",
        "category": "messaging", "type": "integer", "format": "number",
        "description": "使用者在對話中傳送第 3 則訊息的次數", "breakdown_compatible": True,
    },
    "messaging_conversation_replied": {
        "key": "messaging_conversation_replied", "label": "商家已回覆對話", "label_en": "Conversations Replied",
        "category": "messaging", "type": "integer", "format": "number",
        "description": "商家有回覆的對話數（7 天歸因）", "breakdown_compatible": True,
    },
    "messaging_blocks": {
        "key": "messaging_blocks", "label": "封鎖次數", "label_en": "Messaging Blocks",
        "category": "messaging", "type": "integer", "format": "number",
        "description": "使用者封鎖商家訊息的次數", "breakdown_compatible": True,
    },
    "messaging_depth_2_rate": {
        "key": "messaging_depth_2_rate", "label": "深度對話率", "label_en": "Depth 2 Rate",
        "category": "messaging", "type": "float", "format": "percent",
        "description": "對話深度 2 ÷ 開始對話", "breakdown_compatible": False,
    },
    "messaging_reply_rate": {
        "key": "messaging_reply_rate", "label": "回覆率", "label_en": "Reply Rate",
        "category": "messaging", "type": "float", "format": "percent",
        "description": "商家已回覆對話 ÷ 開始對話", "breakdown_compatible": False,
    },
    "messaging_block_rate": {
        "key": "messaging_block_rate", "label": "封鎖率", "label_en": "Block Rate",
        "category": "messaging", "type": "float", "format": "percent",
        "description": "封鎖次數 ÷ 開始對話", "breakdown_compatible": False,
    },
    "cost_per_conversation_started": {
        "key": "cost_per_conversation_started", "label": "每次開始對話成本", "label_en": "Cost per Conversation",
        "category": "cost", "type": "float", "format": "currency",
        "description": "花費 ÷ 開始對話", "breakdown_compatible": False,
    },
    "cost_per_message": {
        "key": "cost_per_message", "label": "每次訊息成本", "label_en": "Cost per Message",
        "category": "cost", "type": "float", "format": "currency",
        "description": "每次私訊回覆的平均花費", "breakdown_compatible": False,
    },
}

CATEGORIES = ["delivery", "cost", "performance", "conversion", "engagement", "video", "messaging"]


def get_metrics_by_category(category: Optional[str] = None) -> list[dict]:
    """依分類篩選指標，回傳按 label 排序的清單"""
    metrics = list(METRICS_REGISTRY.values())
    if category:
        metrics = [m for m in metrics if m["category"] == category]
    return sorted(metrics, key=lambda m: m["label"])


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/registry")
async def get_metrics_registry(
    category: Optional[str] = Query(None, description="篩選指標分類"),
    current_user: User = Depends(get_current_user),
):
    """
    取得廣告指標定義列表。
    前端使用此端點動態取得指標設定，避免前後端各自維護。

    Args:
        category: 可選，篩選特定分類（delivery, cost, performance, conversion, engagement, video, messaging）
    """
    return {
        "metrics": get_metrics_by_category(category),
        "categories": CATEGORIES,
        "total": len(METRICS_REGISTRY),
    }


@router.get("/registry/{metric_key}")
async def get_metric_detail(
    metric_key: str,
    current_user: User = Depends(get_current_user),
):
    """取得單一指標的詳細定義"""
    metric = METRICS_REGISTRY.get(metric_key)
    if not metric:
        raise HTTPException(status_code=404, detail=f"指標 '{metric_key}' 不存在")
    return metric
