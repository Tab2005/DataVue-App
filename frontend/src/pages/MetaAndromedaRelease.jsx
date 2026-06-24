import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';

import { useModuleAccess } from '../hooks/usePermission';
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
    const { hasAccess, loading: loadingModuleAccess } = useModuleAccess('meta_andromeda', selectedTeamId);

    const t = (en, zh) => (language === 'en' ? en : zh);

    const getTranslation = (key) => {
        if (!key) return '--';
        const keyLower = String(key).toLowerCase();
        switch (keyLower) {
            // 資料庫與釋出屬性
            case 'model_version':
                return t('Model Version', '模型版本');
            case 'status':
                return t('Status', '狀態');
            case 'approved_by':
                return t('Approved By', '核准人員');
            case 'pairwise_ranking_accuracy':
                return t('Pairwise Ranking Accuracy', '成對排序準確率');
            case 'mean_band_error':
                return t('Mean Band Error', '平均級距誤差');
            case 'release_status':
                return t('Release Status', '釋出狀態');

            // 狀態值
            case 'approved':
                return t('Approved', '已核准上線');
            case 'rejected':
                return t('Rejected', '已退回');
            case 'rollback':
                return t('Rollback', '回滾');
            case 'rollbacked':
                return t('Rolled Back', '已回滾');
            case 'pending_review':
                return t('Pending Review', '審核中');
            case 'candidate':
                return t('Candidate', '候選版本');
            case 'current_production':
                return t('Current Production', '目前線上版本');

            // 歷史動作
            case 'approve':
                return t('Approve', '核准上線');
            case 'reject':
                return t('Reject', '退回');

            // 漂移狀態與時間視窗
            case 'drifted':
                return t('Drifted', '嚴重預估偏差');
            case 'warning':
                return t('Warning', '警告');
            case 'stable':
                return t('Stable', '穩定');
            case 'last_24h':
                return t('Last 24 Hours', '最近 24 小時');
            case 'last_7d':
                return t('Last 7 Days', '最近 7 天');
            case 'last_30d':
                return t('Last 30 Days', '最近 30 天');
            case 'lifetime':
                return t('Lifetime', '累積歷史成效');
            case 'custom':
                return t('Custom Range', '自訂時間區間');

            // 安全發佈閘門項 (Promotion Gates)
            case 'accuracy_gate':
                return t('Accuracy Gate', '準確率安全門檻');
            case 'mae_gate':
                return t('MAE Gate', '平均偏差安全門檻');
            case 'bias_gate':
                return t('Bias Gate', '模型偏向性門檻');
            case 'model_loaded_check':
                return t('Model Loaded Check', '模型載入測試');
            case 'active_drift_alert_check':
                return t('Active Drift Alert Check', '線上無嚴重預估偏差安全閘');
            case 'release actions now persist to datavue db.':
                return t('Release actions now persist to DataVue DB.', '版本發佈操作已成功持久化至 DataVue 資料庫。');
            case 'release metadata is now aligned with the meta andromeda registry source of truth.':
                return t('Release metadata is now aligned with the Meta Andromeda registry source of truth.', '版本中繼資料已與 Meta Andromeda 註冊表單一事實來源同步。');

            default:
                return key;
        }
    };

    const formatDateTime = (isoString) => {
        if (!isoString) return '--';
        try {
            let dateStr = isoString;
            if (!dateStr.endsWith('Z') && !dateStr.includes('+')) {
                dateStr = dateStr.includes('T') ? `${dateStr}Z` : dateStr;
            }
            const date = new Date(dateStr);
            if (isNaN(date.getTime())) return isoString;

            const y = date.getFullYear();
            const m = String(date.getMonth() + 1).padStart(2, '0');
            const d = String(date.getDate()).padStart(2, '0');
            const hh = String(date.getHours()).padStart(2, '0');
            const mm = String(date.getMinutes()).padStart(2, '0');
            const ss = String(date.getSeconds()).padStart(2, '0');

            return `${y}-${m}-${d} ${hh}:${mm}:${ss}`;
        } catch (e) {
            return isoString;
        }
    };

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
            setError(err.message || t('Failed to load release overview', '無法載入版本釋出總覽'));
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (!hasAccess) {
            return;
        }
        loadOverview();
    }, [hasAccess]);

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
            setActionMessage(`${t('Action executed successfully: ', '動作執行成功：')}${getTranslation(result.action)} (${result.model_version})`);
            await loadOverview();
        } catch (err) {
            setError(err.message || t('Failed to execute release action', '執行發佈動作失敗'));
        } finally {
            setSubmitting(false);
        }
    };

    if (loadingModuleAccess) {
        return (
            <div style={{ padding: isMobile ? '16px' : '24px' }}>
                <div style={panelStyle}>{t('Checking workspace access...', '正在檢查工作區模組權限...')}</div>
            </div>
        );
    }

    if (!hasAccess) {
        return (
            <div style={{ padding: isMobile ? '16px' : '24px' }}>
                <div style={infoPanelStyle}>
                    {t(
                        'You do not have access to Meta Andromeda in this workspace.',
                        '你目前沒有此工作區的 Meta Andromeda 模組存取權限。'
                    )}
                </div>
            </div>
        );
    }

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
                            <ReleaseRecordCard record={overview?.current_production} getTranslation={getTranslation} t={t} />
                            <button
                                type="button"
                                style={{ ...buttonSecondaryStyle, marginTop: '16px' }}
                                disabled={submitting}
                                onClick={() => handleReleaseAction('rollback', overview?.current_production?.model_version)}
                            >
                                {submitting ? t('Submitting...', '送出中...') : t('Rollback to Previous', '回滾到前一版')}
                            </button>
                        </section>
                        <section style={panelStyle}>
                            <h2 style={sectionTitleStyle}>{t('Previous Production', '前一版 Production')}</h2>
                            <ReleaseRecordCard record={overview?.previous_production} getTranslation={getTranslation} t={t} />
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
                                        {t('No recent drift reports found.', '目前無最新預估偏差報告。')}
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
                                                        {getTranslation(driftReport.drift_status)}
                                                    </span>
                                                </div>
                                                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                                    {getTranslation(driftReport.window_kind)}
                                                    {driftReport.window_kind === 'custom' && (() => {
                                                        const since = driftReport.report_payload?.since;
                                                        const until = driftReport.report_payload?.until;
                                                        if (since && until) {
                                                            return ` (${since} ~ ${until})`;
                                                        }
                                                        if (driftReport.note && driftReport.note.includes('~')) {
                                                            const match = driftReport.note.match(/(\d{4}-\d{2}-\d{2})\s*~\s*(\d{4}-\d{2}-\d{2})/);
                                                            if (match) {
                                                                return ` (${match[1]} ~ ${match[2]})`;
                                                            }
                                                        }
                                                        return '';
                                                    })()}
                                                </div>
                                            </div>

                                            <div style={metricGridStyle}>
                                                <Metric
                                                    label={t('Ranking Correlation (ρ)', '排名相關係數 (ρ)')}
                                                    value={driftReport.report_payload?.spearman_r !== undefined ? driftReport.report_payload.spearman_r.toFixed(3) : '--'}
                                                />
                                                <Metric
                                                    label={t('Accuracy', '預測準確率')}
                                                    value={driftReport.report_payload?.accuracy !== undefined ? `${(driftReport.report_payload.accuracy * 100).toFixed(1)}%` : '--'}
                                                />
                                                <Metric
                                                    label={t('MAE', '平均絕對偏差')}
                                                    value={driftReport.report_payload?.mae !== undefined ? driftReport.report_payload.mae.toFixed(2) : '--'}
                                                />
                                            </div>

                                            {driftReport.report_payload?.period_diagnosis && (() => {
                                                const pd = driftReport.report_payload.period_diagnosis;
                                                const stateColors = {
                                                    dual_advantage:    '#34d399',
                                                    market_driven:     '#60a5fa',
                                                    creative_critical: '#f59e0b',
                                                    needs_review:      '#f87171',
                                                };
                                                return (
                                                    <div style={{ marginTop: '10px', padding: '10px', borderRadius: '8px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--glass-border)' }}>
                                                        <div style={{ fontWeight: 700, fontSize: '0.85rem', color: stateColors[pd.state] || 'var(--text-primary)', marginBottom: '4px' }}>
                                                            {t('Campaign State', '投放狀態')}: {pd.label}
                                                            <span style={{ marginLeft: '8px', fontWeight: 400, fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                                                                ρ² = {(pd.creative_explained_variance * 100).toFixed(1)}%
                                                            </span>
                                                        </div>
                                                        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>{pd.recommendation}</div>
                                                    </div>
                                                );
                                            })()}
                                            <div style={{ marginTop: '10px', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                                {t('Triggered by: ', '觸發人員: ')}{driftReport.triggered_by} · {formatDateTime(driftReport.created_at)}
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
                                                        `Ranking correlation has dropped to ρ=${(driftReport?.report_payload?.spearman_r ?? 0).toFixed(3)} (threshold: 0.10). Creative scores no longer predict relative ROAS performance. Release is locked to prevent degraded predictions. Please run drift check and calibration in the Monitoring Console first.`,
                                                        `排名相關係數已降至 ρ=${(driftReport?.report_payload?.spearman_r ?? 0).toFixed(3)}（門檻：0.10），創意評分無法有效預測相對 ROAS 表現。為避免劣質預估，已自動鎖定發佈。請先至監控工作台執行偏差檢查與資料校準。`
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
                                                    <div>{t('Status', '狀態')}: {getTranslation(candidate.release_status)}</div>
                                                    <div>{t('Pairwise Ranking Accuracy', '成對排序準確率')}: {candidate.pairwise_ranking_accuracy}</div>
                                                    <div>{t('Mean Band Error', '平均級距誤差')}: {candidate.mean_band_error}</div>
                                                </div>
                                                <div style={{ display: 'grid', gap: '6px', marginTop: '12px', fontSize: '0.9rem' }}>
                                                    {Object.entries(candidate.promotion_gate_summary || {}).map(([key, value]) => (
                                                        <div key={key} style={gateRowStyle}>
                                                            <span style={{ color: 'var(--text-secondary)' }}>{getTranslation(key)}</span>
                                                            <strong style={{ color: value ? '#10b981' : '#ef4444' }}>
                                                                {value ? t('Passed', '通過') : t('Failed', '未通過')}
                                                            </strong>
                                                        </div>
                                                    ))}
                                                </div>
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
                                                            title={isDrifted ? t('Locked due to online model drift', '因線上模型預估偏差過大而鎖定發佈') : ''}
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
                                                                `Ranking correlation ρ=${(driftReport?.report_payload?.spearman_r ?? 0).toFixed(3)} is below threshold (0.10). Release is locked. Please run drift check in the Monitoring Console first.`,
                                                                `排名相關係數 ρ=${(driftReport?.report_payload?.spearman_r ?? 0).toFixed(3)} 低於門檻（0.10），已自動鎖定發佈。請先至監控工作台執行偏差檢查，再行核准新模型。`
                                                            )}
                                                        </div>
                                                    )}
                                                </div>
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
                                            {getTranslation(item.action)} · {item.model_version}
                                        </div>
                                        <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                            {item.actor} · {formatDateTime(item.created_at)}
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
                                        {getTranslation(note)}
                                    </div>
                                ))}
                            </div>
                        </section>
                    </div>
                </>
            )}
        </div>
    );
};

const ReleaseRecordCard = ({ record, getTranslation, t }) => {
    if (!record) {
        return <div style={{ color: 'var(--text-secondary)' }}>--</div>;
    }

    return (
        <div style={{ display: 'grid', gap: '10px' }}>
            <div style={detailCardStyle}>
                <div style={{ color: 'var(--text-secondary)', marginBottom: '6px' }}>{t('Model Version', '模型版本')}</div>
                <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{record.model_version}</div>
            </div>
            <div style={metricGridStyle}>
                <Metric label={t('Status', '狀態')} value={getTranslation(record.release_status)} />
                <Metric label={t('Approved By', '核准人員')} value={record.approved_by} />
                <Metric label={t('Pairwise Ranking Accuracy', '成對排序準確率')} value={record.pairwise_ranking_accuracy} />
                <Metric label={t('Mean Band Error', '平均級距誤差')} value={record.mean_band_error} />
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
