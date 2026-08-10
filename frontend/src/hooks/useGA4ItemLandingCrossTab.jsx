// frontend/src/hooks/useGA4ItemLandingCrossTab.jsx (docs/33 第 7 波：GA4Insights.jsx 組合層瘦身)
import { useState } from 'react';

import { ga4InsightsService } from '../services/ga4InsightsService';

export const useGA4ItemLandingCrossTab = ({ t }) => {
    const [itemLandingDays, setItemLandingDays] = useState(7);
    const [itemLandingSnapshot, setItemLandingSnapshot] = useState(null);
    const [itemLandingLoading, setItemLandingLoading] = useState(false);
    const [itemLandingError, setItemLandingError] = useState('');
    // docs/56：跟上一期比較開關，預設關閉（不多打一次 GA4 查詢）。
    const [itemLandingCompareEnabled, setItemLandingCompareEnabled] = useState(false);

    const loadItemLandingCross = async (pid, days, compare = itemLandingCompareEnabled) => {
        if (!pid) return;
        setItemLandingLoading(true);
        setItemLandingError('');
        try {
            setItemLandingSnapshot(await ga4InsightsService.getItemLandingCross(pid, days, compare));
        } catch (err) {
            setItemLandingError(err.message || t('Failed to load item x landing page comparison.', '載入商品頁面比對失敗。'));
        } finally {
            setItemLandingLoading(false);
        }
    };

    const ensureLoaded = (pid) => {
        if (!pid || itemLandingSnapshot) return;
        loadItemLandingCross(pid, itemLandingDays);
    };

    // 沿用 GA4Insights.jsx 原本行為：切換 GA4 屬性時不會重置這個分頁的快照
    // （原本就沒有這行，屬既有行為，非本次拆分範圍，故不新增 reset 呼叫）。
    const reset = () => {
        setItemLandingSnapshot(null);
    };

    return {
        itemLandingDays, setItemLandingDays,
        itemLandingSnapshot, itemLandingLoading, itemLandingError,
        itemLandingCompareEnabled, setItemLandingCompareEnabled,
        loadItemLandingCross,
        ensureLoaded,
        reset,
    };
};

export default useGA4ItemLandingCrossTab;
