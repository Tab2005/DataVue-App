// frontend/src/hooks/useGA4OverviewTab.jsx (docs/33 第 7 波：GA4Insights.jsx 組合層瘦身)
//
// 當日總覽分頁的儀表板/即時資料狀態，原本內嵌在 GA4Insights.jsx，比照
// docs/66 的 useGA4LandingPagesTab/useGA4ItemsTab 抽成獨立 hook。
import { useState } from 'react';

import { ga4InsightsService } from '../services/ga4InsightsService';

export const useGA4OverviewTab = ({ propertyId, t }) => {
    const [dashboard, setDashboard] = useState(null);
    const [realtime, setRealtime] = useState(null);
    const [dashboardLoading, setDashboardLoading] = useState(false);
    const [dashboardError, setDashboardError] = useState('');
    const [refreshNotice, setRefreshNotice] = useState('');

    const loadDashboard = async (pid) => {
        if (!pid) return;
        setDashboardLoading(true);
        setDashboardError('');
        try {
            const [dash, rt] = await Promise.all([
                ga4InsightsService.getDashboard(pid),
                ga4InsightsService.getRealtime(pid).catch(() => null),
            ]);
            setDashboard(dash);
            setRealtime(rt);
        } catch (err) {
            setDashboardError(err.message || t('Failed to load dashboard.', '載入儀表板失敗。'));
        } finally {
            setDashboardLoading(false);
        }
    };

    // 直接掛在 <button onClick={handleRefreshDashboard}>（見 OverviewTab.jsx），
    // 第一個參數會是 click event，故沿用原本 GA4Insights.jsx 的寫法：讀 hook
    // 輸入的 propertyId，不吃函式參數。
    const handleRefreshDashboard = async () => {
        if (!propertyId) return;
        setDashboardLoading(true);
        setDashboardError('');
        setRefreshNotice('');
        try {
            const res = await ga4InsightsService.refreshDashboard(propertyId);
            setDashboard(res);
            if (!res.refreshed) {
                setRefreshNotice(t('Still fresh — please try again in a few minutes.', '資料仍新鮮，請稍後幾分鐘再試手動刷新。'));
            }
            const rt = await ga4InsightsService.getRealtime(propertyId).catch(() => null);
            setRealtime(rt);
        } catch (err) {
            setDashboardError(err.message || t('Failed to refresh dashboard.', '刷新儀表板失敗。'));
        } finally {
            setDashboardLoading(false);
        }
    };

    const ensureLoaded = (pid) => {
        if (!pid || dashboard) return;
        loadDashboard(pid);
    };

    const reset = () => {
        setDashboard(null);
        setRealtime(null);
        setRefreshNotice('');
    };

    return {
        dashboard, realtime, dashboardLoading, dashboardError, refreshNotice,
        loadDashboard, handleRefreshDashboard,
        ensureLoaded,
        reset,
    };
};

export default useGA4OverviewTab;
