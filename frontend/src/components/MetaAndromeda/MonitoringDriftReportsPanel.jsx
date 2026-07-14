import React from 'react';

import {
    detailCardStyle,
    panelStyle,
    sectionTitleStyle,
} from './shared';

export const MonitoringDriftReportsPanel = ({ isMobile, monitoring }) => {
    const {
        summary,
        t,
        getTranslation,
        formatDateTime,
        setSelectedDriftReport,
        setExcludedObsIds,
    } = monitoring;

    return (
                        <section style={{ ...panelStyle, gridColumn: isMobile ? undefined : 'span 2' }}>
                            <h2 style={sectionTitleStyle}>{t('Latest Drift Reports', '最近預估偏差報告')}</h2>
                            <div 
                                className="queue-scroll-box"
                                style={{ 
                                    display: 'grid', 
                                    gap: '10px', 
                                    marginBottom: '14px',
                                    maxHeight: '400px',
                                    overflowY: 'auto',
                                    paddingRight: '6px'
                                }}
                            >
                                {(summary?.latest_drift_reports || []).map((report) => {
                                    const accuracy = report.report_payload?.accuracy;
                                    const mae = report.report_payload?.mae;
                                    const spearmanR = report.report_payload?.spearman_r;
                                    const periodDiagnosis = report.report_payload?.period_diagnosis;
                                    const dominantMetric = report.report_payload?.dominant_metric;
                                    const metricDistribution = report.report_payload?.metric_distribution;
                                    const details = report.report_payload?.matched_details || [];
                                    const totalObserved = report.report_payload?.total_observed;
                                    const totalMatched = report.report_payload?.total_matched;
                                    const calibrationCandidates = report.report_payload?.calibration_candidate_total;
                                    const roasThresholds = report.report_payload?.roas_band_thresholds;
                                    const hasDetails = details.length > 0;
                                    
                                    // 狀態樣式與呼吸燈效果
                                    const isDrifted = report.drift_status === 'drifted';
                                    const isStable = report.drift_status === 'stable';
                                    const statusColor = isStable ? '#10b981' : (report.drift_status === 'warning' ? '#f59e0b' : '#ef4444');
                                    
                                    return (
                                        <div key={report.drift_report_id} style={{
                                            ...detailCardStyle,
                                            position: 'relative',
                                            overflow: 'hidden'
                                        }}>
                                            {/* 偏差呼吸燈 */}
                                            {isDrifted && (
                                                <div style={{
                                                    position: 'absolute',
                                                    top: '12px',
                                                    right: '12px',
                                                    width: '10px',
                                                    height: '10px',
                                                    borderRadius: '50%',
                                                    background: '#ef4444',
                                                    boxShadow: '0 0 10px #ef4444',
                                                    animation: 'pulse 1.5s infinite'
                                                }} />
                                            )}
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '8px' }}>
                                                <div style={{ color: statusColor, fontWeight: 700, marginBottom: '6px' }}>
                                                    {getTranslation(report.window_kind)}
                                                    {report.window_kind === 'custom' && (() => {
                                                        const since = report.report_payload?.since;
                                                        const until = report.report_payload?.until;
                                                        if (since && until) {
                                                            return ` (${since} ~ ${until})`;
                                                        }
                                                        if (report.note && report.note.includes('~')) {
                                                            const match = report.note.match(/(\d{4}-\d{2}-\d{2})\s*~\s*(\d{4}-\d{2}-\d{2})/);
                                                            if (match) {
                                                                return ` (${match[1]} ~ ${match[2]})`;
                                                            }
                                                        }
                                                        return '';
                                                    })()} · {getTranslation(report.drift_status)}
                                                </div>
                                                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
                                                    {spearmanR !== undefined && spearmanR !== null && (
                                                        <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                                            ρ = {spearmanR.toFixed(3)} · {t('Accuracy', '準確率')}: {(accuracy * 100).toFixed(1)}% | {t('MAE', '平均絕對偏差')}: {mae.toFixed(2)}
                                                        </span>
                                                    )}
                                                    {(spearmanR === undefined || spearmanR === null) && accuracy !== undefined && (
                                                        <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                                            {t('Accuracy', '準確率')}: {(accuracy * 100).toFixed(1)}% | {t('MAE', '平均絕對偏差')}: {mae.toFixed(2)}
                                                        </span>
                                                    )}
                                                    <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                                                        {t('Observed', '匯入')}: {totalObserved ?? '--'} · {t('Matched', '配對成功')}: {totalMatched ?? '--'} · {t('Calibration Candidates', '可校準')}: {calibrationCandidates ?? '--'}
                                                    </span>
                                                    <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                                                        {t('Run Time', '執行時間')}: {formatDateTime(report.created_at)}
                                                    </span>
                                                </div>
                                            </div>
                                            {roasThresholds && (
                                                <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                                                    {t('ROAS Band', 'ROAS 門檻')}: low &lt; {roasThresholds.low_below} · mid {roasThresholds.low_below}–{roasThresholds.high_above} · high ≥ {roasThresholds.high_above}
                                                    {roasThresholds.method === 'percentile_p33_p67'
                                                        ? ` (P33/P67, n=${roasThresholds.sample_count})`
                                                        : ` (${t('fixed fallback', '固定門檻')})`}
                                                    {dominantMetric && dominantMetric !== 'roas' && (
                                                        <span> · {t('Primary metric', '主指標')}: {dominantMetric.toUpperCase()}</span>
                                                    )}
                                                    {metricDistribution && Object.keys(metricDistribution).length > 1 && (
                                                        <span> · {t('Mixed objectives', '混合目標')}: {Object.entries(metricDistribution).map(([k, v]) => `${k.toUpperCase()}×${v}`).join(', ')}</span>
                                                    )}
                                                </div>
                                            )}
                                            <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6, fontSize: '0.88rem', marginBottom: '8px' }}>{report.summary}</div>
                                            {periodDiagnosis && (() => {
                                                const stateColors = {
                                                    dual_advantage:  { bg: 'rgba(16,185,129,0.07)',  border: 'rgba(16,185,129,0.3)',  text: '#34d399' },
                                                    market_driven:   { bg: 'rgba(59,130,246,0.07)',  border: 'rgba(59,130,246,0.3)',  text: '#60a5fa' },
                                                    creative_critical:{ bg: 'rgba(245,158,11,0.07)', border: 'rgba(245,158,11,0.3)', text: '#f59e0b' },
                                                    needs_review:    { bg: 'rgba(239,68,68,0.07)',   border: 'rgba(239,68,68,0.3)',   text: '#f87171' },
                                                };
                                                const c = stateColors[periodDiagnosis.state] || stateColors.needs_review;
                                                return (
                                                    <div style={{
                                                        marginBottom: '8px',
                                                        padding: '10px 14px',
                                                        borderRadius: '10px',
                                                        background: c.bg,
                                                        border: `1px solid ${c.border}`,
                                                    }}>
                                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                                                            <span style={{ fontWeight: 700, fontSize: '0.85rem', color: c.text }}>
                                                                {t('Campaign State', '投放狀態')}: {periodDiagnosis.label}
                                                            </span>
                                                            <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                                                                ρ² = {(periodDiagnosis.creative_explained_variance * 100).toFixed(1)}%
                                                                {t(' of performance variance explained by creative', ' 的績效差異由創意品質解釋')}
                                                            </span>
                                                        </div>
                                                        <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                                            {periodDiagnosis.recommendation}
                                                        </div>
                                                    </div>
                                                );
                                            })()}
                                            
                                            {hasDetails && (
                                                <button
                                                    type="button"
                                                    onClick={() => {
                                                        setSelectedDriftReport(report);
                                                        setExcludedObsIds(new Set());
                                                    }}
                                                    style={{
                                                        marginTop: '6px',
                                                        padding: '6px 12px',
                                                        borderRadius: '6px',
                                                        border: '1px solid var(--glass-border)',
                                                        background: 'rgba(255,255,255,0.05)',
                                                        color: 'var(--text-primary)',
                                                        fontSize: '0.8rem',
                                                        cursor: 'pointer',
                                                        transition: 'all 0.2s'
                                                    }}
                                                    onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.1)'}
                                                    onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
                                                >
                                                    {t('View Diagnostic Details', '查看診斷明細')}
                                                </button>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </section>
    );
};
