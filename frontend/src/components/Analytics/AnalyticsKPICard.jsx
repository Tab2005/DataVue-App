/**
 * AnalyticsKPICard Component
 * 
 * Memoized KPI card for Analytics page.
 * Optimized to prevent unnecessary re-renders.
 */
import React, { memo } from 'react';

const AnalyticsKPICard = memo(function AnalyticsKPICard({
    label,
    value,
    prevValue,
    change,
    format = 'number',
    color = '#3b82f6',
    isInverse = false,
    language = 'zh'
}) {
    // Format value based on type
    const formatValue = (val, fmt) => {
        if (val === null || val === undefined || isNaN(val)) return '-';

        const num = parseFloat(val);
        switch (fmt) {
            case 'currency':
                // For amounts >= 10, remove decimals. For smaller ones (like CPC), keep them if they are non-zero.
                if (num >= 10 || Number.isInteger(num)) {
                    return `$${num.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
                }
                return `$${num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            case 'percent':
                return `${num.toFixed(2)}%`;
            case 'decimal':
                return num.toFixed(2);
            default:
                return num >= 1000000
                    ? `${(num / 1000000).toFixed(1)}M`
                    : num >= 1000
                        ? `${(num / 1000).toFixed(1)}K`
                        : num.toLocaleString();
        }
    };

    // Calculate change percentage
    const changeNum = parseFloat(change) || 0;
    const isPositive = isInverse ? changeNum < 0 : changeNum > 0;
    const isNeutral = changeNum === 0;

    const styles = {
        card: {
            background: 'rgba(255, 255, 255, 0.03)',
            borderRadius: '12px',
            padding: '16px',
            border: `1px solid ${color}20`,
            borderLeft: `3px solid ${color}`,
            transition: 'transform 0.2s, box-shadow 0.2s',
        },
        label: {
            fontSize: '0.75rem',
            color: 'var(--text-secondary)',
            marginBottom: '8px',
            display: 'block',
        },
        value: {
            fontSize: '1.5rem',
            fontWeight: '700',
            color: 'var(--text-primary)',
            marginBottom: '4px',
        },
        change: {
            fontSize: '0.75rem',
            fontWeight: '500',
            color: isNeutral ? 'var(--text-secondary)' : isPositive ? '#10b981' : '#ef4444',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
        },
        prevValue: {
            fontSize: '0.7rem',
            color: 'var(--text-secondary)',
            marginLeft: '8px',
        }
    };

    return (
        <div
            style={styles.card}
            onMouseOver={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = `0 4px 12px ${color}20`;
            }}
            onMouseOut={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
            }}
        >
            <span style={styles.label}>{label}</span>
            <div style={styles.value}>{formatValue(value, format)}</div>
            <div style={styles.change}>
                {!isNeutral && (
                    <span>{changeNum > 0 ? '▲' : '▼'}</span>
                )}
                <span>{change || '0%'}</span>
                {prevValue !== undefined && (
                    <span style={styles.prevValue}>
                        ({formatValue(prevValue, format)})
                    </span>
                )}
            </div>
        </div>
    );
});

/**
 * AnalyticsKPISection Component
 * 
 * Container for KPI cards with memoization.
 */
export const AnalyticsKPISection = memo(function AnalyticsKPISection({
    summary,
    activeColumns,
    language = 'zh',
    isMobile = false
}) {
    if (!summary || Object.keys(summary).length === 0) {
        return (
            <div style={{ textAlign: 'center', padding: '20px', color: 'var(--text-secondary)' }}>
                {language === 'zh' ? '無資料可顯示' : 'No data to display'}
            </div>
        );
    }

    const styles = {
        grid: {
            display: 'grid',
            gridTemplateColumns: isMobile
                ? 'repeat(2, 1fr)'
                : 'repeat(auto-fit, minmax(160px, 1fr))',
            gap: '12px',
            marginBottom: '24px',
        }
    };

    return (
        <div style={styles.grid}>
            {activeColumns.map((col) => {
                const data = summary[col.key];
                if (!data) return null;

                return (
                    <AnalyticsKPICard
                        key={col.key}
                        label={language === 'zh' ? col.label_zh : col.label_en}
                        value={data.value}
                        prevValue={data.previous}
                        change={data.change}
                        format={col.format}
                        color={col.groupColor || '#3b82f6'}
                        isInverse={col.isInverse}
                        language={language}
                    />
                );
            })}
        </div>
    );
});

export default AnalyticsKPICard;
