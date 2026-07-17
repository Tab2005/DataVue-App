import { Link } from 'react-router-dom';

import { getDiagnosticLabel } from '../../../utils/metaAndromedaLabels';
import { Badge, DriverList, ScoreGauge } from './scoreLabComponents';
import {
    btnSecStyle,
    cardStyle,
    labelSt,
    panelStyle,
    ROAS_COLOR,
    statusLabel,
    TERMINAL,
    titleSt,
} from './scoreLabShared';

const ScoreLabResult = ({ lab, lang, t }) => (
    <section style={panelStyle}>
        <h2 style={titleSt}>{t('Score Result', '評分結果')}</h2>

        {!lab.scoreResult ? (
            <div style={{ color: 'var(--text-secondary)', lineHeight: 1.8 }}>
                {t('Upload an asset and submit to see the scoring result here.', '上傳素材並送出評分後，結果會顯示在此。')}
            </div>
        ) : (
            <div className="sl-scroll" style={{ display: 'grid', gap: '12px', maxHeight: 'calc(100vh - 280px)', overflowY: 'auto', paddingRight: '4px' }}>
                <ScoreSummary scoreResult={lab.scoreResult} polling={lab.polling} t={t} />
                {lab.scoreResult.status === 'completed' && <ReviewQueueLink t={t} />}
                <SummaryCard scoreResult={lab.scoreResult} t={t} />
                <RiskTags scoreResult={lab.scoreResult} t={t} />
                <DriverCards scoreResult={lab.scoreResult} t={t} />
                <DiagnosticBreakdown lang={lang} scoreResult={lab.scoreResult} t={t} />
                <button type="button" onClick={lab.resetForm} style={{ ...btnSecStyle, fontSize: '0.82rem' }}>
                    {t('Submit another asset', '評分另一個素材')}
                </button>
            </div>
        )}
    </section>
);

const ScoreSummary = ({ scoreResult, polling, t }) => (
    <div style={{ ...cardStyle, display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
        <ScoreGauge score={scoreResult.overall_score} />
        <div style={{ flex: 1, minWidth: '120px' }}>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '8px' }}>
                {scoreResult.roas_band && (
                    <Badge color={ROAS_COLOR[scoreResult.roas_band]}>
                        ROAS {scoreResult.roas_band.toUpperCase()}
                    </Badge>
                )}
                <Badge color={TERMINAL.has(scoreResult.status)
                    ? (scoreResult.status === 'completed' ? '#10b981' : '#ef4444')
                    : '#f59e0b'}>
                    {statusLabel(scoreResult.status, t)}
                </Badge>
                {polling && <span style={{ color: '#f59e0b', fontSize: '0.75rem' }}>{t('Scoring...', '評分中...')}</span>}
            </div>
            {scoreResult.lineage && (
                <div style={{ color: scoreResult.lineage.scoring_mode === 'ai' ? 'var(--accent-primary)' : 'var(--text-secondary)', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <span>{scoreResult.lineage.scoring_mode === 'ai' ? 'AI' : 'Rule'}</span>
                    <span>
                        {scoreResult.lineage.scoring_mode === 'ai'
                            ? `OpenRouter - ${scoreResult.lineage.provider_model || '--'}`
                            : t('Heuristic Rule Engine', '啟發式規則引擎')}
                    </span>
                </div>
            )}
            {scoreResult.lineage?.fallback_reason && (
                <div style={{ color: '#ef4444', fontSize: '0.75rem', marginTop: '4px' }}>
                    {scoreResult.lineage.fallback_reason}
                </div>
            )}
        </div>
    </div>
);

const ReviewQueueLink = ({ t }) => (
    <Link
        to="/meta-andromeda/review-queue"
        style={{
            display: 'block',
            textAlign: 'center',
            padding: '8px',
            borderRadius: '10px',
            border: '1px solid var(--accent-primary)',
            color: 'var(--accent-primary)',
            fontWeight: 600,
            fontSize: '0.85rem',
            textDecoration: 'none',
            background: 'rgba(59,130,246,0.06)',
        }}
    >
        {t('View in Evaluation Records', '前往評估紀錄查看')}
    </Link>
);

const SummaryCard = ({ scoreResult, t }) => (
    <div style={cardStyle}>
        <div style={labelSt}>{t('AI Summary', 'AI 評分摘要')}</div>
        <div style={{ color: 'var(--text-primary)', lineHeight: 1.7 }}>
            {scoreResult.explanations?.summary || scoreResult.error_message || '--'}
        </div>
    </div>
);

const RiskTags = ({ scoreResult, t }) => {
    if (!scoreResult.risk_tags?.length) return null;

    return (
        <div style={cardStyle}>
            <div style={labelSt}>{t('Risk Tags', '風險標籤')}</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '8px' }}>
                {scoreResult.risk_tags.map(tag => (
                    <Badge key={tag} color="#ef4444">{tag}</Badge>
                ))}
            </div>
        </div>
    );
};

const DriverCards = ({ scoreResult, t }) => (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
        <DriverList
            items={scoreResult.top_positive_drivers}
            color="#10b981"
            labelKey={t('Positive Drivers', '正向因素')}
        />
        <DriverList
            items={scoreResult.top_negative_drivers}
            color="#ef4444"
            labelKey={t('Risk Drivers', '風險因素')}
        />
    </div>
);

const DiagnosticBreakdown = ({ lang, scoreResult, t }) => {
    if (!scoreResult.diagnostic_breakdown || Object.keys(scoreResult.diagnostic_breakdown).length === 0) return null;

    return (
        <div style={cardStyle}>
            <div style={labelSt}>{t('Diagnostic Breakdown', '診斷細項')}</div>
            <div style={{ display: 'grid', gap: '7px', marginTop: '8px' }}>
                {Object.entries(scoreResult.diagnostic_breakdown).map(([key, value]) => (
                    <div key={key} style={{ display: 'flex', gap: '10px' }}>
                        <span style={{ color: 'var(--text-secondary)', fontSize: '0.78rem', minWidth: '100px', flexShrink: 0 }}>{getDiagnosticLabel(key, lang)}</span>
                        <span style={{ color: 'var(--text-primary)', fontSize: '0.82rem' }}>{value}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default ScoreLabResult;
