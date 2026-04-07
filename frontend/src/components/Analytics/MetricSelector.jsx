/**
 * MetricSelector Component
 * 
 * Memoized metric selection panel for Analytics page.
 */
import React, { memo, useCallback } from 'react';
import { METRIC_GROUPS } from '../../constants/analyticsConfig';

const MetricSelector = memo(function MetricSelector({
    selectedMetrics,
    onToggleMetric, // Make sure it's in the args!
    language = 'zh',
    onClose,
    onToggle
}) {
    // Debug props in production
    console.log('[MetricSelector] Props received:', { 
        hasToggle: typeof onToggleMetric === 'function' || typeof onToggle === 'function',
        onToggleMetricType: typeof onToggleMetric,
        onToggleType: typeof onToggle
    });

    const activeToggle = onToggleMetric || onToggle;
    const styles = {
        overlay: {
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.6)',
            backdropFilter: 'blur(4px)',
            zIndex: 100,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
        },
        panel: {
            backgroundColor: 'var(--glass-bg, #1a1b1e)',
            border: '1px solid var(--glass-border, rgba(255,255,255,0.1))',
            borderRadius: '16px',
            padding: '24px',
            maxWidth: '800px',
            maxHeight: '80vh',
            overflow: 'auto',
            width: '90%',
        },
        header: {
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '20px',
        },
        title: {
            fontSize: '1.25rem',
            fontWeight: '600',
            color: 'var(--text-primary)',
        },
        closeBtn: {
            background: 'none',
            border: 'none',
            color: 'var(--text-secondary)',
            fontSize: '1.5rem',
            cursor: 'pointer',
            padding: '4px 8px',
        },
        groupsGrid: {
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '16px',
        },
        groupCard: (color) => ({
            backgroundColor: 'rgba(255, 255, 255, 0.03)',
            border: `1px solid ${color}40`,
            borderRadius: '12px',
            padding: '16px',
        }),
        groupHeader: (color) => ({
            fontSize: '0.875rem',
            fontWeight: '600',
            color: color,
            marginBottom: '12px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
        }),
        colorDot: (color) => ({
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: color,
        }),
        metricList: {
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
        },
        metricItem: {
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            cursor: 'pointer',
        },
        checkbox: {
            width: '14px',
            height: '14px',
            accentColor: '#3b82f6',
            cursor: 'pointer',
        },
        label: {
            fontSize: '0.8rem',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
        },
    };

    const handleToggle = useCallback((groupId, metricKey) => {
        if (typeof activeToggle === 'function') {
            activeToggle(groupId, metricKey);
        } else {
            console.error('[MetricSelector] No toggle function provided!');
        }
    }, [activeToggle]);

    return (
        <div style={styles.overlay} onClick={onClose}>
            <div style={styles.panel} onClick={(e) => e.stopPropagation()}>
                <div style={styles.header}>
                    <h3 style={styles.title}>
                        {language === 'zh' ? '選擇指標' : 'Select Metrics'}
                    </h3>
                    <button style={styles.closeBtn} onClick={onClose}>×</button>
                </div>

                <div style={styles.groupsGrid}>
                    {METRIC_GROUPS.map((group) => (
                        <div key={group.id} style={styles.groupCard(group.color)}>
                            <div style={styles.groupHeader(group.color)}>
                                <span style={styles.colorDot(group.color)} />
                                {language === 'zh' ? group.label_zh : group.label_en}
                            </div>
                            <div style={styles.metricList}>
                                {group.metrics.map((metric) => {
                                    const compositeKey = `${group.id}:${metric.key}`;
                                    const isChecked = selectedMetrics.has(compositeKey);

                                    return (
                                        <label
                                            key={metric.key}
                                            style={styles.metricItem}
                                        >
                                            <input
                                                type="checkbox"
                                                checked={isChecked}
                                                onChange={() => handleToggle(group.id, metric.key)}
                                                style={styles.checkbox}
                                            />
                                            <span style={styles.label}>
                                                {language === 'zh' ? metric.label_zh : metric.label_en}
                                            </span>
                                        </label>
                                    );
                                })}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
});

export default MetricSelector;
