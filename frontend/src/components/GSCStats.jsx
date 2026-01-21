
import React, { useEffect, useState, useMemo } from 'react';

// Date Range Presets Configuration (aligned with GA4)
const DATE_PRESETS = [
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

// Compare Mode Options (aligned with GA4)
const COMPARE_OPTIONS = [
    { key: 'none', label_zh: '不比較', label_en: 'No Comparison' },
    { key: 'previous_period', label_zh: '前一時段', label_en: 'Previous Period' },
    { key: 'previous_year', label_zh: '去年同期', label_en: 'Previous Year' }
];


// Tab Configuration

const TABS = [
    { key: 'daily', label_zh: '📈 每日成效', label_en: '📈 Daily Performance', dimension: 'date' },
    { key: 'query', label_zh: '🔍 關鍵字分析', label_en: '🔍 Keyword Analysis', dimension: 'query' },
    { key: 'page', label_zh: '📄 頁面分析', label_en: '📄 Page Analysis', dimension: 'page' },
    { key: 'trend', label_zh: '📊 頁面趨勢', label_en: '📊 Page Trends', dimension: 'page' },
    { key: 'country', label_zh: '🌍 地區分佈', label_en: '🌍 Country', dimension: 'country' },
    { key: 'device', label_zh: '📱 裝置分佈', label_en: '📱 Device', dimension: 'device' }
];

// Trend Sub-tabs
const TREND_SUBTABS = [
    { key: 'top', label_zh: '頂層', label_en: 'Top' },
    { key: 'up', label_zh: '走勢向上', label_en: 'Trending Up' },
    { key: 'down', label_zh: '走勢向下', label_en: 'Trending Down' }
];

// Country code to name mapping (expanded list)
const COUNTRY_NAMES = {
    // East Asia
    twn: { zh: '台灣', en: 'Taiwan' },
    jpn: { zh: '日本', en: 'Japan' },
    kor: { zh: '韓國', en: 'South Korea' },
    chn: { zh: '中國', en: 'China' },
    hkg: { zh: '香港', en: 'Hong Kong' },
    mac: { zh: '澳門', en: 'Macau' },
    // Southeast Asia
    sgp: { zh: '新加坡', en: 'Singapore' },
    mys: { zh: '馬來西亞', en: 'Malaysia' },
    tha: { zh: '泰國', en: 'Thailand' },
    vnm: { zh: '越南', en: 'Vietnam' },
    phl: { zh: '菲律賓', en: 'Philippines' },
    idn: { zh: '印尼', en: 'Indonesia' },
    mmr: { zh: '緬甸', en: 'Myanmar' },
    khm: { zh: '柬埔寨', en: 'Cambodia' },
    lao: { zh: '寮國', en: 'Laos' },
    brn: { zh: '汶萊', en: 'Brunei' },
    // North America
    usa: { zh: '美國', en: 'USA' },
    can: { zh: '加拿大', en: 'Canada' },
    mex: { zh: '墨西哥', en: 'Mexico' },
    // Europe
    gbr: { zh: '英國', en: 'UK' },
    deu: { zh: '德國', en: 'Germany' },
    fra: { zh: '法國', en: 'France' },
    ita: { zh: '義大利', en: 'Italy' },
    esp: { zh: '西班牙', en: 'Spain' },
    nld: { zh: '荷蘭', en: 'Netherlands' },
    bel: { zh: '比利時', en: 'Belgium' },
    che: { zh: '瑞士', en: 'Switzerland' },
    aut: { zh: '奧地利', en: 'Austria' },
    pol: { zh: '波蘭', en: 'Poland' },
    swe: { zh: '瑞典', en: 'Sweden' },
    nor: { zh: '挪威', en: 'Norway' },
    dnk: { zh: '丹麥', en: 'Denmark' },
    fin: { zh: '芬蘭', en: 'Finland' },
    irl: { zh: '愛爾蘭', en: 'Ireland' },
    prt: { zh: '葡萄牙', en: 'Portugal' },
    rus: { zh: '俄羅斯', en: 'Russia' },
    ukr: { zh: '烏克蘭', en: 'Ukraine' },
    tur: { zh: '土耳其', en: 'Turkey' },
    grc: { zh: '希臘', en: 'Greece' },
    // Oceania
    aus: { zh: '澳洲', en: 'Australia' },
    nzl: { zh: '紐西蘭', en: 'New Zealand' },
    // South America
    bra: { zh: '巴西', en: 'Brazil' },
    arg: { zh: '阿根廷', en: 'Argentina' },
    chl: { zh: '智利', en: 'Chile' },
    col: { zh: '哥倫比亞', en: 'Colombia' },
    per: { zh: '秘魯', en: 'Peru' },
    // Middle East
    are: { zh: '阿聯酋', en: 'UAE' },
    sau: { zh: '沙烏地阿拉伯', en: 'Saudi Arabia' },
    isr: { zh: '以色列', en: 'Israel' },
    // South Asia
    ind: { zh: '印度', en: 'India' },
    pak: { zh: '巴基斯坦', en: 'Pakistan' },
    bgd: { zh: '孟加拉', en: 'Bangladesh' },
    lka: { zh: '斯里蘭卡', en: 'Sri Lanka' },
    // Africa
    zaf: { zh: '南非', en: 'South Africa' },
    egy: { zh: '埃及', en: 'Egypt' },
    nga: { zh: '奈及利亞', en: 'Nigeria' },
    ken: { zh: '肯亞', en: 'Kenya' },
    // Central Asia
    kaz: { zh: '哈薩克', en: 'Kazakhstan' },
    // Eastern Europe
    alb: { zh: '阿爾巴尼亞', en: 'Albania' },
    // Caribbean / Central America
    pry: { zh: '巴拉圭', en: 'Paraguay' },
    bhs: { zh: '巴哈馬', en: 'Bahamas' },
    blz: { zh: '貝里斯', en: 'Belize' },
    cuw: { zh: '庫拉索', en: 'Curaçao' },
    // Pacific
    fji: { zh: '斐濟', en: 'Fiji' },
    gum: { zh: '關島', en: 'Guam' },
    // Additional countries
    ecu: { zh: '厄瓜多', en: 'Ecuador' },
    geo: { zh: '喬治亞', en: 'Georgia' },
    hnd: { zh: '宏都拉斯', en: 'Honduras' },
    jor: { zh: '約旦', en: 'Jordan' },
    ltu: { zh: '立陶宛', en: 'Lithuania' },
    mar: { zh: '摩洛哥', en: 'Morocco' },
    syc: { zh: '塞席爾', en: 'Seychelles' },
    ven: { zh: '委內瑞拉', en: 'Venezuela' }
};

// Device type mapping
const DEVICE_NAMES = {
    MOBILE: { zh: '📱 手機', en: '📱 Mobile', color: '#10B981' },
    DESKTOP: { zh: '💻 桌機', en: '💻 Desktop', color: '#3B82F6' },
    TABLET: { zh: '📟 平板', en: '📟 Tablet', color: '#F59E0B' }
};

// Helper function to format date to YYYY-MM-DD (local time)
const formatDate = (date) => {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
};

// Helper function to calculate date range from preset (aligned with GA4)
const getDateRangeFromPreset = (presetKey) => {
    const today = new Date();
    const preset = DATE_PRESETS.find(p => p.key === presetKey);

    if (!preset) {
        // Default fallback
        const start = new Date();
        start.setDate(today.getDate() - 30);
        return { start: formatDate(start), end: formatDate(today) };
    }

    // Today
    if (preset.isToday) {
        return { start: formatDate(today), end: formatDate(today) };
    }

    // Yesterday
    if (preset.isYesterday) {
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        return { start: formatDate(yesterday), end: formatDate(yesterday) };
    }

    // This Week (Monday to today)
    if (preset.isThisWeek) {
        const dayOfWeek = today.getDay();
        const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
        const monday = new Date(today);
        monday.setDate(monday.getDate() - daysToMonday);
        return { start: formatDate(monday), end: formatDate(today) };
    }

    // Last Week (Last Monday to Last Sunday)
    if (preset.isLastWeek) {
        const dayOfWeek = today.getDay();
        const daysToLastSunday = dayOfWeek === 0 ? 7 : dayOfWeek;
        const lastSunday = new Date(today);
        lastSunday.setDate(lastSunday.getDate() - daysToLastSunday);
        const lastMonday = new Date(lastSunday);
        lastMonday.setDate(lastMonday.getDate() - 6);
        return { start: formatDate(lastMonday), end: formatDate(lastSunday) };
    }

    // This Month (1st to last day of current month)
    if (preset.isThisMonth) {
        const firstOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
        const lastOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0);
        return { start: formatDate(firstOfMonth), end: formatDate(lastOfMonth) };
    }

    // Last Month (1st to last day of previous month)
    if (preset.isLastMonth) {
        const firstOfLastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
        const lastOfLastMonth = new Date(today.getFullYear(), today.getMonth(), 0);
        return { start: formatDate(firstOfLastMonth), end: formatDate(lastOfLastMonth) };
    }

    // Custom or null days - return current range or default
    if (preset.days === null) {
        const start = new Date();
        start.setDate(today.getDate() - 30);
        return { start: formatDate(start), end: formatDate(today) };
    }

    // For "last X days" presets (complete days, not including today)
    // e.g., "Last 7 days" = 7 complete days before today = (today-7) to (today-1)
    const end = new Date(today);
    end.setDate(today.getDate() - 1);  // Yesterday
    const start = new Date(today);
    start.setDate(today.getDate() - preset.days);  // X days before today
    return { start: formatDate(start), end: formatDate(end) };
};


// Helper: Extract main keyword for grouping (first significant word)
const extractGroupKey = (query) => {
    if (!query) return '';
    // Remove common suffixes/prefixes and get the main topic
    const words = query.trim().toLowerCase().split(/\s+/);
    // Get first 2 significant words for grouping
    const significantWords = words.filter(w => w.length > 1).slice(0, 2);
    return significantWords.join(' ') || query;
};

// Helper: Detect primary language of a string
const detectLanguage = (str) => {
    const chineseChars = (str.match(/[\u4e00-\u9fa5]/g) || []).length;
    const englishChars = (str.match(/[a-zA-Z]/g) || []).length;

    if (chineseChars > englishChars) return 'chinese';
    if (englishChars > chineseChars) return 'english';
    return 'mixed';
};

// Helper: N-gram similarity (better for Chinese)
const ngramSimilarity = (str1, str2, n = 2) => {
    const s1 = str1.toLowerCase().replace(/\s+/g, '');
    const s2 = str2.toLowerCase().replace(/\s+/g, '');

    if (s1.length < n || s2.length < n) {
        // Fallback to character overlap for very short strings
        const chars1 = new Set(s1.split(''));
        const chars2 = new Set(s2.split(''));
        const intersection = [...chars1].filter(c => chars2.has(c));
        const union = new Set([...chars1, ...chars2]);
        return union.size > 0 ? intersection.length / union.size : 0;
    }

    const getNgrams = (s) => {
        const ngrams = new Set();
        for (let i = 0; i <= s.length - n; i++) {
            ngrams.add(s.substring(i, i + n));
        }
        return ngrams;
    };

    const ngrams1 = getNgrams(s1);
    const ngrams2 = getNgrams(s2);
    const intersection = [...ngrams1].filter(ng => ngrams2.has(ng));
    const union = new Set([...ngrams1, ...ngrams2]);

    return union.size > 0 ? intersection.length / union.size : 0;
};

// Helper: Word-split similarity (better for English)
const wordSimilarity = (str1, str2) => {
    const s1 = str1.toLowerCase();
    const s2 = str2.toLowerCase();

    const words1 = new Set(s1.split(/\s+/).filter(w => w.length > 0));
    const words2 = new Set(s2.split(/\s+/).filter(w => w.length > 0));
    const intersection = [...words1].filter(w => words2.has(w));
    const union = new Set([...words1, ...words2]);

    return union.size > 0 ? intersection.length / union.size : 0;
};

// Helper: Adaptive similarity - uses optimal algorithm based on language
const getSimilarity = (str1, str2) => {
    const s1 = str1.toLowerCase();
    const s2 = str2.toLowerCase();

    // Quick check: if one contains the other, they're highly similar
    if (s1.includes(s2) || s2.includes(s1)) return 0.8;

    const lang1 = detectLanguage(str1);
    const lang2 = detectLanguage(str2);

    // Both Chinese → use N-gram (optimal for Chinese)
    if (lang1 === 'chinese' && lang2 === 'chinese') {
        return ngramSimilarity(str1, str2);
    }

    // Both English → use word-split (optimal for English)
    if (lang1 === 'english' && lang2 === 'english') {
        return wordSimilarity(str1, str2);
    }

    // Mixed languages → average of both methods
    return (ngramSimilarity(str1, str2) + wordSimilarity(str1, str2)) / 2;
};

// Helper: Extract a readable title from URL path
const getTitleFromUrl = (url) => {
    if (!url) return '';
    try {
        // Decode URL-encoded characters
        const decoded = decodeURIComponent(url);
        // Get the last path segment
        const path = decoded.replace(/^https?:\/\/[^/]+/, '');
        const segments = path.split('/').filter(s => s.length > 0);
        const lastSegment = segments[segments.length - 1] || '';

        // Remove file extension if any
        const withoutExt = lastSegment.replace(/\.(html?|php|aspx?)$/i, '');

        // Convert slug format to title case (handles both - and _ separators)
        const title = withoutExt
            .replace(/[-_]/g, ' ')
            .replace(/\b\w/g, c => c.toUpperCase());

        return title || path;
    } catch {
        // Fallback: just use the URL
        return url.replace(/^https?:\/\/[^/]+/, '');
    }
};

