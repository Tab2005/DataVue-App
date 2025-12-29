
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
    { key: 'page', label_zh: '📄 頁面分析', label_en: '📄 Page Analysis', dimension: 'page' }
];

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

    const start = new Date();
    start.setDate(today.getDate() - preset.days);
    return { start: formatDate(start), end: formatDate(today) };
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

// Helper: Calculate similarity between two strings (Levenshtein-based)
const getSimilarity = (str1, str2) => {
    const s1 = str1.toLowerCase();
    const s2 = str2.toLowerCase();

    // Check if one contains the other
    if (s1.includes(s2) || s2.includes(s1)) return 0.8;

    // Check common word overlap
    const words1 = new Set(s1.split(/\s+/));
    const words2 = new Set(s2.split(/\s+/));
    const intersection = [...words1].filter(w => words2.has(w));
    const union = new Set([...words1, ...words2]);

    return intersection.length / union.size;
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
            fetchAnalytics(selectedSite, dateRange.start, dateRange.end, dimension);
        }
    }, [selectedSite, dateRange, activeTab]);

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
            let aVal = a[sortConfig.key] ?? 0;
            let bVal = b[sortConfig.key] ?? 0;
            return sortConfig.direction === 'desc' ? bVal - aVal : aVal - bVal;
        });

        if (activeTab !== 'daily') {
            data = data.slice(0, rowLimit);
        }

        return data;
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

            {analyticsLoading ? (
                <div style={{ color: 'var(--text-secondary)' }}>
                    {t('載入數據中...', 'Loading analytics...')}
                </div>
            ) : (
                <>
                    {/* Summary Cards */}
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

                    {/* Table Section */}
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
                                        <th style={thStyle}>
                                            {activeTab === 'daily' && t('日期', 'Date')}
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
                                        sortedData.map((row, idx) => (
                                            <tr
                                                key={idx}
                                                style={{ transition: 'background 0.2s' }}
                                                onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-hover)'}
                                                onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                                            >
                                                <td style={{
                                                    ...tdStyle,
                                                    maxWidth: activeTab === 'page' ? '300px' : 'auto',
                                                    overflow: 'hidden',
                                                    textOverflow: 'ellipsis',
                                                    whiteSpace: activeTab === 'page' ? 'nowrap' : 'normal'
                                                }}>
                                                    {activeTab === 'page' && row.keys && row.keys[0] ? (
                                                        <a
                                                            href={row.keys[0]}
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                            style={{ color: 'var(--accent-primary)', textDecoration: 'none' }}
                                                            title={row.keys[0]}
                                                        >
                                                            {row.keys[0].replace(/^https?:\/\/[^/]+/, '')}
                                                        </a>
                                                    ) : (
                                                        row.keys && row.keys[0]
                                                    )}
                                                </td>
                                                <td style={tdStyle}>{row.clicks.toLocaleString()}</td>
                                                <td style={tdStyle}>{row.impressions.toLocaleString()}</td>
                                                <td style={tdStyle}>{(row.ctr * 100).toFixed(2)}%</td>
                                                <td style={tdStyle}>{row.position.toFixed(1)}</td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
};

export default GSCStats;

