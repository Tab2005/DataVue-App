
import React, { useEffect, useState, useMemo } from 'react';

// Date Range Presets Configuration
const DATE_PRESETS = [
    { key: 'last_7d', label_zh: '過去 7 天', label_en: 'Last 7 Days', days: 7 },
    { key: 'last_28d', label_zh: '過去 28 天', label_en: 'Last 28 Days', days: 28 },
    { key: 'last_3m', label_zh: '過去 3 個月', label_en: 'Last 3 Months', days: 90 },
    { key: 'custom', label_zh: '自訂', label_en: 'Custom', days: null }
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

// Helper function to format date to YYYY-MM-DD
const formatDate = (date) => {
    return date.toISOString().split('T')[0];
};

// Helper function to calculate date range from preset
const getDateRangeFromPreset = (presetKey) => {
    const today = new Date();
    const preset = DATE_PRESETS.find(p => p.key === presetKey);

    if (!preset || preset.days === null) {
        const start = new Date();
        start.setDate(today.getDate() - 30);
        return { start: formatDate(start), end: formatDate(today) };
    }

    if (preset.key === 'today') {
        return { start: formatDate(today), end: formatDate(today) };
    }

    if (preset.key === 'yesterday') {
        const yesterday = new Date();
        yesterday.setDate(today.getDate() - 1);
        return { start: formatDate(yesterday), end: formatDate(yesterday) };
    }

    // For "last X days" presets (complete days, not including today)
    // e.g., "Last 7 days" = 7 complete days before today = (today-7) to (today-1)
    const end = new Date();
    end.setDate(today.getDate() - 1);  // Yesterday
    const start = new Date();
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

    // Tab State
    const [activeTab, setActiveTab] = useState('daily');

    // Date Range State
    const [datePreset, setDatePreset] = useState('last_28d');
    const [dateRange, setDateRange] = useState(getDateRangeFromPreset('last_28d'));
    const [showCustomDate, setShowCustomDate] = useState(false);

    // Keyword/Page specific state
    const [searchKeyword, setSearchKeyword] = useState('');
    const [sortConfig, setSortConfig] = useState({ key: 'clicks', direction: 'desc' });
    const [rowLimit, setRowLimit] = useState(50);

    // Grouping state (for keyword tab)
    const [groupingEnabled, setGroupingEnabled] = useState(false);
    const [expandedGroups, setExpandedGroups] = useState(new Set());

    // Page keywords state (for page tab - shows keywords per page)
    const [pageKeywords, setPageKeywords] = useState({});
    const [expandedPages, setExpandedPages] = useState(new Set());

    // Trend tab state
    const [trendSubTab, setTrendSubTab] = useState('top');
    const [trendData, setTrendData] = useState([]);
    const [trendLoading, setTrendLoading] = useState(false);

    // Page titles cache (for page tab and trend tab)
    const [pageTitles, setPageTitles] = useState({});

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

    useEffect(() => {
        if (selectedSite && dateRange.start && dateRange.end) {
            const currentTab = TABS.find(tab => tab.key === activeTab);
            const dimension = currentTab ? currentTab.dimension : 'date';

            if (activeTab === 'trend') {
                // For trend tab, fetch both current and previous period
                fetchTrendData(selectedSite, dateRange.start, dateRange.end);
            } else {
                fetchAnalytics(selectedSite, dateRange.start, dateRange.end, dimension);

                // Fetch page+query data for page tab (to show keywords per page)
                if (activeTab === 'page') {
                    fetchPageKeywords(selectedSite, dateRange.start, dateRange.end);
                }
            }
        }
    }, [selectedSite, dateRange, activeTab]);

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

    const fetchAnalytics = async (siteUrl, startDate, endDate, dimension = 'date') => {
        setAnalyticsLoading(true);
        try {
            const resp = await fetch(`${API_URL}/api/gsc/analytics?site_url=${encodeURIComponent(siteUrl)}&start_date=${startDate}&end_date=${endDate}&dimensions=${dimension}`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('google_token')}` }
            });
            const data = await resp.json();
            if (!resp.ok) throw new Error(data.detail);
            setAnalytics(data);
        } catch (err) {
            console.error(err);
        } finally {
            setAnalyticsLoading(false);
        }
    };

    // Fetch page+query dimension data to get keywords for each page
    const fetchPageKeywords = async (siteUrl, startDate, endDate) => {
        try {
            const resp = await fetch(`${API_URL}/api/gsc/analytics?site_url=${encodeURIComponent(siteUrl)}&start_date=${startDate}&end_date=${endDate}&dimensions=page,query`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('google_token')}` }
            });
            const data = await resp.json();
            if (!resp.ok) return;

            // Group keywords by page URL
            const keywordMap = {};
            data.forEach(row => {
                if (row.keys && row.keys.length >= 2) {
                    const pageUrl = row.keys[0];
                    const keyword = row.keys[1];
                    if (!keywordMap[pageUrl]) {
                        keywordMap[pageUrl] = [];
                    }
                    keywordMap[pageUrl].push({
                        keyword,
                        clicks: row.clicks,
                        impressions: row.impressions
                    });
                }
            });

            // Sort keywords by clicks and keep top 5 per page
            Object.keys(keywordMap).forEach(page => {
                keywordMap[page].sort((a, b) => b.clicks - a.clicks);
                keywordMap[page] = keywordMap[page].slice(0, 5);
            });

            setPageKeywords(keywordMap);
        } catch (err) {
            console.error('Failed to fetch page keywords:', err);
        }
    };

    // Fetch real page titles from backend (scrapes URLs)
    const fetchPageTitles = async (urls) => {
        // Filter URLs we don't already have titles for
        const newUrls = urls.filter(url => !pageTitles[url]);
        if (newUrls.length === 0) return;

        try {
            const resp = await fetch(`${API_URL}/api/gsc/page-titles`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('google_token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ urls: newUrls.slice(0, 50) })
            });

            if (!resp.ok) return;
            const titles = await resp.json();

            setPageTitles(prev => ({ ...prev, ...titles }));
        } catch (err) {
            console.error('Failed to fetch page titles:', err);
        }
    };

    // Fetch trend data (compare current period with previous period)
    const fetchTrendData = async (siteUrl, startDate, endDate) => {
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

        if (activeTab !== 'daily') {
            data = data.slice(0, rowLimit);
        }

        return data;
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
        <div style={{ padding: '20px', color: 'var(--text-secondary)' }}>
            {t('載入網站列表...', 'Loading sites...')}
        </div>
    );

    if (error) return (
        <div style={{ padding: '20px', color: '#ea4335' }}>
            {t('錯誤:', 'Error:')} {error}
        </div>
    );

    const sortedData = getSortedFilteredData();
    const showGroupedView = groupingEnabled && activeTab === 'query' && groupedData;

    return (
        <div style={containerStyle}>
            {/* Site Selector */}
            <div style={headerStyle}>
                <label style={labelStyle}>{t('選擇資源:', 'Select Property:')}</label>
                <select
                    value={selectedSite}
                    onChange={(e) => setSelectedSite(e.target.value)}
                    style={selectStyle}
                >
                    {sites.map(site => (
                        <option key={site.siteUrl} value={site.siteUrl}>
                            {site.siteUrl} ({site.permissionLevel})
                        </option>
                    ))}
                </select>
            </div>

            {/* Date Range Selector */}
            <div style={{
                background: 'var(--bg-secondary)',
                padding: isMobile ? '12px' : '16px',
                borderRadius: '12px',
                border: '1px solid var(--glass-border)',
                display: 'flex',
                flexDirection: isMobile ? 'column' : 'row',
                gap: isMobile ? '12px' : '16px',
                alignItems: isMobile ? 'stretch' : 'center',
                flexWrap: 'wrap'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: isMobile ? '1' : 'none' }}>
                    <label style={{ ...labelStyle, whiteSpace: 'nowrap' }}>{t('日期範圍:', 'Date Range:')}</label>
                    <select
                        value={datePreset}
                        onChange={(e) => handlePresetChange(e.target.value)}
                        style={{ ...selectStyle, flex: isMobile ? 1 : 'none' }}
                    >
                        {DATE_PRESETS.map(preset => (
                            <option key={preset.key} value={preset.key}>
                                {language === 'zh' ? preset.label_zh : preset.label_en}
                            </option>
                        ))}
                    </select>
                </div>

                {showCustomDate && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: isMobile ? '1' : 'none', flexWrap: 'wrap' }}>
                        <input
                            type="date"
                            value={dateRange.start}
                            onChange={(e) => handleCustomDateChange('start', e.target.value)}
                            style={{ ...selectStyle, flex: isMobile ? 1 : 'none', minWidth: '130px' }}
                        />
                        <span style={{ color: 'var(--text-secondary)' }}>→</span>
                        <input
                            type="date"
                            value={dateRange.end}
                            onChange={(e) => handleCustomDateChange('end', e.target.value)}
                            style={{ ...selectStyle, flex: isMobile ? 1 : 'none', minWidth: '130px' }}
                        />
                    </div>
                )}

                <div style={{ color: 'var(--text-secondary)', fontSize: isMobile ? '12px' : '13px', marginLeft: isMobile ? 0 : 'auto' }}>
                    {dateRange.start} ~ {dateRange.end} ({getDaysInRange()} {t('天', 'days')})
                </div>
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
                <div style={{ color: 'var(--text-secondary)' }}>
                    {t('載入數據中...', 'Loading analytics...')}
                </div>
            ) : (
                <>
                    {/* Summary Cards - hide for trend tab */}
                    {activeTab !== 'trend' && (
                        <div style={gridStyle}>
                            <div style={cardStyle}>
                                <div style={cardLabelStyle}>{t(`總點擊數 (${getDaysInRange()}天)`, `Total Clicks (${getDaysInRange()}d)`)}</div>
                                <div style={cardValueStyle}>
                                    {analytics.reduce((acc, row) => acc + row.clicks, 0).toLocaleString()}
                                </div>
                            </div>
                            <div style={cardStyle}>
                                <div style={cardLabelStyle}>{t(`總曝光數 (${getDaysInRange()}天)`, `Total Impressions (${getDaysInRange()}d)`)}</div>
                                <div style={cardValueStyle}>
                                    {analytics.reduce((acc, row) => acc + row.impressions, 0).toLocaleString()}
                                </div>
                            </div>
                            <div style={cardStyle}>
                                <div style={cardLabelStyle}>{t('平均點閱率', 'Avg CTR')}</div>
                                <div style={cardValueStyle}>
                                    {(analytics.reduce((acc, row) => acc + row.ctr, 0) / (analytics.length || 1) * 100).toFixed(2)}%
                                </div>
                            </div>
                            <div style={cardStyle}>
                                <div style={cardLabelStyle}>{t('平均排名', 'Avg Position')}</div>
                                <div style={cardValueStyle}>
                                    {(analytics.reduce((acc, row) => acc + row.position, 0) / (analytics.length || 1)).toFixed(1)}
                                </div>
                            </div>
                        </div>
                    )}

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
                                        onChange={(e) => setRowLimit(Number(e.target.value))}
                                        style={{ ...selectStyle, width: 'auto', padding: '8px 12px' }}
                                    >
                                        <option value={50}>Top 50</option>
                                        <option value={100}>Top 100</option>
                                        <option value={200}>Top 200</option>
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
                                            return getSortedFilteredData().map((row, idx) => {
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

                                        <input
                                            type="text"
                                            placeholder={t('搜尋...', 'Search...')}
                                            value={searchKeyword}
                                            onChange={(e) => setSearchKeyword(e.target.value)}
                                            style={searchInputStyle}
                                        />
                                        <select
                                            value={rowLimit}
                                            onChange={(e) => setRowLimit(Number(e.target.value))}
                                            style={{ ...selectStyle, width: 'auto', padding: '8px 12px' }}
                                        >
                                            <option value={50}>Top 50</option>
                                            <option value={100}>Top 100</option>
                                            <option value={200}>Top 200</option>
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
                                                                            fontWeight: '500'
                                                                        }}>
                                                                            🔍 {t('核心關鍵字', 'Core Keywords')}
                                                                        </div>
                                                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                                                                            {keywords.map((kw, kIdx) => (
                                                                                <div key={kIdx} style={{
                                                                                    display: 'flex',
                                                                                    justifyContent: 'space-between',
                                                                                    alignItems: 'center',
                                                                                    padding: '6px 10px',
                                                                                    background: 'var(--bg-primary)',
                                                                                    borderRadius: '6px',
                                                                                    fontSize: '13px'
                                                                                }}>
                                                                                    <span style={{ color: 'var(--text-primary)', flex: 1 }}>
                                                                                        {kw.keyword}
                                                                                    </span>
                                                                                    <div style={{ display: 'flex', gap: '16px', marginLeft: '12px' }}>
                                                                                        <span style={{
                                                                                            color: 'var(--accent-primary)',
                                                                                            fontWeight: '500'
                                                                                        }}>
                                                                                            {kw.clicks.toLocaleString()} {t('點擊', 'clicks')}
                                                                                        </span>
                                                                                        <span style={{
                                                                                            color: 'var(--text-secondary)'
                                                                                        }}>
                                                                                            {kw.impressions.toLocaleString()} {t('曝光', 'impr.')}
                                                                                        </span>
                                                                                    </div>
                                                                                </div>
                                                                            ))}
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
                        </div>
                    )}
                </>
            )}
        </div>
    );
};

export default GSCStats;

