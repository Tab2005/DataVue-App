// frontend/src/hooks/useAnalyticsSummary.js (docs/33 第 7 波：Analytics.jsx 組合層瘦身)
//
// 表格列選取狀態 + KPI 加總（calculateSummary 見 analyticsSummary.js）。
import { useMemo, useState } from 'react';

import { calculateSummary } from '../components/Analytics/analyticsSummary';

export const useAnalyticsSummary = ({ filteredData, filteredPrevData }) => {
    // Table Row Selection State
    const [selectedRowIds, setSelectedRowIds] = useState(new Set()); // IDs of selected rows

    // Sync selectedRowIds with filteredData（Default Behavior: When filteredData
    // changes e.g. date change, Select All by default）。原本用 useEffect 做，
    // 但那樣會多等一次 commit 後才更新，畫面會先閃過一輪舊選取狀態；改用
    // React 官方文件建議的「render 期間比較並直接呼叫 setState」寫法
    // （https://react.dev/learn/you-might-not-need-an-effect#adjusting-some-state-when-a-prop-changes），
    // 同一輪 render 就能拿到新選取狀態，行為更正確而非只是搬相同程式碼。
    const [prevFilteredData, setPrevFilteredData] = useState(filteredData);
    if (filteredData !== prevFilteredData) {
        setPrevFilteredData(filteredData);
        if (filteredData) {
            setSelectedRowIds(new Set(filteredData.map(item => item.id)));
        }
    }

    const currentSummaryData = useMemo(
        () => calculateSummary(filteredData, selectedRowIds),
        [filteredData, selectedRowIds]
    );

    const prevSummaryData = useMemo(() => {
        if (!filteredPrevData) return null;
        return calculateSummary(filteredPrevData, selectedRowIds);
    }, [filteredPrevData, selectedRowIds]);

    return {
        selectedRowIds, setSelectedRowIds,
        currentSummaryData,
        prevSummaryData,
    };
};

export default useAnalyticsSummary;
