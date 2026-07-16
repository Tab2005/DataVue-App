import React from 'react';
import { TRAFFIC_DIMENSIONS } from './constants';
import GA4StatsShared from './GA4StatsShared';

export const TrafficControls = ({
    analyticsData,
    isMobile,
    language,
    setEditingGroup,
    setShowGroupModal,
    setSourceFilter,
    setTrafficDimension,
    sourceFilter,
    sourceGroups,
    t,
    trafficDimension
}) => (
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
                    {analyticsData && analyticsData.rows && sourceGroups.filter(group => {
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
                    <option disabled style={{ color: '#666' }}>──────────────</option>
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
);

const TrafficSection = ({
    analyticsData,
    currentPage,
    ga4HasMore,
    ga4LoadingMore,
    getTrafficColumnLabel,
    getTrafficColumnOrder,
    isMobile,
    itemsPerPage,
    loadMoreGa4Data,
    setCurrentPage,
    setItemsPerPage,
    setSortConfig,
    sortConfig,
    t
}) => (
    <GA4StatsShared
        activeTab="traffic"
        analyticsData={analyticsData}
        columns={getTrafficColumnOrder()}
        currentPage={currentPage}
        ga4HasMore={ga4HasMore}
        ga4LoadingMore={ga4LoadingMore}
        getColumnLabel={getTrafficColumnLabel}
        isMobile={isMobile}
        itemsPerPage={itemsPerPage}
        loadMoreGa4Data={loadMoreGa4Data}
        setCurrentPage={setCurrentPage}
        setItemsPerPage={setItemsPerPage}
        setSortConfig={setSortConfig}
        sortConfig={sortConfig}
        t={t}
    />
);

export default TrafficSection;
