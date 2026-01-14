import React, { useEffect, useState, useMemo, useCallback, useRef } from 'react';

// Date Range Presets Configuration (aligned with Analytics page)
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

// Compare Mode Options
const COMPARE_OPTIONS = [
    { key: 'none', label_zh: '不比較', label_en: 'No Comparison' },
    { key: 'previous_period', label_zh: '前一時段', label_en: 'Previous Period' },
    { key: 'previous_year', label_zh: '去年同期', label_en: 'Previous Year' }
];

// Tab Configuration
const TABS = [
    { key: 'overview', label_zh: '📊 總覽', label_en: '📊 Overview', metrics: ['activeUsers', 'totalUsers', 'newUsers', 'screenPageViews', 'ecommercePurchases', 'purchaseRevenue', 'addToCarts'], dimensions: ['date'] },
    { key: 'traffic', label_zh: '🌐 流量來源', label_en: '🌐 Traffic Sources', metrics: ['sessions', 'screenPageViews'], dimensions: ['sessionDefaultChannelGrouping'] },
    { key: 'behavior', label_zh: '👥 用戶行為', label_en: '👥 User Behavior', metrics: ['bounceRate', 'averageSessionDuration'], dimensions: ['date'] },
    { key: 'content', label_zh: '📄 內容分析', label_en: '📄 Content Analysis', metrics: ['screenPageViews', 'sessions'], dimensions: ['pagePath'] }
];

// Cache TTL in milliseconds (5 minutes)
const CACHE_TTL = 5 * 60 * 1000;

