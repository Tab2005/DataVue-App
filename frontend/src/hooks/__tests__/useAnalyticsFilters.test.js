import { renderHook, act } from '@testing-library/react';

import { useAnalyticsFilters } from '../useAnalyticsFilters';

// P2-3 補強測試覆蓋：篩選狀態轉換（關鍵字 include/exclude、狀態、觀測匯入）。
describe('useAnalyticsFilters', () => {
    const rows = [
        { id: 'ad_1', name: 'Summer Sale', status: 'ACTIVE' },
        { id: 'ad_2', name: 'Winter Sale', status: 'PAUSED' },
        { id: 'ad_3', campaign_name: 'Spring Launch', status: 'ACTIVE' },
    ];

    const buildProps = (overrides = {}) => ({
        reportData: rows,
        prevReportData: rows,
        observationImportState: {},
        level: 'ad',
        ...overrides,
    });

    it('returns all rows unfiltered by default', () => {
        const { result } = renderHook(() => useAnalyticsFilters(buildProps()));

        expect(result.current.filteredData).toHaveLength(3);
        expect(result.current.filteredPrevData).toHaveLength(3);
    });

    it('filters to ACTIVE rows only when filterActiveOnly is enabled', () => {
        const { result } = renderHook(() => useAnalyticsFilters(buildProps()));

        act(() => result.current.setFilterActiveOnly(true));

        expect(result.current.filteredData.map((r) => r.id)).toEqual(['ad_1', 'ad_3']);
    });

    it('include mode keeps only rows whose name matches the keyword', () => {
        const { result } = renderHook(() => useAnalyticsFilters(buildProps()));

        act(() => result.current.setFilterKeyword('sale'));

        expect(result.current.filteredData.map((r) => r.id)).toEqual(['ad_1', 'ad_2']);
    });

    it('exclude mode drops rows whose name matches the keyword', () => {
        const { result } = renderHook(() => useAnalyticsFilters(buildProps()));

        act(() => {
            result.current.setFilterKeyword('sale');
            result.current.setFilterMode('exclude');
        });

        expect(result.current.filteredData.map((r) => r.id)).toEqual(['ad_3']);
    });

    it('matches against campaign_name/adset_name/ad_name fallback fields', () => {
        const { result } = renderHook(() => useAnalyticsFilters(buildProps()));

        act(() => result.current.setFilterKeyword('spring'));

        expect(result.current.filteredData.map((r) => r.id)).toEqual(['ad_3']);
    });

    it('keyword filter is case-insensitive', () => {
        const { result } = renderHook(() => useAnalyticsFilters(buildProps()));

        act(() => result.current.setFilterKeyword('SUMMER'));

        expect(result.current.filteredData.map((r) => r.id)).toEqual(['ad_1']);
    });

    it('only trim() is used for the blank-keyword check; surrounding whitespace inside a non-blank keyword is not stripped before matching', () => {
        const { result } = renderHook(() => useAnalyticsFilters(buildProps()));

        act(() => result.current.setFilterKeyword('  summer  '));

        // 名稱不包含帶前後空白的 "  summer  " 字面字串，故無結果——這是
        // 目前實作的實際行為（trim() 只用來判斷關鍵字是否為空白，比對時
        // 用的仍是未 trim 的原字串），而不是把它當成一個規格要求。
        expect(result.current.filteredData).toEqual([]);
    });

    it('a purely-whitespace keyword is treated as empty and disables the keyword filter', () => {
        const { result } = renderHook(() => useAnalyticsFilters(buildProps()));

        act(() => result.current.setFilterKeyword('   '));

        expect(result.current.filteredData).toHaveLength(3);
    });

    it('observation filter only applies when level is "ad"', () => {
        const observationImportState = { ad_1: { observationStatus: 'completed' } };
        const { result } = renderHook(() =>
            useAnalyticsFilters(buildProps({ observationImportState, level: 'campaign' }))
        );

        act(() => result.current.setFilterObservationImported('imported'));

        // level 不是 'ad' 時，觀測匯入篩選不生效
        expect(result.current.filteredData).toHaveLength(3);
    });

    it('"imported" keeps only rows whose observation status is completed', () => {
        const observationImportState = {
            ad_1: { observationStatus: 'completed' },
            ad_2: { observationStatus: 'processing' },
        };
        const { result } = renderHook(() =>
            useAnalyticsFilters(buildProps({ observationImportState }))
        );

        act(() => result.current.setFilterObservationImported('imported'));

        expect(result.current.filteredData.map((r) => r.id)).toEqual(['ad_1']);
    });

    it('"not_imported" excludes rows whose observation status is completed', () => {
        const observationImportState = {
            ad_1: { observationStatus: 'completed' },
            ad_2: { observationStatus: 'processing' },
        };
        const { result } = renderHook(() =>
            useAnalyticsFilters(buildProps({ observationImportState }))
        );

        act(() => result.current.setFilterObservationImported('not_imported'));

        expect(result.current.filteredData.map((r) => r.id)).toEqual(['ad_2', 'ad_3']);
    });

    it('returns an empty array when reportData is null/undefined', () => {
        const { result } = renderHook(() =>
            useAnalyticsFilters(buildProps({ reportData: null, prevReportData: undefined }))
        );

        expect(result.current.filteredData).toEqual([]);
        expect(result.current.filteredPrevData).toEqual([]);
    });

    it('applies filters independently to reportData and prevReportData', () => {
        const prevRows = [{ id: 'ad_9', name: 'Old Sale', status: 'ACTIVE' }];
        const { result } = renderHook(() =>
            useAnalyticsFilters(buildProps({ prevReportData: prevRows }))
        );

        act(() => result.current.setFilterKeyword('sale'));

        expect(result.current.filteredData.map((r) => r.id)).toEqual(['ad_1', 'ad_2']);
        expect(result.current.filteredPrevData.map((r) => r.id)).toEqual(['ad_9']);
    });
});
