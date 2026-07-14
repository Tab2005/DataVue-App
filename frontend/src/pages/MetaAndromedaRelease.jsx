import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';

import { useModuleAccess } from '../hooks/usePermission';
import {
    approveMetaAndromedaRelease,
    createMetaAndromedaBacktestRun,
    createMetaAndromedaReleaseCandidate,
    fetchMetaAndromedaBacktestRuns,
    fetchMetaAndromedaReleaseMetricPairs,
    fetchMetaAndromedaReleaseOverview,
    rejectMetaAndromedaRelease,
    rollbackMetaAndromedaRelease,
} from '../services/metaAndromedaReleaseService';
import { fetchMetaAndromedaMonitoringSummary, validateCandidateModel } from '../services/metaAndromedaMonitoringService';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// 縮圖來源:優先走本地 asset preview(檔案已集中在 worker,穩定),沒有 asset 才退回
// Facebook CDN media_url(可能過期)
const resolvePairPreviewUrl = (item) => {
    if (item?.asset_uri) {
        const base = API_URL.endsWith('/') ? API_URL.slice(0, -1) : API_URL;
        return `${base}/api/meta-andromeda/assets/preview?uri=${encodeURIComponent(item.asset_uri)}`;
    }
    return item?.media_url || null;
};

const MetaAndromedaRelease = () => {
    const { isMobile, language, selectedTeamId } = useOutletContext();
    const [overview, setOverview] = useState(null);
    const [driftReport, setDriftReport] = useState(null);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);
    const [actionMessage, setActionMessage] = useState(null);
    const { hasAccess, loading: loadingModuleAccess } = useModuleAccess('meta_andromeda', selectedTeamId);

    // 新增候選版本表單（讓正式評分模型也能像回測模型一樣自由指定要試哪個
    // model_version，approve/rollback 的稽核流程完全不變）
    const [showCreateCandidateForm, setShowCreateCandidateForm] = useState(false);
    const [newCandidate, setNewCandidate] = useState({
        model_version: '',
        provider: 'openrouter',
        provider_model: '',
        scoring_profile: '',
        note: '',
    });
    const [creatingCandidate, setCreatingCandidate] = useState(false);
    const [createCandidateError, setCreateCandidateError] = useState(null);

    // 配對明細（docs/32 任務 1.2）：展開時才載入，預設 mismatch 排序讓高分低效浮最上面
    const [showMetricPairs, setShowMetricPairs] = useState(false);
    const [metricPairs, setMetricPairs] = useState(null);
    const [metricPairsSort, setMetricPairsSort] = useState('mismatch');
    const [metricPairsLoading, setMetricPairsLoading] = useState(false);
    const [metricPairsError, setMetricPairsError] = useState(null);

    const [backtestRuns, setBacktestRuns] = useState([]);
    const [backtestLoading, setBacktestLoading] = useState(false);
    const [backtestError, setBacktestError] = useState(null);
    const [creatingBacktest, setCreatingBacktest] = useState(false);
    const [backtestForm, setBacktestForm] = useState({
        provider_model: '',
        sample_limit: 20,
        note: '',
    });

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

    const loadBacktestRuns = async () => {
        setBacktestLoading(true);
        setBacktestError(null);
        try {
            const data = await fetchMetaAndromedaBacktestRuns({ limit: 20 });
            setBacktestRuns(data.runs || []);
        } catch (err) {
            setBacktestError(err.message || t('Failed to load backtest runs', '無法載入回測紀錄'));
        } finally {
            setBacktestLoading(false);
        }
    };

    const loadOverview = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await fetchMetaAndromedaReleaseOverview();
            setOverview(data);
            await loadBacktestRuns();
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

    const handleReleaseAction = async (action, modelVersion, options = {}) => {
        const force = Boolean(options.force);
        if (force) {
            const confirmed = window.confirm(
                t(
                    'Force approval bypasses the accuracy gate and will be recorded in release history. Continue?',
                    '強制核准會略過準確率門檻，並記錄在版本歷史中。確定繼續？'
                )
            );
            if (!confirmed) return;
        }
        const note = window.prompt(
            force
                ? t('Required audit note for force approval', '請輸入強制核准的必要稽核備註')
                : t('Optional note for this action', '請輸入這次操作的備註（可留空）'),
            ''
        );
        if (force && !note?.trim()) {
            setError(t('Force approval requires an audit note.', '強制核准必須填寫稽核備註。'));
            return;
        }

        setSubmitting(true);
        setError(null);
        setActionMessage(null);
        try {
            const payload = { model_version: modelVersion, note: note || null };
            if (action === 'approve') {
                payload.force = force;
            }
            const result = action === 'approve'
                ? await approveMetaAndromedaRelease(payload)
                : action === 'reject'
                    ? await rejectMetaAndromedaRelease(payload)
                    : await rollbackMetaAndromedaRelease(payload);
            const forceLabel = result.forced ? t(' (forced)', '（強制）') : '';
            setActionMessage(`${t('Action executed successfully: ', '動作執行成功：')}${getTranslation(result.action)}${forceLabel} (${result.model_version})`);
            await loadOverview();
        } catch (err) {
            setError(err.message || t('Failed to execute release action', '執行發佈動作失敗'));
        } finally {
            setSubmitting(false);
        }
    };

    const handleCreateCandidate = async () => {
        setCreatingCandidate(true);
        setCreateCandidateError(null);
        try {
            await createMetaAndromedaReleaseCandidate({
                model_version: newCandidate.model_version.trim(),
                provider: newCandidate.provider,
                provider_model: newCandidate.provider_model.trim(),
                scoring_profile: newCandidate.scoring_profile.trim() || null,
                note: newCandidate.note.trim() || null,
            });
            setActionMessage(
                t(
                    `New candidate created: ${newCandidate.model_version}`,
                    `已新增候選版本：${newCandidate.model_version}`
                )
            );
            setNewCandidate({ model_version: '', provider: 'openrouter', provider_model: '', scoring_profile: '', note: '' });
            setShowCreateCandidateForm(false);
            await loadOverview();
        } catch (err) {
            setCreateCandidateError(err.message || t('Failed to create candidate', '新增候選版本失敗'));
        } finally {
            setCreatingCandidate(false);
        }
    };

    const currentModelVersion = overview?.current_production?.model_version || null;

    const handleCreateBacktestRun = async () => {
        setCreatingBacktest(true);
        setBacktestError(null);
        try {
            const providerModel = backtestForm.provider_model.trim();
            const validation = await validateCandidateModel(providerModel);
            if (!validation?.ok) {
                const issues = validation?.issues?.length ? validation.issues.join(' / ') : t('Model validation failed', '模型驗證未通過');
                throw new Error(issues);
            }
            await createMetaAndromedaBacktestRun({
                provider_model: providerModel,
                sample_limit: Number(backtestForm.sample_limit) || 20,
                note: backtestForm.note.trim() || null,
            });
            setActionMessage(t('Backtest run queued.', '回測任務已排入佇列。'));
            setBacktestForm({ provider_model: '', sample_limit: 20, note: '' });
            await loadBacktestRuns();
        } catch (err) {
            setBacktestError(err.message || t('Failed to create backtest run', '建立回測任務失敗'));
        } finally {
            setCreatingBacktest(false);
        }
    };

    const getCandidateReleaseGate = (candidate) => {
        if (!candidate) return { passed: false, reason: t('No candidate data', '沒有候選版本資料') };
        if (candidate.is_demo_data) {
            return {
                passed: false,
                reason: t('Metrics have not been computed yet.', '尚未使用真實資料計算指標。'),
            };
        }
        const accuracy = Number(candidate.pairwise_ranking_accuracy);
        if (Number.isNaN(accuracy) || accuracy < 0.55) {
            return {
                passed: false,
                reason: t('Pairwise accuracy is below 0.55.', '成對排序準確率低於 0.55。'),
            };
        }
        return { passed: true, reason: t('Accuracy gate passed.', '準確率門檻已通過。') };
    };

    const getBacktestVerdict = (run) => {
        const baseline = Number(overview?.current_production?.pairwise_ranking_accuracy);
        const accuracy = Number(run?.pairwise_ranking_accuracy);
        if (run?.status !== 'completed' || Number.isNaN(accuracy)) return { label: t('Pending', '待完成'), color: '#94a3b8' };
        if (accuracy >= 0.55 && (Number.isNaN(baseline) || accuracy >= baseline)) {
            return { label: t('Better than baseline', '優於線上基準'), color: '#10b981' };
        }
        return { label: t('Not ready', '不建議上線'), color: '#ef4444' };
    };

    const loadMetricPairs = async (sort) => {
        if (!currentModelVersion) return;
        setMetricPairsLoading(true);
        setMetricPairsError(null);
        try {
            const data = await fetchMetaAndromedaReleaseMetricPairs(currentModelVersion, { sort, limit: 200 });
            setMetricPairs(data);
            setMetricPairsSort(sort);
        } catch (err) {
            setMetricPairsError(err.message || t('Failed to load metric pairs', '無法載入配對明細'));
        } finally {
            setMetricPairsLoading(false);
        }
    };

    const handleToggleMetricPairs = () => {
        const next = !showMetricPairs;
        setShowMetricPairs(next);
        if (next && !metricPairs && !metricPairsLoading) {
            loadMetricPairs(metricPairsSort);
        }
    };

    const handleExportMetricPairsCsv = () => {
        const items = metricPairs?.items || [];
        if (!items.length) return;
        const header = [
            'observed_creative_id', 'score_event_id', 'ad_id', 'ad_name', 'objective',
            'observation_window_kind', 'overall_score', 'pred_band', 'real_band', 'band_gap',
            'label_metric', 'label_value', 'perf_rank', 'spend', 'asset_uri', 'media_url',
        ];
        const escapeCell = (val) => {
            const s = val === null || val === undefined ? '' : String(val);
            return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
        };
        const rows = items.map((item) => header.map((key) => escapeCell(item[key])).join(','));
        // ﻿ BOM:Excel 開啟含中文欄位的 CSV 需要 BOM 才不會亂碼
        const csv = `﻿${header.join(',')}\n${rows.join('\n')}`;
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `metric_pairs_${metricPairs?.model_version || 'current'}_${metricPairsSort}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
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

            {overview?.is_demo_data ? (
                <div style={warningPanelStyle}>
                    {t(
                        '⚠️ The accuracy/error numbers below are still demo data — call POST /release/{model_version}/refresh-metrics to compute them from real drift report matches. Approve/Rollback do switch which model the runtime actually uses.',
                        '⚠️ 以下準確率／誤差數字仍為示範資料，尚未呼叫 POST /release/{model_version}/refresh-metrics 從實際 drift report 配對結果計算；核准/回滾已會切換 runtime 實際使用的模型版本。'
                    )}
                </div>
            ) : null}
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
                        gridTemplateColumns: '1fr',
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

                                            <div style={{
                                                ...metricGridStyle,
                                                gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, minmax(0, 1fr))',
                                            }}>
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

                            {/* 配對明細（docs/32 任務 1.2）：release 指標背後的逐筆配對，供人工歸因抽樣 */}
                            <section style={panelStyle}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
                                    <h2 style={{ ...sectionTitleStyle, margin: 0 }}>{t('Metric Pair Details', '配對明細')}</h2>
                                    <button type="button" style={buttonSecondaryStyle} onClick={handleToggleMetricPairs}>
                                        {showMetricPairs ? t('Collapse', '收合') : t('Expand', '展開')}
                                    </button>
                                </div>
                                {showMetricPairs && (
                                    <div style={{ marginTop: '14px' }}>
                                        <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '12px' }}>
                                            {t(
                                                'Every observed creative matched to its AI score — the same pairs behind pairwise ranking accuracy. Default sort surfaces "high score × low performance" first for manual attribution sampling.',
                                                '每一筆「觀測素材 × AI 評分」配對，就是成對排序準確率背後的原始資料。預設排序讓「高分低效」浮在最上面，供人工歸因抽樣。'
                                            )}
                                        </div>
                                        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '12px' }}>
                                            <button
                                                type="button"
                                                style={metricPairsSort === 'mismatch' ? buttonPrimaryStyle : buttonSecondaryStyle}
                                                disabled={metricPairsLoading}
                                                onClick={() => loadMetricPairs('mismatch')}
                                            >
                                                {t('Mismatch First', '級距差優先')}
                                            </button>
                                            <button
                                                type="button"
                                                style={metricPairsSort === 'score_vs_perf' ? buttonPrimaryStyle : buttonSecondaryStyle}
                                                disabled={metricPairsLoading}
                                                onClick={() => loadMetricPairs('score_vs_perf')}
                                            >
                                                {t('Score vs Performance', '分數對成效')}
                                            </button>
                                            <button
                                                type="button"
                                                style={{
                                                    ...buttonSecondaryStyle,
                                                    opacity: (metricPairs?.items || []).length ? 1 : 0.5,
                                                    cursor: (metricPairs?.items || []).length ? 'pointer' : 'not-allowed',
                                                }}
                                                disabled={!(metricPairs?.items || []).length}
                                                onClick={handleExportMetricPairsCsv}
                                            >
                                                {t('Export CSV', '匯出 CSV')}
                                            </button>
                                        </div>
                                        {metricPairsError && <div style={errorPanelStyle}>{metricPairsError}</div>}
                                        {metricPairsLoading ? (
                                            <div style={emptyStateStyle}>{t('Loading metric pairs...', '配對明細載入中...')}</div>
                                        ) : !metricPairs ? null : !(metricPairs.items || []).length ? (
                                            <div style={emptyStateStyle}>
                                                {t('No matched pairs for the current production model yet.', '目前線上版本尚無任何配對資料。')}
                                            </div>
                                        ) : (
                                            <>
                                                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                                                    {t(
                                                        `Showing ${metricPairs.items.length} of ${metricPairs.sample_count} pairs (model: ${metricPairs.model_version})`,
                                                        `顯示 ${metricPairs.items.length} / ${metricPairs.sample_count} 筆配對（版本：${metricPairs.model_version}）`
                                                    )}
                                                </div>
                                                <div style={{ overflowX: 'auto', maxHeight: '520px', overflowY: 'auto', border: '1px solid var(--glass-border)', borderRadius: '12px' }}>
                                                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem', minWidth: '760px' }}>
                                                        <thead>
                                                            <tr>
                                                                {[
                                                                    t('Creative', '素材'),
                                                                    t('Ad Name', '廣告名稱'),
                                                                    t('Objective', '目標'),
                                                                    t('Score', '模型總分'),
                                                                    t('Pred Band', '預測級距'),
                                                                    t('Real Band', '實際級距'),
                                                                    t('Gap', '級距差'),
                                                                    t('Perf Rank', '成效名次'),
                                                                    t('Spend', '花費'),
                                                                ].map((label) => (
                                                                    <th key={label} style={pairTableHeaderStyle}>{label}</th>
                                                                ))}
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            {metricPairs.items.map((item) => {
                                                                const previewUrl = resolvePairPreviewUrl(item);
                                                                return (
                                                                    <tr key={item.observed_creative_id} style={{ borderTop: '1px solid var(--glass-border)' }}>
                                                                        <td style={pairTableCellStyle}>
                                                                            <div style={{ width: '56px', height: '56px', borderRadius: '8px', overflow: 'hidden', background: 'rgba(255,255,255,0.04)' }}>
                                                                                {previewUrl ? (
                                                                                    item.media_type === 'video'
                                                                                        ? <video src={previewUrl} style={{ width: '100%', height: '100%', objectFit: 'cover' }} muted playsInline />
                                                                                        : <img src={previewUrl} style={{ width: '100%', height: '100%', objectFit: 'cover' }} alt="" loading="lazy" />
                                                                                ) : null}
                                                                            </div>
                                                                        </td>
                                                                        <td style={{ ...pairTableCellStyle, maxWidth: '220px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={item.ad_name || ''}>
                                                                            {item.ad_name || item.ad_id || '--'}
                                                                        </td>
                                                                        <td style={pairTableCellStyle}>{item.objective || '--'}</td>
                                                                        <td style={{ ...pairTableCellStyle, fontWeight: 700, color: 'var(--text-primary)' }}>{item.overall_score}</td>
                                                                        <td style={pairTableCellStyle}>{item.pred_band}</td>
                                                                        <td style={pairTableCellStyle}>{item.real_band}</td>
                                                                        <td style={{
                                                                            ...pairTableCellStyle,
                                                                            fontWeight: 700,
                                                                            color: item.band_gap >= 2 ? '#ef4444' : item.band_gap === 1 ? '#f59e0b' : '#10b981',
                                                                        }}>
                                                                            {item.band_gap}
                                                                        </td>
                                                                        <td style={pairTableCellStyle}>{item.perf_rank}</td>
                                                                        <td style={pairTableCellStyle}>{Number(item.spend).toLocaleString()}</td>
                                                                    </tr>
                                                                );
                                                            })}
                                                        </tbody>
                                                    </table>
                                                </div>
                                            </>
                                        )}
                                    </div>
                                )}
                            </section>

                            {/* 回測對照（docs/32 第 2 波）：候選模型不污染線上 review/monitoring/release 指標 */}
                            <section style={panelStyle}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px', marginBottom: '14px' }}>
                                    <h2 style={{ ...sectionTitleStyle, margin: 0 }}>{t('Backtest Comparison', '回測對照')}</h2>
                                    <button type="button" style={buttonSecondaryStyle} onClick={loadBacktestRuns} disabled={backtestLoading}>
                                        {backtestLoading ? t('Refreshing...', '更新中...') : t('Refresh', '重新整理')}
                                    </button>
                                </div>
                                <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '12px' }}>
                                    {t(
                                        'Run an isolated backtest against observed creatives. Results are compared with the current production baseline and never enter live review, monitoring drift, or release metrics.',
                                        '針對已觀測素材執行隔離回測，結果只用來和目前 Production 基準比較，不會進入線上審核、監控漂移或版本釋出指標。'
                                    )}
                                </div>
                                <div style={{ ...detailCardStyle, marginBottom: '12px' }}>
                                    <div style={metricGridStyle}>
                                        <Metric label={t('Baseline Model', '線上基準模型')} value={overview?.current_production?.model_version || '--'} />
                                        <Metric
                                            label={t('Baseline Accuracy', '線上基準準確率')}
                                            value={overview?.current_production?.pairwise_ranking_accuracy ?? '--'}
                                        />
                                    </div>
                                    <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1.5fr 0.6fr', gap: '10px', marginTop: '12px' }}>
                                        <label style={fieldLabelStyle}>
                                            {t('Provider Model', '供應商模型代號')}
                                            <input
                                                type="text"
                                                style={fieldInputStyle}
                                                value={backtestForm.provider_model}
                                                onChange={(e) => setBacktestForm((prev) => ({ ...prev, provider_model: e.target.value }))}
                                                placeholder="openai/gpt-4.1-mini"
                                            />
                                        </label>
                                        <label style={fieldLabelStyle}>
                                            {t('Sample Limit', '樣本上限')}
                                            <input
                                                type="number"
                                                min="1"
                                                max="200"
                                                style={fieldInputStyle}
                                                value={backtestForm.sample_limit}
                                                onChange={(e) => setBacktestForm((prev) => ({ ...prev, sample_limit: e.target.value }))}
                                            />
                                        </label>
                                    </div>
                                    <label style={{ ...fieldLabelStyle, marginTop: '10px' }}>
                                        {t('Note (optional)', '備註（選填）')}
                                        <input
                                            type="text"
                                            style={fieldInputStyle}
                                            value={backtestForm.note}
                                            onChange={(e) => setBacktestForm((prev) => ({ ...prev, note: e.target.value }))}
                                        />
                                    </label>
                                    <button
                                        type="button"
                                        style={{
                                            ...buttonPrimaryStyle,
                                            marginTop: '12px',
                                            opacity: creatingBacktest || !backtestForm.provider_model.trim() ? 0.5 : 1,
                                            cursor: creatingBacktest || !backtestForm.provider_model.trim() ? 'not-allowed' : 'pointer',
                                        }}
                                        disabled={creatingBacktest || !backtestForm.provider_model.trim()}
                                        onClick={handleCreateBacktestRun}
                                    >
                                        {creatingBacktest ? t('Queuing...', '排程中...') : t('Create Backtest Run', '建立回測任務')}
                                    </button>
                                </div>
                                {backtestError && <div style={{ ...errorPanelStyle, marginBottom: '12px' }}>{backtestError}</div>}
                                {backtestLoading ? (
                                    <div style={emptyStateStyle}>{t('Loading backtest runs...', '回測紀錄載入中...')}</div>
                                ) : !backtestRuns.length ? (
                                    <div style={emptyStateStyle}>{t('No backtest runs yet.', '目前尚無回測紀錄。')}</div>
                                ) : (
                                    <div style={{ overflowX: 'auto', border: '1px solid var(--glass-border)', borderRadius: '12px' }}>
                                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem', minWidth: '820px' }}>
                                            <thead>
                                                <tr>
                                                    {[
                                                        t('Model', '模型'),
                                                        t('Status', '狀態'),
                                                        t('Progress', '進度'),
                                                        t('Accuracy', '準確率'),
                                                        t('Mean Error', '平均誤差'),
                                                        t('Verdict', '判斷'),
                                                        t('Created At', '建立時間'),
                                                    ].map((label) => <th key={label} style={pairTableHeaderStyle}>{label}</th>)}
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {backtestRuns.map((run) => {
                                                    const verdict = getBacktestVerdict(run);
                                                    const progress = run.total_count
                                                        ? `${run.processed_count}/${run.total_count}`
                                                        : `${run.processed_count || 0}`;
                                                    return (
                                                        <tr key={run.run_id} style={{ borderTop: '1px solid var(--glass-border)' }}>
                                                            <td style={{ ...pairTableCellStyle, color: 'var(--text-primary)', fontWeight: 700 }}>{run.provider_model}</td>
                                                            <td style={pairTableCellStyle}>{run.status}</td>
                                                            <td style={pairTableCellStyle}>{progress}</td>
                                                            <td style={pairTableCellStyle}>{run.pairwise_ranking_accuracy ?? '--'}</td>
                                                            <td style={pairTableCellStyle}>{run.mean_band_error ?? '--'}</td>
                                                            <td style={{ ...pairTableCellStyle, color: verdict.color, fontWeight: 700 }}>{verdict.label}</td>
                                                            <td style={pairTableCellStyle}>{formatDateTime(run.created_at)}</td>
                                                        </tr>
                                                    );
                                                })}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </section>

                            {/* 候選版本 */}
                            <section style={panelStyle}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                                    <h2 style={{ ...sectionTitleStyle, margin: 0 }}>{t('Candidates', '候選版本')}</h2>
                                    <button
                                        type="button"
                                        style={buttonSecondaryStyle}
                                        onClick={() => setShowCreateCandidateForm((prev) => !prev)}
                                    >
                                        {showCreateCandidateForm
                                            ? t('Cancel', '取消')
                                            : t('+ New Candidate', '+ 新增候選版本')}
                                    </button>
                                </div>

                                {showCreateCandidateForm && (
                                    <div style={{ ...detailCardStyle, marginBottom: '16px' }}>
                                        <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '14px', lineHeight: 1.5 }}>
                                            {t(
                                                'Register a new candidate model_version so it can be approved/rolled back through the normal release workflow — no more being limited to the handful of candidates created by seed data.',
                                                '註冊一個新的候選 model_version，之後就能走既有的核准／回滾流程上線——不再只能在種子資料建立的少數幾個候選之間切換。'
                                            )}
                                        </div>
                                        {createCandidateError && (
                                            <div style={{ ...errorPanelStyle, marginBottom: '12px' }}>{createCandidateError}</div>
                                        )}
                                        <div style={{ display: 'grid', gap: '10px' }}>
                                            <label style={fieldLabelStyle}>
                                                {t('Model Version (unique ID)', '模型版本（唯一識別碼）')}
                                                <input
                                                    type="text"
                                                    style={fieldInputStyle}
                                                    value={newCandidate.model_version}
                                                    onChange={(e) => setNewCandidate((prev) => ({ ...prev, model_version: e.target.value }))}
                                                    placeholder="cand_v2026_09_01_a"
                                                />
                                            </label>
                                            <label style={fieldLabelStyle}>
                                                {t('Provider', '供應商')}
                                                <select
                                                    style={fieldInputStyle}
                                                    value={newCandidate.provider}
                                                    onChange={(e) => setNewCandidate((prev) => ({ ...prev, provider: e.target.value }))}
                                                >
                                                    <option value="openrouter">openrouter</option>
                                                    <option value="heuristic">heuristic</option>
                                                </select>
                                            </label>
                                            <label style={fieldLabelStyle}>
                                                {t('Provider Model', '供應商模型代號')}
                                                <input
                                                    type="text"
                                                    style={fieldInputStyle}
                                                    value={newCandidate.provider_model}
                                                    onChange={(e) => setNewCandidate((prev) => ({ ...prev, provider_model: e.target.value }))}
                                                    placeholder="some-org/some-model:free"
                                                />
                                            </label>
                                            <label style={fieldLabelStyle}>
                                                {t('Scoring Profile (optional, defaults to current production)', 'Scoring Profile（選填，留空沿用目前正式版）')}
                                                <input
                                                    type="text"
                                                    style={fieldInputStyle}
                                                    value={newCandidate.scoring_profile}
                                                    onChange={(e) => setNewCandidate((prev) => ({ ...prev, scoring_profile: e.target.value }))}
                                                    placeholder="creative_scoring_v2"
                                                />
                                            </label>
                                            <label style={fieldLabelStyle}>
                                                {t('Note (optional)', '備註（選填）')}
                                                <input
                                                    type="text"
                                                    style={fieldInputStyle}
                                                    value={newCandidate.note}
                                                    onChange={(e) => setNewCandidate((prev) => ({ ...prev, note: e.target.value }))}
                                                />
                                            </label>
                                            <button
                                                type="button"
                                                style={{
                                                    ...buttonPrimaryStyle,
                                                    opacity: creatingCandidate || !newCandidate.model_version.trim() || !newCandidate.provider_model.trim() ? 0.5 : 1,
                                                    cursor: creatingCandidate || !newCandidate.model_version.trim() || !newCandidate.provider_model.trim() ? 'not-allowed' : 'pointer',
                                                }}
                                                disabled={creatingCandidate || !newCandidate.model_version.trim() || !newCandidate.provider_model.trim()}
                                                onClick={handleCreateCandidate}
                                            >
                                                {creatingCandidate ? t('Creating...', '建立中...') : t('Create Candidate', '建立候選版本')}
                                            </button>
                                        </div>
                                    </div>
                                )}

                                <div style={{
                                    display: 'grid',
                                    gridTemplateColumns: isMobile ? '1fr' : 'repeat(2, minmax(0, 1fr))',
                                    gap: '12px',
                                    alignItems: 'stretch',
                                }}>
                                    {(overview?.candidates || []).map((candidate) => {
                                        const isDrifted = driftReport?.drift_status === 'drifted';
                                        const releaseGate = getCandidateReleaseGate(candidate);
                                        const approveBlocked = isDrifted || !releaseGate.passed;
                                        return (
                                            <div
                                                key={candidate.model_version}
                                                style={{
                                                    ...detailCardStyle,
                                                    display: 'grid',
                                                    gridTemplateColumns: isMobile ? '1fr' : 'minmax(0, 1fr) minmax(220px, 0.8fr)',
                                                    gap: '16px',
                                                    alignItems: 'start',
                                                    alignContent: 'start',
                                                }}
                                            >
                                                <div style={{ display: 'grid', gap: '12px' }}>
                                                    <div>
                                                        <div style={{ color: 'var(--text-primary)', fontWeight: 700, marginBottom: '8px' }}>
                                                            {candidate.model_version}
                                                        </div>
                                                        <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                                                            {t('Status', '狀態')}: {getTranslation(candidate.release_status)}
                                                        </div>
                                                    </div>
                                                    <div style={{ display: 'grid', gap: '6px', fontSize: '0.9rem' }}>
                                                        {Object.entries(candidate.promotion_gate_summary || {}).map(([key, value]) => (
                                                            <div key={key} style={gateRowStyle}>
                                                                <span style={{ color: 'var(--text-secondary)' }}>{getTranslation(key)}</span>
                                                                <strong style={{ color: value ? '#10b981' : '#ef4444' }}>
                                                                    {value ? t('Passed', '通過') : t('Failed', '未通過')}
                                                                </strong>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>

                                                <div style={{ display: 'grid', gap: '12px', justifyItems: 'stretch' }}>
                                                    <div
                                                        style={{
                                                            display: 'grid',
                                                            gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
                                                            gap: '10px',
                                                            width: '100%',
                                                        }}
                                                    >
                                                        <Metric label={t('Pairwise Ranking Accuracy', '成對排序準確率')} value={candidate.pairwise_ranking_accuracy} />
                                                        <Metric label={t('Mean Band Error', '平均級距誤差')} value={candidate.mean_band_error} />
                                                    </div>
                                                    <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                                                        <button
                                                            type="button"
                                                            style={{
                                                                ...buttonPrimaryStyle,
                                                                opacity: approveBlocked ? 0.4 : 1,
                                                                cursor: approveBlocked ? 'not-allowed' : 'pointer'
                                                            }}
                                                            disabled={submitting || approveBlocked}
                                                            onClick={() => handleReleaseAction('approve', candidate.model_version)}
                                                            title={isDrifted ? t('Locked due to online model drift', '因線上模型預估偏差過大而鎖定發佈') : releaseGate.reason}
                                                        >
                                                            {t('Approve', '批准')}
                                                        </button>
                                                        {approveBlocked && !isDrifted && (
                                                            <button
                                                                type="button"
                                                                style={buttonSecondaryStyle}
                                                                disabled={submitting}
                                                                onClick={() => handleReleaseAction('approve', candidate.model_version, { force: true })}
                                                            >
                                                                {t('Force Approve', '強制核准')}
                                                            </button>
                                                        )}
                                                        <button
                                                            type="button"
                                                            style={buttonSecondaryStyle}
                                                            disabled={submitting}
                                                            onClick={() => handleReleaseAction('reject', candidate.model_version)}
                                                        >
                                                            {t('Reject', '退回')}
                                                        </button>
                                                    </div>
                                                </div>

                                                {!releaseGate.passed && !isDrifted && (
                                                    <div style={{
                                                        gridColumn: '1 / -1',
                                                        color: '#f59e0b',
                                                        fontSize: '0.82rem',
                                                        lineHeight: 1.5,
                                                        background: 'rgba(245, 158, 11, 0.08)',
                                                        padding: '10px',
                                                        borderRadius: '8px',
                                                        border: '1px solid rgba(245, 158, 11, 0.2)',
                                                    }}>
                                                        {t('Approval gate: ', '核准門檻：')}{releaseGate.reason}
                                                    </div>
                                                )}
                                                {isDrifted && (
                                                    <div style={{
                                                        gridColumn: '1 / -1',
                                                        color: '#ef4444',
                                                        fontSize: '0.82rem',
                                                        lineHeight: 1.5,
                                                        background: 'rgba(239, 68, 68, 0.08)',
                                                        padding: '10px',
                                                        borderRadius: '8px',
                                                        border: '1px solid rgba(239, 68, 68, 0.2)',
                                                    }}>
                                                        ⚠️ {t(
                                                            `Ranking correlation ρ=${(driftReport?.report_payload?.spearman_r ?? 0).toFixed(3)} is below threshold (0.10). Release is locked. Please run drift check in the Monitoring Console first.`,
                                                            `排名相關係數 ρ=${(driftReport?.report_payload?.spearman_r ?? 0).toFixed(3)} 低於門檻（0.10），已自動鎖定發佈。請先至監控工作台執行偏差檢查，再行核准新模型。`
                                                        )}
                                                    </div>
                                                )}
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
                                            {getTranslation(item.action)}{item.forced ? t(' (forced)', '（強制）') : ''} · {item.model_version}
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
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                    <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{record.model_version}</div>
                    {record.is_demo_data ? <span style={demoBadgeStyle}>{t('Demo Data', '示範資料')}</span> : null}
                </div>
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


const demoBadgeStyle = {
    display: 'inline-flex',
    alignItems: 'center',
    padding: '3px 8px',
    borderRadius: '999px',
    border: '1px solid rgba(245, 158, 11, 0.35)',
    background: 'rgba(245, 158, 11, 0.1)',
    color: '#fbbf24',
    fontSize: '0.72rem',
    fontWeight: 700,
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

const fieldLabelStyle = {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
    fontSize: '0.8rem',
    color: 'var(--text-secondary)',
};

const fieldInputStyle = {
    padding: '10px 12px',
    borderRadius: '8px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.03)',
    color: 'var(--text-primary)',
    fontSize: '0.85rem',
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

const warningPanelStyle = {
    marginBottom: '16px',
    padding: '16px',
    borderRadius: '12px',
    background: 'rgba(245, 158, 11, 0.1)',
    border: '1px solid rgba(245, 158, 11, 0.3)',
    color: 'var(--text-primary)',
    fontSize: '0.88rem',
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

const pairTableHeaderStyle = {
    position: 'sticky',
    top: 0,
    background: 'var(--bg-secondary)',
    color: 'var(--text-secondary)',
    textAlign: 'left',
    padding: '10px 12px',
    fontWeight: 600,
    whiteSpace: 'nowrap',
};

const pairTableCellStyle = {
    padding: '8px 12px',
    color: 'var(--text-secondary)',
    verticalAlign: 'middle',
};

export default MetaAndromedaRelease;
