import React, { useEffect, useState, useMemo, useCallback, useRef } from 'react';
import { getAllSourceGroups, isDefaultGroup } from '../utils/sourceGroups';
import { getAllContentGroups, saveCustomContentGroup, deleteCustomContentGroup, isDefaultContentGroup } from '../utils/contentGroups';
import SourceGroupModal from './SourceGroupModal';
import ContentGroupModal from './ContentGroupModal';
import {
    DATE_PRESETS,
    COMPARE_OPTIONS,
    TRAFFIC_DIMENSIONS,
    TRAFFIC_METRICS,
    TRAFFIC_COLUMN_HEADERS,
    BEHAVIOR_DIMENSIONS,
    BEHAVIOR_FILTER_LABELS,
    BEHAVIOR_METRICS,
    BEHAVIOR_COLUMN_HEADERS,
    ECOMMERCE_DIMENSIONS,
    TRAFFIC_SECONDARY_DIMENSIONS,
    ECOMMERCE_METRICS,
    ECOMMERCE_COLUMN_HEADERS,
    CONTENT_DIMENSIONS,
    CONTENT_METRICS,
    CONTENT_COLUMN_HEADERS,
    OVERVIEW_COLUMN_ORDER,
    TABS,
    CACHE_TTL
} from './GA4/constants';
import {
    formatLocalDate,
    formatNumber,
    getMetricLabel as getMetricLabelForLanguage,
    getTrafficColumnOrder as getTrafficColumnOrderForDimension,
    getTrafficColumnLabel as getTrafficColumnLabelForLanguage,
    getBehaviorColumnOrder as getBehaviorColumnOrderForDimension,
    getBehaviorColumnLabel as getBehaviorColumnLabelForLanguage,
    getEcommerceColumnOrder as getEcommerceColumnOrderForDimensions,
    getEcommerceColumnLabel as getEcommerceColumnLabelForLanguage,
    getContentColumnOrder as getContentColumnOrderForDimension,
    getContentColumnLabel as getContentColumnLabelForLanguage
} from './GA4/ga4Formatters';
import {
    getOverviewKPIData,
    getTrafficKPIData,
    getBehaviorKPIData,
    getEcommerceKPIData,
    getContentKPIData
} from './GA4/ga4Kpi';


