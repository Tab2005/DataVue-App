import { useEffect, useState } from 'react';

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
import { createReleaseTranslator } from '../components/MetaAndromeda/release/releaseShared';

export const useMetaAndromedaRelease = ({ hasAccess, t }) => {
    const [overview, setOverview] = useState(null);
    const [driftReport, setDriftReport] = useState(null);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);
    const [actionMessage, setActionMessage] = useState(null);

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

    const getTranslation = createReleaseTranslator(t);
    const currentModelVersion = overview?.current_production?.model_version || null;

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
        if (!hasAccess) return;
        loadOverview();
        // Existing page behavior intentionally keeps the initial loader bound to access changes.
        // eslint-disable-next-line react-hooks/exhaustive-deps
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
            if (action === 'approve') payload.force = force;
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
        const csv = `\uFEFF${header.join(',')}\n${rows.join('\n')}`;
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

    return {
        actionMessage,
        backtestError,
        backtestForm,
        backtestLoading,
        backtestRuns,
        createCandidateError,
        creatingBacktest,
        creatingCandidate,
        driftReport,
        error,
        getTranslation,
        handleCreateBacktestRun,
        handleCreateCandidate,
        handleExportMetricPairsCsv,
        handleReleaseAction,
        handleToggleMetricPairs,
        loadBacktestRuns,
        loadMetricPairs,
        loading,
        metricPairs,
        metricPairsError,
        metricPairsLoading,
        metricPairsSort,
        newCandidate,
        overview,
        setBacktestForm,
        setNewCandidate,
        setShowCreateCandidateForm,
        showCreateCandidateForm,
        showMetricPairs,
        submitting,
    };
};
