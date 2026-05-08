/**
 * Analytics Constants Module
 * 
 * Contains all configuration constants for the Analytics page.
 * Extracted from Analytics.jsx for better maintainability.
 */

export const DATE_PRESETS = [
    { label: '今日 (Today)', value: 'today' },
    { label: '昨天 (Yesterday)', value: 'yesterday' },
    { label: '本週 (This Week)', value: 'this_week' },
    { label: '上週 (Last Week)', value: 'last_week' },
    { label: '本月 (This Month)', value: 'this_month' },
    { label: '上月 (Last Month)', value: 'last_month' },
    { label: '最近 7 天 (Last 7 Days)', value: 'last_7d' },
    { label: '最近 14 天 (Last 14 Days)', value: 'last_14d' },
    { label: '最近 30 天 (Last 30 Days)', value: 'last_30d' },
    { label: '自訂 (Custom)', value: 'custom' },
];

export const COMPARE_PRESETS = [
    { label: '前一期 (Previous Period)', value: 'previous_period' },
    { label: '去年同期 (Same Period Last Year)', value: 'year_over_year' },
    { label: '自訂 (Custom)', value: 'custom' },
];

export const VIEW_PRESETS = {
    summary: {
        label_zh: '📊 總覽',
        label_en: '📊 Summary',
        // Creating a match with Dashboard Overview: Impressions, Link Clicks, CTR, CPC, Spend, Purchases, Add to Cart, ROAS
        metrics: ['impressions', 'link_clicks', 'ctr', 'cpc', 'spend', 'purchases', 'add_to_cart', 'roas']
    },
    custom: {
        label_zh: '⚙️ 自訂',
        label_en: '⚙️ Custom',
        metrics: [] // User defined - opens metric selector panel
    }
    // NOTE: E-commerce, Engagement, Funnel presets have been removed.
    // Users can create custom views via the Metrics Manager (指標管理) page.
};

// Unified Metric Groups Config
// Used for BOTH the Metric Selector (Checkbox) and the KPI Cards/Table Columns

export const GA4_METRIC_GROUPS = [
    {
        id: 'ga4_traffic',
        label_zh: 'GA4 流量指標',
        label_en: 'GA4 Traffic',
        color: '#10b981', // Emerald
        module: 'ga4',
        metrics: [
            { key: 'activeUsers', label_zh: '活躍使用者', label_en: 'Active Users', format: 'number' },
            { key: 'totalUsers', label_zh: '總使用者', label_en: 'Total Users', format: 'number' },
            { key: 'newUsers', label_zh: '新使用者', label_en: 'New Users', format: 'number' },
            { key: 'sessions', label_zh: '工作階段', label_en: 'Sessions', format: 'number' },
            { key: 'screenPageViews', label_zh: '頁面瀏覽次數', label_en: 'Pageviews', format: 'number' },
            { key: 'sessionsPerUser', label_zh: '每人工作階段數', label_en: 'Sessions per User', format: 'decimal' },
        ]
    },
    {
        id: 'ga4_behavior',
        label_zh: 'GA4 行為與參與',
        label_en: 'GA4 Behavior',
        color: '#3b82f6', // Blue
        module: 'ga4',
        metrics: [
            { key: 'engagementRate', label_zh: '參與率', label_en: 'Engagement Rate', format: 'percent' },
            { key: 'averageSessionDuration', label_zh: '平均工作階段時間', label_en: 'Avg. Session Duration', format: 'duration' },
            { key: 'bounceRate', label_zh: '跳出率', label_en: 'Bounce Rate', format: 'percent', isInverse: true },
            { key: 'engagedSessions', label_zh: '參與工作階段', label_en: 'Engaged Sessions', format: 'number' },
            { key: 'eventCount', label_zh: '事件數', label_en: 'Event Count', format: 'number' },
        ]
    },
    {
        id: 'ga4_conversion',
        label_zh: 'GA4 轉換與電商',
        label_en: 'GA4 Conversions',
        color: '#f59e0b', // Amber
        module: 'ga4',
        metrics: [
            { key: 'conversions', label_zh: '轉換數', label_en: 'Conversions', format: 'number' },
            { key: 'totalRevenue', label_zh: '總收益', label_en: 'Total Revenue', format: 'currency' },
            { key: 'purchaseRevenue', label_zh: '購買收益', label_en: 'Purchase Revenue', format: 'currency' },
            { key: 'addToCarts', label_zh: '加入購物車次數', label_en: 'Add to Carts', format: 'number' },
            { key: 'checkouts', label_zh: '開始結帳次數', label_en: 'Checkouts', format: 'number' },
            { key: 'ecommercePurchases', label_zh: '電商購買次數', label_en: 'E-commerce Purchases', format: 'number' },
            { key: 'firstPurchasers', label_zh: '首次購買者人數', label_en: 'First Purchasers', format: 'number' },
            { key: 'sessionConversionRate', label_zh: '工作階段轉換率', label_en: 'Session CV Rate', format: 'percent' },
            { key: 'userConversionRate', label_zh: '使用者轉換率', label_en: 'User CV Rate', format: 'percent' },
        ]
    }
];

