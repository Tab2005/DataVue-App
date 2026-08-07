import { useCallback, useEffect, useRef } from 'react';

import {
    fetchMetaAndromedaAiReady,
    fetchMetaAndromedaObservedImportStatus,
    importMetaAndromedaObservedFacebookAd,
} from '../services/metaAndromedaWorkflowService';
import { resolveObservationWindowKind } from '../components/Analytics/analyticsMetrics';

// 觀測匯入是背景 job（202 立即受理，實際處理與自動評分在 worker 完成），送出後
// 需要持續輪詢狀態端點才能讓 UI 徽章反映真實進度；否則畫面會永遠停在「排隊中」
// 直到使用者手動重新整理（docs/68 B1）。
const OBSERVATION_STATUS_POLL_INTERVAL_MS = 5000;
const OBSERVATION_STATUS_POLL_TIMEOUT_MS = 120000;

// 批次送出時同時在飛的匯入請求數上限（docs/68 B2）：後端 POST 只是排入背景 job
// 就立即回 202，真正的下載/存檔/評分都在 worker 端進行，前端逐筆嚴格序列送出
// 純粹是白白等待網路往返——50 筆在 200ms RTT 下要等 10 秒以上才顯示「批次完成」。
// 限制併發數而非全部一次送出，避免瞬間對後端/worker 造成過大突發負載。
export const BATCH_IMPORT_CONCURRENCY = 4;

const TERMINAL_OBSERVATION_STATUSES = new Set(['completed', 'failed']);
const TERMINAL_SCORE_STATUSES = new Set([
    'completed',
    'failed',
    'skipped_no_asset',
    'blocked_by_observation_failure',
]);

// 匯入本身失敗時評分不會再啟動，此時 observation_status=failed 即已是終態，
// 不需要再等 score_status；其餘情況要匯入與評分都到終態才算真正結束。
const isImportStatusTerminal = (status) => {
    if (!status || !TERMINAL_OBSERVATION_STATUSES.has(status.observation_status)) {
        return false;
    }
    if (status.observation_status === 'failed') {
        return true;
    }
    return !status.score_status || TERMINAL_SCORE_STATUSES.has(status.score_status);
};

// 以固定併發上限跑完 items，每個 worker 完成一項就立刻接手下一項（work-stealing），
// 不是把 items 死板切成固定批次——較慢的請求不會拖住其他 worker 提早去拿下一筆。
const runWithConcurrencyLimit = async (items, limit, worker) => {
    const results = new Array(items.length);
    let nextIndex = 0;

    const runNext = async () => {
        for (;;) {
            const currentIndex = nextIndex;
            nextIndex += 1;
            if (currentIndex >= items.length) {
                return;
            }
            results[currentIndex] = await worker(items[currentIndex], currentIndex);
        }
    };

    const workerCount = Math.min(limit, items.length);
    await Promise.all(Array.from({ length: workerCount }, runNext));

    return results;
};

