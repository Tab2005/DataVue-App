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
    ecommerce: {
        label_zh: '🛒 電商詳情',
        label_en: '🛒 E-commerce',
        // User requested 7 specific metrics: ATC Value, CPA, ATC, ROAS, Cost per ATC, Purchase Value, Purchases
        // Reordered for logical funnel flow: ATC -> Cost/ATC -> ATC Value -> Purchases -> CPA -> Purchase Value -> ROAS
        metrics: ['add_to_cart', 'cost_per_atc', 'atc_value', 'purchases', 'cpa', 'purchase_value', 'roas']
    },
    engagement: {
        label_zh: '❤️ 互動指標',
        label_en: '❤️ Engagement',
        metrics: ['post_comments', 'post_saves', 'post_shares', 'post_engagement', 'post_reactions', 'page_likes']
    },
    funnel: {
        label_zh: '🌪️ 漏斗分析',
        label_en: '🌪️ Funnel',
        metrics: ['cvr', 'view_to_cart', 'cart_conversion', 'cart_dropoff', 'cart_value_realization']
    },
    custom: {
        label_zh: '⚙️ 自訂',
        label_en: '⚙️ Custom',
        metrics: [] // User defined
    }
};

// Unified Metric Groups Config
// Used for BOTH the Metric Selector (Checkbox) and the KPI Cards/Table Columns
export const METRIC_GROUPS = [
    {
        id: 'general',
        label_zh: '通用指標',
        label_en: 'General Metrics',
        color: '#3b82f6', // Blue
        metrics: [
            { key: 'spend', label_zh: '花費金額', label_en: 'Spend', format: 'currency', isInverse: true },
            { key: 'reach', label_zh: '觸及人數', label_en: 'Reach', format: 'number' },
            { key: 'impressions', label_zh: '曝光次數', label_en: 'Impressions', format: 'number' },
            { key: 'cpc', label_zh: 'CPC (單次點擊成本)', label_en: 'CPC', format: 'currency', isInverse: true },
            { key: 'ctr', label_zh: 'CTR (連結點擊率)', label_en: 'CTR', format: 'percent' },
            { key: 'cpm', label_zh: 'CPM (千次曝光成本)', label_en: 'CPM', format: 'currency', isInverse: true },
            { key: 'link_clicks', label_zh: '連結點擊次數', label_en: 'Link Clicks', format: 'number' },
        ]
    },
    {
        id: 'ecommerce',
        label_zh: '電商指標',
        label_en: 'E-commerce Metrics',
        color: '#8b5cf6', // Violet
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
        metrics: [
            { key: 'shared_purchases', label_zh: '共享購買次數', label_en: 'Shared Purch.', format: 'number' },
            { key: 'shared_purchase_value', label_zh: '共享購買值', label_en: 'Shared Value', format: 'currency' },
            { key: 'shared_roas', label_zh: '共享 ROAS', label_en: 'Shared ROAS', format: 'decimal' },
            { key: 'shared_add_to_cart', label_zh: '共享加購次數', label_en: 'Shared ATC', format: 'number' },
            { key: 'shared_atc_value', label_zh: '共享加購值', label_en: 'Shared ATC Val', format: 'currency' },
            { key: 'shared_view_content', label_zh: '共享瀏覽次數', label_en: 'Shared Views', format: 'number' },
        ]
    }
];

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
