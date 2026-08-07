import { act, renderHook, waitFor } from '@testing-library/react';

import useAnalyticsObservationImport, { BATCH_IMPORT_CONCURRENCY } from '../useAnalyticsObservationImport';
import {
    fetchMetaAndromedaAiReady,
    fetchMetaAndromedaObservedImportStatus,
    importMetaAndromedaObservedFacebookAd,
} from '../../services/metaAndromedaWorkflowService';

const flushMicrotasks = () => new Promise((resolve) => setTimeout(resolve, 0));

vi.mock('../../services/metaAndromedaWorkflowService', () => ({
    fetchMetaAndromedaAiReady: vi.fn(),
    fetchMetaAndromedaObservedImportStatus: vi.fn(),
    importMetaAndromedaObservedFacebookAd: vi.fn(),
}));

// docs/68 B1：匯入送出後前端要持續輪詢狀態端點，直到匯入/評分都到終態，
// 而不是像修復前那樣只查一次就永遠停在「排隊中」。
describe('useAnalyticsObservationImport polling (docs/68 B1)', () => {
    let observationImportState;
    let setObservationImportState;

    const buildHookProps = (overrides = {}) => ({
        datePreset: 'last_30d',
        dateRange: { since: '2026-07-01', until: '2026-07-30' },
        language: 'zh',
        selectedAccountId: 'act_123456789',
        selectedObservationRows: [],
        setObservationBatchSummary: vi.fn(),
        setObservationImportState,
        ...overrides,
    });

    beforeEach(() => {
        vi.clearAllMocks();
        vi.useFakeTimers();
        observationImportState = {};
        setObservationImportState = vi.fn((updater) => {
            observationImportState = typeof updater === 'function'
                ? updater(observationImportState)
                : updater;
        });
    });

    afterEach(() => {
        vi.useRealTimers();
    });

    it('keeps polling until the import and score both reach a terminal state, then stops', async () => {
        importMetaAndromedaObservedFacebookAd.mockResolvedValue({
            observed_creative_id: 'ma_obs_row_1',
            status: 'accepted',
            score_status: 'pending_observation',
        });
        fetchMetaAndromedaObservedImportStatus
            .mockResolvedValueOnce({
                observed_creative_id: 'ma_obs_row_1',
                observation_status: 'processing',
                score_status: 'pending_observation',
            })
            .mockResolvedValueOnce({
                observed_creative_id: 'ma_obs_row_1',
                observation_status: 'completed',
                score_status: 'queued_background',
            })
            .mockResolvedValueOnce({
                observed_creative_id: 'ma_obs_row_1',
                observation_status: 'completed',
                score_status: 'completed',
            });

        const { result } = renderHook(() => useAnalyticsObservationImport(buildHookProps()));

        await act(async () => {
            await result.current.handleObservationImport({ id: 'row_1', ad_id: '120000000000099' });
        });

        // 第一次檢查（送出後立即查一次）尚未到終態，狀態應為 'polling' 且已排入下一次輪詢。
        expect(fetchMetaAndromedaObservedImportStatus).toHaveBeenCalledTimes(1);
        expect(observationImportState.row_1.status).toBe('polling');
        expect(observationImportState.row_1.observationStatus).toBe('processing');

        // 推進到下一次輪詢間隔：觀測完成但評分仍在背景建立中，仍非終態，繼續輪詢。
        await act(async () => {
            await vi.advanceTimersByTimeAsync(5000);
        });
        expect(fetchMetaAndromedaObservedImportStatus).toHaveBeenCalledTimes(2);
        expect(observationImportState.row_1.status).toBe('polling');
        expect(observationImportState.row_1.scoreStatus).toBe('queued_background');

        // 第三次檢查：觀測與評分都到終態，應停止輪詢並把狀態切到 completed。
        await act(async () => {
            await vi.advanceTimersByTimeAsync(5000);
        });
        expect(fetchMetaAndromedaObservedImportStatus).toHaveBeenCalledTimes(3);
        expect(observationImportState.row_1.status).toBe('completed');
        expect(observationImportState.row_1.scoreStatus).toBe('completed');

        // 到達終態後就不應再排入任何後續輪詢請求。
        await act(async () => {
            await vi.advanceTimersByTimeAsync(60000);
        });
        expect(fetchMetaAndromedaObservedImportStatus).toHaveBeenCalledTimes(3);
    });

    it('stops auto-refreshing after the timeout window and unblocks the row for manual retry', async () => {
        importMetaAndromedaObservedFacebookAd.mockResolvedValue({
            observed_creative_id: 'ma_obs_row_2',
            status: 'accepted',
            score_status: 'pending_observation',
        });
        // 一直卡在 processing，永遠不會自然到終態，模擬長時間排隊的情境。
        fetchMetaAndromedaObservedImportStatus.mockResolvedValue({
            observed_creative_id: 'ma_obs_row_2',
            observation_status: 'processing',
            score_status: 'pending_observation',
        });

        const { result } = renderHook(() => useAnalyticsObservationImport(buildHookProps()));

        await act(async () => {
            await result.current.handleObservationImport({ id: 'row_2', ad_id: '120000000000088' });
        });
        expect(observationImportState.row_2.status).toBe('polling');

        // 推進超過 2 分鐘逾時上限：應停止輪詢，並把狀態切到不屬於
        // loading/accepted/polling 的值，讓匯入按鈕重新可按（供使用者手動重試）。
        await act(async () => {
            await vi.advanceTimersByTimeAsync(125000);
        });

        expect(observationImportState.row_2.status).toBe('timed_out');
        expect(['loading', 'accepted', 'polling']).not.toContain(observationImportState.row_2.status);

        const callCountAtTimeout = fetchMetaAndromedaObservedImportStatus.mock.calls.length;
        await act(async () => {
            await vi.advanceTimersByTimeAsync(30000);
        });
        expect(fetchMetaAndromedaObservedImportStatus).toHaveBeenCalledTimes(callCountAtTimeout);
    });

    it('clears in-flight poll timers on unmount so no state update fires after the component is gone', async () => {
        importMetaAndromedaObservedFacebookAd.mockResolvedValue({
            observed_creative_id: 'ma_obs_row_3',
            status: 'accepted',
            score_status: 'pending_observation',
        });
        fetchMetaAndromedaObservedImportStatus.mockResolvedValue({
            observed_creative_id: 'ma_obs_row_3',
            observation_status: 'processing',
            score_status: 'pending_observation',
        });

        const { result, unmount } = renderHook(() => useAnalyticsObservationImport(buildHookProps()));

        await act(async () => {
            await result.current.handleObservationImport({ id: 'row_3', ad_id: '120000000000077' });
        });
        const callCountBeforeUnmount = fetchMetaAndromedaObservedImportStatus.mock.calls.length;

        unmount();

        await act(async () => {
            await vi.advanceTimersByTimeAsync(30000);
        });

        // 卸載後排定的輪詢應被清掉，不會再打狀態端點。
        expect(fetchMetaAndromedaObservedImportStatus).toHaveBeenCalledTimes(callCountBeforeUnmount);
    });
});

