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
import {
    buildMonitoringSearchParams,
    filterMonitoringDeadLetters,
    filterMonitoringRecentEvents,
    formatMonitoringDateTime,
    getCalibrationSyncSuccessMessage,
    getCleanupStaleConfirmMessage,
    getForcePromoteConfirmMessage,
    getHoldoutBacktestRequiredMessage,
    getMonitoringText,
    getMonitoringTranslation,
    getPromoteProfileConfirmMessage,
} from '../utils/metaAndromedaMonitoringLabels';

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

    const t = useMemo(() => getMonitoringText(language), [language]);
    const getTranslation = useMemo(() => (key) => getMonitoringTranslation(key, language), [language]);
    const formatDateTime = formatMonitoringDateTime;

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
        setSearchParams(buildMonitoringSearchParams({ hostFilter, eventQuery, deadLetterOnly, selectedScoreEventId, driftWindowKind, driftSince, driftUntil }), { replace: true });
    }, [hostFilter, eventQuery, deadLetterOnly, selectedScoreEventId, driftWindowKind, driftSince, driftUntil, setSearchParams]);

    useEffect(() => {
        loadTimeline(selectedScoreEventId);
    }, [selectedScoreEventId]);

    const recentEvents = useMemo(() => filterMonitoringRecentEvents(
        summary?.worker_host?.recent_events || [],
        hostFilter,
        eventQuery,
    ), [summary, hostFilter, eventQuery]);

    const deadLetters = useMemo(() => filterMonitoringDeadLetters(
        summary?.worker_host?.dead_letters || [],
        hostFilter,
        eventQuery,
    ), [summary, hostFilter, eventQuery]);

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
        if (!window.confirm(getCleanupStaleConfirmMessage(language))) {
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
        } catch {
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
        } catch {
            // non-fatal：即使帳號清單失敗也嘗試載入趨勢
            await loadDriftTrend(null);
        }
    };

    const loadDriftTrend = async (accountId = trendAccountId) => {
        setLoadingTrend(true);
        try {
            const data = await fetchDriftTrend(30, accountId || null);
            setDriftTrend(data);
        } catch {
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
            if (!window.confirm(getForcePromoteConfirmMessage(language))) {
                return;
            }
        } else if (!window.confirm(getPromoteProfileConfirmMessage(profileName, language))) {
            return;
        }
        setPromotingProfile(profileName);
        setError(null);
        try {
            await promoteScoringProfile(profileName, failedGate);
            await loadProfiles();
        } catch (err) {
            if (err.code === 'holdout_backtest_required') {
                setError(getHoldoutBacktestRequiredMessage(language));
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
            alert(getCalibrationSyncSuccessMessage(result, language));
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
