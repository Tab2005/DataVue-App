import React from 'react';

import {
    actionButtonStyle,
    detailCardStyle,
    emptyStateStyle,
    panelStyle,
    sectionTitleStyle,
} from './shared';

export const MonitoringScoringProfilesPanel = ({ isMobile, monitoring }) => {
    const {
        scoringProfiles,
        loadingProfiles,
        promotingProfile,
        backtestingProfile,
        backtestResults,
        t,
        formatDateTime,
        loadProfiles,
        handleRunBacktest,
        handlePromoteProfile,
    } = monitoring;

    return (
                        <section style={{ ...panelStyle, gridColumn: isMobile ? undefined : 'span 3' }}>
                            <h2 style={sectionTitleStyle}>{t('Scoring Profiles', 'Scoring Profiles 管理')}</h2>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', gap: '12px' }}>
                                <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                                    {t('AI scoring prompt profiles. Calibration auto-generates new profiles when ≥10 mismatch items are synced — review and promote here.', 'AI 評分使用的 Prompt Profile 管理。校準後（≥10 筆誤判）自動生成待審核 profile，在此審核並套用。')}
                                </div>
                                <button type="button" aria-label={t('Refresh scoring profiles', '重整 Scoring Profiles')} onClick={loadProfiles} style={{ ...actionButtonStyle, flexShrink: 0 }}>
                                    {t('Refresh', '重整')}
                                </button>
                            </div>

                            {(() => {
                                const pending = (scoringProfiles?.profiles || []).filter(
                                    (p) => p.source === 'calibration_auto' && !p.is_promoted
                                );
                                if (pending.length === 0) return null;
                                return (
                                    <div style={{
                                        marginBottom: '16px',
                                        padding: '14px',
                                        borderRadius: '12px',
                                        background: 'rgba(245, 158, 11, 0.06)',
                                        border: '1px solid rgba(245, 158, 11, 0.3)',
                                    }}>
                                        <div style={{ fontWeight: 700, color: '#f59e0b', marginBottom: '8px' }}>
                                            {t(`${pending.length} new calibration profile(s) pending review`, `${pending.length} 個新版校準 Profile 待審核`)}
                                        </div>
                                        {pending.map((p) => (
                                            <div key={p.profile_name} style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '10px' }}>
                                                <div style={{ fontSize: '0.88rem', color: 'var(--text-primary)', fontWeight: 600 }}>{p.profile_name}</div>
                                                {p.bias_summary && (
                                                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                                        {t('Bias', '偏差方向')}: <strong style={{ color: '#f59e0b' }}>{p.bias_summary.dominant_bias}</strong>
                                                        {' · '}{t('Items', '樣本')}: {p.bias_summary.total_items}
                                                        {' · '}{t('Over-predict', '預估偏高')}: {p.bias_summary.over_predict_count}
                                                        {' · '}{t('Under-predict', '預估偏低')}: {p.bias_summary.under_predict_count}
                                                    </div>
                                                )}
                                                {p.calibration_guidance && (
                                                    <div style={{ fontSize: '0.78rem', color: '#f59e0b', fontStyle: 'italic', lineHeight: 1.5 }}>
                                                        {p.calibration_guidance.slice(0, 180)}{p.calibration_guidance.length > 180 ? '...' : ''}
                                                    </div>
                                                )}
                                                {(() => {
                                                    const persisted = p.bias_summary?.holdout_backtest;
                                                    const fresh = backtestResults[p.profile_name];
                                                    const backtest = fresh || persisted;
                                                    if (!backtest) return null;
                                                    const passed = backtest.passed_gate === true;
                                                    return (
                                                        <div style={{
                                                            fontSize: '0.78rem',
                                                            padding: '8px 10px',
                                                            borderRadius: '6px',
                                                            background: passed ? 'rgba(52,211,153,0.08)' : 'rgba(239,68,68,0.08)',
                                                            border: `1px solid ${passed ? 'rgba(52,211,153,0.3)' : 'rgba(239,68,68,0.3)'}`,
                                                            color: passed ? '#34d399' : '#ef4444',
                                                        }}>
                                                            {t('Backtest', '回測')}: {passed
                                                                ? t('Passed', '通過')
                                                                : t('Not passed (candidate not confirmed better than production)', '未通過（未確定優於正式版）')}
                                                            {' · '}accuracy {backtest.baseline_accuracy?.toFixed?.(2) ?? backtest.baseline_accuracy} → {backtest.candidate_accuracy?.toFixed?.(2) ?? backtest.candidate_accuracy}
                                                            {' · '}Spearman {backtest.baseline_spearman?.toFixed?.(2) ?? backtest.baseline_spearman} → {backtest.candidate_spearman?.toFixed?.(2) ?? backtest.candidate_spearman}
                                                            {' · '}n={backtest.evaluated_count}
                                                        </div>
                                                    );
                                                })()}
                                                <div style={{ display: 'flex', gap: '8px' }}>
                                                    <button
                                                        type="button"
                                                        onClick={() => handleRunBacktest(p.profile_name)}
                                                        disabled={backtestingProfile === p.profile_name}
                                                        style={{
                                                            alignSelf: 'flex-start',
                                                            padding: '7px 14px',
                                                            borderRadius: '8px',
                                                            border: '1px solid rgba(245,158,11,0.5)',
                                                            background: 'transparent',
                                                            color: '#f59e0b',
                                                            fontWeight: 600,
                                                            fontSize: '0.82rem',
                                                            cursor: backtestingProfile === p.profile_name ? 'wait' : 'pointer',
                                                        }}
                                                    >
                                                        {backtestingProfile === p.profile_name
                                                            ? t('Running backtest...', '回測執行中...')
                                                            : t('Run Backtest', '執行回測')}
                                                    </button>
                                                    <button
                                                        type="button"
                                                        onClick={() => handlePromoteProfile(p.profile_name, p.bias_summary?.holdout_backtest)}
                                                        disabled={promotingProfile === p.profile_name}
                                                        style={{
                                                            alignSelf: 'flex-start',
                                                            padding: '7px 14px',
                                                            borderRadius: '8px',
                                                            border: 'none',
                                                            background: promotingProfile === p.profile_name ? 'rgba(245,158,11,0.3)' : '#f59e0b',
                                                            color: 'white',
                                                            fontWeight: 600,
                                                            fontSize: '0.82rem',
                                                            cursor: promotingProfile === p.profile_name ? 'wait' : 'pointer',
                                                        }}
                                                    >
                                                        {promotingProfile === p.profile_name
                                                            ? t('Promoting...', '套用中...')
                                                            : t('Promote This Profile', '套用此 Profile')}
                                                    </button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                );
                            })()}

                            <div
                                className="queue-scroll-box"
                                style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(2, 1fr)', gap: '10px', maxHeight: '320px', overflowY: 'auto', paddingRight: '6px' }}
                            >
                                {loadingProfiles ? (
                                    <div style={{ ...emptyStateStyle, gridColumn: '1 / -1' }}>{t('Loading profiles...', '載入 Profiles 中...')}</div>
                                ) : (scoringProfiles?.profiles || []).length === 0 ? (
                                    <div style={{ ...emptyStateStyle, gridColumn: '1 / -1' }}>{t('No scoring profiles found.', '尚無 Scoring Profile 記錄。')}</div>
                                ) : (scoringProfiles?.profiles || []).map((p) => (
                                    <div key={p.profile_name} style={{
                                        ...detailCardStyle,
                                        borderColor: p.is_promoted ? 'rgba(52, 211, 153, 0.4)' : 'var(--glass-border)',
                                        background: p.is_promoted ? 'rgba(52, 211, 153, 0.04)' : 'rgba(255,255,255,0.02)',
                                    }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '6px' }}>
                                            <div style={{ fontWeight: 700, color: p.is_promoted ? '#34d399' : 'var(--text-primary)', fontSize: '0.88rem' }}>
                                                {p.profile_name}
                                                {p.is_promoted && (
                                                    <span style={{ marginLeft: '8px', fontSize: '0.72rem', background: 'rgba(52,211,153,0.15)', color: '#34d399', padding: '2px 6px', borderRadius: '4px', fontWeight: 600 }}>
                                                        {t('ACTIVE', '生效中')}
                                                    </span>
                                                )}
                                            </div>
                                            <div style={{ display: 'flex', gap: '6px' }}>
                                                <span style={{
                                                    fontSize: '0.72rem',
                                                    padding: '2px 8px',
                                                    borderRadius: '4px',
                                                    fontWeight: 600,
                                                    background: p.source === 'calibration_auto' ? 'rgba(99,102,241,0.15)' : 'rgba(107,114,128,0.15)',
                                                    color: p.source === 'calibration_auto' ? '#818cf8' : '#9ca3af',
                                                }}>
                                                    {p.source === 'calibration_auto' ? t('auto', '自動校準') : t('seed', '初始')}
                                                </span>
                                            </div>
                                        </div>
                                        <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '6px' }}>
                                            {t('Created', '建立時間')}: {formatDateTime(p.created_at)}
                                            {p.is_promoted && p.promoted_at && (
                                                <span> · {t('Promoted', '套用時間')}: {formatDateTime(p.promoted_at)}</span>
                                            )}
                                            {p.few_shot_example_count > 0 && (
                                                <span> · {p.few_shot_example_count} {t('few-shot examples', '示範案例')}</span>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </section>
    );
};
