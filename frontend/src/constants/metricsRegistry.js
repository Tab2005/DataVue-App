/**
 * Metrics Registry - Complete Facebook Ads Metrics Database
 * 
 * This is a NEW file that extends (not replaces) the existing analyticsConfig.js
 * Feature toggle: localStorage.getItem('feature_metrics_registry') === 'true'
 * 
 * IMPORTANT: The original METRIC_GROUPS in analyticsConfig.js remains unchanged.
 * This file provides an extended metrics library for the "Metrics Supermarket" feature.
 */

// ============================================================================
// METRIC CATEGORIES
// ============================================================================
export const METRIC_CATEGORIES = {
    general: { label_zh: '通用指標', label_en: 'General', color: '#3b82f6', icon: '📊' },
    ecommerce: { label_zh: '電商指標', label_en: 'E-commerce', color: '#8b5cf6', icon: '🛒' },
    funnel: { label_zh: '漏斗指標', label_en: 'Funnel', color: '#f59e0b', icon: '🌪️' },
    engagement: { label_zh: '互動指標', label_en: 'Engagement', color: '#ec4899', icon: '❤️' },
    video: { label_zh: '影音指標', label_en: 'Video', color: '#06b6d4', icon: '🎬' },
    messaging: { label_zh: '訊息指標', label_en: 'Messaging', color: '#14b8a6', icon: '💬' },
    lead_gen: { label_zh: '潛在客戶', label_en: 'Lead Gen', color: '#84cc16', icon: '📝' },
    app: { label_zh: '應用程式', label_en: 'App', color: '#a855f7', icon: '📱' },
    quality: { label_zh: '品質診斷', label_en: 'Quality', color: '#10b981', icon: '✅' },
    cpas: { label_zh: '協作廣告', label_en: 'CPAS', color: '#06b6d4', icon: '🤝' },
};

