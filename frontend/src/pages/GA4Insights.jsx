import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { ga4Service } from '../services/ga4Service';
import { ga4InsightsService } from '../services/ga4InsightsService';
import { lineService } from '../services/lineService';
import { useModuleAccess, usePermission, useSelectedTeamId } from '../hooks/usePermission';
import OverviewTab from '../components/GA4Insights/OverviewTab';
import ChannelsTab from '../components/GA4Insights/ChannelsTab';
import LandingPagesTab from '../components/GA4Insights/LandingPagesTab';
import ItemsTab from '../components/GA4Insights/ItemsTab';
import KpiTab from '../components/GA4Insights/KpiTab';
import AlertsTab from '../components/GA4Insights/AlertsTab';
import {
    ITEMS_SORT_COLUMNS,
    VIZ_TOKENS,
    baseCardStyle,
    currentMonthKey,
    currentQuarterKey,
    dayButtonStyle,
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

    // 第 1 波：告警規則 / 事件歷史
    const [rules, setRules] = useState([]);
    const [events, setEvents] = useState([]);
    const [lineStatus, setLineStatus] = useState(null);
    const [saving, setSaving] = useState(false);
    const [form, setForm] = useState({
        metric_key: 'conversions',
        sensitivity: 'medium',
        check_frequency: 'hourly',
        is_enabled: true,
        notify_line: true,
        notify_email: false,
        cooldown_hours: 6,
    });
    const [editingRuleId, setEditingRuleId] = useState('');

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

    // 第 2/5 波：到達頁
    const [landingDays, setLandingDays] = useState(7);
    const [landingSnapshot, setLandingSnapshot] = useState(null);
    const [landingLoading, setLandingLoading] = useState(false);
    const [landingError, setLandingError] = useState('');
    const [landingCategoryFilter, setLandingCategoryFilter] = useState('all');
    const [landingKeyEvent, setLandingKeyEvent] = useState('');
    const [landingRules, setLandingRules] = useState(null);
    const [landingRulesOpen, setLandingRulesOpen] = useState(false);
    const [landingRulesLoading, setLandingRulesLoading] = useState(false);
    const [landingRulesError, setLandingRulesError] = useState('');
    const [landingRuleSaving, setLandingRuleSaving] = useState(false);
    const [landingRuleForm, setLandingRuleForm] = useState({ category: 'product', match_type: 'prefix', pattern: '', priority: 0 });

    // 第 2/6 波：商品
    const [itemsDays, setItemsDays] = useState(7);
    const [itemsSnapshot, setItemsSnapshot] = useState(null);
    const [itemsLoading, setItemsLoading] = useState(false);
    const [itemsError, setItemsError] = useState('');
    const [itemsCategoryFilter, setItemsCategoryFilter] = useState('all');
    const [itemsSearchQuery, setItemsSearchQuery] = useState('');
    const [itemsSortKey, setItemsSortKey] = useState(null);
    const [itemsSortDirection, setItemsSortDirection] = useState('desc');

    // 第 7 波：商品分類補充規則（GA4 itemCategory 缺值時的補充來源）
    const [itemCategoryRules, setItemCategoryRules] = useState(null);
    const [itemCategoryRulesOpen, setItemCategoryRulesOpen] = useState(false);
    const [itemCategoryRulesLoading, setItemCategoryRulesLoading] = useState(false);
    const [itemCategoryRulesError, setItemCategoryRulesError] = useState('');
    const [itemCategoryRuleSaving, setItemCategoryRuleSaving] = useState(false);
    const [itemCategoryRuleForm, setItemCategoryRuleForm] = useState({ category: '', match_type: 'prefix', pattern: '', priority: 0 });

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

    const load = async (nextPropertyId) => {
        setLoading(true);
        setError('');
        try {
            const targetPropertyId = nextPropertyId || propertyId;
            const [rulesRes, eventsRes, lineRes] = await Promise.all([
                ga4InsightsService.listRules(targetPropertyId),
                ga4InsightsService.listEvents(targetPropertyId),
                lineService.getStatus(),
            ]);
            setRules(rulesRes.rules || []);
            setEvents(eventsRes.events || []);
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

    const loadLandingPages = async (pid, days, keyEvent = landingKeyEvent) => {
        if (!pid) return;
        setLandingLoading(true);
        setLandingError('');
        try {
            setLandingSnapshot(await ga4InsightsService.getLandingPages(pid, days, keyEvent || null));
        } catch (err) {
            setLandingError(err.message || t('Failed to load landing pages.', '載入到達頁分析失敗。'));
        } finally {
            setLandingLoading(false);
        }
    };

    const loadLandingPageRules = async (pid) => {
        if (!pid) return;
        setLandingRulesLoading(true);
        setLandingRulesError('');
        try {
            const res = await ga4InsightsService.listLandingPageRules(pid);
            setLandingRules(res.rules || []);
        } catch (err) {
            setLandingRulesError(err.message || t('Failed to load landing page rules.', '載入到達頁分類規則失敗。'));
        } finally {
            setLandingRulesLoading(false);
        }
    };

    const handleCreateLandingPageRule = async (event) => {
        event.preventDefault();
        if (!propertyId || !landingRuleForm.pattern.trim()) return;
        setLandingRuleSaving(true);
        setLandingRulesError('');
        try {
            await ga4InsightsService.upsertLandingPageRule({
                property_id: propertyId,
                category: landingRuleForm.category,
                match_type: landingRuleForm.match_type,
                pattern: landingRuleForm.pattern.trim(),
                priority: Number(landingRuleForm.priority) || 0,
            });
            setLandingRuleForm((prev) => ({ ...prev, pattern: '' }));
            await loadLandingPageRules(propertyId);
            await loadLandingPages(propertyId, landingDays);
        } catch (err) {
            setLandingRulesError(err.message || t('Failed to save rule.', '儲存規則失敗。'));
        } finally {
            setLandingRuleSaving(false);
        }
    };

    const handleDeleteLandingPageRule = async (ruleId) => {
        if (!window.confirm(t('Delete this classification rule?', '要刪除此分類規則嗎？'))) return;
        try {
            await ga4InsightsService.deleteLandingPageRule(ruleId);
            await loadLandingPageRules(propertyId);
            await loadLandingPages(propertyId, landingDays);
        } catch (err) {
            setLandingRulesError(err.message || t('Failed to delete rule.', '刪除規則失敗。'));
        }
    };

    const loadItems = async (pid, days) => {
        if (!pid) return;
        setItemsLoading(true);
        setItemsError('');
        try {
            setItemsSnapshot(await ga4InsightsService.getItems(pid, days));
        } catch (err) {
            setItemsError(err.message || t('Failed to load item insights.', '載入商品分析失敗。'));
        } finally {
            setItemsLoading(false);
        }
    };

    const loadItemCategoryRules = async (pid) => {
        if (!pid) return;
        setItemCategoryRulesLoading(true);
        setItemCategoryRulesError('');
        try {
            const res = await ga4InsightsService.listItemCategoryRules(pid);
            setItemCategoryRules(res.rules || []);
        } catch (err) {
            setItemCategoryRulesError(err.message || t('Failed to load item category rules.', '載入商品分類規則失敗。'));
        } finally {
            setItemCategoryRulesLoading(false);
        }
    };

    const handleCreateItemCategoryRule = async (event) => {
        event.preventDefault();
        if (!propertyId || !itemCategoryRuleForm.category.trim() || !itemCategoryRuleForm.pattern.trim()) return;
        setItemCategoryRuleSaving(true);
        setItemCategoryRulesError('');
        try {
            await ga4InsightsService.upsertItemCategoryRule({
                property_id: propertyId,
                category: itemCategoryRuleForm.category.trim(),
                match_type: itemCategoryRuleForm.match_type,
                pattern: itemCategoryRuleForm.pattern.trim(),
                priority: Number(itemCategoryRuleForm.priority) || 0,
            });
            setItemCategoryRuleForm((prev) => ({ ...prev, category: '', pattern: '' }));
            await loadItemCategoryRules(propertyId);
            await loadItems(propertyId, itemsDays);
        } catch (err) {
            setItemCategoryRulesError(err.message || t('Failed to save rule.', '儲存規則失敗。'));
        } finally {
            setItemCategoryRuleSaving(false);
        }
    };

    const handleDeleteItemCategoryRule = async (ruleId) => {
        if (!window.confirm(t('Delete this category rule?', '要刪除此分類規則嗎？'))) return;
        try {
            await ga4InsightsService.deleteItemCategoryRule(ruleId);
            await loadItemCategoryRules(propertyId);
            await loadItems(propertyId, itemsDays);
        } catch (err) {
            setItemCategoryRulesError(err.message || t('Failed to delete rule.', '刪除規則失敗。'));
        }
    };

    const handleItemsSort = (key) => {
        if (itemsSortKey === key) {
            setItemsSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'));
        } else {
            setItemsSortKey(key);
            setItemsSortDirection(ITEMS_SORT_COLUMNS[key].defaultDir);
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
        if (activeTab === 'landing' && !landingSnapshot) loadLandingPages(propertyId, landingDays);
        if (activeTab === 'landing' && !landingRules) loadLandingPageRules(propertyId);
        if (activeTab === 'items' && !itemsSnapshot) loadItems(propertyId, itemsDays);
        if (activeTab === 'items' && !itemCategoryRules) loadItemCategoryRules(propertyId);
        if (activeTab === 'kpi' && !kpiTargets) loadKpiTargets(propertyId);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeTab, propertyId]);

    const handlePropertyChange = async (event) => {
        const next = event.target.value;
        setPropertyId(next);
        setDashboard(null);
        setRealtime(null);
        setChannelsSnapshot(null);
        setLandingSnapshot(null);
        setLandingRules(null);
        setLandingCategoryFilter('all');
        setLandingKeyEvent('');
        setItemsSnapshot(null);
        setItemsCategoryFilter('all');
        setItemsSearchQuery('');
        setItemCategoryRules(null);
        setKpiTargets(null);
        setRefreshNotice('');
        await load(next);
    };

    const resetForm = () => {
        setForm({
            metric_key: 'conversions',
            sensitivity: 'medium',
            check_frequency: 'hourly',
            is_enabled: true,
            notify_line: true,
            notify_email: false,
            cooldown_hours: 6,
        });
        setEditingRuleId('');
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
            await load(propertyId);
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
        { key: 'kpi', en: 'KPI', zh: 'KPI 目標' },
        { key: 'alerts', en: 'Alerts', zh: '告警設定' },
    ];

    const DaySelector = ({ value, onChange }) => (
        <div style={{ display: 'flex', gap: '6px' }}>
            {[7, 14, 30].map((d) => (
                <button key={d} type="button" style={dayButtonStyle(value === d)} onClick={() => onChange(d)}>
                    {d}{t('d', '天')}
                </button>
            ))}
        </div>
    );

    // 商品分析表格的可排序表頭（點擊切換欄位/方向）。
    const renderItemsSortHeader = (key, label, tooltip) => {
        const isActive = itemsSortKey === key;
        const arrow = isActive ? (itemsSortDirection === 'asc' ? ' ▲' : ' ▼') : '';
        return (
            <th
                style={{ padding: '6px', cursor: 'pointer', userSelect: 'none', color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)' }}
                title={tooltip}
                onClick={() => handleItemsSort(key)}
            >
                {label}{tooltip ? ' ⓘ' : ''}{arrow}
            </th>
        );
    };

    const sortedItemsRows = (rows) => {
        if (!itemsSortKey) {
            // 預設排序：潛力商品優先（既有行為）
            return [...rows].sort((a, b) => (b.is_potential ? 1 : 0) - (a.is_potential ? 1 : 0));
        }
        const meta = ITEMS_SORT_COLUMNS[itemsSortKey];
        const dir = itemsSortDirection === 'asc' ? 1 : -1;
        return [...rows].sort((a, b) => {
            const av = a[itemsSortKey];
            const bv = b[itemsSortKey];
            if (meta.type === 'string') {
                return dir * String(av || '').localeCompare(String(bv || ''));
            }
            return dir * ((av ?? 0) - (bv ?? 0));
        });
    };

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

            {unackedEvents.length > 0 && (
                <section style={{ ...baseCardStyle, borderColor: 'rgba(239, 68, 68, 0.3)' }}>
                    <div style={{ color: '#fca5a5', fontWeight: 700, marginBottom: '6px' }}>
                        {t(`${unackedEvents.length} unacknowledged alert(s)`, `${unackedEvents.length} 則未讀告警`)}
                    </div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                        {unackedEvents[0]?.message}
                        {unackedEvents.length > 1 && ` …`}
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
                    unackedEvents={unackedEvents}
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
                    DaySelector={DaySelector}
                />
            )}

            {propertyId && activeTab === 'landing' && (
                <LandingPagesTab
                    language={language}
                    t={t}
                    isMobile={isMobile}
                    propertyId={propertyId}
                    landingDays={landingDays}
                    setLandingDays={setLandingDays}
                    loadLandingPages={loadLandingPages}
                    landingError={landingError}
                    landingLoading={landingLoading}
                    landingSnapshot={landingSnapshot}
                    landingCategoryFilter={landingCategoryFilter}
                    setLandingCategoryFilter={setLandingCategoryFilter}
                    landingKeyEvent={landingKeyEvent}
                    setLandingKeyEvent={setLandingKeyEvent}
                    DaySelector={DaySelector}
                    landingRulesOpen={landingRulesOpen}
                    setLandingRulesOpen={setLandingRulesOpen}
                    landingRulesError={landingRulesError}
                    landingRulesLoading={landingRulesLoading}
                    landingRules={landingRules}
                    canManageGa4InsightsRules={canManageGa4InsightsRules}
                    handleDeleteLandingPageRule={handleDeleteLandingPageRule}
                    handleCreateLandingPageRule={handleCreateLandingPageRule}
                    landingRuleForm={landingRuleForm}
                    setLandingRuleForm={setLandingRuleForm}
                    landingRuleSaving={landingRuleSaving}
                />
            )}

            {propertyId && activeTab === 'items' && (
                <ItemsTab
                    language={language}
                    t={t}
                    isMobile={isMobile}
                    propertyId={propertyId}
                    itemsDays={itemsDays}
                    setItemsDays={setItemsDays}
                    loadItems={loadItems}
                    itemsError={itemsError}
                    itemsLoading={itemsLoading}
                    itemsSnapshot={itemsSnapshot}
                    itemsCategoryFilter={itemsCategoryFilter}
                    setItemsCategoryFilter={setItemsCategoryFilter}
                    itemsSearchQuery={itemsSearchQuery}
                    setItemsSearchQuery={setItemsSearchQuery}
                    DaySelector={DaySelector}
                    renderItemsSortHeader={renderItemsSortHeader}
                    sortedItemsRows={sortedItemsRows}
                    itemCategoryRulesOpen={itemCategoryRulesOpen}
                    setItemCategoryRulesOpen={setItemCategoryRulesOpen}
                    itemCategoryRulesError={itemCategoryRulesError}
                    itemCategoryRulesLoading={itemCategoryRulesLoading}
                    itemCategoryRules={itemCategoryRules}
                    canManageGa4InsightsRules={canManageGa4InsightsRules}
                    handleDeleteItemCategoryRule={handleDeleteItemCategoryRule}
                    handleCreateItemCategoryRule={handleCreateItemCategoryRule}
                    itemCategoryRuleForm={itemCategoryRuleForm}
                    setItemCategoryRuleForm={setItemCategoryRuleForm}
                    itemCategoryRuleSaving={itemCategoryRuleSaving}
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
                    t={t}
                    isMobile={isMobile}
                    propertyId={propertyId}
                    editingRuleId={editingRuleId}
                    form={form}
                    setForm={setForm}
                    saving={saving}
                    resetForm={resetForm}
                    handleSubmit={handleSubmit}
                    loading={loading}
                    rules={rules}
                    startEdit={startEdit}
                    handleDelete={handleDelete}
                    events={events}
                    handleAck={handleAck}
                />
            )}
        </div>
    );
};

export default GA4Insights;
