// frontend/src/hooks/useGA4KpiTab.jsx (docs/33 第 7 波：GA4Insights.jsx 組合層瘦身)
import { useState } from 'react';

import { ga4InsightsService } from '../services/ga4InsightsService';
import { currentMonthKey } from '../components/GA4Insights/GA4InsightsShared';

export const useGA4KpiTab = ({ propertyId, t }) => {
    const [kpiTargets, setKpiTargets] = useState(null);
    const [kpiLoading, setKpiLoading] = useState(false);
    const [kpiError, setKpiError] = useState('');
    const [kpiSaving, setKpiSaving] = useState(false);
    const [kpiForm, setKpiForm] = useState({
        metric_key: 'conversions',
        period_type: 'month',
        period_key: currentMonthKey(),
        target_value: '',
    });

    const loadKpiTargets = async (pid) => {
        if (!pid) return;
        setKpiLoading(true);
        setKpiError('');
        try {
            const res = await ga4InsightsService.listKpiTargets(pid);
            setKpiTargets(res.targets || []);
        } catch (err) {
            setKpiError(err.message || t('Failed to load KPI targets.', '載入 KPI 目標失敗。'));
        } finally {
            setKpiLoading(false);
        }
    };

    // 直接掛在 <form onSubmit={handleCreateKpiTarget}>，讀 hook 輸入的
    // propertyId，不吃函式參數（沿用原本 GA4Insights.jsx 的寫法）。
    const handleCreateKpiTarget = async (event) => {
        event.preventDefault();
        if (!propertyId || !kpiForm.target_value) return;
        setKpiSaving(true);
        setKpiError('');
        try {
            await ga4InsightsService.upsertKpiTarget({
                property_id: propertyId,
                metric_key: kpiForm.metric_key,
                period_type: kpiForm.period_type,
                period_key: kpiForm.period_key,
                target_value: Number(kpiForm.target_value),
            });
            setKpiForm((prev) => ({ ...prev, target_value: '' }));
            await loadKpiTargets(propertyId);
        } catch (err) {
            setKpiError(err.message || t('Failed to save KPI target.', '儲存 KPI 目標失敗。'));
        } finally {
            setKpiSaving(false);
        }
    };

    const handleDeleteKpiTarget = async (targetId) => {
        if (!window.confirm(t('Delete this KPI target?', '要刪除此 KPI 目標嗎？'))) return;
        try {
            await ga4InsightsService.deleteKpiTarget(targetId);
            await loadKpiTargets(propertyId);
        } catch (err) {
            setKpiError(err.message || t('Failed to delete KPI target.', '刪除 KPI 目標失敗。'));
        }
    };

    const ensureLoaded = (pid) => {
        if (!pid || kpiTargets) return;
        loadKpiTargets(pid);
    };

    const reset = () => {
        setKpiTargets(null);
    };

    return {
        kpiTargets, kpiLoading, kpiError, kpiSaving, kpiForm, setKpiForm,
        loadKpiTargets, handleCreateKpiTarget, handleDeleteKpiTarget,
        ensureLoaded,
        reset,
    };
};

export default useGA4KpiTab;
