import React, { Suspense, lazy, useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { ga4Service } from '../services/ga4Service';
import { lineService } from '../services/lineService';
import { useModuleAccess, usePermission, useSelectedTeamId } from '../hooks/usePermission';
import useGA4LandingPagesTab from '../hooks/useGA4LandingPagesTab';
import useGA4ItemsTab from '../hooks/useGA4ItemsTab';
import useGA4OverviewTab from '../hooks/useGA4OverviewTab';
import useGA4ChannelsTab from '../hooks/useGA4ChannelsTab';
import useGA4ItemLandingCrossTab from '../hooks/useGA4ItemLandingCrossTab';
import useGA4KpiTab from '../hooks/useGA4KpiTab';
import useGA4AlertsTab from '../hooks/useGA4AlertsTab';
import OverviewTab from '../components/GA4Insights/OverviewTab';
import ChannelsTab from '../components/GA4Insights/ChannelsTab';
import KpiTab from '../components/GA4Insights/KpiTab';
import AlertsTab from '../components/GA4Insights/AlertsTab';
// docs/59 P2-6：體積最大、且不是每個使用者都會開的三個分頁改成 lazy（同
// App.jsx 既有的做法）。這三個分頁共用的 GA4InsightsTables 本來就已經是另一個
// chunk（docs/64），拆出去後只看當日總覽/告警的使用者就不用載這些。
const LandingPagesTab = lazy(() => import('../components/GA4Insights/LandingPagesTab'));
const ItemsTab = lazy(() => import('../components/GA4Insights/ItemsTab'));
const ItemLandingCrossTab = lazy(() => import('../components/GA4Insights/ItemLandingCrossTab'));
import {
    VIZ_TOKENS,
    baseCardStyle,
    emptyState,
    inputStyle,
    secondaryButtonStyle,
    tabButtonStyle,
    tr,
} from '../components/GA4Insights/GA4InsightsShared';

const GA4Insights = () => {
    const { language, isMobile } = useOutletContext();
    const t = (en, zh) => tr(language, en, zh);

    const [properties, setProperties] = useState([]);
    const [propertyId, setPropertyId] = useState('');
    const [activeTab, setActiveTab] = useState('overview');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [lineStatus, setLineStatus] = useState(null);

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

    // docs/66 + docs/33 第 7 波：每個分頁籤的整組狀態各自抽成獨立 hook（原本
    // 51~53 個 props 或直接內嵌在本檔）。hook 在這裡（父層）呼叫而不是分頁
    // 元件自己呼叫——分頁是條件渲染的，切走就 unmount，狀態放在父層才能在
    // 切回來時保住快照與篩選條件、也不會重打一次 GA4 查詢。
    const landing = useGA4LandingPagesTab({ propertyId, t });
    const items = useGA4ItemsTab({ propertyId, t });
    const overview = useGA4OverviewTab({ propertyId, t });
    const channels = useGA4ChannelsTab({ t });
    const itemLandingCross = useGA4ItemLandingCrossTab({ t });
    const kpi = useGA4KpiTab({ propertyId, t });
    const alerts = useGA4AlertsTab({ propertyId, t, onError: setError });
    const {
        rules, events,
        eventsPage, eventsTotalPages, eventsTotal, eventsLoading,
        unacknowledgedTotal,
        saving, form, setForm, editingRuleId,
        availableKeyEvents, availableKeyEventsLoading,
        loadEvents,
        bootstrapAlerts,
        resetForm,
        loadAvailableKeyEvents,
        handleSubmit,
        startEdit,
        handleDelete,
        handleAck,
    } = alerts;
    const {
        dashboard, realtime, dashboardLoading, dashboardError, refreshNotice,
        handleRefreshDashboard,
    } = overview;
    const {
        channelsDays, setChannelsDays, channelsDimension, setChannelsDimension,
        channelsSnapshot, channelsLoading, channelsError, loadChannels,
    } = channels;
    const {
        itemLandingDays, setItemLandingDays, itemLandingSnapshot, itemLandingLoading,
        itemLandingError, itemLandingCompareEnabled, setItemLandingCompareEnabled,
        loadItemLandingCross,
    } = itemLandingCross;
    const {
        kpiTargets, kpiLoading, kpiError, kpiSaving, kpiForm, setKpiForm,
        handleCreateKpiTarget, handleDeleteKpiTarget,
    } = kpi;

    const load = async (nextPropertyId) => {
        setLoading(true);
        setError('');
        try {
            const targetPropertyId = nextPropertyId || propertyId;
            const [, lineRes] = await Promise.all([
                bootstrapAlerts(targetPropertyId),
                lineService.getStatus(),
            ]);
            setLineStatus(lineRes);
        } catch (err) {
            setError(err.message || t('Failed to load GA4 insights.', '載入 GA4 洞察失敗。'));
        } finally {
            setLoading(false);
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
        if (activeTab === 'overview') overview.ensureLoaded(propertyId);
        if (activeTab === 'channels') channels.ensureLoaded(propertyId);
        if (activeTab === 'landing') landing.ensureLoaded(propertyId);
        if (activeTab === 'items') items.ensureLoaded(propertyId);
        if (activeTab === 'itemLandingCross') itemLandingCross.ensureLoaded(propertyId);
        if (activeTab === 'kpi') kpi.ensureLoaded(propertyId);
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
        alerts.setAvailableKeyEvents([]);
        overview.reset();
        channels.reset();
        landing.reset();
        items.reset();
        kpi.reset();
        await load(next);
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

    // docs/59 P2-6：lazy 分頁的載入中畫面。三個分頁共用同一個，不在 JSX 裡重複寫。
    const tabLoadingFallback = (
        <div style={{ ...baseCardStyle, color: 'var(--text-tertiary)' }}>{t('Loading…', '載入中…')}</div>
    );

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
                <Suspense fallback={tabLoadingFallback}>
                    <LandingPagesTab
                        language={language}
                        t={t}
                        isMobile={isMobile}
                        propertyId={propertyId}
                        canManageGa4InsightsRules={canManageGa4InsightsRules}
                        landing={landing}
                    />
                </Suspense>
            )}

            {propertyId && activeTab === 'items' && (
                <Suspense fallback={tabLoadingFallback}>
                    <ItemsTab
                        language={language}
                        t={t}
                        isMobile={isMobile}
                        propertyId={propertyId}
                        canManageGa4InsightsRules={canManageGa4InsightsRules}
                        items={items}
                    />
                </Suspense>
            )}

            {propertyId && activeTab === 'itemLandingCross' && (
                <Suspense fallback={tabLoadingFallback}>
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
                </Suspense>
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
