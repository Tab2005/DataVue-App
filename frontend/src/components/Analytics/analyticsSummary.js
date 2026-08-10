// frontend/src/components/Analytics/analyticsSummary.js (docs/33 第 7 波：Analytics.jsx 組合層瘦身)
//
// 原本內嵌在 Analytics.jsx 的 KPI 加總計算與數值格式化，純函數，無元件
// state 依賴（selectedRowIds 改由呼叫端明確傳入，而非原本靠 closure 讀取）。

// 7. Calculate Summary for KPI Cards (Dynamic Selection)
export const calculateSummary = (dataSource, selectedRowIds) => {
    if (!dataSource || dataSource.length === 0) return null;

    // Filter by Selection
    // Logic: If selectedRowIds exists, only sum items in it.
    const targetData = dataSource.filter(item => selectedRowIds.has(item.id));

    if (targetData.length === 0) return null; // Or return all zeros? Returning null usually hides cards or shows 0.

    // Sum basic additive metrics
    const sum = (key) => targetData.reduce((acc, row) => acc + (row[key] || 0), 0);

    const total = {
        spend: sum('spend'),
        impressions: sum('impressions'),
        reach: sum('reach'), // Approximation
        frequency: sum('frequency'),  // NEW
        clicks: sum('clicks'),  // NEW
        link_clicks: sum('link_clicks'),
        unique_clicks: sum('unique_clicks'),  // NEW
        outbound_clicks: sum('outbound_clicks'), // NEW for Cost Per Outbound Click
        view_content: sum('view_content'),
        add_to_cart: sum('add_to_cart'),
        initiate_checkout: sum('initiate_checkout'),
        add_payment_info: sum('add_payment_info'),
        purchases: sum('purchases'),
        purchase_value: sum('purchase_value'),
        atc_value: sum('atc_value'),
        // Engagement (New)
        post_comments: sum('post_comments'),
        post_saves: sum('post_saves'),
        post_shares: sum('post_shares'),
        post_engagement: sum('post_engagement'),
        post_reactions: sum('post_reactions'),
        page_likes: sum('page_likes'),
        // CPAS (New)
        shared_purchases: sum('shared_purchases'),
        shared_purchase_value: sum('shared_purchase_value'),
        shared_add_to_cart: sum('shared_add_to_cart'),
        shared_atc_value: sum('shared_atc_value'),
        shared_view_content: sum('shared_view_content'),
        // Video Metrics
        video_views: sum('video_views'),
        video_thruplay: sum('video_thruplay'),
        video_p25_watched: sum('video_p25_watched'),
        video_p50_watched: sum('video_p50_watched'),
        video_p75_watched: sum('video_p75_watched'),
        video_p100_watched: sum('video_p100_watched'),
        video_avg_time_watched: sum('video_avg_time_watched'),
        // Messaging Metrics
        messaging_first_reply: sum('messaging_first_reply'),
        messaging_conversation_started: sum('messaging_conversation_started'),
        // Lead Metrics
        leads: sum('leads'),
        onsite_leads: sum('onsite_leads'),
        // App Metrics
        app_installs: sum('app_installs'),
        app_events: sum('app_events'),
        // Instant Experience (New)
        instant_experience_open: sum('instant_experience_open'),
        instant_experience_start: sum('instant_experience_start'),
    };

    // Recalculate derived rates
    total.cpc = total.link_clicks > 0 ? total.spend / total.link_clicks : 0;
    total.cpm = total.impressions > 0 ? (total.spend / total.impressions) * 1000 : 0;

    total.cpa = total.purchases > 0 ? total.spend / total.purchases : 0;
    total.cost_per_atc = total.add_to_cart > 0 ? total.spend / total.add_to_cart : 0;
    total.roas = total.spend > 0 ? total.purchase_value / total.spend : 0;
    total.shared_roas = total.spend > 0 ? total.shared_purchase_value / total.spend : 0;

    // CTR fields: per-row CTR values are rates (clicks/impressions), so they must be
    // recomputed from the summed raw counts (weighted average), never summed directly -
    // summing rates across rows inflates the total (e.g. 10 days at 2% becomes "20%").
    total.ctr = total.impressions > 0 ? (total.clicks / total.impressions) * 100 : 0;
    total.inline_link_click_ctr = total.impressions > 0 ? (total.link_clicks / total.impressions) * 100 : 0;
    total.unique_ctr = total.reach > 0 ? (total.unique_clicks / total.reach) * 100 : 0;
    total.outbound_clicks_ctr = total.impressions > 0 ? (total.outbound_clicks / total.impressions) * 100 : 0;

    // Cost & Spend Derived
    total.cpp = total.reach > 0 ? (total.spend / total.reach) * 1000 : 0;
    total.cost_per_unique_click = total.unique_clicks > 0 ? total.spend / total.unique_clicks : 0;
    total.cost_per_conversion = total.purchases > 0 ? total.spend / total.purchases : 0;
    // Approximation for others where denominator might be missing or using generic clicks
    total.cost_per_inline_link_click = total.link_clicks > 0 ? total.spend / total.link_clicks : 0;

    // Cost Per Outbound Click
    total.cost_per_outbound_click = total.outbound_clicks > 0 ? total.spend / total.outbound_clicks : 0;

    // Calculated Extended Costs
    total.cost_per_message = total.messaging_first_reply > 0 ? total.spend / total.messaging_first_reply : 0;
    total.cost_per_install = total.app_installs > 0 ? total.spend / total.app_installs : 0;
    total.cost_per_lead = total.leads > 0 ? total.spend / total.leads : 0;

    // Funnel Rates
    total.cvr = total.link_clicks > 0 ? (total.purchases / total.link_clicks) * 100 : 0;
    total.view_to_cart = total.view_content > 0 ? (total.add_to_cart / total.view_content) * 100 : 0;
    total.cart_conversion = total.add_to_cart > 0 ? (total.purchases / total.add_to_cart) * 100 : 0;
    total.cart_dropoff = total.add_to_cart > 0 ? (1 - (total.purchases / total.add_to_cart)) * 100 : 0;
    total.cart_value_realization = total.atc_value > 0 ? (total.purchase_value / total.atc_value) * 100 : 0;

    // Video Derived Rates
    total.cost_per_thruplay = total.video_thruplay > 0 ? total.spend / total.video_thruplay : 0;

    // Messaging Derived Rates
    total.cost_per_message = total.messaging_first_reply > 0 ? total.spend / total.messaging_first_reply : 0;

    // Lead Derived Rates
    total.cost_per_lead = total.leads > 0 ? total.spend / total.leads : 0;

    // App Derived Rates
    total.cost_per_install = total.app_installs > 0 ? total.spend / total.app_installs : 0;

    return total;
};

export const renderMetricValue = (val, format) => {
    if (val === undefined || val === null || isNaN(val)) return '-';
    if (format === 'currency') return `$${val.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`; // Round currency on cards
    if (format === 'currency_decimal') {
        // Smart decimal: show .X only if not a whole number
        const isWholeNumber = Number.isInteger(val) || Math.abs(val - Math.round(val)) < 0.01;
        return `$${val.toLocaleString(undefined, { minimumFractionDigits: isWholeNumber ? 0 : 1, maximumFractionDigits: isWholeNumber ? 0 : 1 })}`;
    }
    if (format === 'percent') return `${val.toFixed(2)}%`;
    if (format === 'decimal') return val.toFixed(2);
    return val.toLocaleString();
};
