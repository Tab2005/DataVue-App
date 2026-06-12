import React, { useEffect, useMemo, useState } from 'react';
import { useOutletContext, useSearchParams } from 'react-router-dom';

import { usePermission } from '../hooks/usePermission';
import {
    fetchMetaAndromedaMonitoringSummary,
    fetchMetaAndromedaMonitoringTimeline,
    triggerMetaAndromedaDriftReport,
} from '../services/metaAndromedaMonitoringService';

const MetaAndromedaMonitoring = () => {
    const { isMobile, language } = useOutletContext();
    const [searchParams, setSearchParams] = useSearchParams();
    const [summary, setSummary] = useState(null);
    const [timeline, setTimeline] = useState(null);
    const [loading, setLoading] = useState(true);
    const [loadingTimeline, setLoadingTimeline] = useState(false);
    const [runningDrift, setRunningDrift] = useState(false);
    const [error, setError] = useState(null);
    const [hostFilter, setHostFilter] = useState(searchParams.get('host') || 'all');
    const [eventQuery, setEventQuery] = useState(searchParams.get('q') || '');
    const [deadLetterOnly, setDeadLetterOnly] = useState(searchParams.get('dead') === '1');
    const [selectedScoreEventId, setSelectedScoreEventId] = useState(searchParams.get('event') || '');
    const [driftWindowKind, setDriftWindowKind] = useState(searchParams.get('window') || 'last_24h');
    const [driftNote, setDriftNote] = useState('');
    const { hasPermission: canOperate, loading: loadingOperatePermission } = usePermission('meta_andromeda:operate');

    const t = (en, zh) => (language === 'en' ? en : zh);

    const loadSummary = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await fetchMetaAndromedaMonitoringSummary();
            setSummary(data);
        } catch (err) {
            setError(err.message || 'Failed to load monitoring summary');
        } finally {
            setLoading(false);
        }
    };

    const loadTimeline = async (scoreEventId) => {
        if (!scoreEventId) {
            setTimeline(null);
            return;
        }
        setLoadingTimeline(true);
        setError(null);
        try {
            const data = await fetchMetaAndromedaMonitoringTimeline(scoreEventId);
            setTimeline(data);
        } catch (err) {
            setError(err.message || 'Failed to load event timeline');
        } finally {
            setLoadingTimeline(false);
        }
    };

    useEffect(() => {
        loadSummary();
    }, []);

    useEffect(() => {
        const nextParams = new URLSearchParams();
        if (hostFilter && hostFilter !== 'all') {
            nextParams.set('host', hostFilter);
        }
        if (eventQuery.trim()) {
            nextParams.set('q', eventQuery.trim());
        }
        if (deadLetterOnly) {
            nextParams.set('dead', '1');
        }
        if (selectedScoreEventId) {
            nextParams.set('event', selectedScoreEventId);
        }
        if (driftWindowKind !== 'last_24h') {
            nextParams.set('window', driftWindowKind);
        }
        setSearchParams(nextParams, { replace: true });
    }, [hostFilter, eventQuery, deadLetterOnly, selectedScoreEventId, driftWindowKind, setSearchParams]);

    useEffect(() => {
        loadTimeline(selectedScoreEventId);
    }, [selectedScoreEventId]);

    const recentEvents = useMemo(() => (summary?.worker_host?.recent_events || []).filter((event) => {
        const hostOk = hostFilter === 'all' || event.queue_host === hostFilter;
        const query = eventQuery.trim().toLowerCase();
        const queryOk = !query
            || event.event_type?.toLowerCase().includes(query)
            || event.queue_host?.toLowerCase().includes(query)
            || event.score_event_id?.toLowerCase().includes(query)
            || event.runtime_job_id?.toLowerCase().includes(query)
            || event.message?.toLowerCase().includes(query);
        return hostOk && queryOk;
    }), [summary, hostFilter, eventQuery]);

    const deadLetters = useMemo(() => (summary?.worker_host?.dead_letters || []).filter((item) => {
        const hostOk = hostFilter === 'all' || item.queue_host === hostFilter;
        const query = eventQuery.trim().toLowerCase();
        const queryOk = !query
            || item.failure_stage?.toLowerCase().includes(query)
            || item.queue_host?.toLowerCase().includes(query)
            || item.score_event_id?.toLowerCase().includes(query)
            || item.runtime_job_id?.toLowerCase().includes(query)
            || item.final_error_message?.toLowerCase().includes(query);
        return hostOk && queryOk;
    }), [summary, hostFilter, eventQuery]);

    const visibleRecentEvents = deadLetterOnly ? [] : recentEvents.slice(0, 8);
    const visibleDeadLetters = deadLetterOnly ? deadLetters : deadLetters.slice(0, 6);

    const handleDriftTrigger = async (event) => {
        event.preventDefault();
        setRunningDrift(true);
        setError(null);
        try {
            await triggerMetaAndromedaDriftReport({
                window_kind: driftWindowKind,
                note: driftNote.trim() || null,
            });
            setDriftNote('');
            await loadSummary();
        } catch (err) {
            setError(err.message || 'Failed to trigger drift report');
        } finally {
            setRunningDrift(false);
        }
    };

    const handleSelectTimeline = (scoreEventId) => {
        setSelectedScoreEventId(scoreEventId);
    };

    return (
        <div style={{ padding: isMobile ? '16px' : '24px' }}>
            <div style={{
                marginBottom: '20px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: isMobile ? 'flex-start' : 'center',
                gap: '16px',
                flexDirection: isMobile ? 'column' : 'row',
            }}>
                <div>
                    <div style={{ color: 'var(--accent-primary)', fontWeight: 700, marginBottom: '8px' }}>
                        Meta Andromeda
                    </div>
                    <h1 style={{ margin: 0, color: 'var(--text-primary)' }}>
                        {t('Monitoring Summary', '監控總覽')}
                    </h1>
                </div>
                <button type="button" onClick={loadSummary} style={actionButtonStyle}>
                    {t('Refresh', '重新整理')}
                </button>
            </div>

            <div style={{
                ...panelStyle,
                marginBottom: '16px',
                display: 'grid',
                gridTemplateColumns: isMobile ? '1fr' : '1.1fr 0.8fr auto',
                gap: '12px',
                alignItems: 'center',
            }}>
                <input
                    type="text"
                    value={eventQuery}
                    onChange={(event) => setEventQuery(event.target.value)}
                    placeholder={t('Search score event, runtime job, or message', '搜尋 score event、runtime job 或訊息')}
                    style={inputStyle}
                />
                <select value={hostFilter} onChange={(event) => setHostFilter(event.target.value)} style={inputStyle}>
                    <option value="all">{t('All Hosts', '全部宿主')}</option>
                    {Array.from(new Set([
                        summary?.worker_host?.active_host,
                        ...(summary?.worker_host?.recent_events || []).map((event) => event.queue_host),
                        ...(summary?.worker_host?.dead_letters || []).map((item) => item.queue_host),
                    ].filter(Boolean))).map((host) => (
                        <option key={host} value={host}>{host}</option>
                    ))}
                </select>
                <label style={toggleLabelStyle}>
                    <input
                        type="checkbox"
                        checked={deadLetterOnly}
                        onChange={(event) => setDeadLetterOnly(event.target.checked)}
                    />
                    <span>{t('Dead Letters Only', '只看死信')}</span>
                </label>
            </div>

            {error ? <div style={errorPanelStyle}>{error}</div> : null}

            {loading ? (
                <div style={panelStyle}>{t('Loading monitoring summary...', '載入監控總覽中...')}</div>
            ) : (
                <>
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: isMobile ? '1fr' : 'repeat(2, 1fr)',
                        gap: '16px',
                        marginBottom: '16px'
                    }}>
                        {Object.entries(summary?.jobs || {}).map(([jobKey, job]) => (
                            <section key={jobKey} style={panelStyle}>
                                <h2 style={sectionTitleStyle}>{jobKey}</h2>
                                <div style={metricGridStyle}>
                                    <Metric label="queued_total" value={job.queued_total} />
                                    <Metric label="completed_total" value={job.completed_total} />
                                    <Metric label="failure_total" value={job.failure_total} />
                                    <Metric label="queue_depth.current" value={job.queue_depth?.current} />
                                    <Metric label="queue_depth.peak" value={job.queue_depth?.peak} />
                                    <Metric label="latency.avg(ms)" value={job.latency_ms?.avg} />
                                    <Metric label="latency.p95(ms)" value={job.latency_ms?.p95} />
                                    <Metric label="latency.max(ms)" value={job.latency_ms?.max} />
                                </div>
                            </section>
                        ))}

                        <section style={panelStyle}>
                            <h2 style={sectionTitleStyle}>{t('Drift Trigger', '漂移檢查')}</h2>
                            {loadingOperatePermission ? null : canOperate ? (
                                <form onSubmit={handleDriftTrigger} style={{ display: 'grid', gap: '12px' }}>
                                    <select value={driftWindowKind} onChange={(event) => setDriftWindowKind(event.target.value)} style={inputStyle}>
                                        <option value="last_24h">{t('Last 24 Hours', '最近 24 小時')}</option>
                                        <option value="last_7d">{t('Last 7 Days', '最近 7 天')}</option>
                                        <option value="last_30d">{t('Last 30 Days', '最近 30 天')}</option>
                                    </select>
                                    <textarea
                                        value={driftNote}
                                        onChange={(event) => setDriftNote(event.target.value)}
                                        rows={3}
                                        placeholder={t('Optional operator note', '可選操作備註')}
                                        style={inputStyle}
                                    />
                                    <button type="submit" style={buttonPrimaryStyle} disabled={runningDrift}>
                                        {runningDrift ? t('Running...', '執行中...') : t('Run Drift Check', '執行漂移檢查')}
                                    </button>
                                </form>
                            ) : (
                                <div style={infoPanelStyle}>
                                    {t(
                                        'Triggering drift reports requires meta_andromeda:operate.',
                                        '執行漂移檢查需要 meta_andromeda:operate 權限。'
                                    )}
                                </div>
                            )}
                        </section>
                    </div>

                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: isMobile ? '1fr' : 'repeat(2, 1fr)',
                        gap: '16px'
                    }}>
                        <section style={panelStyle}>
                            <h2 style={sectionTitleStyle}>{t('Worker Host', 'Worker 宿主')}</h2>
                            <div style={{ display: 'grid', gap: '12px', marginBottom: '16px' }}>
                                <Metric label={t('active_host', '目前宿主')} value={summary?.worker_host?.active_host} />
                                <Metric label={t('host_strategy', '宿主策略')} value={summary?.worker_host?.host_strategy} />
                                <Metric label={t('dead_letter_count', '死信數量')} value={summary?.worker_host?.dead_letter_count} />
                            </div>

                            <div style={{ marginBottom: '14px' }}>
                                <div style={subTitleStyle}>{t('Recent Worker Events', '最近 Worker 事件')}</div>
                                <div style={{ display: 'grid', gap: '10px' }}>
                                    {visibleRecentEvents.map((event) => (
                                        <button
                                            key={event.worker_event_id}
                                            type="button"
                                            onClick={() => handleSelectTimeline(event.score_event_id)}
                                            style={{
                                                ...detailCardStyle,
                                                textAlign: 'left',
                                                cursor: 'pointer',
                                                borderColor: selectedScoreEventId === event.score_event_id
                                                    ? 'var(--accent-primary)'
                                                    : 'var(--glass-border)',
                                            }}
                                        >
                                            <div style={{ color: 'var(--accent-primary)', fontWeight: 700, marginBottom: '6px' }}>
                                                {event.event_type} · {event.queue_host}
                                            </div>
                                            <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6, fontSize: '0.9rem' }}>
                                                {t('status', '狀態')}: {event.status} / {t('attempt', '嘗試次數')}: {event.attempt_count}
                                            </div>
                                            <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6, fontSize: '0.9rem' }}>
                                                {event.score_event_id}
                                            </div>
                                            <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6, fontSize: '0.9rem' }}>
                                                {event.message || '--'}
                                            </div>
                                        </button>
                                    ))}
                                    {visibleRecentEvents.length === 0 && (
                                        <div style={emptyStateStyle}>{t('No worker events match the current filter.', '目前篩選條件下沒有 worker 事件。')}</div>
                                    )}
                                </div>
                            </div>

                            <div>
                                <div style={subTitleStyle}>{t('Dead Letters', '死信事件')}</div>
                                <div style={{ display: 'grid', gap: '10px' }}>
                                    {visibleDeadLetters.map((item) => (
                                        <button
                                            key={item.dead_letter_id}
                                            type="button"
                                            onClick={() => handleSelectTimeline(item.score_event_id)}
                                            style={{
                                                ...detailCardStyle,
                                                textAlign: 'left',
                                                cursor: 'pointer',
                                                borderColor: selectedScoreEventId === item.score_event_id
                                                    ? '#f59e0b'
                                                    : 'var(--glass-border)',
                                            }}
                                        >
                                            <div style={{ color: '#f59e0b', fontWeight: 700, marginBottom: '6px' }}>
                                                {item.failure_stage} · {item.queue_host}
                                            </div>
                                            <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6, fontSize: '0.9rem' }}>
                                                {item.score_event_id}
                                            </div>
                                            <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6, fontSize: '0.9rem' }}>
                                                {item.final_error_message}
                                            </div>
                                        </button>
                                    ))}
                                    {visibleDeadLetters.length === 0 && (
                                        <div style={emptyStateStyle}>{t('No dead letters match the current filter.', '目前篩選條件下沒有死信事件。')}</div>
                                    )}
                                </div>
                            </div>
                        </section>

                        <section style={panelStyle}>
                            <h2 style={sectionTitleStyle}>{t('Event Timeline', '事件時間線')}</h2>
                            {!selectedScoreEventId ? (
                                <div style={emptyStateStyle}>{t('Select a worker event or dead letter to inspect the full timeline.', '請先選擇一筆 worker event 或死信事件以查看完整時間線。')}</div>
                            ) : loadingTimeline ? (
                                <div style={emptyStateStyle}>{t('Loading event timeline...', '載入事件時間線中...')}</div>
                            ) : !timeline ? (
                                <div style={emptyStateStyle}>{t('Timeline is unavailable.', '目前無法取得時間線。')}</div>
                            ) : (
                                <div style={{ display: 'grid', gap: '12px' }}>
                                    <div style={detailCardStyle}>
                                        <div style={{ color: 'var(--text-secondary)', marginBottom: '6px' }}>score_event_id</div>
                                        <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{timeline.score_event.score_event_id}</div>
                                        <div style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>
                                            {timeline.score_event.status} · attempt {timeline.score_event.attempt_count}
                                        </div>
                                    </div>
                                    <div style={detailCardStyle}>
                                        <div style={subTitleStyle}>{t('Worker Timeline', 'Worker 時間線')}</div>
                                        <div style={{ display: 'grid', gap: '10px' }}>
                                            {(timeline.worker_events || []).map((event) => (
                                                <div key={event.worker_event_id} style={timelineItemStyle}>
                                                    <strong style={{ color: 'var(--text-primary)' }}>{event.event_type}</strong>
                                                    <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                                        {event.queue_host} · {event.status} · {event.created_at || '--'}
                                                    </div>
                                                    <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                                        {event.message || '--'}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                    <div style={detailCardStyle}>
                                        <div style={subTitleStyle}>{t('Dead Letter Detail', '死信明細')}</div>
                                        {(timeline.dead_letters || []).length === 0 ? (
                                            <div style={{ color: 'var(--text-secondary)' }}>{t('No dead letters for this score event.', '這筆 score event 沒有死信紀錄。')}</div>
                                        ) : (
                                            <div style={{ display: 'grid', gap: '10px' }}>
                                                {timeline.dead_letters.map((item) => (
                                                    <div key={item.dead_letter_id} style={timelineItemStyle}>
                                                        <strong style={{ color: '#f59e0b' }}>{item.failure_stage}</strong>
                                                        <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                                            {item.final_error_message}
                                                        </div>
                                                        <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                                            {item.created_at || '--'}
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                        </section>

                        <section style={panelStyle}>
                            <h2 style={sectionTitleStyle}>{t('Prediction Distribution', '預測分布')}</h2>
                            <div style={{ display: 'grid', gap: '10px' }}>
                                {Object.entries(summary?.prediction_distribution || {}).map(([band, count]) => (
                                    <div key={band} style={rowStyle}>
                                        <span style={{ color: 'var(--text-secondary)' }}>{band}</span>
                                        <strong style={{ color: 'var(--text-primary)' }}>{count}</strong>
                                    </div>
                                ))}
                            </div>
                        </section>

                        <section style={panelStyle}>
                            <h2 style={sectionTitleStyle}>{t('Latest Drift Reports', '最近漂移報告')}</h2>
                            <div style={{ display: 'grid', gap: '10px', marginBottom: '14px' }}>
                                {(summary?.latest_drift_reports || []).map((report) => (
                                    <div key={report.drift_report_id} style={detailCardStyle}>
                                        <div style={{ color: report.drift_status === 'stable' ? 'var(--accent-primary)' : '#f59e0b', fontWeight: 700, marginBottom: '6px' }}>
                                            {report.window_kind} · {report.drift_status}
                                        </div>
                                        <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>{report.summary}</div>
                                    </div>
                                ))}
                            </div>
                            <div style={{ display: 'grid', gap: '8px' }}>
                                {(summary?.notes || []).map((note, index) => (
                                    <div key={index} style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                        {note}
                                    </div>
                                ))}
                            </div>
                        </section>

                        <section style={panelStyle}>
                            <h2 style={sectionTitleStyle}>{t('Active Alerts', '目前告警')}</h2>
                            <div style={{ display: 'grid', gap: '10px' }}>
                                {(summary?.active_alerts || []).length === 0 ? (
                                    <div style={emptyStateStyle}>{t('No active alerts.', '目前沒有告警。')}</div>
                                ) : (summary?.active_alerts || []).map((alert, index) => (
                                    <div key={index} style={detailCardStyle}>
                                        <div style={{ color: 'var(--accent-primary)', fontWeight: 700, marginBottom: '6px' }}>
                                            {alert.severity} · {alert.code}
                                        </div>
                                        <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>{alert.message}</div>
                                    </div>
                                ))}
                            </div>
                        </section>
                    </div>
                </>
            )}
        </div>
    );
};

const Metric = ({ label, value }) => (
    <div style={detailCardStyle}>
        <div style={{ color: 'var(--text-secondary)', marginBottom: '6px', fontSize: '0.85rem' }}>{label}</div>
        <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{value ?? '--'}</div>
    </div>
);

const panelStyle = {
    background: 'var(--bg-secondary)',
    border: '1px solid var(--glass-border)',
    borderRadius: '16px',
    padding: '24px',
};

const sectionTitleStyle = {
    margin: '0 0 16px 0',
    color: 'var(--text-primary)',
    fontSize: '1rem',
};

const subTitleStyle = {
    marginBottom: '10px',
    color: 'var(--text-primary)',
    fontSize: '0.9rem',
    fontWeight: 700,
};

const metricGridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: '12px',
};

const detailCardStyle = {
    padding: '14px',
    borderRadius: '12px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.02)',
};

const rowStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px 14px',
    borderRadius: '12px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.02)',
};

const errorPanelStyle = {
    marginBottom: '16px',
    padding: '16px',
    borderRadius: '12px',
    background: 'rgba(239, 68, 68, 0.08)',
    border: '1px solid rgba(239, 68, 68, 0.18)',
    color: 'var(--text-primary)',
};

const inputStyle = {
    width: '100%',
    padding: '12px 14px',
    borderRadius: '12px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.03)',
    color: 'var(--text-primary)',
    outline: 'none',
};

const toggleLabelStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    color: 'var(--text-secondary)',
    fontSize: '0.9rem',
};

const actionButtonStyle = {
    padding: '12px 16px',
    borderRadius: '12px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.04)',
    color: 'var(--text-primary)',
    cursor: 'pointer',
    fontWeight: 700,
};

const buttonPrimaryStyle = {
    padding: '12px 16px',
    borderRadius: '10px',
    border: 'none',
    background: 'var(--accent-primary)',
    color: 'white',
    cursor: 'pointer',
};

const emptyStateStyle = {
    padding: '14px',
    borderRadius: '12px',
    border: '1px dashed var(--glass-border)',
    color: 'var(--text-secondary)',
};

const timelineItemStyle = {
    padding: '12px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.02)',
};

const infoPanelStyle = {
    padding: '12px 14px',
    borderRadius: '12px',
    background: 'rgba(59, 130, 246, 0.08)',
    border: '1px solid rgba(59, 130, 246, 0.18)',
    color: 'var(--text-secondary)',
    lineHeight: 1.7,
};

export default MetaAndromedaMonitoring;
