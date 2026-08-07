import { act, renderHook, waitFor } from '@testing-library/react';

import useAnalyticsObservationImport from '../useAnalyticsObservationImport';
import {
    fetchMetaAndromedaObservedImportStatus,
    importMetaAndromedaObservedFacebookAd,
} from '../../services/metaAndromedaWorkflowService';

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
