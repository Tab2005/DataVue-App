import React from 'react';

import KPICard from '../KPICard';
import { ALL_METRIC_GROUPS } from './analyticsMetrics';

const AnalyticsKpiSection = ({
    currentSummaryData,
    dateRange,
    handleExportImage,
    isCompareMode,
    isMobile,
    language,
    kpiRef,
    prevDateRange,
    prevSummaryData,
    renderMetricValue,
    selectedMetrics,
    setShowKpiMenu,
    showKpiMenu,
    txt,
}) => (
    <>
            {/* KPI Section */}
            <div>
                {currentSummaryData && (
                    <div ref={kpiRef} className="glass-panel" style={{ marginBottom: '32px', padding: '24px', borderRadius: '16px', position: 'relative' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', borderBottom: '1px solid var(--glass-border)', paddingBottom: '16px' }}>
                            <h2 style={{
                                fontSize: '1.2rem',
                                color: '#fbbf24',
                                display: 'flex',
                                flexDirection: 'row', // Always row, let wrap handle it
                                flexWrap: 'wrap',
                                alignItems: 'baseline',
                                gap: '8px',
                                margin: 0,
                                lineHeight: 1.5
                            }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', whiteSpace: 'nowrap' }}>
                                    ⭐ {txt.keyMetrics}
                                </div>
                                <span style={{
                                    fontSize: isMobile ? '0.8rem' : '0.9rem',
                                    color: 'var(--text-secondary)',
                                    fontWeight: 'normal',
                                    lineHeight: isMobile ? '1.4' : 'inherit'
                                }}>
                                    ({dateRange.since} ~ {dateRange.until}
                                    {isCompareMode && prevDateRange.since ? ` vs ${prevDateRange.since} ~ ${prevDateRange.until}` : ''})
                                </span>
                            </h2>

                            {/* More Options Menu */}
                            <div style={{ position: 'relative' }} data-html2canvas-ignore="true">
                                <button
                                    onClick={() => setShowKpiMenu(!showKpiMenu)}
                                    style={{
                                        background: 'transparent',
                                        border: 'none',
                                        color: 'var(--text-secondary)',
                                        fontSize: '1.2rem',
                                        cursor: 'pointer',
                                        padding: '4px',
                                        borderRadius: '50%',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        transition: 'background 0.2s'
                                    }}
                                    onMouseEnter={(e) => e.target.style.background = 'rgba(255,255,255,0.1)'}
                                    onMouseLeave={(e) => e.target.style.background = 'transparent'}
                                >
                                    ⋮
                                </button>

                                {showKpiMenu && (
                                    <div style={{
                                        position: 'absolute',
                                        top: '100%',
                                        right: 0,
                                        marginTop: '8px',
                                        background: '#242526',
                                        border: '1px solid var(--glass-border)',
                                        borderRadius: '8px',
                                        padding: '4px',
                                        zIndex: 100,
                                        boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
                                        minWidth: '140px'
                                    }}>
                                        <button
                                            onClick={handleExportImage}
                                            style={{
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: '8px',
                                                width: '100%',
                                                padding: '8px 12px',
                                                background: 'transparent',
                                                border: 'none',
                                                color: 'var(--text-primary)',
                                                fontSize: '0.9rem',
                                                cursor: 'pointer',
                                                borderRadius: '4px',
                                                textAlign: 'left'
                                            }}
                                            onMouseEnter={(e) => e.target.style.background = 'rgba(255,255,255,0.1)'}
                                            onMouseLeave={(e) => e.target.style.background = 'transparent'}
                                        >
                                            ⬇️ {language === 'zh' ? '匯出圖片' : 'Export Image'}
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                            {ALL_METRIC_GROUPS.map((group, gIdx) => {
                                // Filter metrics for this group that are currently selected using composite key
                                const activeGroupMetrics = group.metrics.filter(m => selectedMetrics.has(`${group.id}:${m.key}`));

                                // If no metrics in this group are selected, don't render the group title or container
                                if (activeGroupMetrics.length === 0) return null;

                                return (
                                    <div key={gIdx}>
                                        <h3 style={{ fontSize: '1rem', color: group.color || '#3b82f6', marginBottom: '12px', borderLeft: `3px solid ${group.color || '#3b82f6'}`, paddingLeft: '8px' }}>
                                            {language === 'zh' ? group.label_zh : group.label_en}
                                        </h3>
                                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '12px' }}>
                                            {activeGroupMetrics.map(m => {
                                                const currentVal = currentSummaryData ? (currentSummaryData[m.key] || 0) : 0;
                                                const prevVal = prevSummaryData ? (prevSummaryData[m.key] || 0) : null;

                                                // Debug: Log each metric's value
                                                if (m.key === 'ctr') {
                                                    console.log('[Analytics Debug] Rendering CTR card:', {
                                                        key: m.key,
                                                        currentVal,
                                                        raw_value: currentSummaryData?.[m.key],
                                                        summaryData_exists: !!currentSummaryData,
                                                        format: m.format
                                                    });
                                                }

                                                // Diff calculation
                                                let diff = null;
                                                let percent = null;
                                                let isIncrease = false;

                                                if (prevSummaryData) {
                                                    const d = currentVal - prevVal;
                                                    isIncrease = d >= 0;

                                                    // Format Difference
                                                    if (m.format === 'currency') diff = `${d >= 0 ? '+' : ''}$${Math.abs(d).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
                                                    else if (m.format === 'percent') diff = `${d >= 0 ? '+' : ''}${d.toFixed(2)}%`;
                                                    else if (m.format === 'decimal') diff = `${d >= 0 ? '+' : ''}${d.toFixed(2)}`;
                                                    else diff = `${d >= 0 ? '+' : ''}${Math.abs(d).toLocaleString()}`;

                                                    // Calculate Percent Change
                                                    if (prevVal !== 0) {
                                                        const p = (d / prevVal) * 100;
                                                        percent = `${p >= 0 ? '+' : ''}${p.toFixed(1)}%`;
                                                    } else if (currentVal !== 0) {
                                                        percent = '+100%';
                                                    } else {
                                                        percent = '0%';
                                                    }
                                                }

                                                return (
                                                    <KPICard
                                                        key={m.key}
                                                        title={language === 'zh' ? m.label_zh : m.label_en}
                                                        value={renderMetricValue(currentVal, m.format)}
                                                        sub_value={prevSummaryData ? `(${renderMetricValue(prevVal, m.format)})` : ''}
                                                        diff={diff}
                                                        percent={percent}
                                                        is_increase={isIncrease}
                                                        is_inverse={m.isInverse || false}
                                                    />
                                                );
                                            })}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )
                }
            </div>
    </>
);

export default AnalyticsKpiSection;
