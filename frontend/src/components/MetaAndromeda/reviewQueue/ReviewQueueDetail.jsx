import { formatPerfValue, getDiagnosticLabel, getPerfMetricLabel, getPredictedBandLabel } from '../../../utils/metaAndromedaLabels';
import {
    detailCardStyle,
    innerCardStyle,
    labelStyle,
    listStyle,
    panelStyle,
    resolvePreviewUrl,
    roasBandColor,
    sectionTitleStyle,
} from './reviewQueueShared';

const ReviewQueueDetail = ({ detail, isMobile, loadingDetail, language, t }) => (
    <section style={panelStyle}>
        <h2 style={sectionTitleStyle}>{t('Evaluation Detail', '評估明細')}</h2>
        {loadingDetail ? (
            <div style={{ color: 'var(--text-secondary)' }}>{t('Loading...', '載入中...')}</div>
        ) : !detail ? (
            <div style={{ color: 'var(--text-secondary)' }}>{t('Select a record to view details.', '請選擇一筆紀錄查看明細。')}</div>
        ) : (
            <div className="queue-scroll-box" style={{ display: 'grid', gap: '14px', maxHeight: 'calc(100vh - 290px)', overflowY: 'auto', paddingRight: '4px' }}>
                <PreviewCard detail={detail} t={t} />
                <ScoreSummary detail={detail} isMobile={isMobile} language={language} t={t} />
                <ScoringEngineCard detail={detail} t={t} />
                <ObservationCard detail={detail} language={language} t={t} />
                <SummaryCard detail={detail} t={t} />
                <DiagnosticBreakdown detail={detail} language={language} t={t} />
                <DriverCards detail={detail} isMobile={isMobile} t={t} />
                <AdCopyContext detail={detail} t={t} />
            </div>
        )}
    </section>
);

const PreviewCard = ({ detail, t }) => {
    const url = resolvePreviewUrl(detail);

    return (
        <div style={{ ...detailCardStyle, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '160px', background: 'rgba(0,0,0,0.2)', overflow: 'hidden' }}>
            {!url ? (
                <div style={{ color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '2.5rem' }}>{detail.asset_type === 'video' ? 'video' : 'image'}</span>
                    <span style={{ fontSize: '0.82rem' }}>{t('No preview', '無預覽圖')}</span>
                </div>
            ) : detail.asset_type === 'video' ? (
                <video src={url} controls style={{ maxWidth: '100%', maxHeight: '280px', borderRadius: '8px' }} />
            ) : (
                <img src={url} style={{ maxWidth: '100%', maxHeight: '280px', objectFit: 'contain', borderRadius: '8px' }} alt="" />
            )}
        </div>
    );
};

const ScoreSummary = ({ detail, isMobile, language, t }) => (
    <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)', gap: '10px' }}>
        <div style={detailCardStyle}>
            <div style={labelStyle}>{t('Overall Score', '總評分')}</div>
            <div style={{ color: 'var(--text-primary)', fontWeight: 700, fontSize: '1.5rem' }}>{detail.overall_score ?? '--'}</div>
        </div>
        <div style={detailCardStyle}>
            <div style={labelStyle}>{getPredictedBandLabel(detail.objective_group, language)}</div>
            <div style={{ fontWeight: 700, fontSize: '1.1rem', color: roasBandColor[detail.roas_prediction?.band] || 'var(--text-secondary)' }}>
                {detail.roas_prediction?.band ? detail.roas_prediction.band.toUpperCase() : '--'}
            </div>
        </div>
        <div style={detailCardStyle}>
            <div style={labelStyle}>{t('Model', '模型版本')}</div>
            <div style={{ color: 'var(--text-primary)', fontWeight: 700, fontSize: '0.85rem' }}>{detail.model_version || '--'}</div>
        </div>
    </div>
);

