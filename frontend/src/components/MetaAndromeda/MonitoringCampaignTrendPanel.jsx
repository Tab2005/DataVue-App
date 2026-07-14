import React from 'react';

import {
    actionButtonStyle,
    detailCardStyle,
    emptyStateStyle,
    inputStyle,
    panelStyle,
    sectionTitleStyle,
    subTitleStyle,
} from './shared';

export const MonitoringCampaignTrendPanel = ({ monitoring }) => {
    const {
        loading,
        driftTrend,
        loadingTrend,
        observedAccounts,
        trendAccountId,
        setTrendAccountId,
        t,
        getTranslation,
        loadDriftTrend,
    } = monitoring;

    return (
        <>
            {/* 投放趨勢 */}
            {!loading && (() => {
                const trendEntries = driftTrend?.entries || [];
                const stateColors = {
                    dual_advantage:   { bg: 'rgba(16,185,129,0.07)',  border: 'rgba(16,185,129,0.35)',  dot: '#34d399', text: '#34d399' },
                    market_driven:    { bg: 'rgba(59,130,246,0.07)',  border: 'rgba(59,130,246,0.35)',  dot: '#60a5fa', text: '#60a5fa' },
                    creative_critical:{ bg: 'rgba(245,158,11,0.07)',  border: 'rgba(245,158,11,0.35)',  dot: '#f59e0b', text: '#f59e0b' },
                    needs_review:     { bg: 'rgba(239,68,68,0.07)',   border: 'rgba(239,68,68,0.35)',   dot: '#f87171', text: '#f87171' },
                };
                const driftStatusColor = { healthy: '#34d399', warning: '#f59e0b', drifted: '#f87171', insufficient_data: '#6b7280' };

                const formatEntryDate = (entry) => {
                    if (entry.window_kind === 'custom' && entry.since && entry.until) {
                        return `${entry.since} ~ ${entry.until}`;
                    }
                    if (entry.note) {
                        const match = entry.note.match(/(\d{4}-\d{2}-\d{2})\s*~\s*(\d{4}-\d{2}-\d{2})/);
                        if (match) return `${match[1]} ~ ${match[2]}`;
                    }
                    if (entry.created_at) return entry.created_at.slice(0, 10);
                    return '--';
                };

                const windowLabel = (wk) => {
                    const map = { last_24h: '24h', last_7d: '7d', last_30d: '30d', lifetime: '全歷史', custom: '自訂' };
                    return map[wk] || wk;
                };

                return (
                    <section style={{ ...panelStyle, marginTop: '16px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '10px' }}>
                            <h2 style={{ ...sectionTitleStyle, margin: 0 }}>{t('Campaign Environment Trend', '投放趨勢')}</h2>
                            <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                                {observedAccounts.length > 0 ? (
                                    <select
                                        value={trendAccountId}
                                        onChange={(e) => {
                                            setTrendAccountId(e.target.value);
                                            loadDriftTrend(e.target.value || null);
                                        }}
                                        style={{ ...inputStyle, width: '260px', padding: '8px 12px', fontSize: '0.82rem' }}
                                    >
                                        <option value="">{t('All accounts', '全部帳號')}</option>
                                        {observedAccounts.map((acc) => (
                                            <option key={acc.account_id} value={acc.account_id}>
                                                {acc.account_id}
                                                {acc.platform !== 'facebook_ads' ? ` (${acc.platform})` : ''}
                                                {' '}· {acc.total_creatives} {t('creatives', '筆')}
                                            </option>
                                        ))}
                                    </select>
                                ) : (
                                    <>
                                        <input
                                            type="text"
                                            value={trendAccountId}
                                            onChange={(e) => setTrendAccountId(e.target.value)}
                                            placeholder={t('Filter by account ID', '依帳號 ID 篩選')}
                                            style={{ ...inputStyle, width: '220px', padding: '8px 12px', fontSize: '0.82rem' }}
                                        />
                                        <button
                                            type="button"
                                            onClick={() => loadDriftTrend(trendAccountId || null)}
                                            style={actionButtonStyle}
                                        >
                                            {t('Apply', '套用')}
                                        </button>
                                    </>
                                )}
                            </div>
                        </div>
                        {trendAccountId && observedAccounts.length > 1 && (
                            <div style={{ fontSize: '0.78rem', color: '#60a5fa', marginBottom: '12px' }}>
                                {t('Showing trend for account:', '目前顯示帳號：')} <strong>{trendAccountId}</strong>
                                <button
                                    type="button"
                                    onClick={() => { setTrendAccountId(''); loadDriftTrend(''); }}
                                    style={{ marginLeft: '8px', background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '0.78rem' }}
                                >
                                    {t('Clear', '清除篩選')}
                                </button>
                            </div>
                        )}

                        {loadingTrend ? (
                            <div style={emptyStateStyle}>{t('Loading trend data...', '載入趨勢資料中...')}</div>
                        ) : trendEntries.length === 0 ? (
                            <div style={emptyStateStyle}>
                                {t(
                                    'No trend data yet. Run a drift check with sufficient matched data (≥5 pairs) to start tracking campaign environment quadrant history.',
                                    '尚無趨勢資料。執行預估偏差檢查且配對成功 ≥5 筆後，投放環境象限歷史會顯示於此。'
                                )}
                            </div>
                        ) : (
                            <>
                                {/* 橫向時間軸 */}
                                <div
                                    className="queue-scroll-box"
                                    style={{
                                        overflowX: 'auto',
                                        paddingBottom: '8px',
                                        marginBottom: '20px',
                                    }}
                                >
                                    <div style={{
                                        display: 'flex',
                                        alignItems: 'flex-start',
                                        gap: '0',
                                        minWidth: `${trendEntries.length * 160}px`,
                                        paddingTop: '8px',
                                    }}>
                                        {trendEntries.map((entry, idx) => {
                                            const c = stateColors[entry.period_state] || stateColors.needs_review;
                                            const dColor = driftStatusColor[entry.drift_status] || '#6b7280';
                                            const prevState = idx > 0 ? trendEntries[idx - 1].period_state : null;
                                            const stateChanged = prevState && prevState !== entry.period_state;
                                            const isLast = idx === trendEntries.length - 1;

                                            return (
                                                <div key={entry.drift_report_id} style={{ display: 'flex', alignItems: 'flex-start', flex: 1 }}>
                                                    {/* 連接線 + 節點 */}
                                                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1 }}>
                                                        {/* 時間軸線段 + 節點 */}
                                                        <div style={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                                                            {/* 左側線 */}
                                                            {idx > 0 && (
                                                                <div style={{
                                                                    flex: 1,
                                                                    height: '2px',
                                                                    background: stateChanged
                                                                        ? 'linear-gradient(to right, rgba(107,114,128,0.3), rgba(107,114,128,0.6))'
                                                                        : 'rgba(107,114,128,0.3)',
                                                                }} />
                                                            )}
                                                            {/* 節點圓點 */}
                                                            <div style={{
                                                                width: '14px',
                                                                height: '14px',
                                                                borderRadius: '50%',
                                                                background: c.dot,
                                                                border: stateChanged ? `3px solid ${c.dot}` : `2px solid ${c.dot}`,
                                                                flexShrink: 0,
                                                                boxShadow: stateChanged ? `0 0 8px ${c.dot}` : 'none',
                                                            }} />
                                                            {/* 右側線 */}
                                                            {!isLast && (
                                                                <div style={{
                                                                    flex: 1,
                                                                    height: '2px',
                                                                    background: 'rgba(107,114,128,0.3)',
                                                                }} />
                                                            )}
                                                        </div>

                                                        {/* 節點資訊 */}
                                                        <div style={{ marginTop: '10px', textAlign: 'center', padding: '0 4px' }}>
                                                            <div style={{
                                                                display: 'inline-block',
                                                                padding: '2px 8px',
                                                                borderRadius: '6px',
                                                                background: c.bg,
                                                                border: `1px solid ${c.border}`,
                                                                color: c.text,
                                                                fontWeight: 700,
                                                                fontSize: '0.72rem',
                                                                marginBottom: '4px',
                                                                whiteSpace: 'nowrap',
                                                            }}>
                                                                {entry.period_label}
                                                            </div>
                                                            <div style={{ fontSize: '0.7rem', color: dColor, fontWeight: 600, marginBottom: '2px' }}>
                                                                {entry.spearman_r != null ? `ρ=${entry.spearman_r.toFixed(3)}` : '--'}
                                                            </div>
                                                            <div style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                                                                [{windowLabel(entry.window_kind)}]
                                                            </div>
                                                            <div style={{ fontSize: '0.66rem', color: 'var(--text-secondary)', marginTop: '2px', whiteSpace: 'nowrap' }}>
                                                                {formatEntryDate(entry)}
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>

                                {/* 象限切換提醒 */}
                                {(() => {
                                    const transitions = [];
                                    for (let i = 1; i < trendEntries.length; i++) {
                                        const prev = trendEntries[i - 1];
                                        const curr = trendEntries[i];
                                        if (prev.period_state && curr.period_state && prev.period_state !== curr.period_state) {
                                            transitions.push({ from: prev, to: curr, idx: i });
                                        }
                                    }
                                    if (transitions.length === 0) return null;
                                    return (
                                        <div style={{ marginBottom: '16px' }}>
                                            <div style={{ ...subTitleStyle, marginBottom: '8px' }}>
                                                {t('State Transitions', '象限切換紀錄')}
                                            </div>
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                                {transitions.map(({ from, to, idx }) => {
                                                    const fromC = stateColors[from.period_state] || stateColors.needs_review;
                                                    const toC = stateColors[to.period_state] || stateColors.needs_review;
                                                    return (
                                                        <div key={idx} style={{
                                                            padding: '10px 14px',
                                                            borderRadius: '10px',
                                                            background: 'rgba(255,255,255,0.02)',
                                                            border: `1px solid ${toC.border}`,
                                                            display: 'flex',
                                                            alignItems: 'center',
                                                            gap: '10px',
                                                            flexWrap: 'wrap',
                                                        }}>
                                                            <span style={{ fontSize: '0.8rem', color: fromC.text, fontWeight: 700 }}>
                                                                {from.period_label || from.period_state}
                                                            </span>
                                                            <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>→</span>
                                                            <span style={{ fontSize: '0.8rem', color: toC.text, fontWeight: 700 }}>
                                                                {to.period_label || to.period_state}
                                                            </span>
                                                            <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginLeft: 'auto' }}>
                                                                {formatEntryDate(to)}
                                                            </span>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    );
                                })()}

                                {/* 明細列表 */}
                                <div>
                                    <div style={{ ...subTitleStyle, marginBottom: '8px' }}>
                                        {t('Report Detail', '各期報告明細')}
                                    </div>
                                    <div
                                        className="queue-scroll-box"
                                        style={{ display: 'grid', gap: '8px', maxHeight: '320px', overflowY: 'auto', paddingRight: '6px' }}
                                    >
                                        {[...trendEntries].reverse().map((entry) => {
                                            const c = stateColors[entry.period_state] || stateColors.needs_review;
                                            const dColor = driftStatusColor[entry.drift_status] || '#6b7280';
                                            return (
                                                <div key={entry.drift_report_id} style={{
                                                    ...detailCardStyle,
                                                    borderColor: entry.period_state ? c.border : 'var(--glass-border)',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    gap: '12px',
                                                    flexWrap: 'wrap',
                                                }}>
                                                    <div style={{ flex: '0 0 auto' }}>
                                                        {entry.period_label ? (
                                                            <span style={{
                                                                padding: '3px 8px',
                                                                borderRadius: '6px',
                                                                background: c.bg,
                                                                border: `1px solid ${c.border}`,
                                                                color: c.text,
                                                                fontWeight: 700,
                                                                fontSize: '0.78rem',
                                                                whiteSpace: 'nowrap',
                                                            }}>
                                                                {entry.period_label}
                                                            </span>
                                                        ) : (
                                                            <span style={{ fontSize: '0.78rem', color: '#6b7280' }}>--</span>
                                                        )}
                                                    </div>
                                                    <div style={{ flex: 1, minWidth: '120px' }}>
                                                        <div style={{ fontSize: '0.8rem', color: dColor, fontWeight: 600 }}>
                                                            ρ = {entry.spearman_r != null ? entry.spearman_r.toFixed(3) : '--'}
                                                            {entry.creative_explained_variance != null && (
                                                                <span style={{ fontWeight: 400, color: 'var(--text-secondary)' }}>
                                                                    {' '}(ρ²={( entry.creative_explained_variance * 100).toFixed(1)}%)
                                                                </span>
                                                            )}
                                                        </div>
                                                        <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                                                            {entry.perf_median != null && (
                                                                <span>{(entry.dominant_metric || 'ROAS').toUpperCase()} P50={entry.perf_median.toFixed(2)} · </span>
                                                            )}
                                                            {t('Matched', '配對')}: {entry.total_matched ?? '--'}
                                                        </div>
                                                    </div>
                                                    <div style={{ flex: '0 0 auto', textAlign: 'right' }}>
                                                        {entry.account_id && (
                                                            <div style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', marginBottom: '2px', fontFamily: 'monospace' }}>
                                                                {entry.account_id}
                                                            </div>
                                                        )}
                                                        <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                                                            [{windowLabel(entry.window_kind)}] {formatEntryDate(entry)}
                                                        </div>
                                                        <div style={{ fontSize: '0.7rem', color: driftStatusColor[entry.drift_status] || '#6b7280', marginTop: '2px', fontWeight: 600 }}>
                                                            {getTranslation(entry.drift_status)}
                                                        </div>
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            </>
                        )}
                    </section>
                );
            })()}
        </>
    );
};
