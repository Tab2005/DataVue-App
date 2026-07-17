import React from 'react';
import { BEHAVIOR_DIMENSIONS, BEHAVIOR_FILTER_LABELS } from './constants';
import GA4StatsShared from './GA4StatsShared';

export const BehaviorControls = ({
    analyticsData,
    behaviorDimension,
    behaviorFilter,
    isMobile,
    language,
    setBehaviorDimension,
    setBehaviorFilter,
    t
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
                {analyticsData && analyticsData.rows &&
                    [...new Set(analyticsData.rows.map(row => (
                        row[behaviorDimension] || row.dimension
                    )).filter(Boolean))].sort().map(value => (
                        <option key={value} value={value} style={{ color: 'black' }}>
                            {value}
                        </option>
                    ))
                }
            </select>
        </div>
    </div>
);

const BehaviorSection = ({
    analyticsData,
    currentPage,
    ga4HasMore,
    ga4LoadingMore,
    getBehaviorColumnLabel,
    getBehaviorColumnOrder,
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
        activeTab="behavior"
        analyticsData={analyticsData}
        columns={getBehaviorColumnOrder()}
        currentPage={currentPage}
        ga4HasMore={ga4HasMore}
        ga4LoadingMore={ga4LoadingMore}
        getColumnLabel={getBehaviorColumnLabel}
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

export default BehaviorSection;