// docs/68 B2：批次送出改以有限併發處理，避免 N 筆選取變成 N 次嚴格序列往返
// （每筆都要等前一筆完全處理完才送下一筆，50 筆在正常網路延遲下要等超過十秒）。
describe('useAnalyticsObservationImport batch concurrency (docs/68 B2)', () => {
    let observationImportState;
    let setObservationImportState;
    let observationBatchSummary;
    let setObservationBatchSummary;

    const buildHookProps = (overrides = {}) => ({
        datePreset: 'last_30d',
        dateRange: { since: '2026-07-01', until: '2026-07-30' },
        language: 'zh',
        selectedAccountId: 'act_123456789',
        selectedObservationRows: [],
        setObservationBatchSummary,
        setObservationImportState,
        ...overrides,
    });

    beforeEach(() => {
        vi.clearAllMocks();
        observationImportState = {};
        setObservationImportState = vi.fn((updater) => {
            observationImportState = typeof updater === 'function'
                ? updater(observationImportState)
                : updater;
        });
        observationBatchSummary = null;
        setObservationBatchSummary = vi.fn((updater) => {
            observationBatchSummary = typeof updater === 'function'
                ? updater(observationBatchSummary)
                : updater;
        });
        fetchMetaAndromedaAiReady.mockResolvedValue({ ready: true });
        fetchMetaAndromedaObservedImportStatus.mockResolvedValue({
            observation_status: 'completed',
            score_status: 'completed',
        });
    });

    it('caps in-flight batch import requests at BATCH_IMPORT_CONCURRENCY instead of sending them fully serially or all at once', async () => {
        const totalRows = 9;
        const rows = Array.from({ length: totalRows }, (_, i) => ({
            id: `row_${i}`,
            ad_id: `1200000${String(i).padStart(5, '0')}`,
        }));

        const pendingResolvers = [];
        importMetaAndromedaObservedFacebookAd.mockImplementation(() => new Promise((resolve) => {
            pendingResolvers.push(resolve);
        }));

        const { result } = renderHook(() => useAnalyticsObservationImport(
            buildHookProps({ selectedObservationRows: rows }),
        ));

        let batchDone = false;
        let batchPromise;
        await act(async () => {
            batchPromise = result.current.handleBatchObservationImport().then(() => {
                batchDone = true;
            });
            await flushMicrotasks();
        });

        // 第一波應該只送出「併發上限」筆請求，而不是 9 筆一次全送出，也不是只送 1 筆。
        expect(importMetaAndromedaObservedFacebookAd).toHaveBeenCalledTimes(BATCH_IMPORT_CONCURRENCY);
        expect(batchDone).toBe(false);

        // 逐波釋放目前卡住的請求：驗證釋放後才會接著送出下一批，符合
        // work-stealing（有 worker 空出來才拿下一筆），而非固定切批次。
        let safetyCounter = 0;
        while (
            importMetaAndromedaObservedFacebookAd.mock.calls.length < totalRows
            && safetyCounter < totalRows
        ) {
            const toRelease = pendingResolvers.splice(0, pendingResolvers.length);
            expect(toRelease.length).toBeGreaterThan(0);
            await act(async () => {
                toRelease.forEach((resolve) => resolve({
                    observed_creative_id: `ma_obs_batch_${safetyCounter}`,
                    status: 'accepted',
                    score_status: 'pending_observation',
                }));
                await flushMicrotasks();
            });
            safetyCounter += 1;
        }

        expect(importMetaAndromedaObservedFacebookAd).toHaveBeenCalledTimes(totalRows);

        // 釋放最後一波，讓批次真正跑完。
        await act(async () => {
            pendingResolvers.splice(0).forEach((resolve) => resolve({
                observed_creative_id: 'ma_obs_batch_last',
                status: 'accepted',
                score_status: 'pending_observation',
            }));
            await batchPromise;
        });

        expect(batchDone).toBe(true);
        expect(observationBatchSummary.successCount).toBe(totalRows);
        expect(observationBatchSummary.failureCount).toBe(0);
    });
});
