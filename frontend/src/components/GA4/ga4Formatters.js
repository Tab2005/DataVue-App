import {
    TRAFFIC_DIMENSIONS,
    TRAFFIC_COLUMN_HEADERS,
    BEHAVIOR_DIMENSIONS,
    BEHAVIOR_COLUMN_HEADERS,
    ECOMMERCE_DIMENSIONS,
    TRAFFIC_SECONDARY_DIMENSIONS,
    ECOMMERCE_COLUMN_HEADERS,
    CONTENT_DIMENSIONS,
    CONTENT_COLUMN_HEADERS
} from './constants';

export const formatLocalDate = (date) => {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
};

export const formatNumber = (num, type = 'number') => {
    if (typeof num !== 'number') return num;

    switch (type) {
        case 'percentage': {
            return `${(num * 100).toFixed(1)}%`;
        }
        case 'duration': {
            const minutes = Math.floor(num / 60);
            const seconds = Math.floor(num % 60);
            return `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }
        case 'decimal':
            return num.toFixed(2);
        case 'currency':
            return `$${num.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
        default:
            return num.toLocaleString();
    }
};

export const calculateChange = (current, previous) => {
    if (!previous || previous === 0) return null;
    const change = ((current - previous) / previous) * 100;
    return {
        value: change,
        isPositive: change > 0,
        formatted: `${change > 0 ? '+' : ''}${change.toFixed(1)}%`
    };
};

export const getMetricLabel = (metric, language) => {
    const labels = {
        activeUsers: { zh: '活躍使用者', en: 'Active Users' },
        totalUsers: { zh: '總人數', en: 'Total Users' },
        newUsers: { zh: '新使用者人數', en: 'New Users' },
        sessions: { zh: '工作階段', en: 'Sessions' },
        screenPageViews: { zh: '瀏覽', en: 'Page Views' },
        averageSessionDuration: { zh: '平均工作階段持續時間', en: 'Avg. Session Duration' },
        bounceRate: { zh: '跳出率', en: 'Bounce Rate' },
        ecommercePurchases: { zh: '購買', en: 'Purchases' },
        purchaseRevenue: { zh: '總購買收益', en: 'Total Revenue' },
        addToCarts: { zh: '加入購物車', en: 'Add to Cart' },
        averageOrderValue: { zh: '客單價', en: 'Avg. Order Value' },
        purchaseConversionRate: { zh: '購買轉換率', en: 'Conversion Rate' },
        date: { zh: '日期', en: 'Date' },
        pagePath: { zh: '頁面路徑', en: 'Page Path' },
        sessionDefaultChannelGrouping: { zh: '流量來源管道', en: 'Channel Grouping' },
        deviceCategory: { zh: '裝置類別', en: 'Device Category' },
        country: { zh: '國家', en: 'Country' },
        city: { zh: '城市', en: 'City' }
    };
    const label = labels[metric];
    if (!label) return metric;
    return language === 'zh' ? label.zh : label.en;
};

export const getMetricIcon = (metric) => {
    const icons = {
        activeUsers: '👥',
        totalUsers: '👤',
        newUsers: '🆕',
        sessions: '🔄',
        screenPageViews: '👁️',
        averageSessionDuration: '⏱️',
        bounceRate: '📈',
        ecommercePurchases: '🛒',
        purchaseRevenue: '💰',
        addToCarts: '🛍️',
        averageOrderValue: '💵',
        purchaseConversionRate: '🎯'
    };
    return icons[metric] || '📊';
};

export const getTrafficColumnOrder = (trafficDimension) => [
    trafficDimension,
    'totalUsers', 'sessions', 'engagedSessions', 'engagementRate',
    'averageSessionDuration', 'addToCarts', 'ecommercePurchases', 'purchaseRevenue', 'conversionRate'
];

export const getTrafficColumnLabel = (col, language) => {
    const dimConfig = TRAFFIC_DIMENSIONS.find(d => d.key === col);
    if (dimConfig) return language === 'zh' ? dimConfig.label_zh : dimConfig.label_en;
    if (TRAFFIC_COLUMN_HEADERS[col]) return language === 'zh' ? TRAFFIC_COLUMN_HEADERS[col].zh : TRAFFIC_COLUMN_HEADERS[col].en;
    return col;
};

export const getBehaviorColumnOrder = (behaviorDimension) => [
    behaviorDimension,
    'totalUsers', 'engagedSessions', 'screenPageViews', 'engagementRate',
    'averageSessionDuration', 'addToCarts', 'ecommercePurchases', 'purchaseRevenue', 'conversionRate'
];

export const getBehaviorColumnLabel = (col, language) => {
    const dimConfig = BEHAVIOR_DIMENSIONS.find(d => d.key === col);
    if (dimConfig) return language === 'zh' ? dimConfig.label_zh : dimConfig.label_en;
    if (BEHAVIOR_COLUMN_HEADERS[col]) return language === 'zh' ? BEHAVIOR_COLUMN_HEADERS[col].zh : BEHAVIOR_COLUMN_HEADERS[col].en;
    return col;
};

export const getEcommerceColumnOrder = (ecommerceDimension, ecommerceSecondaryDimension) => {
    const columns = [ecommerceDimension];
    if (ecommerceSecondaryDimension !== 'none') columns.push(ecommerceSecondaryDimension);
    columns.push('totalUsers', 'itemsViewed', 'itemsAddedToCart', 'addToCartRate', 'itemsPurchased', 'totalPurchasers', 'itemRevenue', 'checkoutConversionRate', 'conversionRate');
    return columns;
};

export const getEcommerceColumnLabel = (col, language) => {
    const dimConfig = ECOMMERCE_DIMENSIONS.find(d => d.key === col);
    if (dimConfig) return language === 'zh' ? dimConfig.label_zh : dimConfig.label_en;
    const trafficDimConfig = TRAFFIC_SECONDARY_DIMENSIONS.find(d => d.key === col);
    if (trafficDimConfig) return language === 'zh' ? trafficDimConfig.label_zh : trafficDimConfig.label_en;
    if (ECOMMERCE_COLUMN_HEADERS[col]) return language === 'zh' ? ECOMMERCE_COLUMN_HEADERS[col].zh : ECOMMERCE_COLUMN_HEADERS[col].en;
    return col;
};

export const getContentColumnOrder = (contentDimension) => [
    contentDimension,
    'totalUsers', 'activeUsers', 'screenPageViews', 'sessions', 'averageSessionDuration', 'bounceRate'
];

export const getContentColumnLabel = (col, language) => {
    const dimConfig = CONTENT_DIMENSIONS.find(d => d.key === col);
    if (dimConfig) return language === 'zh' ? dimConfig.label_zh : dimConfig.label_en;
    if (CONTENT_COLUMN_HEADERS[col]) return language === 'zh' ? CONTENT_COLUMN_HEADERS[col].zh : CONTENT_COLUMN_HEADERS[col].en;
    return col;
};