// API URL configuration for production deployment
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const GSCStats = ({ language, isMobile = false }) => {
    const t = (zh, en) => language === 'zh' ? zh : en;
    const [sites, setSites] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedSite, setSelectedSite] = useState('');
    const [analytics, setAnalytics] = useState([]);
    const [analyticsLoading, setAnalyticsLoading] = useState(false);

    // Query pagination state (server-side load more)
    const [queryOffset, setQueryOffset] = useState(0);
    const [queryHasMore, setQueryHasMore] = useState(true);
    const [queryLoadingMore, setQueryLoadingMore] = useState(false);

    // 新增：數據緩存狀態 - { cacheKey: data }
    const [analyticsCache, setAnalyticsCache] = useState({});
    // 新增：已載入的分頁追蹤 (預設載入 daily 分頁)
    const [loadedDimensions, setLoadedDimensions] = useState(new Set(['date']));

    // Tab State
    const [activeTab, setActiveTab] = useState('daily');

    // Date Range State
    const [datePreset, setDatePreset] = useState('last_28d');
    const [dateRange, setDateRange] = useState(getDateRangeFromPreset('last_28d'));
    const [showCustomDate, setShowCustomDate] = useState(false);

    // Compare Mode State
    const [compareMode, setCompareMode] = useState('none');
    const [compareData, setCompareData] = useState([]);
    const [compareLoading, setCompareLoading] = useState(false);


    // Keyword/Page specific state
    const [searchKeyword, setSearchKeyword] = useState('');
    const [sortConfig, setSortConfig] = useState({ key: 'clicks', direction: 'desc' });
    const [rowLimit, setRowLimit] = useState(50);
    const [displayLimit, setDisplayLimit] = useState(100); // Progressive rendering: start with 100 rows

    const queryPageSize = useMemo(() => {
        if (rowLimit === 99999) return 5000;
        return Math.max(rowLimit * 5, 2000);
    }, [rowLimit]);

    // Grouping state (for keyword tab)
    const [groupingEnabled, setGroupingEnabled] = useState(false);
    const [expandedGroups, setExpandedGroups] = useState(new Set());

    // Page keywords state (for page tab - shows keywords per page)
    const [pageKeywords, setPageKeywords] = useState({});
    const [expandedPages, setExpandedPages] = useState(new Set());

    // Page keywords pagination and load time state
    const [pageKeywordsOffset, setPageKeywordsOffset] = useState(0);
    const [pageKeywordsHasMore, setPageKeywordsHasMore] = useState(true);
    const [pageKeywordsLoading, setPageKeywordsLoading] = useState(false);
    const [pageKeywordsLoadTime, setPageKeywordsLoadTime] = useState(null);  // Load time in ms
    const [pageKeywordsTotalCount, setPageKeywordsTotalCount] = useState(0);  // Total keyword combinations loaded

    // Trend tab state
    const [trendSubTab, setTrendSubTab] = useState('top');
    const [trendData, setTrendData] = useState([]);
    const [trendLoading, setTrendLoading] = useState(false);

    // Page titles cache (for page tab and trend tab)
    const [pageTitles, setPageTitles] = useState({});
    const [titlesRefreshing, setTitlesRefreshing] = useState(false);

    // Search Intent Analysis state (AI-powered) - KEYWORD-LEVEL cache
    // Structure: { "關鍵字": { intent: "informational", confidence: 0.92 } }
    const [keywordIntents, setKeywordIntents] = useState(() => {
        try {
            const saved = localStorage.getItem('gsc_keyword_intents');
            return saved ? JSON.parse(saved) : {};
        } catch {
            return {};
        }
    });
    const [intentLoading, setIntentLoading] = useState({});  // { pageUrl: boolean }
    const [intentError, setIntentError] = useState({});  // { pageUrl: string }

    // Expanded keywords count per page (for "Load More" feature)
    const [expandedKeywordsCount, setExpandedKeywordsCount] = useState({});  // { pageUrl: number }

    // Persist keywordIntents to LocalStorage whenever it changes
    useEffect(() => {
        if (Object.keys(keywordIntents).length > 0) {
            try {
                localStorage.setItem('gsc_keyword_intents', JSON.stringify(keywordIntents));
            } catch (e) {
                console.warn('Failed to save keyword intents to LocalStorage:', e);
            }
        }
    }, [keywordIntents]);

    // Intent type labels and colors
    const INTENT_TYPES = {
        informational: { label_zh: '資訊型', label_en: 'Informational', color: '#3B82F6', emoji: '🔵' },
        commercial: { label_zh: '商業型', label_en: 'Commercial', color: '#F59E0B', emoji: '🟠' },
        navigational: { label_zh: '導航型', label_en: 'Navigational', color: '#10B981', emoji: '🟢' },
        transactional: { label_zh: '交易型', label_en: 'Transactional', color: '#EF4444', emoji: '🔴' }
    };

    // Dynamic page intent calculation based on top keywords
    const getPageIntent = (pageUrl) => {
        const keywords = pageKeywords[pageUrl] || [];
        if (keywords.length === 0) return null;

        // Only use top 10 keywords for page intent calculation
        const topKeywords = keywords.slice(0, 10);
        const totalClicks = topKeywords.reduce((sum, kw) => sum + (kw.clicks || 0), 0) || 1;

        // Calculate weighted intent distribution
        const distribution = {
            informational: 0,
            commercial: 0,
            navigational: 0,
            transactional: 0
        };

        let analyzedCount = 0;
        topKeywords.forEach(kw => {
            const query = kw.keyword || kw.query;
            const cached = keywordIntents[query];
            if (cached && cached.intent) {
                const weight = (kw.clicks || 0) / totalClicks;
                distribution[cached.intent] = (distribution[cached.intent] || 0) + weight;
                analyzedCount++;
            }
        });

        if (analyzedCount === 0) return null;

        // Find primary intent
        const primaryIntent = Object.entries(distribution)
            .sort((a, b) => b[1] - a[1])[0][0];

        return {
            primary_intent: primaryIntent,
            intent_distribution: distribution,
            analyzed_count: analyzedCount,
            total_count: topKeywords.length
        };
    };

    useEffect(() => {
        fetchSites();
    }, []);

    const fetchSites = async () => {
        try {
            const resp = await fetch(`${API_URL}/api/gsc/sites`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('google_token')}` }
            });
            const contentType = resp.headers.get("content-type");
            if (contentType && contentType.indexOf("application/json") !== -1) {
                const data = await resp.json();
                if (!resp.ok) throw new Error(data.detail || 'Failed to fetch sites');
                setSites(data);
                if (data.length > 0) setSelectedSite(data[0].siteUrl);
            } else {
                throw new Error("Server returned non-JSON response");
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };


    // Reset displayLimit when switching tabs, sites, or date range
    useEffect(() => {
        setDisplayLimit(100);
    }, [selectedSite, dateRange, activeTab, rowLimit]);

    // Reset query pagination when context changes
    useEffect(() => {
        if (activeTab === 'query') {
            setQueryOffset(0);
            setQueryHasMore(true);
            setQueryLoadingMore(false);
        }
        // Reset page keywords pagination when context changes
        if (activeTab === 'page') {
            setPageKeywordsOffset(0);
            setPageKeywordsHasMore(true);
            setPageKeywordsLoadTime(null);
        }
    }, [selectedSite, dateRange.start, dateRange.end, activeTab, rowLimit]);

    // 當網站或日期範圍改變時，清除緩存並重置載入狀態
    useEffect(() => {
        if (selectedSite && dateRange.start && dateRange.end) {
            setAnalyticsCache({});
            setLoadedDimensions(new Set());
            setAnalytics([]);
            // Also reset page keywords cache
            setPageKeywords({});
            setPageKeywordsTotalCount(0);
        }
    }, [selectedSite, dateRange.start, dateRange.end]);

    useEffect(() => {
        if (selectedSite && dateRange.start && dateRange.end) {
            const currentTab = TABS.find(tab => tab.key === activeTab);
            const dimension = currentTab ? currentTab.dimension : 'date';

            if (activeTab === 'trend') {
                // For trend tab, fetch both current and previous period
                fetchTrendData(selectedSite, dateRange.start, dateRange.end);
            } else {
                // 檢查是否已載入此dimension的數據
                if (!loadedDimensions.has(dimension)) {
                    fetchAnalytics(selectedSite, dateRange.start, dateRange.end, dimension);
                } else {
                    // 如果已載入，從緩存中恢復數據
                    const cacheKey = `${selectedSite}-${dateRange.start}-${dateRange.end}-${dimension}`;
                    if (analyticsCache[cacheKey]) {
                        setAnalytics(analyticsCache[cacheKey]);
                    }
                }

                // Fetch page+query data for page tab (to show keywords per page)
                if (activeTab === 'page') {
                    fetchPageKeywords(selectedSite, dateRange.start, dateRange.end);
                }
            }
        }
    }, [selectedSite, dateRange, activeTab, loadedDimensions, analyticsCache]);

    // Fetch page titles when page data is available
    useEffect(() => {
        if (activeTab === 'page' && analytics.length > 0) {
            const urls = analytics.slice(0, 50).map(row => row.keys?.[0]).filter(Boolean);
            if (urls.length > 0) {
                fetchPageTitles(urls);
            }
        } else if (activeTab === 'trend' && trendData.length > 0) {
            const urls = trendData.slice(0, 50).map(row => row.keys?.[0]).filter(Boolean);
            if (urls.length > 0) {
                fetchPageTitles(urls);
            }
        }
    }, [activeTab, analytics, trendData]);

    const fetchAnalytics = async (siteUrl, startDate, endDate, dimension = 'date', options = {}) => {
        const { append = false, offset = 0 } = options;

        // 建立緩存鍵
        const baseKey = `${siteUrl}-${startDate}-${endDate}-${dimension}`;
        const limit = dimension === 'query' ? queryPageSize : null;
        const cacheKey = dimension === 'query' ? `${baseKey}-${offset}-${limit}` : baseKey;
        const combinedKey = dimension === 'query' ? `${baseKey}-combined` : baseKey;

        // 檢查緩存中是否已有數據
        if (dimension === 'query') {
            if (!append && analyticsCache[combinedKey]) {
                console.log(`Using cached combined data for ${dimension}`);
                setAnalytics(analyticsCache[combinedKey]);
                return;
            }
            if (append && analyticsCache[cacheKey]) {
                console.log(`Using cached page data for ${dimension}`);
                setAnalytics(prev => {
                    const merged = [...prev, ...analyticsCache[cacheKey]];
                    setAnalyticsCache(prevCache => ({ ...prevCache, [combinedKey]: merged }));
                    return merged;
                });
                return;
            }
        } else if (analyticsCache[cacheKey]) {
            console.log(`Using cached data for ${dimension}`);
            setAnalytics(analyticsCache[cacheKey]);
            return;
        }

        console.log(`Fetching fresh data for ${dimension}`);
        if (dimension === 'query' && append) {
            setQueryLoadingMore(true);
        } else {
            setAnalyticsLoading(true);
        }

        try {
            const limitParam = limit ? `&limit=${limit}` : '';
            const offsetParam = dimension === 'query' && offset ? `&offset=${offset}` : '';
            const resp = await fetch(`${API_URL}/api/gsc/analytics?site_url=${encodeURIComponent(siteUrl)}&start_date=${startDate}&end_date=${endDate}&dimensions=${dimension}${limitParam}${offsetParam}`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('google_token')}` }
            });
            const data = await resp.json();
            if (!resp.ok) throw new Error(data.detail);

            if (dimension === 'query') {
                setAnalyticsCache(prev => ({ ...prev, [cacheKey]: data }));
                setAnalytics(prev => {
                    const merged = append ? [...prev, ...data] : data;
                    setAnalyticsCache(prevCache => ({ ...prevCache, [combinedKey]: merged }));
                    return merged;
                });

                if (append) {
                    setQueryOffset(offset);
                } else {
                    setQueryOffset(0);
                }

                if (limit && data.length < limit) {
                    setQueryHasMore(false);
                }
            } else {
                // 保存到緩存並更新當前數據
                setAnalyticsCache(prev => ({ ...prev, [cacheKey]: data }));
                setAnalytics(data);
            }

            // 標記此dimension已載入
            setLoadedDimensions(prev => new Set([...prev, dimension]));
        } catch (err) {
            console.error(err);
        } finally {
            if (dimension === 'query' && append) {
                setQueryLoadingMore(false);
            } else {
                setAnalyticsLoading(false);
            }
        }
    };

    // Page keywords pagination config
    const pageKeywordsPageSize = 2000;  // Load 2000 page+query combinations per request (reduced for faster initial load)

    // Fetch page+query dimension data to get keywords for each page (with pagination and load time tracking)
    const fetchPageKeywords = async (siteUrl, startDate, endDate, options = {}) => {
        const { append = false, offset = 0 } = options;
        const startTime = performance.now();

        if (!append) {
            setPageKeywordsLoading(true);
        }

        try {
            const limitParam = `&limit=${pageKeywordsPageSize}`;
            const offsetParam = offset > 0 ? `&offset=${offset}` : '';

            const resp = await fetch(`${API_URL}/api/gsc/analytics?site_url=${encodeURIComponent(siteUrl)}&start_date=${startDate}&end_date=${endDate}&dimensions=page,query${limitParam}${offsetParam}`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('google_token')}` }
            });
            const data = await resp.json();

            // Calculate load time
            const loadTime = Math.round(performance.now() - startTime);
            setPageKeywordsLoadTime(loadTime);

            if (!resp.ok) {
                setPageKeywordsLoading(false);
                return;
            }

            // Check if there are more pages
            if (data.length < pageKeywordsPageSize) {
                setPageKeywordsHasMore(false);
            }

            // Group keywords by page URL
            const newKeywordMap = {};
            data.forEach(row => {
                if (row.keys && row.keys.length >= 2) {
                    const pageUrl = row.keys[0];
                    const keyword = row.keys[1];
                    if (!newKeywordMap[pageUrl]) {
                        newKeywordMap[pageUrl] = [];
                    }
                    newKeywordMap[pageUrl].push({
                        keyword,
                        clicks: row.clicks,
                        impressions: row.impressions
                    });
                }
            });

            // Sort keywords by clicks within each page
            Object.keys(newKeywordMap).forEach(page => {
                newKeywordMap[page].sort((a, b) => b.clicks - a.clicks);
            });

            // Merge with existing data if appending
            if (append) {
                setPageKeywords(prev => {
                    const merged = { ...prev };
                    Object.keys(newKeywordMap).forEach(page => {
                        if (merged[page]) {
                            // Append and re-sort
                            merged[page] = [...merged[page], ...newKeywordMap[page]]
                                .sort((a, b) => b.clicks - a.clicks);
                        } else {
                            merged[page] = newKeywordMap[page];
                        }
                    });
                    return merged;
                });
                setPageKeywordsTotalCount(prev => prev + data.length);
            } else {
                setPageKeywords(newKeywordMap);
                setPageKeywordsTotalCount(data.length);
            }

            setPageKeywordsOffset(offset);
            console.log(`[Page Keywords] Loaded ${data.length} rows in ${loadTime}ms (offset: ${offset})`);
        } catch (err) {
            console.error('Failed to fetch page keywords:', err);
        } finally {
            setPageKeywordsLoading(false);
        }
    };

    // Load more page keywords from server
    const loadMorePageKeywords = () => {
        if (pageKeywordsLoading || !pageKeywordsHasMore) return;
        if (!selectedSite || !dateRange.start || !dateRange.end) return;

        const nextOffset = pageKeywordsOffset + pageKeywordsPageSize;
        fetchPageKeywords(selectedSite, dateRange.start, dateRange.end, { append: true, offset: nextOffset });
    };

    const loadMoreQueryData = () => {
        if (activeTab !== 'query' || queryLoadingMore || !queryHasMore) return;
        if (!selectedSite || !dateRange.start || !dateRange.end) return;

        const nextOffset = queryOffset + queryPageSize;
        fetchAnalytics(selectedSite, dateRange.start, dateRange.end, 'query', { append: true, offset: nextOffset });
    };

    // Fetch real page titles from backend (with database caching)
    // forceRefresh=true will bypass cache and re-fetch all titles
    const fetchPageTitles = async (urls, forceRefresh = false) => {
        // When not forcing refresh, filter URLs we don't already have titles for
        const newUrls = forceRefresh ? urls : urls.filter(url => !pageTitles[url]);
        if (newUrls.length === 0) return;

        try {
            const resp = await fetch(`${API_URL}/api/gsc/page-titles`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('google_token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    urls: newUrls.slice(0, 50),
                    force_refresh: forceRefresh
                })
            });

            if (!resp.ok) return;
            const titles = await resp.json();

            setPageTitles(prev => ({ ...prev, ...titles }));
        } catch (err) {
            console.error('Failed to fetch page titles:', err);
        }
    };

    // Fetch AI-powered search intent analysis for a specific page
    // analyzeAll: false = first-time analysis (top 10 only), true = continue analysis (all remaining up to 100)
    // Now stores results in KEYWORD-LEVEL cache, only analyzes uncached keywords
    const fetchPageIntent = async (pageUrl, analyzeAll = false) => {
        if (!selectedSite || !dateRange.start || !dateRange.end) return;
        if (intentLoading[pageUrl]) return; // Already loading

        // Get current keywords for this page
        const keywords = pageKeywords[pageUrl] || [];
        if (keywords.length === 0) {
            setIntentError(prev => ({ ...prev, [pageUrl]: 'No keywords available' }));
            return;
        }

        // Filter to only uncached keywords
        const uncachedKeywords = keywords.filter(kw => {
            const query = kw.keyword || kw.query;
            return !keywordIntents[query];
        });

        // If all keywords already cached, no need to call API
        if (uncachedKeywords.length === 0) {
            console.log(`All ${keywords.length} keywords already analyzed for ${pageUrl}`);
            return;
        }

        setIntentLoading(prev => ({ ...prev, [pageUrl]: true }));
        setIntentError(prev => ({ ...prev, [pageUrl]: null }));

        try {
            // First-time analysis: only top 10 keywords (to save API costs)
            // Continue analysis (analyzeAll=true): all remaining (up to 100)
            const maxKeywords = analyzeAll ? 100 : 10;
            const keywordsToAnalyze = uncachedKeywords.slice(0, maxKeywords).map(kw => kw.keyword || kw.query);

            // Build request body
            // For first-time analysis (analyzeAll=false): don't send keywords, let backend fetch from GSC
            // For continue analysis (analyzeAll=true): send specific keywords to skip GSC fetch
            const requestBody = {
                site_url: selectedSite,
                page_url: pageUrl,
                start_date: dateRange.start,
                end_date: dateRange.end,
                top_n: maxKeywords
            };
            // Determine AI provider based on user preference stored in localStorage (synced from backend)
            const savedProvider = localStorage.getItem('ai_provider') || 'zeabur';

            // Just pass provider to backend - backend will retrieve encrypted API key from database
            requestBody.provider = savedProvider;
            // Note: No need to send ai_api_key - backend will fetch from user's encrypted storage

            // Only send keywords array for continue analysis
            if (analyzeAll) {
                requestBody.keywords = keywordsToAnalyze;
            }

            const resp = await fetch(`${API_URL}/api/gsc/page-intents`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('google_token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });

            if (!resp.ok) {
                const error = await resp.json();
                throw new Error(error.detail || 'Intent analysis failed');
            }

            const data = await resp.json();
            console.log('API response data:', data);

            // Check if API key was missing (backend returns message about configuration)
            if (data.message && data.message.includes('not configured')) {
                throw new Error(data.message);
            }

            // Store each keyword's intent in the keyword-level cache
            // Skip 'unknown' intents - they indicate API failure and should be re-analyzable
            const newKeywordIntents = {};
            (data.keywords || []).forEach(kw => {
                const query = kw.query || kw.keyword;
                const intent = kw.intent;
                // Only cache valid intents, not 'unknown'
                if (query && intent && intent !== 'unknown') {
                    newKeywordIntents[query] = {
                        intent: intent,
                        confidence: kw.confidence || 0.8,
                        analyzed_at: new Date().toISOString()
                    };
                }
            });

            console.log('New keyword intents to add:', Object.keys(newKeywordIntents).length, newKeywordIntents);
            setKeywordIntents(prev => {
                const updated = { ...prev, ...newKeywordIntents };
                console.log('Total keyword intents after update:', Object.keys(updated).length);
                return updated;
            });
            console.log(`Analyzed ${Object.keys(newKeywordIntents).length} new keywords for ${pageUrl}`);
        } catch (err) {
            console.error('Failed to fetch page intent:', err);
            setIntentError(prev => ({ ...prev, [pageUrl]: err.message }));
        } finally {
            setIntentLoading(prev => ({ ...prev, [pageUrl]: false }));
        }
    };

    // Fetch trend data (compare current period with previous period)
    const fetchTrendData = async (siteUrl, startDate, endDate) => {
        // 建立 trend 專用的緩存鍵
        const cacheKey = `trend-${siteUrl}-${startDate}-${endDate}`;

        // 檢查緩存
        if (analyticsCache[cacheKey]) {
            console.log('Using cached trend data');
            setTrendData(analyticsCache[cacheKey]);
            return;
        }

        console.log('Fetching fresh trend data');
        setTrendLoading(true);
        try {
            // Calculate previous period dates
            const start = new Date(startDate);
            const end = new Date(endDate);
            const daysDiff = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1;

            const prevEnd = new Date(start);
            prevEnd.setDate(prevEnd.getDate() - 1);
            const prevStart = new Date(prevEnd);
            prevStart.setDate(prevStart.getDate() - daysDiff + 1);

            const prevStartStr = formatDate(prevStart);
            const prevEndStr = formatDate(prevEnd);

            // Fetch both periods in parallel
            const [currentResp, prevResp] = await Promise.all([
                fetch(`${API_URL}/api/gsc/analytics?site_url=${encodeURIComponent(siteUrl)}&start_date=${startDate}&end_date=${endDate}&dimensions=page`, {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('google_token')}` }
                }),
                fetch(`${API_URL}/api/gsc/analytics?site_url=${encodeURIComponent(siteUrl)}&start_date=${prevStartStr}&end_date=${prevEndStr}&dimensions=page`, {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('google_token')}` }
                })
            ]);

            const currentData = await currentResp.json();
            const prevData = await prevResp.json();

            if (!currentResp.ok) throw new Error(currentData.detail);

            // Create a map of previous period data
            const prevMap = {};
            (prevData || []).forEach(row => {
                const url = row.keys?.[0];
                if (url) {
                    prevMap[url] = {
                        clicks: row.clicks,
                        impressions: row.impressions
                    };
                }
            });

            // Calculate changes for each page
            const trendResults = (currentData || []).map(row => {
                const url = row.keys?.[0];
                const prev = prevMap[url] || { clicks: 0, impressions: 0 };

                const clicksChange = prev.clicks > 0
                    ? ((row.clicks - prev.clicks) / prev.clicks * 100)
                    : (row.clicks > 0 ? 100 : 0);

                const impressionsChange = prev.impressions > 0
                    ? ((row.impressions - prev.impressions) / prev.impressions * 100)
                    : (row.impressions > 0 ? 100 : 0);

                return {
                    ...row,
                    prevClicks: prev.clicks,
                    prevImpressions: prev.impressions,
                    clicksChange,
                    impressionsChange
                };
            });

            // 保存到緩存並更新數據
            setAnalyticsCache(prev => ({ ...prev, [cacheKey]: trendResults }));
            setTrendData(trendResults);
        } catch (err) {
            console.error('Failed to fetch trend data:', err);
        } finally {
            setTrendLoading(false);
        }
    };
    const handlePresetChange = (presetKey) => {
        setDatePreset(presetKey);
        if (presetKey === 'custom') {
            setShowCustomDate(true);
        } else {
            setShowCustomDate(false);
            setDateRange(getDateRangeFromPreset(presetKey));
        }
    };

    const handleCustomDateChange = (field, value) => {
        setDateRange(prev => ({ ...prev, [field]: value }));
    };

    const getDaysInRange = () => {
        const start = new Date(dateRange.start);
        const end = new Date(dateRange.end);
        const diffTime = Math.abs(end - start);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
        return diffDays;
    };

    // Compare Mode Functions
    const getCompareDateRange = () => {
        if (compareMode === 'none') return null;

        const start = new Date(dateRange.start);
        const end = new Date(dateRange.end);
        const daysDiff = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1;

        if (compareMode === 'previous_period') {
            // 前一時段：相同天數往前推
            const prevEnd = new Date(start);
            prevEnd.setDate(prevEnd.getDate() - 1);
            const prevStart = new Date(prevEnd);
            prevStart.setDate(prevStart.getDate() - daysDiff + 1);
            return { start: formatDate(prevStart), end: formatDate(prevEnd) };
        } else if (compareMode === 'previous_year') {
            // 去年同期
            const prevStart = new Date(start);
            prevStart.setFullYear(prevStart.getFullYear() - 1);
            const prevEnd = new Date(end);
            prevEnd.setFullYear(prevEnd.getFullYear() - 1);
            return { start: formatDate(prevStart), end: formatDate(prevEnd) };
        }
        return null;
    };

    const fetchCompareData = async (compareDateRange) => {
        if (!selectedSite || !compareDateRange) return;

        setCompareLoading(true);
        try {
            const currentTab = TABS.find(tab => tab.key === activeTab);
            const dimension = currentTab?.dimension || 'date';

            const resp = await fetch(
                `${API_URL}/api/gsc/analytics?site_url=${encodeURIComponent(selectedSite)}&start_date=${compareDateRange.start}&end_date=${compareDateRange.end}&dimensions=${dimension}`,
                { headers: { 'Authorization': `Bearer ${localStorage.getItem('google_token')}` } }
            );
            const data = await resp.json();
            if (resp.ok) {
                setCompareData(data);
            }
        } catch (err) {
            console.error('Failed to fetch compare data:', err);
        } finally {
            setCompareLoading(false);
        }
    };

    const calculateChange = (current, previous) => {
        if (previous === 0) return current > 0 ? 100 : 0;
        return ((current - previous) / previous * 100);
    };

    // Compute compare totals from compare data
    const getCompareTotals = () => {
        if (!compareData || compareData.length === 0) return null;

        const totals = {
            clicks: 0,
            impressions: 0,
            ctr: 0,
            position: 0
        };

        compareData.forEach(row => {
            totals.clicks += row.clicks || 0;
            totals.impressions += row.impressions || 0;
            totals.ctr += row.ctr || 0;
            totals.position += row.position || 0;
        });

        // Average CTR and position
        const count = compareData.length || 1;
        totals.ctr = totals.ctr / count;
        totals.position = totals.position / count;

        return totals;
    };

    // Effect: Fetch compare data when compare mode changes
    useEffect(() => {
        if (compareMode !== 'none' && selectedSite && dateRange.start && dateRange.end) {
            const compareDateRange = getCompareDateRange();
            if (compareDateRange) {
                fetchCompareData(compareDateRange);
            }
        } else {
            setCompareData([]);
        }
    }, [compareMode, selectedSite, dateRange, activeTab]);


    const handleSort = (key) => {
        setSortConfig(prev => ({
            key,
            direction: prev.key === key && prev.direction === 'desc' ? 'asc' : 'desc'
        }));
    };

    const toggleGroup = (groupKey) => {
        setExpandedGroups(prev => {
            const next = new Set(prev);
            if (next.has(groupKey)) {
                next.delete(groupKey);
            } else {
                next.add(groupKey);
            }
            return next;
        });
    };

    const togglePageExpand = (pageUrl) => {
        setExpandedPages(prev => {
            const next = new Set(prev);
            if (next.has(pageUrl)) {
                next.delete(pageUrl);
            } else {
                next.add(pageUrl);
            }
            return next;
        });
    };

    // Get performance indicator for page tab (Top 5 green, Bottom 5 red)
    const getPerformanceIndicator = (index, totalLength) => {
        if (totalLength < 10) return null;
        if (index < 5) return { type: 'top', label: '🏆', color: '#10B981' };
        if (index >= totalLength - 5) return { type: 'bottom', label: '⚠️', color: '#EF4444' };
        return null;
    };

    // Group keywords by similarity
    const groupedData = useMemo(() => {
        if (!groupingEnabled || activeTab !== 'query') return null;

        let data = [...analytics];

        // Filter by search
        if (searchKeyword) {
            const lowerSearch = searchKeyword.toLowerCase();
            data = data.filter(row =>
                row.keys && row.keys[0] && row.keys[0].toLowerCase().includes(lowerSearch)
            );
        }

        // Sort first
        data.sort((a, b) => {
            let aVal = a[sortConfig.key] ?? 0;
            let bVal = b[sortConfig.key] ?? 0;
            return sortConfig.direction === 'desc' ? bVal - aVal : aVal - bVal;
        });

        // Group similar keywords
        const groups = [];
        const assigned = new Set();

        for (let i = 0; i < Math.min(data.length, rowLimit * 2); i++) {
            if (assigned.has(i)) continue;

            const mainQuery = data[i].keys?.[0] || '';
            const group = {
                mainKeyword: mainQuery,
                items: [data[i]],
                totalClicks: data[i].clicks,
                totalImpressions: data[i].impressions
            };
            assigned.add(i);

            // Find similar keywords
            for (let j = i + 1; j < Math.min(data.length, rowLimit * 3); j++) {
                if (assigned.has(j)) continue;

                const otherQuery = data[j].keys?.[0] || '';
                const similarity = getSimilarity(mainQuery, otherQuery);

                if (similarity >= 0.4) {
                    group.items.push(data[j]);
                    group.totalClicks += data[j].clicks;
                    group.totalImpressions += data[j].impressions;
                    assigned.add(j);
                }
            }

            groups.push(group);
            if (groups.length >= rowLimit) break;
        }

        // Sort groups by total clicks
        groups.sort((a, b) => b.totalClicks - a.totalClicks);

        return groups;
    }, [analytics, groupingEnabled, activeTab, searchKeyword, sortConfig, rowLimit]);

    // Get sorted and filtered data (non-grouped view)
    // Returns { displayData, totalCount, hasMore } for progressive rendering
    const getSortedFilteredData = () => {
        let data = [...analytics];

        if (searchKeyword && (activeTab === 'query' || activeTab === 'page')) {
            const lowerSearch = searchKeyword.toLowerCase();
            data = data.filter(row =>
                row.keys && row.keys[0] && row.keys[0].toLowerCase().includes(lowerSearch)
            );
        }

        data.sort((a, b) => {
            // Special handling for date sorting (date is in keys[0])
            if (sortConfig.key === 'date') {
                const aVal = a.keys?.[0] || '';
                const bVal = b.keys?.[0] || '';
                return sortConfig.direction === 'desc'
                    ? bVal.localeCompare(aVal)
                    : aVal.localeCompare(bVal);
            }
            let aVal = a[sortConfig.key] ?? 0;
            let bVal = b[sortConfig.key] ?? 0;
            return sortConfig.direction === 'desc' ? bVal - aVal : aVal - bVal;
        });

        // Apply rowLimit first (user's selection)
        if (activeTab !== 'daily') {
            data = data.slice(0, rowLimit);
        }

        const totalCount = data.length;
        // Apply displayLimit for progressive rendering
        const effectiveLimit = Math.min(displayLimit, totalCount);
        const displayData = data.slice(0, effectiveLimit);
        const hasMore = effectiveLimit < totalCount;

        return { displayData, totalCount, hasMore };
    };

    // Get sorted trend data based on sub-tab selection
    const getSortedTrendData = () => {
        let data = [...trendData];

        // Filter by search
        if (searchKeyword) {
            const lowerSearch = searchKeyword.toLowerCase();
            data = data.filter(row =>
                row.keys && row.keys[0] && row.keys[0].toLowerCase().includes(lowerSearch)
            );
        }

        // Sort based on sub-tab
        // GSC uses ABSOLUTE click difference, not percentage change
        switch (trendSubTab) {
            case 'top':
                // Sort by absolute clicks (descending) - "熱門：點擊次數最多的內容"
                data.sort((a, b) => b.clicks - a.clicks);
                break;
            case 'up':
                // Sort by absolute click GROWTH (descending) - "趨勢上升：點擊次數成長最多的內容"
                data = data.filter(row => (row.clicks - row.prevClicks) > 0);
                data.sort((a, b) => (b.clicks - b.prevClicks) - (a.clicks - a.prevClicks));
                break;
            case 'down':
                // Sort by absolute click DECREASE (ascending) - "趨勢下降：點擊次數減少最多的內容"
                data = data.filter(row => (row.clicks - row.prevClicks) < 0);
                data.sort((a, b) => (a.clicks - a.prevClicks) - (b.clicks - b.prevClicks));
                break;
            default:
                data.sort((a, b) => b.clicks - a.clicks);
        }

        return data.slice(0, rowLimit);
    };
    // Styles
    const containerStyle = {
        display: 'flex',
        flexDirection: 'column',
        gap: isMobile ? '16px' : '24px',
        width: '100%',
        maxWidth: '100%',
        overflow: 'hidden',
        boxSizing: 'border-box'
    };

    const headerStyle = {
        display: 'flex',
        flexDirection: isMobile ? 'column' : 'row',
        alignItems: isMobile ? 'stretch' : 'center',
        gap: isMobile ? '8px' : '16px'
    };

    const labelStyle = {
        color: 'var(--text-primary)',
        fontWeight: '500',
        fontSize: isMobile ? '0.9rem' : '1rem'
    };

    const selectStyle = {
        padding: isMobile ? '10px 12px' : '8px 12px',
        borderRadius: '8px',
        border: '1px solid var(--glass-border)',
        background: 'var(--bg-secondary)',
        color: 'var(--text-primary)',
        outline: 'none',
        fontSize: isMobile ? '0.9rem' : '1rem',
        width: isMobile ? '100%' : 'auto'
    };

    const gridStyle = {
        display: 'grid',
        gridTemplateColumns: isMobile ? 'calc(50% - 4px) calc(50% - 4px)' : 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: isMobile ? '8px' : '16px',
        width: '100%',
        boxSizing: 'border-box'
    };

    const cardStyle = {
        background: 'var(--bg-secondary)',
        padding: isMobile ? '12px' : '20px',
        borderRadius: isMobile ? '8px' : '12px',
        border: '1px solid var(--glass-border)',
        boxShadow: 'var(--shadow-sm)',
        minWidth: 0
    };

    const cardLabelStyle = {
        fontSize: isMobile ? '12px' : '14px',
        color: 'var(--text-secondary)',
        marginBottom: '8px'
    };

    const cardValueStyle = {
        fontSize: isMobile ? '16px' : '24px',
        fontWeight: 'bold',
        color: 'var(--text-primary)',
        wordBreak: 'break-word'
    };

    const tableContainerStyle = {
        background: 'var(--bg-secondary)',
        borderRadius: '12px',
        border: '1px solid var(--glass-border)',
        overflow: 'hidden'
    };

    const tableHeaderStyle = {
        padding: isMobile ? '12px 16px' : '16px',
        borderBottom: '1px solid var(--glass-border)',
        fontWeight: 'bold',
        color: 'var(--text-primary)',
        fontSize: isMobile ? '0.95rem' : '1rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '8px'
    };

    const tableScrollStyle = {
        overflowX: 'auto',
        WebkitOverflowScrolling: 'touch',
        maxWidth: '100%'
    };

    const tableStyle = {
        width: '100%',
        borderCollapse: 'collapse',
        textAlign: 'left',
        minWidth: '600px'
    };

    const thStyle = {
        padding: isMobile ? '10px 12px' : '12px 24px',
        fontSize: isMobile ? '11px' : '12px',
        color: 'var(--text-secondary)',
        textTransform: 'uppercase',
        borderBottom: '1px solid var(--glass-border)',
        whiteSpace: 'nowrap',
        cursor: 'pointer',
        userSelect: 'none'
    };

    const tdStyle = {
        padding: isMobile ? '12px' : '16px 24px',
        fontSize: isMobile ? '13px' : '14px',
        color: 'var(--text-primary)',
        borderBottom: '1px solid var(--glass-border)'
    };

    const tabContainerStyle = {
        display: 'flex',
        gap: '4px',
        background: 'var(--bg-secondary)',
        padding: '4px',
        borderRadius: '12px',
        border: '1px solid var(--glass-border)',
        overflowX: 'auto',
        WebkitOverflowScrolling: 'touch'
    };

    const tabStyle = (isActive) => ({
        padding: isMobile ? '10px 16px' : '12px 20px',
        borderRadius: '8px',
        border: 'none',
        background: isActive ? 'var(--accent-primary)' : 'transparent',
        color: isActive ? 'white' : 'var(--text-secondary)',
        fontWeight: isActive ? '600' : '500',
        fontSize: isMobile ? '13px' : '14px',
        cursor: 'pointer',
        transition: 'all 0.2s',
        whiteSpace: 'nowrap'
    });

    const searchInputStyle = {
        padding: '8px 12px',
        borderRadius: '8px',
        border: '1px solid var(--glass-border)',
        background: 'var(--bg-primary)',
        color: 'var(--text-primary)',
        outline: 'none',
        fontSize: '14px',
        width: isMobile ? '100%' : '200px'
    };

    const toggleButtonStyle = (isActive) => ({
        padding: '8px 12px',
        borderRadius: '8px',
        border: `1px solid ${isActive ? 'var(--accent-primary)' : 'var(--glass-border)'}`,
        background: isActive ? 'var(--accent-primary)' : 'transparent',
        color: isActive ? 'white' : 'var(--text-secondary)',
        fontSize: '13px',
        cursor: 'pointer',
        transition: 'all 0.2s',
        whiteSpace: 'nowrap'
    });

    const groupRowStyle = {
        background: 'var(--bg-hover)',
        cursor: 'pointer',
        fontWeight: '600'
    };

    const childRowStyle = {
        background: 'var(--bg-primary)',
        paddingLeft: '40px'
    };

    const renderSortIndicator = (key) => {
        if (sortConfig.key !== key) return ' ↕';
        return sortConfig.direction === 'desc' ? ' ↓' : ' ↑';
    };

    if (loading) return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '60px 20px',
            background: 'rgba(255, 255, 255, 0.02)',
            borderRadius: '16px',
            border: '1px solid var(--glass-border)',
            margin: '20px'
        }}>
            {/* Spinner Animation */}
            <div style={{
                width: '48px',
                height: '48px',
                border: '4px solid rgba(52, 168, 83, 0.2)',
                borderTop: '4px solid #34a853',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite',
                marginBottom: '20px'
            }} />

            {/* Main Message */}
            <div style={{
                fontSize: '16px',
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginBottom: '8px'
            }}>
                {t('正在載入 Search Console 網站列表', 'Loading Search Console sites')}
            </div>

            {/* Sub Message */}
            <div style={{
                fontSize: '14px',
                color: 'var(--text-secondary)',
                textAlign: 'center'
            }}>
                {t('請稍候...', 'Please wait...')}
            </div>

            {/* CSS Animation Keyframes */}
            <style>{`
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            `}</style>
        </div>
    );

    if (error) return (
        <div style={{ padding: '20px', color: '#ea4335' }}>
            {t('錯誤:', 'Error:')} {error}
        </div>
    );

    const { displayData: sortedData, totalCount: sortedDataTotal, hasMore: sortedDataHasMore } = getSortedFilteredData();
    const showGroupedView = groupingEnabled && activeTab === 'query' && groupedData;

    return (
        <div style={containerStyle}>
            {/* Main Settings Panel - Glass Style (aligned with GA4) */}
            <div className="glass-panel" style={{
                padding: isMobile ? '16px' : '24px',
                borderRadius: '16px',
                marginBottom: '24px',
                background: 'rgba(255, 255, 255, 0.03)',
                border: '1px solid var(--glass-border)',
                backdropFilter: 'blur(10px)'
            }}>
                <h3 style={{
                    margin: '0 0 20px 0',
                    fontSize: '0.95rem',
                    color: 'var(--text-secondary)',
                    fontWeight: 600,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                }}>
                    ⚙️ {t('主要設定', 'Main Settings')}
                </h3>

                {/* Row 1: Site Selector + Date Range */}
                <div style={{
                    display: 'flex',
                    flexDirection: isMobile ? 'column' : 'row',
                    gap: '20px',
                    flexWrap: 'wrap'
                }}>
                    {/* Site Selector */}
                    <div style={{ flex: 1, minWidth: isMobile ? '100%' : '200px' }}>
                        <label style={{
                            display: 'block',
                            marginBottom: '8px',
                            fontWeight: 600,
                            color: 'var(--text-secondary)',
                            fontSize: '0.85rem'
                        }}>
                            {t('選擇資源', 'Select Property')}
                        </label>
                        <select
                            value={selectedSite}
                            onChange={(e) => setSelectedSite(e.target.value)}
                            style={{
                                width: '100%',
                                padding: '10px 12px',
                                border: '1px solid var(--glass-border)',
                                borderRadius: '8px',
                                background: 'rgba(255, 255, 255, 0.05)',
                                color: 'var(--text-primary)',
                                fontSize: '14px'
                            }}
                        >
                            {sites.map(site => (
                                <option key={site.siteUrl} value={site.siteUrl} style={{ color: 'black' }}>
                                    {site.siteUrl} ({site.permissionLevel})
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Date Range Selector */}
                    <div style={{ flex: 1, minWidth: isMobile ? '100%' : '180px' }}>
                        <label style={{
                            display: 'block',
                            marginBottom: '8px',
                            fontWeight: 600,
                            color: 'var(--text-secondary)',
                            fontSize: '0.85rem'
                        }}>
                            {t('日期範圍', 'Date Range')}
                        </label>
                        <select
                            value={datePreset}
                            onChange={(e) => handlePresetChange(e.target.value)}
                            style={{
                                width: '100%',
                                padding: '10px 12px',
                                border: '1px solid var(--glass-border)',
                                borderRadius: '8px',
                                background: 'rgba(255, 255, 255, 0.05)',
                                color: 'var(--text-primary)',
                                fontSize: '14px'
                            }}
                        >
                            {DATE_PRESETS.map(preset => (
                                <option key={preset.key} value={preset.key} style={{ color: 'black' }}>
                                    {language === 'zh' ? preset.label_zh : preset.label_en}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Compare Mode Selector */}
                    <div style={{ flex: 1, minWidth: isMobile ? '100%' : '150px' }}>
                        <label style={{
                            display: 'block',
                            marginBottom: '8px',
                            fontWeight: 600,
                            color: 'var(--text-secondary)',
                            fontSize: '0.85rem'
                        }}>
                            📊 {t('比較模式', 'Compare Mode')}
                        </label>
                        <select
                            value={compareMode}
                            onChange={(e) => setCompareMode(e.target.value)}
                            style={{
                                width: '100%',
                                padding: '10px 12px',
                                border: '1px solid var(--glass-border)',
                                borderRadius: '8px',
                                background: 'rgba(255, 255, 255, 0.05)',
                                color: 'var(--text-primary)',
                                fontSize: '14px'
                            }}
                        >
                            {COMPARE_OPTIONS.map(opt => (
                                <option key={opt.key} value={opt.key} style={{ color: 'black' }}>
                                    {language === 'zh' ? opt.label_zh : opt.label_en}
                                </option>
                            ))}
                        </select>
                    </div>
                </div>

                {/* Date Range Info Bar - Always visible (aligned with GA4) */}
                <div style={{
                    marginTop: '16px',
                    padding: '12px 16px',
                    background: compareMode !== 'none' ? 'rgba(139, 92, 246, 0.1)' : 'rgba(66, 133, 244, 0.1)',
                    borderRadius: '8px',
                    border: `1px solid ${compareMode !== 'none' ? 'rgba(139, 92, 246, 0.2)' : 'rgba(66, 133, 244, 0.2)'}`,
                    fontSize: '13px',
                    color: 'var(--text-secondary)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    flexWrap: 'wrap'
                }}>
                    {/* Current Period */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        📆 {t('目前期間', 'Current Period')}:
                        <strong style={{ color: 'var(--text-primary)' }}>
                            {dateRange.start} ~ {dateRange.end}
                        </strong>
                        <span style={{ opacity: 0.7 }}>
                            ({getDaysInRange()} {t('天', 'days')})
                        </span>
                    </div>

                    {/* Compare Period - Only when enabled */}
                    {compareMode !== 'none' && getCompareDateRange() && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span style={{ color: 'var(--text-secondary)' }}>|</span>
                            📊 {compareMode === 'previous_period' ? t('前一時段', 'Previous Period') : t('去年同期', 'Previous Year')}:
                            <strong style={{ color: '#a78bfa' }}>
                                {getCompareDateRange().start} ~ {getCompareDateRange().end}
                            </strong>
                        </div>
                    )}
                </div>


                {/* Custom Date Picker - Inline when selected */}
                {showCustomDate && (
                    <div style={{
                        marginTop: '20px',
                        paddingTop: '20px',
                        borderTop: '1px solid var(--glass-border)'
                    }}>
                        <div style={{
                            display: 'flex',
                            flexDirection: isMobile ? 'column' : 'row',
                            gap: '16px',
                            alignItems: isMobile ? 'stretch' : 'flex-end'
                        }}>
                            {/* Start Date */}
                            <div style={{ flex: 1 }}>
                                <label style={{
                                    display: 'block',
                                    marginBottom: '8px',
                                    fontWeight: 600,
                                    color: 'var(--text-secondary)',
                                    fontSize: '0.85rem'
                                }}>
                                    {t('開始日期', 'Start Date')}
                                </label>
                                <input
                                    type="date"
                                    value={dateRange.start}
                                    max={dateRange.end}
                                    onChange={(e) => handleCustomDateChange('start', e.target.value)}
                                    style={{
                                        width: '100%',
                                        padding: '10px 12px',
                                        border: '1px solid var(--glass-border)',
                                        borderRadius: '8px',
                                        background: 'rgba(255, 255, 255, 0.05)',
                                        color: 'var(--text-primary)',
                                        fontSize: '14px',
                                        colorScheme: 'dark'
                                    }}
                                />
                            </div>

                            {/* End Date */}
                            <div style={{ flex: 1 }}>
                                <label style={{
                                    display: 'block',
                                    marginBottom: '8px',
                                    fontWeight: 600,
                                    color: 'var(--text-secondary)',
                                    fontSize: '0.85rem'
                                }}>
                                    {t('結束日期', 'End Date')}
                                </label>
                                <input
                                    type="date"
                                    value={dateRange.end}
                                    min={dateRange.start}
                                    max={formatDate(new Date())}
                                    onChange={(e) => handleCustomDateChange('end', e.target.value)}
                                    style={{
                                        width: '100%',
                                        padding: '10px 12px',
                                        border: '1px solid var(--glass-border)',
                                        borderRadius: '8px',
                                        background: 'rgba(255, 255, 255, 0.05)',
                                        color: 'var(--text-primary)',
                                        fontSize: '14px',
                                        colorScheme: 'dark'
                                    }}
                                />
                            </div>
                        </div>

                        {/* Quick Selection Buttons */}
                        <div style={{
                            display: 'flex',
                            flexWrap: 'wrap',
                            gap: '8px',
                            marginTop: '16px',
                            alignItems: 'center'
                        }}>
                            <span style={{
                                fontSize: '13px',
                                color: 'var(--text-secondary)',
                                marginRight: '8px'
                            }}>
                                {t('快速選擇：', 'Quick select:')}
                            </span>
                            {[
                                { label: t('今天', 'Today'), key: 'today' },
                                { label: t('昨天', 'Yesterday'), key: 'yesterday' },
                                { label: t('本週', 'This Week'), key: 'this_week' },
                                { label: t('上週', 'Last Week'), key: 'last_week' },
                                { label: t('本月', 'This Month'), key: 'this_month' },
                                { label: t('上月', 'Last Month'), key: 'last_month' }
                            ].map(quick => (
                                <button
                                    key={quick.key}
                                    onClick={() => {
                                        const range = getDateRangeFromPreset(quick.key);
                                        setDateRange(range);
                                    }}
                                    style={{
                                        padding: '6px 12px',
                                        border: '1px solid var(--glass-border)',
                                        borderRadius: '16px',
                                        background: 'rgba(255, 255, 255, 0.05)',
                                        color: 'var(--text-secondary)',
                                        fontSize: '12px',
                                        cursor: 'pointer',
                                        transition: 'all 0.2s'
                                    }}
                                    onMouseOver={(e) => {
                                        e.target.style.background = 'var(--accent-primary)';
                                        e.target.style.color = 'white';
                                    }}
                                    onMouseOut={(e) => {
                                        e.target.style.background = 'rgba(255, 255, 255, 0.05)';
                                        e.target.style.color = 'var(--text-secondary)';
                                    }}
                                >
                                    {quick.label}
                                </button>
                            ))}
                        </div>
                    </div>
                )}
            </div>


            {/* Tab Navigation */}
            <div style={tabContainerStyle}>
                {TABS.map(tab => (
                    <button
                        key={tab.key}
                        onClick={() => setActiveTab(tab.key)}
                        style={tabStyle(activeTab === tab.key)}
                    >
                        {language === 'zh' ? tab.label_zh : tab.label_en}
                    </button>
                ))}
            </div>

            {(analyticsLoading || (activeTab === 'trend' && trendLoading)) ? (
                <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '60px 20px',
                    background: 'rgba(255, 255, 255, 0.02)',
                    borderRadius: '16px',
                    border: '1px solid var(--glass-border)',
                    marginTop: '24px'
                }}>
                    {/* Spinner Animation */}
                    <div style={{
                        width: '48px',
                        height: '48px',
                        border: '4px solid rgba(52, 168, 83, 0.2)',
                        borderTop: '4px solid #34a853',
                        borderRadius: '50%',
                        animation: 'spin 1s linear infinite',
                        marginBottom: '20px'
                    }} />

                    {/* Main Message */}
                    <div style={{
                        fontSize: '16px',
                        fontWeight: 600,
                        color: 'var(--text-primary)',
                        marginBottom: '8px'
                    }}>
                        {t('正在從 Search Console 抓取數據', 'Fetching data from Search Console')}
                    </div>

                    {/* Sub Message */}
                    <div style={{
                        fontSize: '14px',
                        color: 'var(--text-secondary)',
                        textAlign: 'center'
                    }}>
                        {t('請稍候，這可能需要幾秒鐘...', 'Please wait, this may take a few seconds...')}
                    </div>

                    {/* CSS Animation Keyframes */}
                    <style>{`
                        @keyframes spin {
                            0% { transform: rotate(0deg); }
                            100% { transform: rotate(360deg); }
                        }
                    `}</style>
                </div>
            ) : (
                <>
                    {/* Summary Cards - hide for trend tab */}
                    {activeTab !== 'trend' && (() => {
                        // Calculate current totals
                        const currentClicks = analytics.reduce((acc, row) => acc + row.clicks, 0);
                        const currentImpressions = analytics.reduce((acc, row) => acc + row.impressions, 0);
                        const currentCtr = analytics.reduce((acc, row) => acc + row.ctr, 0) / (analytics.length || 1) * 100;
                        const currentPosition = analytics.reduce((acc, row) => acc + row.position, 0) / (analytics.length || 1);

                        // Get compare totals
                        const compareTotals = getCompareTotals();

                        // Calculate changes if compare mode is active
                        const clicksChange = compareTotals ? calculateChange(currentClicks, compareTotals.clicks) : null;
                        const impressionsChange = compareTotals ? calculateChange(currentImpressions, compareTotals.impressions) : null;
                        const ctrChange = compareTotals ? calculateChange(currentCtr, compareTotals.ctr * 100) : null;
                        const positionChange = compareTotals ? calculateChange(currentPosition, compareTotals.position) : null;

                        // Helper to render change badge with previous value
                        const renderCompareInfo = (change, previousValue, formatter = (v) => v.toLocaleString(), isPositionMetric = false) => {
                            if (compareMode === 'none' || change === null) return null;
                            // For position, lower is better so reverse the color logic
                            const isPositive = isPositionMetric ? change < 0 : change >= 0;
                            const displayChange = isPositionMetric ? -change : change;
                            return (
                                <div style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '8px',
                                    marginTop: '6px'
                                }}>
                                    <span style={{
                                        fontSize: '12px',
                                        padding: '2px 8px',
                                        borderRadius: '12px',
                                        background: isPositive ? 'rgba(52, 168, 83, 0.15)' : 'rgba(234, 67, 53, 0.15)',
                                        color: isPositive ? '#34a853' : '#ea4335',
                                        fontWeight: 600
                                    }}>
                                        {isPositive ? '▲' : '▼'} {Math.abs(displayChange).toFixed(1)}%
                                    </span>
                                    <span style={{
                                        fontSize: '11px',
                                        color: 'var(--text-secondary)',
                                        opacity: 0.7
                                    }}>
                                        vs {formatter(previousValue)}
                                    </span>
                                </div>
                            );
                        };

                        return (
                            <div style={gridStyle}>
                                <div style={cardStyle}>
                                    <div style={cardLabelStyle}>{t(`總點擊數 (${getDaysInRange()}天)`, `Total Clicks (${getDaysInRange()}d)`)}</div>
                                    <div style={cardValueStyle}>
                                        {currentClicks.toLocaleString()}
                                    </div>
                                    {renderCompareInfo(clicksChange, compareTotals?.clicks || 0)}
                                </div>
                                <div style={cardStyle}>
                                    <div style={cardLabelStyle}>{t(`總曝光數 (${getDaysInRange()}天)`, `Total Impressions (${getDaysInRange()}d)`)}</div>
                                    <div style={cardValueStyle}>
                                        {currentImpressions.toLocaleString()}
                                    </div>
                                    {renderCompareInfo(impressionsChange, compareTotals?.impressions || 0)}
                                </div>
                                <div style={cardStyle}>
                                    <div style={cardLabelStyle}>{t('平均點閱率', 'Avg CTR')}</div>
                                    <div style={cardValueStyle}>
                                        {currentCtr.toFixed(2)}%
                                    </div>
                                    {renderCompareInfo(ctrChange, (compareTotals?.ctr || 0) * 100, (v) => `${v.toFixed(2)}%`)}
                                </div>
                                <div style={cardStyle}>
                                    <div style={cardLabelStyle}>{t('平均排名', 'Avg Position')}</div>
                                    <div style={cardValueStyle}>
                                        {currentPosition.toFixed(1)}
                                    </div>
                                    {renderCompareInfo(positionChange, compareTotals?.position || 0, (v) => v.toFixed(1), true)}
                                </div>
                                {/* Indexed Pages Count - only for page tab */}
                                {activeTab === 'page' && (
                                    <div style={{ ...cardStyle, background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(139, 92, 246, 0.05))' }}>
                                        <div style={cardLabelStyle}>📄 {t('索引頁面數', 'Indexed Pages')}</div>
                                        <div style={{ ...cardValueStyle, color: '#8B5CF6' }}>
                                            {analytics.length.toLocaleString()}
                                        </div>
                                    </div>
                                )}
                            </div>
                        );
                    })()}




                    {/* Trend Tab Content */}
                    {activeTab === 'trend' ? (
                        <div style={tableContainerStyle}>
                            {/* Trend Sub-tabs */}
                            <div style={{
                                padding: '12px 16px',
                                borderBottom: '1px solid var(--glass-border)',
                                display: 'flex',
                                gap: '8px',
                                flexWrap: 'wrap',
                                alignItems: 'center',
                                justifyContent: 'space-between'
                            }}>
                                <div style={{ display: 'flex', gap: '4px' }}>
                                    {TREND_SUBTABS.map(subtab => (
                                        <button
                                            key={subtab.key}
                                            onClick={() => setTrendSubTab(subtab.key)}
                                            style={{
                                                padding: '8px 16px',
                                                borderRadius: '6px',
                                                border: 'none',
                                                background: trendSubTab === subtab.key ? 'var(--accent-primary)' : 'var(--bg-primary)',
                                                color: trendSubTab === subtab.key ? 'white' : 'var(--text-secondary)',
                                                fontWeight: trendSubTab === subtab.key ? '600' : '400',
                                                fontSize: '13px',
                                                cursor: 'pointer',
                                                transition: 'all 0.2s'
                                            }}
                                        >
                                            {language === 'zh' ? subtab.label_zh : subtab.label_en}
                                        </button>
                                    ))}
                                </div>
                                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                    <input
                                        type="text"
                                        placeholder={t('搜尋...', 'Search...')}
                                        value={searchKeyword}
                                        onChange={(e) => setSearchKeyword(e.target.value)}
                                        style={searchInputStyle}
                                    />
                                    <select
                                        value={rowLimit}
                                        onChange={(e) => setRowLimit(Number(e.target.value) || 99999)}
                                        style={{ ...selectStyle, width: 'auto', padding: '8px 12px' }}
                                    >
                                        <option value={50}>Top 50</option>
                                        <option value={100}>Top 100</option>
                                        <option value={200}>Top 200</option>
                                        <option value={500}>Top 500</option>
                                        <option value={99999}>{t('全部', 'All')}</option>
                                    </select>
                                </div>
                            </div>

                            {/* Period comparison info */}
                            <div style={{
                                padding: '8px 16px',
                                background: 'var(--bg-primary)',
                                fontSize: '12px',
                                color: 'var(--text-secondary)',
                                borderBottom: '1px solid var(--glass-border)'
                            }}>
                                📊 {t(`比較期間: 本期 ${getDaysInRange()} 天 vs 前期 ${getDaysInRange()} 天`, `Comparing: Current ${getDaysInRange()} days vs Previous ${getDaysInRange()} days`)}
                            </div>

                            {/* Trend Table */}
                            <div style={tableScrollStyle}>
                                <table style={tableStyle}>
                                    <thead>
                                        <tr style={{ background: 'var(--bg-hover)' }}>
                                            <th style={thStyle}>{t('頁面', 'Page')}</th>
                                            <th style={thStyle}>{t('點擊', 'Clicks')}</th>
                                            <th style={thStyle}>{t('變化', 'Change')}</th>
                                            <th style={thStyle}>{t('曝光', 'Impressions')}</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {getSortedTrendData().map((row, idx) => {
                                            const pageUrl = row.keys?.[0] || '';
                                            const isUp = row.clicksChange > 0;
                                            const isDown = row.clicksChange < 0;

                                            return (
                                                <tr
                                                    key={idx}
                                                    style={{
                                                        background: isUp ? 'rgba(16, 185, 129, 0.05)' : isDown ? 'rgba(239, 68, 68, 0.05)' : 'transparent',
                                                        transition: 'background 0.2s'
                                                    }}
                                                    onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-hover)'}
                                                    onMouseLeave={(e) => e.currentTarget.style.background = isUp ? 'rgba(16, 185, 129, 0.05)' : isDown ? 'rgba(239, 68, 68, 0.05)' : 'transparent'}
                                                >
                                                    <td style={{ ...tdStyle, maxWidth: '350px' }}>
                                                        <a
                                                            href={pageUrl}
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                            style={{
                                                                color: 'var(--accent-primary)',
                                                                textDecoration: 'none',
                                                                wordBreak: 'break-word'
                                                            }}
                                                            title={pageUrl}
                                                        >
                                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                                                {/* Page Title */}
                                                                <span style={{
                                                                    fontWeight: '500',
                                                                    color: 'var(--text-primary)',
                                                                    fontSize: '14px'
                                                                }}>
                                                                    {pageTitles[pageUrl] || getTitleFromUrl(pageUrl)}
                                                                </span>
                                                                {/* URL Path */}
                                                                <span style={{
                                                                    fontSize: '12px',
                                                                    color: 'var(--text-secondary)'
                                                                }}>
                                                                    {(() => {
                                                                        try {
                                                                            const path = pageUrl.replace(/^https?:\/\/[^/]+/, '');
                                                                            return decodeURIComponent(path);
                                                                        } catch {
                                                                            return pageUrl.replace(/^https?:\/\/[^/]+/, '');
                                                                        }
                                                                    })()}
                                                                </span>
                                                            </div>
                                                        </a>
                                                    </td>
                                                    <td style={tdStyle}>
                                                        {row.clicks.toLocaleString()}
                                                    </td>
                                                    <td style={{
                                                        ...tdStyle,
                                                        color: isUp ? '#10B981' : isDown ? '#EF4444' : 'var(--text-secondary)',
                                                        fontWeight: '600'
                                                    }}>
                                                        {isUp ? '↑' : isDown ? '↓' : ''} {Math.abs(row.clicksChange).toFixed(0)}%
                                                    </td>
                                                    <td style={tdStyle}>
                                                        {row.impressions.toLocaleString()}
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    ) : activeTab === 'country' ? (
                        /* Country Distribution Tab */
                        <div style={tableContainerStyle}>
                            <div style={tableHeaderStyle}>
                                <span>🌍 {t('地區流量分佈', 'Traffic by Country')} ({analytics.length})</span>
                            </div>
                            <div style={tableScrollStyle}>
                                <table style={tableStyle}>
                                    <thead>
                                        <tr style={{ background: 'var(--bg-hover)' }}>
                                            <th style={thStyle}>{t('國家/地區', 'Country')}</th>
                                            <th style={thStyle} onClick={() => handleSort('clicks')}>
                                                {t('點擊', 'Clicks')}{renderSortIndicator('clicks')}
                                            </th>
                                            <th style={thStyle} onClick={() => handleSort('impressions')}>
                                                {t('曝光', 'Impressions')}{renderSortIndicator('impressions')}
                                            </th>
                                            <th style={thStyle} onClick={() => handleSort('ctr')}>
                                                {t('點閱率', 'CTR')}{renderSortIndicator('ctr')}
                                            </th>
                                            <th style={thStyle}>{t('佔比', 'Share')}</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {(() => {
                                            const totalClicks = analytics.reduce((sum, row) => sum + row.clicks, 0);
                                            const { displayData } = getSortedFilteredData();
                                            return displayData.map((row, idx) => {
                                                const countryCode = (row.keys?.[0] || '').toLowerCase();
                                                const countryName = COUNTRY_NAMES[countryCode]?.[language] || countryCode.toUpperCase();
                                                const sharePercent = totalClicks > 0 ? (row.clicks / totalClicks * 100) : 0;

                                                return (
                                                    <tr
                                                        key={idx}
                                                        style={{ transition: 'background 0.2s' }}
                                                        onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-hover)'}
                                                        onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                                                    >
                                                        <td style={tdStyle}>
                                                            <span style={{ fontSize: '16px', marginRight: '8px' }}>🏳️</span>
                                                            {countryName}
                                                        </td>
                                                        <td style={{ ...tdStyle, fontWeight: '600', color: 'var(--accent-primary)' }}>
                                                            {row.clicks.toLocaleString()}
                                                        </td>
                                                        <td style={tdStyle}>{row.impressions.toLocaleString()}</td>
                                                        <td style={tdStyle}>{(row.ctr * 100).toFixed(2)}%</td>
                                                        <td style={tdStyle}>
                                                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                                <div style={{
                                                                    width: '60px',
                                                                    height: '8px',
                                                                    background: 'var(--bg-hover)',
                                                                    borderRadius: '4px',
                                                                    overflow: 'hidden'
                                                                }}>
                                                                    <div style={{
                                                                        width: `${Math.min(sharePercent, 100)}%`,
                                                                        height: '100%',
                                                                        background: 'var(--accent-primary)',
                                                                        borderRadius: '4px'
                                                                    }} />
                                                                </div>
                                                                <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                                                                    {sharePercent.toFixed(1)}%
                                                                </span>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                );
                                            });
                                        })()}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    ) : activeTab === 'device' ? (
                        /* Device Distribution Tab */
                        <div style={tableContainerStyle}>
                            <div style={tableHeaderStyle}>
                                <span>📱 {t('裝置分佈', 'Traffic by Device')}</span>
                            </div>

                            {/* Device Cards */}
                            <div style={{
                                display: 'grid',
                                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                                gap: '16px',
                                padding: '16px'
                            }}>
                                {(() => {
                                    const totalClicks = analytics.reduce((sum, row) => sum + row.clicks, 0);
                                    return analytics.map((row, idx) => {
                                        const deviceType = row.keys?.[0] || 'UNKNOWN';
                                        const device = DEVICE_NAMES[deviceType] || { zh: deviceType, en: deviceType, color: '#6B7280' };
                                        const sharePercent = totalClicks > 0 ? (row.clicks / totalClicks * 100) : 0;

                                        return (
                                            <div key={idx} style={{
                                                background: 'var(--bg-primary)',
                                                border: '1px solid var(--glass-border)',
                                                borderRadius: '12px',
                                                padding: '20px',
                                                display: 'flex',
                                                flexDirection: 'column',
                                                gap: '12px'
                                            }}>
                                                <div style={{
                                                    display: 'flex',
                                                    justifyContent: 'space-between',
                                                    alignItems: 'center'
                                                }}>
                                                    <span style={{
                                                        fontSize: '18px',
                                                        fontWeight: '600',
                                                        color: device.color
                                                    }}>
                                                        {language === 'zh' ? device.zh : device.en}
                                                    </span>
                                                    <span style={{
                                                        fontSize: '24px',
                                                        fontWeight: '700',
                                                        color: device.color
                                                    }}>
                                                        {sharePercent.toFixed(1)}%
                                                    </span>
                                                </div>

                                                {/* Progress bar */}
                                                <div style={{
                                                    width: '100%',
                                                    height: '8px',
                                                    background: 'var(--bg-hover)',
                                                    borderRadius: '4px',
                                                    overflow: 'hidden'
                                                }}>
                                                    <div style={{
                                                        width: `${sharePercent}%`,
                                                        height: '100%',
                                                        background: device.color,
                                                        borderRadius: '4px',
                                                        transition: 'width 0.5s ease'
                                                    }} />
                                                </div>

                                                <div style={{
                                                    display: 'flex',
                                                    justifyContent: 'space-between',
                                                    fontSize: '13px',
                                                    color: 'var(--text-secondary)'
                                                }}>
                                                    <span>{t('點擊', 'Clicks')}: <strong style={{ color: 'var(--text-primary)' }}>{row.clicks.toLocaleString()}</strong></span>
                                                    <span>{t('曝光', 'Impr.')}: <strong style={{ color: 'var(--text-primary)' }}>{row.impressions.toLocaleString()}</strong></span>
                                                </div>

                                                <div style={{
                                                    fontSize: '12px',
                                                    color: 'var(--text-secondary)'
                                                }}>
                                                    CTR: {(row.ctr * 100).toFixed(2)}% | {t('排名', 'Pos')}: {row.position.toFixed(1)}
                                                </div>
                                            </div>
                                        );
                                    });
                                })()}
                            </div>
                        </div>
                    ) : (
                        /* Regular Table Section */
                        <div style={tableContainerStyle}>
                            <div style={tableHeaderStyle}>
                                <span>
                                    {activeTab === 'daily' && t('每日成效', 'Daily Performance')}
                                    {activeTab === 'query' && t('關鍵字排行', 'Top Keywords')}
                                    {activeTab === 'page' && t('頁面排行', 'Top Pages')}
                                    {activeTab !== 'daily' && ` (${showGroupedView ? groupedData.length + ' 組' : sortedData.length})`}
                                </span>

                                {/* Load time display for page tab */}
                                {activeTab === 'page' && (
                                    <span style={{
                                        display: 'inline-flex',
                                        alignItems: 'center',
                                        gap: '6px',
                                        marginLeft: '12px',
                                        fontSize: '11px',
                                        color: 'var(--text-tertiary)'
                                    }}>
                                        {pageKeywordsLoading ? (
                                            <span style={{ color: '#3B82F6' }}>
                                                ⏳ {t('載入中...', 'Loading...')}
                                            </span>
                                        ) : pageKeywordsLoadTime !== null ? (
                                            <>
                                                <span style={{
                                                    background: 'rgba(16, 185, 129, 0.15)',
                                                    color: '#10B981',
                                                    padding: '2px 8px',
                                                    borderRadius: '10px',
                                                    fontWeight: '500'
                                                }}>
                                                    ⚡ {pageKeywordsLoadTime}ms
                                                </span>
                                                <span>
                                                    {t(`${pageKeywordsTotalCount.toLocaleString()} 組關鍵字`, `${pageKeywordsTotalCount.toLocaleString()} keyword pairs`)}
                                                </span>
                                                {pageKeywordsHasMore && (
                                                    <button
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            loadMorePageKeywords();
                                                        }}
                                                        style={{
                                                            background: 'rgba(59, 130, 246, 0.15)',
                                                            border: '1px solid rgba(59, 130, 246, 0.3)',
                                                            color: '#3B82F6',
                                                            padding: '2px 8px',
                                                            borderRadius: '10px',
                                                            fontSize: '10px',
                                                            fontWeight: '500',
                                                            cursor: 'pointer'
                                                        }}
                                                        title={t('載入更多關鍵字資料', 'Load more keyword data')}
                                                    >
                                                        {t('載入更多', 'Load More')}
                                                    </button>
                                                )}
                                            </>
                                        ) : null}
                                    </span>
                                )}

                                {/* Controls for query/page tabs */}
                                {activeTab !== 'daily' && (
                                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                                        {/* Grouping Toggle (only for query tab) */}
                                        {activeTab === 'query' && (
                                            <button
                                                onClick={() => setGroupingEnabled(!groupingEnabled)}
                                                style={toggleButtonStyle(groupingEnabled)}
                                                title={t('將類似關鍵字歸為一組', 'Group similar keywords')}
                                            >
                                                📦 {t('群組', 'Group')}
                                            </button>
                                        )}

                                        {/* Download CSV button (only for query tab when grouping is enabled) */}
                                        {activeTab === 'query' && groupingEnabled && groupedData && groupedData.length > 0 && (
                                            <button
                                                onClick={() => {
                                                    // Prepare CSV content for grouped keywords
                                                    const headers = [
                                                        t('群組關鍵字', 'Group Keyword'),
                                                        t('群組總點擊', 'Group Total Clicks'),
                                                        t('群組總曝光', 'Group Total Impressions'),
                                                        t('子關鍵字數量', 'Sub-keywords Count'),
                                                        t('子關鍵字列表', 'Sub-keywords List')
                                                    ];
                                                    const csvRows = [headers.join(',')];

                                                    // Escape CSV fields (handle commas and quotes)
                                                    const escapeCSV = (str) => {
                                                        const strVal = String(str);
                                                        if (strVal.includes(',') || strVal.includes('"') || strVal.includes('\n')) {
                                                            return `"${strVal.replace(/"/g, '""')}"`;
                                                        }
                                                        return strVal;
                                                    };

                                                    groupedData.forEach(group => {
                                                        // Collect all sub-keywords (excluding the main keyword)
                                                        const subKeywords = group.items
                                                            .map(item => item.keys?.[0] || '')
                                                            .filter(kw => kw !== group.mainKeyword)
                                                            .join(' | ');

                                                        csvRows.push([
                                                            escapeCSV(group.mainKeyword),
                                                            group.totalClicks,
                                                            group.totalImpressions,
                                                            group.items.length,
                                                            escapeCSV(subKeywords || '-')
                                                        ].join(','));
                                                    });

                                                    // Create and download file
                                                    const csvContent = '\uFEFF' + csvRows.join('\n'); // BOM for Excel UTF-8
                                                    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                                                    const url = URL.createObjectURL(blob);
                                                    const link = document.createElement('a');
                                                    link.href = url;
                                                    link.download = `gsc_keyword_groups_${new Date().toISOString().split('T')[0]}.csv`;
                                                    document.body.appendChild(link);
                                                    link.click();
                                                    document.body.removeChild(link);
                                                    URL.revokeObjectURL(url);
                                                }}
                                                style={toggleButtonStyle(false)}
                                                title={t('下載群組關鍵字為 CSV', 'Download grouped keywords as CSV')}
                                            >
                                                📥 {t('下載 CSV', 'Download CSV')}
                                            </button>
                                        )}

                                        {/* Refresh Titles button (only for page tab) */}
                                        {activeTab === 'page' && (
                                            <button
                                                onClick={async () => {
                                                    setTitlesRefreshing(true);

                                                    // Get URLs based on current rowLimit setting
                                                    const limit = rowLimit === 99999 ? analytics.length : rowLimit;
                                                    const allUrls = analytics.slice(0, limit).map(row => row.keys?.[0]).filter(Boolean);

                                                    // Process in batches of 50 (API limit)
                                                    const batchSize = 50;
                                                    for (let i = 0; i < allUrls.length; i += batchSize) {
                                                        const batch = allUrls.slice(i, i + batchSize);
                                                        console.log(`[Refresh] Processing batch ${Math.floor(i / batchSize) + 1}/${Math.ceil(allUrls.length / batchSize)} (${batch.length} URLs)`);
                                                        await fetchPageTitles(batch, true); // force refresh
                                                    }

                                                    setTitlesRefreshing(false);
                                                }}
                                                disabled={titlesRefreshing}
                                                style={{
                                                    ...toggleButtonStyle(false),
                                                    opacity: titlesRefreshing ? 0.6 : 1,
                                                    cursor: titlesRefreshing ? 'wait' : 'pointer'
                                                }}
                                                title={t('重新抓取頁面標題（依照顯示數量）', 'Refresh page titles (based on display count)')}
                                            >
                                                {titlesRefreshing ? '⏳' : '🔄'} {t('刷新標題', 'Refresh Titles')}
                                            </button>
                                        )}

                                        {/* Download CSV button (only for page tab) */}
                                        {activeTab === 'page' && (
                                            <button
                                                onClick={() => {
                                                    // Get displayed data based on current settings
                                                    const limit = rowLimit === 99999 ? sortedData.length : rowLimit;
                                                    const displayData = sortedData.slice(0, limit);

                                                    // Prepare CSV content
                                                    const headers = ['URL', t('頁面標題', 'Page Title'), t('點擊', 'Clicks'), t('曝光', 'Impressions'), 'CTR', t('排名', 'Position')];
                                                    const csvRows = [headers.join(',')];

                                                    displayData.forEach(row => {
                                                        const pageUrl = row.keys?.[0] || '';
                                                        const title = pageTitles[pageUrl] || getTitleFromUrl(pageUrl);
                                                        const clicks = row.clicks || 0;
                                                        const impressions = row.impressions || 0;
                                                        const ctr = row.ctr ? (row.ctr * 100).toFixed(2) + '%' : '0%';
                                                        const position = row.position ? row.position.toFixed(1) : '-';

                                                        // Escape CSV fields (handle commas and quotes in title/URL)
                                                        const escapeCSV = (str) => {
                                                            if (str.includes(',') || str.includes('"') || str.includes('\n')) {
                                                                return `"${str.replace(/"/g, '""')}"`;
                                                            }
                                                            return str;
                                                        };

                                                        csvRows.push([
                                                            escapeCSV(pageUrl),
                                                            escapeCSV(title),
                                                            clicks,
                                                            impressions,
                                                            ctr,
                                                            position
                                                        ].join(','));
                                                    });

                                                    // Create and download file
                                                    const csvContent = '\uFEFF' + csvRows.join('\n'); // BOM for Excel UTF-8
                                                    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                                                    const url = URL.createObjectURL(blob);
                                                    const link = document.createElement('a');
                                                    link.href = url;
                                                    link.download = `gsc_page_analysis_${new Date().toISOString().split('T')[0]}.csv`;
                                                    document.body.appendChild(link);
                                                    link.click();
                                                    document.body.removeChild(link);
                                                    URL.revokeObjectURL(url);
                                                }}
                                                style={toggleButtonStyle(false)}
                                                title={t('下載頁面分析資料為 CSV', 'Download page analysis data as CSV')}
                                            >
                                                📥 {t('下載 CSV', 'Download CSV')}
                                            </button>
                                        )}

                                        <input
                                            type="text"
                                            placeholder={t('搜尋...', 'Search...')}
                                            value={searchKeyword}
                                            onChange={(e) => setSearchKeyword(e.target.value)}
                                            style={searchInputStyle}
                                        />
                                        <select
                                            value={rowLimit}
                                            onChange={(e) => setRowLimit(Number(e.target.value) || 99999)}
                                            style={{ ...selectStyle, width: 'auto', padding: '8px 12px' }}
                                        >
                                            <option value={50}>Top 50</option>
                                            <option value={100}>Top 100</option>
                                            <option value={200}>Top 200</option>
                                            <option value={500}>Top 500</option>
                                            <option value={99999}>{t('全部', 'All')}</option>
                                        </select>
                                    </div>
                                )}
                            </div>

                            {/* Grouping Notice */}
                            {showGroupedView && (
                                <div style={{
                                    padding: '12px 16px',
                                    background: 'rgba(66, 133, 244, 0.1)',
                                    borderBottom: '1px solid var(--glass-border)',
                                    color: 'var(--accent-primary)',
                                    fontSize: '13px',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '8px'
                                }}>
                                    💡 {t('系統已將類似的關鍵字歸為一組，點擊展開查看詳細。', 'Similar keywords are grouped together. Click to expand.')}
                                </div>
                            )}

                            <div style={tableScrollStyle}>
                                <table style={tableStyle}>
                                    <thead>
                                        <tr style={{ background: 'var(--bg-hover)' }}>
                                            <th style={thStyle} onClick={() => activeTab === 'daily' && handleSort('date')}>
                                                {activeTab === 'daily' && <>{t('日期', 'Date')}{renderSortIndicator('date')}</>}
                                                {activeTab === 'query' && t('關鍵字', 'Keyword')}
                                                {activeTab === 'page' && t('頁面', 'Page')}
                                            </th>
                                            <th style={thStyle} onClick={() => handleSort('clicks')}>
                                                {t('點擊', 'Clicks')}{renderSortIndicator('clicks')}
                                            </th>
                                            <th style={thStyle} onClick={() => handleSort('impressions')}>
                                                {t('曝光', 'Impressions')}{renderSortIndicator('impressions')}
                                            </th>
                                            <th style={thStyle} onClick={() => handleSort('ctr')}>
                                                {t('點閱率', 'CTR')}{renderSortIndicator('ctr')}
                                            </th>
                                            <th style={thStyle} onClick={() => handleSort('position')}>
                                                {t('排名', 'Position')}{renderSortIndicator('position')}
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {showGroupedView ? (
                                            // Grouped View
                                            groupedData.map((group, gIdx) => (
                                                <React.Fragment key={gIdx}>
                                                    {/* Group Header Row */}
                                                    <tr
                                                        style={groupRowStyle}
                                                        onClick={() => toggleGroup(gIdx)}
                                                        onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-hover)'}
                                                        onMouseLeave={(e) => e.currentTarget.style.background = 'var(--bg-hover)'}
                                                    >
                                                        <td style={{ ...tdStyle, display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                            <span style={{
                                                                display: 'inline-block',
                                                                width: '20px',
                                                                textAlign: 'center',
                                                                transition: 'transform 0.2s',
                                                                transform: expandedGroups.has(gIdx) ? 'rotate(90deg)' : 'rotate(0deg)'
                                                            }}>
                                                                ▶
                                                            </span>
                                                            <span>{group.mainKeyword}</span>
                                                            {group.items.length > 1 && (
                                                                <span style={{
                                                                    background: 'var(--accent-primary)',
                                                                    color: 'white',
                                                                    padding: '2px 8px',
                                                                    borderRadius: '12px',
                                                                    fontSize: '11px',
                                                                    fontWeight: '500'
                                                                }}>
                                                                    +{group.items.length - 1}
                                                                </span>
                                                            )}
                                                        </td>
                                                        <td style={tdStyle}>{group.totalClicks.toLocaleString()}</td>
                                                        <td style={tdStyle}>{group.totalImpressions.toLocaleString()}</td>
                                                        <td style={tdStyle}>-</td>
                                                        <td style={tdStyle}>-</td>
                                                    </tr>

                                                    {/* Child Rows (when expanded) */}
                                                    {expandedGroups.has(gIdx) && group.items.map((row, rIdx) => (
                                                        <tr
                                                            key={`${gIdx}-${rIdx}`}
                                                            style={childRowStyle}
                                                            onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-hover)'}
                                                            onMouseLeave={(e) => e.currentTarget.style.background = 'var(--bg-primary)'}
                                                        >
                                                            <td style={{ ...tdStyle, paddingLeft: '48px', color: 'var(--text-secondary)' }}>
                                                                ↳ {row.keys && row.keys[0]}
                                                            </td>
                                                            <td style={tdStyle}>{row.clicks.toLocaleString()}</td>
                                                            <td style={tdStyle}>{row.impressions.toLocaleString()}</td>
                                                            <td style={tdStyle}>{(row.ctr * 100).toFixed(2)}%</td>
                                                            <td style={tdStyle}>{row.position.toFixed(1)}</td>
                                                        </tr>
                                                    ))}
                                                </React.Fragment>
                                            ))
                                        ) : (
                                            // Regular View
                                            sortedData.map((row, idx) => {
                                                const pageUrl = row.keys && row.keys[0];
                                                const indicator = activeTab === 'page' ? getPerformanceIndicator(idx, sortedData.length) : null;
                                                const keywords = activeTab === 'page' && pageUrl ? pageKeywords[pageUrl] : null;
                                                const hasKeywords = keywords && keywords.length > 0;
                                                const isExpanded = expandedPages.has(pageUrl);

                                                return (
                                                    <React.Fragment key={idx}>
                                                        <tr
                                                            style={{
                                                                transition: 'background 0.2s',
                                                                background: indicator ? `${indicator.color}10` : 'transparent',
                                                                cursor: hasKeywords ? 'pointer' : 'default'
                                                            }}
                                                            onClick={() => hasKeywords && togglePageExpand(pageUrl)}
                                                            onMouseEnter={(e) => e.currentTarget.style.background = indicator ? `${indicator.color}20` : 'var(--bg-hover)'}
                                                            onMouseLeave={(e) => e.currentTarget.style.background = indicator ? `${indicator.color}10` : 'transparent'}
                                                        >
                                                            <td style={{
                                                                ...tdStyle,
                                                                maxWidth: activeTab === 'page' ? '400px' : 'auto',
                                                                overflow: 'visible',
                                                                whiteSpace: 'normal'
                                                            }}>
                                                                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', flexWrap: 'wrap' }}>
                                                                    {/* Performance indicator */}
                                                                    {indicator && (
                                                                        <span style={{
                                                                            fontSize: '14px',
                                                                            flexShrink: 0
                                                                        }}>
                                                                            {indicator.label}
                                                                        </span>
                                                                    )}

                                                                    {/* Expand arrow for pages with keywords */}
                                                                    {hasKeywords && (
                                                                        <span style={{
                                                                            display: 'inline-block',
                                                                            width: '16px',
                                                                            textAlign: 'center',
                                                                            transition: 'transform 0.2s',
                                                                            transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)',
                                                                            color: 'var(--text-secondary)',
                                                                            fontSize: '12px',
                                                                            flexShrink: 0
                                                                        }}>
                                                                            ▶
                                                                        </span>
                                                                    )}

                                                                    <div style={{ flex: 1, minWidth: 0 }}>
                                                                        {activeTab === 'page' && pageUrl ? (
                                                                            <a
                                                                                href={pageUrl}
                                                                                target="_blank"
                                                                                rel="noopener noreferrer"
                                                                                style={{
                                                                                    color: indicator ? indicator.color : 'var(--accent-primary)',
                                                                                    textDecoration: 'none',
                                                                                    fontWeight: indicator ? '600' : '400',
                                                                                    wordBreak: 'break-word'
                                                                                }}
                                                                                title={pageUrl}
                                                                                onClick={(e) => e.stopPropagation()}
                                                                            >
                                                                                <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                                                                    {/* Page Title */}
                                                                                    <span style={{
                                                                                        fontWeight: '500',
                                                                                        color: indicator ? indicator.color : 'var(--text-primary)',
                                                                                        fontSize: '14px'
                                                                                    }}>
                                                                                        {pageTitles[pageUrl] || getTitleFromUrl(pageUrl)}
                                                                                    </span>
                                                                                    {/* URL Path */}
                                                                                    <span style={{
                                                                                        fontSize: '12px',
                                                                                        color: 'var(--text-secondary)',
                                                                                        fontWeight: '400'
                                                                                    }}>
                                                                                        {(() => {
                                                                                            try {
                                                                                                const path = pageUrl.replace(/^https?:\/\/[^/]+/, '');
                                                                                                return decodeURIComponent(path);
                                                                                            } catch {
                                                                                                return pageUrl.replace(/^https?:\/\/[^/]+/, '');
                                                                                            }
                                                                                        })()}
                                                                                    </span>
                                                                                </div>
                                                                            </a>
                                                                        ) : (
                                                                            row.keys && row.keys[0]
                                                                        )}

                                                                        {/* Search Intent Badge (AI-powered) */}
                                                                        {activeTab === 'page' && pageUrl && (
                                                                            <div style={{
                                                                                marginTop: '8px',
                                                                                display: 'flex',
                                                                                alignItems: 'center',
                                                                                gap: '8px',
                                                                                flexWrap: 'wrap'
                                                                            }}>
                                                                                {(() => {
                                                                                    // Dynamically calculate page intent based on current keywords
                                                                                    const pageIntent = getPageIntent(pageUrl);
                                                                                    const allKeywords = pageKeywords[pageUrl] || [];
                                                                                    const analyzedCount = allKeywords.filter(kw => {
                                                                                        const query = kw.keyword || kw.query;
                                                                                        return keywordIntents[query];
                                                                                    }).length;
                                                                                    const uncachedCount = allKeywords.length - analyzedCount;

                                                                                    if (pageIntent) {
                                                                                        // Show dynamically calculated intent result
                                                                                        return (
                                                                                            <>
                                                                                                <span
                                                                                                    style={{
                                                                                                        display: 'inline-flex',
                                                                                                        alignItems: 'center',
                                                                                                        gap: '4px',
                                                                                                        background: `${INTENT_TYPES[pageIntent.primary_intent]?.color}20`,
                                                                                                        color: INTENT_TYPES[pageIntent.primary_intent]?.color,
                                                                                                        padding: '3px 10px',
                                                                                                        borderRadius: '12px',
                                                                                                        fontSize: '11px',
                                                                                                        fontWeight: '600'
                                                                                                    }}
                                                                                                    title={t('AI 分析的主要搜尋意圖', 'AI-analyzed primary search intent')}
                                                                                                >
                                                                                                    {INTENT_TYPES[pageIntent.primary_intent]?.emoji}
                                                                                                    {language === 'zh'
                                                                                                        ? INTENT_TYPES[pageIntent.primary_intent]?.label_zh
                                                                                                        : INTENT_TYPES[pageIntent.primary_intent]?.label_en}
                                                                                                </span>
                                                                                                {/* Horizontal distribution bar with labels */}
                                                                                                <div style={{
                                                                                                    display: 'flex',
                                                                                                    alignItems: 'center',
                                                                                                    gap: '4px',
                                                                                                    width: '160px',
                                                                                                    height: '18px',
                                                                                                    background: 'rgba(0,0,0,0.2)',
                                                                                                    borderRadius: '4px',
                                                                                                    overflow: 'hidden'
                                                                                                }}>
                                                                                                    {Object.entries(pageIntent.intent_distribution || {})
                                                                                                        .filter(([_, value]) => value > 0.05)
                                                                                                        .sort((a, b) => b[1] - a[1])
                                                                                                        .map(([intent, value]) => (
                                                                                                            <div
                                                                                                                key={intent}
                                                                                                                style={{
                                                                                                                    display: 'flex',
                                                                                                                    alignItems: 'center',
                                                                                                                    justifyContent: 'center',
                                                                                                                    width: `${value * 100}%`,
                                                                                                                    height: '100%',
                                                                                                                    background: INTENT_TYPES[intent]?.color || '#666',
                                                                                                                    fontSize: '9px',
                                                                                                                    fontWeight: '500',
                                                                                                                    color: 'white',
                                                                                                                    whiteSpace: 'nowrap',
                                                                                                                    overflow: 'hidden',
                                                                                                                    textShadow: '0 1px 2px rgba(0,0,0,0.5)'
                                                                                                                }}
                                                                                                                title={`${language === 'zh' ? INTENT_TYPES[intent]?.label_zh : INTENT_TYPES[intent]?.label_en}: ${(value * 100).toFixed(0)}%`}
                                                                                                            >
                                                                                                                {value >= 0.15 && `${(value * 100).toFixed(0)}%`}
                                                                                                            </div>
                                                                                                        ))}
                                                                                                </div>
                                                                                                {/* Show analyzed count and continue button if needed */}
                                                                                                <span style={{ fontSize: '10px', color: 'var(--text-tertiary)' }}>
                                                                                                    ({analyzedCount}/{allKeywords.length})
                                                                                                </span>
                                                                                                {/* Show loading indicator during continue analysis */}
                                                                                                {intentLoading[pageUrl] && (
                                                                                                    <span style={{
                                                                                                        fontSize: '10px',
                                                                                                        color: '#3B82F6',
                                                                                                        display: 'inline-flex',
                                                                                                        alignItems: 'center',
                                                                                                        gap: '4px',
                                                                                                        animation: 'pulse 1.5s ease-in-out infinite'
                                                                                                    }}>
                                                                                                        ⏳ {t('分析中', 'Analyzing')}...
                                                                                                    </span>
                                                                                                )}
                                                                                                {/* Continue analysis button if there are uncached keywords */}
                                                                                                {uncachedCount > 0 && !intentLoading[pageUrl] && (
                                                                                                    <button
                                                                                                        onClick={(e) => {
                                                                                                            e.stopPropagation();
                                                                                                            // Check if using Gemini provider
                                                                                                            const provider = localStorage.getItem('ai_provider') || 'zeabur';
                                                                                                            const isGemini = provider === 'gemini';
                                                                                                            const batchCount = Math.ceil(uncachedCount / 10);
                                                                                                            const estimatedTime = isGemini && batchCount > 1 ? Math.round(batchCount * 6) : 0;

                                                                                                            // Show confirmation dialog for continue analysis (API cost warning)
                                                                                                            let message = language === 'zh'
                                                                                                                ? `⚠️ 繼續分析將分析剩餘 ${Math.min(uncachedCount, 100)} 個關鍵字\n\n這會消耗 AI API 額度，確定要繼續嗎？`
                                                                                                                : `⚠️ Continue analysis will analyze ${Math.min(uncachedCount, 100)} more keywords\n\nThis will consume AI API credits. Continue?`;

                                                                                                            // Add Gemini rate limit warning
                                                                                                            if (isGemini && batchCount > 1) {
                                                                                                                message += language === 'zh'
                                                                                                                    ? `\n\n💎 您正在使用 Google Gemini，因免費版有請求限制，\n分析將分 ${batchCount} 批次進行，預計需要 ${estimatedTime} 秒。`
                                                                                                                    : `\n\n💎 You're using Google Gemini. Due to free tier rate limits,\nanalysis will be processed in ${batchCount} batches (~${estimatedTime}s).`;
                                                                                                            }

                                                                                                            if (window.confirm(message)) {
                                                                                                                fetchPageIntent(pageUrl, true); // analyzeAll = true
                                                                                                            }
                                                                                                        }}
                                                                                                        style={{
                                                                                                            display: 'inline-flex',
                                                                                                            alignItems: 'center',
                                                                                                            gap: '4px',
                                                                                                            background: 'rgba(59, 130, 246, 0.15)',
                                                                                                            border: '1px solid rgba(59, 130, 246, 0.4)',
                                                                                                            color: '#3B82F6',
                                                                                                            padding: '3px 10px',
                                                                                                            borderRadius: '12px',
                                                                                                            fontSize: '10px',
                                                                                                            fontWeight: '500',
                                                                                                            cursor: 'pointer',
                                                                                                            transition: 'all 0.2s'
                                                                                                        }}
                                                                                                        onMouseEnter={(e) => {
                                                                                                            e.currentTarget.style.background = 'rgba(59, 130, 246, 0.25)';
                                                                                                        }}
                                                                                                        onMouseLeave={(e) => {
                                                                                                            e.currentTarget.style.background = 'rgba(59, 130, 246, 0.15)';
                                                                                                        }}
                                                                                                        title={t(`還有 ${uncachedCount} 個關鍵字待分析`, `${uncachedCount} more keywords to analyze`)}
                                                                                                    >
                                                                                                        🔄 {t('繼續分析', 'Continue')} +{uncachedCount}
                                                                                                    </button>
                                                                                                )}
                                                                                            </>
                                                                                        );
                                                                                    } else if (intentLoading[pageUrl]) {
                                                                                        // Loading state
                                                                                        return (
                                                                                            <span style={{
                                                                                                fontSize: '11px',
                                                                                                color: 'var(--text-secondary)',
                                                                                                display: 'flex',
                                                                                                alignItems: 'center',
                                                                                                gap: '4px'
                                                                                            }}>
                                                                                                <span style={{ animation: 'spin 1s linear infinite' }}>🔄</span>
                                                                                                {t('分析中...', 'Analyzing...')}
                                                                                            </span>
                                                                                        );
                                                                                    } else if (intentError[pageUrl]) {
                                                                                        // Error state
                                                                                        return (
                                                                                            <span style={{
                                                                                                fontSize: '11px',
                                                                                                color: '#EF4444',
                                                                                                display: 'flex',
                                                                                                alignItems: 'center',
                                                                                                gap: '4px'
                                                                                            }}>
                                                                                                ⚠️ {t('分析失敗', 'Analysis failed')}
                                                                                            </span>
                                                                                        );
                                                                                    } else {
                                                                                        // Analyze button with keyword count
                                                                                        const allKeywords = pageKeywords[pageUrl] || [];
                                                                                        const analyzedCount = allKeywords.filter(kw => {
                                                                                            const query = kw.keyword || kw.query;
                                                                                            return keywordIntents[query];
                                                                                        }).length;
                                                                                        const uncachedCount = allKeywords.length - analyzedCount;

                                                                                        return (
                                                                                            <button
                                                                                                onClick={(e) => {
                                                                                                    e.stopPropagation();
                                                                                                    fetchPageIntent(pageUrl);
                                                                                                }}
                                                                                                style={{
                                                                                                    display: 'inline-flex',
                                                                                                    alignItems: 'center',
                                                                                                    gap: '4px',
                                                                                                    background: 'transparent',
                                                                                                    border: '1px dashed var(--glass-border)',
                                                                                                    color: 'var(--text-secondary)',
                                                                                                    padding: '3px 10px',
                                                                                                    borderRadius: '12px',
                                                                                                    fontSize: '11px',
                                                                                                    cursor: 'pointer',
                                                                                                    transition: 'all 0.2s'
                                                                                                }}
                                                                                                onMouseEnter={(e) => {
                                                                                                    e.currentTarget.style.borderColor = 'var(--accent-primary)';
                                                                                                    e.currentTarget.style.color = 'var(--accent-primary)';
                                                                                                }}
                                                                                                onMouseLeave={(e) => {
                                                                                                    e.currentTarget.style.borderColor = 'var(--glass-border)';
                                                                                                    e.currentTarget.style.color = 'var(--text-secondary)';
                                                                                                }}
                                                                                                title={t(`共 ${allKeywords.length} 個關鍵字，${uncachedCount} 個待分析`, `${allKeywords.length} keywords, ${uncachedCount} to analyze`)}
                                                                                            >
                                                                                                🤖 {t('分析意圖', 'Analyze Intent')}
                                                                                                <span style={{ opacity: 0.7 }}>
                                                                                                    ({allKeywords.length})
                                                                                                </span>
                                                                                            </button>
                                                                                        );
                                                                                    }
                                                                                })()}
                                                                            </div>
                                                                        )}

                                                                        {/* Keyword tags (collapsed preview) */}
                                                                        {hasKeywords && !isExpanded && (
                                                                            <div style={{
                                                                                marginTop: '6px',
                                                                                display: 'flex',
                                                                                flexWrap: 'wrap',
                                                                                gap: '4px'
                                                                            }}>
                                                                                {keywords.slice(0, 3).map((kw, kIdx) => (
                                                                                    <span key={kIdx} style={{
                                                                                        background: 'var(--bg-hover)',
                                                                                        padding: '2px 8px',
                                                                                        borderRadius: '12px',
                                                                                        fontSize: '11px',
                                                                                        color: 'var(--text-secondary)'
                                                                                    }}>
                                                                                        {kw.keyword}
                                                                                    </span>
                                                                                ))}
                                                                                {keywords.length > 3 && (
                                                                                    <span style={{
                                                                                        padding: '2px 8px',
                                                                                        fontSize: '11px',
                                                                                        color: 'var(--text-secondary)'
                                                                                    }}>
                                                                                        +{keywords.length - 3}
                                                                                    </span>
                                                                                )}
                                                                            </div>
                                                                        )}
                                                                    </div>
                                                                </div>
                                                            </td>
                                                            <td style={{ ...tdStyle, color: indicator?.color || 'inherit', fontWeight: indicator ? '600' : '400' }}>
                                                                {row.clicks.toLocaleString()}
                                                            </td>
                                                            <td style={tdStyle}>{row.impressions.toLocaleString()}</td>
                                                            <td style={tdStyle}>{(row.ctr * 100).toFixed(2)}%</td>
                                                            <td style={tdStyle}>{row.position.toFixed(1)}</td>
                                                        </tr>

                                                        {/* Expanded keywords list */}
                                                        {isExpanded && keywords && (
                                                            <tr style={{ background: 'var(--bg-primary)' }}>
                                                                <td colSpan={5} style={{ padding: '0 24px 16px 48px' }}>
                                                                    <div style={{
                                                                        background: 'var(--bg-secondary)',
                                                                        borderRadius: '8px',
                                                                        padding: '12px',
                                                                        border: '1px solid var(--glass-border)'
                                                                    }}>
                                                                        <div style={{
                                                                            fontSize: '12px',
                                                                            color: 'var(--text-secondary)',
                                                                            marginBottom: '8px',
                                                                            fontWeight: '500',
                                                                            display: 'flex',
                                                                            justifyContent: 'space-between',
                                                                            alignItems: 'center'
                                                                        }}>
                                                                            <span>🔍 {t('核心關鍵字', 'Core Keywords')}</span>
                                                                            {(() => {
                                                                                // Count how many keywords have been analyzed
                                                                                const analyzedCount = keywords.filter(kw => {
                                                                                    const query = kw.keyword || kw.query;
                                                                                    return keywordIntents[query];
                                                                                }).length;
                                                                                if (analyzedCount > 0) {
                                                                                    return (
                                                                                        <span style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>
                                                                                            ✨ AI {t('意圖分析', 'Intent Analysis')} ({analyzedCount}/{keywords.length})
                                                                                        </span>
                                                                                    );
                                                                                }
                                                                                return null;
                                                                            })()}
                                                                        </div>
                                                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                                                                            {/* Show keywords with dynamic limit (default 5, increases with load more) */}
                                                                            {keywords.slice(0, expandedKeywordsCount[pageUrl] || 5).map((kw, kIdx) => {
                                                                                const query = kw.keyword || kw.query;
                                                                                // Lookup intent from keyword-level cache
                                                                                const cachedIntent = keywordIntents[query];
                                                                                const intent = cachedIntent?.intent || null;
                                                                                const intentType = INTENT_TYPES[intent];
                                                                                const clicks = kw.clicks || 0;
                                                                                const impressions = kw.impressions || 0;

                                                                                return (
                                                                                    <div key={kIdx} style={{
                                                                                        display: 'flex',
                                                                                        justifyContent: 'space-between',
                                                                                        alignItems: 'center',
                                                                                        padding: '6px 10px',
                                                                                        background: 'var(--bg-primary)',
                                                                                        borderRadius: '6px',
                                                                                        fontSize: '13px',
                                                                                        gap: '8px'
                                                                                    }}>
                                                                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1, minWidth: 0 }}>
                                                                                            <span style={{ color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                                                                                {query}
                                                                                            </span>
                                                                                            {/* Intent badge for each keyword */}
                                                                                            {intentType && (
                                                                                                <span style={{
                                                                                                    display: 'inline-flex',
                                                                                                    alignItems: 'center',
                                                                                                    gap: '2px',
                                                                                                    background: `${intentType.color}15`,
                                                                                                    color: intentType.color,
                                                                                                    padding: '2px 6px',
                                                                                                    borderRadius: '8px',
                                                                                                    fontSize: '10px',
                                                                                                    fontWeight: '500',
                                                                                                    flexShrink: 0
                                                                                                }}>
                                                                                                    {intentType.emoji}
                                                                                                    {language === 'zh' ? intentType.label_zh : intentType.label_en}
                                                                                                </span>
                                                                                            )}
                                                                                        </div>
                                                                                        <div style={{ display: 'flex', gap: '12px', flexShrink: 0 }}>
                                                                                            <span style={{
                                                                                                color: 'var(--accent-primary)',
                                                                                                fontWeight: '500',
                                                                                                fontSize: '12px'
                                                                                            }}>
                                                                                                {clicks.toLocaleString()} {t('點擊', 'clicks')}
                                                                                            </span>
                                                                                            <span style={{
                                                                                                color: 'var(--text-secondary)',
                                                                                                fontSize: '12px'
                                                                                            }}>
                                                                                                {impressions.toLocaleString()} {t('曝光', 'impr.')}
                                                                                            </span>
                                                                                        </div>
                                                                                    </div>
                                                                                );
                                                                            })}
                                                                            {/* Show "Load More" button if there are more keywords (dynamic) */}
                                                                            {(() => {
                                                                                const currentLimit = expandedKeywordsCount[pageUrl] || 5;
                                                                                const remaining = keywords.length - currentLimit;

                                                                                if (remaining > 0) {
                                                                                    return (
                                                                                        <button
                                                                                            onClick={(e) => {
                                                                                                e.stopPropagation();
                                                                                                // Load more keywords (increase by 10)
                                                                                                setExpandedKeywordsCount(prev => ({
                                                                                                    ...prev,
                                                                                                    [pageUrl]: currentLimit + 10
                                                                                                }));
                                                                                            }}
                                                                                            style={{
                                                                                                display: 'flex',
                                                                                                justifyContent: 'center',
                                                                                                alignItems: 'center',
                                                                                                gap: '4px',
                                                                                                padding: '6px 12px',
                                                                                                margin: '4px 0',
                                                                                                background: 'rgba(59, 130, 246, 0.1)',
                                                                                                border: '1px solid rgba(59, 130, 246, 0.3)',
                                                                                                borderRadius: '6px',
                                                                                                color: '#3B82F6',
                                                                                                fontSize: '11px',
                                                                                                fontWeight: '500',
                                                                                                cursor: 'pointer',
                                                                                                transition: 'all 0.2s'
                                                                                            }}
                                                                                        >
                                                                                            ⬇️ {t('載入更多', 'Load More')} (+{Math.min(remaining, 10)})
                                                                                        </button>
                                                                                    );
                                                                                }
                                                                                return null;
                                                                            })()}
                                                                        </div>
                                                                    </div>
                                                                </td>
                                                            </tr>
                                                        )}
                                                    </React.Fragment>
                                                );
                                            })
                                        )}
                                    </tbody>
                                </table>
                            </div>

                            {/* Load More from server (query tab, full dataset) */}
                            {activeTab === 'query' && rowLimit === 99999 && queryHasMore && (
                                <div style={{
                                    padding: '16px',
                                    borderTop: '1px solid var(--glass-border)',
                                    display: 'flex',
                                    justifyContent: 'center',
                                    alignItems: 'center',
                                    gap: '12px'
                                }}>
                                    <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
                                        {t(`已載入 ${analytics.length} 筆`, `Loaded ${analytics.length} rows`)}
                                    </span>
                                    <button
                                        onClick={loadMoreQueryData}
                                        disabled={queryLoadingMore}
                                        style={{
                                            padding: '8px 20px',
                                            background: 'var(--accent-primary)',
                                            border: 'none',
                                            borderRadius: '8px',
                                            color: 'white',
                                            fontSize: '13px',
                                            fontWeight: '500',
                                            cursor: queryLoadingMore ? 'wait' : 'pointer',
                                            opacity: queryLoadingMore ? 0.7 : 1,
                                            transition: 'all 0.2s'
                                        }}
                                    >
                                        {queryLoadingMore
                                            ? t('載入中...', 'Loading...')
                                            : `⬇️ ${t('載入更多資料', 'Load More Data')}`}
                                    </button>
                                </div>
                            )}

                            {/* Load More Button for progressive rendering */}
                            {!showGroupedView && sortedDataHasMore && (
                                <div style={{
                                    padding: '16px',
                                    borderTop: '1px solid var(--glass-border)',
                                    display: 'flex',
                                    justifyContent: 'center',
                                    alignItems: 'center',
                                    gap: '12px'
                                }}>
                                    <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
                                        {t(`顯示 ${sortedData.length} / ${sortedDataTotal} 筆`, `Showing ${sortedData.length} of ${sortedDataTotal}`)}
                                    </span>
                                    <button
                                        onClick={() => setDisplayLimit(prev => prev + 100)}
                                        style={{
                                            padding: '8px 20px',
                                            background: 'var(--accent-primary)',
                                            border: 'none',
                                            borderRadius: '8px',
                                            color: 'white',
                                            fontSize: '13px',
                                            fontWeight: '500',
                                            cursor: 'pointer',
                                            transition: 'all 0.2s'
                                        }}
                                    >
                                        ⬇️ {t('載入更多', 'Load More')} (+{Math.min(100, sortedDataTotal - sortedData.length)})
                                    </button>
                                    <button
                                        onClick={() => setDisplayLimit(sortedDataTotal)}
                                        style={{
                                            padding: '8px 16px',
                                            background: 'transparent',
                                            border: '1px solid var(--glass-border)',
                                            borderRadius: '8px',
                                            color: 'var(--text-secondary)',
                                            fontSize: '13px',
                                            cursor: 'pointer',
                                            transition: 'all 0.2s'
                                        }}
                                        title={sortedDataTotal > 1000
                                            ? t('大量資料可能導致瀏覽器變慢', 'Large data may slow down the browser')
                                            : ''}
                                    >
                                        {t('載入全部', 'Load All')}
                                        {sortedDataTotal > 1000 && ' ⚠️'}
                                    </button>
                                    {/* Warning for large datasets */}
                                    {sortedDataTotal > 5000 && (
                                        <span style={{
                                            fontSize: '11px',
                                            color: '#F59E0B',
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '4px'
                                        }}>
                                            ⚠️ {t('大量資料載入可能較慢', 'Large dataset may be slow')}
                                        </span>
                                    )}
                                </div>
                            )}
                        </div>
                    )}
                </>
            )}
        </div>
    );
};

export default GSCStats;

