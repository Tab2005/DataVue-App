/**
 * 廣告文案庫共用標籤與格式化（docs/73、docs/74）
 */
export const t = (language, en, zh) => (language === 'en' ? en : zh);

export const STATUS_LABELS = {
    ACTIVE: ['Active', '投放中'],
    PAUSED: ['Paused', '已暫停'],
    CAMPAIGN_PAUSED: ['Campaign paused', '活動已暫停'],
    ADSET_PAUSED: ['Ad set paused', '廣告組合已暫停'],
    ARCHIVED: ['Archived', '已封存'],
    DELETED: ['Deleted', '已刪除'],
    DISAPPROVED: ['Disapproved', '未通過審查'],
    WITH_ISSUES: ['With issues', '有問題'],
    IN_PROCESS: ['In process', '處理中'],
    PENDING_REVIEW: ['Pending review', '審查中'],
};

export const MEDIA_TYPE_LABELS = {
    image: ['Image', '圖片'],
    video: ['Video', '影片'],
    carousel: ['Carousel', '輪播'],
    dynamic: ['Dynamic', '動態創意'],
};

export const OBJECTIVE_LABELS = {
    OUTCOME_SALES: ['Sales', '銷售'],
    OUTCOME_LEADS: ['Leads', '潛在顧客'],
    OUTCOME_TRAFFIC: ['Traffic', '流量'],
    OUTCOME_ENGAGEMENT: ['Engagement', '互動'],
    OUTCOME_AWARENESS: ['Awareness', '知名度'],
    OUTCOME_APP_PROMOTION: ['App promotion', '應用程式推廣'],
};

export const OPTIMIZATION_GOAL_LABELS = {
    OFFSITE_CONVERSIONS: ['Conversions', '轉換'],
    VALUE: ['Conversion value', '轉換價值'],
    LINK_CLICKS: ['Link clicks', '連結點擊'],
    LANDING_PAGE_VIEWS: ['Landing page views', '到達頁面瀏覽'],
    IMPRESSIONS: ['Impressions', '曝光'],
    REACH: ['Reach', '觸及'],
    THRUPLAY: ['ThruPlay', 'ThruPlay'],
    LEAD_GENERATION: ['Leads', '潛在顧客'],
    POST_ENGAGEMENT: ['Post engagement', '貼文互動'],
    CONVERSATIONS: ['Conversations', '對話'],
};

export const label = (map, key, language) => {
    const entry = map[key];
    if (entry) return t(language, entry[0], entry[1]);
    return key || '—';
};

export const formatNumber = (n) => new Intl.NumberFormat('zh-TW').format(Math.round(n || 0));
export const formatMoney = (n) => new Intl.NumberFormat('zh-TW', { maximumFractionDigits: 2 }).format(n || 0);
export const formatDate = (s) => (s ? new Date(`${s}Z`).toLocaleDateString('zh-TW') : '—');