export const METRIC_GROUPS = [
    {
        id: 'general',
        label_zh: '通用指標',
        label_en: 'General Metrics',
        color: '#3b82f6', // Blue
        module: 'fb_ads',
        metrics: [
            { key: 'spend', label_zh: '花費金額', label_en: 'Spend', format: 'currency', isInverse: true },
            { key: 'reach', label_zh: '觸及人數', label_en: 'Reach', format: 'number' },
            { key: 'impressions', label_zh: '曝光次數', label_en: 'Impressions', format: 'number' },
            { key: 'cpc', label_zh: 'CPC (單次點擊成本)', label_en: 'CPC', format: 'currency', isInverse: true },
            { key: 'ctr', label_zh: 'CTR (全部點擊率)', label_en: 'CTR (All Clicks)', format: 'percent' },
            { key: 'cpm', label_zh: 'CPM (千次曝光成本)', label_en: 'CPM', format: 'currency', isInverse: true },
            { key: 'link_clicks', label_zh: '連結點擊次數', label_en: 'Link Clicks', format: 'number' },
        ]
    },
    {
        id: 'ecommerce',
        label_zh: '電商指標',
        label_en: 'E-commerce Metrics',
        color: '#8b5cf6', // Violet
        module: 'fb_ads',
        metrics: [
            { key: 'roas', label_zh: '購買 ROAS', label_en: 'ROAS', format: 'decimal' },
            { key: 'purchases', label_zh: '購買次數', label_en: 'Purchases', format: 'number' },
            { key: 'purchase_value', label_zh: '購買轉換價值', label_en: 'Purchase Value', format: 'currency' },
            { key: 'cpa', label_zh: 'CPA (單次購買成本)', label_en: 'CPA', format: 'currency', isInverse: true },
            { key: 'add_to_cart', label_zh: '加到購物車次數', label_en: 'Add to Cart', format: 'number' },
            { key: 'atc_value', label_zh: '加到購物車的轉換值', label_en: 'ATC Value', format: 'currency' },
            { key: 'cost_per_atc', label_zh: '加入購物車成本', label_en: 'Cost per ATC', format: 'currency', isInverse: true },
            { key: 'initiate_checkout', label_zh: '開始結帳次數', label_en: 'Initiate Checkout', format: 'number' },
            { key: 'add_payment_info', label_zh: '新增付款資訊次數', label_en: 'Add Payment Info', format: 'number' },
        ]
    },
    {
        id: 'funnel',
        label_zh: '漏斗指標',
        label_en: 'Funnel Metrics',
        color: '#f59e0b', // Amber
        module: 'fb_ads',
        metrics: [
            { key: 'view_to_cart', label_zh: '查看後購物車加入率', label_en: 'View to Cart Rate', format: 'percent' },
            { key: 'cvr', label_zh: '購買轉換率', label_en: 'Conversion Rate', format: 'percent' },
            { key: 'cart_value_realization', label_zh: '購物車價值實現率', label_en: 'Cart Value Realization', format: 'percent' },
            { key: 'cart_conversion', label_zh: '購物車購買率', label_en: 'Cart Purchase Rate', format: 'percent' },
            { key: 'cart_dropoff', label_zh: '廣告購物車流失率', label_en: 'Cart Dropoff Rate', format: 'percent', isInverse: true },
        ]
    },
    {
        id: 'engagement',
        label_zh: '互動指標',
        label_en: 'Engagement',
        color: '#ec4899', // Pink
        module: 'fb_ads',
        metrics: [
            { key: 'post_comments', label_zh: '貼文留言', label_en: 'Post Comments', format: 'number' },
            { key: 'post_saves', label_zh: '貼文儲存', label_en: 'Post Saves', format: 'number' },
            { key: 'post_shares', label_zh: '貼文分享', label_en: 'Post Shares', format: 'number' },
            { key: 'post_engagement', label_zh: '貼文互動', label_en: 'Post Engagement', format: 'number' },
            { key: 'post_reactions', label_zh: '貼文心情', label_en: 'Post Reactions', format: 'number' },
            { key: 'page_likes', label_zh: '粉絲專頁按讚', label_en: 'Page Likes', format: 'number' },
        ]
    },
    {
        id: 'quality',
        label_zh: '品質診斷',
        label_en: 'Quality Diagnosis',
        color: '#10b981', // Emerald
        module: 'fb_ads',
        metrics: [
            { key: 'quality_ranking', label_zh: '品質排名', label_en: 'Quality Ranking', format: 'string' },
            { key: 'conversion_rate_ranking', label_zh: '轉換率排名', label_en: 'Conversion Rate Ranking', format: 'string' },
            { key: 'engagement_rate_ranking', label_zh: '互動率排名', label_en: 'Engagement Rate Ranking', format: 'string' },
        ]
    },
    {
        id: 'collaborative',
        label_zh: '協作指標 (CPAS)',
        label_en: 'Collaborative Ads',
        color: '#06b6d4', // Cyan
        module: 'fb_ads',
        metrics: [
            { key: 'shared_purchases', label_zh: '共享購買次數', label_en: 'Shared Purch.', format: 'number' },
            { key: 'shared_purchase_value', label_zh: '共享購買值', label_en: 'Shared Value', format: 'currency' },
            { key: 'shared_roas', label_zh: '共享 ROAS', label_en: 'Shared ROAS', format: 'decimal' },
            { key: 'shared_add_to_cart', label_zh: '共享加購次數', label_en: 'Shared ATC', format: 'number' },
            { key: 'shared_atc_value', label_zh: '共享加購值', label_en: 'Shared ATC Val', format: 'currency' },
            { key: 'shared_view_content', label_zh: '共享瀏覽次數', label_en: 'Shared Views', format: 'number' },
        ]
    },
    ...GA4_METRIC_GROUPS
];

/**
 * Get all metric groups for a specific module
 */
export const getGroupsByModule = (module = 'fb_ads') => {
    return METRIC_GROUPS.filter(g => g.module === module);
};

/**
 * Get all metric keys from a specific group
 */
export const getMetricsByGroup = (groupId) => {
    const group = METRIC_GROUPS.find(g => g.id === groupId);
    return group ? group.metrics.map(m => m.key) : [];
};

/**
 * Get all available metric keys as composite keys (groupId:metricKey)
 */
export const getAllMetricKeys = () => {
    return METRIC_GROUPS.flatMap(g => g.metrics.map(m => `${g.id}:${m.key}`));
};

/**
 * Find metric configuration by key
 */
export const getMetricConfig = (key) => {
    for (const group of METRIC_GROUPS) {
        const metric = group.metrics.find(m => m.key === key);
        if (metric) {
            return { ...metric, groupId: group.id, groupColor: group.color };
        }
    }
    return null;
};
