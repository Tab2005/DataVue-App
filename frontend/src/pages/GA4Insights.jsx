import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { ga4Service } from '../services/ga4Service';
import { ga4InsightsService } from '../services/ga4InsightsService';
import { lineService } from '../services/lineService';
import { useModuleAccess, usePermission, useSelectedTeamId } from '../hooks/usePermission';
import useGA4LandingPagesTab from '../hooks/useGA4LandingPagesTab';
import useGA4ItemsTab from '../hooks/useGA4ItemsTab';
import OverviewTab from '../components/GA4Insights/OverviewTab';
import ChannelsTab from '../components/GA4Insights/ChannelsTab';
import LandingPagesTab from '../components/GA4Insights/LandingPagesTab';
import ItemsTab from '../components/GA4Insights/ItemsTab';
import ItemLandingCrossTab from '../components/GA4Insights/ItemLandingCrossTab';
import KpiTab from '../components/GA4Insights/KpiTab';
import AlertsTab from '../components/GA4Insights/AlertsTab';
import {
    VIZ_TOKENS,
    baseCardStyle,
    currentMonthKey,
    emptyState,
    inputStyle,
    secondaryButtonStyle,
    tabButtonStyle,
    tr,
} from '../components/GA4Insights/GA4InsightsShared';

const EVENTS_PAGE_SIZE = 10;

