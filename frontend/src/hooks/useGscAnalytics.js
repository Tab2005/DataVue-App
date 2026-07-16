import { useEffect, useState } from 'react';
import { TABS } from '../components/GSC/constants';
import { formatDate, getDateRangeFromPreset } from '../components/GSC/gscUtils';

export const useGscAnalytics = ({ apiUrl, rowLimit, queryPageSize }) => {
    const [sites, setSites] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedSite, setSelectedSite] = useState('');
    const [analytics, setAnalytics] = useState([]);
    const [analyticsLoading, setAnalyticsLoading] = useState(false);

    const [queryOffset, setQueryOffset] = useState(0);
    const [queryHasMore, setQueryHasMore] = useState(true);
    const [queryLoadingMore, setQueryLoadingMore] = useState(false);

    const [analyticsCache, setAnalyticsCache] = useState({});
    const [loadedDimensions, setLoadedDimensions] = useState(new Set(['date']));

    const [activeTab, setActiveTab] = useState('daily');

    const [datePreset, setDatePreset] = useState('last_28d');
    const [dateRange, setDateRange] = useState(getDateRangeFromPreset('last_28d'));
    const [activeDateRange, setActiveDateRange] = useState(getDateRangeFromPreset('last_28d'));
    const [showCustomDate, setShowCustomDate] = useState(false);

    const [compareMode, setCompareMode] = useState('none');
    const [compareData, setCompareData] = useState([]);

    const [trendSubTab, setTrendSubTab] = useState('top');
    const [trendData, setTrendData] = useState([]);
    const [trendLoading, setTrendLoading] = useState(false);

    useEffect(() => {
        fetchSites();
    }, []);

    const fetchSites = async () => {
        try {
            const resp = await fetch(`${apiUrl}/api/gsc/sites`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('google_token')}` }
            });
            const contentType = resp.headers.get('content-type');
            if (contentType && contentType.indexOf('application/json') !== -1) {
                const data = await resp.json();
                if (!resp.ok) throw new Error(data.detail || 'Failed to fetch sites');
                setSites(data);
                if (data.length > 0) setSelectedSite(data[0].siteUrl);
            } else {
                throw new Error('Server returned non-JSON response');
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (activeTab === 'query') {
            setQueryOffset(0);
            setQueryHasMore(true);
            setQueryLoadingMore(false);
        }
    }, [selectedSite, activeDateRange.start, activeDateRange.end, activeTab, rowLimit]);

    useEffect(() => {
        if (selectedSite && activeDateRange.start && activeDateRange.end) {
            setAnalyticsCache({});
            setLoadedDimensions(new Set());
            setAnalytics([]);
        }
    }, [selectedSite, activeDateRange.start, activeDateRange.end]);

    useEffect(() => {
        if (selectedSite && activeDateRange.start && activeDateRange.end) {
            const currentTab = TABS.find(tab => tab.key === activeTab);
            const dimension = currentTab ? currentTab.dimension : 'date';

            if (activeTab === 'trend') {
                fetchTrendData(selectedSite, activeDateRange.start, activeDateRange.end);
            } else if (!loadedDimensions.has(dimension)) {
                fetchAnalytics(selectedSite, activeDateRange.start, activeDateRange.end, dimension);
            } else {
                const cacheKey = `${selectedSite}-${activeDateRange.start}-${activeDateRange.end}-${dimension}`;
                if (analyticsCache[cacheKey]) {
                    setAnalytics(analyticsCache[cacheKey]);
                }
            }
        }
    }, [selectedSite, activeDateRange, activeTab, loadedDimensions, analyticsCache]);

    const fetchAnalytics = async (siteUrl, startDate, endDate, dimension = 'date', options = {}) => {
        const { append = false, offset = 0 } = options;

        const baseKey = `${siteUrl}-${startDate}-${endDate}-${dimension}`;
        const limit = dimension === 'query' ? queryPageSize : null;
        const cacheKey = dimension === 'query' ? `${baseKey}-${offset}-${limit}` : baseKey;
        const combinedKey = dimension === 'query' ? `${baseKey}-combined` : baseKey;

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
            const resp = await fetch(`${apiUrl}/api/gsc/analytics?site_url=${encodeURIComponent(siteUrl)}&start_date=${startDate}&end_date=${endDate}&dimensions=${dimension}${limitParam}${offsetParam}`, {
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
                setAnalyticsCache(prev => ({ ...prev, [cacheKey]: data }));
                setAnalytics(data);
            }

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

    const loadMoreQueryData = () => {
        if (activeTab !== 'query' || queryLoadingMore || !queryHasMore) return;
        if (!selectedSite || !dateRange.start || !dateRange.end) return;

        const nextOffset = queryOffset + queryPageSize;
        fetchAnalytics(selectedSite, dateRange.start, dateRange.end, 'query', { append: true, offset: nextOffset });
    };

    const fetchTrendData = async (siteUrl, startDate, endDate) => {
        const cacheKey = `trend-${siteUrl}-${startDate}-${endDate}`;

        if (analyticsCache[cacheKey]) {
            console.log('Using cached trend data');
            setTrendData(analyticsCache[cacheKey]);
            return;
        }

        console.log('Fetching fresh trend data');
        setTrendLoading(true);
        try {
            const start = new Date(startDate);
            const end = new Date(endDate);
            const daysDiff = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1;

            const prevEnd = new Date(start);
            prevEnd.setDate(prevEnd.getDate() - 1);
            const prevStart = new Date(prevEnd);
            prevStart.setDate(prevStart.getDate() - daysDiff + 1);

            const prevStartStr = formatDate(prevStart);
            const prevEndStr = formatDate(prevEnd);

            const [currentResp, prevResp] = await Promise.all([
                fetch(`${apiUrl}/api/gsc/analytics?site_url=${encodeURIComponent(siteUrl)}&start_date=${startDate}&end_date=${endDate}&dimensions=page`, {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('google_token')}` }
                }),
                fetch(`${apiUrl}/api/gsc/analytics?site_url=${encodeURIComponent(siteUrl)}&start_date=${prevStartStr}&end_date=${prevEndStr}&dimensions=page`, {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('google_token')}` }
                })
            ]);

            const currentData = await currentResp.json();
            const prevData = await prevResp.json();

            if (!currentResp.ok) throw new Error(currentData.detail);

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
            const newRange = getDateRangeFromPreset(presetKey);
            setDateRange(newRange);
            setActiveDateRange(newRange);
        }
    };

    const handleRunAnalysis = () => {
        setActiveDateRange({ ...dateRange });
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

    const getCompareDateRange = () => {
        if (compareMode === 'none') return null;

        const start = new Date(dateRange.start);
        const end = new Date(dateRange.end);
        const daysDiff = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1;

        if (compareMode === 'previous_period') {
            const prevEnd = new Date(start);
            prevEnd.setDate(prevEnd.getDate() - 1);
            const prevStart = new Date(prevEnd);
            prevStart.setDate(prevStart.getDate() - daysDiff + 1);
            return { start: formatDate(prevStart), end: formatDate(prevEnd) };
        } else if (compareMode === 'previous_year') {
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

        try {
            const currentTab = TABS.find(tab => tab.key === activeTab);
            const dimension = currentTab?.dimension || 'date';

            const resp = await fetch(
                `${apiUrl}/api/gsc/analytics?site_url=${encodeURIComponent(selectedSite)}&start_date=${compareDateRange.start}&end_date=${compareDateRange.end}&dimensions=${dimension}`,
                { headers: { 'Authorization': `Bearer ${localStorage.getItem('google_token')}` } }
            );
            const data = await resp.json();
            if (resp.ok) {
                setCompareData(data);
            }
        } catch (err) {
            console.error('Failed to fetch compare data:', err);
        } finally {
            // No local cleanup required; compare data is best-effort and optional.
        }
    };

    const calculateChange = (current, previous) => {
        if (previous === 0) return current > 0 ? 100 : 0;
        return ((current - previous) / previous * 100);
    };

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

        const count = compareData.length || 1;
        totals.ctr = totals.ctr / count;
        totals.position = totals.position / count;

        return totals;
    };

    useEffect(() => {
        if (compareMode !== 'none' && selectedSite && activeDateRange.start && activeDateRange.end) {
            const compareDateRange = getCompareDateRange();
            if (compareDateRange) {
                fetchCompareData(compareDateRange);
            }
        } else {
            setCompareData([]);
        }
    }, [compareMode, selectedSite, activeDateRange, activeTab]);

    return {
        sites,
        loading,
        error,
        selectedSite,
        setSelectedSite,
        analytics,
        analyticsLoading,
        queryHasMore,
        queryLoadingMore,
        activeTab,
        setActiveTab,
        datePreset,
        dateRange,
        setDateRange,
        activeDateRange,
        showCustomDate,
        setShowCustomDate,
        compareMode,
        setCompareMode,
        trendSubTab,
        setTrendSubTab,
        trendData,
        trendLoading,
        loadMoreQueryData,
        handlePresetChange,
        handleRunAnalysis,
        handleCustomDateChange,
        getDaysInRange,
        getCompareDateRange,
        calculateChange,
        getCompareTotals
    };
};