const ScoringEngineCard = ({ detail, t }) => {
    if (!detail.lineage) return null;

    return (
        <div style={detailCardStyle}>
            <div style={labelStyle}>{t('Scoring Engine', '評估核心')}</div>
            <div style={{ color: detail.lineage.scoring_mode === 'ai' ? 'var(--accent-primary)' : 'var(--text-secondary)', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span>{detail.lineage.scoring_mode === 'ai' ? 'AI' : 'Rule'}</span>
                <span style={{ fontSize: '0.88rem' }}>
                    {detail.lineage.scoring_mode === 'ai'
                        ? `OpenRouter (${detail.lineage.provider_model || '--'})`
                        : t('Heuristic Rule Engine', '啟發式規則引擎')
                    }
                </span>
            </div>
            {detail.lineage.fallback_reason && (
                <div style={{ color: '#ef4444', fontSize: '0.8rem', marginTop: '6px' }}>
                    {detail.lineage.fallback_reason}
                </div>
            )}
        </div>
    );
};

const ObservationCard = ({ detail, language, t }) => {
    if (!detail.observation) {
        return (
            <div style={{ ...detailCardStyle, border: '1px solid rgba(245,158,11,0.2)', background: 'rgba(245,158,11,0.03)' }}>
                <div style={{ color: '#f59e0b', fontWeight: 600, marginBottom: '6px' }}>{t('Awaiting Match', '等待實際成效匹配')}</div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', lineHeight: 1.6 }}>
                    {t(
                        'Import actual ad data via Analytics -> Batch Import to enable comparison.',
                        '透過「成效分析」→ 批次匯入後，系統會自動關聯實際成效，即可在此查看預測準確度。'
                    )}
                </div>
            </div>
        );
    }

    return (
        <div style={{ ...detailCardStyle, border: '1px solid rgba(16,185,129,0.3)', background: 'rgba(16,185,129,0.03)' }}>
            <div style={{ fontWeight: 700, color: '#10b981', marginBottom: '10px' }}>{t('Actual Performance Match', '實際成效對照')}</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', marginBottom: '10px' }}>
                {[
                    [t('Predicted', '預測'), detail.observation.prediction_band],
                    [t('Actual', '實際'), detail.observation.observed_band],
                    [t('Error', '誤差'), detail.observation.error],
                ].map(([label, val]) => (
                    <div key={label} style={innerCardStyle}>
                        <div style={labelStyle}>{label}</div>
                        <div style={{ fontWeight: 700, color: typeof val === 'string' ? (roasBandColor[val] || 'var(--text-primary)') : (val === 0 ? '#10b981' : val <= 1 ? '#f59e0b' : '#ef4444') }}>
                            {typeof val === 'string' ? val.toUpperCase() : val ?? '--'}
                        </div>
                    </div>
                ))}
            </div>
            {detail.observation.ad_name && (
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '4px' }}>
                    {t('Ad: ', '廣告：')}<span style={{ color: 'var(--text-primary)' }}>{detail.observation.ad_name}</span>
                </div>
            )}
            {detail.observation.observation_window_kind && (
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '8px' }}>
                    {t('Window: ', '窗口：')}{detail.observation.observation_window_kind}
                    {detail.observation.observation_window_start && ` (${detail.observation.observation_window_start} -> ${detail.observation.observation_window_end})`}
                </div>
            )}
            {detail.observation.performance_snapshot && Object.keys(detail.observation.performance_snapshot).length > 0 && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(100px, 1fr))', gap: '6px' }}>
                    {Object.entries(detail.observation.performance_snapshot)
                        .filter(([, v]) => v !== null && v !== undefined)
                        .slice(0, 8)
                        .map(([key, value]) => (
                            <div key={key} style={innerCardStyle}>
                                <div style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', marginBottom: '2px' }}>{getPerfMetricLabel(key, language)}</div>
                                <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.85rem' }}>
                                    {formatPerfValue(key, value)}
                                </div>
                            </div>
                        ))}
                </div>
            )}
        </div>
    );
};

const SummaryCard = ({ detail, t }) => (
    <div style={detailCardStyle}>
        <div style={labelStyle}>{t('AI Summary', 'AI 評分摘要')}</div>
        <div style={{ color: 'var(--text-primary)', lineHeight: 1.6 }}>
            {detail.explanations?.summary || t('No summary available.', '尚無評分摘要。')}
        </div>
    </div>
);

const DiagnosticBreakdown = ({ detail, language, t }) => {
    if (!detail.diagnostic_breakdown || Object.keys(detail.diagnostic_breakdown).length === 0) return null;

    return (
        <div style={detailCardStyle}>
            <div style={labelStyle}>{t('Diagnostic Breakdown', '診斷細項')}</div>
            <div style={{ display: 'grid', gap: '8px', marginTop: '8px' }}>
                {Object.entries(detail.diagnostic_breakdown).map(([key, value]) => (
                    <div key={key} style={{ display: 'flex', gap: '10px' }}>
                        <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', minWidth: '110px', flexShrink: 0 }}>{getDiagnosticLabel(key, language)}</span>
                        <span style={{ color: 'var(--text-primary)', fontSize: '0.82rem', lineHeight: 1.5 }}>{value}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};

const DriverCards = ({ detail, isMobile, t }) => (
    <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(2, 1fr)', gap: '10px' }}>
        <div style={detailCardStyle}>
            <div style={labelStyle}>{t('Positive Drivers', '正向因素')}</div>
            <ul style={listStyle}>
                {(detail.top_positive_drivers || []).length > 0
                    ? detail.top_positive_drivers.map((d) => <li key={d}>{d}</li>)
                    : <li>--</li>}
            </ul>
        </div>
        <div style={detailCardStyle}>
            <div style={labelStyle}>{t('Risk Drivers', '風險因素')}</div>
            <ul style={listStyle}>
                {(detail.top_negative_drivers || []).length > 0
                    ? detail.top_negative_drivers.map((d) => <li key={d}>{d}</li>)
                    : <li>--</li>}
            </ul>
        </div>
    </div>
);

const AdCopyContext = ({ detail, t }) => {
    if (!detail.request_context || !Object.values(detail.request_context).some(Boolean)) return null;

    return (
        <div style={detailCardStyle}>
            <div style={labelStyle}>{t('Ad Copy Context', '廣告文案')}</div>
            <div style={{ display: 'grid', gap: '6px', marginTop: '8px' }}>
                {[['headline', t('Headline', '標題')], ['primary_text', t('Primary Text', '主要文字')], ['cta', 'CTA']].map(([key, label]) =>
                    detail.request_context[key] ? (
                        <div key={key} style={{ display: 'flex', gap: '10px' }}>
                            <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', minWidth: '70px', flexShrink: 0 }}>{label}</span>
                            <span style={{ color: 'var(--text-primary)', fontSize: '0.85rem' }}>{detail.request_context[key]}</span>
                        </div>
                    ) : null
                )}
            </div>
        </div>
    );
};

export default ReviewQueueDetail;