const GA4Stats = ({ language, isMobile }) => {
    const t = (zh, en) => language === 'zh' ? zh : en;

    // State management
    const [properties, setProperties] = useState([]);
    const [propertiesLoading, setPropertiesLoading] = useState(false);
    const [selectedProperty, setSelectedProperty] = useState('');
    const [analyticsData, setAnalyticsData] = useState(null);
    const [summaryData, setSummaryData] = useState(null); // 新增：用於 KPI 卡片的去重總數
    const [compareData, setCompareData] = useState(null);
    const [compareSummaryData, setCompareSummaryData] = useState(null); // 新增：比較期間的去重總數
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('overview');

    // Server-side pagination for GA4 table data
    const [ga4Offset, setGa4Offset] = useState(0);
    const [ga4HasMore, setGa4HasMore] = useState(true);
    const [ga4LoadingMore, setGa4LoadingMore] = useState(false);
    const [showCustomDatePicker, setShowCustomDatePicker] = useState(false);
    const [compareMode, setCompareMode] = useState('none');
    // 日期計算：「過去 N 天」不包含今天（業界標準，因為今天數據不完整）
    // 例如：過去 28 天 = 昨天往前推 27 天 = 共 28 天
    const [dateRange, setDateRange] = useState(() => {
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        const startDate = new Date(yesterday);
        startDate.setDate(startDate.getDate() - 27); // 28 days total (including yesterday)
        return {
            startDate: formatLocalDate(startDate),
            endDate: formatLocalDate(yesterday),
            preset: 'last_28d'
        };
    });
    const [sortConfig, setSortConfig] = useState({ key: 'date', direction: 'desc' });

    // Table Pagination State
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(20);

    const ga4PageSize = useMemo(() => {
        return Math.max(itemsPerPage * 10, 1000);
    }, [itemsPerPage]);

    // Traffic Tab State
    const [trafficDimension, setTrafficDimension] = useState('sessionDefaultChannelGrouping');
    const [sourceFilter, setSourceFilter] = useState('all'); // 'all' or specific source value
    const [sourceGroups, setSourceGroups] = useState([]);
    const [showGroupModal, setShowGroupModal] = useState(false);
    const [editingGroup, setEditingGroup] = useState(null);

    // Load source groups when property changes
    useEffect(() => {
        if (selectedProperty) {
            setSourceGroups(getAllSourceGroups(selectedProperty));
        }
    }, [selectedProperty]);

    // Reload source groups (called after add/edit/delete)
    const reloadSourceGroups = useCallback(() => {
        if (selectedProperty) {
            setSourceGroups(getAllSourceGroups(selectedProperty));
        }
    }, [selectedProperty]);

    // Load content groups when property changes
    useEffect(() => {
        if (selectedProperty) {
            setContentGroups(getAllContentGroups(selectedProperty));
        }
    }, [selectedProperty]);

    // Reload content groups (called after add/edit/delete)
    const reloadContentGroups = useCallback(() => {
        if (selectedProperty) {
            setContentGroups(getAllContentGroups(selectedProperty));
        }
    }, [selectedProperty]);


    // Behavior Tab State
    const [behaviorDimension, setBehaviorDimension] = useState('deviceCategory');
    const [behaviorFilter, setBehaviorFilter] = useState('all'); // 'all' or specific value

    // Ecommerce Tab State
    const [ecommerceDimension, setEcommerceDimension] = useState('itemName');
    const [ecommerceSecondaryDimension, setEcommerceSecondaryDimension] = useState('none');
    const [ecommerceFilter, setEcommerceFilter] = useState('all');
    const [ecommerceSecondaryFilter, setEcommerceSecondaryFilter] = useState('all');

    // Content Tab State
    const [contentDimension, setContentDimension] = useState('pageTitle');
    const [contentTypeFilter, setContentTypeFilter] = useState('all');
    const [contentGroups, setContentGroups] = useState([]);
    const [showContentGroupModal, setShowContentGroupModal] = useState(false);
    const [editingContentGroup, setEditingContentGroup] = useState(null);

    const getMetricLabel = (metric) => getMetricLabelForLanguage(metric, language);

    const getTrafficColumnOrder = () => getTrafficColumnOrderForDimension(trafficDimension);

    const getTrafficColumnLabel = (col) => getTrafficColumnLabelForLanguage(col, language);

    const getBehaviorColumnOrder = () => getBehaviorColumnOrderForDimension(behaviorDimension);

    const getBehaviorColumnLabel = (col) => getBehaviorColumnLabelForLanguage(col, language);

    const getEcommerceColumnOrder = () => getEcommerceColumnOrderForDimensions(ecommerceDimension, ecommerceSecondaryDimension);

    const getEcommerceColumnLabel = (col) => getEcommerceColumnLabelForLanguage(col, language);

    const getContentColumnOrder = () => getContentColumnOrderForDimension(contentDimension);

    const getContentColumnLabel = (col) => getContentColumnLabelForLanguage(col, language);

    // Cache ref for analytics data
    const cacheRef = useRef(new Map());

    // Generate cache key
    const getCacheKey = useCallback((propertyId, tab, start, end) => {
        return `${propertyId}|${tab}|${start}|${end}`;
    }, []);

    // Check if cache is valid
    const getCachedData = useCallback((key) => {
        const cached = cacheRef.current.get(key);
        if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
            return cached.data;
        }
        return null;
    }, []);

    // Set cache data
    const setCachedData = useCallback((key, data) => {
        cacheRef.current.set(key, { data, timestamp: Date.now() });
    }, []);

    // Fetch GA4 properties
    const fetchProperties = async () => {
        setPropertiesLoading(true);
        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/api/ga4/properties`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('google_token')}` }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch properties');
            }

            const data = await response.json();
            setProperties(data.properties || []);

            // Auto-select first property if available
            if (data.properties && data.properties.length > 0 && !selectedProperty) {
                setSelectedProperty(data.properties[0].property_id);
            }
        } catch (err) {
            console.error('Error fetching GA4 properties:', err);
            setError('Failed to load properties');
        } finally {
            setPropertiesLoading(false);
        }
    };

    // Fetch analytics data with caching
    // 同時獲取兩組數據：帶 dimension（表格）和不帶 dimension（KPI 總數去重）
    const fetchAnalytics = useCallback(async (forceRefresh = false, options = {}) => {
        const { append = false, offset = 0 } = options;
        if (!selectedProperty) return;

        if (forceRefresh) {
            setGa4Offset(0);
            setGa4HasMore(true);
        }

        // Include dimension in cache key for traffic, behavior, and ecommerce tabs
        let dimensionKey;
        if (activeTab === 'traffic') {
            dimensionKey = trafficDimension;
        } else if (activeTab === 'behavior') {
            dimensionKey = behaviorDimension;
        } else if (activeTab === 'ecommerce') {
            dimensionKey = `${ecommerceDimension}|${ecommerceSecondaryDimension}`;
        } else if (activeTab === 'content') {
            dimensionKey = contentDimension;
        } else {
            dimensionKey = 'default';
        }

        const baseKey = getCacheKey(selectedProperty, activeTab + '|' + dimensionKey, dateRange.startDate, dateRange.endDate);
        const pageKey = `${baseKey}|page|${offset}|${ga4PageSize}`;
        const combinedKey = `${baseKey}|combined`;
        const summaryCacheKey = `${baseKey}|summary`;

        // Check cache first (unless force refresh)
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
                        return mergedData;
                    });
                    if (cachedPage.total_row_count) {
                        setGa4HasMore((analyticsData?.rows?.length || 0) + cachedPage.rows.length < cachedPage.total_row_count);
                    }
                    return;
                }
            }
        }

        if (append) {
            setGa4LoadingMore(true);
        } else {
            setLoading(true);
        }
        setError(null);

        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const tabConfig = TABS.find(tab => tab.key === activeTab);

            // For traffic/behavior/ecommerce/content tabs, use dynamic dimension; otherwise use tab config
            let activeDimension;
            if (activeTab === 'traffic') {
                activeDimension = trafficDimension;
            } else if (activeTab === 'behavior') {
                activeDimension = behaviorDimension;
            } else if (activeTab === 'ecommerce') {
                // Ecommerce supports multiple dimensions
                activeDimension = ecommerceSecondaryDimension !== 'none'
                    ? `${ecommerceDimension},${ecommerceSecondaryDimension}`
                    : ecommerceDimension;
            } else if (activeTab === 'content') {
                activeDimension = contentDimension;
            } else {
                activeDimension = tabConfig.dimensions[0];
            }

            // 1. 帶 dimension 的請求（用於表格顯示每日數據）
            const params = new URLSearchParams({
                property_id: selectedProperty,
                start_date: dateRange.startDate,
                end_date: dateRange.endDate,
                metrics: tabConfig.metrics.join(','),
                dimensions: activeDimension,
                limit: String(ga4PageSize),
                offset: String(offset)
            });

            // 2. 不帶 dimension 的請求（用於 KPI 卡片顯示去重總數）
            const summaryParams = new URLSearchParams({
                property_id: selectedProperty,
                start_date: dateRange.startDate,
                end_date: dateRange.endDate,
                metrics: tabConfig.metrics.join(','),
                dimensions: '' // 空字串表示不帶 dimension
            });

            // 並行請求兩組數據
            const [response, summaryResponse] = await Promise.all([
                fetch(`${apiUrl}/api/ga4/report?${params}`, {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('google_token')}` }
                }),
                fetch(`${apiUrl}/api/ga4/report?${summaryParams}`, {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('google_token')}` }
                })
            ]);

            if (!response.ok) {
                throw new Error('Failed to fetch analytics data');
            }

            const data = await response.json();
            const summary = summaryResponse.ok ? await summaryResponse.json() : null;

            const totalRowCount = data.total_row_count ?? data.row_count ?? (data.rows ? data.rows.length : 0);
            const incomingRows = data.rows || [];
            const mergedRows = append && analyticsData?.rows
                ? [...analyticsData.rows, ...incomingRows]
                : incomingRows;

            const combinedData = {
                ...data,
                rows: mergedRows,
                row_count: mergedRows.length,
                total_row_count: totalRowCount,
                limit: ga4PageSize,
                offset
            };

            // Store in cache
            setCachedData(pageKey, data);
            setCachedData(combinedKey, combinedData);
            if (summary) {
                setCachedData(summaryCacheKey, summary);
            }
            console.log('💾 Cached data for:', combinedKey);

            setAnalyticsData(combinedData);
            setSummaryData(summary);
            setCurrentPage(1);

            if (totalRowCount) {
                setGa4HasMore(mergedRows.length < totalRowCount);
            } else if (ga4PageSize && incomingRows.length < ga4PageSize) {
                setGa4HasMore(false);
            }

            if (append) {
                setGa4Offset(offset);
            } else {
                setGa4Offset(0);
            }
        } catch (err) {
            console.error('Error fetching GA4 analytics:', err);
            setError('Failed to load analytics data');
        } finally {
            if (append) {
                setGa4LoadingMore(false);
            } else {
                setLoading(false);
            }
        }
    }, [selectedProperty, activeTab, dateRange.startDate, dateRange.endDate, trafficDimension, behaviorDimension, ecommerceDimension, ecommerceSecondaryDimension, contentDimension, ga4PageSize, analyticsData, getCacheKey, getCachedData, setCachedData]);

    const loadMoreGa4Data = () => {
        if (ga4LoadingMore || !ga4HasMore) return;
        const nextOffset = ga4Offset + ga4PageSize;
        fetchAnalytics(false, { append: true, offset: nextOffset });
    };

    // Fetch comparison data (also with summary for KPI)
    const fetchCompareData = useCallback(async (compareDateRange) => {
        if (!selectedProperty || !compareDateRange) {
            setCompareData(null);
            setCompareSummaryData(null);
            return;
        }

        // Include dimension in cache key for traffic, behavior, ecommerce, and content tabs
        let dimensionKey;
        if (activeTab === 'traffic') {
            dimensionKey = trafficDimension;
        } else if (activeTab === 'behavior') {
            dimensionKey = behaviorDimension;
        } else if (activeTab === 'ecommerce') {
            dimensionKey = `${ecommerceDimension}|${ecommerceSecondaryDimension}`;
        } else if (activeTab === 'content') {
            dimensionKey = contentDimension;
        } else {
            dimensionKey = 'default';
        }
        const cacheKey = getCacheKey(selectedProperty, activeTab + '|compare|' + dimensionKey, compareDateRange.startDate, compareDateRange.endDate);
        const summaryCacheKey = `${cacheKey}|summary`;

        // Check cache first
        const cachedData = getCachedData(cacheKey);
        const cachedSummary = getCachedData(summaryCacheKey);
        if (cachedData && cachedSummary) {
            console.log('📦 Using cached compare data for:', cacheKey);
            setCompareData(cachedData);
            setCompareSummaryData(cachedSummary);
            return;
        }

        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const tabConfig = TABS.find(tab => tab.key === activeTab);

            // For traffic/behavior/ecommerce/content tabs, use dynamic dimension; otherwise use tab config
            let activeDimension;
            if (activeTab === 'traffic') {
                activeDimension = trafficDimension;
            } else if (activeTab === 'behavior') {
                activeDimension = behaviorDimension;
            } else if (activeTab === 'ecommerce') {
                // Ecommerce supports multiple dimensions
                activeDimension = ecommerceSecondaryDimension !== 'none'
                    ? `${ecommerceDimension},${ecommerceSecondaryDimension}`
                    : ecommerceDimension;
            } else if (activeTab === 'content') {
                activeDimension = contentDimension;
            } else {
                activeDimension = tabConfig.dimensions[0];
            }

            const params = new URLSearchParams({
                property_id: selectedProperty,
                start_date: compareDateRange.startDate,
                end_date: compareDateRange.endDate,
                metrics: tabConfig.metrics.join(','),
                dimensions: activeDimension
            });


            // 比較期間也需要不帶 dimension 的總數
            const summaryParams = new URLSearchParams({
                property_id: selectedProperty,
                start_date: compareDateRange.startDate,
                end_date: compareDateRange.endDate,
                metrics: tabConfig.metrics.join(','),
                dimensions: ''
            });

            const [response, summaryResponse] = await Promise.all([
                fetch(`${apiUrl}/api/ga4/report?${params}`, {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('google_token')}` }
                }),
                fetch(`${apiUrl}/api/ga4/report?${summaryParams}`, {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('google_token')}` }
                })
            ]);

            if (response.ok) {
                const data = await response.json();
                const summary = summaryResponse.ok ? await summaryResponse.json() : null;
                setCachedData(cacheKey, data);
                if (summary) {
                    setCachedData(summaryCacheKey, summary);
                }
                setCompareData(data);
                setCompareSummaryData(summary);
            }
        } catch (err) {
            console.error('Error fetching compare data:', err);
        }
    }, [selectedProperty, activeTab, trafficDimension, behaviorDimension, ecommerceDimension, ecommerceSecondaryDimension, contentDimension, getCacheKey, getCachedData, setCachedData]);

    // Handle date preset change (aligned with Analytics page logic)
    const handleDatePresetChange = (preset) => {
        const presetConfig = DATE_PRESETS.find(p => p.key === preset);
        const today = new Date();
        let startDate, endDate;

        // Handle special presets that need custom date calculation
        if (presetConfig.isToday) {
            startDate = endDate = new Date(today);
        } else if (presetConfig.isYesterday) {
            startDate = endDate = new Date(today);
            startDate.setDate(startDate.getDate() - 1);
        } else if (presetConfig.isThisWeek) {
            // 本週：從本週一到今天
            endDate = new Date(today);
            startDate = new Date(today);
            const dayOfWeek = startDate.getDay();
            const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
            startDate.setDate(startDate.getDate() - daysToMonday);
        } else if (presetConfig.isLastWeek) {
            // 上週：從上週一到上週日
            const lastWeekEnd = new Date(today);
            const dayOfWeek = lastWeekEnd.getDay();
            const daysToLastSunday = dayOfWeek === 0 ? 7 : dayOfWeek;
            lastWeekEnd.setDate(lastWeekEnd.getDate() - daysToLastSunday);
            endDate = new Date(lastWeekEnd);
            startDate = new Date(lastWeekEnd);
            startDate.setDate(startDate.getDate() - 6);
        } else if (presetConfig.isThisMonth) {
            // 本月：從本月1日到本月最後一天
            endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);
            startDate = new Date(today.getFullYear(), today.getMonth(), 1);
        } else if (presetConfig.isLastMonth) {
            // 上月：從上月1日到上月最後一天
            startDate = new Date(today.getFullYear(), today.getMonth() - 1, 1);
            endDate = new Date(today.getFullYear(), today.getMonth(), 0);
        } else if (presetConfig.days !== null && presetConfig.days > 0) {
            // 「過去 N 天」不包含今天（業界標準）
            // endDate = 昨天，startDate = 昨天往前推 (N-1) 天
            const yesterday = new Date(today);
            yesterday.setDate(yesterday.getDate() - 1);
            endDate = new Date(yesterday);
            startDate = new Date(yesterday);
            startDate.setDate(startDate.getDate() - (presetConfig.days - 1));
        } else if (preset === 'custom') {
            // Custom preset - toggle date picker
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


    // Toggle custom date picker visibility
    const toggleCustomDatePicker = () => {
        if (dateRange.preset === 'custom') {
            setShowCustomDatePicker(prev => !prev);
        } else {
            handleDatePresetChange('custom');
        }
    };

    // Calculate comparison date range
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
        } else if (compareMode === 'previous_year') {
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

    // Handle custom date selection
    const handleCustomDateChange = (type, value) => {
        setDateRange(prev => ({
            ...prev,
            [type]: value,
            preset: 'custom'
        }));
    };

    // Apply custom date range
    const applyCustomDateRange = () => {
        setShowCustomDatePicker(false);
        // The fetchAnalytics will be triggered by useEffect
    };

    // Effects
    useEffect(() => {
        fetchProperties();
    }, []);

    useEffect(() => {
        setGa4Offset(0);
        setGa4HasMore(true);
        setGa4LoadingMore(false);
        setCurrentPage(1);
    }, [selectedProperty, activeTab, dateRange.startDate, dateRange.endDate, trafficDimension, behaviorDimension, ecommerceDimension, ecommerceSecondaryDimension, contentDimension]);

    useEffect(() => {
        if (selectedProperty && !showCustomDatePicker) {
            fetchAnalytics();
        }
    }, [selectedProperty, activeTab, dateRange, showCustomDatePicker, fetchAnalytics]);

    // Fetch compare data when compare mode changes
    useEffect(() => {
        if (compareMode !== 'none' && selectedProperty && analyticsData) {
            const compareDateRange = getCompareDateRange();
            if (compareDateRange) {
                fetchCompareData(compareDateRange);
            }
        } else {
            setCompareData(null);
            setCompareSummaryData(null);
        }
    }, [compareMode, getCompareDateRange, fetchCompareData, selectedProperty, analyticsData, trafficDimension, behaviorDimension, ecommerceDimension, ecommerceSecondaryDimension]);

    // Reset source filter when dimension changes (for traffic tab)
    useEffect(() => {
        setSourceFilter('all');
    }, [trafficDimension]);

    // Reset behavior filter when dimension changes (for behavior tab)
    useEffect(() => {
        setBehaviorFilter('all');
    }, [behaviorDimension]);

    // Reset ecommerce filters when dimensions change
    useEffect(() => {
        setEcommerceFilter('all');
    }, [ecommerceDimension]);

    useEffect(() => {
        setEcommerceSecondaryFilter('all');
    }, [ecommerceSecondaryDimension]);

    // Reset pagination when tab, filters, or data changes
    useEffect(() => {
        setCurrentPage(1);
    }, [activeTab, trafficDimension, sourceFilter, behaviorDimension, behaviorFilter, ecommerceDimension, ecommerceSecondaryDimension, ecommerceFilter, ecommerceSecondaryFilter, contentDimension, contentTypeFilter, analyticsData]);

    // Reset content filter when dimension changes
    useEffect(() => {
        setContentTypeFilter('all');
    }, [contentDimension]);


    // Use tab-specific KPIs
    const kpiData = useMemo(() => {
        const shared = { analyticsData, compareData, compareMode, language };
        if (activeTab === 'traffic') {
            return getTrafficKPIData({ ...shared, sourceFilter, sourceGroups, trafficDimension });
        } else if (activeTab === 'behavior') {
            return getBehaviorKPIData({ ...shared, behaviorFilter, behaviorDimension });
        } else if (activeTab === 'ecommerce') {
            return getEcommerceKPIData({ ...shared, ecommerceFilter, ecommerceDimension, ecommerceSecondaryFilter, ecommerceSecondaryDimension, sourceGroups });
        } else if (activeTab === 'content') {
            return getContentKPIData({ ...shared, contentTypeFilter, contentGroups, contentDimension });
        }
        return getOverviewKPIData({ ...shared, summaryData, compareSummaryData });
    }, [analyticsData, summaryData, compareData, compareSummaryData, compareMode, activeTab, sourceFilter, sourceGroups, trafficDimension, behaviorFilter, behaviorDimension, ecommerceFilter, ecommerceDimension, ecommerceSecondaryFilter, ecommerceSecondaryDimension, contentDimension, contentTypeFilter, contentGroups, language]);


    return (
        <div style={{ width: '100%', padding: isMobile ? '16px' : '24px' }}>
            {/* Main Settings Panel - Glass Style */}
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

                {/* Row 1: Account + Date Range + Compare Mode */}
                <div style={{
                    display: 'flex',
                    flexDirection: isMobile ? 'column' : 'row',
                    gap: '20px',
                    flexWrap: 'wrap'
                }}>
                    {/* Account Selector */}
                    <div style={{ flex: 1, minWidth: isMobile ? '100%' : '200px' }}>
                        <label style={{
                            display: 'block',
                            marginBottom: '8px',
                            fontWeight: 600,
                            color: 'var(--text-secondary)',
                            fontSize: '0.85rem'
                        }}>
                            {t('選擇帳號', 'Select Account')}
                        </label>
                        {propertiesLoading && (
                            <div style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '8px',
                                marginBottom: '8px',
                                color: 'var(--text-secondary)',
                                fontSize: '12px'
                            }}>
                                <div style={{
                                    width: '14px',
                                    height: '14px',
                                    border: '2px solid rgba(52, 168, 83, 0.2)',
                                    borderTop: '2px solid #34a853',
                                    borderRadius: '50%',
                                    animation: 'spin 1s linear infinite'
                                }} />
                                {t('載入 GA4 帳號列表中...', 'Loading GA4 properties...')}
                                <style>{`
                                    @keyframes spin {
                                        0% { transform: rotate(0deg); }
                                        100% { transform: rotate(360deg); }
                                    }
                                `}</style>
                            </div>
                        )}
                        <select
                            value={selectedProperty}
                            onChange={(e) => setSelectedProperty(e.target.value)}
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
                            <option value="" style={{ color: 'black' }}>{t('選擇 GA4 帳號...', 'Select GA4 Account...')}</option>
                            {properties.map(prop => (
                                <option key={prop.property_id} value={prop.property_id} style={{ color: 'black' }}>
                                    {prop.display_name || prop.property_id}
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
                            value={dateRange.preset}
                            onChange={(e) => handleDatePresetChange(e.target.value)}
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
                    <div style={{ flex: 1, minWidth: isMobile ? '100%' : '180px' }}>
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

                    {/* Refresh Button */}
                    <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                        <button
                            onClick={() => fetchAnalytics(true)}
                            disabled={loading || !selectedProperty}
                            style={{
                                padding: '10px 20px',
                                border: '1px solid var(--glass-border)',
                                borderRadius: '8px',
                                background: 'rgba(255, 255, 255, 0.05)',
                                color: 'var(--text-primary)',
                                fontSize: '14px',
                                cursor: loading || !selectedProperty ? 'not-allowed' : 'pointer',
                                opacity: loading || !selectedProperty ? 0.5 : 1,
                                display: 'flex',
                                alignItems: 'center',
                                gap: '6px',
                                transition: 'all 0.2s'
                            }}
                            title={t('強制重新整理（忽略快取）', 'Force refresh (ignore cache)')}
                        >
                            🔄 {t('重新整理', 'Refresh')}
                        </button>
                    </div>
                </div>

                {/* Custom Date Picker - Inline when selected */}
                {dateRange.preset === 'custom' && (
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
                                    value={dateRange.startDate}
                                    max={dateRange.endDate}
                                    onChange={(e) => handleCustomDateChange('startDate', e.target.value)}
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
                                    value={dateRange.endDate}
                                    min={dateRange.startDate}
                                    max={formatLocalDate(new Date())}
                                    onChange={(e) => handleCustomDateChange('endDate', e.target.value)}
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

                        {/* Quick Selection + Range Display */}
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
                                { label: t('今天', 'Today'), type: 'today' },
                                { label: t('昨天', 'Yesterday'), type: 'yesterday' },
                                { label: t('本週', 'This Week'), type: 'thisWeek' },
                                { label: t('上週', 'Last Week'), type: 'lastWeek' },
                                { label: t('本月', 'This Month'), type: 'thisMonth' },
                                { label: t('上月', 'Last Month'), type: 'lastMonth' }
                            ].map(quick => (
                                <button
                                    key={quick.label}
                                    onClick={() => {
                                        const today = new Date();
                                        let start, end;

                                        switch (quick.type) {
                                            case 'today':
                                                start = end = new Date(today);
                                                break;
                                            case 'yesterday':
                                                start = end = new Date(today);
                                                start.setDate(start.getDate() - 1);
                                                break;
                                            case 'thisWeek':
                                                // 本週：從本週一到今天
                                                end = new Date(today);
                                                start = new Date(today);
                                                const dayOfWeek = start.getDay();
                                                const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
                                                start.setDate(start.getDate() - daysToMonday);
                                                break;
                                            case 'lastWeek':
                                                // 上週：從上週一到上週日
                                                const lastWeekEnd = new Date(today);
                                                const dow = lastWeekEnd.getDay();
                                                const daysToLastSunday = dow === 0 ? 7 : dow;
                                                lastWeekEnd.setDate(lastWeekEnd.getDate() - daysToLastSunday);
                                                end = new Date(lastWeekEnd);
                                                start = new Date(lastWeekEnd);
                                                start.setDate(start.getDate() - 6);
                                                break;
                                            case 'thisMonth':
                                                // 本月：從本月1日到本月最後一天（GA4 不接受未來日期，需封頂到今天）
                                                const monthEnd = new Date(today.getFullYear(), today.getMonth() + 1, 0);
                                                end = monthEnd > today ? new Date(today) : monthEnd;
                                                start = new Date(today.getFullYear(), today.getMonth(), 1);
                                                break;
                                            case 'lastMonth':
                                                // 上月：從上月1日到上月最後一天
                                                start = new Date(today.getFullYear(), today.getMonth() - 1, 1);
                                                end = new Date(today.getFullYear(), today.getMonth(), 0);
                                                break;
                                            default:
                                                start = end = new Date(today);
                                        }

                                        setDateRange({
                                            startDate: formatLocalDate(start),
                                            endDate: formatLocalDate(end),
                                            preset: 'custom'
                                        });
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


                            {/* Selected Range Display */}
                            <div style={{
                                marginLeft: 'auto',
                                padding: '6px 12px',
                                background: 'rgba(66, 133, 244, 0.1)',
                                borderRadius: '6px',
                                fontSize: '13px',
                                color: 'var(--text-secondary)'
                            }}>
                                📆 {dateRange.startDate} ~ {dateRange.endDate}
                                <span style={{ marginLeft: '8px', opacity: 0.8 }}>
                                    ({Math.ceil((new Date(dateRange.endDate) - new Date(dateRange.startDate)) / (1000 * 60 * 60 * 24)) + 1} {t('天', 'days')})
                                </span>
                            </div>
                        </div>
                    </div>
                )}

                {/* Date Range Info Bar - Always visible */}
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
                            {dateRange.startDate} ~ {dateRange.endDate}
                        </strong>
                        <span style={{ opacity: 0.7 }}>
                            ({Math.ceil((new Date(dateRange.endDate) - new Date(dateRange.startDate)) / (1000 * 60 * 60 * 24)) + 1} {t('天', 'days')})
                        </span>
                    </div>

                    {/* Compare Period - Only when enabled */}
                    {compareMode !== 'none' && getCompareDateRange() && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span style={{ color: 'var(--text-secondary)' }}>|</span>
                            📊 {compareMode === 'previous_period' ? t('前一時段', 'Previous Period') : t('去年同期', 'Previous Year')}:
                            <strong style={{ color: '#a78bfa' }}>
                                {getCompareDateRange().startDate} ~ {getCompareDateRange().endDate}
                            </strong>
                        </div>
                    )}
                </div>

            </div>

            {/* Content Area - Glass Panel Wrapper (aligned with GSC) */}
            <div className="glass-panel" style={{
                padding: isMobile ? '16px' : '24px',
                borderRadius: '16px',
                background: 'rgba(255, 255, 255, 0.03)',
                border: '1px solid var(--glass-border)',
                backdropFilter: 'blur(10px)'
            }}>
                {/* Tab Navigation */}
                <div style={{
                    display: 'flex',
                    borderBottom: '1px solid var(--glass-border)',
                    marginBottom: '24px',
                    overflowX: 'auto'
                }}>

                    {TABS.map(tab => (
                        <button
                            key={tab.key}
                            onClick={() => setActiveTab(tab.key)}
                            style={{
                                padding: '12px 16px',
                                border: 'none',
                                background: activeTab === tab.key ? 'var(--accent-primary)' : 'transparent',
                                color: activeTab === tab.key ? 'white' : 'var(--text-secondary)',
                                borderRadius: '8px 8px 0 0',
                                fontSize: '14px',
                                fontWeight: '500',
                                cursor: 'pointer',
                                whiteSpace: 'nowrap',
                                marginRight: '4px'
                            }}
                        >
                            {language === 'zh' ? tab.label_zh : tab.label_en}
                        </button>
                    ))}
                </div>

                {/* Traffic Tab Controls */}
                {activeTab === 'traffic' && (
                    <div style={{
                        display: 'flex',
                        flexDirection: isMobile ? 'column' : 'row',
                        gap: '16px',
                        marginBottom: '20px',
                        padding: '16px',
                        background: 'rgba(255, 255, 255, 0.02)',
                        borderRadius: '12px',
                        border: '1px solid var(--glass-border)'
                    }}>
                        {/* Dimension Selector */}
                        <div style={{ flex: 1 }}>
                            <label style={{
                                display: 'block',
                                marginBottom: '8px',
                                fontSize: '13px',
                                fontWeight: 600,
                                color: 'var(--text-secondary)'
                            }}>
                                📊 {t('分析維度', 'Analysis Dimension')}
                            </label>
                            <select
                                value={trafficDimension}
                                onChange={(e) => setTrafficDimension(e.target.value)}
                                style={{
                                    width: '100%',
                                    padding: '10px 12px',
                                    border: '1px solid var(--glass-border)',
                                    borderRadius: '8px',
                                    background: '#ffffff',
                                    color: '#000000',
                                    fontSize: '14px'
                                }}
                            >
                                {TRAFFIC_DIMENSIONS.map(dim => (
                                    <option key={dim.key} value={dim.key} style={{ color: 'black' }}>
                                        {language === 'zh' ? dim.label_zh : dim.label_en}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* Dynamic Source Filter */}
                        <div style={{ flex: 1 }}>
                            <label style={{
                                display: 'flex',
                                marginBottom: '8px',
                                fontSize: '13px',
                                fontWeight: 600,
                                color: 'var(--text-secondary)',
                                justifyContent: 'space-between',
                                alignItems: 'center'
                            }}>
                                <span>🎯 {t('來源篩選', 'Source Filter')}</span>
                                <button
                                    onClick={() => {
                                        setEditingGroup(null);
                                        setShowGroupModal(true);
                                    }}
                                    style={{
                                        background: 'rgba(99, 102, 241, 0.2)',
                                        border: '1px solid rgba(99, 102, 241, 0.4)',
                                        borderRadius: '4px',
                                        color: '#818cf8',
                                        fontSize: '11px',
                                        padding: '2px 8px',
                                        cursor: 'pointer'
                                    }}
                                >
                                    + {t('新增分組', 'Add Group')}
                                </button>
                            </label>
                            <div style={{ display: 'flex', gap: '8px' }}>
                                <select
                                    value={sourceFilter}
                                    onChange={(e) => setSourceFilter(e.target.value)}
                                    style={{
                                        flex: 1,
                                        padding: '10px 12px',
                                        border: '1px solid var(--glass-border)',
                                        borderRadius: '8px',
                                        background: 'rgba(255, 255, 255, 0.05)',
                                        color: 'var(--text-primary)',
                                        fontSize: '14px'
                                    }}
                                >
                                    <option value="all" style={{ color: 'black' }}>
                                        {t('全部來源', 'All Sources')}
                                    </option>

                                    {/* Source Groups - only show groups that have matching data */}
                                    {analyticsData && analyticsData.rows && sourceGroups.filter(group => {
                                        // Only show group if there are matching sources in data
                                        const sources = analyticsData.rows.map(row =>
                                            (row[trafficDimension] || row.dimension || '').toLowerCase()
                                        );
                                        return group.patterns.some(pattern =>
                                            sources.some(source => source.includes(pattern.toLowerCase()))
                                        );
                                    }).map(group => (
                                        <option key={group.key} value={group.key} style={{ color: 'black', fontWeight: 'bold' }}>
                                            {language === 'zh' ? group.label_zh : group.label_en}
                                        </option>
                                    ))}

                                    {/* Separator */}
                                    <option disabled style={{ color: '#666' }}>──────────────</option>

                                    {/* Individual sources */}
                                    {analyticsData && analyticsData.rows &&
                                        [...new Set(analyticsData.rows.map(row => {
                                            const dimKey = trafficDimension.replace('session', '').replace('Default', '').toLowerCase();
                                            return row[trafficDimension] || row[dimKey] || row.dimension;
                                        }).filter(Boolean))].sort().map(source => (
                                            <option key={source} value={source} style={{ color: 'black' }}>
                                                {source}
                                            </option>
                                        ))
                                    }
                                </select>

                                {/* Edit button - only show when a group is selected */}
                                {(sourceFilter.startsWith('group_') || sourceFilter.startsWith('custom_')) && sourceFilter !== 'all' && (
                                    <button
                                        onClick={() => {
                                            const group = sourceGroups.find(g => g.key === sourceFilter);
                                            if (group) {
                                                setEditingGroup(group);
                                                setShowGroupModal(true);
                                            }
                                        }}
                                        style={{
                                            padding: '10px 12px',
                                            border: '1px solid var(--glass-border)',
                                            borderRadius: '8px',
                                            background: 'rgba(255, 255, 255, 0.05)',
                                            color: 'var(--text-secondary)',
                                            cursor: 'pointer',
                                            fontSize: '14px'
                                        }}
                                        title={t('編輯分組', 'Edit Group')}
                                    >
                                        ✏️
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* Behavior Tab Controls */}
                {activeTab === 'behavior' && (
                    <div style={{
                        display: 'flex',
                        flexDirection: isMobile ? 'column' : 'row',
                        gap: '16px',
                        marginBottom: '20px',
                        padding: '16px',
                        background: 'rgba(255, 255, 255, 0.02)',
                        borderRadius: '12px',
                        border: '1px solid var(--glass-border)'
                    }}>
                        {/* Dimension Selector */}
                        <div style={{ flex: 1 }}>
                            <label style={{
                                display: 'block',
                                marginBottom: '8px',
                                fontSize: '13px',
                                fontWeight: 600,
                                color: 'var(--text-secondary)'
                            }}>
                                📊 {t('分析維度', 'Analysis Dimension')}
                            </label>
                            <select
                                value={behaviorDimension}
                                onChange={(e) => setBehaviorDimension(e.target.value)}
                                style={{
                                    width: '100%',
                                    padding: '10px 12px',
                                    border: '1px solid var(--glass-border)',
                                    borderRadius: '8px',
                                    background: '#ffffff',
                                    color: '#000000',
                                    fontSize: '14px'
                                }}
                            >
                                {BEHAVIOR_DIMENSIONS.map(dim => (
                                    <option key={dim.key} value={dim.key} style={{ color: 'black' }}>
                                        {language === 'zh' ? dim.label_zh : dim.label_en}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* Dynamic Filter */}
                        <div style={{ flex: 1 }}>
                            <label style={{
                                display: 'block',
                                marginBottom: '8px',
                                fontSize: '13px',
                                fontWeight: 600,
                                color: 'var(--text-secondary)'
                            }}>
                                🎯 {BEHAVIOR_FILTER_LABELS[behaviorDimension]
                                    ? (language === 'zh' ? BEHAVIOR_FILTER_LABELS[behaviorDimension].zh : BEHAVIOR_FILTER_LABELS[behaviorDimension].en)
                                    : t('篩選', 'Filter')}
                            </label>
                            <select
                                value={behaviorFilter}
                                onChange={(e) => setBehaviorFilter(e.target.value)}
                                style={{
                                    width: '100%',
                                    padding: '10px 12px',
                                    border: '1px solid var(--glass-border)',
                                    borderRadius: '8px',
                                    background: '#ffffff',
                                    color: '#000000',
                                    fontSize: '14px'
                                }}
                            >
                                <option value="all" style={{ color: 'black' }}>
                                    {t('全部', 'All')}
                                </option>

                                {/* Individual values from data */}
                                {analyticsData && analyticsData.rows &&
                                    [...new Set(analyticsData.rows.map(row => {
                                        return row[behaviorDimension] || row.dimension;
                                    }).filter(Boolean))].sort().map(value => (
                                        <option key={value} value={value} style={{ color: 'black' }}>
                                            {value}
                                        </option>
                                    ))
                                }
                            </select>
                        </div>
                    </div>
                )}

                {/* Ecommerce Tab Controls */}
                {activeTab === 'ecommerce' && (
                    <div style={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '16px',
                        marginBottom: '20px',
                        padding: '16px',
                        background: 'rgba(255, 255, 255, 0.02)',
                        borderRadius: '12px',
                        border: '1px solid var(--glass-border)'
                    }}>
                        {/* Row 1: Dimension Selectors */}
                        <div style={{
                            display: 'flex',
                            flexDirection: isMobile ? 'column' : 'row',
                            gap: '16px'
                        }}>
                            {/* Product Dimension Selector */}
                            <div style={{ flex: 1 }}>
                                <label style={{
                                    display: 'block',
                                    marginBottom: '8px',
                                    fontSize: '13px',
                                    fontWeight: 600,
                                    color: 'var(--text-secondary)'
                                }}>
                                    📦 {t('商品維度', 'Product Dimension')}
                                </label>
                                <select
                                    value={ecommerceDimension}
                                    onChange={(e) => setEcommerceDimension(e.target.value)}
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
                                    {ECOMMERCE_DIMENSIONS.map(dim => (
                                        <option key={dim.key} value={dim.key} style={{ color: 'black' }}>
                                            {language === 'zh' ? dim.label_zh : dim.label_en}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            {/* Traffic Dimension Selector (Secondary) */}
                            <div style={{ flex: 1 }}>
                                <label style={{
                                    display: 'block',
                                    marginBottom: '8px',
                                    fontSize: '13px',
                                    fontWeight: 600,
                                    color: 'var(--text-secondary)'
                                }}>
                                    🌐 {t('流量維度（選填）', 'Traffic Dimension (Optional)')}
                                </label>
                                <select
                                    value={ecommerceSecondaryDimension}
                                    onChange={(e) => setEcommerceSecondaryDimension(e.target.value)}
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
                                    {TRAFFIC_SECONDARY_DIMENSIONS.map(dim => (
                                        <option key={dim.key} value={dim.key} style={{ color: 'black' }}>
                                            {language === 'zh' ? dim.label_zh : dim.label_en}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        {/* Row 2: Filters */}
                        <div style={{
                            display: 'flex',
                            flexDirection: isMobile ? 'column' : 'row',
                            gap: '16px'
                        }}>
                            {/* Product Filter */}
                            <div style={{ flex: 1 }}>
                                <label style={{
                                    display: 'block',
                                    marginBottom: '8px',
                                    fontSize: '13px',
                                    fontWeight: 600,
                                    color: 'var(--text-secondary)'
                                }}>
                                    🎯 {t('商品篩選', 'Product Filter')}
                                </label>
                                <select
                                    value={ecommerceFilter}
                                    onChange={(e) => setEcommerceFilter(e.target.value)}
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
                                    <option value="all" style={{ color: 'black' }}>
                                        {t('全部商品', 'All Products')}
                                    </option>
                                    {analyticsData && analyticsData.rows &&
                                        [...new Set(analyticsData.rows.map(row =>
                                            row[ecommerceDimension]
                                        ).filter(Boolean))].sort().map(value => (
                                            <option key={value} value={value} style={{ color: 'black' }}>
                                                {value.length > 40 ? value.substring(0, 40) + '...' : value}
                                            </option>
                                        ))
                                    }
                                </select>
                            </div>

                            {/* Secondary Traffic Filter - only show when traffic dimension is selected */}
                            {ecommerceSecondaryDimension !== 'none' && (
                                <div style={{ flex: 1 }}>
                                    <label style={{
                                        display: 'flex',
                                        marginBottom: '8px',
                                        fontSize: '13px',
                                        fontWeight: 600,
                                        color: 'var(--text-secondary)',
                                        justifyContent: 'space-between',
                                        alignItems: 'center'
                                    }}>
                                        <span>🌐 {t('來源篩選', 'Traffic Filter')}</span>
                                        <button
                                            onClick={() => {
                                                setEditingGroup(null);
                                                setShowGroupModal(true);
                                            }}
                                            style={{
                                                background: 'rgba(99, 102, 241, 0.2)',
                                                border: '1px solid rgba(99, 102, 241, 0.4)',
                                                borderRadius: '4px',
                                                color: '#818cf8',
                                                fontSize: '11px',
                                                padding: '2px 8px',
                                                cursor: 'pointer'
                                            }}
                                        >
                                            + {t('新增分組', 'Add Group')}
                                        </button>
                                    </label>
                                    <div style={{ display: 'flex', gap: '8px' }}>
                                        <select
                                            value={ecommerceSecondaryFilter}
                                            onChange={(e) => setEcommerceSecondaryFilter(e.target.value)}
                                            style={{
                                                flex: 1,
                                                padding: '10px 12px',
                                                border: '1px solid var(--glass-border)',
                                                borderRadius: '8px',
                                                background: 'rgba(255, 255, 255, 0.05)',
                                                color: 'var(--text-primary)',
                                                fontSize: '14px'
                                            }}
                                        >
                                            <option value="all" style={{ color: 'black' }}>
                                                {t('全部來源', 'All Sources')}
                                            </option>

                                            {/* Source Groups - only show groups that have matching data */}
                                            {analyticsData && analyticsData.rows && sourceGroups.filter(group => {
                                                const sources = analyticsData.rows.map(row =>
                                                    (row[ecommerceSecondaryDimension] || '').toLowerCase()
                                                );
                                                return group.patterns.some(pattern =>
                                                    sources.some(source => source.includes(pattern.toLowerCase()))
                                                );
                                            }).map(group => (
                                                <option key={group.key} value={group.key} style={{ color: 'black', fontWeight: 'bold' }}>
                                                    {language === 'zh' ? group.label_zh : group.label_en}
                                                </option>
                                            ))}

                                            {/* Separator */}
                                            <option disabled style={{ color: '#666' }}>──────────────</option>

                                            {/* Individual sources */}
                                            {analyticsData && analyticsData.rows &&
                                                [...new Set(analyticsData.rows.map(row =>
                                                    row[ecommerceSecondaryDimension]
                                                ).filter(Boolean))].sort().map(value => (
                                                    <option key={value} value={value} style={{ color: 'black' }}>
                                                        {value}
                                                    </option>
                                                ))
                                            }
                                        </select>

                                        {/* Edit button - only show when a group is selected */}
                                        {(ecommerceSecondaryFilter.startsWith('group_') || ecommerceSecondaryFilter.startsWith('custom_')) && ecommerceSecondaryFilter !== 'all' && (
                                            <button
                                                onClick={() => {
                                                    const group = sourceGroups.find(g => g.key === ecommerceSecondaryFilter);
                                                    if (group) {
                                                        setEditingGroup(group);
                                                        setShowGroupModal(true);
                                                    }
                                                }}
                                                style={{
                                                    padding: '10px 12px',
                                                    border: '1px solid var(--glass-border)',
                                                    borderRadius: '8px',
                                                    background: 'rgba(255, 255, 255, 0.05)',
                                                    color: 'var(--text-secondary)',
                                                    cursor: 'pointer',
                                                    fontSize: '14px'
                                                }}
                                                title={t('編輯分組', 'Edit Group')}
                                            >
                                                ✏️
                                            </button>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Content Tab Controls */}
                {activeTab === 'content' && (
                    <div style={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '16px',
                        marginBottom: '20px',
                        padding: '16px',
                        background: 'rgba(255, 255, 255, 0.02)',
                        borderRadius: '12px',
                        border: '1px solid var(--glass-border)'
                    }}>
                        <div style={{
                            display: 'flex',
                            flexDirection: isMobile ? 'column' : 'row',
                            gap: '16px'
                        }}>
                            {/* Content Dimension Selector */}
                            <div style={{ flex: 1 }}>
                                <label style={{
                                    display: 'block',
                                    marginBottom: '8px',
                                    fontSize: '13px',
                                    fontWeight: 600,
                                    color: 'var(--text-secondary)'
                                }}>
                                    📄 {t('內容維度', 'Content Dimension')}
                                </label>
                                <select
                                    value={contentDimension}
                                    onChange={(e) => setContentDimension(e.target.value)}
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
                                    {CONTENT_DIMENSIONS.map(dim => (
                                        <option key={dim.key} value={dim.key} style={{ color: 'black' }}>
                                            {language === 'zh' ? dim.label_zh : dim.label_en}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            {/* Content Type Filter */}
                            <div style={{ flex: 1 }}>
                                <label style={{
                                    display: 'block',
                                    marginBottom: '8px',
                                    fontSize: '13px',
                                    fontWeight: 600,
                                    color: 'var(--text-secondary)'
                                }}>
                                    🏷️ {t('內容類型', 'Content Type')}
                                </label>
                                <div style={{ display: 'flex', gap: '8px' }}>
                                    <select
                                        value={contentTypeFilter}
                                        onChange={(e) => {
                                            if (e.target.value === 'add_new') {
                                                setEditingContentGroup(null);
                                                setShowContentGroupModal(true);
                                            } else {
                                                setContentTypeFilter(e.target.value);
                                            }
                                        }}
                                        style={{
                                            flex: 1,
                                            padding: '10px 12px',
                                            border: '1px solid var(--glass-border)',
                                            borderRadius: '8px',
                                            background: 'rgba(255, 255, 255, 0.05)',
                                            color: 'var(--text-primary)',
                                            fontSize: '14px'
                                        }}
                                    >
                                        <option value="all" style={{ color: 'black' }}>
                                            {t('全部頁面', 'All Pages')}
                                        </option>

                                        {/* Default Groups */}
                                        {contentGroups.filter(g => g.isDefault).length > 0 && (
                                            <option disabled style={{ color: '#666' }}>── {t('預設分組', 'Default Groups')} ──</option>
                                        )}
                                        {contentGroups.filter(g => g.isDefault).map(group => (
                                            <option key={group.key} value={group.key} style={{ color: 'black' }}>
                                                {language === 'zh' ? group.label_zh : group.label_en}
                                            </option>
                                        ))}

                                        {/* Custom Groups */}
                                        {contentGroups.filter(g => !g.isDefault).length > 0 && (
                                            <option disabled style={{ color: '#666' }}>── {t('自訂分組', 'Custom Groups')} ──</option>
                                        )}
                                        {contentGroups.filter(g => !g.isDefault).map(group => (
                                            <option key={group.key} value={group.key} style={{ color: 'black' }}>
                                                {language === 'zh' ? group.label_zh : group.label_en}
                                            </option>
                                        ))}

                                        {/* Add new option */}
                                        <option disabled style={{ color: '#666' }}>──────────────</option>
                                        <option value="add_new" style={{ color: 'black' }}>
                                            ➕ {t('新增分組...', 'Add Group...')}
                                        </option>
                                    </select>

                                    {/* Edit button - show when a group is selected */}
                                    {contentTypeFilter !== 'all' && contentTypeFilter !== 'add_new' && (
                                        <button
                                            onClick={() => {
                                                const group = contentGroups.find(g => g.key === contentTypeFilter);
                                                if (group) {
                                                    setEditingContentGroup(group);
                                                    setShowContentGroupModal(true);
                                                }
                                            }}
                                            style={{
                                                padding: '10px 12px',
                                                border: '1px solid var(--glass-border)',
                                                borderRadius: '8px',
                                                background: 'rgba(255, 255, 255, 0.05)',
                                                color: 'var(--text-secondary)',
                                                cursor: 'pointer',
                                                fontSize: '14px'
                                            }}
                                            title={t('編輯分組', 'Edit Group')}
                                        >
                                            ✏️
                                        </button>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                )}


                {/* Loading State */}
                {loading && (
                    <div style={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        padding: '60px 20px',
                        background: 'rgba(255, 255, 255, 0.02)',
                        borderRadius: '16px',
                        border: '1px solid var(--glass-border)',
                        margin: '20px 0'
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
                            {t('正在載入 GA4 數據', 'Loading GA4 data')}
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
                )}

                {/* Error State */}
                {error && (
                    <div style={{
                        padding: '16px',
                        background: 'rgba(234, 67, 53, 0.1)',
                        color: '#ea4335',
                        borderRadius: '8px',
                        border: '1px solid rgba(234, 67, 53, 0.2)',
                        marginBottom: '24px'
                    }}>
                        ⚠️ {error}
                    </div>
                )}

                {/* KPI Cards - 3x3 Grid Layout */}
                {!loading && !error && kpiData.length > 0 && (
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: isMobile ? 'repeat(3, 1fr)' : 'repeat(3, 1fr)',
                        gap: isMobile ? '8px' : '16px',
                        marginBottom: '24px'
                    }}>
                        {kpiData.map((kpi, index) => (
                            <div
                                key={index}
                                style={{
                                    padding: isMobile ? '12px' : '20px',
                                    background: 'rgba(255, 255, 255, 0.03)',
                                    border: '1px solid var(--glass-border)',
                                    borderRadius: '12px',
                                    display: 'flex',
                                    flexDirection: isMobile ? 'column' : 'row',
                                    alignItems: isMobile ? 'center' : 'flex-start',
                                    gap: isMobile ? '8px' : '16px',
                                    textAlign: isMobile ? 'center' : 'left'
                                }}
                            >
                                <div style={{ fontSize: isMobile ? '24px' : '28px', opacity: 0.9 }}>{kpi.icon}</div>
                                <div style={{ flex: 1, width: '100%' }}>
                                    <div style={{ fontSize: isMobile ? '11px' : '13px', color: 'var(--text-secondary)', marginBottom: isMobile ? '4px' : '6px' }}>
                                        {kpi.label}
                                    </div>
                                    <div style={{ fontSize: isMobile ? '18px' : '26px', fontWeight: '700', color: 'var(--text-primary)' }}>
                                        {kpi.value}
                                    </div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '6px' }}>
                                        {kpi.change && (
                                            <span style={{
                                                fontSize: '12px',
                                                padding: '2px 8px',
                                                borderRadius: '12px',
                                                background: kpi.change.isPositive ? 'rgba(52, 168, 83, 0.15)' : 'rgba(234, 67, 53, 0.15)',
                                                color: kpi.change.isPositive ? '#34a853' : '#ea4335',
                                                fontWeight: 600
                                            }}>
                                                {kpi.change.formatted}
                                            </span>
                                        )}
                                        {compareMode !== 'none' && kpi.previousValue && (
                                            <span style={{
                                                fontSize: '11px',
                                                color: 'var(--text-secondary)',
                                                opacity: 0.7
                                            }}>
                                                {t('vs', 'vs')} {kpi.previousValue}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Data Table Placeholder */}
                {!loading && !error && analyticsData && (
                    <div style={{
                        background: 'var(--bg-secondary)',
                        border: '1px solid var(--glass-border)',
                        borderRadius: '12px',
                        padding: '20px'
                    }}>
                        <h3 style={{ margin: '0 0 16px 0', color: 'var(--text-primary)' }}>
                            {t('詳細數據', 'Detailed Data')}
                        </h3>
                        <div style={{
                            overflowX: 'auto',
                            maxHeight: '400px',
                            overflowY: 'auto'
                        }}>
                            <table style={{
                                width: '100%',
                                borderCollapse: 'collapse',
                                fontSize: '14px'
                            }}>
                                <thead>
                                    <tr style={{ borderBottom: '1px solid var(--glass-border)' }}>
                                        {(activeTab === 'traffic'
                                            ? getTrafficColumnOrder()
                                            : activeTab === 'behavior'
                                                ? getBehaviorColumnOrder()
                                                : activeTab === 'ecommerce'
                                                    ? getEcommerceColumnOrder()
                                                    : activeTab === 'content'
                                                        ? getContentColumnOrder()
                                                        : OVERVIEW_COLUMN_ORDER.filter(col =>
                                                            col === 'averageOrderValue' || col === 'purchaseConversionRate' || analyticsData.dimensions.includes(col) || analyticsData.metrics.includes(col)
                                                        )).map(col => (
                                                            <th
                                                                key={col}
                                                                onClick={() => {
                                                                    setSortConfig(prev => ({
                                                                        key: col,
                                                                        direction: prev.key === col && prev.direction === 'asc' ? 'desc' : 'asc'
                                                                    }));
                                                                }}
                                                                style={{
                                                                    padding: '12px 8px',
                                                                    textAlign: 'left',
                                                                    color: 'var(--text-secondary)',
                                                                    fontWeight: '500',
                                                                    cursor: 'pointer',
                                                                    userSelect: 'none',
                                                                    whiteSpace: 'nowrap'
                                                                }}
                                                            >
                                                                {activeTab === 'traffic'
                                                                    ? getTrafficColumnLabel(col)
                                                                    : activeTab === 'behavior'
                                                                        ? getBehaviorColumnLabel(col)
                                                                        : activeTab === 'ecommerce'
                                                                            ? getEcommerceColumnLabel(col)
                                                                            : activeTab === 'content'
                                                                                ? getContentColumnLabel(col)
                                                                                : getMetricLabel(col)}
                                                                {sortConfig.key === col && (
                                                                    <span style={{ marginLeft: '4px' }}>
                                                                        {sortConfig.direction === 'asc' ? '▲' : '▼'}
                                                                    </span>
                                                                )}
                                                            </th>
                                                        ))}
                                    </tr>
                                </thead>

                                <tbody>
                                    {[...analyticsData.rows]
                                        .map(row => {
                                            const purchases = parseFloat(row.ecommercePurchases) || 0;
                                            const revenue = parseFloat(row.purchaseRevenue) || 0;
                                            const users = parseFloat(row.totalUsers) || 0;
                                            const itemsViewed = parseFloat(row.itemsViewed) || 0;
                                            const itemsPurchased = parseFloat(row.itemsPurchased) || 0;
                                            const itemsAddedToCart = parseFloat(row.itemsAddedToCart) || 0;
                                            return {
                                                ...row,
                                                // Calculate averageOrderValue for each row
                                                averageOrderValue: purchases > 0 ? revenue / purchases : 0,
                                                // Calculate purchaseConversionRate for each row (overview tab)
                                                purchaseConversionRate: users > 0 ? (purchases / users) * 100 : 0,
                                                // Calculate conversionRate for traffic/behavior tab
                                                conversionRate: activeTab === 'ecommerce'
                                                    ? (itemsViewed > 0 ? (itemsPurchased / itemsViewed) * 100 : 0)
                                                    : (users > 0 ? (purchases / users) * 100 : 0),
                                                // Ecommerce calculated metrics
                                                addToCartRate: itemsViewed > 0 ? (itemsAddedToCart / itemsViewed) * 100 : 0,
                                                checkoutConversionRate: itemsAddedToCart > 0 ? (itemsPurchased / itemsAddedToCart) * 100 : 0
                                            };
                                        })
                                        .sort((a, b) => {
                                            const aVal = a[sortConfig.key];
                                            const bVal = b[sortConfig.key];
                                            const aNum = parseFloat(aVal);
                                            const bNum = parseFloat(bVal);

                                            // Check if both are valid numbers
                                            if (!isNaN(aNum) && !isNaN(bNum)) {
                                                return sortConfig.direction === 'asc' ? aNum - bNum : bNum - aNum;
                                            }
                                            // String comparison
                                            const aStr = String(aVal || '');
                                            const bStr = String(bVal || '');
                                            return sortConfig.direction === 'asc'
                                                ? aStr.localeCompare(bStr)
                                                : bStr.localeCompare(aStr);
                                        })
                                        .slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage)
                                        .map((row, index) => (
                                            <tr key={index} style={{
                                                borderBottom: '1px solid var(--glass-border)',
                                                background: index % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)'
                                            }}>
                                                {(activeTab === 'traffic'
                                                    ? getTrafficColumnOrder()
                                                    : activeTab === 'behavior'
                                                        ? getBehaviorColumnOrder()
                                                        : activeTab === 'ecommerce'
                                                            ? getEcommerceColumnOrder()
                                                            : activeTab === 'content'
                                                                ? getContentColumnOrder()
                                                                : OVERVIEW_COLUMN_ORDER.filter(col =>
                                                                    col === 'averageOrderValue' || col === 'purchaseConversionRate' || analyticsData.dimensions.includes(col) || analyticsData.metrics.includes(col)
                                                                )).map(col => (
                                                                    <td key={col} style={{
                                                                        padding: '12px 8px',
                                                                        color: 'var(--text-primary)'
                                                                    }}>
                                                                        {/* Dimension columns (first column) */}
                                                                        {TRAFFIC_DIMENSIONS.some(d => d.key === col) || BEHAVIOR_DIMENSIONS.some(d => d.key === col) || ECOMMERCE_DIMENSIONS.some(d => d.key === col) || TRAFFIC_SECONDARY_DIMENSIONS.some(d => d.key === col) || CONTENT_DIMENSIONS.some(d => d.key === col)
                                                                            ? (row[col] || row.dimension || '-')
                                                                            : col === 'date'
                                                                                ? row[col]
                                                                                : col === 'purchaseRevenue' || col === 'averageOrderValue' || col === 'itemRevenue'
                                                                                    ? formatNumber(parseFloat(row[col]) || 0, 'currency')
                                                                                    : col === 'purchaseConversionRate' || col === 'conversionRate' || col === 'addToCartRate' || col === 'checkoutConversionRate'
                                                                                        ? `${(parseFloat(row[col]) || 0).toFixed(2)}%`
                                                                                        : col === 'engagementRate'
                                                                                            ? `${((parseFloat(row[col]) || 0) * 100).toFixed(1)}%`
                                                                                            : col === 'bounceRate'
                                                                                                ? formatNumber(parseFloat(row[col]) || 0, 'percentage')
                                                                                                : col === 'averageSessionDuration'
                                                                                                    ? formatNumber(parseFloat(row[col]) || 0, 'duration')
                                                                                                    : formatNumber(parseFloat(row[col]) || 0, 'number')
                                                                        }
                                                                    </td>
                                                                ))}
                                            </tr>
                                        ))}
                                </tbody>

                            </table>
                        </div>

                        {/* Server-side Load More */}
                        {!loading && !error && analyticsData && ga4HasMore && (
                            <div style={{
                                display: 'flex',
                                flexDirection: isMobile ? 'column' : 'row',
                                justifyContent: 'space-between',
                                alignItems: isMobile ? 'stretch' : 'center',
                                gap: '12px',
                                padding: '16px 0',
                                borderTop: '1px solid var(--glass-border)',
                                marginTop: '8px'
                            }}>
                                <div style={{
                                    color: 'var(--text-secondary)',
                                    fontSize: '13px',
                                    textAlign: isMobile ? 'center' : 'left'
                                }}>
                                    {t(`已載入 ${analyticsData.rows.length} / ${analyticsData.total_row_count || analyticsData.rows.length} 筆`,
                                        `Loaded ${analyticsData.rows.length} / ${analyticsData.total_row_count || analyticsData.rows.length}`)}
                                </div>
                                <button
                                    onClick={loadMoreGa4Data}
                                    disabled={ga4LoadingMore}
                                    style={{
                                        padding: '8px 20px',
                                        background: 'var(--accent-primary)',
                                        border: 'none',
                                        borderRadius: '8px',
                                        color: 'white',
                                        fontSize: '13px',
                                        fontWeight: '500',
                                        cursor: ga4LoadingMore ? 'wait' : 'pointer',
                                        opacity: ga4LoadingMore ? 0.7 : 1,
                                        transition: 'all 0.2s'
                                    }}
                                >
                                    {ga4LoadingMore ? t('載入中...', 'Loading...') : `⬇️ ${t('載入更多資料', 'Load More Data')}`}
                                </button>
                            </div>
                        )}

                        {/* Pagination Controls */}
                        {analyticsData.rows.length > 0 && (() => {
                            const totalRows = analyticsData.rows.length;
                            const totalPages = Math.ceil(totalRows / itemsPerPage);
                            const startRow = (currentPage - 1) * itemsPerPage + 1;
                            const endRow = Math.min(currentPage * itemsPerPage, totalRows);

                            return (
                                <div style={{
                                    display: 'flex',
                                    flexDirection: isMobile ? 'column' : 'row',
                                    justifyContent: 'space-between',
                                    alignItems: isMobile ? 'stretch' : 'center',
                                    gap: '12px',
                                    padding: '16px 0',
                                    borderTop: '1px solid var(--glass-border)',
                                    marginTop: '8px'
                                }}>
                                    {/* Left: Page info */}
                                    <div style={{
                                        color: 'var(--text-secondary)',
                                        fontSize: '13px',
                                        textAlign: isMobile ? 'center' : 'left'
                                    }}>
                                        {t(`顯示第 ${startRow}-${endRow} 筆，共 ${totalRows} 筆`,
                                            `Showing ${startRow}-${endRow} of ${totalRows}`)}
                                    </div>

                                    {/* Center/Right: Pagination controls */}
                                    <div style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '8px',
                                        justifyContent: isMobile ? 'center' : 'flex-end',
                                        flexWrap: 'wrap'
                                    }}>
                                        {/* Items per page selector */}
                                        <select
                                            value={itemsPerPage}
                                            onChange={(e) => {
                                                setItemsPerPage(Number(e.target.value));
                                                setCurrentPage(1);
                                            }}
                                            style={{
                                                padding: '6px 10px',
                                                border: '1px solid var(--glass-border)',
                                                borderRadius: '6px',
                                                background: 'rgba(255,255,255,0.05)',
                                                color: 'var(--text-primary)',
                                                fontSize: '13px',
                                                cursor: 'pointer'
                                            }}
                                        >
                                            <option value={20} style={{ color: 'black' }}>20 / {t('頁', 'page')}</option>
                                            <option value={50} style={{ color: 'black' }}>50 / {t('頁', 'page')}</option>
                                            <option value={100} style={{ color: 'black' }}>100 / {t('頁', 'page')}</option>
                                        </select>

                                        {/* Page navigation */}
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                            {/* First page */}
                                            <button
                                                onClick={() => setCurrentPage(1)}
                                                disabled={currentPage === 1}
                                                style={{
                                                    padding: '6px 10px',
                                                    border: '1px solid var(--glass-border)',
                                                    borderRadius: '6px',
                                                    background: currentPage === 1 ? 'transparent' : 'rgba(255,255,255,0.05)',
                                                    color: currentPage === 1 ? 'var(--text-secondary)' : 'var(--text-primary)',
                                                    cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
                                                    opacity: currentPage === 1 ? 0.5 : 1,
                                                    fontSize: '13px'
                                                }}
                                            >
                                                ⏮
                                            </button>

                                            {/* Previous page */}
                                            <button
                                                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                                disabled={currentPage === 1}
                                                style={{
                                                    padding: '6px 12px',
                                                    border: '1px solid var(--glass-border)',
                                                    borderRadius: '6px',
                                                    background: currentPage === 1 ? 'transparent' : 'rgba(255,255,255,0.05)',
                                                    color: currentPage === 1 ? 'var(--text-secondary)' : 'var(--text-primary)',
                                                    cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
                                                    opacity: currentPage === 1 ? 0.5 : 1,
                                                    fontSize: '13px'
                                                }}
                                            >
                                                ◀
                                            </button>

                                            {/* Page indicator */}
                                            <span style={{
                                                padding: '6px 12px',
                                                color: 'var(--text-primary)',
                                                fontSize: '13px',
                                                fontWeight: 600
                                            }}>
                                                {currentPage} / {totalPages}
                                            </span>

                                            {/* Next page */}
                                            <button
                                                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                                                disabled={currentPage === totalPages}
                                                style={{
                                                    padding: '6px 12px',
                                                    border: '1px solid var(--glass-border)',
                                                    borderRadius: '6px',
                                                    background: currentPage === totalPages ? 'transparent' : 'rgba(255,255,255,0.05)',
                                                    color: currentPage === totalPages ? 'var(--text-secondary)' : 'var(--text-primary)',
                                                    cursor: currentPage === totalPages ? 'not-allowed' : 'pointer',
                                                    opacity: currentPage === totalPages ? 0.5 : 1,
                                                    fontSize: '13px'
                                                }}
                                            >
                                                ▶
                                            </button>

                                            {/* Last page */}
                                            <button
                                                onClick={() => setCurrentPage(totalPages)}
                                                disabled={currentPage === totalPages}
                                                style={{
                                                    padding: '6px 10px',
                                                    border: '1px solid var(--glass-border)',
                                                    borderRadius: '6px',
                                                    background: currentPage === totalPages ? 'transparent' : 'rgba(255,255,255,0.05)',
                                                    color: currentPage === totalPages ? 'var(--text-secondary)' : 'var(--text-primary)',
                                                    cursor: currentPage === totalPages ? 'not-allowed' : 'pointer',
                                                    opacity: currentPage === totalPages ? 0.5 : 1,
                                                    fontSize: '13px'
                                                }}
                                            >
                                                ⏭
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            );
                        })()}
                    </div>
                )}

                {/* No Data State */}
                {!loading && !error && (!analyticsData || !analyticsData.rows || analyticsData.rows.length === 0) && selectedProperty && (
                    <div style={{
                        textAlign: 'center',
                        padding: '40px',
                        color: 'var(--text-secondary)'
                    }}>
                        {t('此日期範圍內沒有數據', 'No data available for this date range')}
                    </div>
                )}
            </div>

            {/* Source Group Modal */}
            <SourceGroupModal
                isOpen={showGroupModal}
                onClose={() => {
                    setShowGroupModal(false);
                    setEditingGroup(null);
                }}
                onSave={reloadSourceGroups}
                propertyId={selectedProperty}
                editGroup={editingGroup}
                language={language}
            />

            {/* Content Group Modal */}
            <ContentGroupModal
                isOpen={showContentGroupModal}
                onClose={() => {
                    setShowContentGroupModal(false);
                    setEditingContentGroup(null);
                }}
                onSave={(group) => {
                    saveCustomContentGroup(selectedProperty, group);
                    reloadContentGroups();
                }}
                onDelete={(groupKey) => {
                    deleteCustomContentGroup(selectedProperty, groupKey);
                    setContentTypeFilter('all');
                    reloadContentGroups();
                }}
                group={editingContentGroup}
                language={language}
                previewData={analyticsData?.rows || []}
                dimension={contentDimension}
            />
        </div>
    );

};

export default GA4Stats;
