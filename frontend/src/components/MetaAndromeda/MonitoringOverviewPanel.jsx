import React from 'react';

import {
    Metric,
    buttonPrimaryStyle,
    formatPercent,
    inputStyle,
    metricGridStyle,
    panelStyle,
    sectionTitleStyle,
} from './shared';

export const MonitoringOverviewPanel = ({ isMobile, monitoring }) => {
    const {
        summary,
        runningDrift,
        driftWindowKind,
        setDriftWindowKind,
        driftSince,
        setDriftSince,
        driftUntil,
        setDriftUntil,
        driftNote,
        setDriftNote,
        driftAccountId,
        setDriftAccountId,
        observedAccounts,
        t,
        getTranslation,
        handleDriftTrigger,
    } = monitoring;

    return (
        <>
                    {/* Alert Banner */}
                    {(summary?.active_alerts || []).length > 0 && (
                        <div style={{
                            marginBottom: '14px',
                            padding: '12px 16px',
                            borderRadius: '12px',
                            background: 'rgba(239, 68, 68, 0.08)',
                            border: '1px solid rgba(239, 68, 68, 0.3)',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '12px',
                            flexWrap: 'wrap',
                        }}>
                            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ef4444', boxShadow: '0 0 8px #ef4444', flexShrink: 0, animation: 'pulse 1.5s infinite' }} />
                            <span style={{ fontWeight: 700, color: '#f87171', fontSize: '0.88rem' }}>
                                {summary.active_alerts.length} {t('active alert(s)', '條告警中')}
                            </span>
                            <span style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>
                                {summary.active_alerts.slice(0, 2).map((a) => a.message || a.code || '').filter(Boolean).join(' · ')}
                                {summary.active_alerts.length > 2 && ` ··· +${summary.active_alerts.length - 2}`}
                            </span>
                        </div>
                    )}

                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)',
                        gap: '16px',
                        marginBottom: '16px'
                    }}>
                        {Object.entries(summary?.jobs || {}).map(([jobKey, job]) => (
                            <section key={jobKey} style={panelStyle}>
                                <h2 style={sectionTitleStyle}>{getTranslation(jobKey)}</h2>
                                <div style={metricGridStyle}>
                                    <Metric label={getTranslation("queued_total")} value={job.queued_total} />
                                    <Metric label={getTranslation("completed_total")} value={job.completed_total} />
                                    <Metric label={getTranslation("failure_total")} value={job.failure_total} />
                                    <Metric label={getTranslation("queue_depth.current")} value={job.queue_depth?.current} />
                                    <Metric label={getTranslation("queue_depth.peak")} value={job.queue_depth?.peak} />
                                    <Metric label={getTranslation("latency.avg(ms)")} value={job.latency_ms?.avg} />
                                    <Metric label={getTranslation("latency.p95(ms)")} value={job.latency_ms?.p95} />
                                    <Metric label={getTranslation("latency.max(ms)")} value={job.latency_ms?.max} />
                                </div>
                            </section>
                        ))}

                        <section style={panelStyle}>
                            <h2 style={sectionTitleStyle}>{t('Observation Pipeline', 'Observation 資料管線')}</h2>
                            <div style={{ marginBottom: '12px', color: 'var(--text-secondary)', fontSize: '0.78rem', lineHeight: 1.5 }}>
                                {t('FB Ads import line only. Score Lab uploads excluded unless matched by a drift report.', '僅統計 FB Ads 匯入線，Score Lab 上傳不計入。')}
                            </div>
                            <div style={metricGridStyle}>
                                <Metric
                                    label={getTranslation('observed_total')}
                                    value={summary?.observation_pipeline?.observed_total}
                                />
                                <Metric
                                    label={getTranslation('latest_observed_total')}
                                    value={summary?.observation_pipeline?.latest_observed_total}
                                />
                                <Metric
                                    label={getTranslation('observed_with_asset')}
                                    value={summary?.observation_pipeline?.observed_with_asset}
                                />
                                <Metric
                                    label={getTranslation('latest_matched_total')}
                                    value={summary?.observation_pipeline?.latest_matched_total}
                                />
                                <Metric
                                    label={getTranslation('latest_match_rate')}
                                    value={formatPercent(summary?.observation_pipeline?.latest_match_rate)}
                                />
                                <Metric
                                    label={getTranslation('latest_calibration_candidate_total')}
                                    value={summary?.observation_pipeline?.latest_calibration_candidate_total}
                                />
                                <Metric
                                    label={getTranslation('latest_calibration_synced_total')}
                                    value={summary?.observation_pipeline?.latest_calibration_synced_total}
                                />
                            </div>
                            <div style={{ marginTop: '10px', color: 'var(--text-secondary)', fontSize: '0.78rem', lineHeight: 1.5 }}>
                                {t('Calibration', '校準狀態')}: {getTranslation(summary?.observation_pipeline?.latest_calibration_status)}
                                {summary?.observation_pipeline?.latest_calibration_dataset_id
                                    ? ` · ${summary.observation_pipeline.latest_calibration_dataset_id}`
                                    : ''}
                            </div>
                        </section>

                        <section style={panelStyle}>
                            <h2 style={sectionTitleStyle}>{t('Drift Trigger', '預估偏差檢查')}</h2>
                            <form onSubmit={handleDriftTrigger} style={{ display: 'grid', gap: '12px' }}>
                                <select value={driftWindowKind} onChange={(event) => setDriftWindowKind(event.target.value)} style={inputStyle}>
                                    <option value="last_24h">{t('Last 24 Hours', '最近 24 小時')}</option>
                                    <option value="last_7d">{t('Last 7 Days', '最近 7 天')}</option>
                                    <option value="last_30d">{t('Last 30 Days', '最近 30 天')}</option>
                                    <option value="custom">{t('Custom Date Range', '自訂時間區間')}</option>
                                </select>
                                {driftWindowKind === 'custom' && (
                                    <div style={{ display: 'flex', gap: '8px', marginBottom: '4px' }}>
                                        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '4px' }}>
                                            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{t('Start Date', '開始日期')}</span>
                                            <input 
                                                type="date" 
                                                value={driftSince} 
                                                onChange={(e) => setDriftSince(e.target.value)} 
                                                style={{ ...inputStyle, colorScheme: 'dark' }}
                                            />
                                        </div>
                                        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '4px' }}>
                                            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{t('End Date', '結束日期')}</span>
                                            <input 
                                                type="date" 
                                                value={driftUntil} 
                                                onChange={(e) => setDriftUntil(e.target.value)} 
                                                style={{ ...inputStyle, colorScheme: 'dark' }}
                                            />
                                        </div>
                                    </div>
                                )}
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                                    <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                        {t('Ad Account', '廣告帳號')}
                                    </span>
                                    {observedAccounts.length > 0 ? (
                                        <select
                                            value={driftAccountId}
                                            onChange={(e) => setDriftAccountId(e.target.value)}
                                            style={inputStyle}
                                        >
                                            <option value="">{t('All accounts', '全部帳號')}</option>
                                            {observedAccounts.map((acc) => (
                                                <option key={acc.account_id} value={acc.account_id}>
                                                    {acc.account_id}
                                                    {acc.platform !== 'facebook_ads' ? ` (${acc.platform})` : ''}
                                                    {' '}· {acc.total_creatives} {t('creatives', '筆素材')}
                                                </option>
                                            ))}
                                        </select>
                                    ) : (
                                        <input
                                            type="text"
                                            value={driftAccountId}
                                            onChange={(e) => setDriftAccountId(e.target.value)}
                                            placeholder={t('No accounts imported yet', '尚未匯入任何帳號資料')}
                                            style={inputStyle}
                                        />
                                    )}
                                </div>
                                <textarea
                                    value={driftNote}
                                    onChange={(event) => setDriftNote(event.target.value)}
                                    rows={2}
                                    placeholder={t('Optional operator note', '可選操作備註')}
                                    style={inputStyle}
                                />
                                <button type="submit" style={buttonPrimaryStyle} disabled={runningDrift}>
                                    {runningDrift ? t('Running...', '執行中...') : t('Run Drift Check', '執行預估偏差檢查')}
                                </button>
                            </form>
                        </section>
                    </div>
        </>
    );
};
