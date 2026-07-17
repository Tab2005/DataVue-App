import React, { useEffect, useState, useMemo, useCallback } from 'react';
import { getAllSourceGroups } from '../utils/sourceGroups';
import { getAllContentGroups, saveCustomContentGroup, deleteCustomContentGroup } from '../utils/contentGroups';
import SourceGroupModal from './SourceGroupModal';
import ContentGroupModal from './ContentGroupModal';
import {
    DATE_PRESETS,
    COMPARE_OPTIONS,
    TRAFFIC_METRICS,
    TRAFFIC_COLUMN_HEADERS,
    BEHAVIOR_METRICS,
    BEHAVIOR_COLUMN_HEADERS,
    ECOMMERCE_METRICS,
    ECOMMERCE_COLUMN_HEADERS,
    CONTENT_METRICS,
    CONTENT_COLUMN_HEADERS,
    TABS
} from './GA4/constants';
import {
    formatLocalDate,
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
import BehaviorSection, { BehaviorControls } from './GA4/BehaviorSection';
import ContentSection, { ContentControls } from './GA4/ContentSection';
import EcommerceSection, { EcommerceControls } from './GA4/EcommerceSection';
import OverviewSection from './GA4/OverviewSection';
import TrafficSection, { TrafficControls } from './GA4/TrafficSection';
import { useGa4StatsData } from '../hooks/useGa4StatsData';


const GA4Stats = ({ language, isMobile }) => {
    const t = (zh, en) => language === 'zh' ? zh : en;

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

    const {
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
        getCompareDateRange,
        handleCustomDateChange
    } = useGa4StatsData({
        trafficDimension,
        behaviorDimension,
        ecommerceDimension,
        ecommerceSecondaryDimension,
        contentDimension,
        ga4PageSize,
        setCurrentPage
    });

    const [sortConfig, setSortConfig] = useState({ key: 'date', direction: 'desc' });

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


    const getMetricLabel = (metric) => getMetricLabelForLanguage(metric, language);

    const getTrafficColumnOrder = () => getTrafficColumnOrderForDimension(trafficDimension);

    const getTrafficColumnLabel = (col) => getTrafficColumnLabelForLanguage(col, language);

    const getBehaviorColumnOrder = () => getBehaviorColumnOrderForDimension(behaviorDimension);

    const getBehaviorColumnLabel = (col) => getBehaviorColumnLabelForLanguage(col, language);

    const getEcommerceColumnOrder = () => getEcommerceColumnOrderForDimensions(ecommerceDimension, ecommerceSecondaryDimension);

    const getEcommerceColumnLabel = (col) => getEcommerceColumnLabelForLanguage(col, language);

    const getContentColumnOrder = () => getContentColumnOrderForDimension(contentDimension);

    const getContentColumnLabel = (col) => getContentColumnLabelForLanguage(col, language);

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
                    <TrafficControls
                        analyticsData={analyticsData}
                        isMobile={isMobile}
                        language={language}
                        setEditingGroup={setEditingGroup}
                        setShowGroupModal={setShowGroupModal}
                        setSourceFilter={setSourceFilter}
                        setTrafficDimension={setTrafficDimension}
                        sourceFilter={sourceFilter}
                        sourceGroups={sourceGroups}
                        t={t}
                        trafficDimension={trafficDimension}
                    />
                )}

                {/* Behavior Tab Controls */}
                {activeTab === 'behavior' && (
                    <BehaviorControls
                        analyticsData={analyticsData}
                        behaviorDimension={behaviorDimension}
                        behaviorFilter={behaviorFilter}
                        isMobile={isMobile}
                        language={language}
                        setBehaviorDimension={setBehaviorDimension}
                        setBehaviorFilter={setBehaviorFilter}
                        t={t}
                    />
                )}
                {/* Ecommerce Tab Controls */}
                {activeTab === 'ecommerce' && (
                    <EcommerceControls
                        analyticsData={analyticsData}
                        ecommerceDimension={ecommerceDimension}
                        ecommerceFilter={ecommerceFilter}
                        ecommerceSecondaryDimension={ecommerceSecondaryDimension}
                        ecommerceSecondaryFilter={ecommerceSecondaryFilter}
                        isMobile={isMobile}
                        language={language}
                        setEcommerceDimension={setEcommerceDimension}
                        setEcommerceFilter={setEcommerceFilter}
                        setEcommerceSecondaryDimension={setEcommerceSecondaryDimension}
                        setEcommerceSecondaryFilter={setEcommerceSecondaryFilter}
                        setEditingGroup={setEditingGroup}
                        setShowGroupModal={setShowGroupModal}
                        sourceGroups={sourceGroups}
                        t={t}
                    />
                )}
                {/* Content Tab Controls */}
                {activeTab === 'content' && (
                    <ContentControls
                        contentDimension={contentDimension}
                        contentGroups={contentGroups}
                        contentTypeFilter={contentTypeFilter}
                        isMobile={isMobile}
                        language={language}
                        setContentDimension={setContentDimension}
                        setContentTypeFilter={setContentTypeFilter}
                        setEditingContentGroup={setEditingContentGroup}
                        setShowContentGroupModal={setShowContentGroupModal}
                        t={t}
                    />
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
                {!loading && !error && analyticsData && activeTab === 'overview' && (
                    <OverviewSection
                        analyticsData={analyticsData}
                        currentPage={currentPage}
                        ga4HasMore={ga4HasMore}
                        ga4LoadingMore={ga4LoadingMore}
                        getMetricLabel={getMetricLabel}
                        isMobile={isMobile}
                        itemsPerPage={itemsPerPage}
                        loadMoreGa4Data={loadMoreGa4Data}
                        setCurrentPage={setCurrentPage}
                        setItemsPerPage={setItemsPerPage}
                        setSortConfig={setSortConfig}
                        sortConfig={sortConfig}
                        t={t}
                    />
                )}

                {!loading && !error && analyticsData && activeTab === 'traffic' && (
                    <TrafficSection
                        analyticsData={analyticsData}
                        currentPage={currentPage}
                        ga4HasMore={ga4HasMore}
                        ga4LoadingMore={ga4LoadingMore}
                        getTrafficColumnLabel={getTrafficColumnLabel}
                        getTrafficColumnOrder={getTrafficColumnOrder}
                        isMobile={isMobile}
                        itemsPerPage={itemsPerPage}
                        loadMoreGa4Data={loadMoreGa4Data}
                        setCurrentPage={setCurrentPage}
                        setItemsPerPage={setItemsPerPage}
                        setSortConfig={setSortConfig}
                        sortConfig={sortConfig}
                        t={t}
                    />
                )}

                {!loading && !error && analyticsData && activeTab === 'behavior' && (
                    <BehaviorSection
                        analyticsData={analyticsData}
                        currentPage={currentPage}
                        ga4HasMore={ga4HasMore}
                        ga4LoadingMore={ga4LoadingMore}
                        getBehaviorColumnLabel={getBehaviorColumnLabel}
                        getBehaviorColumnOrder={getBehaviorColumnOrder}
                        isMobile={isMobile}
                        itemsPerPage={itemsPerPage}
                        loadMoreGa4Data={loadMoreGa4Data}
                        setCurrentPage={setCurrentPage}
                        setItemsPerPage={setItemsPerPage}
                        setSortConfig={setSortConfig}
                        sortConfig={sortConfig}
                        t={t}
                    />
                )}

                {!loading && !error && analyticsData && activeTab === 'ecommerce' && (
                    <EcommerceSection
                        analyticsData={analyticsData}
                        currentPage={currentPage}
                        ga4HasMore={ga4HasMore}
                        ga4LoadingMore={ga4LoadingMore}
                        getEcommerceColumnLabel={getEcommerceColumnLabel}
                        getEcommerceColumnOrder={getEcommerceColumnOrder}
                        isMobile={isMobile}
                        itemsPerPage={itemsPerPage}
                        loadMoreGa4Data={loadMoreGa4Data}
                        setCurrentPage={setCurrentPage}
                        setItemsPerPage={setItemsPerPage}
                        setSortConfig={setSortConfig}
                        sortConfig={sortConfig}
                        t={t}
                    />
                )}

                {!loading && !error && analyticsData && activeTab === 'content' && (
                    <ContentSection
                        analyticsData={analyticsData}
                        currentPage={currentPage}
                        ga4HasMore={ga4HasMore}
                        ga4LoadingMore={ga4LoadingMore}
                        getContentColumnLabel={getContentColumnLabel}
                        getContentColumnOrder={getContentColumnOrder}
                        isMobile={isMobile}
                        itemsPerPage={itemsPerPage}
                        loadMoreGa4Data={loadMoreGa4Data}
                        setCurrentPage={setCurrentPage}
                        setItemsPerPage={setItemsPerPage}
                        setSortConfig={setSortConfig}
                        sortConfig={sortConfig}
                        t={t}
                    />
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
