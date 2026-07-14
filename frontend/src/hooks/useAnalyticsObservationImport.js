import { useCallback } from 'react';

import {
    fetchMetaAndromedaAiReady,
    fetchMetaAndromedaObservedImportStatus,
    importMetaAndromedaObservedFacebookAd,
} from '../services/metaAndromedaWorkflowService';
import { resolveObservationWindowKind } from '../components/Analytics/analyticsMetrics';

const useAnalyticsObservationImport = ({
    datePreset,
    dateRange,
    language,
    selectedAccountId,
    selectedObservationRows,
    setObservationBatchSummary,
    setObservationImportState,
}) => {
    const submitObservationRow = useCallback(async (row) => {
        if (!row?.ad_id || !selectedAccountId) {
            const message = language === 'zh'
                ? '缺少廣告或帳號資訊，無法匯入。'
                : 'Missing ad or account information.';
            setObservationImportState((prev) => ({
                ...prev,
                [row?.id || 'unknown']: {
                    status: 'failed',
                    observationStatus: 'failed',
                    scoreStatus: 'blocked_by_observation_failure',
                    message,
                },
            }));
            return { ok: false };
        }

        const rowKey = row.id;
        setObservationImportState((prev) => ({
            ...prev,
            [rowKey]: {
                ...(prev[rowKey] || {}),
                status: 'loading',
                observationStatus: 'queued',
                scoreStatus: 'pending_observation',
                message: language === 'zh' ? '送出匯入請求中...' : 'Submitting import request...',
            },
        }));

        try {
            const observationWindowKind = resolveObservationWindowKind(datePreset);
            const payload = {
                account_id: selectedAccountId,
                ad_id: row.ad_id,
                observation_window_kind: observationWindowKind,
                since: observationWindowKind === 'custom' ? dateRange.since : undefined,
                until: observationWindowKind === 'custom' ? dateRange.until : undefined,
                market: 'TW',
                placement_family: 'all',
                primary_text: row.primary_text || row.body || null,
                headline: row.headline || row.title || row.name || null,
                cta: row.cta || null,
            };

            const accepted = await importMetaAndromedaObservedFacebookAd(payload);
            const observedCreativeId = accepted?.observed_creative_id;

            setObservationImportState((prev) => ({
                ...prev,
                [rowKey]: {
                    ...(prev[rowKey] || {}),
                    status: 'accepted',
                    observedCreativeId,
                    observationStatus: accepted?.status === 'accepted' ? 'queued' : (accepted?.status || 'queued'),
                    scoreStatus: accepted?.score_status || 'pending_observation',
                    message: language === 'zh' ? '已送出，等待背景匯入。' : 'Accepted, waiting for background import.',
                },
            }));

            if (observedCreativeId) {
                try {
                    const status = await fetchMetaAndromedaObservedImportStatus(observedCreativeId);
                    setObservationImportState((prev) => ({
                        ...prev,
                        [rowKey]: {
                            ...(prev[rowKey] || {}),
                            status: status?.observation_status === 'completed' || status?.observation_status === 'failed'
                                ? status.observation_status
                                : 'polling',
                            observedCreativeId,
                            observationStatus: status?.observation_status || 'queued',
                            scoreStatus: status?.score_status || accepted?.score_status || 'pending_observation',
                            message: status?.observation_message || (language === 'zh' ? '匯入狀態已更新。' : 'Import status updated.'),
                        },
                    }));
                } catch {
                    setObservationImportState((prev) => ({
                        ...prev,
                        [rowKey]: {
                            ...(prev[rowKey] || {}),
                            status: 'polling',
                            observedCreativeId,
                            message: language === 'zh' ? '已送出，暫時無法讀取最新狀態。' : 'Accepted; latest status is not available yet.',
                        },
                    }));
                }
            }

            return { ok: true };
        } catch (err) {
            setObservationImportState((prev) => ({
                ...prev,
                [rowKey]: {
                    ...(prev[rowKey] || {}),
                    status: 'failed',
                    observationStatus: 'failed',
                    scoreStatus: 'blocked_by_observation_failure',
                    message: err?.message || (language === 'zh' ? '匯入失敗。' : 'Import failed.'),
                },
            }));
            return { ok: false };
        }
    }, [datePreset, dateRange, language, selectedAccountId, setObservationImportState]);

    const handleObservationImport = useCallback(async (row) => {
        await submitObservationRow(row);
    }, [submitObservationRow]);

    const handleBatchObservationImport = useCallback(async () => {
        if (!selectedObservationRows.length) {
            return;
        }

        try {
            const aiStatus = await fetchMetaAndromedaAiReady();
            if (aiStatus && !aiStatus.ready && aiStatus.warning) {
                const continueAnyway = window.confirm(
                    (language === 'zh' ? '⚠️ AI 評分連線異常\n\n' : '⚠️ AI Scoring Unavailable\n\n') +
                    aiStatus.warning +
                    (language === 'zh'
                        ? '\n\n是否仍要繼續批次匯入？（評分將使用啟發式備用模式）'
                        : '\n\nContinue with batch import anyway? (Scoring will use heuristic fallback)')
                );
                if (!continueAnyway) return;
            }
        } catch {
            // AI readiness failures should not block observation import.
        }

        setObservationBatchSummary({
            status: 'loading',
            attemptedCount: selectedObservationRows.length,
            successCount: 0,
            failureCount: 0,
            message: language === 'zh'
                ? `批次送出中，共 ${selectedObservationRows.length} 筆。`
                : `Batch submission in progress for ${selectedObservationRows.length} ads.`,
        });

        let successCount = 0;
        let failureCount = 0;

        for (const row of selectedObservationRows) {
            const result = await submitObservationRow(row);
            if (result.ok) {
                successCount += 1;
            } else {
                failureCount += 1;
            }
        }

        setObservationBatchSummary({
            status: failureCount === 0 ? 'success' : 'warning',
            attemptedCount: selectedObservationRows.length,
            successCount,
            failureCount,
            message: language === 'zh'
                ? `批次送出完成，成功送出 ${successCount} 筆，失敗 ${failureCount} 筆。`
                : `Batch submission completed: ${successCount} accepted, ${failureCount} failed.`,
        });
    }, [language, selectedObservationRows, setObservationBatchSummary, submitObservationRow]);

    return {
        handleBatchObservationImport,
        handleObservationImport,
    };
};

export default useAnalyticsObservationImport;
