import React from 'react';

import {
    KPI_METRIC_OPTIONS,
    KpiPacingCard,
    baseCardStyle,
    buttonStyle,
    emptyState,
    inputStyle,
} from './GA4InsightsShared';

const KpiTab = ({
    t,
    isMobile,
    kpiForm,
    setKpiForm,
    kpiSaving,
    handleCreateKpiTarget,
    kpiError,
    kpiLoading,
    kpiTargets,
    language,
    handleDeleteKpiTarget,
}) => (
    <>
                    <section style={{ ...baseCardStyle, display: 'grid', gap: '14px' }}>
                        <div>
                            <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{t('Set a KPI target', '設定 KPI 目標')}</div>
                            <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                                {t('Target values per metric, per month or quarter.', '依指標、按月或按季設定目標值。')}
                            </div>
                        </div>
                        <form onSubmit={handleCreateKpiTarget} style={{ display: 'grid', gap: '12px', gridTemplateColumns: isMobile ? '1fr' : 'repeat(4, minmax(0, 1fr))' }}>
                            <select
                                value={kpiForm.metric_key}
                                onChange={(event) => setKpiForm((prev) => ({ ...prev, metric_key: event.target.value }))}
                                style={inputStyle}
                            >
                                {KPI_METRIC_OPTIONS.map((option) => (
                                    <option key={option.value} value={option.value}>{t(option.en, option.zh)}</option>
                                ))}
                            </select>
                            <select
                                value={kpiForm.period_type}
                                onChange={(event) => {
                                    const nextType = event.target.value;
                                    setKpiForm((prev) => ({
                                        ...prev,
                                        period_type: nextType,
                                        period_key: nextType === 'month' ? currentMonthKey() : currentQuarterKey(),
                                    }));
                                }}
                                style={inputStyle}
                            >
                                <option value="month">{t('Monthly', '按月')}</option>
                                <option value="quarter">{t('Quarterly', '按季')}</option>
                            </select>
                            <input
                                type="text"
                                value={kpiForm.period_key}
                                onChange={(event) => setKpiForm((prev) => ({ ...prev, period_key: event.target.value }))}
                                placeholder={kpiForm.period_type === 'month' ? 'YYYY-MM' : 'YYYY-Qn'}
                                style={inputStyle}
                            />
                            <input
                                type="number"
                                min="0"
                                step="any"
                                value={kpiForm.target_value}
                                onChange={(event) => setKpiForm((prev) => ({ ...prev, target_value: event.target.value }))}
                                placeholder={t('Target value', '目標值')}
                                style={inputStyle}
                            />
                            <div style={{ gridColumn: isMobile ? 'auto' : 'span 4' }}>
                                <button type="submit" style={buttonStyle} disabled={kpiSaving || !kpiForm.target_value}>
                                    {kpiSaving ? t('Saving…', '儲存中…') : t('Save target', '儲存目標')}
                                </button>
                            </div>
                        </form>
                    </section>

                    <section>
                        {kpiError && <div style={{ color: '#fca5a5', fontSize: '0.85rem', marginBottom: '10px' }}>{kpiError}</div>}
                        {kpiLoading && !kpiTargets ? (
                            <div style={baseCardStyle}>{emptyState(t('Loading KPI targets…', '載入 KPI 目標中…'))}</div>
                        ) : kpiTargets && kpiTargets.length > 0 ? (
                            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fill, minmax(280px, 1fr))', gap: '14px' }}>
                                {kpiTargets.map((target) => (
                                    <KpiPacingCard key={target.id} language={language} target={target} onDelete={handleDeleteKpiTarget} />
                                ))}
                            </div>
                        ) : (
                            <div style={baseCardStyle}>{emptyState(t('No KPI targets yet. Set one above.', '尚無 KPI 目標，請在上方設定。'))}</div>
                        )}
                    </section>
    </>
);

export default KpiTab;
