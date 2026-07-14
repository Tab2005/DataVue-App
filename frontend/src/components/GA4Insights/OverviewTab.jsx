import React from 'react';

import {
    AIInsightNote,
    DASHBOARD_METRICS,
    IntradayMetricCard,
    baseCardStyle,
    emptyState,
    fmtNumber,
    secondaryButtonStyle,
} from './GA4InsightsShared';

const OverviewTab = ({
    language,
    t,
    isMobile,
    propertyId,
    dashboard,
    dashboardLoading,
    dashboardError,
    realtime,
    refreshNotice,
    handleRefreshDashboard,
    unackedEvents,
}) => (
    <>
                    <section style={baseCardStyle}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px', flexWrap: 'wrap', gap: '8px' }}>
                            <div>
                                <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>
                                    {t('Realtime (last 30 min)', 'Realtime 心跳（近 30 分鐘）')}
                                </div>
                                {dashboard?.payload?.date && (
                                    <div style={{ color: 'var(--text-tertiary)', fontSize: '0.78rem' }}>
                                        {t('Intraday data as of hour', '當日資料截至小時')} {dashboard.payload.current_hour}:00 · {dashboard.payload.date}
                                    </div>
                                )}
                            </div>
                            <button type="button" style={secondaryButtonStyle} onClick={handleRefreshDashboard} disabled={dashboardLoading}>
                                {dashboardLoading ? t('Refreshing…', '刷新中…') : t('Manual refresh', '立即刷新')}
                            </button>
                        </div>
                        {refreshNotice && <div style={{ color: '#fbbf24', fontSize: '0.82rem', marginBottom: '8px' }}>{refreshNotice}</div>}
                        {dashboardError && <div style={{ color: '#fca5a5', fontSize: '0.85rem', marginBottom: '8px' }}>{dashboardError}</div>}
                        {realtime ? (
                            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(2, 1fr)', gap: '14px' }}>
                                <div>
                                    <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-primary)' }}>{fmtNumber(realtime.active_users)}</div>
                                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>{t('Active users', '活躍使用者')}</div>
                                </div>
                                <div>
                                    <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-primary)' }}>{fmtNumber(realtime.event_count)}</div>
                                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>{t('Events', '事件數')}</div>
                                </div>
                            </div>
                        ) : (
                            !dashboardLoading && emptyState(t('No realtime data.', '暫無即時資料。'))
                        )}
                    </section>

                    <section style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)', gap: '14px' }}>
                        {dashboardLoading && !dashboard ? (
                            <div style={baseCardStyle}>{emptyState(t('Loading dashboard…', '載入儀表板中…'))}</div>
                        ) : dashboard?.payload ? (
                            DASHBOARD_METRICS.map((metricKey) => (
                                <IntradayMetricCard
                                    key={metricKey}
                                    language={language}
                                    metricKey={metricKey}
                                    hourlyTotals={dashboard.payload.hourly_totals}
                                    baseline={dashboard.payload.baseline?.[metricKey]}
                                    cumulativeValue={dashboard.payload.cumulative_totals?.[metricKey]}
                                    isAnomaly={dashboard.payload.is_anomaly?.[metricKey]}
                                />
                            ))
                        ) : (
                            <div style={baseCardStyle}>{emptyState(t('No dashboard data yet.', '尚無儀表板資料。'))}</div>
                        )}
                    </section>

                    <AIInsightNote
                        language={language}
                        snapshot={dashboard}
                        kind="intraday_hourly"
                        contextLabel={t(
                            `Property ${propertyId}; date ${dashboard?.payload?.date || ''}; current hour ${dashboard?.payload?.current_hour ?? ''}`,
                            `屬性 ${propertyId}；日期 ${dashboard?.payload?.date || ''}；目前小時 ${dashboard?.payload?.current_hour ?? ''}`
                        )}
                        buildPayload={() => ({
                            date: dashboard?.payload?.date,
                            current_hour: dashboard?.payload?.current_hour,
                            cumulative_totals: dashboard?.payload?.cumulative_totals,
                            baseline: dashboard?.payload?.baseline,
                            is_anomaly: dashboard?.payload?.is_anomaly,
                            realtime_active_users: realtime?.active_users ?? null,
                            unacked_alerts: unackedEvents.length,
                        })}
                    />
    </>
);

export default OverviewTab;
