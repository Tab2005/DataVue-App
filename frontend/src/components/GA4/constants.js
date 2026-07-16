// Date Range Presets Configuration (aligned with Analytics page)
export const DATE_PRESETS = [
    { key: 'today', label_zh: '今日', label_en: 'Today', days: 0, isToday: true },
    { key: 'yesterday', label_zh: '昨天', label_en: 'Yesterday', days: 1, isYesterday: true },
    { key: 'this_week', label_zh: '本週', label_en: 'This Week', days: null, isThisWeek: true },
    { key: 'last_week', label_zh: '上週', label_en: 'Last Week', days: null, isLastWeek: true },
    { key: 'this_month', label_zh: '本月', label_en: 'This Month', days: null, isThisMonth: true },
    { key: 'last_month', label_zh: '上月', label_en: 'Last Month', days: null, isLastMonth: true },
    { key: 'last_7d', label_zh: '過去 7 天', label_en: 'Past 7 Days', days: 7 },
    { key: 'last_14d', label_zh: '過去 14 天', label_en: 'Past 14 Days', days: 14 },
    { key: 'last_28d', label_zh: '過去 28 天', label_en: 'Past 28 Days', days: 28 },
    { key: 'custom', label_zh: '自訂', label_en: 'Custom', days: null }
];

// Compare Mode Options
export const COMPARE_OPTIONS = [
    { key: 'none', label_zh: '不比較', label_en: 'No Comparison' },
    { key: 'previous_period', label_zh: '前一時段', label_en: 'Previous Period' },
    { key: 'previous_year', label_zh: '去年同期', label_en: 'Previous Year' }
];

// Traffic Dimensions Configuration (for traffic tab)
export const TRAFFIC_DIMENSIONS = [
    { key: 'sessionDefaultChannelGrouping', label_zh: '管道分組', label_en: 'Channel Grouping' },
    { key: 'sessionSource', label_zh: '來源', label_en: 'Source' },
    { key: 'sessionMedium', label_zh: '媒介', label_en: 'Medium' },
    { key: 'sessionSourceMedium', label_zh: '來源/媒介', label_en: 'Source/Medium' },
    { key: 'sessionCampaignName', label_zh: '廣告活動', label_en: 'Campaign' }
];

// Traffic Tab Metrics (9 metrics as requested)
// 總人數, 工作階段, 互動工作階段, 參與度, 平均參與時間, 加入購物車, 購買, 總購買收益, 轉換率(計算)
export const TRAFFIC_METRICS = [
    'totalUsers', 'sessions', 'engagedSessions', 'engagementRate',
    'averageSessionDuration', 'addToCarts', 'ecommercePurchases', 'purchaseRevenue'
    // conversionRate is calculated as: ecommercePurchases / totalUsers * 100
];

// Traffic metrics column headers (for table display)
export const TRAFFIC_COLUMN_HEADERS = {
    totalUsers: { zh: '總人數', en: 'Total Users' },
    sessions: { zh: '工作階段', en: 'Sessions' },
    engagedSessions: { zh: '互動工作階段', en: 'Engaged Sessions' },
    engagementRate: { zh: '參與度', en: 'Engagement Rate' },
    averageSessionDuration: { zh: '平均參與時間', en: 'Avg Duration' },
    addToCarts: { zh: '加入購物車', en: 'Add to Carts' },
    ecommercePurchases: { zh: '購買', en: 'Purchases' },
    purchaseRevenue: { zh: '總購買收益', en: 'Revenue' },
    conversionRate: { zh: '轉換率', en: 'Conversion Rate' }
};

// NOTE: SOURCE_GROUPS moved to ../utils/sourceGroups.js with custom group support

