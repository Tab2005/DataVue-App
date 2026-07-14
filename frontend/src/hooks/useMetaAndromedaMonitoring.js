import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { useModuleAccess } from './usePermission';
import {
    fetchMetaAndromedaMonitoringSummary,
    fetchMetaAndromedaMonitoringTimeline,
    triggerMetaAndromedaDriftReport,
    syncMetaAndromedaCalibrationDataset,
    cleanupStaleScoreEvents,
    fetchScoringProfiles,
    promoteScoringProfile,
    runScoringProfileBacktest,
    fetchDriftTrend,
    fetchObservedAccounts,
    fetchModelRegistry,
    updateBacktestModel,
    fetchEffectiveScoringStatus,
    validateCandidateModel,
} from '../services/metaAndromedaMonitoringService';

export const useMetaAndromedaMonitoring = ({ language, selectedTeamId }) => {
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
    const [driftAccountId, setDriftAccountId] = useState('');
    const [trendAccountId, setTrendAccountId] = useState('');
    const [selectedDriftReport, setSelectedDriftReport] = useState(null);
    const [excludedObsIds, setExcludedObsIds] = useState(new Set());
    const [syncingCal, setSyncingCal] = useState(false);
    const [cleanupResult, setCleanupResult] = useState(null);
    const [runningCleanup, setRunningCleanup] = useState(false);
    const [scoringProfiles, setScoringProfiles] = useState(null);
    const [loadingProfiles, setLoadingProfiles] = useState(false);
    const [promotingProfile, setPromotingProfile] = useState(null);
    const [backtestingProfile, setBacktestingProfile] = useState(null);
    const [backtestResults, setBacktestResults] = useState({});
    const [driftTrend, setDriftTrend] = useState(null);
    const [loadingTrend, setLoadingTrend] = useState(false);
    const [observedAccounts, setObservedAccounts] = useState([]);
    const [modelRegistry, setModelRegistry] = useState(null);
    const [loadingModelRegistry, setLoadingModelRegistry] = useState(false);
    const [backtestModelInput, setBacktestModelInput] = useState('');
    const [savingBacktestModel, setSavingBacktestModel] = useState(false);
    const [effectiveStatus, setEffectiveStatus] = useState(null);
    const [candidateModelInput, setCandidateModelInput] = useState('');
    const [validatingCandidate, setValidatingCandidate] = useState(false);
    const [candidateValidation, setCandidateValidation] = useState(null);
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
        loadObservedAccounts();
        loadModelRegistry();
        loadEffectiveScoringStatus();
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
                account_id: driftAccountId.trim() || null,
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

    const loadModelRegistry = async () => {
        setLoadingModelRegistry(true);
        try {
            const data = await fetchModelRegistry();
            setModelRegistry(data);
            const backtestEntry = (data?.entries || []).find((e) => e.release_channel === 'backtest_reference');
            if (backtestEntry) {
                setBacktestModelInput(backtestEntry.provider_model);
            }
        } catch (err) {
            setError(err.message || 'Failed to load model registry');
        } finally {
            setLoadingModelRegistry(false);
        }
    };

    const handleSaveBacktestModel = async () => {
        if (!backtestModelInput.trim()) return;
        setSavingBacktestModel(true);
        setError(null);
        try {
            await updateBacktestModel('openrouter', backtestModelInput.trim());
            await loadModelRegistry();
        } catch (err) {
            setError(err.message || 'Failed to save backtest model');
        } finally {
            setSavingBacktestModel(false);
        }
    };

    const loadEffectiveScoringStatus = async () => {
        try {
            const data = await fetchEffectiveScoringStatus();
            setEffectiveStatus(data);
        } catch (err) {
            // 非阻斷性資訊：讀取失敗不影響頁面其餘功能，安靜失敗即可
            setEffectiveStatus(null);
        }
    };

    const handleValidateCandidateModel = async () => {
        if (!candidateModelInput.trim()) return;
        setValidatingCandidate(true);
        setCandidateValidation(null);
        try {
            const data = await validateCandidateModel(candidateModelInput.trim());
            setCandidateValidation(data);
        } catch (err) {
            setCandidateValidation({
                model_id: candidateModelInput.trim(),
                exists: null,
                ok: false,
                issues: [err.message || t('Failed to validate model', '查詢模型失敗')],
            });
        } finally {
            setValidatingCandidate(false);
        }
    };

    const loadObservedAccounts = async () => {
        try {
            const data = await fetchObservedAccounts();
            const accounts = data?.accounts || [];
            setObservedAccounts(accounts);
            // 只有一個帳號時自動預選；多帳號時預設「全部」
            const autoId = accounts.length === 1 ? accounts[0].account_id : '';
            if (accounts.length === 1) {
                setDriftAccountId(autoId);
                setTrendAccountId(autoId);
            }
            // 帳號清單載入後再拉趨勢，確保帶入正確 account_id
            await loadDriftTrend(autoId || null);
        } catch (err) {
            // non-fatal：即使帳號清單失敗也嘗試載入趨勢
            await loadDriftTrend(null);
        }
    };

    const loadDriftTrend = async (accountId = trendAccountId) => {
        setLoadingTrend(true);
        try {
            const data = await fetchDriftTrend(30, accountId || null);
            setDriftTrend(data);
        } catch (err) {
            // non-fatal: trend section shows empty state
        } finally {
            setLoadingTrend(false);
        }
    };

    const handleRunBacktest = async (profileName) => {
        setBacktestingProfile(profileName);
        setError(null);
        try {
            const result = await runScoringProfileBacktest(profileName);
            setBacktestResults((prev) => ({ ...prev, [profileName]: result }));
        } catch (err) {
            setError(err.message || 'Backtest failed');
        } finally {
            setBacktestingProfile(null);
        }
    };

    const handlePromoteProfile = async (profileName, persistedBacktest) => {
        // 優先看剛跑完、還沒 reload 進 scoringProfiles 的最新結果，沒有的話退回已存進
        // profile.bias_summary.holdout_backtest 的舊結果
        const backtest = backtestResults[profileName] || persistedBacktest;
        // calibration_auto 產生的候選 profile 後端會要求先跑過回測且通過才准套用（P1-6 gate），
        // 沒跑過或沒過的話這裡先跟使用者確認是否要用 force 覆寫，而不是讓他們直接撞 409
        const failedGate = backtest && backtest.status === 'evaluated' && backtest.passed_gate === false;
        if (failedGate) {
            if (!window.confirm(language === 'zh'
                ? `這個候選版本的回測結果未通過門檻（並未確定優於目前正式版）。仍要強制套用嗎？`
                : `This candidate did not pass the backtest gate (not confirmed better than production). Force promote anyway?`)) {
                return;
            }
        } else if (!window.confirm(language === 'zh'
            ? `確定要將 "${profileName}" 設為生效中的 Scoring Profile？\n目前生效的 profile 會被取消。`
            : `Promote "${profileName}" as the active Scoring Profile?\nThe current active profile will be deactivated.`)) {
            return;
        }
        setPromotingProfile(profileName);
        setError(null);
        try {
            await promoteScoringProfile(profileName, failedGate);
            await loadProfiles();
        } catch (err) {
            if (err.code === 'holdout_backtest_required') {
                setError(language === 'zh'
                    ? `套用被擋下：尚未執行 holdout 回測。請先點「執行回測」按鈕。`
                    : `Promote blocked: holdout backtest hasn't run yet. Click "Run Backtest" first.`);
            } else {
                setError(err.message || 'Promote failed');
            }
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

    return {
        summary,
        timeline,
        loading,
        loadingTimeline,
        runningDrift,
        error,
        hostFilter,
        setHostFilter,
        eventQuery,
        setEventQuery,
        deadLetterOnly,
        setDeadLetterOnly,
        selectedScoreEventId,
        setSelectedScoreEventId,
        driftWindowKind,
        setDriftWindowKind,
        driftSince,
        setDriftSince,
        driftUntil,
        setDriftUntil,
        driftNote,
        setDriftNote,
        driftAccountId,
        setDriftAccountId,
        trendAccountId,
        setTrendAccountId,
        selectedDriftReport,
        setSelectedDriftReport,
        excludedObsIds,
        setExcludedObsIds,
        syncingCal,
        cleanupResult,
        runningCleanup,
        scoringProfiles,
        loadingProfiles,
        promotingProfile,
        backtestingProfile,
        backtestResults,
        driftTrend,
        loadingTrend,
        observedAccounts,
        modelRegistry,
        loadingModelRegistry,
        backtestModelInput,
        setBacktestModelInput,
        savingBacktestModel,
        effectiveStatus,
        candidateModelInput,
        setCandidateModelInput,
        validatingCandidate,
        candidateValidation,
        hasAccess,
        loadingModuleAccess,
        t,
        getTranslation,
        formatDateTime,
        loadSummary,
        loadTimeline,
        recentEvents,
        deadLetters,
        visibleRecentEvents,
        visibleDeadLetters,
        handleDriftTrigger,
        handleSelectTimeline,
        handleCleanupStale,
        loadProfiles,
        loadModelRegistry,
        handleSaveBacktestModel,
        loadEffectiveScoringStatus,
        handleValidateCandidateModel,
        loadObservedAccounts,
        loadDriftTrend,
        handleRunBacktest,
        handlePromoteProfile,
        handleToggleExcludeObs,
        handleSyncCalibration,
    };
};
