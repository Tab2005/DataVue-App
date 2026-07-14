import React from 'react';

import {
    baseCardStyle,
    buttonStyle,
    emptyState,
    inputStyle,
    secondaryButtonStyle,
} from './GA4InsightsShared';

const AlertsTab = ({
    t,
    isMobile,
    propertyId,
    editingRuleId,
    form,
    setForm,
    saving,
    resetForm,
    handleSubmit,
    loading,
    rules,
    startEdit,
    handleDelete,
    events,
    handleAck,
}) => (
    <>
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
    </>
);

export default AlertsTab;
