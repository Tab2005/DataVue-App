import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';

import { usePermission } from '../hooks/usePermission';
import {
    approveMetaAndromedaRelease,
    fetchMetaAndromedaReleaseOverview,
    rejectMetaAndromedaRelease,
    rollbackMetaAndromedaRelease,
} from '../services/metaAndromedaReleaseService';
import { fetchMetaAndromedaMonitoringSummary } from '../services/metaAndromedaMonitoringService';

const MetaAndromedaRelease = () => {
    const { isMobile, language, selectedTeamId } = useOutletContext();
    const [overview, setOverview] = useState(null);
    const [driftReport, setDriftReport] = useState(null);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);
    const [actionMessage, setActionMessage] = useState(null);
    const { hasPermission: canRelease, loading: loadingReleasePermission } = usePermission('meta_andromeda:release', selectedTeamId);

    const t = (en, zh) => (language === 'en' ? en : zh);

    const loadOverview = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await fetchMetaAndromedaReleaseOverview();
            setOverview(data);
            try {
                const monitoringData = await fetchMetaAndromedaMonitoringSummary();
                if (monitoringData && monitoringData.latest_drift_reports && monitoringData.latest_drift_reports.length > 0) {
                    setDriftReport(monitoringData.latest_drift_reports[0]);
                } else {
                    setDriftReport(null);
                }
            } catch (monErr) {
                console.error('Failed to load monitoring summary', monErr);
            }
        } catch (err) {
            setError(err.message || 'Failed to load release overview');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadOverview();
    }, []);

    const handleReleaseAction = async (action, modelVersion) => {
        const note = window.prompt(
            t('Optional note for this action', '請輸入這次操作的備註（可留空）'),
            ''
        );

        setSubmitting(true);
        setError(null);
        setActionMessage(null);
        try {
            const payload = { model_version: modelVersion, note: note || null };
            const result = action === 'approve'
                ? await approveMetaAndromedaRelease(payload)
                : action === 'reject'
                    ? await rejectMetaAndromedaRelease(payload)
                    : await rollbackMetaAndromedaRelease(payload);
            setActionMessage(`${result.action}: ${result.model_version}`);
            await loadOverview();
        } catch (err) {
            setError(err.message || 'Failed to execute release action');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div style={{ padding: isMobile ? '16px' : '24px' }}>
            <div style={{ marginBottom: '20px' }}>
                <div style={{ color: 'var(--accent-primary)', fontWeight: 700, marginBottom: '8px' }}>
                    Meta Andromeda
                </div>
                <h1 style={{ margin: 0, color: 'var(--text-primary)' }}>
                    {t('Release Overview', '版本釋出總覽')}
                </h1>
            </div>

            {actionMessage ? <div style={successPanelStyle}>{actionMessage}</div> : null}
            {loading ? (
                <div style={panelStyle}>{t('Loading release overview...', '載入版本總覽中...')}</div>
            ) : error ? (
                <div style={errorPanelStyle}>{error}</div>
            ) : (
                <>
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: isMobile ? '1fr' : 'repeat(2, 1fr)',
                        gap: '16px',
                        marginBottom: '16px'
                    }}>
                        <section style={panelStyle}>
                            <h2 style={sectionTitleStyle}>{t('Current Production', '目前 Production')}</h2>
                            <ReleaseRecordCard record={overview?.current_production} />
                            {!loadingReleasePermission && canRelease ? (
                                <button
                                    type="button"
                                    style={{ ...buttonSecondaryStyle, marginTop: '16px' }}
                                    disabled={submitting}
                                    onClick={() => handleReleaseAction('rollback', overview?.current_production?.model_version)}
                                >
                                    {submitting ? t('Submitting...', '送出中...') : t('Rollback to Previous', '回滾到前一版')}
                                </button>
                            ) : null}
                        </section>
                        <section style={panelStyle}>
                            <h2 style={sectionTitleStyle}>{t('Previous Production', '前一版 Production')}</h2>
                            <ReleaseRecordCard record={overview?.previous_production} />
                        </section>
                    </div>

                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: isMobile ? '1fr' : '1.1fr 0.9fr',
                        gap: '16px'
                    }}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                            {/* 線上實測對照證據面板 */}
                            <section style={panelStyle}>
                                <h2 style={sectionTitleStyle}>{t('Online Performance Evidence', '線上實測對照證據')}</h2>
                                {!driftReport ? (
                                    <div style={emptyStateStyle}>
                                        {t('No recent drift reports found.', '目前無最新漂移報告。')}
                                    </div>
                                ) : (
                                    <div style={{ display: 'grid', gap: '12px' }}>
                                        <div style={{
                                            ...detailCardStyle,
                                            border: driftReport.drift_status === 'drifted' ? '1px solid rgba(239, 68, 68, 0.3)' : '1px solid var(--glass-border)',
                                            background: driftReport.drift_status === 'drifted' ? 'rgba(239, 68, 68, 0.02)' : 'rgba(255, 255, 255, 0.02)',
                                        }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                                                <div style={{ fontWeight: 'bold', fontSize: '0.95rem', color: 'var(--text-primary)' }}>
                                                    {t('Status: ', '報告狀態: ')}
                                                    <span style={{
                                                        color: driftReport.drift_status === 'drifted' ? '#ef4444' : driftReport.drift_status === 'warning' ? '#f59e0b' : '#10b981',
                                                        marginLeft: '6px'
                                                    }}>
                                                        {driftReport.drift_status.toUpperCase()}
                                                    </span>
                                                </div>
                                                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                                    {driftReport.window_kind}
                                                </div>
                                            </div>

                                            <div style={metricGridStyle}>
                                                <Metric
                                                    label={t('Accuracy', '預測準確率')}
                                                    value={driftReport.report_payload?.accuracy !== undefined ? `${(driftReport.report_payload.accuracy * 100).toFixed(1)}%` : '--'}
                                                />
                                                <Metric
                                                    label={t('MAE', '平均絕對偏差')}
                                                    value={driftReport.report_payload?.mae !== undefined ? driftReport.report_payload.mae.toFixed(2) : '--'}
                                                />
                                            </div>

                                            <div style={{ marginTop: '10px', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                                {t('Triggered by: ', '觸發人員: ')}{driftReport.triggered_by} · {new Date(driftReport.created_at).toLocaleString()}
                                            </div>

                                            {driftReport.drift_status === 'drifted' && (
                                                <div style={{
                                                    marginTop: '10px',
                                                    color: '#ef4444',
                                                    fontSize: '0.85rem',
                                                    lineHeight: 1.5,
                                                    background: 'rgba(239, 68, 68, 0.08)',
                                                    padding: '10px',
                                                    borderRadius: '8px',
                                                    border: '1px solid rgba(239, 68, 68, 0.15)'
                                                }}>
                                                    ⚠️ {t(
                                                        'Online model detected significant drift. Release functionality is locked to prevent degraded inference quality. Please perform calibration inside the Monitoring Console first.',
                                                        '線上模型已檢測出顯著漂移。為了避免劣質預估，已自動鎖定發佈。請先進入監控工作台執行「資料校準」。'
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </section>

                            {/* 候選版本 */}
                            <section style={panelStyle}>
                                <h2 style={sectionTitleStyle}>{t('Candidates', '候選版本')}</h2>
                                <div style={{ display: 'grid', gap: '12px' }}>
                                    {(overview?.candidates || []).map((candidate) => {
                                        const isDrifted = driftReport?.drift_status === 'drifted';
                                        return (
                                            <div key={candidate.model_version} style={detailCardStyle}>
                                                <div style={{ color: 'var(--text-primary)', fontWeight: 700, marginBottom: '8px' }}>
                                                    {candidate.model_version}
                                                </div>
                                                <div style={{ display: 'grid', gap: '8px', color: 'var(--text-secondary)' }}>
                                                    <div>status: {candidate.release_status}</div>
                                                    <div>pairwise_ranking_accuracy: {candidate.pairwise_ranking_accuracy}</div>
                                                    <div>mean_band_error: {candidate.mean_band_error}</div>
                                                </div>
                                                <div style={{ display: 'grid', gap: '6px', marginTop: '12px', fontSize: '0.9rem' }}>
                                                    {Object.entries(candidate.promotion_gate_summary || {}).map(([key, value]) => (
                                                        <div key={key} style={gateRowStyle}>
                                                            <span style={{ color: 'var(--text-secondary)' }}>{key}</span>
                                                            <strong style={{ color: value ? '#10b981' : '#ef4444' }}>
                                                                {String(value)}
                                                            </strong>
                                                        </div>
                                                    ))}
                                                </div>
                                                {!loadingReleasePermission && canRelease ? (
                                                    <div style={{ display: 'flex', gap: '10px', marginTop: '16px', flexWrap: 'wrap', flexDirection: 'column' }}>
                                                        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                                                            <button
                                                                type="button"
                                                                style={{
                                                                    ...buttonPrimaryStyle,
                                                                    opacity: isDrifted ? 0.4 : 1,
                                                                    cursor: isDrifted ? 'not-allowed' : 'pointer'
                                                                }}
                                                                disabled={submitting || isDrifted}
                                                                onClick={() => handleReleaseAction('approve', candidate.model_version)}
                                                                title={isDrifted ? t('Locked due to online model drift', '因線上模型漂移而鎖定發佈') : ''}
                                                            >
                                                                {t('Approve', '批准')}
                                                            </button>
                                                            <button
                                                                type="button"
                                                                style={buttonSecondaryStyle}
                                                                disabled={submitting}
                                                                onClick={() => handleReleaseAction('reject', candidate.model_version)}
                                                            >
                                                                {t('Reject', '退回')}
                                                            </button>
                                                        </div>
                                                        {isDrifted && (
                                                            <div style={{
                                                                color: '#ef4444',
                                                                fontSize: '0.82rem',
                                                                lineHeight: 1.5,
                                                                background: 'rgba(239, 68, 68, 0.08)',
                                                                padding: '10px',
                                                                borderRadius: '8px',
                                                                border: '1px solid rgba(239, 68, 68, 0.2)',
                                                                marginTop: '8px',
                                                                alignSelf: 'stretch'
                                                            }}>
                                                                ⚠️ {t(
                                                                    `Online model detected significant drift (Accuracy: ${(driftReport?.report_payload?.accuracy * 100).toFixed(1)}% < 60%). Release has been automatically locked to prevent poor predictions. Please run "Data Calibration" in the monitoring workshop before approving new models.`,
                                                                    `線上模型已檢測出顯著漂移 (Accuracy: ${(driftReport?.report_payload?.accuracy * 100).toFixed(1)}% < 60%)。為了避免劣質預估，已自動鎖定發佈。請先進入監控工作台執行「資料校準」，再行核准新模型。`
                                                                )}
                                                            </div>
                                                        )}
                                                    </div>
                                                ) : null}
                                            </div>
                                        );
                                    })}
                                </div>
                            </section>
                        </div>

                        <section style={panelStyle}>
                            <h2 style={sectionTitleStyle}>{t('Release History', '版本歷史')}</h2>
                            <div style={{ display: 'grid', gap: '12px', marginBottom: '16px' }}>
                                {(overview?.history || []).map((item, index) => (
                                    <div key={index} style={detailCardStyle}>
                                        <div style={{ color: 'var(--accent-primary)', fontWeight: 700, marginBottom: '6px' }}>
                                            {item.action} · {item.model_version}
                                        </div>
                                        <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                            {item.actor} · {item.created_at}
                                        </div>
                                        <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6, marginTop: '6px' }}>
                                            {item.note || '--'}
                                        </div>
                                    </div>
                                ))}
                            </div>
                            <div style={{ display: 'grid', gap: '8px' }}>
                                {(overview?.notes || []).map((note, index) => (
                                    <div key={index} style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                        {note}
                                    </div>
                                ))}
                            </div>
                            {!loadingReleasePermission && !canRelease ? (
                                <div style={infoPanelStyle}>
                                    {t(
                                        'Release actions require meta_andromeda:release. You currently have read-only visibility.',
                                        '執行 release action 需要 meta_andromeda:release 權限，目前你只有唯讀可見權。'
                                    )}
                                </div>
                            ) : null}
                        </section>
                    </div>
                </>
            )}
        </div>
    );
};

const ReleaseRecordCard = ({ record }) => {
    if (!record) {
        return <div style={{ color: 'var(--text-secondary)' }}>--</div>;
    }

    return (
        <div style={{ display: 'grid', gap: '10px' }}>
            <div style={detailCardStyle}>
                <div style={{ color: 'var(--text-secondary)', marginBottom: '6px' }}>model_version</div>
                <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{record.model_version}</div>
            </div>
            <div style={metricGridStyle}>
                <Metric label="status" value={record.release_status} />
                <Metric label="approved_by" value={record.approved_by} />
                <Metric label="pairwise_ranking_accuracy" value={record.pairwise_ranking_accuracy} />
                <Metric label="mean_band_error" value={record.mean_band_error} />
            </div>
        </div>
    );
};

const Metric = ({ label, value }) => (
    <div style={detailCardStyle}>
        <div style={{ color: 'var(--text-secondary)', marginBottom: '6px', fontSize: '0.85rem' }}>{label}</div>
        <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{value ?? '--'}</div>
    </div>
);

const panelStyle = {
    background: 'var(--bg-secondary)',
    border: '1px solid var(--glass-border)',
    borderRadius: '16px',
    padding: '24px',
};

const sectionTitleStyle = {
    margin: '0 0 16px 0',
    color: 'var(--text-primary)',
    fontSize: '1rem',
};

const metricGridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: '12px',
};

const detailCardStyle = {
    padding: '14px',
    borderRadius: '12px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.02)',
};

const gateRowStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
};

const buttonPrimaryStyle = {
    padding: '12px 16px',
    borderRadius: '10px',
    border: 'none',
    background: 'var(--accent-primary)',
    color: 'white',
    cursor: 'pointer',
};

const buttonSecondaryStyle = {
    padding: '12px 16px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.02)',
    color: 'var(--text-primary)',
    cursor: 'pointer',
};

const errorPanelStyle = {
    marginBottom: '16px',
    padding: '16px',
    borderRadius: '12px',
    background: 'rgba(239, 68, 68, 0.08)',
    border: '1px solid rgba(239, 68, 68, 0.18)',
    color: 'var(--text-primary)',
};

const successPanelStyle = {
    marginBottom: '16px',
    padding: '16px',
    borderRadius: '12px',
    background: 'rgba(16, 185, 129, 0.12)',
    border: '1px solid rgba(16, 185, 129, 0.25)',
    color: 'var(--text-primary)',
};

const infoPanelStyle = {
    marginTop: '16px',
    padding: '12px 14px',
    borderRadius: '12px',
    background: 'rgba(59, 130, 246, 0.08)',
    border: '1px solid rgba(59, 130, 246, 0.18)',
    color: 'var(--text-secondary)',
    lineHeight: 1.7,
};

const emptyStateStyle = {
    padding: '14px',
    borderRadius: '12px',
    border: '1px dashed var(--glass-border)',
    color: 'var(--text-secondary)',
    textAlign: 'center',
};

export default MetaAndromedaRelease;
