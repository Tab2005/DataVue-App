// frontend/src/hooks/useAnalyticsObservationSelection.js (docs/33 第 7 波：Analytics.jsx 組合層瘦身)
//
// 「成效分析匯入 Meta Andromeda」的選取狀態 + 狀態文字對照，原本內嵌在
// Analytics.jsx，並在這裡直接組合既有的 useAnalyticsObservationImport
// （負責實際送出匯入請求），讓頁面只拿最終需要的一組結果。
//
// observationImportState/observationBatchSummary 兩個 state 由頁面層擁有
// 並傳入（不是這裡自己 useState）——因為 useAnalyticsFilters 的
// filteredData 計算也需要讀 observationImportState（依匯入狀態篩選列），
// 而這個 hook 又需要 filteredData 來算 observationImportableRows，兩個
// hook 互相需要對方的輸出/輸入；把這兩個 state 的「擁有權」留在頁面層、
// 兩邊都當唯讀輸入（或拿 setter 寫入），就不會出現循環依賴。
import { useCallback, useEffect, useMemo, useState } from 'react';

import useAnalyticsObservationImport from './useAnalyticsObservationImport';
import { resolveObservationWindowKind } from '../components/Analytics/analyticsMetrics';

export const useAnalyticsObservationSelection = ({
    level, hasMetaAndromedaAccess, hasFbAnalyticsPermission,
    filteredData, datePreset, dateRange, language, selectedAccountId,
    setObservationBatchSummary, setObservationImportState,
}) => {
    const [selectedObservationIds, setSelectedObservationIds] = useState(new Set());

    const getObservationStatusText = useCallback((status) => {
        const map = {
            queued: language === 'zh' ? '排隊中' : 'Queued',
            processing: language === 'zh' ? '背景處理中' : 'Processing',
            completed: language === 'zh' ? '已匯入' : 'Imported',
            failed: language === 'zh' ? '匯入失敗' : 'Import failed',
            not_found: language === 'zh' ? '尚未建立' : 'Not found',
        };
        return map[status] || status || (language === 'zh' ? '未送出' : 'Idle');
    }, [language]);

    const getScoreStatusText = useCallback((status) => {
        const map = {
            pending_observation: language === 'zh' ? '等待匯入完成' : 'Waiting for import',
            pending_score_event: language === 'zh' ? '等待建立評分事件' : 'Waiting for score event',
            queued_background: language === 'zh' ? '背景建立中' : 'Creating in background',
            queued: language === 'zh' ? '評分已排隊' : 'Queued',
            processing: language === 'zh' ? '評分中' : 'Processing',
            completed: language === 'zh' ? '評分完成' : 'Completed',
            failed: language === 'zh' ? '評分失敗' : 'Failed',
            skipped_no_asset: language === 'zh' ? '無素材，略過' : 'Skipped: no asset',
            blocked_by_observation_failure: language === 'zh' ? '因匯入失敗未建立' : 'Blocked by import failure',
        };
        return map[status] || status || (language === 'zh' ? '未建立' : 'Not created');
    }, [language]);

    const canUseObservationImport = level === 'ad' && hasMetaAndromedaAccess && hasFbAnalyticsPermission;
    const observationWindowKind = useMemo(() => resolveObservationWindowKind(datePreset), [datePreset]);
    const observationImportableRows = useMemo(() => {
        if (!canUseObservationImport) {
            return [];
        }
        return filteredData.filter((row) => Boolean(row?.ad_id));
    }, [canUseObservationImport, filteredData]);

    const selectedObservationRows = useMemo(() => {
        if (!canUseObservationImport) {
            return [];
        }
        return observationImportableRows.filter((row) => selectedObservationIds.has(row.id));
    }, [canUseObservationImport, observationImportableRows, selectedObservationIds]);

    useEffect(() => {
        if (!canUseObservationImport) {
            setSelectedObservationIds(new Set());
            setObservationBatchSummary(null);
            return;
        }

        setSelectedObservationIds((prev) => {
            const next = new Set();
            observationImportableRows.forEach((row) => {
                if (prev.has(row.id)) {
                    next.add(row.id);
                }
            });
            return next;
        });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [canUseObservationImport, observationImportableRows]);

    const handleToggleObservationRow = useCallback((rowId, checked) => {
        setSelectedObservationIds((prev) => {
            const next = new Set(prev);
            if (checked) {
                next.add(rowId);
            } else {
                next.delete(rowId);
            }
            return next;
        });
    }, []);

    const handleToggleAllObservationRows = useCallback((checked) => {
        if (!checked) {
            setSelectedObservationIds(new Set());
            return;
        }

        setSelectedObservationIds(new Set(observationImportableRows.map((row) => row.id)));
    }, [observationImportableRows]);

    const {
        handleBatchObservationImport,
        handleObservationImport,
    } = useAnalyticsObservationImport({
        datePreset,
        dateRange,
        language,
        selectedAccountId,
        selectedObservationRows,
        setObservationBatchSummary,
        setObservationImportState,
    });

    return {
        selectedObservationIds,
        canUseObservationImport,
        observationWindowKind,
        observationImportableRows,
        selectedObservationRows,
        handleToggleObservationRow,
        handleToggleAllObservationRows,
        getObservationStatusText,
        getScoreStatusText,
        handleBatchObservationImport,
        handleObservationImport,
    };
};

export default useAnalyticsObservationSelection;
