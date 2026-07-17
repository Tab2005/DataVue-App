/* eslint-disable react-refresh/only-export-components */
import React from 'react';

export const getTabStyle = (isMobile) => (isActive) => ({
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

export const getToggleButtonStyle = (isActive) => ({
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

export const getSortIndicator = (sortConfig, key) => {
    if (sortConfig.key !== key) return ' ↕';
    return sortConfig.direction === 'desc' ? ' ↓' : ' ↑';
};

const buildSummaryStyles = (isMobile) => ({
    gridStyle: {
        display: 'grid',
        gridTemplateColumns: isMobile ? 'calc(50% - 4px) calc(50% - 4px)' : 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: isMobile ? '8px' : '16px',
        width: '100%',
        boxSizing: 'border-box'
    },
    cardStyle: {
        background: 'var(--bg-secondary)',
        padding: isMobile ? '12px' : '20px',
        borderRadius: isMobile ? '8px' : '12px',
        border: '1px solid var(--glass-border)',
        boxShadow: 'var(--shadow-sm)',
        minWidth: 0
    },
    cardLabelStyle: {
        fontSize: isMobile ? '12px' : '14px',
        color: 'var(--text-secondary)',
        marginBottom: '8px'
    },
    cardValueStyle: {
        fontSize: isMobile ? '16px' : '24px',
        fontWeight: 'bold',
        color: 'var(--text-primary)',
        wordBreak: 'break-word'
    }
});

export const GscCompareInfo = ({
    change,
    previousValue,
    compareMode,
    formatter = (value) => value.toLocaleString(),
    isPositionMetric = false
}) => {
    if (compareMode === 'none' || change === null) return null;

    const isPositive = isPositionMetric ? change < 0 : change >= 0;
    const displayChange = isPositionMetric ? -change : change;

    return (
        <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginTop: '6px'
        }}>
            <span style={{
                fontSize: '12px',
                padding: '2px 8px',
                borderRadius: '12px',
                background: isPositive ? 'rgba(52, 168, 83, 0.15)' : 'rgba(234, 67, 53, 0.15)',
                color: isPositive ? '#34a853' : '#ea4335',
                fontWeight: 600
            }}>
                {isPositive ? '▲' : '▼'} {Math.abs(displayChange).toFixed(1)}%
            </span>
            <span style={{
                fontSize: '11px',
                color: 'var(--text-secondary)',
                opacity: 0.7
            }}>
                vs {formatter(previousValue)}
            </span>
        </div>
    );
};

export const GscSummaryCards = ({
    analytics,
    activeTab,
    compareMode,
    calculateChange,
    getCompareTotals,
    getDaysInRange,
    isMobile,
    t
}) => {
    // trend 與 searchAppearance 有各自的彙總 KPI 呈現方式：
    // trend 沒有單一期間總量的概念；searchAppearance 各列可能重複計算（同一結果可同時符合多種外觀類型），
    // 所以這裡的通用加總不適用，改由各自的 tab 元件顯示正確的彙總數據。
    if (activeTab === 'trend' || activeTab === 'searchAppearance') return null;

    const { gridStyle, cardStyle, cardLabelStyle, cardValueStyle } = buildSummaryStyles(isMobile);
    const currentClicks = analytics.reduce((acc, row) => acc + row.clicks, 0);
    const currentImpressions = analytics.reduce((acc, row) => acc + row.impressions, 0);
    const currentCtr = analytics.reduce((acc, row) => acc + row.ctr, 0) / (analytics.length || 1) * 100;
    const currentPosition = analytics.reduce((acc, row) => acc + row.position, 0) / (analytics.length || 1);
    const compareTotals = getCompareTotals();

    const clicksChange = compareTotals ? calculateChange(currentClicks, compareTotals.clicks) : null;
    const impressionsChange = compareTotals ? calculateChange(currentImpressions, compareTotals.impressions) : null;
    const ctrChange = compareTotals ? calculateChange(currentCtr, compareTotals.ctr * 100) : null;
    const positionChange = compareTotals ? calculateChange(currentPosition, compareTotals.position) : null;

    return (
        <div style={gridStyle}>
            <div style={cardStyle}>
                <div style={cardLabelStyle}>{t(`總點擊數 (${getDaysInRange()}天)`, `Total Clicks (${getDaysInRange()}d)`)}</div>
                <div style={cardValueStyle}>{currentClicks.toLocaleString()}</div>
                <GscCompareInfo change={clicksChange} previousValue={compareTotals?.clicks || 0} compareMode={compareMode} />
            </div>
            <div style={cardStyle}>
                <div style={cardLabelStyle}>{t(`總曝光數 (${getDaysInRange()}天)`, `Total Impressions (${getDaysInRange()}d)`)}</div>
                <div style={cardValueStyle}>{currentImpressions.toLocaleString()}</div>
                <GscCompareInfo change={impressionsChange} previousValue={compareTotals?.impressions || 0} compareMode={compareMode} />
            </div>
            <div style={cardStyle}>
                <div style={cardLabelStyle}>{t('平均點閱率', 'Avg CTR')}</div>
                <div style={cardValueStyle}>{currentCtr.toFixed(2)}%</div>
                <GscCompareInfo
                    change={ctrChange}
                    previousValue={(compareTotals?.ctr || 0) * 100}
                    compareMode={compareMode}
                    formatter={(value) => `${value.toFixed(2)}%`}
                />
            </div>
            <div style={cardStyle}>
                <div style={cardLabelStyle}>{t('平均排名', 'Avg Position')}</div>
                <div style={cardValueStyle}>{currentPosition.toFixed(1)}</div>
                <GscCompareInfo
                    change={positionChange}
                    previousValue={compareTotals?.position || 0}
                    compareMode={compareMode}
                    formatter={(value) => value.toFixed(1)}
                    isPositionMetric
                />
            </div>
            {activeTab === 'page' && (
                <div style={{ ...cardStyle, background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(139, 92, 246, 0.05))' }}>
                    <div style={cardLabelStyle}>📄 {t('索引頁面數', 'Indexed Pages')}</div>
                    <div style={{ ...cardValueStyle, color: '#8B5CF6' }}>{analytics.length.toLocaleString()}</div>
                </div>
            )}
        </div>
    );
};
