import { useCallback, useEffect, useRef, useState } from 'react';
import { CACHE_TTL, DATE_PRESETS, TABS } from '../components/GA4/constants';
import { formatLocalDate } from '../components/GA4/ga4Formatters';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const getInitialDateRange = () => {
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const startDate = new Date(yesterday);
    startDate.setDate(startDate.getDate() - 27);
    return {
        startDate: formatLocalDate(startDate),
        endDate: formatLocalDate(yesterday),
        preset: 'last_28d'
    };
};

const getDimensionKey = ({
    activeTab,
    trafficDimension,
    behaviorDimension,
    ecommerceDimension,
    ecommerceSecondaryDimension,
    contentDimension
}) => {
    if (activeTab === 'traffic') return trafficDimension;
    if (activeTab === 'behavior') return behaviorDimension;
    if (activeTab === 'ecommerce') return `${ecommerceDimension}|${ecommerceSecondaryDimension}`;
    if (activeTab === 'content') return contentDimension;
    return 'default';
};

const getActiveDimension = ({
    activeTab,
    tabConfig,
    trafficDimension,
    behaviorDimension,
    ecommerceDimension,
    ecommerceSecondaryDimension,
    contentDimension
}) => {
    if (activeTab === 'traffic') return trafficDimension;
    if (activeTab === 'behavior') return behaviorDimension;
    if (activeTab === 'ecommerce') {
        return ecommerceSecondaryDimension !== 'none'
            ? `${ecommerceDimension},${ecommerceSecondaryDimension}`
            : ecommerceDimension;
    }
    if (activeTab === 'content') return contentDimension;
    return tabConfig.dimensions[0];
};

