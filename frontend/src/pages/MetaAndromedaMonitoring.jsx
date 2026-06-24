import React, { useEffect, useMemo, useState } from 'react';
import { useOutletContext, useSearchParams } from 'react-router-dom';

import { useModuleAccess } from '../hooks/usePermission';
import {
    fetchMetaAndromedaMonitoringSummary,
    fetchMetaAndromedaMonitoringTimeline,
    triggerMetaAndromedaDriftReport,
    syncMetaAndromedaCalibrationDataset,
    cleanupStaleScoreEvents,
    fetchScoringProfiles,
    promoteScoringProfile,
    fetchDriftTrend,
} from '../services/metaAndromedaMonitoringService';

const MetaAndromedaMonitoring = () => {
    const { isMobile, language, selectedTeamId } = useOutletContext();
    const [searchParams, setSearchParams] = useSearchParams();
    const [summary, setSummary] = useState(null);
    const [timeline, setTimeline] = useState(null);
    const [loading, setLoading] = useState(true);
    const [loadingTimeline, setLoadingTimeline] = useState(false);
    const [runningDrift, setRunningDrift] = useState(false);
    const [error, setError] = useState(null);
    const [hostFilter, setHostFilter] = useState(searchParams.get('host') || 'all');
    const [eventQuery, setEventQuery] = useState(searchParams.get('q') || '');
    const [deadLetterOnly, setDeadLetterOnly] = useState(searchParams.get('dead') === '1');
    const [selectedScoreEventId, setSelectedScoreEventId] = useState(searchParams.get('event') || '');
    const [driftWindowKind, setDriftWindowKind] = useState(searchParams.get('window') || 'last_24h');
    const [driftSince, setDriftSince] = useState(searchParams.get('since') || '');
    const [driftUntil, setDriftUntil] = useState(searchParams.get('until') || '');
    const [driftNote, setDriftNote] = useState('');
    const [selectedDriftReport, setSelectedDriftReport] = useState(null);
    const [excludedObsIds, setExcludedObsIds] = useState(new Set());
    const [syncingCal, setSyncingCal] = useState(false);
    const [cleanupResult, setCleanupResult] = useState(null);
    const [runningCleanup, setRunningCleanup] = useState(false);
    const [scoringProfiles, setScoringProfiles] = useState(null);
    const [loadingProfiles, setLoadingProfiles] = useState(false);
    const [promotingProfile, setPromotingProfile] = useState(null);
    const [driftTrend, setDriftTrend] = useState(null);
    const [loadingTrend, setLoadingTrend] = useState(false);
    const { hasAccess, loading: loadingModuleAccess } = useModuleAccess('meta_andromeda', selectedTeamId);

    const t = (en, zh) => (language === 'en' ? en : zh);

    const getTranslation = (key) => {
        if (!key) return '--';
        const keyLower = String(key).toLowerCase();
        switch (keyLower) {
            // 指標標籤
            case 'queued_total':
                return t('Queued Total', '累計佇列數');
            case 'completed_total':
                return t('Completed Total', '累計完成數');
            case 'failure_total':
                return t('Failure Total', '累計失敗數');
            case 'score-request':
                return t('Prediction / ScoreEvent Queue', 'Prediction / ScoreEvent 佇列');
            case 'observed_total':
                return t('Observed Imported (Cumulative)', '已匯入 Observation（累積）');
            case 'latest_observed_total':
                return t('Observed in Latest Drift Window', '最近 Drift 區間 Observation');
            case 'observed_with_asset':
                return t('Observed With Asset', '已有素材 Observation');
            case 'latest_matched_total':
                return t('Matched to Completed Score', '成功配對 Completed Score');
            case 'latest_match_rate':
                return t('Latest Match Rate', '最近配對率');
            case 'latest_calibration_candidate_total':
                return t('Calibration Candidates', '可校準偏差樣本');
            case 'latest_calibration_synced_total':
                return t('Calibration Synced', '已同步校準資料');
            case 'latest_calibration_status':
                return t('Calibration Status', '校準資料狀態');
            case 'queue_depth.current':
                return t('Current Queue Depth', '當前佇列深度');
            case 'queue_depth.peak':
                return t('Peak Queue Depth', '佇列深度峰值');
            case 'latency.avg(ms)':
                return t('Avg Latency (ms)', '平均延遲 (ms)');
            case 'latency.p95(ms)':
                return t('P95 Latency (ms)', 'P95 延遲 (ms)');
            case 'latency.max(ms)':
                return t('Max Latency (ms)', '最大延遲 (ms)');

            // 策略與佇列
            case 'database_queue':
                return t('Database Queue', '資料庫排程佇列');
            case 'redis_stream':
                return t('Redis Stream', 'Redis 串流佇列');
            case 'apscheduler':
                return t('APScheduler', '背景排程器');

            // 狀態與事件狀態
            case 'processing_started':
                return t('Processing Started', '已啟動處理');
            case 'completed':
                return t('Completed', '處理完成');
            case 'failed':
                return t('Failed', '處理失敗');
            case 'queued':
                return t('Queued', '已入佇列');
            case 'dead_letter':
                return t('Dead Letter', '異常任務 (已隔離)');
            case 'drifted':
                return t('Drifted', '嚴重預估偏差');
            case 'warning':
                return t('Warning', '警告');
            case 'stable':
                return t('Stable', '穩定');

            // 時間窗口
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

            // 級距
            case 'high':
                return t('High', '高 (High)');
            case 'mid':
                return t('Mid', '中 (Mid)');
            case 'low':
                return t('Low', '低 (Low)');

            // 任務與事件類型
            case 'score_request_received':
                return t('Score Request Received', '收到評分請求');
            case 'dataset_calibration':
                return t('Dataset Calibration', '資料集校準');
            case 'drift_diagnostics':
                return t('Drift Diagnostics', '偏差診斷');
            case 'prediction_inference':
                return t('Prediction Inference', '預測推論');
            case 'model_sync':
                return t('Model Sync', '模型同步');

            // 告警層級
            case 'info':
                return t('Info', '資訊');
            case 'error':
                return t('Error', '錯誤');
            case 'critical':
                return t('Critical', '嚴重');

            // 主機策略
            case 'shared_queue_host_adapter':
                return t('Shared Queue Host Adapter', '共用佇列適配器');
            case 'not_started':
                return t('Not Started', '尚未開始');
            case 'queued_for_calibration':
                return t('Queued for Calibration', '已排入校準');
            case 'no_data_to_sync':
                return t('No Data to Sync', '沒有可同步資料');

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

    const loadSummary = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await fetchMetaAndromedaMonitoringSummary();
            setSummary(data);
        } catch (err) {
            setError(err.message || 'Failed to load monitoring summary');
        } finally {
            setLoading(false);
        }
    };

    const loadTimeline = async (scoreEventId) => {
        if (!scoreEventId) {
            setTimeline(null);
            return;
        }
        setLoadingTimeline(true);
        setError(null);
        try {
            const data = await fetchMetaAndromedaMonitoringTimeline(scoreEventId);
            setTimeline(data);
        } catch (err) {
            setError(err.message || 'Failed to load event timeline');
        } finally {
            setLoadingTimeline(false);
        }
    };

    useEffect(() => {
        if (!hasAccess) {
            return;
        }
        loadSummary();
        loadProfiles();
        loadDriftTrend();
    }, [hasAccess]);

    useEffect(() => {
        const nextParams = new URLSearchParams();
        if (hostFilter && hostFilter !== 'all') {
            nextParams.set('host', hostFilter);
        }
        if (eventQuery.trim()) {
            nextParams.set('q', eventQuery.trim());
        }
        if (deadLetterOnly) {
            nextParams.set('dead', '1');
        }
        if (selectedScoreEventId) {
            nextParams.set('event', selectedScoreEventId);
        }
        if (driftWindowKind !== 'last_24h') {
            nextParams.set('window', driftWindowKind);
        }
        if (driftWindowKind === 'custom') {
            if (driftSince) nextParams.set('since', driftSince);
            if (driftUntil) nextParams.set('until', driftUntil);
        } else {
            nextParams.delete('since');
            nextParams.delete('until');
        }
        setSearchParams(nextParams, { replace: true });
    }, [hostFilter, eventQuery, deadLetterOnly, selectedScoreEventId, driftWindowKind, driftSince, driftUntil, setSearchParams]);

    useEffect(() => {
        loadTimeline(selectedScoreEventId);
    }, [selectedScoreEventId]);

    const recentEvents = useMemo(() => (summary?.worker_host?.recent_events || []).filter((event) => {
        const hostOk = hostFilter === 'all' || event.queue_host === hostFilter;
        const query = eventQuery.trim().toLowerCase();
        const queryOk = !query
            || event.event_type?.toLowerCase().includes(query)
            || event.queue_host?.toLowerCase().includes(query)
            || event.score_event_id?.toLowerCase().includes(query)
            || event.runtime_job_id?.toLowerCase().includes(query)
            || event.message?.toLowerCase().includes(query);
        return hostOk && queryOk;
    }), [summary, hostFilter, eventQuery]);

    const deadLetters = useMemo(() => (summary?.worker_host?.dead_letters || []).filter((item) => {
        const hostOk = hostFilter === 'all' || item.queue_host === hostFilter;
        const query = eventQuery.trim().toLowerCase();
        const queryOk = !query
            || item.failure_stage?.toLowerCase().includes(query)
            || item.queue_host?.toLowerCase().includes(query)
            || item.score_event_id?.toLowerCase().includes(query)
            || item.runtime_job_id?.toLowerCase().includes(query)
            || item.final_error_message?.toLowerCase().includes(query);
        return hostOk && queryOk;
    }), [summary, hostFilter, eventQuery]);

    const visibleRecentEvents = deadLetterOnly ? [] : recentEvents.slice(0, 8);
    const visibleDeadLetters = deadLetterOnly ? deadLetters : deadLetters.slice(0, 6);

    const handleDriftTrigger = async (event) => {
        event.preventDefault();
        if (driftWindowKind === 'custom' && (!driftSince || !driftUntil)) {
            setError(language === 'zh' ? '請提供自訂時間區間的開始與結束日期' : 'Please provide both start and end dates for custom range');
            return;
        }
        setRunningDrift(true);
        setError(null);
        try {
            await triggerMetaAndromedaDriftReport({
                window_kind: driftWindowKind,
                note: driftNote.trim() || null,
                since: driftWindowKind === 'custom' ? driftSince : null,
                until: driftWindowKind === 'custom' ? driftUntil : null,
            });
            setDriftNote('');
            await loadSummary();
        } catch (err) {
            setError(err.message || 'Failed to trigger drift report');
        } finally {
            setRunningDrift(false);
        }
    };

    const handleSelectTimeline = (scoreEventId) => {
        setSelectedScoreEventId(scoreEventId);
    };

    const handleCleanupStale = async () => {
        if (!window.confirm(language === 'zh'
            ? '確定要清除所有超過 30 分鐘仍卡在 queued / processing 的評分任務？\n\n此操作會將這些任務標記為 failed，不可回復。'
            : 'Clear all score events stuck in queued/processing for more than 30 minutes?\n\nThey will be marked as failed. This cannot be undone.')) {
            return;
        }
        setRunningCleanup(true);
        setCleanupResult(null);
        setError(null);
        try {
            const result = await cleanupStaleScoreEvents({ include_queued: true });
            setCleanupResult(result);
            await loadSummary();
        } catch (err) {
            setError(err.message || 'Cleanup failed');
        } finally {
            setRunningCleanup(false);
        }
    };

    const loadProfiles = async () => {
        setLoadingProfiles(true);
        try {
            const data = await fetchScoringProfiles();
            setScoringProfiles(data);
        } catch (err) {
            setError(err.message || 'Failed to load scoring profiles');
        } finally {
            setLoadingProfiles(false);
        }
    };

    const loadDriftTrend = async () => {
        setLoadingTrend(true);
        try {
            const data = await fetchDriftTrend(30);
            setDriftTrend(data);
        } catch (err) {
            // non-fatal: trend section shows empty state
        } finally {
            setLoadingTrend(false);
        }
    };

    const handlePromoteProfile = async (profileName) => {
        if (!window.confirm(language === 'zh'
            ? `確定要將 "${profileName}" 設為生效中的 Scoring Profile？\n目前生效的 profile 會被取消。`
            : `Promote "${profileName}" as the active Scoring Profile?\nThe current active profile will be deactivated.`)) {
            return;
        }
        setPromotingProfile(profileName);
        setError(null);
        try {
            await promoteScoringProfile(profileName);
            await loadProfiles();
        } catch (err) {
            setError(err.message || 'Promote failed');
        } finally {
            setPromotingProfile(null);
        }
    };

    const handleToggleExcludeObs = (obsId) => {
        setExcludedObsIds((prev) => {
            const next = new Set(prev);
            if (next.has(obsId)) {
                next.delete(obsId);
            } else {
                next.add(obsId);
            }
            return next;
        });
    };

    const handleSyncCalibration = async () => {
        if (!selectedDriftReport) return;
        setSyncingCal(true);
        setError(null);
        try {
            const result = await syncMetaAndromedaCalibrationDataset({
                window_kind: selectedDriftReport.window_kind,
                excluded_observed_ids: Array.from(excludedObsIds),
            });
            alert(language === 'zh'
                ? `校準資料集建立成功！ID: ${result.dataset_id}，共 ${result.synced_count} 筆偏移素材。`
                : `Dataset created successfully! ID: ${result.dataset_id}, synced ${result.synced_count} ads.`
            );
            setSelectedDriftReport(null);
            setExcludedObsIds(new Set());
            await loadSummary();
        } catch (err) {
            setError(err.message || 'Failed to sync calibration dataset');
        } finally {
            setSyncingCal(false);
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
            {/* 注入精美磨砂玻璃滾動條樣式 */}
            <style>{`
                .queue-scroll-box::-webkit-scrollbar {
                    width: 6px;
                }
                .queue-scroll-box::-webkit-scrollbar-track {
                    background: rgba(255, 255, 255, 0.01);
                    border-radius: 999px;
                }
                .queue-scroll-box::-webkit-scrollbar-thumb {
                    background: var(--glass-border);
                    border-radius: 999px;
                    transition: all 0.2s;
                }
                .queue-scroll-box::-webkit-scrollbar-thumb:hover {
                    background: var(--accent-primary);
                }
            `}</style>

            <div style={{
                marginBottom: '20px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: isMobile ? 'flex-start' : 'center',
                gap: '16px',
                flexDirection: isMobile ? 'column' : 'row',
            }}>
                <div>
                    <div style={{ color: 'var(--accent-primary)', fontWeight: 700, marginBottom: '8px' }}>
                        Meta Andromeda
                    </div>
                    <h1 style={{ margin: 0, color: 'var(--text-primary)' }}>
                        {t('Monitoring Summary', '監控總覽')}
                    </h1>
                </div>
                <button type="button" onClick={loadSummary} style={actionButtonStyle}>
                    {t('Refresh', '重新整理')}
                </button>
            </div>

            <div style={{
                ...panelStyle,
                marginBottom: '16px',
                display: 'grid',
                gridTemplateColumns: isMobile ? '1fr' : '1.1fr 0.8fr auto',
                gap: '12px',
                alignItems: 'center',
            }}>
                <input
                    type="text"
                    value={eventQuery}
                    onChange={(event) => setEventQuery(event.target.value)}
                    placeholder={t('Search score event, runtime job, or message', '搜尋評分事件、執行任務或訊息')}
                    style={inputStyle}
                />
                <select value={hostFilter} onChange={(event) => setHostFilter(event.target.value)} style={inputStyle}>
                    <option value="all">{t('All Hosts', '所有主機')}</option>
                    {Array.from(new Set([
                        summary?.worker_host?.active_host,
                        ...(summary?.worker_host?.recent_events || []).map((event) => event.queue_host),
                        ...(summary?.worker_host?.dead_letters || []).map((item) => item.queue_host),
                    ].filter(Boolean))).map((host) => (
                        <option key={host} value={host}>{host}</option>
                    ))}
                </select>
                <label style={toggleLabelStyle}>
                    <input
                        type="checkbox"
                        checked={deadLetterOnly}
                        onChange={(event) => setDeadLetterOnly(event.target.checked)}
                    />
                    <span>{t('Dead Letters Only', '只看異常任務')}</span>
                </label>
            </div>

            {error ? <div style={errorPanelStyle}>{error}</div> : null}

            {loading ? (
                <div style={panelStyle}>{t('Loading monitoring summary...', '正在載入監控資料...')}</div>
            ) : (
                <>
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: isMobile ? '1fr' : 'repeat(2, 1fr)',
                        gap: '16px',
                        marginBottom: '16px'
                    }}>
                        {Object.entries(summary?.jobs || {}).map(([jobKey, job]) => (
                            <section key={jobKey} style={panelStyle}>
                                <h2 style={sectionTitleStyle}>{getTranslation(jobKey)}</h2>
                                <div style={metricGridStyle}>
                                    <Metric label={getTranslation("queued_total")} value={job.queued_total} />
                                    <Metric label={getTranslation("completed_total")} value={job.completed_total} />
                                    <Metric label={getTranslation("failure_total")} value={job.failure_total} />
                                    <Metric label={getTranslation("queue_depth.current")} value={job.queue_depth?.current} />
                                    <Metric label={getTranslation("queue_depth.peak")} value={job.queue_depth?.peak} />
                                    <Metric label={getTranslation("latency.avg(ms)")} value={job.latency_ms?.avg} />
                                    <Metric label={getTranslation("latency.p95(ms)")} value={job.latency_ms?.p95} />
                                    <Metric label={getTranslation("latency.max(ms)")} value={job.latency_ms?.max} />
                                </div>
                            </section>
                        ))}

                        <section style={panelStyle}>
                            <h2 style={sectionTitleStyle}>{t('Observation Pipeline', 'Observation 資料管線')}</h2>
                            <div style={{ marginBottom: '12px', color: 'var(--text-secondary)', fontSize: '0.85rem', lineHeight: 1.6 }}>
                                {t(
                                    'These metrics only track the FB Ads observation import line. Manual Score Lab uploads are not counted here unless a drift report explicitly matches them.',
                                    '這些指標僅統計 FB Ads observation 匯入這條線；Score Lab 手動上傳素材不會算在這裡，除非某次 drift 報告有明確配對到它們。'
                                )}
                            </div>
                            <div style={metricGridStyle}>
                                <Metric
                                    label={getTranslation('observed_total')}
                                    value={summary?.observation_pipeline?.observed_total}
                                />
                                <Metric
                                    label={getTranslation('latest_observed_total')}
                                    value={summary?.observation_pipeline?.latest_observed_total}
                                />
                                <Metric
                                    label={getTranslation('observed_with_asset')}
                                    value={summary?.observation_pipeline?.observed_with_asset}
                                />
                                <Metric
                                    label={getTranslation('latest_matched_total')}
                                    value={summary?.observation_pipeline?.latest_matched_total}
                                />
                                <Metric
                                    label={getTranslation('latest_match_rate')}
                                    value={formatPercent(summary?.observation_pipeline?.latest_match_rate)}
                                />
                                <Metric
                                    label={getTranslation('latest_calibration_candidate_total')}
                                    value={summary?.observation_pipeline?.latest_calibration_candidate_total}
                                />
                                <Metric
                                    label={getTranslation('latest_calibration_synced_total')}
                                    value={summary?.observation_pipeline?.latest_calibration_synced_total}
                                />
                            </div>
                            <div style={{ marginTop: '12px', color: 'var(--text-secondary)', fontSize: '0.85rem', lineHeight: 1.6 }}>
                                {t('Calibration status', '校準狀態')}: {getTranslation(summary?.observation_pipeline?.latest_calibration_status)}
                                {summary?.observation_pipeline?.latest_calibration_dataset_id
                                    ? ` · Dataset: ${summary.observation_pipeline.latest_calibration_dataset_id}`
                                    : ''}
                            </div>
                        </section>

                        <section style={panelStyle}>
                            <h2 style={sectionTitleStyle}>{t('Drift Trigger', '預估偏差檢查')}</h2>
                            <form onSubmit={handleDriftTrigger} style={{ display: 'grid', gap: '12px' }}>
                                <select value={driftWindowKind} onChange={(event) => setDriftWindowKind(event.target.value)} style={inputStyle}>
                                    <option value="last_24h">{t('Last 24 Hours', '最近 24 小時')}</option>
                                    <option value="last_7d">{t('Last 7 Days', '最近 7 天')}</option>
                                    <option value="last_30d">{t('Last 30 Days', '最近 30 天')}</option>
                                    <option value="custom">{t('Custom Date Range', '自訂時間區間')}</option>
                                </select>
                                {driftWindowKind === 'custom' && (
                                    <div style={{ display: 'flex', gap: '8px', marginBottom: '4px' }}>
                                        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '4px' }}>
                                            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{t('Start Date', '開始日期')}</span>
                                            <input 
                                                type="date" 
                                                value={driftSince} 
                                                onChange={(e) => setDriftSince(e.target.value)} 
                                                style={{ ...inputStyle, colorScheme: 'dark' }}
                                            />
                                        </div>
                                        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '4px' }}>
                                            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{t('End Date', '結束日期')}</span>
                                            <input 
                                                type="date" 
                                                value={driftUntil} 
                                                onChange={(e) => setDriftUntil(e.target.value)} 
                                                style={{ ...inputStyle, colorScheme: 'dark' }}
                                            />
                                        </div>
                                    </div>
                                )}
                                <textarea
                                    value={driftNote}
                                    onChange={(event) => setDriftNote(event.target.value)}
                                    rows={3}
                                    placeholder={t('Optional operator note', '可選操作備註')}
                                    style={inputStyle}
                                />
                                <button type="submit" style={buttonPrimaryStyle} disabled={runningDrift}>
                                    {runningDrift ? t('Running...', '執行中...') : t('Run Drift Check', '執行預估偏差檢查')}
                                </button>
                            </form>
                        </section>
                    </div>

                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: isMobile ? '1fr' : 'repeat(2, 1fr)',
                        gap: '16px'
                    }}>
                        <section style={panelStyle}>
                            <h2 style={sectionTitleStyle}>{t('Worker Host', 'Worker 主機')}</h2>
                            <div style={{ display: 'grid', gap: '12px', marginBottom: '16px' }}>
                                <Metric label={t('active_host', '目前主機')} value={summary?.worker_host?.active_host} />
                                <Metric label={t('host_strategy', '主機策略')} value={getTranslation(summary?.worker_host?.host_strategy)} />
                                <Metric label={t('dead_letter_count', '異常任務數量')} value={summary?.worker_host?.dead_letter_count} />
                            </div>

                            <div style={{ marginBottom: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                                <button
                                    type="button"
                                    onClick={handleCleanupStale}
                                    disabled={runningCleanup}
                                    style={{
                                        padding: '10px 16px',
                                        borderRadius: '10px',
                                        border: '1px solid rgba(239, 68, 68, 0.3)',
                                        background: runningCleanup ? 'rgba(239, 68, 68, 0.05)' : 'rgba(239, 68, 68, 0.08)',
                                        color: runningCleanup ? 'var(--text-secondary)' : '#f87171',
                                        fontWeight: 600,
                                        fontSize: '0.88rem',
                                        cursor: runningCleanup ? 'wait' : 'pointer',
                                        textAlign: 'left',
                                    }}
                                >
                                    {runningCleanup
                                        ? t('Cleaning up...', '清除中...')
                                        : t('Clear Stuck Score Events (queued / processing > 30 min)', '清除卡死評分任務（queued / processing 超過 30 分鐘）')}
                                </button>
                                {cleanupResult && (
                                    <div style={{
                                        padding: '12px 14px',
                                        borderRadius: '10px',
                                        border: '1px solid rgba(52, 211, 153, 0.25)',
                                        background: 'rgba(52, 211, 153, 0.06)',
                                        color: 'var(--text-secondary)',
                                        fontSize: '0.85rem',
                                        lineHeight: 1.7,
                                    }}>
                                        <strong style={{ color: '#34d399' }}>
                                            {t('Cleanup complete', '清除完成')} · {cleanupResult.cleaned_total} {t('events terminated', '筆任務已終止')}
                                        </strong>
                                        <div>{t('Cutoff', '截止時間')}: {formatDateTime(cleanupResult.cutoff_timestamp)}</div>
                                        {cleanupResult.removed_scheduler_jobs > 0 && (
                                            <div>{t('Scheduler jobs removed', '已移除排程工作')}: {cleanupResult.removed_scheduler_jobs}</div>
                                        )}
                                    </div>
                                )}
                            </div>

                            <div style={{ marginBottom: '14px' }}>
                                <div style={subTitleStyle}>{t('Recent Worker Events', '最近 Worker 事件')}</div>
                                <div 
                                    className="queue-scroll-box"
                                    style={{ 
                                        display: 'grid', 
                                        gap: '10px',
                                        maxHeight: '350px',
                                        overflowY: 'auto',
                                        paddingRight: '6px'
                                    }}
                                >
                                    {visibleRecentEvents.map((event) => (
                                        <button
                                            key={event.worker_event_id}
                                            type="button"
                                            onClick={() => handleSelectTimeline(event.score_event_id)}
                                            style={{
                                                ...detailCardStyle,
                                                textAlign: 'left',
                                                cursor: 'pointer',
                                                borderColor: selectedScoreEventId === event.score_event_id
                                                    ? 'var(--accent-primary)'
                                                    : 'var(--glass-border)',
                                            }}
                                        >
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                                                <div style={{ color: 'var(--accent-primary)', fontWeight: 700 }}>
                                                    {getTranslation(event.event_type)} · {event.queue_host}
                                                </div>
                                                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                                    {formatDateTime(event.created_at)}
                                                </span>
                                            </div>
                                            <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6, fontSize: '0.9rem' }}>
                                                {t('status', '狀態')}: {getTranslation(event.status)} / {t('attempt', '嘗試次數')}: {event.attempt_count}
                                            </div>
                                            <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6, fontSize: '0.9rem' }}>
                                                {event.score_event_id}
                                            </div>
                                            <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6, fontSize: '0.9rem' }}>
                                                {event.message || '--'}
                                            </div>
                                        </button>
                                    ))}
                                    {visibleRecentEvents.length === 0 && (
                                        <div style={emptyStateStyle}>{t('No worker events match the current filter.', '目前篩選條件下沒有 worker 事件。')}</div>
                                    )}
                                </div>
                            </div>

                            <div>
                                <div style={subTitleStyle}>{t('Dead Letters', '異常任務')}</div>
                                <div 
                                    className="queue-scroll-box"
                                    style={{ 
                                        display: 'grid', 
                                        gap: '10px',
                                        maxHeight: '350px',
                                        overflowY: 'auto',
                                        paddingRight: '6px'
                                    }}
                                >
                                    {visibleDeadLetters.map((item) => (
                                        <button
                                            key={item.dead_letter_id}
                                            type="button"
                                            onClick={() => handleSelectTimeline(item.score_event_id)}
                                            style={{
                                                ...detailCardStyle,
                                                textAlign: 'left',
                                                cursor: 'pointer',
                                                borderColor: selectedScoreEventId === item.score_event_id
                                                    ? '#f59e0b'
                                                    : 'var(--glass-border)',
                                            }}
                                        >
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                                                <div style={{ color: '#f59e0b', fontWeight: 700 }}>
                                                    {getTranslation(item.failure_stage)} · {item.queue_host}
                                                </div>
                                                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                                    {formatDateTime(item.created_at)}
                                                </span>
                                            </div>
                                            <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6, fontSize: '0.9rem' }}>
                                                {item.score_event_id}
                                            </div>
                                            <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6, fontSize: '0.9rem' }}>
                                                {item.final_error_message}
                                            </div>
                                        </button>
                                    ))}
                                    {visibleDeadLetters.length === 0 && (
                                        <div style={emptyStateStyle}>{t('No dead letters match the current filter.', '目前篩選條件下沒有異常任務。')}</div>
                                    )}
                                </div>
                            </div>
                        </section>

                        <section style={panelStyle}>
                            <h2 style={sectionTitleStyle}>{t('Event Timeline', '事件時間軸')}</h2>
                            {!selectedScoreEventId ? (
                                <div style={emptyStateStyle}>{t('Select a worker event or dead letter to inspect the full timeline.', '請先選擇一筆 worker event 或異常任務以查看完整時間軸。')}</div>
                            ) : loadingTimeline ? (
                                <div style={emptyStateStyle}>{t('Loading event timeline...', '載入事件時間軸中...')}</div>
                            ) : !timeline ? (
                                <div style={emptyStateStyle}>{t('Timeline is unavailable.', '目前無法取得時間軸。')}</div>
                            ) : (
                                <div style={{ display: 'grid', gap: '12px' }}>
                                    <div style={detailCardStyle}>
                                        <div style={{ color: 'var(--text-secondary)', marginBottom: '6px' }}>{t('Score Event ID', '評分事件 ID')}</div>
                                        <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{timeline.score_event.score_event_id}</div>
                                        <div style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>
                                            {getTranslation(timeline.score_event.status)} · {t('attempt', '嘗試')} {timeline.score_event.attempt_count}
                                        </div>
                                    </div>
                                    <div style={detailCardStyle}>
                                        <div style={subTitleStyle}>{t('Worker Timeline', 'Worker 時間軸')}</div>
                                        <div style={{ display: 'grid', gap: '10px' }}>
                                            {(timeline.worker_events || []).map((event) => (
                                                <div key={event.worker_event_id} style={timelineItemStyle}>
                                                    <strong style={{ color: 'var(--text-primary)' }}>{getTranslation(event.event_type)}</strong>
                                                    <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                                        {event.queue_host} · {getTranslation(event.status)} · {formatDateTime(event.created_at)}
                                                    </div>
                                                    <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                                        {event.message || '--'}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                    <div style={detailCardStyle}>
                                        <div style={subTitleStyle}>{t('Dead Letter Detail', '異常任務明細')}</div>
                                        {(timeline.dead_letters || []).length === 0 ? (
                                            <div style={{ color: 'var(--text-secondary)' }}>{t('No dead letters for this score event.', '這筆 score event 沒有異常任務紀錄。')}</div>
                                        ) : (
                                            <div style={{ display: 'grid', gap: '10px' }}>
                                                {timeline.dead_letters.map((item) => (
                                                    <div key={item.dead_letter_id} style={timelineItemStyle}>
                                                        <strong style={{ color: '#f59e0b' }}>{getTranslation(item.failure_stage)}</strong>
                                                        <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                                            {item.final_error_message}
                                                        </div>
                                                        <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                                            {formatDateTime(item.created_at)}
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                        </section>

                        <section style={panelStyle}>
                            <h2 style={sectionTitleStyle}>{t('Prediction Distribution', '預測分布')}</h2>
                            <div style={{ display: 'grid', gap: '10px' }}>
                                {Object.entries(summary?.prediction_distribution || {}).map(([band, count]) => (
                                    <div key={band} style={rowStyle}>
                                        <span style={{ color: 'var(--text-secondary)' }}>{getTranslation(band)}</span>
                                        <strong style={{ color: 'var(--text-primary)' }}>{count}</strong>
                                    </div>
                                ))}
                            </div>
                        </section>

                        <section style={panelStyle}>
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
                            <div style={{ display: 'grid', gap: '8px' }}>
                                {(summary?.notes || []).map((note, index) => (
                                    <div key={index} style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                        {note}
                                    </div>
                                ))}
                            </div>
                        </section>

                        <section style={panelStyle}>
                            <h2 style={sectionTitleStyle}>{t('Scoring Profiles', 'Scoring Profiles 管理')}</h2>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                                <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                                    {t('Manage prompt profiles used by the AI scoring model. Calibration auto-generates new profiles after syncing ≥10 mismatch items.', '管理 AI 評分模型使用的 Prompt Profile。校準資料集同步後（≥10 筆誤判），系統自動生成新 profile 待審核。')}
                                </div>
                                <button type="button" onClick={loadProfiles} style={actionButtonStyle}>
                                    {t('Refresh', '重整')}
                                </button>
                            </div>

                            {(() => {
                                const pending = (scoringProfiles?.profiles || []).filter(
                                    (p) => p.source === 'calibration_auto' && !p.is_promoted
                                );
                                if (pending.length === 0) return null;
                                return (
                                    <div style={{
                                        marginBottom: '16px',
                                        padding: '14px',
                                        borderRadius: '12px',
                                        background: 'rgba(245, 158, 11, 0.06)',
                                        border: '1px solid rgba(245, 158, 11, 0.3)',
                                    }}>
                                        <div style={{ fontWeight: 700, color: '#f59e0b', marginBottom: '8px' }}>
                                            {t(`${pending.length} new calibration profile(s) pending review`, `${pending.length} 個新版校準 Profile 待審核`)}
                                        </div>
                                        {pending.map((p) => (
                                            <div key={p.profile_name} style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '10px' }}>
                                                <div style={{ fontSize: '0.88rem', color: 'var(--text-primary)', fontWeight: 600 }}>{p.profile_name}</div>
                                                {p.bias_summary && (
                                                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                                        {t('Bias', '偏差方向')}: <strong style={{ color: '#f59e0b' }}>{p.bias_summary.dominant_bias}</strong>
                                                        {' · '}{t('Items', '樣本')}: {p.bias_summary.total_items}
                                                        {' · '}{t('Over-predict', '預估偏高')}: {p.bias_summary.over_predict_count}
                                                        {' · '}{t('Under-predict', '預估偏低')}: {p.bias_summary.under_predict_count}
                                                    </div>
                                                )}
                                                {p.calibration_guidance && (
                                                    <div style={{ fontSize: '0.78rem', color: '#f59e0b', fontStyle: 'italic', lineHeight: 1.5 }}>
                                                        {p.calibration_guidance.slice(0, 180)}{p.calibration_guidance.length > 180 ? '...' : ''}
                                                    </div>
                                                )}
                                                <button
                                                    type="button"
                                                    onClick={() => handlePromoteProfile(p.profile_name)}
                                                    disabled={promotingProfile === p.profile_name}
                                                    style={{
                                                        alignSelf: 'flex-start',
                                                        padding: '7px 14px',
                                                        borderRadius: '8px',
                                                        border: 'none',
                                                        background: promotingProfile === p.profile_name ? 'rgba(245,158,11,0.3)' : '#f59e0b',
                                                        color: 'white',
                                                        fontWeight: 600,
                                                        fontSize: '0.82rem',
                                                        cursor: promotingProfile === p.profile_name ? 'wait' : 'pointer',
                                                    }}
                                                >
                                                    {promotingProfile === p.profile_name
                                                        ? t('Promoting...', '套用中...')
                                                        : t('Promote This Profile', '套用此 Profile')}
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                );
                            })()}

                            <div
                                className="queue-scroll-box"
                                style={{ display: 'grid', gap: '10px', maxHeight: '320px', overflowY: 'auto', paddingRight: '6px' }}
                            >
                                {loadingProfiles ? (
                                    <div style={emptyStateStyle}>{t('Loading profiles...', '載入 Profiles 中...')}</div>
                                ) : (scoringProfiles?.profiles || []).length === 0 ? (
                                    <div style={emptyStateStyle}>{t('No scoring profiles found.', '尚無 Scoring Profile 記錄。')}</div>
                                ) : (scoringProfiles?.profiles || []).map((p) => (
                                    <div key={p.profile_name} style={{
                                        ...detailCardStyle,
                                        borderColor: p.is_promoted ? 'rgba(52, 211, 153, 0.4)' : 'var(--glass-border)',
                                        background: p.is_promoted ? 'rgba(52, 211, 153, 0.04)' : 'rgba(255,255,255,0.02)',
                                    }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '6px' }}>
                                            <div style={{ fontWeight: 700, color: p.is_promoted ? '#34d399' : 'var(--text-primary)', fontSize: '0.88rem' }}>
                                                {p.profile_name}
                                                {p.is_promoted && (
                                                    <span style={{ marginLeft: '8px', fontSize: '0.72rem', background: 'rgba(52,211,153,0.15)', color: '#34d399', padding: '2px 6px', borderRadius: '4px', fontWeight: 600 }}>
                                                        {t('ACTIVE', '生效中')}
                                                    </span>
                                                )}
                                            </div>
                                            <div style={{ display: 'flex', gap: '6px' }}>
                                                <span style={{
                                                    fontSize: '0.72rem',
                                                    padding: '2px 8px',
                                                    borderRadius: '4px',
                                                    fontWeight: 600,
                                                    background: p.source === 'calibration_auto' ? 'rgba(99,102,241,0.15)' : 'rgba(107,114,128,0.15)',
                                                    color: p.source === 'calibration_auto' ? '#818cf8' : '#9ca3af',
                                                }}>
                                                    {p.source === 'calibration_auto' ? t('auto', '自動校準') : t('seed', '初始')}
                                                </span>
                                            </div>
                                        </div>
                                        <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '6px' }}>
                                            {t('Created', '建立時間')}: {formatDateTime(p.created_at)}
                                            {p.is_promoted && p.promoted_at && (
                                                <span> · {t('Promoted', '套用時間')}: {formatDateTime(p.promoted_at)}</span>
                                            )}
                                            {p.few_shot_example_count > 0 && (
                                                <span> · {p.few_shot_example_count} {t('few-shot examples', '示範案例')}</span>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </section>

                        <section style={panelStyle}>
                            <h2 style={sectionTitleStyle}>{t('Active Alerts', '目前告警')}</h2>
                            <div 
                                className="queue-scroll-box"
                                style={{ 
                                    display: 'grid', 
                                    gap: '10px',
                                    maxHeight: '350px',
                                    overflowY: 'auto',
                                    paddingRight: '6px'
                                }}
                            >
                                {(summary?.active_alerts || []).length === 0 ? (
                                    <div style={emptyStateStyle}>{t('No active alerts.', '目前沒有告警。')}</div>
                                ) : (summary?.active_alerts || []).map((alert, index) => {
                                    const isTransition = alert.code === 'period_state_transition';
                                    const transitionStateColors = {
                                        dual_advantage:   { bg: 'rgba(16,185,129,0.12)',  border: 'rgba(16,185,129,0.4)',  text: '#34d399' },
                                        market_driven:    { bg: 'rgba(59,130,246,0.12)',  border: 'rgba(59,130,246,0.4)',  text: '#60a5fa' },
                                        creative_critical:{ bg: 'rgba(245,158,11,0.12)',  border: 'rgba(245,158,11,0.4)',  text: '#f59e0b' },
                                        needs_review:     { bg: 'rgba(239,68,68,0.12)',   border: 'rgba(239,68,68,0.4)',   text: '#f87171' },
                                    };
                                    const severityColor = { high: '#f87171', medium: '#f59e0b', info: '#60a5fa' };
                                    const headerColor = severityColor[alert.severity] || 'var(--accent-primary)';

                                    if (isTransition) {
                                        const fromC = transitionStateColors[alert.from_state] || transitionStateColors.needs_review;
                                        const toC = transitionStateColors[alert.to_state] || transitionStateColors.needs_review;
                                        const toCardBorder = toC.border;
                                        return (
                                            <div key={index} style={{
                                                ...detailCardStyle,
                                                borderColor: toCardBorder,
                                                background: `linear-gradient(135deg, ${fromC.bg}, ${toC.bg})`,
                                            }}>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', flexWrap: 'wrap' }}>
                                                    <span style={{ fontSize: '0.72rem', color: '#f59e0b', fontWeight: 700, letterSpacing: '0.05em' }}>
                                                        {t('QUADRANT SHIFT', '象限切換')}
                                                    </span>
                                                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                                        <span style={{
                                                            padding: '2px 8px', borderRadius: '5px',
                                                            background: fromC.bg, border: `1px solid ${fromC.border}`,
                                                            color: fromC.text, fontWeight: 700, fontSize: '0.78rem', whiteSpace: 'nowrap',
                                                        }}>
                                                            {alert.from_state ? alert.from_state.replace(/_/g, ' ') : '--'}
                                                        </span>
                                                        <span style={{ color: 'var(--text-secondary)' }}>→</span>
                                                        <span style={{
                                                            padding: '2px 8px', borderRadius: '5px',
                                                            background: toC.bg, border: `1px solid ${toC.border}`,
                                                            color: toC.text, fontWeight: 700, fontSize: '0.78rem', whiteSpace: 'nowrap',
                                                        }}>
                                                            {alert.to_state ? alert.to_state.replace(/_/g, ' ') : '--'}
                                                        </span>
                                                    </div>
                                                </div>
                                                <div style={{ color: 'var(--text-secondary)', lineHeight: 1.7, fontSize: '0.85rem' }}>
                                                    {alert.message.replace(/^【象限切換】[^。]+。/, '')}
                                                </div>
                                            </div>
                                        );
                                    }

                                    return (
                                        <div key={index} style={{
                                            ...detailCardStyle,
                                            borderColor: alert.severity === 'high' ? 'rgba(239,68,68,0.3)' : 'var(--glass-border)',
                                        }}>
                                            <div style={{ color: headerColor, fontWeight: 700, marginBottom: '6px', fontSize: '0.85rem' }}>
                                                {getTranslation(alert.severity)} · {alert.code}
                                            </div>
                                            <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>{alert.message}</div>
                                        </div>
                                    );
                                })}
                            </div>
                        </section>
                    </div>
                </>
            )}

            {/* 投放趨勢 */}
            {!loading && (() => {
                const trendEntries = driftTrend?.entries || [];
                const stateColors = {
                    dual_advantage:   { bg: 'rgba(16,185,129,0.07)',  border: 'rgba(16,185,129,0.35)',  dot: '#34d399', text: '#34d399' },
                    market_driven:    { bg: 'rgba(59,130,246,0.07)',  border: 'rgba(59,130,246,0.35)',  dot: '#60a5fa', text: '#60a5fa' },
                    creative_critical:{ bg: 'rgba(245,158,11,0.07)',  border: 'rgba(245,158,11,0.35)',  dot: '#f59e0b', text: '#f59e0b' },
                    needs_review:     { bg: 'rgba(239,68,68,0.07)',   border: 'rgba(239,68,68,0.35)',   dot: '#f87171', text: '#f87171' },
                };
                const driftStatusColor = { healthy: '#34d399', warning: '#f59e0b', drifted: '#f87171', insufficient_data: '#6b7280' };

                const formatEntryDate = (entry) => {
                    if (entry.window_kind === 'custom' && entry.since && entry.until) {
                        return `${entry.since} ~ ${entry.until}`;
                    }
                    if (entry.note) {
                        const match = entry.note.match(/(\d{4}-\d{2}-\d{2})\s*~\s*(\d{4}-\d{2}-\d{2})/);
                        if (match) return `${match[1]} ~ ${match[2]}`;
                    }
                    if (entry.created_at) return entry.created_at.slice(0, 10);
                    return '--';
                };

                const windowLabel = (wk) => {
                    const map = { last_24h: '24h', last_7d: '7d', last_30d: '30d', lifetime: '全歷史', custom: '自訂' };
                    return map[wk] || wk;
                };

                return (
                    <section style={{ ...panelStyle, marginTop: '16px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                            <h2 style={sectionTitleStyle}>{t('Campaign Environment Trend', '投放趨勢')}</h2>
                            <button type="button" onClick={loadDriftTrend} style={actionButtonStyle}>
                                {t('Refresh', '重整')}
                            </button>
                        </div>

                        {loadingTrend ? (
                            <div style={emptyStateStyle}>{t('Loading trend data...', '載入趨勢資料中...')}</div>
                        ) : trendEntries.length === 0 ? (
                            <div style={emptyStateStyle}>
                                {t('No drift reports yet. Run a drift check to start tracking campaign environment trends.', '尚無預估偏差報告。執行預估偏差檢查以開始追蹤投放環境趨勢。')}
                            </div>
                        ) : (
                            <>
                                {/* 橫向時間軸 */}
                                <div
                                    className="queue-scroll-box"
                                    style={{
                                        overflowX: 'auto',
                                        paddingBottom: '8px',
                                        marginBottom: '20px',
                                    }}
                                >
                                    <div style={{
                                        display: 'flex',
                                        alignItems: 'flex-start',
                                        gap: '0',
                                        minWidth: `${trendEntries.length * 160}px`,
                                        paddingTop: '8px',
                                    }}>
                                        {trendEntries.map((entry, idx) => {
                                            const c = stateColors[entry.period_state] || stateColors.needs_review;
                                            const dColor = driftStatusColor[entry.drift_status] || '#6b7280';
                                            const prevState = idx > 0 ? trendEntries[idx - 1].period_state : null;
                                            const stateChanged = prevState && prevState !== entry.period_state;
                                            const isLast = idx === trendEntries.length - 1;

                                            return (
                                                <div key={entry.drift_report_id} style={{ display: 'flex', alignItems: 'flex-start', flex: 1 }}>
                                                    {/* 連接線 + 節點 */}
                                                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1 }}>
                                                        {/* 時間軸線段 + 節點 */}
                                                        <div style={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                                                            {/* 左側線 */}
                                                            {idx > 0 && (
                                                                <div style={{
                                                                    flex: 1,
                                                                    height: '2px',
                                                                    background: stateChanged
                                                                        ? 'linear-gradient(to right, rgba(107,114,128,0.3), rgba(107,114,128,0.6))'
                                                                        : 'rgba(107,114,128,0.3)',
                                                                }} />
                                                            )}
                                                            {/* 節點圓點 */}
                                                            <div style={{
                                                                width: '14px',
                                                                height: '14px',
                                                                borderRadius: '50%',
                                                                background: c.dot,
                                                                border: stateChanged ? `3px solid ${c.dot}` : `2px solid ${c.dot}`,
                                                                flexShrink: 0,
                                                                boxShadow: stateChanged ? `0 0 8px ${c.dot}` : 'none',
                                                            }} />
                                                            {/* 右側線 */}
                                                            {!isLast && (
                                                                <div style={{
                                                                    flex: 1,
                                                                    height: '2px',
                                                                    background: 'rgba(107,114,128,0.3)',
                                                                }} />
                                                            )}
                                                        </div>

                                                        {/* 節點資訊 */}
                                                        <div style={{ marginTop: '10px', textAlign: 'center', padding: '0 4px' }}>
                                                            {entry.period_label ? (
                                                                <div style={{
                                                                    display: 'inline-block',
                                                                    padding: '2px 8px',
                                                                    borderRadius: '6px',
                                                                    background: c.bg,
                                                                    border: `1px solid ${c.border}`,
                                                                    color: c.text,
                                                                    fontWeight: 700,
                                                                    fontSize: '0.72rem',
                                                                    marginBottom: '4px',
                                                                    whiteSpace: 'nowrap',
                                                                }}>
                                                                    {entry.period_label}
                                                                </div>
                                                            ) : (
                                                                <div style={{
                                                                    display: 'inline-block',
                                                                    padding: '2px 8px',
                                                                    borderRadius: '6px',
                                                                    background: 'rgba(107,114,128,0.1)',
                                                                    border: '1px solid rgba(107,114,128,0.2)',
                                                                    color: '#6b7280',
                                                                    fontWeight: 600,
                                                                    fontSize: '0.72rem',
                                                                    marginBottom: '4px',
                                                                    whiteSpace: 'nowrap',
                                                                }}>
                                                                    {t('No Data', '資料不足')}
                                                                </div>
                                                            )}
                                                            <div style={{ fontSize: '0.7rem', color: dColor, fontWeight: 600, marginBottom: '2px' }}>
                                                                {entry.spearman_r != null ? `ρ=${entry.spearman_r.toFixed(3)}` : '--'}
                                                            </div>
                                                            <div style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                                                                [{windowLabel(entry.window_kind)}]
                                                            </div>
                                                            <div style={{ fontSize: '0.66rem', color: 'var(--text-secondary)', marginTop: '2px', whiteSpace: 'nowrap' }}>
                                                                {formatEntryDate(entry)}
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>

                                {/* 象限切換提醒 */}
                                {(() => {
                                    const transitions = [];
                                    for (let i = 1; i < trendEntries.length; i++) {
                                        const prev = trendEntries[i - 1];
                                        const curr = trendEntries[i];
                                        if (prev.period_state && curr.period_state && prev.period_state !== curr.period_state) {
                                            transitions.push({ from: prev, to: curr, idx: i });
                                        }
                                    }
                                    if (transitions.length === 0) return null;
                                    return (
                                        <div style={{ marginBottom: '16px' }}>
                                            <div style={{ ...subTitleStyle, marginBottom: '8px' }}>
                                                {t('State Transitions', '象限切換紀錄')}
                                            </div>
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                                {transitions.map(({ from, to, idx }) => {
                                                    const fromC = stateColors[from.period_state] || stateColors.needs_review;
                                                    const toC = stateColors[to.period_state] || stateColors.needs_review;
                                                    return (
                                                        <div key={idx} style={{
                                                            padding: '10px 14px',
                                                            borderRadius: '10px',
                                                            background: 'rgba(255,255,255,0.02)',
                                                            border: `1px solid ${toC.border}`,
                                                            display: 'flex',
                                                            alignItems: 'center',
                                                            gap: '10px',
                                                            flexWrap: 'wrap',
                                                        }}>
                                                            <span style={{ fontSize: '0.8rem', color: fromC.text, fontWeight: 700 }}>
                                                                {from.period_label || from.period_state}
                                                            </span>
                                                            <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>→</span>
                                                            <span style={{ fontSize: '0.8rem', color: toC.text, fontWeight: 700 }}>
                                                                {to.period_label || to.period_state}
                                                            </span>
                                                            <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginLeft: 'auto' }}>
                                                                {formatEntryDate(to)}
                                                            </span>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    );
                                })()}

                                {/* 明細列表 */}
                                <div>
                                    <div style={{ ...subTitleStyle, marginBottom: '8px' }}>
                                        {t('Report Detail', '各期報告明細')}
                                    </div>
                                    <div
                                        className="queue-scroll-box"
                                        style={{ display: 'grid', gap: '8px', maxHeight: '320px', overflowY: 'auto', paddingRight: '6px' }}
                                    >
                                        {[...trendEntries].reverse().map((entry) => {
                                            const c = stateColors[entry.period_state] || stateColors.needs_review;
                                            const dColor = driftStatusColor[entry.drift_status] || '#6b7280';
                                            return (
                                                <div key={entry.drift_report_id} style={{
                                                    ...detailCardStyle,
                                                    borderColor: entry.period_state ? c.border : 'var(--glass-border)',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    gap: '12px',
                                                    flexWrap: 'wrap',
                                                }}>
                                                    <div style={{ flex: '0 0 auto' }}>
                                                        {entry.period_label ? (
                                                            <span style={{
                                                                padding: '3px 8px',
                                                                borderRadius: '6px',
                                                                background: c.bg,
                                                                border: `1px solid ${c.border}`,
                                                                color: c.text,
                                                                fontWeight: 700,
                                                                fontSize: '0.78rem',
                                                                whiteSpace: 'nowrap',
                                                            }}>
                                                                {entry.period_label}
                                                            </span>
                                                        ) : (
                                                            <span style={{ fontSize: '0.78rem', color: '#6b7280' }}>--</span>
                                                        )}
                                                    </div>
                                                    <div style={{ flex: 1, minWidth: '120px' }}>
                                                        <div style={{ fontSize: '0.8rem', color: dColor, fontWeight: 600 }}>
                                                            ρ = {entry.spearman_r != null ? entry.spearman_r.toFixed(3) : '--'}
                                                            {entry.creative_explained_variance != null && (
                                                                <span style={{ fontWeight: 400, color: 'var(--text-secondary)' }}>
                                                                    {' '}(ρ²={( entry.creative_explained_variance * 100).toFixed(1)}%)
                                                                </span>
                                                            )}
                                                        </div>
                                                        <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                                                            {entry.perf_median != null && (
                                                                <span>{(entry.dominant_metric || 'ROAS').toUpperCase()} P50={entry.perf_median.toFixed(2)} · </span>
                                                            )}
                                                            {t('Matched', '配對')}: {entry.total_matched ?? '--'}
                                                        </div>
                                                    </div>
                                                    <div style={{ flex: '0 0 auto', textAlign: 'right' }}>
                                                        <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                                                            [{windowLabel(entry.window_kind)}] {formatEntryDate(entry)}
                                                        </div>
                                                        <div style={{ fontSize: '0.7rem', color: driftStatusColor[entry.drift_status] || '#6b7280', marginTop: '2px', fontWeight: 600 }}>
                                                            {getTranslation(entry.drift_status)}
                                                        </div>
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            </>
                        )}
                    </section>
                );
            })()}

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

                                                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginLeft: 'auto' }}>
                                                    ROAS: {item.real_roas.toFixed(2)}
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
        </div>
    );
};

const Metric = ({ label, value }) => (
    <div style={detailCardStyle}>
        <div style={{ color: 'var(--text-secondary)', marginBottom: '6px', fontSize: '0.85rem' }}>{label}</div>
        <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{value ?? '--'}</div>
    </div>
);

const formatPercent = (value) => {
    if (value === null || value === undefined) {
        return '--';
    }
    return `${(Number(value) * 100).toFixed(1)}%`;
};

const badgeStyle = {
    padding: '3px 8px',
    borderRadius: '6px',
    fontSize: '0.76rem',
    fontWeight: 600
};

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

const subTitleStyle = {
    marginBottom: '10px',
    color: 'var(--text-primary)',
    fontSize: '0.9rem',
    fontWeight: 700,
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

const rowStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px 14px',
    borderRadius: '12px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.02)',
};

const errorPanelStyle = {
    marginBottom: '16px',
    padding: '16px',
    borderRadius: '12px',
    background: 'rgba(239, 68, 68, 0.08)',
    border: '1px solid rgba(239, 68, 68, 0.18)',
    color: 'var(--text-primary)',
};

const inputStyle = {
    width: '100%',
    padding: '12px 14px',
    borderRadius: '12px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255, 255, 255, 0.05)',
    color: 'var(--text-primary)',
    outline: 'none',
};

const toggleLabelStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    color: 'var(--text-secondary)',
    fontSize: '0.9rem',
};

const actionButtonStyle = {
    padding: '12px 16px',
    borderRadius: '12px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.04)',
    color: 'var(--text-primary)',
    cursor: 'pointer',
    fontWeight: 700,
};

const buttonPrimaryStyle = {
    padding: '12px 16px',
    borderRadius: '10px',
    border: 'none',
    background: 'var(--accent-primary)',
    color: 'white',
    cursor: 'pointer',
};

const emptyStateStyle = {
    padding: '14px',
    borderRadius: '12px',
    border: '1px dashed var(--glass-border)',
    color: 'var(--text-secondary)',
};

const timelineItemStyle = {
    padding: '12px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.02)',
};

const infoPanelStyle = {
    padding: '12px 14px',
    borderRadius: '12px',
    background: 'rgba(59, 130, 246, 0.08)',
    border: '1px solid rgba(59, 130, 246, 0.18)',
    color: 'var(--text-secondary)',
    lineHeight: 1.7,
};

export default MetaAndromedaMonitoring;