const GA4Insights = () => {
    const { language, isMobile } = useOutletContext();
    const t = (en, zh) => tr(language, en, zh);

    const [properties, setProperties] = useState([]);
    const [propertyId, setPropertyId] = useState('');
    const [activeTab, setActiveTab] = useState('overview');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // 分類規則（到達頁 / 商品）的寫入操作依 ga4:insights:manage_alerts 權限
    // 顯示（第 5 波 3 點）。個人工作區沒有團隊角色，PermissionService.
    // check_permission 對細項權限一律回 false（見 modules/ga4/dependencies.py
    // 的個人工作區修復說明）；後端 PUT/DELETE 端點在個人工作區改退回模組
    // 存取即可通過，前端若直接用 usePermission 判斷會在個人工作區把本來能
    // 用的功能誤藏起來，所以這裡比照後端同一套複合邏輯：有選團隊才看細項
    // 權限，沒有就看模組存取。兩個規則管理區塊（到達頁、商品）共用同一個
    // 權限鍵，故共用同一個判斷結果。
    const selectedTeamId = useSelectedTeamId();
    const { hasAccess: ga4ModuleAccess } = useModuleAccess('ga4');
    const { hasPermission: ga4ManageAlertsPermission } = usePermission('ga4:insights:manage_alerts');
    const canManageGa4InsightsRules = selectedTeamId ? ga4ManageAlertsPermission : ga4ModuleAccess;

    // docs/66：到達頁與商品這兩個分頁的整組狀態抽成各自的 hook（原本是 51 / 53
    // 個 props）。hook 在這裡（父層）呼叫而不是分頁元件自己呼叫——分頁是條件
    // 渲染的，切走就 unmount，狀態放在父層才能在切回來時保住快照與篩選條件、
    // 也不會重打一次 GA4 查詢。
    const landing = useGA4LandingPagesTab({ propertyId, t });
    const items = useGA4ItemsTab({ propertyId, t });

    // 第 1 波：告警規則 / 事件歷史
    const [rules, setRules] = useState([]);
    const [events, setEvents] = useState([]);
    const [eventsPage, setEventsPage] = useState(1);
    const [eventsTotalPages, setEventsTotalPages] = useState(1);
    // docs/56：分頁元件補「共 N 筆」用，跟 eventsTotalPages 分開存（後者是頁數）。
    const [eventsTotal, setEventsTotal] = useState(0);
    const [eventsLoading, setEventsLoading] = useState(false);
    // 未讀總數獨立於分頁抓取（docs/39 追加）：分頁只影響 events 顯示哪一頁，
    // 未讀提示卡永遠顯示「全部歷史」的未讀數，不會因為使用者切頁而跳動。
    const [unacknowledgedTotal, setUnacknowledgedTotal] = useState(0);
    const [lineStatus, setLineStatus] = useState(null);
    const [saving, setSaving] = useState(false);
    const [form, setForm] = useState({
        metric_key: 'conversions',
        key_event: null,
        sensitivity: 'medium',
        check_frequency: 'hourly',
        is_enabled: true,
        notify_line: true,
        notify_email: false,
        cooldown_hours: 6,
    });
    const [editingRuleId, setEditingRuleId] = useState('');
    // docs/52：告警規則「轉換」的關鍵事件下拉選單，開表單選到「轉換」時才查一次，
    // 查詢失敗只是少了個別事件選項，不擋整個表單。
    const [availableKeyEvents, setAvailableKeyEvents] = useState([]);
    const [availableKeyEventsLoading, setAvailableKeyEventsLoading] = useState(false);

    // 第 2 波：當日總覽
    const [dashboard, setDashboard] = useState(null);
    const [realtime, setRealtime] = useState(null);
    const [dashboardLoading, setDashboardLoading] = useState(false);
    const [dashboardError, setDashboardError] = useState('');
    const [refreshNotice, setRefreshNotice] = useState('');

    // 第 2/4 波：渠道對照
    const [channelsDays, setChannelsDays] = useState(7);
    const [channelsDimension, setChannelsDimension] = useState('default_channel_group');
    const [channelsSnapshot, setChannelsSnapshot] = useState(null);
    const [channelsLoading, setChannelsLoading] = useState(false);
    const [channelsError, setChannelsError] = useState('');

    // docs/47：商品頁面與商品轉換率交叉對照（獨立新分頁）
    const [itemLandingDays, setItemLandingDays] = useState(7);
    const [itemLandingSnapshot, setItemLandingSnapshot] = useState(null);
    const [itemLandingLoading, setItemLandingLoading] = useState(false);
    const [itemLandingError, setItemLandingError] = useState('');
    // docs/56：跟上一期比較開關，預設關閉（不多打一次 GA4 查詢）。
    const [itemLandingCompareEnabled, setItemLandingCompareEnabled] = useState(false);

    // 第 3 波：KPI 目標追蹤
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

    const loadEvents = async (nextPropertyId, page = 1) => {
        const targetPropertyId = nextPropertyId || propertyId;
        if (!targetPropertyId) return;
        setEventsLoading(true);
        try {
            const eventsRes = await ga4InsightsService.listEvents(targetPropertyId, page, EVENTS_PAGE_SIZE);
            setEvents(eventsRes.events || []);
            setEventsPage(eventsRes.page || page);
            setEventsTotalPages(Math.max(1, Math.ceil((eventsRes.total || 0) / EVENTS_PAGE_SIZE)));
            setEventsTotal(eventsRes.total || 0);
            setUnacknowledgedTotal(eventsRes.unacknowledged_total || 0);
        } catch (err) {
            setError(err.message || t('Failed to load alert history.', '載入告警歷史失敗。'));
        } finally {
            setEventsLoading(false);
        }
    };

    const load = async (nextPropertyId) => {
        setLoading(true);
        setError('');
        try {
            const targetPropertyId = nextPropertyId || propertyId;
            const [rulesRes, eventsRes, lineRes] = await Promise.all([
                ga4InsightsService.listRules(targetPropertyId),
                ga4InsightsService.listEvents(targetPropertyId, 1, EVENTS_PAGE_SIZE),
                lineService.getStatus(),
            ]);
            setRules(rulesRes.rules || []);
            setEvents(eventsRes.events || []);
            setEventsPage(eventsRes.page || 1);
            setEventsTotalPages(Math.max(1, Math.ceil((eventsRes.total || 0) / EVENTS_PAGE_SIZE)));
            setUnacknowledgedTotal(eventsRes.unacknowledged_total || 0);
            setLineStatus(lineRes);
        } catch (err) {
            setError(err.message || t('Failed to load GA4 insights.', '載入 GA4 洞察失敗。'));
        } finally {
            setLoading(false);
        }
    };

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

    const loadChannels = async (pid, days, dimension = channelsDimension) => {
        if (!pid) return;
        setChannelsLoading(true);
        setChannelsError('');
        try {
            setChannelsSnapshot(await ga4InsightsService.getChannels(pid, days, dimension));
        } catch (err) {
            setChannelsError(err.message || t('Failed to load channel comparison.', '載入渠道對照失敗。'));
        } finally {
            setChannelsLoading(false);
        }
    };

    // docs/47：商品頁面與商品轉換率交叉對照
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

    useEffect(() => {
        let cancelled = false;
        const bootstrap = async () => {
            setLoading(true);
            try {
                const props = await ga4Service.getProperties();
                if (cancelled) return;
                setProperties(props);
                const initialPropertyId = props[0]?.property_id || '';
                setPropertyId(initialPropertyId);
                if (initialPropertyId) {
                    await load(initialPropertyId);
                } else {
                    const lineRes = await lineService.getStatus();
                    setLineStatus(lineRes);
                    setLoading(false);
                }
            } catch (err) {
                if (!cancelled) {
                    setError(err.message || t('Failed to load properties.', '載入 GA4 屬性失敗。'));
                    setLoading(false);
                }
            }
        };
        bootstrap();
        return () => {
            cancelled = true;
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // 分頁籤切換／屬性切換時，懶載入該分頁的資料（每個分頁只在首次進入時抓一次）
    useEffect(() => {
        if (!propertyId) return;
        if (activeTab === 'overview' && !dashboard) loadDashboard(propertyId);
        if (activeTab === 'channels' && !channelsSnapshot) loadChannels(propertyId, channelsDays);
        if (activeTab === 'landing') landing.ensureLoaded(propertyId);
        if (activeTab === 'items') items.ensureLoaded(propertyId);
        if (activeTab === 'itemLandingCross' && !itemLandingSnapshot) loadItemLandingCross(propertyId, itemLandingDays);
        if (activeTab === 'kpi' && !kpiTargets) loadKpiTargets(propertyId);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeTab, propertyId]);

    // docs/52：告警規則表單選到「轉換」時才查一次關鍵事件下拉清單，離開這個
    // 分頁籤或切換到別的指標不用查；同一屬性已經查過就不重查。
    useEffect(() => {
        if (
            activeTab === 'alerts' && propertyId && form.metric_key === 'conversions' &&
            availableKeyEvents.length === 0 && !availableKeyEventsLoading
        ) {
            loadAvailableKeyEvents(propertyId);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeTab, propertyId, form.metric_key]);

    const handlePropertyChange = async (event) => {
        const next = event.target.value;
        setPropertyId(next);
        setAvailableKeyEvents([]);
        setDashboard(null);
        setRealtime(null);
        setChannelsSnapshot(null);
        landing.reset();
        items.reset();
        setKpiTargets(null);
        setRefreshNotice('');
        await load(next);
    };

    const resetForm = () => {
        setForm({
            metric_key: 'conversions',
            key_event: null,
            sensitivity: 'medium',
            check_frequency: 'hourly',
            is_enabled: true,
            notify_line: true,
            notify_email: false,
            cooldown_hours: 6,
        });
        setEditingRuleId('');
    };

    const loadAvailableKeyEvents = async (targetPropertyId) => {
        setAvailableKeyEventsLoading(true);
        try {
            const res = await ga4InsightsService.getRuleAvailableKeyEvents(targetPropertyId);
            setAvailableKeyEvents(res.events || []);
        } catch (err) {
            // docs/52：查詢失敗只是少了個別事件選項，不擋建立規則表單其他操作。
            setAvailableKeyEvents([]);
        } finally {
            setAvailableKeyEventsLoading(false);
        }
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        if (!propertyId) return;
        setSaving(true);
        setError('');
        try {
            const payload = { ...form, property_id: propertyId, cooldown_hours: Number(form.cooldown_hours) || 6 };
            if (editingRuleId) {
                await ga4InsightsService.updateRule(editingRuleId, payload);
            } else {
                await ga4InsightsService.createRule(payload);
            }
            resetForm();
            await load(propertyId);
        } catch (err) {
            setError(err.message || t('Failed to save rule.', '儲存規則失敗。'));
        } finally {
            setSaving(false);
        }
    };

    const startEdit = (rule) => {
        setEditingRuleId(rule.id);
        setForm({
            metric_key: rule.metric_key,
            key_event: rule.key_event ?? null,
            sensitivity: rule.sensitivity,
            check_frequency: rule.check_frequency,
            is_enabled: rule.is_enabled,
            notify_line: rule.notify_line,
            notify_email: rule.notify_email,
            cooldown_hours: rule.cooldown_hours,
        });
    };

    const handleDelete = async (ruleId) => {
        if (!window.confirm(t('Delete this anomaly rule?', '要刪除此告警規則嗎？'))) return;
        try {
            await ga4InsightsService.deleteRule(ruleId);
            if (editingRuleId === ruleId) resetForm();
            await load(propertyId);
        } catch (err) {
            setError(err.message || t('Failed to delete rule.', '刪除規則失敗。'));
        }
    };

    const handleAck = async (eventId) => {
        try {
            await ga4InsightsService.acknowledgeEvent(eventId);
            await loadEvents(propertyId, eventsPage);
        } catch (err) {
            setError(err.message || t('Failed to acknowledge event.', '標記已讀失敗。'));
        }
    };

    const unackedEvents = events.filter((e) => !e.acknowledged_at);

    const tabs = [
        { key: 'overview', en: 'Today', zh: '當日總覽' },
        { key: 'channels', en: 'Channels', zh: '渠道對照' },
        { key: 'landing', en: 'Landing Pages', zh: '到達頁' },
        { key: 'items', en: 'Items', zh: '商品' },
        { key: 'itemLandingCross', en: 'Item x Landing Page', zh: '商品頁面比對' },
        { key: 'kpi', en: 'KPI', zh: 'KPI 目標' },
        { key: 'alerts', en: 'Alerts', zh: '告警設定' },
    ];

    return (
        <div style={{ padding: isMobile ? '16px' : '24px', display: 'grid', gap: '16px' }}>
            <style>{VIZ_TOKENS}</style>
            <header style={{ display: 'grid', gap: '6px' }}>
                <div style={{ color: 'var(--accent-primary)', fontWeight: 700 }}>
                    {t('GA4 Conversion Insights', 'GA4 轉換洞察')}
                </div>
                <h1 style={{ margin: 0, color: 'var(--text-primary)' }}>
                    {t('Same-day dashboard, anomaly alerts, and channel/page/item breakdowns', '當日儀表板、異常告警與渠道／頁面／商品拆解')}
                </h1>
            </header>

            {error && (
                <div style={{ ...baseCardStyle, borderColor: 'rgba(239, 68, 68, 0.3)', color: '#fca5a5' }}>
                    {error}
                </div>
            )}

            <section style={baseCardStyle}>
                <div style={{ display: 'grid', gap: '10px', gridTemplateColumns: isMobile ? '1fr' : '2fr auto' }}>
                    <select value={propertyId} onChange={handlePropertyChange} style={inputStyle}>
                        <option value="">{t('Select GA4 property', '選擇 GA4 屬性')}</option>
                        {properties.map((property) => (
                            <option key={property.property_id} value={property.property_id}>
                                {property.display_name} · {property.property_id}
                            </option>
                        ))}
                    </select>
                    <div style={{ ...inputStyle, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        {lineStatus?.is_linked ? t('LINE linked', 'LINE 已綁定') : t('LINE not linked', 'LINE 尚未綁定')}
                    </div>
                </div>
            </section>

            {unacknowledgedTotal > 0 && (
                <section style={{ ...baseCardStyle, borderColor: 'rgba(239, 68, 68, 0.3)' }}>
                    <div style={{ color: '#fca5a5', fontWeight: 700, marginBottom: '6px' }}>
                        {t(`${unacknowledgedTotal} unacknowledged alert(s)`, `${unacknowledgedTotal} 則未讀告警`)}
                    </div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                        {unackedEvents[0]?.message}
                        {unacknowledgedTotal > 1 && ` …`}
                    </div>
                    <button type="button" style={{ ...secondaryButtonStyle, marginTop: '10px' }} onClick={() => setActiveTab('alerts')}>
                        {t('Go to alert settings', '前往告警設定')}
                    </button>
                </section>
            )}

            <nav style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '2px' }}>
                {tabs.map((tab) => (
                    <button
                        key={tab.key}
                        type="button"
                        style={tabButtonStyle(activeTab === tab.key)}
                        onClick={() => setActiveTab(tab.key)}
                    >
                        {t(tab.en, tab.zh)}
                    </button>
                ))}
            </nav>

            {!propertyId && !loading && (
                <section style={baseCardStyle}>{emptyState(t('Connect a GA4 property to see insights.', '請先連接 GA4 屬性以查看洞察。'))}</section>
            )}

            {propertyId && activeTab === 'overview' && (
                <OverviewTab
                    language={language}
                    t={t}
                    isMobile={isMobile}
                    propertyId={propertyId}
                    dashboard={dashboard}
                    dashboardLoading={dashboardLoading}
                    dashboardError={dashboardError}
                    realtime={realtime}
                    refreshNotice={refreshNotice}
                    handleRefreshDashboard={handleRefreshDashboard}
                    unacknowledgedTotal={unacknowledgedTotal}
                />
            )}

            {propertyId && activeTab === 'channels' && (
                <ChannelsTab
                    language={language}
                    t={t}
                    propertyId={propertyId}
                    channelsDimension={channelsDimension}
                    setChannelsDimension={setChannelsDimension}
                    channelsDays={channelsDays}
                    setChannelsDays={setChannelsDays}
                    loadChannels={loadChannels}
                    channelsError={channelsError}
                    channelsSnapshot={channelsSnapshot}
                    channelsLoading={channelsLoading}
                />
            )}

            {propertyId && activeTab === 'landing' && (
                <LandingPagesTab
                    language={language}
                    t={t}
                    isMobile={isMobile}
                    propertyId={propertyId}
                    canManageGa4InsightsRules={canManageGa4InsightsRules}
                    landing={landing}
                />
            )}

            {propertyId && activeTab === 'items' && (
                <ItemsTab
                    language={language}
                    t={t}
                    isMobile={isMobile}
                    propertyId={propertyId}
                    canManageGa4InsightsRules={canManageGa4InsightsRules}
                    items={items}
                />
            )}

            {propertyId && activeTab === 'itemLandingCross' && (
                <ItemLandingCrossTab
                    language={language}
                    t={t}
                    propertyId={propertyId}
                    itemLandingDays={itemLandingDays}
                    setItemLandingDays={setItemLandingDays}
                    loadItemLandingCross={loadItemLandingCross}
                    itemLandingError={itemLandingError}
                    itemLandingLoading={itemLandingLoading}
                    itemLandingSnapshot={itemLandingSnapshot}
                    itemLandingCompareEnabled={itemLandingCompareEnabled}
                    setItemLandingCompareEnabled={setItemLandingCompareEnabled}
                />
            )}

            {propertyId && activeTab === 'kpi' && (
                <KpiTab
                    t={t}
                    isMobile={isMobile}
                    kpiForm={kpiForm}
                    setKpiForm={setKpiForm}
                    kpiSaving={kpiSaving}
                    handleCreateKpiTarget={handleCreateKpiTarget}
                    kpiError={kpiError}
                    kpiLoading={kpiLoading}
                    kpiTargets={kpiTargets}
                    language={language}
                    handleDeleteKpiTarget={handleDeleteKpiTarget}
                />
            )}

            {propertyId && activeTab === 'alerts' && (
                <AlertsTab
                    language={language}
                    t={t}
                    isMobile={isMobile}
                    propertyId={propertyId}
                    editingRuleId={editingRuleId}
                    form={form}
                    setForm={setForm}
                    availableKeyEvents={availableKeyEvents}
                    availableKeyEventsLoading={availableKeyEventsLoading}
                    saving={saving}
                    resetForm={resetForm}
                    handleSubmit={handleSubmit}
                    loading={loading}
                    rules={rules}
                    startEdit={startEdit}
                    handleDelete={handleDelete}
                    events={events}
                    eventsLoading={eventsLoading}
                    eventsPage={eventsPage}
                    eventsTotalPages={eventsTotalPages}
                    eventsTotal={eventsTotal}
                    onEventsPageChange={(page) => loadEvents(propertyId, page)}
                    handleAck={handleAck}
                />
            )}
        </div>
    );
};

export default GA4Insights;
