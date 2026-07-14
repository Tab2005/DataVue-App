import React from 'react';

import {
    Metric,
    badgeStyle,
    detailCardStyle,
} from './shared';

export const MonitoringDriftDiagnosticsDrawer = ({ isMobile, monitoring }) => {
    const {
        selectedDriftReport,
        setSelectedDriftReport,
        excludedObsIds,
        setExcludedObsIds,
        syncingCal,
        t,
        getTranslation,
        handleToggleExcludeObs,
        handleSyncCalibration,
    } = monitoring;

    return (
        <>
            {/* 預估偏差診斷 Slide-over 滑出面板 */}
            <div style={{
                position: 'fixed',
                top: 0,
                right: selectedDriftReport ? 0 : '-500px', // Slide in/out
                width: isMobile ? '100%' : '500px',
                height: '100vh',
                backgroundColor: 'var(--bg-secondary)',
                boxShadow: selectedDriftReport ? '-4px 0 24px rgba(0,0,0,0.6)' : 'none',
                transition: 'right 0.3s ease',
                zIndex: 2000,
                display: 'flex',
                flexDirection: 'column',
                borderLeft: '1px solid var(--glass-border)',
                backdropFilter: 'blur(20px)',
            }}>
                {/* Header */}
                <div style={{
                    padding: '16px',
                    borderBottom: '1px solid var(--glass-border)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    background: 'var(--bg-primary)'
                }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                        <div style={{ fontWeight: 'bold', fontSize: '1.05rem', color: 'var(--text-primary)' }}>
                            {t('Drift Diagnostics Workspace', '預估偏差診斷工作台')}
                        </div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                            {selectedDriftReport ? `${getTranslation(selectedDriftReport.window_kind)} · ${t('Accuracy', '準確率')}: ${(selectedDriftReport.report_payload?.accuracy * 100).toFixed(1)}%` : ''}
                        </div>
                    </div>
                    <button
                        onClick={() => {
                            setSelectedDriftReport(null);
                            setExcludedObsIds(new Set());
                        }}
                        style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '1.2rem' }}
                    >
                        ✕
                    </button>
                </div>

                {/* Content */}
                <div style={{ flex: 1, overflowY: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                    {selectedDriftReport && (
                        <>
                            {/* 同步工具區 */}
                            <div style={{
                                padding: '14px',
                                borderRadius: '12px',
                                background: 'rgba(99, 102, 241, 0.08)',
                                border: '1px solid rgba(99, 102, 241, 0.18)',
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '8px'
                            }}>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
                                    <Metric
                                        label={t('Observed', '匯入')}
                                        value={selectedDriftReport.report_payload?.total_observed}
                                    />
                                    <Metric
                                        label={t('Matched', '配對成功')}
                                        value={selectedDriftReport.report_payload?.total_matched}
                                    />
                                    <Metric
                                        label={t('Calibration Candidates', '可校準')}
                                        value={selectedDriftReport.report_payload?.calibration_candidate_total}
                                    />
                                </div>
                                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                                    {t('Package observed creatives with prediction errors into a dataset to calibrate Gemini runtime model.', '將有預測偏差的觀測素材打包同步為校準資料集，可用於微調與校準 Gemini 創意預估模型。')}
                                </div>
                                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                                    {t(
                                        'The counts above belong to the observation import line only and are separate from standalone Score Lab submissions.',
                                        '上方這些數字只屬於 observation 匯入這條線，與 Score Lab 單獨送評的素材統計分開。'
                                    )}
                                </div>
                                <button
                                    type="button"
                                    onClick={handleSyncCalibration}
                                    disabled={syncingCal || (selectedDriftReport.report_payload?.matched_details || []).filter(tc => !excludedObsIds.has(tc.id) && tc.error > 0).length === 0}
                                    style={{
                                        alignSelf: 'flex-start',
                                        padding: '8px 16px',
                                        borderRadius: '8px',
                                        border: 'none',
                                        background: 'var(--accent-primary)',
                                        color: 'white',
                                        fontWeight: 600,
                                        fontSize: '0.82rem',
                                        cursor: syncingCal ? 'wait' : 'pointer',
                                        opacity: (syncingCal || (selectedDriftReport.report_payload?.matched_details || []).filter(tc => !excludedObsIds.has(tc.id) && tc.error > 0).length === 0) ? 0.5 : 1,
                                    }}
                                >
                                    {syncingCal ? t('Syncing...', '同步中...') : t('Package & Sync Dataset', '打包並同步校準資料集')}
                                </button>
                            </div>

                            {/* 廣告對照列表 */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                                <div style={{ fontSize: '0.88rem', fontWeight: 'bold', color: 'var(--text-primary)' }}>
                                    {t('Prediction vs Observation Comparison', '預估與實際績效對比')}
                                </div>
                                
                                {(selectedDriftReport.report_payload?.matched_details || []).map((item) => {
                                    const isExcluded = excludedObsIds.has(item.id);
                                    const hasError = item.error > 0;
                                    
                                    // Band styling mapping
                                    const getBandStyle = (band) => {
                                        if (band === 'high') return { background: 'rgba(168, 85, 247, 0.15)', color: '#c084fc', border: '1px solid rgba(168, 85, 247, 0.3)' };
                                        if (band === 'mid') return { background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa', border: '1px solid rgba(59, 130, 246, 0.3)' };
                                        return { background: 'rgba(107, 114, 128, 0.15)', color: '#9ca3af', border: '1px solid rgba(107, 114, 128, 0.3)' };
                                    };

                                    const predStyle = getBandStyle(item.prediction_band);
                                    const obsStyle = getBandStyle(item.observed_band);
                                    
                                    return (
                                        <div key={item.id} style={{
                                            ...detailCardStyle,
                                            opacity: isExcluded ? 0.4 : 1,
                                            border: isExcluded ? '1px dashed var(--glass-border)' : (hasError ? '1px solid rgba(239, 68, 68, 0.25)' : '1px solid var(--glass-border)'),
                                            background: hasError && !isExcluded ? 'rgba(239, 68, 68, 0.02)' : 'rgba(255,255,255,0.02)',
                                            transition: 'all 0.2s'
                                        }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                                                <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.88rem', maxWidth: '75%', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={item.ad_name}>
                                                    {item.ad_name || item.ad_id}
                                                </div>
                                                <button
                                                    type="button"
                                                    onClick={() => handleToggleExcludeObs(item.id)}
                                                    style={{
                                                        background: 'transparent',
                                                        border: 'none',
                                                        color: isExcluded ? 'var(--accent-primary)' : 'var(--text-secondary)',
                                                        fontSize: '0.78rem',
                                                        cursor: 'pointer',
                                                        fontWeight: 600
                                                    }}
                                                >
                                                    {isExcluded ? t('Include', '加入') : t('Exclude', '排除')}
                                                </button>
                                            </div>

                                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                                                {/* Prediction */}
                                                <div style={{ ...badgeStyle, ...predStyle }}>
                                                    {t('Pred: ', '預估: ')}{getTranslation(item.prediction_band)}
                                                </div>
                                                
                                                {/* Connection arrow */}
                                                <span style={{ color: hasError ? '#ef4444' : 'var(--text-secondary)', fontSize: '0.9rem' }}>
                                                    {hasError ? '⚡' : '→'}
                                                </span>

                                                {/* Observation */}
                                                <div style={{ ...badgeStyle, ...obsStyle }}>
                                                    {t('Obs: ', '實際: ')}{getTranslation(item.observed_band)}
                                                </div>

                                                <span style={{ fontSize: '0.8rem', marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                    <span style={{ color: 'var(--text-secondary)' }}>
                                                        ROAS: {typeof item.real_roas === 'number' ? item.real_roas.toFixed(2) : '—'}
                                                    </span>
                                                    {item.real_spend !== undefined && (
                                                        <span style={{
                                                            color: item.real_spend <= 0 ? '#ef4444' : 'var(--text-secondary)',
                                                            fontSize: '0.75rem',
                                                        }}>
                                                            {item.real_spend <= 0
                                                                ? t('spend=$0 ⚠', '花費=$0 ⚠')
                                                                : `spend=$${item.real_spend.toFixed(0)}`}
                                                        </span>
                                                    )}
                                                </span>
                                            </div>

                                            {hasError && !isExcluded && (() => {
                                                const bandOrder = { low: 1, mid: 2, high: 3 };
                                                const predVal = bandOrder[item.prediction_band] || 0;
                                                const obsVal = bandOrder[item.observed_band] || 0;
                                                const isOver = predVal > obsVal;
                                                
                                                return (
                                                    <div style={{ fontSize: '0.75rem', color: '#ef4444', marginTop: '6px', fontStyle: 'italic' }}>
                                                        ⚠ {isOver 
                                                            ? t(`Overestimated by ${item.error} bands`, `預估偏高 ${item.error} 個級距`)
                                                            : t(`Underestimated by ${item.error} bands`, `預估偏低 ${item.error} 個級距`)}
                                                    </div>
                                                );
                                            })()}
                                        </div>
                                    );
                                })}
                            </div>
                        </>
                    )}
                </div>
            </div>

            {/* Backdrop */}
            {selectedDriftReport && (
                <div
                    onClick={() => {
                        setSelectedDriftReport(null);
                        setExcludedObsIds(new Set());
                    }}
                    style={{
                        position: 'fixed',
                        top: 0, left: 0, right: 0, bottom: 0,
                        background: 'rgba(0,0,0,0.5)',
                        zIndex: 1999,
                        backdropFilter: 'blur(2px)'
                    }}
                />
            )}
        </>
    );
};
