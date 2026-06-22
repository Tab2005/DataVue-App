"""權限系統初始資料 Seed Data"""

MODULES = [
    {"key": "fb_ads", "name": "FB Ads 廣告管理", "icon": "📊", "sort_order": 1},
    {"key": "gsc", "name": "Google Search Console", "icon": "🔍", "sort_order": 2},
    {"key": "ga4", "name": "Google Analytics 4", "icon": "📈", "sort_order": 3, "enabled": True},
    {"key": "meta_andromeda", "name": "Meta Andromeda", "icon": "🛰️", "sort_order": 4, "enabled": True},
]

PERMISSIONS = {
    "fb_ads": [
        {"key": "fb_ads:analytics:view", "name": "數據查看", "category": "feature"},
        {"key": "fb_ads:account:manage", "name": "帳號管理", "category": "admin"},
        {"key": "fb_ads:report:generate", "name": "報表生成", "category": "feature"},
        {"key": "fb_ads:view:create", "name": "新增視角", "category": "feature"},
        {"key": "fb_ads:view:edit", "name": "編輯視角", "category": "feature"},
        {"key": "fb_ads:ai:use", "name": "AI 分析師", "category": "feature"},
    ],
    "gsc": [
        {"key": "gsc:site:connect", "name": "連接站點", "category": "admin"},
        {"key": "gsc:analytics:view", "name": "數據查看", "category": "feature"},
        {"key": "gsc:keyword:view", "name": "關鍵字分析", "category": "feature"},
        {"key": "gsc:page:view", "name": "頁面分析", "category": "feature"},
        {"key": "gsc:trend:view", "name": "趨勢分析", "category": "feature"},
    ],
    "ga4": [
        {"key": "ga4:property:connect", "name": "連接屬性", "category": "admin"},
        {"key": "ga4:analytics:view", "name": "數據查看", "category": "feature"},
    ],
    "meta_andromeda": [],
}

ROLES = [
    {"key": "team_owner", "name": "團隊擁有者", "scope": "team", "description": "團隊擁有者，最高權限"},
    {"key": "team_admin", "name": "團隊管理員", "scope": "team", "description": "可管理成員與配置"},
    {"key": "team_member", "name": "團隊成員", "scope": "team", "description": "一般成員權限"},
    {"key": "team_viewer", "name": "團隊檢視者", "scope": "team", "description": "僅能查看數據"},
]

# 角色預設權限矩陣
ROLE_PERMISSIONS = {
    "team_owner": ["*"],  # 全部權限
    "team_admin": [
        "fb_ads:analytics:view", "fb_ads:account:manage", "fb_ads:report:generate",
        "fb_ads:view:create", "fb_ads:view:edit", "fb_ads:ai:use",
        "gsc:site:connect", "gsc:analytics:view", "gsc:keyword:view",
        "gsc:page:view", "gsc:trend:view",
        "ga4:property:connect", "ga4:analytics:view",
    ],
    "team_member": [
        "fb_ads:analytics:view", "fb_ads:report:generate",
        "fb_ads:view:create", "fb_ads:view:edit", "fb_ads:ai:use",
        "gsc:analytics:view", "gsc:keyword:view", "gsc:page:view", "gsc:trend:view",
        "ga4:analytics:view",
    ],
    "team_viewer": [
        "fb_ads:analytics:view", "fb_ads:report:generate",
        "gsc:analytics:view", "gsc:keyword:view", "gsc:page:view", "gsc:trend:view",
        "ga4:analytics:view",
    ],
}
