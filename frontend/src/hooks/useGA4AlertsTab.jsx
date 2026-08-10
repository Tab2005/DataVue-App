// frontend/src/hooks/useGA4AlertsTab.jsx (docs/33 第 7 波：GA4Insights.jsx 組合層瘦身)
//
// 告警規則 + 事件歷史的狀態與 CRUD。原本 GA4Insights.jsx 的 load() 一次用
// Promise.all 抓 rules/events/lineStatus 三樣——lineStatus 跟告警規則無關
// （單純是 LINE 綁定狀態，畫面上一直顯示，不分分頁），故仍留在頁面層，
// 這裡的 bootstrapAlerts() 只負責 rules/events 兩樣，由頁面層的 load() 跟
// lineService.getStatus() 一起 Promise.all。
//
// 小簡化（跟原始行為的唯一差異）：新增/刪除規則後原本會連 lineStatus 一併
// 重新抓一次（因為都是呼叫同一個 load()），這裡改成只重抓 rules/events——
// 規則 CRUD 不會影響 LINE 綁定狀態，重抓沒有意義，只是少一次多餘的
// API 呼叫。
import { useState } from 'react';

import { ga4InsightsService } from '../services/ga4InsightsService';

const EVENTS_PAGE_SIZE = 10;

export const useGA4AlertsTab = ({ propertyId, t, onError }) => {
    const [rules, setRules] = useState([]);
    const [events, setEvents] = useState([]);
    const [eventsPage, setEventsPage] = useState(1);
    const [eventsTotalPages, setEventsTotalPages] = useState(1);
    const [eventsTotal, setEventsTotal] = useState(0);
    const [eventsLoading, setEventsLoading] = useState(false);
    const [unacknowledgedTotal, setUnacknowledgedTotal] = useState(0);
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
    const [availableKeyEvents, setAvailableKeyEvents] = useState([]);
    const [availableKeyEventsLoading, setAvailableKeyEventsLoading] = useState(false);

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
            onError(err.message || t('Failed to load alert history.', '載入告警歷史失敗。'));
        } finally {
            setEventsLoading(false);
        }
    };

    // 頁面層 load() 的 rules/events 部分（見檔頭說明）。
    const bootstrapAlerts = async (pid) => {
        const [rulesRes, eventsRes] = await Promise.all([
            ga4InsightsService.listRules(pid),
            ga4InsightsService.listEvents(pid, 1, EVENTS_PAGE_SIZE),
        ]);
        setRules(rulesRes.rules || []);
        setEvents(eventsRes.events || []);
        setEventsPage(eventsRes.page || 1);
        setEventsTotalPages(Math.max(1, Math.ceil((eventsRes.total || 0) / EVENTS_PAGE_SIZE)));
        setUnacknowledgedTotal(eventsRes.unacknowledged_total || 0);
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
        } catch {
            // docs/52：查詢失敗只是少了個別事件選項，不擋建立規則表單其他操作。
            setAvailableKeyEvents([]);
        } finally {
            setAvailableKeyEventsLoading(false);
        }
    };

    // 直接掛在 <form onSubmit={handleSubmit}>，讀 hook 輸入的 propertyId，
    // 不吃函式參數（沿用原本 GA4Insights.jsx 的寫法）。
    const handleSubmit = async (event) => {
        event.preventDefault();
        if (!propertyId) return;
        setSaving(true);
        onError('');
        try {
            const payload = { ...form, property_id: propertyId, cooldown_hours: Number(form.cooldown_hours) || 6 };
            if (editingRuleId) {
                await ga4InsightsService.updateRule(editingRuleId, payload);
            } else {
                await ga4InsightsService.createRule(payload);
            }
            resetForm();
            await bootstrapAlerts(propertyId);
        } catch (err) {
            onError(err.message || t('Failed to save rule.', '儲存規則失敗。'));
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
            await bootstrapAlerts(propertyId);
        } catch (err) {
            onError(err.message || t('Failed to delete rule.', '刪除規則失敗。'));
        }
    };

    const handleAck = async (eventId) => {
        try {
            await ga4InsightsService.acknowledgeEvent(eventId);
            await loadEvents(propertyId, eventsPage);
        } catch (err) {
            onError(err.message || t('Failed to acknowledge event.', '標記已讀失敗。'));
        }
    };

    return {
        rules, events,
        eventsPage, eventsTotalPages, eventsTotal, eventsLoading,
        unacknowledgedTotal,
        saving, form, setForm, editingRuleId,
        availableKeyEvents, availableKeyEventsLoading, setAvailableKeyEvents,
        loadEvents,
        bootstrapAlerts,
        resetForm,
        loadAvailableKeyEvents,
        handleSubmit,
        startEdit,
        handleDelete,
        handleAck,
    };
};

export default useGA4AlertsTab;
