import React from 'react';

import {
    detailCardStyle,
    emptyStateStyle,
    panelStyle,
    sectionTitleStyle,
    subTitleStyle,
    timelineItemStyle,
} from './shared';

export const MonitoringEventsPanel = ({ isMobile, monitoring }) => {
    const {
        summary,
        timeline,
        loadingTimeline,
        runningCleanup,
        cleanupResult,
        selectedScoreEventId,
        t,
        getTranslation,
        formatDateTime,
        visibleRecentEvents,
        visibleDeadLetters,
        handleSelectTimeline,
        handleCleanupStale,
    } = monitoring;

    return (
        <>
                        <section style={panelStyle}>
                            <h2 style={sectionTitleStyle}>{t('Worker Host', 'Worker 主機')}</h2>
                            <div style={{ display: 'flex', gap: '12px', marginBottom: '14px', flexWrap: 'wrap' }}>
                                <div style={{ flex: '1 1 auto', minWidth: 0, padding: '8px 12px', borderRadius: '8px', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--glass-border)' }}>
                                    <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginBottom: '2px' }}>{t('Host', '主機')}</div>
                                    <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.85rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{summary?.worker_host?.active_host || '--'}</div>
                                </div>
                                <div style={{ flex: '0 0 auto', padding: '8px 12px', borderRadius: '8px', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--glass-border)' }}>
                                    <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginBottom: '2px' }}>{t('Strategy', '策略')}</div>
                                    <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.85rem' }}>{getTranslation(summary?.worker_host?.host_strategy) || '--'}</div>
                                </div>
                                <div style={{ flex: '0 0 auto', padding: '8px 12px', borderRadius: '8px', background: (summary?.worker_host?.dead_letter_count || 0) > 0 ? 'rgba(239,68,68,0.08)' : 'rgba(255,255,255,0.04)', border: `1px solid ${(summary?.worker_host?.dead_letter_count || 0) > 0 ? 'rgba(239,68,68,0.3)' : 'var(--glass-border)'}` }}>
                                    <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginBottom: '2px' }}>{t('Dead Letters', '異常任務')}</div>
                                    <div style={{ fontWeight: 700, color: (summary?.worker_host?.dead_letter_count || 0) > 0 ? '#f87171' : 'var(--text-primary)', fontSize: '0.85rem' }}>{summary?.worker_host?.dead_letter_count ?? '--'}</div>
                                </div>
                            </div>

                            <div style={{ marginBottom: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                                <button
                                    type="button"
                                    onClick={handleCleanupStale}
                                    disabled={runningCleanup}
                                    style={{
                                        padding: '10px 16px',
                                        borderRadius: '10px',
                                        border: '1px solid rgba(239, 68, 68, 0.3)',
                                        background: runningCleanup ? 'rgba(239, 68, 68, 0.05)' : 'rgba(239, 68, 68, 0.08)',
                                        color: runningCleanup ? 'var(--text-secondary)' : '#f87171',
                                        fontWeight: 600,
                                        fontSize: '0.88rem',
                                        cursor: runningCleanup ? 'wait' : 'pointer',
                                        textAlign: 'left',
                                    }}
                                >
                                    {runningCleanup
                                        ? t('Cleaning up...', '清除中...')
                                        : t('Clear Stuck Score Events (queued / processing > 30 min)', '清除卡死評分任務（queued / processing 超過 30 分鐘）')}
                                </button>
                                {cleanupResult && (
                                    <div style={{
                                        padding: '12px 14px',
                                        borderRadius: '10px',
                                        border: '1px solid rgba(52, 211, 153, 0.25)',
                                        background: 'rgba(52, 211, 153, 0.06)',
                                        color: 'var(--text-secondary)',
                                        fontSize: '0.85rem',
                                        lineHeight: 1.7,
                                    }}>
                                        <strong style={{ color: '#34d399' }}>
                                            {t('Cleanup complete', '清除完成')} · {cleanupResult.cleaned_total} {t('events terminated', '筆任務已終止')}
                                        </strong>
                                        <div>{t('Cutoff', '截止時間')}: {formatDateTime(cleanupResult.cutoff_timestamp)}</div>
                                        {cleanupResult.removed_scheduler_jobs > 0 && (
                                            <div>{t('Scheduler jobs removed', '已移除排程工作')}: {cleanupResult.removed_scheduler_jobs}</div>
                                        )}
                                    </div>
                                )}
                            </div>

                            <div style={{ marginBottom: '14px' }}>
                                <div style={subTitleStyle}>{t('Recent Worker Events', '最近 Worker 事件')}</div>
                                <div 
                                    className="queue-scroll-box"
                                    style={{ 
                                        display: 'grid', 
                                        gap: '10px',
                                        maxHeight: '350px',
                                        overflowY: 'auto',
                                        paddingRight: '6px'
                                    }}
                                >
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
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                                                <div style={{ color: 'var(--accent-primary)', fontWeight: 700 }}>
                                                    {getTranslation(event.event_type)} · {event.queue_host}
                                                </div>
                                                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                                    {formatDateTime(event.created_at)}
                                                </span>
                                            </div>
                                            <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6, fontSize: '0.9rem' }}>
                                                {t('status', '狀態')}: {getTranslation(event.status)} / {t('attempt', '嘗試次數')}: {event.attempt_count}
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
                                <div style={subTitleStyle}>{t('Dead Letters', '異常任務')}</div>
                                <div 
                                    className="queue-scroll-box"
                                    style={{ 
                                        display: 'grid', 
                                        gap: '10px',
                                        maxHeight: '350px',
                                        overflowY: 'auto',
                                        paddingRight: '6px'
                                    }}
                                >
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
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                                                <div style={{ color: '#f59e0b', fontWeight: 700 }}>
                                                    {getTranslation(item.failure_stage)} · {item.queue_host}
                                                </div>
                                                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                                    {formatDateTime(item.created_at)}
                                                </span>
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
                                        <div style={emptyStateStyle}>{t('No dead letters match the current filter.', '目前篩選條件下沒有異常任務。')}</div>
                                    )}
                                </div>
                            </div>
                        </section>

                        <section style={{ ...panelStyle, gridColumn: isMobile ? undefined : 'span 2' }}>
                            <h2 style={sectionTitleStyle}>{t('Event Timeline', '事件時間軸')}</h2>
                            {!selectedScoreEventId ? (
                                <div style={emptyStateStyle}>{t('Select a worker event or dead letter to inspect the full timeline.', '請先選擇一筆 worker event 或異常任務以查看完整時間軸。')}</div>
                            ) : loadingTimeline ? (
                                <div style={emptyStateStyle}>{t('Loading event timeline...', '載入事件時間軸中...')}</div>
                            ) : !timeline ? (
                                <div style={emptyStateStyle}>{t('Timeline is unavailable.', '目前無法取得時間軸。')}</div>
                            ) : (
                                <div style={{ display: 'grid', gap: '12px' }}>
                                    <div style={detailCardStyle}>
                                        <div style={{ color: 'var(--text-secondary)', marginBottom: '6px' }}>{t('Score Event ID', '評分事件 ID')}</div>
                                        <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{timeline.score_event.score_event_id}</div>
                                        <div style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>
                                            {getTranslation(timeline.score_event.status)} · {t('attempt', '嘗試')} {timeline.score_event.attempt_count}
                                        </div>
                                    </div>
                                    <div style={detailCardStyle}>
                                        <div style={subTitleStyle}>{t('Worker Timeline', 'Worker 時間軸')}</div>
                                        <div style={{ display: 'grid', gap: '10px' }}>
                                            {(timeline.worker_events || []).map((event) => (
                                                <div key={event.worker_event_id} style={timelineItemStyle}>
                                                    <strong style={{ color: 'var(--text-primary)' }}>{getTranslation(event.event_type)}</strong>
                                                    <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                                        {event.queue_host} · {getTranslation(event.status)} · {formatDateTime(event.created_at)}
                                                    </div>
                                                    <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                                        {event.message || '--'}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                    <div style={detailCardStyle}>
                                        <div style={subTitleStyle}>{t('Dead Letter Detail', '異常任務明細')}</div>
                                        {(timeline.dead_letters || []).length === 0 ? (
                                            <div style={{ color: 'var(--text-secondary)' }}>{t('No dead letters for this score event.', '這筆 score event 沒有異常任務紀錄。')}</div>
                                        ) : (
                                            <div style={{ display: 'grid', gap: '10px' }}>
                                                {timeline.dead_letters.map((item) => (
                                                    <div key={item.dead_letter_id} style={timelineItemStyle}>
                                                        <strong style={{ color: '#f59e0b' }}>{getTranslation(item.failure_stage)}</strong>
                                                        <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                                            {item.final_error_message}
                                                        </div>
                                                        <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                                            {formatDateTime(item.created_at)}
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
                            {(() => {
                                const dist = summary?.prediction_distribution || {};
                                const total = Object.values(dist).reduce((s, v) => s + (v || 0), 0);
                                const bandColors = { high: '#10b981', mid: '#f59e0b', low: '#ef4444' };
                                const bandOrder = ['high', 'mid', 'low'];
                                return (
                                    <div style={{ display: 'grid', gap: '12px' }}>
                                        {bandOrder.map((band) => {
                                            const count = dist[band] ?? 0;
                                            const pct = total > 0 ? (count / total) * 100 : 0;
                                            const color = bandColors[band] || 'var(--accent-primary)';
                                            return (
                                                <div key={band}>
                                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                                                        <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{getTranslation(band)}</span>
                                                        <span style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.85rem' }}>{count} <span style={{ fontWeight: 400, color: 'var(--text-secondary)', fontSize: '0.78rem' }}>({pct.toFixed(0)}%)</span></span>
                                                    </div>
                                                    <div style={{ height: '6px', borderRadius: '3px', background: 'rgba(255,255,255,0.08)' }}>
                                                        <div style={{ height: '100%', borderRadius: '3px', background: color, width: `${pct}%`, transition: 'width 0.4s ease' }} />
                                                    </div>
                                                </div>
                                            );
                                        })}
                                        {total > 0 && (
                                            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textAlign: 'right' }}>
                                                {t('Total', '合計')} {total} {t('predictions', '筆預測')}
                                            </div>
                                        )}
                                    </div>
                                );
                            })()}
                        </section>
        </>
    );
};