const useAnalyticsObservationImport = ({
    datePreset,
    dateRange,
    language,
    selectedAccountId,
    selectedObservationRows,
    setObservationBatchSummary,
    setObservationImportState,
}) => {
    // rowKey -> setTimeout id，元件卸載或該列重新送出匯入時要能清掉舊的輪詢鏈，
    // 避免對已卸載元件呼叫 setState，或同一列同時存在兩條輪詢鏈。
    const pollTimersRef = useRef({});
    const isMountedRef = useRef(true);

    useEffect(() => {
        isMountedRef.current = true;
        const timers = pollTimersRef.current;
        return () => {
            isMountedRef.current = false;
            Object.values(timers).forEach(clearTimeout);
            pollTimersRef.current = {};
        };
    }, []);

    const stopPollingForRow = useCallback((rowKey) => {
        const timerId = pollTimersRef.current[rowKey];
        if (timerId) {
            clearTimeout(timerId);
            delete pollTimersRef.current[rowKey];
        }
    }, []);

    // 檢查一次狀態；若尚未到終態且未逾時，排入下一次檢查。遞迴透過 setTimeout
    // （而非 setInterval）串接，確保上一次請求還沒回來時不會疊加下一次請求。
    const checkObservationStatusOnce = useCallback(async (rowKey, observedCreativeId, startedAt) => {
        if (!isMountedRef.current) return;

        let status;
        try {
            status = await fetchMetaAndromedaObservedImportStatus(observedCreativeId);
        } catch {
            if (!isMountedRef.current) return;
            if (Date.now() - startedAt < OBSERVATION_STATUS_POLL_TIMEOUT_MS) {
                const timerId = setTimeout(
                    () => checkObservationStatusOnce(rowKey, observedCreativeId, startedAt),
                    OBSERVATION_STATUS_POLL_INTERVAL_MS,
                );
                pollTimersRef.current[rowKey] = timerId;
            } else {
                stopPollingForRow(rowKey);
            }
            return;
        }
        if (!isMountedRef.current) return;

        const terminal = isImportStatusTerminal(status);
        setObservationImportState((prev) => ({
            ...prev,
            [rowKey]: {
                ...(prev[rowKey] || {}),
                status: terminal
                    ? (status.observation_status === 'failed' ? 'failed' : 'completed')
                    : 'polling',
                observedCreativeId,
                observationStatus: status?.observation_status,
                scoreStatus: status?.score_status,
                message: status?.observation_message || (prev[rowKey] || {}).message,
            },
        }));

        if (terminal) {
            stopPollingForRow(rowKey);
            return;
        }

        if (Date.now() - startedAt >= OBSERVATION_STATUS_POLL_TIMEOUT_MS) {
            stopPollingForRow(rowKey);
            setObservationImportState((prev) => ({
                ...prev,
                [rowKey]: {
                    ...(prev[rowKey] || {}),
                    // 特意不落在 'loading'/'accepted'/'polling' 集合內，讓匯入按鈕重新可按，
                    // 使用者可手動重試或稍後自行重新整理查看最新狀態。
                    status: 'timed_out',
                    message: language === 'zh'
                        ? '已停止自動更新最新狀態，可稍後重新整理查看，或重新送出匯入。'
                        : 'Stopped auto-refreshing status; refresh later or resubmit the import.',
                },
            }));
            return;
        }

        const timerId = setTimeout(
            () => checkObservationStatusOnce(rowKey, observedCreativeId, startedAt),
            OBSERVATION_STATUS_POLL_INTERVAL_MS,
        );
        pollTimersRef.current[rowKey] = timerId;
    }, [language, setObservationImportState, stopPollingForRow]);

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
        stopPollingForRow(rowKey);
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
                // 第一次檢查立即進行（維持既有的「送出後馬上看到一次更新」體感），
                // 若尚未到終態，checkObservationStatusOnce 內部會自行排入後續輪詢，
                // 這裡不 await 整條輪詢鏈，批次送出才不會被單一列的背景進度卡住。
                await checkObservationStatusOnce(rowKey, observedCreativeId, Date.now());
            }

            return { ok: true };
        } catch (err) {
            stopPollingForRow(rowKey);
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
    }, [checkObservationStatusOnce, datePreset, dateRange, language, selectedAccountId, setObservationImportState, stopPollingForRow]);

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

        // docs/68 B2：以有限併發（而非逐筆嚴格序列）送出，大幅縮短「批次送出中」
        // 卡住使用者的時間——每筆本身只是快速的 202 受理 + 一次狀態檢查，序列送出
        // 純粹是白白等待網路往返，並不會減少後端/worker 負擔。
        const results = await runWithConcurrencyLimit(
            selectedObservationRows,
            BATCH_IMPORT_CONCURRENCY,
            submitObservationRow,
        );

        let successCount = 0;
        let failureCount = 0;
        for (const result of results) {
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
