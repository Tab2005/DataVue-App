import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';

import { ga4Service } from '../services/ga4Service';
import { ga4InsightsService } from '../services/ga4InsightsService';
import { lineService } from '../services/lineService';

const baseCardStyle = {
    background: 'var(--bg-secondary)',
    border: '1px solid var(--glass-border)',
    borderRadius: '16px',
    padding: '20px',
};

const inputStyle = {
    width: '100%',
    padding: '10px 12px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255, 255, 255, 0.04)',
    color: 'var(--text-primary)',
};

const buttonStyle = {
    padding: '10px 14px',
    borderRadius: '10px',
    border: '1px solid rgba(59, 130, 246, 0.35)',
    background: 'rgba(59, 130, 246, 0.16)',
    color: '#bfdbfe',
    cursor: 'pointer',
};

const secondaryButtonStyle = {
    ...buttonStyle,
    border: '1px solid var(--glass-border)',
    background: 'transparent',
    color: 'var(--text-secondary)',
};

const emptyState = (text) => (
    <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{text}</div>
);

const defaultForm = {
    metric_key: 'conversions',
    sensitivity: 'medium',
    check_frequency: 'hourly',
    is_enabled: true,
    notify_line: true,
    notify_email: false,
    cooldown_hours: 6,
};

const GA4Insights = () => {
    const { language, isMobile } = useOutletContext();
    const [properties, setProperties] = useState([]);
    const [propertyId, setPropertyId] = useState('');
    const [rules, setRules] = useState([]);
    const [events, setEvents] = useState([]);
    const [lineStatus, setLineStatus] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [form, setForm] = useState(defaultForm);
    const [editingRuleId, setEditingRuleId] = useState('');

    const t = (en, zh) => (language === 'en' ? en : zh);

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

    const resetForm = () => {
        setForm(defaultForm);
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

    return (
        <div style={{ padding: isMobile ? '16px' : '24px', display: 'grid', gap: '16px' }}>
            <header style={{ display: 'grid', gap: '6px' }}>
                <div style={{ color: 'var(--accent-primary)', fontWeight: 700 }}>
                    {t('GA4 Conversion Insights', 'GA4 轉換洞察')}
                </div>
                <h1 style={{ margin: 0, color: 'var(--text-primary)' }}>
                    {t('Wave 1: anomaly alerts and history', '第 1 波：異常告警與事件歷史')}
                </h1>
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.92rem' }}>
                    {t(
                        'Set hourly or daily anomaly rules, receive LINE or email notifications, and review event history here.',
                        '在這裡設定每小時或每日異常規則、接收 LINE / Email 通知，並查看事件歷史。'
                    )}
                </div>
            </header>

            {error && (
                <div style={{ ...baseCardStyle, borderColor: 'rgba(239, 68, 68, 0.3)', color: '#fca5a5' }}>
                    {error}
                </div>
            )}

            <section style={baseCardStyle}>
                <div style={{ display: 'grid', gap: '10px', gridTemplateColumns: isMobile ? '1fr' : '2fr auto auto' }}>
                    <select
                        value={propertyId}
                        onChange={async (event) => {
                            const next = event.target.value;
                            setPropertyId(next);
                            await load(next);
                        }}
                        style={inputStyle}
                    >
                        <option value="">{t('Select GA4 property', '選擇 GA4 屬性')}</option>
                        {properties.map((property) => (
                            <option key={property.property_id} value={property.property_id}>
                                {property.display_name} · {property.property_id}
                            </option>
                        ))}
                    </select>
                    <button type="button" onClick={() => load(propertyId)} style={secondaryButtonStyle} disabled={!propertyId || loading}>
                        {loading ? t('Loading…', '載入中…') : t('Refresh', '重新整理')}
                    </button>
                    <div style={{ ...inputStyle, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        {lineStatus?.is_linked ? t('LINE linked', 'LINE 已綁定') : t('LINE not linked', 'LINE 尚未綁定')}
                    </div>
                </div>
            </section>

            <section style={{ ...baseCardStyle, display: 'grid', gap: '14px' }}>
                <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>
                    {editingRuleId ? t('Edit alert rule', '編輯告警規則') : t('Create alert rule', '建立告警規則')}
                </div>
                <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '12px', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, minmax(0, 1fr))' }}>
                    <select value={form.metric_key} onChange={(event) => setForm((prev) => ({ ...prev, metric_key: event.target.value }))} style={inputStyle}>
                        <option value="conversions">{t('Conversions', '轉換')}</option>
                        <option value="sessions">{t('Sessions', '工作階段')}</option>
                        <option value="purchase_revenue">{t('Revenue', '營收')}</option>
                    </select>
                    <select value={form.sensitivity} onChange={(event) => setForm((prev) => ({ ...prev, sensitivity: event.target.value }))} style={inputStyle}>
                        <option value="high">{t('High sensitivity', '高敏感')}</option>
                        <option value="medium">{t('Medium sensitivity', '中敏感')}</option>
                        <option value="low">{t('Low sensitivity', '低敏感')}</option>
                    </select>
                    <select value={form.check_frequency} onChange={(event) => setForm((prev) => ({ ...prev, check_frequency: event.target.value }))} style={inputStyle}>
                        <option value="hourly">{t('Hourly cumulative', '每小時累計')}</option>
                        <option value="daily">{t('Daily total', '每日總量')}</option>
                    </select>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)' }}>
                        <input type="checkbox" checked={form.is_enabled} onChange={(event) => setForm((prev) => ({ ...prev, is_enabled: event.target.checked }))} />
                        {t('Enabled', '啟用')}
                    </label>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)' }}>
                        <input type="checkbox" checked={form.notify_line} onChange={(event) => setForm((prev) => ({ ...prev, notify_line: event.target.checked }))} />
                        {t('Notify via LINE', 'LINE 通知')}
                    </label>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)' }}>
                        <input type="checkbox" checked={form.notify_email} onChange={(event) => setForm((prev) => ({ ...prev, notify_email: event.target.checked }))} />
                        {t('Notify via email', 'Email 通知')}
                    </label>
                    <input
                        type="number"
                        min="1"
                        value={form.cooldown_hours}
                        onChange={(event) => setForm((prev) => ({ ...prev, cooldown_hours: event.target.value }))}
                        style={inputStyle}
                        placeholder={t('Cooldown hours', '冷卻小時')}
                    />
                    <div style={{ display: 'flex', gap: '8px', gridColumn: isMobile ? 'auto' : 'span 2' }}>
                        <button type="submit" style={buttonStyle} disabled={!propertyId || saving}>
                            {saving ? t('Saving…', '儲存中…') : editingRuleId ? t('Update rule', '更新規則') : t('Create rule', '建立規則')}
                        </button>
                        {editingRuleId && (
                            <button type="button" style={secondaryButtonStyle} onClick={resetForm}>
                                {t('Cancel', '取消')}
                            </button>
                        )}
                    </div>
                </form>
            </section>

            <section style={baseCardStyle}>
                <div style={{ marginBottom: '12px', color: 'var(--text-primary)', fontWeight: 700 }}>
                    {t('Alert rules', '告警規則')}
                </div>
                {loading ? emptyState(t('Loading rules…', '載入規則中…')) : rules.length === 0 ? emptyState(t('No rules yet.', '目前沒有規則。')) : (
                    <div style={{ display: 'grid', gap: '10px' }}>
                        {rules.map((rule) => (
                            <div key={rule.id} style={{ border: '1px solid var(--glass-border)', borderRadius: '12px', padding: '14px' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
                                    <div>
                                        <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>
                                            {rule.metric_key} · {rule.check_frequency}
                                        </div>
                                        <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                                            {rule.sensitivity} · cooldown {rule.cooldown_hours}h · {rule.is_enabled ? t('enabled', '啟用中') : t('disabled', '已停用')}
                                        </div>
                                    </div>
                                    <div style={{ display: 'flex', gap: '8px' }}>
                                        <button type="button" style={secondaryButtonStyle} onClick={() => startEdit(rule)}>
                                            {t('Edit', '編輯')}
                                        </button>
                                        <button type="button" style={secondaryButtonStyle} onClick={() => handleDelete(rule.id)}>
                                            {t('Delete', '刪除')}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </section>

            <section style={baseCardStyle}>
                <div style={{ marginBottom: '12px', color: 'var(--text-primary)', fontWeight: 700 }}>
                    {t('Alert history', '告警歷史')}
                </div>
                {loading ? emptyState(t('Loading events…', '載入事件中…')) : events.length === 0 ? emptyState(t('No events yet.', '目前沒有事件。')) : (
                    <div style={{ display: 'grid', gap: '10px' }}>
                        {events.map((eventRow) => (
                            <div key={eventRow.id} style={{ border: '1px solid var(--glass-border)', borderRadius: '12px', padding: '14px' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
                                    <div style={{ display: 'grid', gap: '6px' }}>
                                        <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>
                                            {eventRow.metric_key} · {eventRow.direction} · {eventRow.severity}
                                        </div>
                                        <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{eventRow.message}</div>
                                        <div style={{ color: 'var(--text-tertiary)', fontSize: '0.8rem' }}>
                                            observed {eventRow.observed_value} / expected {eventRow.expected_low} - {eventRow.expected_high}
                                        </div>
                                    </div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        {eventRow.acknowledged_at ? (
                                            <span style={{ color: '#86efac', fontSize: '0.85rem' }}>{t('Acknowledged', '已讀')}</span>
                                        ) : (
                                            <button type="button" style={buttonStyle} onClick={() => handleAck(eventRow.id)}>
                                                {t('Acknowledge', '標記已讀')}
                                            </button>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </section>

            <section style={baseCardStyle}>
                <div style={{ color: 'var(--text-primary)', fontWeight: 700, marginBottom: '8px' }}>
                    {t('Wave 2 placeholders', '第 2 波預留區')}
                </div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                    {t(
                        'Intraday dashboard, channel comparison, landing pages, and item insights will be added in Wave 2.',
                        '當日儀表板、渠道對照、到達頁與商品洞察會在第 2 波補上。'
                    )}
                </div>
            </section>
        </div>
    );
};

export default GA4Insights;