export const useGa4StatsData = ({
    trafficDimension,
    behaviorDimension,
    ecommerceDimension,
    ecommerceSecondaryDimension,
    contentDimension,
    ga4PageSize,
    setCurrentPage
}) => {
    const [properties, setProperties] = useState([]);
    const [propertiesLoading, setPropertiesLoading] = useState(false);
    const [selectedProperty, setSelectedProperty] = useState('');
    const [analyticsData, setAnalyticsData] = useState(null);
    const [summaryData, setSummaryData] = useState(null);
    const [compareData, setCompareData] = useState(null);
    const [compareSummaryData, setCompareSummaryData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('overview');
    const [ga4Offset, setGa4Offset] = useState(0);
    const [ga4HasMore, setGa4HasMore] = useState(true);
    const [ga4LoadingMore, setGa4LoadingMore] = useState(false);
    const [showCustomDatePicker, setShowCustomDatePicker] = useState(false);
    const [compareMode, setCompareMode] = useState('none');
    const [dateRange, setDateRange] = useState(getInitialDateRange);
    const cacheRef = useRef(new Map());

    const getCacheKey = useCallback((propertyId, tab, start, end) => {
        return `${propertyId}|${tab}|${start}|${end}`;
    }, []);

    const getCachedData = useCallback((key) => {
        const cached = cacheRef.current.get(key);
        if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
            return cached.data;
        }
        return null;
    }, []);

    const setCachedData = useCallback((key, data) => {
        cacheRef.current.set(key, { data, timestamp: Date.now() });
    }, []);

    const fetchProperties = useCallback(async () => {
        setPropertiesLoading(true);
        try {
            const response = await fetch(`${API_URL}/api/ga4/properties`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('google_token')}` }
            });
            if (!response.ok) throw new Error('Failed to fetch properties');
            const data = await response.json();
            setProperties(data.properties || []);
            if (data.properties && data.properties.length > 0) {
                setSelectedProperty(prev => prev || data.properties[0].property_id);
            }
        } catch (err) {
            console.error('Error fetching GA4 properties:', err);
            setError('Failed to load properties');
        } finally {
            setPropertiesLoading(false);
        }
    }, []);

    const fetchAnalytics = useCallback(async (forceRefresh = false, options = {}) => {
        const { append = false, offset = 0 } = options;
        if (!selectedProperty) return;

        if (forceRefresh) {
            setGa4Offset(0);
            setGa4HasMore(true);
        }

        const dimensionKey = getDimensionKey({
            activeTab,
            trafficDimension,
            behaviorDimension,
            ecommerceDimension,
            ecommerceSecondaryDimension,
            contentDimension
        });
        const baseKey = getCacheKey(selectedProperty, `${activeTab}|${dimensionKey}`, dateRange.startDate, dateRange.endDate);
        const pageKey = `${baseKey}|page|${offset}|${ga4PageSize}`;
        const combinedKey = `${baseKey}|combined`;
        const summaryCacheKey = `${baseKey}|summary`;

        if (!forceRefresh) {
            if (!append) {
                const cachedCombined = getCachedData(combinedKey);
                const cachedSummary = getCachedData(summaryCacheKey);
                if (cachedCombined && cachedSummary) {
                    console.log('📦 Using cached data for:', combinedKey);
                    setAnalyticsData(cachedCombined);
                    setSummaryData(cachedSummary);
                    if (cachedCombined.total_row_count) {
                        setGa4HasMore(cachedCombined.rows.length < cachedCombined.total_row_count);
                    }
                    return;
                }
            } else {
                const cachedPage = getCachedData(pageKey);
                if (cachedPage) {
                    setAnalyticsData(prev => {
                        const prevRows = prev?.rows || [];
                        const mergedRows = [...prevRows, ...(cachedPage.rows || [])];
                        const totalRowCount = cachedPage.total_row_count || prev?.total_row_count || mergedRows.length;
                        const mergedData = {
                            ...cachedPage,
                            rows: mergedRows,
                            row_count: mergedRows.length,
                            total_row_count: totalRowCount
                        };
                        setCachedData(combinedKey, mergedData);
                        if (cachedPage.total_row_count) {
                            setGa4HasMore(mergedRows.length < cachedPage.total_row_count);
                        }
                        return mergedData;
                    });
                    return;
                }
            }
        }

        if (append) setGa4LoadingMore(true);
        else setLoading(true);
        setError(null);

        try {
            const tabConfig = TABS.find(tab => tab.key === activeTab);
            const activeDimension = getActiveDimension({
                activeTab,
                tabConfig,
                trafficDimension,
                behaviorDimension,
                ecommerceDimension,
                ecommerceSecondaryDimension,
                contentDimension
            });
            const params = new URLSearchParams({
                property_id: selectedProperty,
                start_date: dateRange.startDate,
                end_date: dateRange.endDate,
                metrics: tabConfig.metrics.join(','),
                dimensions: activeDimension,
                limit: String(ga4PageSize),
                offset: String(offset)
            });
            const summaryParams = new URLSearchParams({
                property_id: selectedProperty,
                start_date: dateRange.startDate,
                end_date: dateRange.endDate,
                metrics: tabConfig.metrics.join(','),
                dimensions: ''
            });

            const [response, summaryResponse] = await Promise.all([
                fetch(`${API_URL}/api/ga4/report?${params}`, {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('google_token')}` }
                }),
                fetch(`${API_URL}/api/ga4/report?${summaryParams}`, {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('google_token')}` }
                })
            ]);

            if (!response.ok) throw new Error('Failed to fetch analytics data');
            const data = await response.json();
            const summary = summaryResponse.ok ? await summaryResponse.json() : null;
            const totalRowCount = data.total_row_count ?? data.row_count ?? (data.rows ? data.rows.length : 0);
            const incomingRows = data.rows || [];
            const mergedRows = append && analyticsData?.rows ? [...analyticsData.rows, ...incomingRows] : incomingRows;
            const combinedData = {
                ...data,
                rows: mergedRows,
                row_count: mergedRows.length,
                total_row_count: totalRowCount,
                limit: ga4PageSize,
                offset
            };

            setCachedData(pageKey, data);
            setCachedData(combinedKey, combinedData);
            if (summary) setCachedData(summaryCacheKey, summary);
            console.log('💾 Cached data for:', combinedKey);

            setAnalyticsData(combinedData);
            setSummaryData(summary);
            setCurrentPage(1);

            if (totalRowCount) setGa4HasMore(mergedRows.length < totalRowCount);
            else if (ga4PageSize && incomingRows.length < ga4PageSize) setGa4HasMore(false);

            setGa4Offset(append ? offset : 0);
        } catch (err) {
            console.error('Error fetching GA4 analytics:', err);
            setError('Failed to load analytics data');
        } finally {
            if (append) setGa4LoadingMore(false);
            else setLoading(false);
        }
    }, [
        selectedProperty,
        activeTab,
        dateRange.startDate,
        dateRange.endDate,
        trafficDimension,
        behaviorDimension,
        ecommerceDimension,
        ecommerceSecondaryDimension,
        contentDimension,
        ga4PageSize,
        analyticsData,
        getCacheKey,
        getCachedData,
        setCachedData,
        setCurrentPage
    ]);

    const loadMoreGa4Data = () => {
        if (ga4LoadingMore || !ga4HasMore) return;
        const nextOffset = ga4Offset + ga4PageSize;
        fetchAnalytics(false, { append: true, offset: nextOffset });
    };

    const fetchCompareData = useCallback(async (compareDateRange) => {
        if (!selectedProperty || !compareDateRange) {
            setCompareData(null);
            setCompareSummaryData(null);
            return;
        }

        const dimensionKey = getDimensionKey({
            activeTab,
            trafficDimension,
            behaviorDimension,
            ecommerceDimension,
            ecommerceSecondaryDimension,
            contentDimension
        });
        const cacheKey = getCacheKey(selectedProperty, `${activeTab}|compare|${dimensionKey}`, compareDateRange.startDate, compareDateRange.endDate);
        const summaryCacheKey = `${cacheKey}|summary`;
        const cachedData = getCachedData(cacheKey);
        const cachedSummary = getCachedData(summaryCacheKey);
        if (cachedData && cachedSummary) {
            console.log('📦 Using cached compare data for:', cacheKey);
            setCompareData(cachedData);
            setCompareSummaryData(cachedSummary);
            return;
        }

        try {
            const tabConfig = TABS.find(tab => tab.key === activeTab);
            const activeDimension = getActiveDimension({
                activeTab,
                tabConfig,
                trafficDimension,
                behaviorDimension,
                ecommerceDimension,
                ecommerceSecondaryDimension,
                contentDimension
            });
            const params = new URLSearchParams({
                property_id: selectedProperty,
                start_date: compareDateRange.startDate,
                end_date: compareDateRange.endDate,
                metrics: tabConfig.metrics.join(','),
                dimensions: activeDimension
            });
            const summaryParams = new URLSearchParams({
                property_id: selectedProperty,
                start_date: compareDateRange.startDate,
                end_date: compareDateRange.endDate,
                metrics: tabConfig.metrics.join(','),
                dimensions: ''
            });
            const [response, summaryResponse] = await Promise.all([
                fetch(`${API_URL}/api/ga4/report?${params}`, {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('google_token')}` }
                }),
                fetch(`${API_URL}/api/ga4/report?${summaryParams}`, {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('google_token')}` }
                })
            ]);

            if (response.ok) {
                const data = await response.json();
                const summary = summaryResponse.ok ? await summaryResponse.json() : null;
                setCachedData(cacheKey, data);
                if (summary) setCachedData(summaryCacheKey, summary);
                setCompareData(data);
                setCompareSummaryData(summary);
            }
        } catch (err) {
            console.error('Error fetching compare data:', err);
        }
    }, [
        selectedProperty,
        activeTab,
        trafficDimension,
        behaviorDimension,
        ecommerceDimension,
        ecommerceSecondaryDimension,
        contentDimension,
        getCacheKey,
        getCachedData,
        setCachedData
    ]);

    const handleDatePresetChange = (preset) => {
        const presetConfig = DATE_PRESETS.find(p => p.key === preset);
        const today = new Date();
        let startDate;
        let endDate;

        if (presetConfig.isToday) {
            startDate = endDate = new Date(today);
        } else if (presetConfig.isYesterday) {
            startDate = endDate = new Date(today);
            startDate.setDate(startDate.getDate() - 1);
        } else if (presetConfig.isThisWeek) {
            endDate = new Date(today);
            startDate = new Date(today);
            const dayOfWeek = startDate.getDay();
            const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
            startDate.setDate(startDate.getDate() - daysToMonday);
        } else if (presetConfig.isLastWeek) {
            const lastWeekEnd = new Date(today);
            const dayOfWeek = lastWeekEnd.getDay();
            const daysToLastSunday = dayOfWeek === 0 ? 7 : dayOfWeek;
            lastWeekEnd.setDate(lastWeekEnd.getDate() - daysToLastSunday);
            endDate = new Date(lastWeekEnd);
            startDate = new Date(lastWeekEnd);
            startDate.setDate(startDate.getDate() - 6);
        } else if (presetConfig.isThisMonth) {
            endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);
            startDate = new Date(today.getFullYear(), today.getMonth(), 1);
        } else if (presetConfig.isLastMonth) {
            startDate = new Date(today.getFullYear(), today.getMonth() - 1, 1);
            endDate = new Date(today.getFullYear(), today.getMonth(), 0);
        } else if (presetConfig.days !== null && presetConfig.days > 0) {
            const yesterday = new Date(today);
            yesterday.setDate(yesterday.getDate() - 1);
            endDate = new Date(yesterday);
            startDate = new Date(yesterday);
            startDate.setDate(startDate.getDate() - (presetConfig.days - 1));
        } else if (preset === 'custom') {
            setShowCustomDatePicker(true);
            setDateRange(prev => ({ ...prev, preset: 'custom' }));
            return;
        }

        if (startDate && endDate) {
            setDateRange({
                startDate: formatLocalDate(startDate),
                endDate: formatLocalDate(endDate),
                preset
            });
            setShowCustomDatePicker(false);
        }
    };

    const toggleCustomDatePicker = () => {
        if (dateRange.preset === 'custom') setShowCustomDatePicker(prev => !prev);
        else handleDatePresetChange('custom');
    };

    const getCompareDateRange = useCallback(() => {
        if (compareMode === 'none') return null;
        const start = new Date(dateRange.startDate);
        const end = new Date(dateRange.endDate);
        const daysDiff = Math.ceil((end - start) / (1000 * 60 * 60 * 24));

        if (compareMode === 'previous_period') {
            const compareEnd = new Date(start.getTime() - 24 * 60 * 60 * 1000);
            const compareStart = new Date(compareEnd.getTime() - daysDiff * 24 * 60 * 60 * 1000);
            return {
                startDate: formatLocalDate(compareStart),
                endDate: formatLocalDate(compareEnd)
            };
        }
        if (compareMode === 'previous_year') {
            const compareStart = new Date(start);
            compareStart.setFullYear(compareStart.getFullYear() - 1);
            const compareEnd = new Date(end);
            compareEnd.setFullYear(compareEnd.getFullYear() - 1);
            return {
                startDate: formatLocalDate(compareStart),
                endDate: formatLocalDate(compareEnd)
            };
        }
        return null;
    }, [compareMode, dateRange.startDate, dateRange.endDate]);

    const handleCustomDateChange = (type, value) => {
        setDateRange(prev => ({
            ...prev,
            [type]: value,
            preset: 'custom'
        }));
    };

    const applyCustomDateRange = () => {
        setShowCustomDatePicker(false);
    };

    useEffect(() => {
        fetchProperties();
    }, [fetchProperties]);

    useEffect(() => {
        setGa4Offset(0);
        setGa4HasMore(true);
        setGa4LoadingMore(false);
        setCurrentPage(1);
    }, [
        selectedProperty,
        activeTab,
        dateRange.startDate,
        dateRange.endDate,
        trafficDimension,
        behaviorDimension,
        ecommerceDimension,
        ecommerceSecondaryDimension,
        contentDimension,
        setCurrentPage
    ]);

    useEffect(() => {
        if (selectedProperty && !showCustomDatePicker) {
            fetchAnalytics();
        }
    }, [selectedProperty, activeTab, dateRange, showCustomDatePicker, fetchAnalytics]);

    useEffect(() => {
        if (compareMode !== 'none' && selectedProperty && analyticsData) {
            const compareDateRange = getCompareDateRange();
            if (compareDateRange) fetchCompareData(compareDateRange);
        } else {
            setCompareData(null);
            setCompareSummaryData(null);
        }
    }, [
        compareMode,
        getCompareDateRange,
        fetchCompareData,
        selectedProperty,
        analyticsData,
        trafficDimension,
        behaviorDimension,
        ecommerceDimension,
        ecommerceSecondaryDimension,
        contentDimension
    ]);

    return {
        properties,
        propertiesLoading,
        selectedProperty,
        setSelectedProperty,
        analyticsData,
        summaryData,
        compareData,
        compareSummaryData,
        loading,
        error,
        activeTab,
        setActiveTab,
        ga4HasMore,
        ga4LoadingMore,
        compareMode,
        setCompareMode,
        dateRange,
        setDateRange,
        fetchAnalytics,
        loadMoreGa4Data,
        handleDatePresetChange,
        toggleCustomDatePicker,
        getCompareDateRange,
        handleCustomDateChange,
        applyCustomDateRange
    };
};