// ============================================================================
// METRICS REGISTRY - Full Database
// ============================================================================
export const METRICS_REGISTRY = {
    // ─────────────────────────────────────────────────────────────────────────
    // GENERAL METRICS (Core - is_default: true)
    // ─────────────────────────────────────────────────────────────────────────
    spend: {
        key: 'spend', label_zh: '花費金額', label_en: 'Spend',
        category: 'general', format: 'currency', isInverse: true,
        source: 'direct', fb_field: 'spend',
        is_default: true
    },
    impressions: {
        key: 'impressions', label_zh: '曝光次數', label_en: 'Impressions',
        category: 'general', format: 'number',
        source: 'direct', fb_field: 'impressions',
        is_default: true
    },
    reach: {
        key: 'reach', label_zh: '觸及人數', label_en: 'Reach',
        category: 'general', format: 'number',
        source: 'direct', fb_field: 'reach',
        is_default: true
    },
    frequency: {
        key: 'frequency', label_zh: '頻率', label_en: 'Frequency',
        category: 'general', format: 'decimal',
        source: 'direct', fb_field: 'frequency',
        is_default: true
    },
    cpc: {
        key: 'cpc', label_zh: 'CPC (單次點擊成本)', label_en: 'CPC',
        category: 'general', format: 'currency', isInverse: true,
        source: 'direct', fb_field: 'cpc',
        is_default: true
    },
    cpm: {
        key: 'cpm', label_zh: 'CPM (千次曝光成本)', label_en: 'CPM',
        category: 'general', format: 'currency', isInverse: true,
        source: 'direct', fb_field: 'cpm',
        is_default: true
    },
    ctr: {
        key: 'ctr', label_zh: 'CTR (連結點擊率)', label_en: 'CTR',
        category: 'general', format: 'percent',
        source: 'direct', fb_field: 'ctr',
        is_default: true
    },
    clicks: {
        key: 'clicks', label_zh: '點擊次數 (全部)', label_en: 'Clicks (All)',
        category: 'general', format: 'number',
        source: 'direct', fb_field: 'clicks',
        is_default: true
    },
    link_clicks: {
        key: 'link_clicks', label_zh: '連結點擊次數', label_en: 'Link Clicks',
        category: 'general', format: 'number',
        source: 'direct', fb_field: 'inline_link_clicks',
        is_default: true
    },
    unique_clicks: {
        key: 'unique_clicks', label_zh: '不重複點擊次數', label_en: 'Unique Clicks',
        category: 'general', format: 'number',
        source: 'direct', fb_field: 'unique_clicks',
        is_default: true
    },

    // ─────────────────────────────────────────────────────────────────────────
    // E-COMMERCE METRICS
    // ─────────────────────────────────────────────────────────────────────────
    roas: {
        key: 'roas', label_zh: '購買 ROAS', label_en: 'ROAS',
        category: 'ecommerce', format: 'decimal',
        source: 'purchase_roas', fb_field: 'purchase_roas',
        is_default: false
    },
    purchases: {
        key: 'purchases', label_zh: '購買次數', label_en: 'Purchases',
        category: 'ecommerce', format: 'number',
        source: 'actions', action_type: 'purchase',
        is_default: false
    },
    purchase_value: {
        key: 'purchase_value', label_zh: '購買轉換價值', label_en: 'Purchase Value',
        category: 'ecommerce', format: 'currency',
        source: 'action_values', action_type: 'purchase',
        is_default: false
    },
    cpa: {
        key: 'cpa', label_zh: 'CPA (單次購買成本)', label_en: 'CPA',
        category: 'ecommerce', format: 'currency', isInverse: true,
        source: 'calculated', formula: 'spend / purchases',
        is_default: false
    },
    add_to_cart: {
        key: 'add_to_cart', label_zh: '加到購物車次數', label_en: 'Add to Cart',
        category: 'ecommerce', format: 'number',
        source: 'actions', action_type: 'add_to_cart',
        is_default: false
    },
    atc_value: {
        key: 'atc_value', label_zh: '加到購物車的轉換值', label_en: 'ATC Value',
        category: 'ecommerce', format: 'currency',
        source: 'action_values', action_type: 'add_to_cart',
        is_default: false
    },
    cost_per_atc: {
        key: 'cost_per_atc', label_zh: '加入購物車成本', label_en: 'Cost per ATC',
        category: 'ecommerce', format: 'currency', isInverse: true,
        source: 'calculated', formula: 'spend / add_to_cart',
        is_default: false
    },
    initiate_checkout: {
        key: 'initiate_checkout', label_zh: '開始結帳次數', label_en: 'Initiate Checkout',
        category: 'ecommerce', format: 'number',
        source: 'actions', action_type: 'initiate_checkout',
        is_default: false
    },
    add_payment_info: {
        key: 'add_payment_info', label_zh: '新增付款資訊次數', label_en: 'Add Payment Info',
        category: 'ecommerce', format: 'number',
        source: 'actions', action_type: 'add_payment_info',
        is_default: false
    },
    view_content: {
        key: 'view_content', label_zh: '瀏覽內容次數', label_en: 'View Content',
        category: 'ecommerce', format: 'number',
        source: 'actions', action_type: 'view_content',
        is_default: false
    },

    // ─────────────────────────────────────────────────────────────────────────
    // FUNNEL METRICS
    // ─────────────────────────────────────────────────────────────────────────
    cvr: {
        key: 'cvr', label_zh: '購買轉換率', label_en: 'CVR',
        category: 'funnel', format: 'percent',
        source: 'calculated', formula: '(purchases / link_clicks) * 100',
        is_default: false
    },
    view_to_cart: {
        key: 'view_to_cart', label_zh: '查看後購物車加入率', label_en: 'View to Cart',
        category: 'funnel', format: 'percent',
        source: 'calculated', formula: '(add_to_cart / view_content) * 100',
        is_default: false
    },
    cart_conversion: {
        key: 'cart_conversion', label_zh: '購物車購買率', label_en: 'Cart Purchase Rate',
        category: 'funnel', format: 'percent',
        source: 'calculated', formula: '(purchases / add_to_cart) * 100',
        is_default: false
    },
    cart_dropoff: {
        key: 'cart_dropoff', label_zh: '廣告購物車流失率', label_en: 'Cart Dropoff',
        category: 'funnel', format: 'percent', isInverse: true,
        source: 'calculated', formula: '(1 - purchases / add_to_cart) * 100',
        is_default: false
    },
    cart_value_realization: {
        key: 'cart_value_realization', label_zh: '購物車價值實現率', label_en: 'Cart Value Realization',
        category: 'funnel', format: 'percent',
        source: 'calculated', formula: '(purchase_value / atc_value) * 100',
        is_default: false
    },

    // ─────────────────────────────────────────────────────────────────────────
    // ENGAGEMENT METRICS
    // ─────────────────────────────────────────────────────────────────────────
    post_comments: {
        key: 'post_comments', label_zh: '貼文留言', label_en: 'Comments',
        category: 'engagement', format: 'number',
        source: 'actions', action_type: 'comment',
        is_default: false
    },
    post_saves: {
        key: 'post_saves', label_zh: '貼文儲存', label_en: 'Saves',
        category: 'engagement', format: 'number',
        source: 'actions', action_type: 'onsite_conversion.post_save',
        is_default: false
    },
    post_shares: {
        key: 'post_shares', label_zh: '貼文分享', label_en: 'Shares',
        category: 'engagement', format: 'number',
        source: 'actions', action_type: 'post',
        is_default: false
    },
    post_engagement: {
        key: 'post_engagement', label_zh: '貼文互動', label_en: 'Engagement',
        category: 'engagement', format: 'number',
        source: 'actions', action_type: 'post_engagement',
        is_default: false
    },
    post_reactions: {
        key: 'post_reactions', label_zh: '貼文心情', label_en: 'Reactions',
        category: 'engagement', format: 'number',
        source: 'actions', action_type: 'post_reaction',
        is_default: false
    },
    page_likes: {
        key: 'page_likes', label_zh: '粉絲專頁按讚', label_en: 'Page Likes',
        category: 'engagement', format: 'number',
        source: 'actions', action_type: 'like',
        is_default: false
    },

    // ─────────────────────────────────────────────────────────────────────────
    // VIDEO METRICS (NEW - Extended)
    // ─────────────────────────────────────────────────────────────────────────
    video_views: {
        key: 'video_views', label_zh: '影片觀看次數', label_en: 'Video Views',
        category: 'video', format: 'number',
        source: 'actions', action_type: 'video_view',
        is_default: false,
        description_zh: '影片播放 3 秒以上的次數'
    },
    video_thruplay: {
        key: 'video_thruplay', label_zh: 'ThruPlay', label_en: 'ThruPlay',
        category: 'video', format: 'number',
        source: 'actions', action_type: 'video_view',
        is_default: false,
        description_zh: '影片完整播放或播放至少 15 秒的次數'
    },
    video_p25_watched: {
        key: 'video_p25_watched', label_zh: '影片觀看 25%', label_en: 'Video 25%',
        category: 'video', format: 'number',
        source: 'direct', fb_field: 'video_p25_watched_actions',
        is_default: false
    },
    video_p50_watched: {
        key: 'video_p50_watched', label_zh: '影片觀看 50%', label_en: 'Video 50%',
        category: 'video', format: 'number',
        source: 'direct', fb_field: 'video_p50_watched_actions',
        is_default: false
    },
    video_p75_watched: {
        key: 'video_p75_watched', label_zh: '影片觀看 75%', label_en: 'Video 75%',
        category: 'video', format: 'number',
        source: 'direct', fb_field: 'video_p75_watched_actions',
        is_default: false
    },
    video_p100_watched: {
        key: 'video_p100_watched', label_zh: '影片觀看 100%', label_en: 'Video 100%',
        category: 'video', format: 'number',
        source: 'direct', fb_field: 'video_p100_watched_actions',
        is_default: false
    },
    video_avg_time_watched: {
        key: 'video_avg_time_watched', label_zh: '平均觀看時間', label_en: 'Avg Watch Time',
        category: 'video', format: 'number',
        source: 'direct', fb_field: 'video_avg_time_watched_actions',
        is_default: false,
        description_zh: '平均觀看時間 (秒)'
    },
    cost_per_thruplay: {
        key: 'cost_per_thruplay', label_zh: '每次 ThruPlay 成本', label_en: 'Cost per ThruPlay',
        category: 'video', format: 'currency_decimal', isInverse: true,
        source: 'direct', fb_field: 'cost_per_thruplay',
        is_default: false
    },

    // ─────────────────────────────────────────────────────────────────────────
    // MESSAGING METRICS (NEW - Extended)
    // ─────────────────────────────────────────────────────────────────────────
    messaging_first_reply: {
        key: 'messaging_first_reply', label_zh: '首次訊息回覆', label_en: 'First Reply',
        category: 'messaging', format: 'number',
        source: 'actions', action_type: 'onsite_conversion.messaging_first_reply',
        is_default: false
    },
    messaging_conversation_started: {
        key: 'messaging_conversation_started', label_zh: '開始對話', label_en: 'Conversation Started',
        category: 'messaging', format: 'number',
        source: 'actions', action_type: 'onsite_conversion.messaging_conversation_started_7d',
        is_default: false
    },
    cost_per_message: {
        key: 'cost_per_message', label_zh: '每則訊息成本', label_en: 'Cost per Message',
        category: 'messaging', format: 'currency', isInverse: true,
        source: 'calculated', formula: 'spend / messaging_first_reply',
        is_default: false
    },

    // ─────────────────────────────────────────────────────────────────────────
    // LEAD GEN METRICS (NEW - Extended)
    // ─────────────────────────────────────────────────────────────────────────
    leads: {
        key: 'leads', label_zh: '潛在客戶', label_en: 'Leads',
        category: 'lead_gen', format: 'number',
        source: 'actions', action_type: 'lead',
        is_default: false
    },
    cost_per_lead: {
        key: 'cost_per_lead', label_zh: '每筆潛在客戶成本', label_en: 'Cost per Lead',
        category: 'lead_gen', format: 'currency', isInverse: true,
        source: 'calculated', formula: 'spend / leads',
        is_default: false
    },
    onsite_leads: {
        key: 'onsite_leads', label_zh: '站上潛在客戶', label_en: 'On-site Leads',
        category: 'lead_gen', format: 'number',
        source: 'actions', action_type: 'onsite_conversion.lead_grouped',
        is_default: false
    },

    // ─────────────────────────────────────────────────────────────────────────
    // APP METRICS (NEW - Extended)
    // ─────────────────────────────────────────────────────────────────────────
    app_installs: {
        key: 'app_installs', label_zh: '應用程式安裝', label_en: 'App Installs',
        category: 'app', format: 'number',
        source: 'actions', action_type: 'mobile_app_install',
        is_default: false
    },
    cost_per_install: {
        key: 'cost_per_install', label_zh: '每次安裝成本', label_en: 'Cost per Install',
        category: 'app', format: 'currency', isInverse: true,
        source: 'calculated', formula: 'spend / app_installs',
        is_default: false
    },
    app_events: {
        key: 'app_events', label_zh: '應用程式事件', label_en: 'App Events',
        category: 'app', format: 'number',
        source: 'actions', action_type: 'app_custom_event',
        is_default: false
    },

    // ─────────────────────────────────────────────────────────────────────────
    // QUALITY METRICS
    // ─────────────────────────────────────────────────────────────────────────
    quality_ranking: {
        key: 'quality_ranking', label_zh: '品質排名', label_en: 'Quality Ranking',
        category: 'quality', format: 'string',
        source: 'direct', fb_field: 'quality_ranking',
        is_default: false
    },
    engagement_rate_ranking: {
        key: 'engagement_rate_ranking', label_zh: '互動率排名', label_en: 'Engagement Ranking',
        category: 'quality', format: 'string',
        source: 'direct', fb_field: 'engagement_rate_ranking',
        is_default: false
    },
    conversion_rate_ranking: {
        key: 'conversion_rate_ranking', label_zh: '轉換率排名', label_en: 'Conversion Ranking',
        category: 'quality', format: 'string',
        source: 'direct', fb_field: 'conversion_rate_ranking',
        is_default: false
    },

    // ─────────────────────────────────────────────────────────────────────────
    // CPAS (Collaborative Ads) METRICS
    // ─────────────────────────────────────────────────────────────────────────
    shared_purchases: {
        key: 'shared_purchases', label_zh: '共享購買次數', label_en: 'Shared Purchases',
        category: 'cpas', format: 'number',
        source: 'catalog_segment_actions', action_type: 'purchase',
        is_default: false
    },
    shared_purchase_value: {
        key: 'shared_purchase_value', label_zh: '共享購買值', label_en: 'Shared Value',
        category: 'cpas', format: 'currency',
        source: 'catalog_segment_value', action_type: 'purchase',
        is_default: false
    },
    shared_roas: {
        key: 'shared_roas', label_zh: '共享 ROAS', label_en: 'Shared ROAS',
        category: 'cpas', format: 'decimal',
        source: 'calculated', formula: 'shared_purchase_value / spend',
        is_default: false
    },
    shared_add_to_cart: {
        key: 'shared_add_to_cart', label_zh: '共享加購次數', label_en: 'Shared ATC',
        category: 'cpas', format: 'number',
        source: 'catalog_segment_actions', action_type: 'add_to_cart',
        is_default: false
    },
    shared_atc_value: {
        key: 'shared_atc_value', label_zh: '共享加購值', label_en: 'Shared ATC Val',
        category: 'cpas', format: 'currency',
        source: 'catalog_segment_value', action_type: 'add_to_cart',
        is_default: false
    },
    shared_view_content: {
        key: 'shared_view_content', label_zh: '共享瀏覽次數', label_en: 'Shared Views',
        category: 'cpas', format: 'number',
        source: 'catalog_segment_actions', action_type: 'view_content',
        is_default: false
    },
};

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Check if the Metrics Registry feature is enabled
 */