const GA4Stats = ({ language, isMobile }) => {
    const t = (zh, en) => language === 'zh' ? zh : en;

    // State management
    const [properties, setProperties] = useState([]);
    const [selectedProperty, setSelectedProperty] = useState('');
    const [analyticsData, setAnalyticsData] = useState(null);
    const [summaryData, setSummaryData] = useState(null); // 新增：用於 KPI 卡片的去重總數
    const [compareData, setCompareData] = useState(null);
    const [compareSummaryData, setCompareSummaryData] = useState(null); // 新增：比較期間的去重總數
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('overview');
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
            startDate: startDate.toISOString().split('T')[0],
            endDate: yesterday.toISOString().split('T')[0],
            preset: 'last_28d'
        };
    });
    const [sortConfig, setSortConfig] = useState({ key: 'date', direction: 'desc' });

    // Define column order for overview table (including calculated fields)
    const OVERVIEW_COLUMN_ORDER = ['date', 'activeUsers', 'totalUsers', 'newUsers', 'screenPageViews', 'ecommercePurchases', 'purchaseRevenue', 'addToCarts', 'averageOrderValue', 'purchaseConversionRate'];

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
        }
    };

    // Fetch analytics data with caching
    // 同時獲取兩組數據：帶 dimension（表格）和不帶 dimension（KPI 總數去重）
    const fetchAnalytics = useCallback(async (forceRefresh = false) => {
        if (!selectedProperty) return;

        const cacheKey = getCacheKey(selectedProperty, activeTab, dateRange.startDate, dateRange.endDate);
        const summaryCacheKey = `${cacheKey}|summary`;

        // Check cache first (unless force refresh)
        if (!forceRefresh) {
            const cachedData = getCachedData(cacheKey);
            const cachedSummary = getCachedData(summaryCacheKey);
            if (cachedData && cachedSummary) {
                console.log('📦 Using cached data for:', cacheKey);
                setAnalyticsData(cachedData);
                setSummaryData(cachedSummary);
                return;
            }
        }

        setLoading(true);
        setError(null);

        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const tabConfig = TABS.find(tab => tab.key === activeTab);

            // 1. 帶 dimension 的請求（用於表格顯示每日數據）
            const params = new URLSearchParams({
                property_id: selectedProperty,
                start_date: dateRange.startDate,
                end_date: dateRange.endDate,
                metrics: tabConfig.metrics.join(','),
                dimensions: tabConfig.dimensions.join(',')
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

            // Store in cache
            setCachedData(cacheKey, data);
            if (summary) {
                setCachedData(summaryCacheKey, summary);
            }
            console.log('💾 Cached data for:', cacheKey);

            setAnalyticsData(data);
            setSummaryData(summary);
        } catch (err) {
            console.error('Error fetching GA4 analytics:', err);
            setError('Failed to load analytics data');
        } finally {
            setLoading(false);
        }
    }, [selectedProperty, activeTab, dateRange.startDate, dateRange.endDate, getCacheKey, getCachedData, setCachedData]);

    // Fetch comparison data (also with summary for KPI)
    const fetchCompareData = useCallback(async (compareDateRange) => {
        if (!selectedProperty || !compareDateRange) {
            setCompareData(null);
            setCompareSummaryData(null);
            return;
        }

        const cacheKey = getCacheKey(selectedProperty, activeTab, compareDateRange.startDate, compareDateRange.endDate);
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

            const params = new URLSearchParams({
                property_id: selectedProperty,
                start_date: compareDateRange.startDate,
                end_date: compareDateRange.endDate,
                metrics: tabConfig.metrics.join(','),
                dimensions: tabConfig.dimensions.join(',')
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
    }, [selectedProperty, activeTab, getCacheKey, getCachedData, setCachedData]);

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
            // 本月：從本月1日到今天
            endDate = new Date(today);
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
                startDate: startDate.toISOString().split('T')[0],
                endDate: endDate.toISOString().split('T')[0],
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
                startDate: compareStart.toISOString().split('T')[0],
                endDate: compareEnd.toISOString().split('T')[0]
            };
        } else if (compareMode === 'previous_year') {
            const compareStart = new Date(start);
            compareStart.setFullYear(compareStart.getFullYear() - 1);
            const compareEnd = new Date(end);
            compareEnd.setFullYear(compareEnd.getFullYear() - 1);
            return {
                startDate: compareStart.toISOString().split('T')[0],
                endDate: compareEnd.toISOString().split('T')[0]
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

    // Format numbers for display
    const formatNumber = (num, type = 'number') => {
        if (typeof num !== 'number') return num;

        switch (type) {
            case 'percentage':
                return `${(num * 100).toFixed(1)}%`;
            case 'duration':
                const minutes = Math.floor(num / 60);
                const seconds = Math.floor(num % 60);
                return `${minutes}:${seconds.toString().padStart(2, '0')}`;
            case 'decimal':
                return num.toFixed(2);
            case 'currency':
                return `$${num.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
            default:
                return num.toLocaleString();
        }
    };

    // Calculate KPI changes (simplified - in real app would compare with previous period)
    const calculateChange = (current, previous) => {
        if (!previous || previous === 0) return null;
        const change = ((current - previous) / previous) * 100;
        return {
            value: change,
            isPositive: change > 0,
            formatted: `${change > 0 ? '+' : ''}${change.toFixed(1)}%`
        };
    };

    // Get KPI data from analytics
    // 使用 summaryData（不帶 dimension 的去重數據）來顯示 KPI 卡片
    const getKPIData = () => {
        if (!analyticsData || !analyticsData.rows) return [];

        // 優先使用 summaryData（去重總數），如果沒有則 fallback 到加總
        const currentTotals = {};

        if (summaryData && summaryData.rows && summaryData.rows.length > 0) {
            // 使用去重的總數（正確的方式）
            const summaryRow = summaryData.rows[0];
            analyticsData.metrics.forEach(metric => {
                currentTotals[metric] = parseFloat(summaryRow[metric]) || 0;
            });
            console.log('📊 Using summary data for KPIs (deduplicated)');
        } else {
            // Fallback: 加總每日數據（對於 sessions, pageviews 等可加總指標是正確的）
            analyticsData.rows.forEach(row => {
                analyticsData.metrics.forEach(metric => {
                    if (!currentTotals[metric]) currentTotals[metric] = 0;
                    currentTotals[metric] += parseFloat(row[metric]) || 0;
                });
            });
            console.log('⚠️ Fallback: summing daily data for KPIs');
        }

        // Determine comparison data source based on compare mode
        let previousTotals = {};

        if (compareMode !== 'none') {
            if (compareSummaryData && compareSummaryData.rows && compareSummaryData.rows.length > 0) {
                // 使用去重的比較總數
                const compareSummaryRow = compareSummaryData.rows[0];
                analyticsData.metrics.forEach(metric => {
                    previousTotals[metric] = parseFloat(compareSummaryRow[metric]) || 0;
                });
            } else if (compareData && compareData.rows) {
                // Fallback: 加總比較期間數據
                compareData.rows.forEach(row => {
                    analyticsData.metrics.forEach(metric => {
                        if (!previousTotals[metric]) previousTotals[metric] = 0;
                        previousTotals[metric] += parseFloat(row[metric]) || 0;
                    });
                });
            }
        } else {
            // 無比較模式時，使用當前期間的前半段作為比較基準
            // 但這對用戶類指標也不準確，所以只用於顯示變化趨勢
            const rows = analyticsData.rows;
            const midPoint = Math.floor(rows.length / 2);
            const previousPeriodRows = rows.slice(0, midPoint);
            previousPeriodRows.forEach(row => {
                analyticsData.metrics.forEach(metric => {
                    if (!previousTotals[metric]) previousTotals[metric] = 0;
                    previousTotals[metric] += parseFloat(row[metric]) || 0;
                });
            });
        }

        const kpis = [];
        analyticsData.metrics.forEach(metric => {
            const current = currentTotals[metric] || 0;
            const previous = previousTotals[metric] || 0;
            const change = calculateChange(current, previous);

            let type = 'number';
            if (metric === 'bounceRate') type = 'percentage';
            if (metric === 'averageSessionDuration') type = 'duration';
            if (metric === 'purchaseRevenue') type = 'currency';

            kpis.push({
                label: getMetricLabel(metric),
                value: formatNumber(current, type),
                change: change,
                icon: getMetricIcon(metric),
                previousValue: compareMode !== 'none' ? formatNumber(previous, type) : null
            });
        });

        // Add derived metric: 客單價 (AOV = purchaseRevenue / ecommercePurchases)
        const currentRevenue = currentTotals['purchaseRevenue'] || 0;
        const currentPurchases = currentTotals['ecommercePurchases'] || 0;
        const currentAOV = currentPurchases > 0 ? currentRevenue / currentPurchases : 0;

        const previousRevenue = previousTotals['purchaseRevenue'] || 0;
        const previousPurchases = previousTotals['ecommercePurchases'] || 0;
        const previousAOV = previousPurchases > 0 ? previousRevenue / previousPurchases : 0;

        const aovChange = calculateChange(currentAOV, previousAOV);

        kpis.push({
            label: getMetricLabel('averageOrderValue'),
            value: formatNumber(currentAOV, 'currency'),
            change: aovChange,
            icon: getMetricIcon('averageOrderValue'),
            previousValue: compareMode !== 'none' ? formatNumber(previousAOV, 'currency') : null
        });

        // Add derived metric: 購買轉換率 (Purchase Conversion Rate = ecommercePurchases / totalUsers)
        const currentUsers = currentTotals['totalUsers'] || 0;
        const currentConversionRate = currentUsers > 0 ? (currentPurchases / currentUsers) * 100 : 0;

        const previousUsers = previousTotals['totalUsers'] || 0;
        const previousConversionRate = previousUsers > 0 ? (previousPurchases / previousUsers) * 100 : 0;

        const conversionRateChange = calculateChange(currentConversionRate, previousConversionRate);

        kpis.push({
            label: getMetricLabel('purchaseConversionRate'),
            value: `${currentConversionRate.toFixed(2)}%`,
            change: conversionRateChange,
            icon: getMetricIcon('purchaseConversionRate'),
            previousValue: compareMode !== 'none' ? `${previousConversionRate.toFixed(2)}%` : null
        });

        return kpis;
    };

    // Get metric display labels
    const getMetricLabel = (metric) => {
        const labels = {
            // Metrics
            activeUsers: t('活躍使用者', 'Active Users'),
            totalUsers: t('總人數', 'Total Users'),
            newUsers: t('新使用者人數', 'New Users'),
            sessions: t('工作階段', 'Sessions'),
            screenPageViews: t('瀏覽', 'Page Views'),
            averageSessionDuration: t('平均工作階段持續時間', 'Avg. Session Duration'),
            bounceRate: t('跳出率', 'Bounce Rate'),
            ecommercePurchases: t('購買', 'Purchases'),
            purchaseRevenue: t('總購買收益', 'Total Revenue'),
            addToCarts: t('加入購物車', 'Add to Cart'),
            averageOrderValue: t('客單價', 'Avg. Order Value'),
            purchaseConversionRate: t('購買轉換率', 'Conversion Rate'),
            // Dimensions
            date: t('日期', 'Date'),
            pagePath: t('頁面路徑', 'Page Path'),
            sessionDefaultChannelGrouping: t('流量來源管道', 'Channel Grouping'),
            deviceCategory: t('裝置類別', 'Device Category'),
            country: t('國家', 'Country'),
            city: t('城市', 'City')
        };
        return labels[metric] || metric;
    };

    // Get metric icons
    const getMetricIcon = (metric) => {
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
            purchaseConversionRate: '📊'
        };
        return icons[metric] || '📊';
    };

    // Effects
    useEffect(() => {
        fetchProperties();
    }, []);

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
    }, [compareMode, getCompareDateRange, fetchCompareData, selectedProperty, analyticsData]);

    const kpiData = useMemo(() => getKPIData(), [analyticsData, summaryData, compareData, compareSummaryData, compareMode]);

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
                                    max={new Date().toISOString().split('T')[0]}
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
                                                // 本月：從本月1日到今天
                                                end = new Date(today);
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
                                            startDate: start.toISOString().split('T')[0],
                                            endDate: end.toISOString().split('T')[0],
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

                {/* Compare Mode Info */}
                {compareMode !== 'none' && (
                    <div style={{
                        marginTop: '16px',
                        padding: '12px 16px',
                        background: 'rgba(139, 92, 246, 0.1)',
                        borderRadius: '8px',
                        border: '1px solid rgba(139, 92, 246, 0.2)',
                        fontSize: '13px',
                        color: 'var(--text-secondary)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                    }}>
                        📊 {t('比較模式已啟用', 'Compare mode enabled')}:
                        <strong style={{ color: '#a78bfa' }}>
                            {compareMode === 'previous_period' ? t('前一時段', 'Previous Period') : t('去年同期', 'Previous Year')}
                        </strong>
                        {getCompareDateRange() && (
                            <span style={{ marginLeft: '8px' }}>
                                ({getCompareDateRange().startDate} ~ {getCompareDateRange().endDate})
                            </span>
                        )}
                    </div>
                )}
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

                {/* Loading State */}
                {loading && (
                    <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>
                        {t('載入中...', 'Loading...')}
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
                                        {OVERVIEW_COLUMN_ORDER.filter(col =>
                                            col === 'averageOrderValue' || col === 'purchaseConversionRate' || analyticsData.dimensions.includes(col) || analyticsData.metrics.includes(col)
                                        ).map(col => (
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
                                                {getMetricLabel(col)}
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
                                            return {
                                                ...row,
                                                // Calculate averageOrderValue for each row
                                                averageOrderValue: purchases > 0 ? revenue / purchases : 0,
                                                // Calculate purchaseConversionRate for each row
                                                purchaseConversionRate: users > 0 ? (purchases / users) * 100 : 0
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
                                        .slice(0, 20)
                                        .map((row, index) => (
                                            <tr key={index} style={{
                                                borderBottom: '1px solid var(--glass-border)',
                                                background: index % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)'
                                            }}>
                                                {OVERVIEW_COLUMN_ORDER.filter(col =>
                                                    col === 'averageOrderValue' || col === 'purchaseConversionRate' || analyticsData.dimensions.includes(col) || analyticsData.metrics.includes(col)
                                                ).map(col => (
                                                    <td key={col} style={{
                                                        padding: '12px 8px',
                                                        color: 'var(--text-primary)'
                                                    }}>
                                                        {col === 'date'
                                                            ? row[col] // Keep date as-is without formatting
                                                            : col === 'purchaseRevenue' || col === 'averageOrderValue'
                                                                ? formatNumber(parseFloat(row[col]) || 0, 'currency')
                                                                : col === 'purchaseConversionRate'
                                                                    ? `${(parseFloat(row[col]) || 0).toFixed(2)}%`
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
                        {analyticsData.rows.length > 20 && (
                            <div style={{
                                textAlign: 'center',
                                padding: '12px',
                                color: 'var(--text-secondary)',
                                fontSize: '14px'
                            }}>
                                {t(`顯示前 20 筆，共 ${analyticsData.rows.length} 筆`, `Showing first 20 rows of ${analyticsData.rows.length} total`)}
                            </div>
                        )}
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
        </div>
    );
};

export default GA4Stats;
