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
    { key: 'overview', label_zh: '📊 總覽', label_en: '📊 Overview', metrics: ['activeUsers', 'totalUsers', 'newUsers', 'sessions'], dimensions: ['date'] },
    { key: 'traffic', label_zh: '🌐 流量來源', label_en: '🌐 Traffic Sources', metrics: ['sessions', 'screenPageViews'], dimensions: ['sessionDefaultChannelGrouping'] },
    { key: 'behavior', label_zh: '👥 用戶行為', label_en: '👥 User Behavior', metrics: ['bounceRate', 'averageSessionDuration'], dimensions: ['date'] },
    { key: 'content', label_zh: '📄 內容分析', label_en: '📄 Content Analysis', metrics: ['screenPageViews', 'sessions'], dimensions: ['pagePath'] }
];

const GA4Stats = ({ language, isMobile }) => {
    const t = (zh, en) => language === 'zh' ? zh : en;

    // State management
    const [properties, setProperties] = useState([]);
    const [selectedProperty, setSelectedProperty] = useState('');
    const [analyticsData, setAnalyticsData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('overview');
    const [dateRange, setDateRange] = useState({
        startDate: new Date(Date.now() - 28 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        endDate: new Date().toISOString().split('T')[0],
        preset: 'last_28d'
    });

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

    // Fetch analytics data
    const fetchAnalytics = async () => {
        if (!selectedProperty) return;

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
            setAnalyticsData(data);
        } catch (err) {
            console.error('Error fetching GA4 analytics:', err);
            setError('Failed to load analytics data');
        } finally {
            setLoading(false);
        }
    };

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
        } else {
            setDateRange(prev => ({ ...prev, preset }));
        }
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

        const latestRow = analyticsData.rows[analyticsData.rows.length - 1];
        const previousRow = analyticsData.rows.length > 1 ? analyticsData.rows[analyticsData.rows.length - 2] : null;

        const kpis = [];
        analyticsData.metrics.forEach(metric => {
            const current = latestRow[metric];
            const previous = previousRow ? previousRow[metric] : null;
            const change = calculateChange(current, previous);

            let type = 'number';
            if (metric === 'bounceRate') type = 'percentage';
            if (metric === 'averageSessionDuration') type = 'duration';

            kpis.push({
                label: getMetricLabel(metric),
                value: formatNumber(current, type),
                change: change,
                icon: getMetricIcon(metric)
            });
        });

        return kpis;
    };

    // Get metric display labels
    const getMetricLabel = (metric) => {
        const labels = {
            activeUsers: t('活躍用戶', 'Active Users'),
            totalUsers: t('總用戶', 'Total Users'),
            newUsers: t('新用戶', 'New Users'),
            sessions: t('工作階段', 'Sessions'),
            screenPageViews: t('頁面瀏覽', 'Page Views'),
            averageSessionDuration: t('平均工作階段持續時間', 'Avg. Session Duration'),
            bounceRate: t('跳出率', 'Bounce Rate')
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
        if (selectedProperty) {
            fetchAnalytics();
        }
    }, [selectedProperty, activeTab, dateRange]);

    const kpiData = useMemo(() => getKPIData(), [analyticsData]);

    return (
        <div style={{ width: '100%', padding: isMobile ? '16px' : '24px' }}>
            {/* Controls Section */}
            <div style={{
                display: 'flex',
                flexDirection: isMobile ? 'column' : 'row',
                gap: '16px',
                marginBottom: '24px',
                alignItems: isMobile ? 'stretch' : 'center'
            }}>
                {/* Property Selector */}
                <div style={{ flex: 1 }}>
                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: 'var(--text-primary)' }}>
                        {t('選擇屬性', 'Select Property')}
                    </label>
                    <select
                        value={selectedProperty}
                        onChange={(e) => setSelectedProperty(e.target.value)}
                        style={{
                            width: '100%',
                            padding: '8px 12px',
                            border: '1px solid var(--glass-border)',
                            borderRadius: '8px',
                            background: 'var(--bg-secondary)',
                            color: 'var(--text-primary)',
                            fontSize: '14px'
                        }}
                    >
                        <option value="">{t('選擇 GA4 屬性...', 'Select GA4 Property...')}</option>
                        {properties.map(prop => (
                            <option key={prop.property_id} value={prop.property_id}>
                                {prop.display_name || prop.property_id}
                            </option>
                        ))}
                    </select>
                </div>

                {/* Date Range Selector */}
                <div style={{ flex: 1 }}>
                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: 'var(--text-primary)' }}>
                        {t('日期範圍', 'Date Range')}
                    </label>
                    <select
                        value={dateRange.preset}
                        onChange={(e) => handleDatePresetChange(e.target.value)}
                        style={{
                            width: '100%',
                            padding: '8px 12px',
                            border: '1px solid var(--glass-border)',
                            borderRadius: '8px',
                            background: 'var(--bg-secondary)',
                            color: 'var(--text-primary)',
                            fontSize: '14px'
                        }}
                    >
                        {DATE_PRESETS.map(preset => (
                            <option key={preset.key} value={preset.key}>
                                {language === 'zh' ? preset.label_zh : preset.label_en}
                            </option>
                        ))}
                    </select>
                </div>
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
                    gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fit, minmax(200px, 1fr))',
                    gap: '16px',
                    marginBottom: '24px'
                }}>
                    {kpiData.map((kpi, index) => (
                        <div
                            key={index}
                            style={{
                                padding: '20px',
                                background: 'var(--bg-secondary)',
                                border: '1px solid var(--glass-border)',
                                borderRadius: '12px',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '16px'
                            }}
                        >
                            <div style={{ fontSize: '24px' }}>{kpi.icon}</div>
                            <div style={{ flex: 1 }}>
                                <div style={{ fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                                    {kpi.label}
                                </div>
                                <div style={{ fontSize: '24px', fontWeight: '700', color: 'var(--text-primary)' }}>
                                    {kpi.value}
                                </div>
                                {kpi.change && (
                                    <div style={{
                                        fontSize: '12px',
                                        color: kpi.change.isPositive ? '#34a853' : '#ea4335',
                                        marginTop: '4px'
                                    }}>
                                        {kpi.change.formatted}
                                    </div>
                                )}
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