// Behavior Dimensions Configuration (for user behavior tab)
export const BEHAVIOR_DIMENSIONS = [
    { key: 'deviceCategory', label_zh: '裝置類別', label_en: 'Device Category' },
    { key: 'deviceModel', label_zh: '裝置型號', label_en: 'Device Model' },
    { key: 'country', label_zh: '國家/地區', label_en: 'Country' },
    { key: 'region', label_zh: '區域', label_en: 'Region' },
    { key: 'userAgeBracket', label_zh: '年齡', label_en: 'Age' },
    { key: 'language', label_zh: '語言', label_en: 'Language' }
];

// Behavior filter labels (dynamic based on selected dimension)
export const BEHAVIOR_FILTER_LABELS = {
    deviceCategory: { zh: '裝置篩選', en: 'Device Filter' },
    deviceModel: { zh: '型號篩選', en: 'Model Filter' },
    country: { zh: '國家篩選', en: 'Country Filter' },
    region: { zh: '區域篩選', en: 'Region Filter' },
    userAgeBracket: { zh: '年齡篩選', en: 'Age Filter' },
    language: { zh: '語言篩選', en: 'Language Filter' }
};

// Behavior Tab Metrics (same 9 metrics as traffic tab)
// 總人數, 互動工作階段, 瀏覽, 參與度, 平均參與時間, 加入購物車, 購買, 總購買收益, 轉換率(計算)
export const BEHAVIOR_METRICS = [
    'totalUsers', 'engagedSessions', 'screenPageViews', 'engagementRate',
    'averageSessionDuration', 'addToCarts', 'ecommercePurchases', 'purchaseRevenue'
    // conversionRate is calculated as: ecommercePurchases / totalUsers * 100
];

// Behavior metrics column headers (for table display)
export const BEHAVIOR_COLUMN_HEADERS = {
    totalUsers: { zh: '總人數', en: 'Total Users' },
    engagedSessions: { zh: '互動工作階段', en: 'Engaged Sessions' },
    screenPageViews: { zh: '瀏覽', en: 'Page Views' },
    engagementRate: { zh: '參與度', en: 'Engagement Rate' },
    averageSessionDuration: { zh: '平均參與時間', en: 'Avg Duration' },
    addToCarts: { zh: '加入購物車', en: 'Add to Carts' },
    ecommercePurchases: { zh: '購買', en: 'Purchases' },
    purchaseRevenue: { zh: '總購買收益', en: 'Revenue' },
    conversionRate: { zh: '轉換率', en: 'Conversion Rate' }
};

// Ecommerce Dimensions Configuration (for ecommerce tab)
export const ECOMMERCE_DIMENSIONS = [
    { key: 'itemName', label_zh: '項目名稱', label_en: 'Item Name' },
    { key: 'itemCategory', label_zh: '商品類別', label_en: 'Item Category' },
    { key: 'itemBrand', label_zh: '商品品牌', label_en: 'Item Brand' }
];

// Secondary Traffic Dimensions (optional, for cross-analysis)
export const TRAFFIC_SECONDARY_DIMENSIONS = [
    { key: 'none', label_zh: '無', label_en: 'None' },
    { key: 'sessionDefaultChannelGrouping', label_zh: '管道分組', label_en: 'Channel' },
    { key: 'sessionSource', label_zh: '來源', label_en: 'Source' },
    { key: 'sessionMedium', label_zh: '媒介', label_en: 'Medium' },
    { key: 'sessionSourceMedium', label_zh: '來源/媒介', label_en: 'Source/Medium' }
];

// Ecommerce Tab Metrics (9 metrics)
// 總人數, 已看過的商品數, 加入購物車的商品數, 加入購物車率(計算), 已購買的商品數, 購買者總人數, 商品收益, 結帳轉換率(計算), 轉換率(計算)
export const ECOMMERCE_METRICS = [
    'totalUsers', 'itemsViewed', 'itemsAddedToCart', 'itemsPurchased', 'totalPurchasers', 'itemRevenue'
    // Calculated metrics:
    // addToCartRate: itemsAddedToCart / itemsViewed * 100
    // checkoutConversionRate: itemsPurchased / itemsAddedToCart * 100
    // conversionRate: itemsPurchased / itemsViewed * 100
];