export const isMetricsRegistryEnabled = () => {
    if (typeof window === 'undefined') return false;
    return localStorage.getItem('feature_metrics_registry') === 'true';
};

/**
 * Get metrics by category
 */
export const getMetricsByCategory = (category) => {
    return Object.values(METRICS_REGISTRY).filter(m => m.category === category);
};

/**
 * Get default metrics (backward compatible with original METRIC_GROUPS)
 */
export const getDefaultMetrics = () => {
    return Object.values(METRICS_REGISTRY).filter(m => m.is_default);
};

/**
 * Get enabled metrics (defaults + user selected)
 */
export const getEnabledMetrics = (userSelected = []) => {
    return Object.values(METRICS_REGISTRY).filter(m =>
        m.is_default || userSelected.includes(m.key)
    );
};

/**
 * Search metrics by keyword
 */
export const searchMetrics = (keyword, language = 'zh') => {
    const lowerKeyword = keyword.toLowerCase();
    return Object.values(METRICS_REGISTRY).filter(m => {
        const label = language === 'zh' ? m.label_zh : m.label_en;
        return label.toLowerCase().includes(lowerKeyword) ||
            m.key.toLowerCase().includes(lowerKeyword);
    });
};

/**
 * Get metric config by key
 */
export const getMetricByKey = (key) => {
    return METRICS_REGISTRY[key] || null;
};

// Stats
export const REGISTRY_STATS = {
    totalMetrics: Object.keys(METRICS_REGISTRY).length,
    defaultMetrics: Object.values(METRICS_REGISTRY).filter(m => m.is_default).length,
    extendedMetrics: Object.values(METRICS_REGISTRY).filter(m => !m.is_default).length,
};

console.log(`[Metrics Registry] Loaded: ${REGISTRY_STATS.totalMetrics} metrics (${REGISTRY_STATS.defaultMetrics} default, ${REGISTRY_STATS.extendedMetrics} extended)`);
