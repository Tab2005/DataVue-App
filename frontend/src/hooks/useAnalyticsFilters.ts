// frontend/src/hooks/useAnalyticsFilters.ts (docs/33 第 7 波：Analytics.jsx 組合層瘦身)
//
// 關鍵字/狀態/觀測匯入篩選，原本內嵌在 Analytics.jsx，且 filteredData 與
// filteredPrevData 兩份幾乎一模一樣的篩選邏輯重複貼了一次——這裡合併成
// 一個 applyFilters 共用，兩邊呼叫。
import { useMemo, useState } from 'react';

export interface AnalyticsRow {
    id?: string | number;
    status?: string;
    name?: string;
    campaign_name?: string;
    adset_name?: string;
    ad_name?: string;
    [key: string]: unknown;
}

export type AnalyticsFilterMode = 'include' | 'exclude';
export type ObservationImportFilter = 'all' | 'imported' | 'not_imported';

export interface ObservationImportEntry {
    observationStatus?: string;
    [key: string]: unknown;
}

export type ObservationImportState = Record<string | number, ObservationImportEntry | undefined>;

const applyFilters = (
    rows: AnalyticsRow[] | null | undefined,
    filterActiveOnly: boolean,
    filterKeyword: string,
    filterMode: AnalyticsFilterMode,
    level: string,
    filterObservationImported: ObservationImportFilter,
    observationImportState: ObservationImportState
): AnalyticsRow[] => {
    if (!rows) return [];
    return rows.filter(row => {
        // 1. Status Filter
        if (filterActiveOnly) {
            const status = (row.status || '').toUpperCase();
            if (status !== 'ACTIVE') return false;
        }

        // 2. Keyword Filter
        if (filterKeyword.trim()) {
            const keyword = filterKeyword.toLowerCase();
            // Check all name fields
            const name = (row.name || row.campaign_name || row.adset_name || row.ad_name || '').toLowerCase();
            const match = name.includes(keyword);

            if (filterMode === 'include') {
                if (!match) return false;
            } else {
                if (match) return false;
            }
        }

        // 3. Observation Filter (Only when level is 'ad')
        if (level === 'ad' && filterObservationImported !== 'all') {
            const importState = row.id !== undefined ? observationImportState[row.id]?.observationStatus : undefined;
            if (filterObservationImported === 'imported') {
                if (importState !== 'completed') return false;
            } else if (filterObservationImported === 'not_imported') {
                if (importState === 'completed') return false;
            }
        }

        return true;
    });
};

export interface UseAnalyticsFiltersParams {
    reportData: AnalyticsRow[] | null | undefined;
    prevReportData: AnalyticsRow[] | null | undefined;
    observationImportState: ObservationImportState;
    level: string;
}

export const useAnalyticsFilters = ({ reportData, prevReportData, observationImportState, level }: UseAnalyticsFiltersParams) => {
    const [filterKeyword, setFilterKeyword] = useState('');
    const [filterMode, setFilterMode] = useState<AnalyticsFilterMode>('include'); // include, exclude
    const [filterActiveOnly, setFilterActiveOnly] = useState(false);
    const [filterObservationImported, setFilterObservationImported] = useState<ObservationImportFilter>('all'); // 'all', 'imported', 'not_imported'

    const filteredData = useMemo(
        () => applyFilters(reportData, filterActiveOnly, filterKeyword, filterMode, level, filterObservationImported, observationImportState),
        [reportData, filterKeyword, filterMode, filterActiveOnly, filterObservationImported, observationImportState, level]
    );

    const filteredPrevData = useMemo(
        () => applyFilters(prevReportData, filterActiveOnly, filterKeyword, filterMode, level, filterObservationImported, observationImportState),
        [prevReportData, filterKeyword, filterMode, filterActiveOnly, filterObservationImported, observationImportState, level]
    );

    return {
        filterKeyword, setFilterKeyword,
        filterMode, setFilterMode,
        filterActiveOnly, setFilterActiveOnly,
        filterObservationImported, setFilterObservationImported,
        filteredData,
        filteredPrevData,
    };
};

export default useAnalyticsFilters;
