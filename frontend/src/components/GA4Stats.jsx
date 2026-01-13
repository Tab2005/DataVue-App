import React, { useEffect, useState, useMemo, useCallback, useRef } from 'react';

// Date Range Presets Configuration
const DATE_PRESETS = [
    { key: 'last_7d', label_zh: '過去 7 天', label_en: 'Last 7 Days', days: 7 },
    { key: 'last_28d', label_zh: '過去 28 天', label_en: 'Last 28 Days', days: 28 },
    { key: 'last_3m', label_zh: '過去 3 個月', label_en: 'Last 3 Months', days: 90 },
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
    { key: 'overview', label_zh: '📊 總覽', label_en: '📊 Overview', metrics: ['activeUsers', 'totalUsers', 'newUsers', 'sessions'], dimensions: ['date'] },
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
    const [compareData, setCompareData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('overview');
    const [showCustomDatePicker, setShowCustomDatePicker] = useState(false);
    const [compareMode, setCompareMode] = useState('none');
    const [dateRange, setDateRange] = useState({
        startDate: new Date(Date.now() - 28 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        endDate: new Date().toISOString().split('T')[0],
        preset: 'last_28d'
    });

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
    const fetchAnalytics = useCallback(async (forceRefresh = false) => {
        if (!selectedProperty) return;

        const cacheKey = getCacheKey(selectedProperty, activeTab, dateRange.startDate, dateRange.endDate);
        
        // Check cache first (unless force refresh)
        if (!forceRefresh) {
            const cachedData = getCachedData(cacheKey);
            if (cachedData) {
                console.log('📦 Using cached data for:', cacheKey);
                setAnalyticsData(cachedData);
                return;
            }
        }

        setLoading(true);
        setError(null);

        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const tabConfig = TABS.find(tab => tab.key === activeTab);

            const params = new URLSearchParams({
                property_id: selectedProperty,
                start_date: dateRange.startDate,
                end_date: dateRange.endDate,
                metrics: tabConfig.metrics.join(','),
                dimensions: tabConfig.dimensions.join(',')
            });

            const response = await fetch(`${apiUrl}/api/ga4/report?${params}`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('google_token')}` }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch analytics data');
            }

            const data = await response.json();
            
            // Store in cache
            setCachedData(cacheKey, data);
            console.log('💾 Cached data for:', cacheKey);
            
            setAnalyticsData(data);
        } catch (err) {
            console.error('Error fetching GA4 analytics:', err);
            setError('Failed to load analytics data');
        } finally {
            setLoading(false);
        }
    }, [selectedProperty, activeTab, dateRange.startDate, dateRange.endDate, getCacheKey, getCachedData, setCachedData]);

    // Fetch comparison data
    const fetchCompareData = useCallback(async (compareDateRange) => {
        if (!selectedProperty || !compareDateRange) {
            setCompareData(null);
            return;
        }

        const cacheKey = getCacheKey(selectedProperty, activeTab, compareDateRange.startDate, compareDateRange.endDate);
        
        // Check cache first
        const cachedData = getCachedData(cacheKey);
        if (cachedData) {
            console.log('📦 Using cached compare data for:', cacheKey);
            setCompareData(cachedData);
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

            const response = await fetch(`${apiUrl}/api/ga4/report?${params}`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('google_token')}` }
            });

            if (response.ok) {
                const data = await response.json();
                setCachedData(cacheKey, data);
                setCompareData(data);
            }
        } catch (err) {
            console.error('Error fetching compare data:', err);
        }
    }, [selectedProperty, activeTab, getCacheKey, getCachedData, setCachedData]);

    // Handle date preset change
    const handleDatePresetChange = (preset) => {
        const presetConfig = DATE_PRESETS.find(p => p.key === preset);
        if (presetConfig.days) {
            const endDate = new Date();
            const startDate = new Date(Date.now() - presetConfig.days * 24 * 60 * 60 * 1000);
            setDateRange({
                startDate: startDate.toISOString().split('T')[0],
                endDate: endDate.toISOString().split('T')[0],
                preset
            });
            setShowCustomDatePicker(false);
        } else {
            // Custom preset - toggle date picker (fix: always show when clicking custom)
            setShowCustomDatePicker(true);
            setDateRange(prev => ({ ...prev, preset: 'custom' }));
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
    const getKPIData = () => {
        if (!analyticsData || !analyticsData.rows) return [];

        const rows = analyticsData.rows;
        
        // Calculate totals for current period (all rows)
        const currentTotals = {};
        rows.forEach(row => {
            analyticsData.metrics.forEach(metric => {
                if (!currentTotals[metric]) currentTotals[metric] = 0;
                currentTotals[metric] += row[metric] || 0;
            });
        });

        // Determine comparison data source based on compare mode
        let previousTotals = {};
        
        if (compareMode !== 'none' && compareData && compareData.rows) {
            // Use compare data from different period/year
            compareData.rows.forEach(row => {
                analyticsData.metrics.forEach(metric => {
                    if (!previousTotals[metric]) previousTotals[metric] = 0;
                    previousTotals[metric] += row[metric] || 0;
                });
            });
        } else {
            // Default: split current data for period-over-period comparison
            const midPoint = Math.floor(rows.length / 2);
            const previousPeriodRows = rows.slice(0, midPoint);
            previousPeriodRows.forEach(row => {
                analyticsData.metrics.forEach(metric => {
                    if (!previousTotals[metric]) previousTotals[metric] = 0;
                    previousTotals[metric] += row[metric] || 0;
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

            kpis.push({
                label: getMetricLabel(metric),
                value: formatNumber(current, type),
                change: change,
                icon: getMetricIcon(metric),
                previousValue: compareMode !== 'none' ? formatNumber(previous, type) : null
            });
        });

        return kpis;
    };

    // Get metric display labels
    const getMetricLabel = (metric) => {
        const labels = {
            // Metrics
            activeUsers: t('活躍用戶', 'Active Users'),
            totalUsers: t('總用戶', 'Total Users'),
            newUsers: t('新用戶', 'New Users'),
            sessions: t('工作階段', 'Sessions'),
            screenPageViews: t('頁面瀏覽', 'Page Views'),
            averageSessionDuration: t('平均工作階段持續時間', 'Avg. Session Duration'),
            bounceRate: t('跳出率', 'Bounce Rate'),
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
            bounceRate: '📈'
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
        }
    }, [compareMode, getCompareDateRange, fetchCompareData, selectedProperty, analyticsData]);

    const kpiData = useMemo(() => getKPIData(), [analyticsData, compareData, compareMode]);

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
                                { label: t('今天', 'Today'), days: 0 },
                                { label: t('昨天', 'Yesterday'), days: 1 },
                                { label: t('本週', 'This Week'), days: 7 },
                                { label: t('本月', 'This Month'), days: 30 },
                                { label: t('本季', 'This Quarter'), days: 90 }
                            ].map(quick => (
                                <button
                                    key={quick.label}
                                    onClick={() => {
                                        const end = quick.days === 1 
                                            ? new Date(Date.now() - 24 * 60 * 60 * 1000)
                                            : new Date();
                                        const start = quick.days === 0 
                                            ? new Date()
                                            : new Date(end.getTime() - quick.days * 24 * 60 * 60 * 1000);
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

            {/* KPI Cards */}
            {!loading && !error && kpiData.length > 0 && (
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fit, minmax(220px, 1fr))',
                    gap: '16px',
                    marginBottom: '24px'
                }}>
                    {kpiData.map((kpi, index) => (
                        <div
                            key={index}
                            style={{
                                padding: '20px',
                                background: 'rgba(255, 255, 255, 0.03)',
                                border: '1px solid var(--glass-border)',
                                borderRadius: '12px',
                                display: 'flex',
                                alignItems: 'flex-start',
                                gap: '16px'
                            }}
                        >
                            <div style={{ fontSize: '28px', opacity: 0.9 }}>{kpi.icon}</div>
                            <div style={{ flex: 1 }}>
                                <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                                    {kpi.label}
                                </div>
                                <div style={{ fontSize: '26px', fontWeight: '700', color: 'var(--text-primary)' }}>
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
                                    {analyticsData.dimensions.map(dim => (
                                        <th key={dim} style={{
                                            padding: '12px 8px',
                                            textAlign: 'left',
                                            color: 'var(--text-secondary)',
                                            fontWeight: '500'
                                        }}>
                                            {getMetricLabel(dim)}
                                        </th>
                                    ))}
                                    {analyticsData.metrics.map(metric => (
                                        <th key={metric} style={{
                                            padding: '12px 8px',
                                            textAlign: 'left',
                                            color: 'var(--text-secondary)',
                                            fontWeight: '500'
                                        }}>
                                            {getMetricLabel(metric)}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {analyticsData.rows.slice(0, 20).map((row, index) => (
                                    <tr key={index} style={{
                                        borderBottom: '1px solid var(--glass-border)',
                                        background: index % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)'
                                    }}>
                                        {analyticsData.dimensions.map(dim => (
                                            <td key={dim} style={{
                                                padding: '12px 8px',
                                                color: 'var(--text-primary)'
                                            }}>
                                                {row[dim]}
                                            </td>
                                        ))}
                                        {analyticsData.metrics.map(metric => (
                                            <td key={metric} style={{
                                                padding: '12px 8px',
                                                color: 'var(--text-primary)'
                                            }}>
                                                {formatNumber(row[metric], metric === 'bounceRate' ? 'percentage' :
                                                    metric === 'averageSessionDuration' ? 'duration' : 'number')}
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
    );
};

export default GA4Stats;