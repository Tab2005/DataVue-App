import React from 'react';

import {
    detailCardStyle,
    emptyStateStyle,
    panelStyle,
    sectionTitleStyle,
} from './shared';

export const MonitoringModelSettingsPanel = ({ isMobile, monitoring }) => {
    const {
        summary,
        modelRegistry,
        loadingModelRegistry,
        backtestModelInput,
        setBacktestModelInput,
        savingBacktestModel,
        effectiveStatus,
        candidateModelInput,
        setCandidateModelInput,
        validatingCandidate,
        candidateValidation,
        t,
        getTranslation,
        handleSaveBacktestModel,
        handleValidateCandidateModel,
    } = monitoring;

    return (
        <>
                        <section style={{ ...panelStyle, gridColumn: isMobile ? undefined : 'span 2' }}>
                            <h2 style={sectionTitleStyle}>{t('Model Settings', '模型設定')}</h2>
                            <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '14px' }}>
                                {t(
                                    'Interactive/production scoring model is changed via the Release workflow only (approve/rollback), shown here read-only. Backtest model is independent and can be set directly.',
                                    '互動／正式評分模型只能透過版本總覽的核准／回退流程變更，這裡僅唯讀顯示。回測模型是獨立設定，可直接在這裡調整。'
                                )}
                            </div>

                            {(() => {
                                const entries = modelRegistry?.entries || [];
                                const productionEntry = entries.find((e) => e.is_current_production);
                                return (
                                    <div style={{
                                        marginBottom: '16px',
                                        padding: '12px 14px',
                                        borderRadius: '10px',
                                        background: 'rgba(255,255,255,0.03)',
                                        border: '1px solid var(--glass-border)',
                                    }}>
                                        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                                            {t('Current interactive/production model', '目前生效中的互動／正式評分模型')}
                                        </div>
                                        {loadingModelRegistry ? (
                                            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{t('Loading...', '載入中...')}</div>
                                        ) : productionEntry ? (
                                            <div style={{ fontSize: '0.88rem', fontWeight: 600 }}>
                                                {productionEntry.provider_model}
                                                <span style={{ fontWeight: 400, color: 'var(--text-secondary)', marginLeft: '8px' }}>
                                                    ({productionEntry.model_version})
                                                </span>
                                            </div>
                                        ) : (
                                            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{t('Not found', '查無資料')}</div>
                                        )}
                                        <a href="/meta-andromeda/release" style={{ fontSize: '0.78rem', color: '#60a5fa' }}>
                                            {t('Change via Release Overview →', '至版本總覽變更 →')}
                                        </a>
                                    </div>
                                );
                            })()}

                            {effectiveStatus && (
                                <div style={{
                                    marginBottom: '16px',
                                    padding: '12px 14px',
                                    borderRadius: '10px',
                                    background: effectiveStatus.is_overridden ? 'rgba(245, 158, 11, 0.06)' : 'rgba(16, 185, 129, 0.06)',
                                    border: effectiveStatus.is_overridden ? '1px solid rgba(245, 158, 11, 0.3)' : '1px solid rgba(16, 185, 129, 0.25)',
                                }}>
                                    <div style={{
                                        fontSize: '0.8rem',
                                        fontWeight: 700,
                                        color: effectiveStatus.is_overridden ? '#fbbf24' : '#10b981',
                                        marginBottom: '4px',
                                    }}>
                                        {effectiveStatus.is_overridden
                                            ? t('⚠ Actual scoring uses an env-overridden model', '⚠ 實際評分目前使用環境變數覆寫的模型')
                                            : t('✓ Actual scoring matches the model shown above', '✓ 實際評分與上方顯示的模型一致')}
                                    </div>
                                    {effectiveStatus.is_overridden && (
                                        <>
                                            <div style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: '2px' }}>
                                                {t('In effect: ', '目前實際使用：')}{effectiveStatus.resolved_provider_model}
                                                <span style={{ fontWeight: 400, color: 'var(--text-secondary)', marginLeft: '6px' }}>
                                                    ({effectiveStatus.resolved_model_version})
                                                </span>
                                            </div>
                                            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                                                {t(
                                                    `Registry shows: ${effectiveStatus.db_production_provider_model || '--'} (${effectiveStatus.db_production_model_version || '--'})`,
                                                    `資料庫顯示：${effectiveStatus.db_production_provider_model || '--'}（${effectiveStatus.db_production_model_version || '--'}）`
                                                )}
                                            </div>
                                            <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                                                {t(
                                                    `Caused by deployment env vars (META_ANDROMEDA_SCORING_PROVIDER=${effectiveStatus.scoring_provider_setting}, META_ANDROMEDA_SCORING_MODEL=${effectiveStatus.scoring_model_setting}${effectiveStatus.scoring_model_version_env_set ? ', META_ANDROMEDA_SCORING_MODEL_VERSION is set' : ''}) — approving a new candidate in Release Overview will not change this until the env vars are cleared.`,
                                                    `原因來自部署環境變數（META_ANDROMEDA_SCORING_PROVIDER=${effectiveStatus.scoring_provider_setting}、META_ANDROMEDA_SCORING_MODEL=${effectiveStatus.scoring_model_setting}${effectiveStatus.scoring_model_version_env_set ? '、META_ANDROMEDA_SCORING_MODEL_VERSION 已設定' : ''}）——在版本總覽核准新候選版本前，這些環境變數不清除的話畫面與實際評分仍會不一致。`
                                                )}
                                            </div>
                                        </>
                                    )}
                                </div>
                            )}

                            <div style={{
                                padding: '12px 14px',
                                borderRadius: '10px',
                                background: 'rgba(255,255,255,0.03)',
                                border: '1px solid var(--glass-border)',
                            }}>
                                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                                    {t(
                                        'Backtest model (used only when running holdout backtests before promoting a candidate profile). Leave empty to fall back to the production model above.',
                                        '回測專用模型（僅在候選 profile 執行 holdout 回測時使用）。留空則自動退回使用上方的正式評分模型。'
                                    )}
                                </div>
                                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                                    <input
                                        type="text"
                                        value={backtestModelInput}
                                        onChange={(e) => setBacktestModelInput(e.target.value)}
                                        placeholder="e.g. openai/gpt-4o-mini"
                                        style={{
                                            flex: '1 1 260px',
                                            padding: '8px 10px',
                                            borderRadius: '8px',
                                            border: '1px solid var(--glass-border)',
                                            background: 'rgba(255,255,255,0.04)',
                                            color: 'var(--text-primary)',
                                            fontSize: '0.85rem',
                                        }}
                                    />
                                    <button
                                        type="button"
                                        onClick={handleSaveBacktestModel}
                                        disabled={savingBacktestModel || !backtestModelInput.trim()}
                                        style={{
                                            padding: '8px 16px',
                                            borderRadius: '8px',
                                            border: 'none',
                                            background: savingBacktestModel ? 'rgba(96,165,250,0.3)' : '#60a5fa',
                                            color: 'white',
                                            fontWeight: 600,
                                            fontSize: '0.85rem',
                                            cursor: savingBacktestModel ? 'wait' : 'pointer',
                                        }}
                                    >
                                        {savingBacktestModel ? t('Saving...', '儲存中...') : t('Save', '儲存')}
                                    </button>
                                </div>
                                {(() => {
                                    const backtestEntry = (modelRegistry?.entries || []).find((e) => e.release_channel === 'backtest_reference');
                                    if (!backtestEntry) return null;
                                    return (
                                        <div style={{ fontSize: '0.78rem', color: '#34d399', marginTop: '8px' }}>
                                            {t('Currently set to', '目前設定為')}: {backtestEntry.provider_model}
                                        </div>
                                    );
                                })()}
                            </div>

                            <div style={{
                                marginTop: '12px',
                                padding: '12px 14px',
                                borderRadius: '10px',
                                background: 'rgba(255,255,255,0.03)',
                                border: '1px solid var(--glass-border)',
                            }}>
                                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                                    {t(
                                        'Validate a candidate model before setting it (Release Overview candidate, or META_ANDROMEDA_SCORING_MODEL env override) — checks whether it actually exists on OpenRouter, supports image input, and what its real context/output limits are.',
                                        '換模型前先驗證（不管是要設版本總覽的候選，還是要設 META_ANDROMEDA_SCORING_MODEL 環境變數覆寫）——查這個模型是否真的存在於 OpenRouter、支不支援圖片輸入、實際 context/輸出上限多大。'
                                    )}
                                </div>
                                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                                    <input
                                        type="text"
                                        value={candidateModelInput}
                                        onChange={(e) => setCandidateModelInput(e.target.value)}
                                        placeholder="e.g. nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"
                                        style={{
                                            flex: '1 1 260px',
                                            padding: '8px 10px',
                                            borderRadius: '8px',
                                            border: '1px solid var(--glass-border)',
                                            background: 'rgba(255,255,255,0.04)',
                                            color: 'var(--text-primary)',
                                            fontSize: '0.85rem',
                                        }}
                                    />
                                    <button
                                        type="button"
                                        onClick={handleValidateCandidateModel}
                                        disabled={validatingCandidate || !candidateModelInput.trim()}
                                        style={{
                                            padding: '8px 16px',
                                            borderRadius: '8px',
                                            border: 'none',
                                            background: validatingCandidate ? 'rgba(96,165,250,0.3)' : '#60a5fa',
                                            color: 'white',
                                            fontWeight: 600,
                                            fontSize: '0.85rem',
                                            cursor: validatingCandidate ? 'wait' : 'pointer',
                                        }}
                                    >
                                        {validatingCandidate ? t('Checking...', '查詢中...') : t('Check', '查詢')}
                                    </button>
                                </div>
                                {candidateValidation && (
                                    <div style={{
                                        marginTop: '10px',
                                        padding: '10px 12px',
                                        borderRadius: '8px',
                                        background: candidateValidation.ok ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)',
                                        border: candidateValidation.ok ? '1px solid rgba(16,185,129,0.3)' : '1px solid rgba(239,68,68,0.3)',
                                        fontSize: '0.8rem',
                                    }}>
                                        <div style={{ fontWeight: 700, color: candidateValidation.ok ? '#34d399' : '#f87171', marginBottom: '4px' }}>
                                            {candidateValidation.exists === false
                                                ? t('✗ Model not found on OpenRouter', '✗ 這個模型 ID 在 OpenRouter 查無資料')
                                                : candidateValidation.ok
                                                    ? t('✓ Looks safe to use', '✓ 可以安全使用')
                                                    : t('⚠ Found, but has issues', '⚠ 查得到，但有問題')}
                                        </div>
                                        {candidateValidation.exists !== false && (
                                            <div style={{ color: 'var(--text-secondary)', marginBottom: candidateValidation.issues?.length ? '6px' : 0 }}>
                                                {candidateValidation.name && <span>{candidateValidation.name} · </span>}
                                                {t('context', '上下文')}: {candidateValidation.context_length ?? '--'} tokens ·{' '}
                                                {t('max output', '輸出上限')}: {candidateValidation.max_completion_tokens ?? '--'} tokens ·{' '}
                                                {t('image input', '圖片輸入')}: {candidateValidation.supports_image_input ? t('yes', '支援') : t('no', '不支援')}
                                                {candidateValidation.is_free && <span> · {t('free', '免費')}</span>}
                                            </div>
                                        )}
                                        {(candidateValidation.issues || []).map((issue, idx) => (
                                            <div key={idx} style={{ color: '#fbbf24', marginTop: '2px' }}>• {issue}</div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </section>

                        <section style={panelStyle}>
                            <h2 style={sectionTitleStyle}>{t('Active Alerts', '目前告警')}</h2>
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
                                {(summary?.active_alerts || []).length === 0 ? (
                                    <div style={emptyStateStyle}>{t('No active alerts.', '目前沒有告警。')}</div>
                                ) : (summary?.active_alerts || []).map((alert, index) => {
                                    const isTransition = alert.code === 'period_state_transition';
                                    const transitionStateColors = {
                                        dual_advantage:   { bg: 'rgba(16,185,129,0.12)',  border: 'rgba(16,185,129,0.4)',  text: '#34d399' },
                                        market_driven:    { bg: 'rgba(59,130,246,0.12)',  border: 'rgba(59,130,246,0.4)',  text: '#60a5fa' },
                                        creative_critical:{ bg: 'rgba(245,158,11,0.12)',  border: 'rgba(245,158,11,0.4)',  text: '#f59e0b' },
                                        needs_review:     { bg: 'rgba(239,68,68,0.12)',   border: 'rgba(239,68,68,0.4)',   text: '#f87171' },
                                    };
                                    const severityColor = { high: '#f87171', medium: '#f59e0b', info: '#60a5fa' };
                                    const headerColor = severityColor[alert.severity] || 'var(--accent-primary)';

                                    if (isTransition) {
                                        const fromC = transitionStateColors[alert.from_state] || transitionStateColors.needs_review;
                                        const toC = transitionStateColors[alert.to_state] || transitionStateColors.needs_review;
                                        const toCardBorder = toC.border;
                                        return (
                                            <div key={index} style={{
                                                ...detailCardStyle,
                                                borderColor: toCardBorder,
                                                background: `linear-gradient(135deg, ${fromC.bg}, ${toC.bg})`,
                                            }}>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', flexWrap: 'wrap' }}>
                                                    <span style={{ fontSize: '0.72rem', color: '#f59e0b', fontWeight: 700, letterSpacing: '0.05em' }}>
                                                        {t('QUADRANT SHIFT', '象限切換')}
                                                    </span>
                                                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                                        <span style={{
                                                            padding: '2px 8px', borderRadius: '5px',
                                                            background: fromC.bg, border: `1px solid ${fromC.border}`,
                                                            color: fromC.text, fontWeight: 700, fontSize: '0.78rem', whiteSpace: 'nowrap',
                                                        }}>
                                                            {alert.from_state ? alert.from_state.replace(/_/g, ' ') : '--'}
                                                        </span>
                                                        <span style={{ color: 'var(--text-secondary)' }}>→</span>
                                                        <span style={{
                                                            padding: '2px 8px', borderRadius: '5px',
                                                            background: toC.bg, border: `1px solid ${toC.border}`,
                                                            color: toC.text, fontWeight: 700, fontSize: '0.78rem', whiteSpace: 'nowrap',
                                                        }}>
                                                            {alert.to_state ? alert.to_state.replace(/_/g, ' ') : '--'}
                                                        </span>
                                                    </div>
                                                </div>
                                                <div style={{ color: 'var(--text-secondary)', lineHeight: 1.7, fontSize: '0.85rem' }}>
                                                    {alert.message.replace(/^【象限切換】[^。]+。/, '')}
                                                </div>
                                            </div>
                                        );
                                    }

                                    return (
                                        <div key={index} style={{
                                            ...detailCardStyle,
                                            borderColor: alert.severity === 'high' ? 'rgba(239,68,68,0.3)' : 'var(--glass-border)',
                                        }}>
                                            <div style={{ color: headerColor, fontWeight: 700, marginBottom: '6px', fontSize: '0.85rem' }}>
                                                {getTranslation(alert.severity)} · {alert.code}
                                            </div>
                                            <div style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>{alert.message}</div>
                                        </div>
                                    );
                                })}
                            </div>
                        </section>
        </>
    );
};
