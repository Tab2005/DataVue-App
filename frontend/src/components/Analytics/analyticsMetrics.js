import { METRICS_REGISTRY, METRIC_CATEGORIES } from '../../constants/metricsRegistry';

// METRIC_GROUPS imported from analyticsConfig but kept inline for backward compatibility
// TODO: Migrate remaining code to use imported METRIC_GROUPS
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

// Unified metric groups: Merge original + registry metrics
export const buildUnifiedMetricGroups = () => {
    // 1. Deep clone existing hardcoded groups to avoid mutation
    const groups = JSON.parse(JSON.stringify(METRIC_GROUPS));

    // Mapping from Registry Category to Group ID
    // Some keys might differ between registry and hardcoded groups (e.g. cpas vs collaborative)
    const categoryToGroupId = {
        'general': 'general',
        'ecommerce': 'ecommerce',
        'funnel': 'funnel',
        'engagement': 'engagement',
        'quality': 'quality',
        'cpas': 'collaborative',
    };

    // 2. Iterate through all metrics in registry
    Object.values(METRICS_REGISTRY).forEach(registryMetric => {
        // Determine target group ID
        const targetGroupId = categoryToGroupId[registryMetric.category] || registryMetric.category;

        // Find existing group
        let group = groups.find(g => g.id === targetGroupId);

        // If group doesn't exist (e.g. video, messaging, app), create it from METRIC_CATEGORIES
        if (!group) {
            const catInfo = METRIC_CATEGORIES[registryMetric.category];
            if (catInfo) {
                group = {
                    id: targetGroupId,
                    label_zh: catInfo.label_zh, // No "(Extended)" or "(擴展)" suffix
                    label_en: catInfo.label_en,
                    color: catInfo.color,
                    metrics: []
                };
                groups.push(group);
            }
        }

        // Add metric to group if not already present
        if (group) {
            // Check if key exists (handle both simple and composite keys if necessary, but registry keys are unique)
            const exists = group.metrics.some(m => m.key === registryMetric.key);

            if (!exists) {
                group.metrics.push({
                    key: registryMetric.key,
                    label_zh: registryMetric.label_zh,
                    label_en: registryMetric.label_en,
                    format: registryMetric.format,
                    isInverse: registryMetric.isInverse || false
                });
            }
        }
    });

    return groups;
};

export const ALL_METRIC_GROUPS = buildUnifiedMetricGroups();

export const resolveObservationWindowKind = (datePreset) => {
    if (datePreset === 'last_7d') {
        return 'last_7d';
    }
    if (datePreset === 'last_30d') {
        return 'last_30d';
    }
    if (datePreset === 'custom') {
        return 'custom';
    }
    return 'custom';
};