// Ecommerce metrics column headers (for table display)
export const ECOMMERCE_COLUMN_HEADERS = {
    totalUsers: { zh: '總人數', en: 'Total Users' },
    itemsViewed: { zh: '已看過的商品數', en: 'Items Viewed' },
    itemsAddedToCart: { zh: '加入購物車的商品數', en: 'Added to Cart' },
    addToCartRate: { zh: '加入購物車率', en: 'Add to Cart Rate' },
    itemsPurchased: { zh: '已購買的商品數', en: 'Items Purchased' },
    totalPurchasers: { zh: '購買者總人數', en: 'Purchasers' },
    itemRevenue: { zh: '商品收益', en: 'Item Revenue' },
    checkoutConversionRate: { zh: '結帳轉換率', en: 'Checkout Conv. Rate' },
    conversionRate: { zh: '轉換率', en: 'Conversion Rate' }
};

// Content Analysis Dimensions Configuration
export const CONTENT_DIMENSIONS = [
    { key: 'pageTitle', label_zh: '網頁標題', label_en: 'Page Title' },
    { key: 'pagePath', label_zh: '網頁路徑', label_en: 'Page Path' },
    { key: 'pageLocation', label_zh: '網頁 URL', label_en: 'Page URL' }
];

// Content Analysis Metrics (6 metrics)
// 總人數, 活躍使用者, 瀏覽, 工作階段, 平均停留時間, 跳出率
export const CONTENT_METRICS = [
    'totalUsers', 'activeUsers', 'screenPageViews',
    'sessions', 'averageSessionDuration', 'bounceRate'
];

// Content Analysis column headers
export const CONTENT_COLUMN_HEADERS = {
    totalUsers: { zh: '總人數', en: 'Total Users' },
    activeUsers: { zh: '活躍使用者', en: 'Active Users' },
    screenPageViews: { zh: '瀏覽', en: 'Page Views' },
    sessions: { zh: '工作階段', en: 'Sessions' },
    averageSessionDuration: { zh: '平均停留時間', en: 'Avg Duration' },
    bounceRate: { zh: '跳出率', en: 'Bounce Rate' }
};

// NOTE: Content Type Groups are now managed dynamically via contentGroups.js

// Tab Configuration

// Overview Tab Column Order (for table display)
// 日期, 活躍使用者, 總人數, 新使用者人數, 瀏覽, 加入購物車, 購買, 總購買收益, 客單價, 轉換率
export const OVERVIEW_COLUMN_ORDER = [
    'date', 'activeUsers', 'totalUsers', 'newUsers', 'screenPageViews',
    'ecommercePurchases', 'purchaseRevenue', 'addToCarts', 'averageOrderValue', 'purchaseConversionRate'
];

export const TABS = [
    { key: 'overview', label_zh: '📊 總覽', label_en: '📊 Overview', metrics: ['activeUsers', 'totalUsers', 'newUsers', 'screenPageViews', 'addToCarts', 'ecommercePurchases', 'purchaseRevenue'], dimensions: ['date'] },
    { key: 'traffic', label_zh: '🌐 流量來源', label_en: '🌐 Traffic Sources', metrics: TRAFFIC_METRICS, dimensions: ['sessionDefaultChannelGrouping'] },
    { key: 'behavior', label_zh: '👥 用戶行為', label_en: '👥 User Behavior', metrics: BEHAVIOR_METRICS, dimensions: ['deviceCategory'] },
    { key: 'ecommerce', label_zh: '🛒 電子商務', label_en: '🛒 Ecommerce', metrics: ECOMMERCE_METRICS, dimensions: ['itemName'] },
    { key: 'content', label_zh: '📄 內容分析', label_en: '📄 Content Analysis', metrics: CONTENT_METRICS, dimensions: ['pageTitle'] }
];


// Cache TTL in milliseconds (5 minutes)
export const CACHE_TTL = 5 * 60 * 1000;
