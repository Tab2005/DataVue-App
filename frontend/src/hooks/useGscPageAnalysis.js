import { useEffect, useState } from 'react';
import { getDateRangeFromPreset } from '../components/GSC/gscUtils';

export const INTENT_TYPES = {
    informational: { label_zh: '資訊型', label_en: 'Informational', color: '#3B82F6', emoji: '🔵' },
    commercial: { label_zh: '商業型', label_en: 'Commercial', color: '#F59E0B', emoji: '🟠' },
    navigational: { label_zh: '導航型', label_en: 'Navigational', color: '#10B981', emoji: '🟢' },
    transactional: { label_zh: '交易型', label_en: 'Transactional', color: '#EF4444', emoji: '🔴' }
};

export const useGscPageAnalysis = ({
    apiUrl,
    selectedSite,
    dateRange,
    datePreset,
    activeDateRange,
    activeTab,
    analytics,
    trendData,
    rowLimit,
    setActiveTab,
    language
}) => {
    const [pageKeywords, setPageKeywords] = useState({});
    const [pageKeywordsOffset, setPageKeywordsOffset] = useState(0);
    const [pageKeywordsHasMore, setPageKeywordsHasMore] = useState(true);
    const [pageKeywordsLoading, setPageKeywordsLoading] = useState(false);
    const [pageKeywordsLoadTime, setPageKeywordsLoadTime] = useState(null);
    const [pageKeywordsTotalCount, setPageKeywordsTotalCount] = useState(0);
    const [pageTitles, setPageTitles] = useState({});
    const [titlesRefreshing, setTitlesRefreshing] = useState(false);
    const [keywordIntents, setKeywordIntents] = useState(() => {
        try {
            const saved = localStorage.getItem('gsc_keyword_intents');
            return saved ? JSON.parse(saved) : {};
        } catch {
            return {};
        }
    });
    const [intentLoading, setIntentLoading] = useState({});
    const [intentError, setIntentError] = useState({});
    const [expandedKeywordsCount, setExpandedKeywordsCount] = useState({});
    const [gapLoading, setGapLoading] = useState(false);
    const [gapResults, setGapResults] = useState(null);
    const [gapError, setGapError] = useState(null);
    const [gapUrl, setGapUrl] = useState('');
    const [gapTopN, setGapTopN] = useState(100);
    const [gapDatePreset, setGapDatePreset] = useState('last_28d');
    const [gapDateRange, setGapDateRange] = useState(getDateRangeFromPreset('last_28d'));
    const pageKeywordsPageSize = 2000;

    useEffect(() => {
        if (!gapResults) {
            setGapDateRange(dateRange);
            setGapDatePreset(datePreset);
        }
    }, [selectedSite]);

    useEffect(() => {
        if (Object.keys(keywordIntents).length > 0) {
            try {
                localStorage.setItem('gsc_keyword_intents', JSON.stringify(keywordIntents));
            } catch (e) {
                console.warn('Failed to save keyword intents to LocalStorage:', e);
            }
        }
    }, [keywordIntents]);

    const getPageIntent = (pageUrl) => {
        const keywords = pageKeywords[pageUrl] || [];
        if (keywords.length === 0) return null;
        const topKeywords = keywords.slice(0, 10);
        const totalClicks = topKeywords.reduce((sum, kw) => sum + (kw.clicks || 0), 0) || 1;
        const distribution = { informational: 0, commercial: 0, navigational: 0, transactional: 0 };
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
        const primaryIntent = Object.entries(distribution).sort((a, b) => b[1] - a[1])[0][0];
        return { primary_intent: primaryIntent, intent_distribution: distribution, analyzed_count: analyzedCount, total_count: topKeywords.length };
    };

    useEffect(() => {
        if (activeTab === 'page') {
            setPageKeywordsOffset(0);
            setPageKeywordsHasMore(true);
            setPageKeywordsLoadTime(null);
        }
    }, [selectedSite, activeDateRange.start, activeDateRange.end, activeTab, rowLimit]);

    useEffect(() => {
        if (selectedSite && activeDateRange.start && activeDateRange.end) {
            setPageKeywords({});
            setPageKeywordsTotalCount(0);
        }
    }, [selectedSite, activeDateRange.start, activeDateRange.end]);

    const fetchPageKeywords = async (siteUrl, startDate, endDate, options = {}) => {
        const { append = false, offset = 0 } = options;
        const startTime = performance.now();
        if (!append) setPageKeywordsLoading(true);
        try {
            const limitParam = `&limit=${pageKeywordsPageSize}`;
            const offsetParam = offset > 0 ? `&offset=${offset}` : '';
            const resp = await fetch(`${apiUrl}/api/gsc/analytics?site_url=${encodeURIComponent(siteUrl)}&start_date=${startDate}&end_date=${endDate}&dimensions=page,query${limitParam}${offsetParam}`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('google_token')}` }
            });
            const data = await resp.json();
            const loadTime = Math.round(performance.now() - startTime);
            setPageKeywordsLoadTime(loadTime);
            if (!resp.ok) {
                setPageKeywordsLoading(false);
                return;
            }
            if (data.length < pageKeywordsPageSize) setPageKeywordsHasMore(false);
            const newKeywordMap = {};
            data.forEach(row => {
                if (row.keys && row.keys.length >= 2) {
                    const pageUrl = row.keys[0];
                    const keyword = row.keys[1];
                    if (!newKeywordMap[pageUrl]) newKeywordMap[pageUrl] = [];
                    newKeywordMap[pageUrl].push({ keyword, clicks: row.clicks, impressions: row.impressions });
                }
            });
            Object.keys(newKeywordMap).forEach(page => {
                newKeywordMap[page].sort((a, b) => b.clicks - a.clicks);
            });
            if (append) {
                setPageKeywords(prev => {
                    const merged = { ...prev };
                    Object.keys(newKeywordMap).forEach(page => {
                        merged[page] = merged[page]
                            ? [...merged[page], ...newKeywordMap[page]].sort((a, b) => b.clicks - a.clicks)
                            : newKeywordMap[page];
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

    const loadMorePageKeywords = () => {
        if (pageKeywordsLoading || !pageKeywordsHasMore) return;
        if (!selectedSite || !dateRange.start || !dateRange.end) return;
        const nextOffset = pageKeywordsOffset + pageKeywordsPageSize;
        fetchPageKeywords(selectedSite, dateRange.start, dateRange.end, { append: true, offset: nextOffset });
    };

    const fetchPageTitles = async (urls, forceRefresh = false) => {
        const newUrls = forceRefresh ? urls : urls.filter(url => !pageTitles[url]);
        if (newUrls.length === 0) return;
        try {
            const resp = await fetch(`${apiUrl}/api/gsc/page-titles`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('google_token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ urls: newUrls.slice(0, 50), force_refresh: forceRefresh })
            });
            if (!resp.ok) return;
            const titles = await resp.json();
            setPageTitles(prev => ({ ...prev, ...titles }));
        } catch (err) {
            console.error('Failed to fetch page titles:', err);
        }
    };

    useEffect(() => {
        if (activeTab === 'page' && selectedSite && activeDateRange.start && activeDateRange.end) {
            fetchPageKeywords(selectedSite, activeDateRange.start, activeDateRange.end);
        }
    }, [selectedSite, activeDateRange, activeTab]);

    useEffect(() => {
        if (activeTab === 'page' && analytics.length > 0) {
            const urls = analytics.slice(0, 50).map(row => row.keys?.[0]).filter(Boolean);
            if (urls.length > 0) fetchPageTitles(urls);
        } else if (activeTab === 'trend' && trendData.length > 0) {
            const urls = trendData.slice(0, 50).map(row => row.keys?.[0]).filter(Boolean);
            if (urls.length > 0) fetchPageTitles(urls);
        }
    }, [activeTab, analytics, trendData]);

    const fetchPageIntent = async (pageUrl, analyzeAll = false) => {
        if (!selectedSite || !dateRange.start || !dateRange.end) return;
        if (intentLoading[pageUrl]) return;
        const keywords = pageKeywords[pageUrl] || [];
        if (keywords.length === 0) {
            setIntentError(prev => ({ ...prev, [pageUrl]: 'No keywords available' }));
            return;
        }
        const uncachedKeywords = keywords.filter(kw => !keywordIntents[kw.keyword || kw.query]);
        if (uncachedKeywords.length === 0) {
            console.log(`All ${keywords.length} keywords already analyzed for ${pageUrl}`);
            return;
        }
        setIntentLoading(prev => ({ ...prev, [pageUrl]: true }));
        setIntentError(prev => ({ ...prev, [pageUrl]: null }));
        try {
            const maxKeywords = analyzeAll ? 100 : 10;
            const keywordsToAnalyze = uncachedKeywords.slice(0, maxKeywords).map(kw => kw.keyword || kw.query);
            const requestBody = {
                site_url: selectedSite,
                page_url: pageUrl,
                start_date: dateRange.start,
                end_date: dateRange.end,
                top_n: maxKeywords,
                provider: localStorage.getItem('ai_provider') || 'zeabur'
            };
            if (analyzeAll) requestBody.keywords = keywordsToAnalyze;
            const resp = await fetch(`${apiUrl}/api/gsc/page-intents`, {
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
            if (data.message && data.message.includes('not configured')) throw new Error(data.message);
            const newKeywordIntents = {};
            (data.keywords || []).forEach(kw => {
                const query = kw.query || kw.keyword;
                const intent = kw.intent;
                if (query && intent && intent !== 'unknown') {
                    newKeywordIntents[query] = { intent, confidence: kw.confidence || 0.8, analyzed_at: new Date().toISOString() };
                }
            });
            setKeywordIntents(prev => ({ ...prev, ...newKeywordIntents }));
        } catch (err) {
            console.error('Failed to fetch page intent:', err);
            setIntentError(prev => ({ ...prev, [pageUrl]: err.message }));
        } finally {
            setIntentLoading(prev => ({ ...prev, [pageUrl]: false }));
        }
    };

    const fetchKeywordGap = async (targetUrl = null) => {
        const urlToAnalyze = targetUrl || gapUrl;
        if (!urlToAnalyze || !selectedSite) {
            const msg = language === 'zh' ? '請提供有效的網頁 URL' : 'Please provide a valid page URL';
            setGapError(msg);
            alert(msg);
            return;
        }
        setGapLoading(true);
        setGapError(null);
        setActiveTab('gap');
        if (targetUrl) setGapUrl(targetUrl);
        try {
            const resp = await fetch(`${apiUrl}/api/gsc/keyword-gap`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('google_token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    site_url: selectedSite,
                    page_url: urlToAnalyze,
                    start_date: gapDateRange.start,
                    end_date: gapDateRange.end,
                    top_n: gapTopN
                })
            });
            if (!resp.ok) {
                const errorData = await resp.json();
                throw new Error(errorData.error || errorData.detail || 'Gap analysis failed');
            }
            setGapResults(await resp.json());
        } catch (err) {
            console.error('Failed to fetch keyword gap:', err);
            setGapError(err.message);
        } finally {
            setGapLoading(false);
        }
    };

    return {
        pageKeywords,
        pageKeywordsHasMore,
        pageKeywordsLoading,
        pageKeywordsLoadTime,
        pageKeywordsTotalCount,
        loadMorePageKeywords,
        pageTitles,
        titlesRefreshing,
        setTitlesRefreshing,
        keywordIntents,
        intentLoading,
        intentError,
        expandedKeywordsCount,
        setExpandedKeywordsCount,
        INTENT_TYPES,
        getPageIntent,
        fetchPageTitles,
        fetchPageIntent,
        gapLoading,
        gapResults,
        gapError,
        gapUrl,
        setGapUrl,
        gapTopN,
        setGapTopN,
        gapDatePreset,
        setGapDatePreset,
        gapDateRange,
        setGapDateRange,
        fetchKeywordGap
    };
};
