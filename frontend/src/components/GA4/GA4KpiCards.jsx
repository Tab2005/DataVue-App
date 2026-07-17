import React from 'react';

const GA4KpiCards = ({ compareMode, isMobile, kpiData, loading, error, t }) => {
    if (loading || error || kpiData.length === 0) return null;

    return (
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
                        <div style={{
                            fontSize: isMobile ? '11px' : '13px',
                            color: 'var(--text-secondary)',
                            marginBottom: isMobile ? '4px' : '6px'
                        }}>
                            {kpi.label}
                        </div>
                        <div style={{
                            fontSize: isMobile ? '18px' : '26px',
                            fontWeight: '700',
                            color: 'var(--text-primary)'
                        }}>
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
    );
};

export default GA4KpiCards;
