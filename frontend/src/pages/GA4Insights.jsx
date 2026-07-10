import React, { useEffect, useRef, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { FiCpu, FiRefreshCcw } from 'react-icons/fi';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    ReferenceArea,
    ReferenceLine,
} from 'recharts';

import { ga4Service } from '../services/ga4Service';
import { ga4InsightsService } from '../services/ga4InsightsService';
import { aiService } from '../services/aiService';
import { lineService } from '../services/lineService';

// ── Chart token layer（沿用 ContributionAnalysis.jsx 已驗證通過 dataviz
//    六項檢查的同一組categorical色票，維持全站視覺一致；docs/22 第 2 波） ──
const VIZ_TOKENS = `
.ga4-insights-chart-root {
  --viz-surface:        #18191a;
  --viz-grid:           rgba(255, 255, 255, 0.06);
  --viz-axis:           rgba(255, 255, 255, 0.18);
  --viz-text:           #b0b3b8;
  --viz-text-strong:    #e4e6eb;
  --viz-tooltip-bg:     #242526;
  --viz-tooltip-border: rgba(255, 255, 255, 0.10);
  --viz-series-1:       #3987e5;
  --viz-series-2:       #199e70;
  --viz-series-3:       #c98500;
  --viz-series-muted:   #6b7280;
  --viz-direct-label:   #e4e6eb;
}
@media (prefers-color-scheme: light) {
  .ga4-insights-chart-root {
    --viz-surface:        #fcfcfb;
    --viz-grid:           rgba(11, 11, 11, 0.07);
    --viz-axis:           rgba(11, 11, 11, 0.22);
    --viz-text:           #52514e;
    --viz-text-strong:    #0b0b0b;
    --viz-tooltip-bg:     #ffffff;
    --viz-tooltip-border: rgba(11, 11, 11, 0.12);
    --viz-series-1:       #2a78d6;
    --viz-series-2:       #1baf7a;
    --viz-series-3:       #eda100;
    --viz-series-muted:   #6b7280;
    --viz-direct-label:   #0b0b0b;
  }
}
.ga4-insights-chart-root text { font-variant-numeric: tabular-nums; }

.report-ai-content { font-size: 0.9rem; line-height: 1.75; color: var(--text-primary); }
.report-ai-content h2 {
  font-size: 1.05rem; font-weight: 700; color: #06b6d4;
  margin: 1.1rem 0 0.55rem; border-left: 3px solid #06b6d4; padding-left: 10px;
}
.report-ai-content h2:first-child { margin-top: 0; }
.report-ai-content p { margin: 0.5rem 0; color: var(--text-secondary); }
.report-ai-content ul { margin: 0.5rem 0 0.7rem; padding-left: 1.4rem; list-style: none; }
.report-ai-content li { position: relative; margin: 0.35rem 0; line-height: 1.7; color: var(--text-primary); }
.report-ai-content li::before { content: '▸'; color: #06b6d4; position: absolute; left: -1rem; font-weight: bold; }
.report-ai-content ol { margin: 0.5rem 0 0.7rem; padding-left: 1.6rem; color: var(--text-primary); }
.report-ai-content ol li::before { content: ''; }
.report-ai-content table { width: 100%; border-collapse: collapse; margin: 0.6rem 0 0.8rem; font-size: 0.82rem; }
.report-ai-content th {
  background: rgba(6, 182, 212, 0.1); color: #06b6d4; padding: 7px 10px;
  text-align: left; border-bottom: 2px solid #06b6d4; font-weight: 600;
}
.report-ai-content td { padding: 6px 10px; border-bottom: 1px solid rgba(255, 255, 255, 0.08); color: var(--text-primary); }
.report-ai-content tr:last-child td { border-bottom: none; }
.report-ai-content strong { color: #06b6d4; font-weight: 600; }
`;

const baseCardStyle = {
    background: 'var(--bg-secondary)',
    border: '1px solid var(--glass-border)',
    borderRadius: '16px',
    padding: '20px',
};

const inputStyle = {
    width: '100%',
    padding: '10px 12px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255, 255, 255, 0.04)',
    color: 'var(--text-primary)',
};

const buttonStyle = {
    padding: '10px 14px',
    borderRadius: '10px',
    border: '1px solid rgba(59, 130, 246, 0.35)',
    background: 'rgba(59, 130, 246, 0.16)',
    color: '#bfdbfe',
    cursor: 'pointer',
};

const secondaryButtonStyle = {
    ...buttonStyle,
    border: '1px solid var(--glass-border)',
    background: 'transparent',
    color: 'var(--text-secondary)',
};

const tabButtonStyle = (active) => ({
    padding: '9px 16px',
    borderRadius: '999px',
    border: active ? '1px solid rgba(59, 130, 246, 0.5)' : '1px solid var(--glass-border)',
    background: active ? 'rgba(59, 130, 246, 0.18)' : 'transparent',
    color: active ? '#bfdbfe' : 'var(--text-secondary)',
    fontWeight: active ? 700 : 500,
    cursor: 'pointer',
    whiteSpace: 'nowrap',
});

const dayButtonStyle = (active) => ({
    padding: '6px 12px',
    borderRadius: '8px',
    border: active ? '1px solid rgba(59, 130, 246, 0.5)' : '1px solid var(--glass-border)',
    background: active ? 'rgba(59, 130, 246, 0.16)' : 'transparent',
    color: active ? '#bfdbfe' : 'var(--text-secondary)',
    cursor: 'pointer',
    fontSize: '0.82rem',
});

const badgeStyle = (kind) => {
    const palette = {
        assist: { bg: 'rgba(57, 135, 229, 0.16)', fg: '#93c5fd', border: 'rgba(57, 135, 229, 0.35)' },
        close: { bg: 'rgba(25, 158, 112, 0.16)', fg: '#86efac', border: 'rgba(25, 158, 112, 0.35)' },
        balanced: { bg: 'rgba(107, 114, 128, 0.16)', fg: '#d1d5db', border: 'rgba(107, 114, 128, 0.35)' },
        insufficient_data: { bg: 'rgba(107, 114, 128, 0.1)', fg: '#9ca3af', border: 'rgba(107, 114, 128, 0.25)' },
        flagged: { bg: 'rgba(248, 113, 113, 0.16)', fg: '#fca5a5', border: 'rgba(248, 113, 113, 0.35)' },
        potential: { bg: 'rgba(201, 133, 0, 0.18)', fg: '#fbbf24', border: 'rgba(201, 133, 0, 0.4)' },
        ahead: { bg: 'rgba(25, 158, 112, 0.16)', fg: '#86efac', border: 'rgba(25, 158, 112, 0.35)' },
        on_track: { bg: 'rgba(57, 135, 229, 0.16)', fg: '#93c5fd', border: 'rgba(57, 135, 229, 0.35)' },
        behind: { bg: 'rgba(248, 113, 113, 0.16)', fg: '#fca5a5', border: 'rgba(248, 113, 113, 0.35)' },
    }[kind] || { bg: 'rgba(107, 114, 128, 0.1)', fg: '#9ca3af', border: 'rgba(107, 114, 128, 0.25)' };
    return {
        display: 'inline-block',
        padding: '2px 9px',
        borderRadius: '999px',
        fontSize: '0.74rem',
        fontWeight: 700,
        background: palette.bg,
        color: palette.fg,
        border: `1px solid ${palette.border}`,
    };
};

const emptyState = (text) => (
    <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{text}</div>
);

const tr = (language, en, zh) => (language === 'en' ? en : zh);

const fmtNumber = (value, digits = 0) => {
    if (value == null || Number.isNaN(value)) return '--';
    return Number(value).toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: 0 });
};

const fmtPct = (value, digits = 1) => {
    if (value == null || Number.isNaN(value)) return '--';
    return `${(value * 100).toFixed(digits)}%`;
};

const CHANNEL_TAG_LABELS = {
    assist: { en: 'Assist', zh: '助攻型' },
    close: { en: 'Close', zh: '主攻型' },
    balanced: { en: 'Balanced', zh: '均衡' },
    insufficient_data: { en: 'Insufficient data', zh: '資料不足' },
};

const METRIC_LABELS = {
    sessions: { en: 'Sessions', zh: '工作階段' },
    conversions: { en: 'Conversions', zh: '轉換' },
    purchaseRevenue: { en: 'Revenue', zh: '營收' },
};

const KPI_STATUS_LABELS = {
    ahead: { en: 'Ahead of pace', zh: '超前進度' },
    on_track: { en: 'On track', zh: '符合進度' },
    behind: { en: 'Behind pace', zh: '落後進度' },
    no_target: { en: 'No target set', zh: '未設定目標' },
    data_unavailable: { en: 'Data unavailable', zh: '資料暫缺' },
};

const KPI_METRIC_OPTIONS = [
    { value: 'conversions', en: 'Conversions', zh: '轉換' },
    { value: 'sessions', en: 'Sessions', zh: '工作階段' },
    { value: 'purchase_revenue', en: 'Revenue', zh: '營收' },
];

const currentMonthKey = () => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
};

const currentQuarterKey = () => {
    const now = new Date();
    return `${now.getFullYear()}-Q${Math.floor(now.getMonth() / 3) + 1}`;
};

const DASHBOARD_METRICS = ['sessions', 'conversions', 'purchaseRevenue'];

// ── AI 白話解讀共用卡（同週報 / 貢獻分析頁的模式，docs/22 任務 2.4） ──
const AIInsightNote = ({ language, snapshot, kind, buildPayload, contextLabel }) => {
    const t = (en, zh) => tr(language, en, zh);
    const existing = snapshot?.ai_summary || '';
    const [aiContent, setAiContent] = useState(existing);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [aiError, setAiError] = useState(null);
    const aiContentRef = useRef(existing);

    useEffect(() => {
        setAiContent(existing);
        aiContentRef.current = existing;
        setAiError(null);
    }, [snapshot?.snapshot_id, existing]);

    if (!snapshot) return null;

    const handleGenerate = async () => {
        if (isAnalyzing) return;
        setIsAnalyzing(true);
        setAiError(null);
        setAiContent('');
        aiContentRef.current = '';
        const payload = { kind, ...buildPayload() };
        try {
            await aiService.analyzeDataStream(
                payload,
                contextLabel,
                'ga4_insights',
                null,
                (chunk) => {
                    aiContentRef.current += chunk;
                    setAiContent((prev) => prev + chunk);
                },
                null,
                null,
                'daily',
                'ga4'
            );
        } catch (err) {
            setAiError(err?.message || t('AI analysis failed. Check AI key in settings.', 'AI 解讀失敗，請至設定頁確認 AI 金鑰。'));
            setIsAnalyzing(false);
            return;
        }
        setIsAnalyzing(false);
        setIsSaving(true);
        try {
            await ga4InsightsService.saveAiSummary(snapshot.snapshot_id, aiContentRef.current);
        } catch (err) {
            setAiError(err?.message || t('AI summary generated but failed to save. Retry to persist.', 'AI 解讀已生成但儲存失敗，請重試以持久化。'));
        } finally {
            setIsSaving(false);
        }
    };

    const hasContent = aiContent && aiContent.length > 0;
    const buttonLabel = hasContent ? t('Regenerate', '重新解讀') : t('Generate Insights', '開始 AI 解讀');

    return (
        <div style={{ ...baseCardStyle, marginTop: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px', flexWrap: 'wrap', gap: '8px' }}>
                <div>
                    <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{t('AI Plain-Language Insights', 'AI 白話解讀')}</div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                        {t('Translates the numbers above into a quick read.', '把上方數字翻成白話文，快速掌握重點。')}
                    </div>
                </div>
                <button
                    type="button"
                    onClick={handleGenerate}
                    disabled={isAnalyzing || isSaving}
                    style={{ ...secondaryButtonStyle, display: 'flex', alignItems: 'center', gap: '6px', opacity: isAnalyzing || isSaving ? 0.5 : 1 }}
                >
                    {isAnalyzing || isSaving ? <FiRefreshCcw className="spin" /> : <FiCpu />}
                    {isAnalyzing ? t('Analyzing…', '解讀中…') : isSaving ? t('Saving…', '儲存中…') : buttonLabel}
                </button>
            </div>

            {aiError && (
                <div style={{ color: '#fca5a5', fontSize: '0.85rem', marginBottom: '10px' }}>{aiError}</div>
            )}

            <div
                style={{
                    background: 'rgba(59, 130, 246, 0.05)',
                    border: '1px solid rgba(59, 130, 246, 0.2)',
                    borderRadius: '12px',
                    padding: '16px 18px',
                    minHeight: '80px',
                    color: 'var(--text-primary)',
                    lineHeight: 1.7,
                }}
            >
                {hasContent ? (
                    <div className="report-ai-content">
                        <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
                            {aiContent}
                        </ReactMarkdown>
                    </div>
                ) : (
                    <div style={{ color: 'var(--text-tertiary)', textAlign: 'center', padding: '16px', fontSize: '0.85rem' }}>
                        {isAnalyzing
                            ? t('AI is analyzing your data…', 'AI 正在分析您的數據…')
                            : t('No AI summary yet. Click "Generate Insights".', '尚無 AI 解讀，點選「開始 AI 解讀」。')}
                    </div>
                )}
            </div>

            <div style={{ marginTop: '10px', fontSize: '0.74rem', color: 'var(--text-tertiary)', lineHeight: 1.5 }}>
                {t('Disclaimer: AI insights are for reference only. The numbers above are the source of truth.', '免責聲明：AI 解讀僅供參考，數字以上方圖表為準。')}
            </div>
        </div>
    );
};

// ── 當日總覽：單一指標的小圖（實際柱狀 + 灰帶預期區間 + 中位數虛線） ──
const IntradayMetricCard = ({ language, metricKey, hourlyTotals, baseline, cumulativeValue, isAnomaly }) => {
    const t = (en, zh) => tr(language, en, zh);
    const label = METRIC_LABELS[metricKey] ? tr(language, METRIC_LABELS[metricKey].en, METRIC_LABELS[metricKey].zh) : metricKey;
    const data = (hourlyTotals || []).map((row) => ({ hour: row.hour, value: row[metricKey] || 0 }));
    const low = baseline?.low;
    const high = baseline?.high;
    const median = baseline?.median;

    return (
        <div className="ga4-insights-chart-root" style={baseCardStyle}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '4px' }}>
                <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{label}</div>
                {isAnomaly && (
                    <span style={badgeStyle('flagged')}>{t('Unusual', '異常')}</span>
                )}
            </div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: isAnomaly ? '#f87171' : 'var(--text-primary)' }}>
                {fmtNumber(cumulativeValue, metricKey === 'purchaseRevenue' ? 0 : 0)}
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '8px', minHeight: '1.1em' }}>
                {median != null
                    ? `${t('Usual range', '平常區間')} ${fmtNumber(low)} ~ ${fmtNumber(high)}`
                    : t('Not enough history yet', '歷史樣本不足，暫無基線')}
            </div>
            <ResponsiveContainer width="100%" height={140}>
                <BarChart data={data} margin={{ top: 4, right: 4, bottom: 4, left: 4 }}>
                    <CartesianGrid stroke="var(--viz-grid)" vertical={false} />
                    <XAxis dataKey="hour" tick={{ fill: 'var(--viz-text)', fontSize: 11 }} axisLine={{ stroke: 'var(--viz-axis)' }} tickLine={false} />
                    <YAxis tick={{ fill: 'var(--viz-text)', fontSize: 11 }} axisLine={false} tickLine={false} width={36} />
                    <Tooltip contentStyle={{ background: 'var(--viz-tooltip-bg)', border: '1px solid var(--viz-tooltip-border)', borderRadius: 8, fontSize: '0.8rem' }} labelStyle={{ color: 'var(--viz-text-strong)' }} />
                    {low != null && high != null && (
                        <ReferenceArea y1={Math.max(low, 0)} y2={high} fill="var(--viz-series-muted)" fillOpacity={0.18} strokeOpacity={0} />
                    )}
                    {median != null && <ReferenceLine y={median} stroke="var(--viz-series-muted)" strokeDasharray="4 4" />}
                    <Bar dataKey="value" radius={[4, 4, 0, 0]} fill={isAnomaly ? '#f87171' : 'var(--viz-series-1)'} />
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
};

// ── KPI 目標：達成率 vs 時間進度的 pacing 卡（docs/22 第 3 波） ──
const KpiPacingCard = ({ language, target, onDelete }) => {
    const t = (en, zh) => tr(language, en, zh);
    const metricLabel = METRIC_LABELS[target.metric_key]
        ? tr(language, METRIC_LABELS[target.metric_key].en, METRIC_LABELS[target.metric_key].zh)
        : KPI_METRIC_OPTIONS.find((m) => m.value === target.metric_key)
            ? tr(language, KPI_METRIC_OPTIONS.find((m) => m.value === target.metric_key).en, KPI_METRIC_OPTIONS.find((m) => m.value === target.metric_key).zh)
            : target.metric_key;
    const statusLabel = KPI_STATUS_LABELS[target.status]
        ? tr(language, KPI_STATUS_LABELS[target.status].en, KPI_STATUS_LABELS[target.status].zh)
        : target.status;
    const timeProgressPct = Math.min(100, Math.max(0, (target.time_progress || 0) * 100));
    const achievementPct = target.achievement_rate != null ? Math.min(140, Math.max(0, target.achievement_rate * 100)) : 0;

    return (
        <div style={baseCardStyle}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px', marginBottom: '8px' }}>
                <div>
                    <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{metricLabel}</div>
                    <div style={{ color: 'var(--text-tertiary)', fontSize: '0.78rem' }}>
                        {target.period_type === 'month' ? t('Month', '月') : t('Quarter', '季')} · {target.period_key}
                    </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={badgeStyle(target.status)}>{statusLabel}</span>
                    <button type="button" onClick={() => onDelete(target.id)} style={{ ...secondaryButtonStyle, padding: '4px 10px', fontSize: '0.78rem' }}>
                        {t('Delete', '刪除')}
                    </button>
                </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                <span>{t('Actual', '目前累計')}: <strong style={{ color: 'var(--text-primary)' }}>{fmtNumber(target.actual_value)}</strong></span>
                <span>{t('Target', '目標')}: <strong style={{ color: 'var(--text-primary)' }}>{fmtNumber(target.target_value)}</strong></span>
            </div>

            <div style={{ position: 'relative', height: '10px', borderRadius: '999px', background: 'rgba(107, 114, 128, 0.2)', marginBottom: '6px', overflow: 'hidden' }}>
                <div
                    style={{
                        position: 'absolute',
                        left: 0,
                        top: 0,
                        bottom: 0,
                        width: `${Math.min(100, achievementPct)}%`,
                        background: target.status === 'behind' ? '#f87171' : target.status === 'ahead' ? '#34d399' : 'var(--accent-primary, #3987e5)',
                        borderRadius: '999px',
                    }}
                />
                <div
                    title={t('Time elapsed', '時間進度')}
                    style={{
                        position: 'absolute',
                        left: `${timeProgressPct}%`,
                        top: '-2px',
                        bottom: '-2px',
                        width: '2px',
                        background: 'var(--text-primary)',
                        opacity: 0.6,
                    }}
                />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.74rem', color: 'var(--text-tertiary)' }}>
                <span>{t('Achievement', '達成率')} {fmtPct(target.achievement_rate)}</span>
                <span>{t('Time elapsed', '時間進度')} {fmtPct(target.time_progress)}</span>
            </div>
            {target.projected_final_value != null && (
                <div style={{ marginTop: '8px', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                    {t('At this pace, projected to reach', '照這個速度，預估期末達到')} <strong style={{ color: 'var(--text-primary)' }}>{fmtNumber(target.projected_final_value)}</strong>
                </div>
            )}
        </div>
    );
};

const GA4Insights = () => {
    const { language, isMobile } = useOutletContext();
    const t = (en, zh) => tr(language, en, zh);

    const [properties, setProperties] = useState([]);
    const [propertyId, setPropertyId] = useState('');
    const [activeTab, setActiveTab] = useState('overview');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // 第 1 波：告警規則 / 事件歷史
    const [rules, setRules] = useState([]);
    const [events, setEvents] = useState([]);
    const [lineStatus, setLineStatus] = useState(null);
    const [saving, setSaving] = useState(false);
    const [form, setForm] = useState({
        metric_key: 'conversions',
        sensitivity: 'medium',
        check_frequency: 'hourly',
        is_enabled: true,
        notify_line: true,
        notify_email: false,
        cooldown_hours: 6,
    });
    const [editingRuleId, setEditingRuleId] = useState('');

    // 第 2 波：當日總覽
    const [dashboard, setDashboard] = useState(null);
    const [realtime, setRealtime] = useState(null);
    const [dashboardLoading, setDashboardLoading] = useState(false);
    const [dashboardError, setDashboardError] = useState('');
    const [refreshNotice, setRefreshNotice] = useState('');

    // 第 2 波：渠道對照
    const [channelsDays, setChannelsDays] = useState(7);
    const [channelsSnapshot, setChannelsSnapshot] = useState(null);
    const [channelsLoading, setChannelsLoading] = useState(false);
    const [channelsError, setChannelsError] = useState('');

    // 第 2 波：到達頁
    const [landingDays, setLandingDays] = useState(7);
    const [landingSnapshot, setLandingSnapshot] = useState(null);
    const [landingLoading, setLandingLoading] = useState(false);
    const [landingError, setLandingError] = useState('');

    // 第 2 波：商品
    const [itemsDays, setItemsDays] = useState(7);
    const [itemsSnapshot, setItemsSnapshot] = useState(null);
    const [itemsLoading, setItemsLoading] = useState(false);
    const [itemsError, setItemsError] = useState('');

    // 第 3 波：KPI 目標追蹤
    const [kpiTargets, setKpiTargets] = useState(null);
    const [kpiLoading, setKpiLoading] = useState(false);
    const [kpiError, setKpiError] = useState('');
    const [kpiSaving, setKpiSaving] = useState(false);
    const [kpiForm, setKpiForm] = useState({
        metric_key: 'conversions',
        period_type: 'month',
        period_key: currentMonthKey(),
        target_value: '',
    });

    const load = async (nextPropertyId) => {
        setLoading(true);
        setError('');
        try {
            const targetPropertyId = nextPropertyId || propertyId;
            const [rulesRes, eventsRes, lineRes] = await Promise.all([
                ga4InsightsService.listRules(targetPropertyId),
                ga4InsightsService.listEvents(targetPropertyId),
                lineService.getStatus(),
            ]);
            setRules(rulesRes.rules || []);
            setEvents(eventsRes.events || []);
            setLineStatus(lineRes);
        } catch (err) {
            setError(err.message || t('Failed to load GA4 insights.', '載入 GA4 洞察失敗。'));
        } finally {
            setLoading(false);
        }
    };

    const loadDashboard = async (pid) => {
        if (!pid) return;
        setDashboardLoading(true);
        setDashboardError('');
        try {
            const [dash, rt] = await Promise.all([
                ga4InsightsService.getDashboard(pid),
                ga4InsightsService.getRealtime(pid).catch(() => null),
            ]);
            setDashboard(dash);
            setRealtime(rt);
        } catch (err) {
            setDashboardError(err.message || t('Failed to load dashboard.', '載入儀表板失敗。'));
        } finally {
            setDashboardLoading(false);
        }
    };

    const handleRefreshDashboard = async () => {
        if (!propertyId) return;
        setDashboardLoading(true);
        setDashboardError('');
        setRefreshNotice('');
        try {
            const res = await ga4InsightsService.refreshDashboard(propertyId);
            setDashboard(res);
            if (!res.refreshed) {
                setRefreshNotice(t('Still fresh — please try again in a few minutes.', '資料仍新鮮，請稍後幾分鐘再試手動刷新。'));
            }
            const rt = await ga4InsightsService.getRealtime(propertyId).catch(() => null);
            setRealtime(rt);
        } catch (err) {
            setDashboardError(err.message || t('Failed to refresh dashboard.', '刷新儀表板失敗。'));
        } finally {
            setDashboardLoading(false);
        }
    };

    const loadChannels = async (pid, days) => {
        if (!pid) return;
        setChannelsLoading(true);
        setChannelsError('');
        try {
            setChannelsSnapshot(await ga4InsightsService.getChannels(pid, days));
        } catch (err) {
            setChannelsError(err.message || t('Failed to load channel comparison.', '載入渠道對照失敗。'));
        } finally {
            setChannelsLoading(false);
        }
    };

    const loadLandingPages = async (pid, days) => {
        if (!pid) return;
        setLandingLoading(true);
        setLandingError('');
        try {
            setLandingSnapshot(await ga4InsightsService.getLandingPages(pid, days));
        } catch (err) {
            setLandingError(err.message || t('Failed to load landing pages.', '載入到達頁分析失敗。'));
        } finally {
            setLandingLoading(false);
        }
    };

    const loadItems = async (pid, days) => {
        if (!pid) return;
        setItemsLoading(true);
        setItemsError('');
        try {
            setItemsSnapshot(await ga4InsightsService.getItems(pid, days));
        } catch (err) {
            setItemsError(err.message || t('Failed to load item insights.', '載入商品分析失敗。'));
        } finally {
            setItemsLoading(false);
        }
    };

    const loadKpiTargets = async (pid) => {
        if (!pid) return;
        setKpiLoading(true);
        setKpiError('');
        try {
            const res = await ga4InsightsService.listKpiTargets(pid);
            setKpiTargets(res.targets || []);
        } catch (err) {
            setKpiError(err.message || t('Failed to load KPI targets.', '載入 KPI 目標失敗。'));
        } finally {
            setKpiLoading(false);
        }
    };

    const handleCreateKpiTarget = async (event) => {
        event.preventDefault();
        if (!propertyId || !kpiForm.target_value) return;
        setKpiSaving(true);
        setKpiError('');
        try {
            await ga4InsightsService.upsertKpiTarget({
                property_id: propertyId,
                metric_key: kpiForm.metric_key,
                period_type: kpiForm.period_type,
                period_key: kpiForm.period_key,
                target_value: Number(kpiForm.target_value),
            });
            setKpiForm((prev) => ({ ...prev, target_value: '' }));
            await loadKpiTargets(propertyId);
        } catch (err) {
            setKpiError(err.message || t('Failed to save KPI target.', '儲存 KPI 目標失敗。'));
        } finally {
            setKpiSaving(false);
        }
    };

    const handleDeleteKpiTarget = async (targetId) => {
        if (!window.confirm(t('Delete this KPI target?', '要刪除此 KPI 目標嗎？'))) return;
        try {
            await ga4InsightsService.deleteKpiTarget(targetId);
            await loadKpiTargets(propertyId);
        } catch (err) {
            setKpiError(err.message || t('Failed to delete KPI target.', '刪除 KPI 目標失敗。'));
        }
    };

    useEffect(() => {
        let cancelled = false;
        const bootstrap = async () => {
            setLoading(true);
            try {
                const props = await ga4Service.getProperties();
                if (cancelled) return;
                setProperties(props);
                const initialPropertyId = props[0]?.property_id || '';
                setPropertyId(initialPropertyId);
                if (initialPropertyId) {
                    await load(initialPropertyId);
                } else {
                    const lineRes = await lineService.getStatus();
                    setLineStatus(lineRes);
                    setLoading(false);
                }
            } catch (err) {
                if (!cancelled) {
                    setError(err.message || t('Failed to load properties.', '載入 GA4 屬性失敗。'));
                    setLoading(false);
                }
            }
        };
        bootstrap();
        return () => {
            cancelled = true;
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // 分頁籤切換／屬性切換時，懶載入該分頁的資料（每個分頁只在首次進入時抓一次）
    useEffect(() => {
        if (!propertyId) return;
        if (activeTab === 'overview' && !dashboard) loadDashboard(propertyId);
        if (activeTab === 'channels' && !channelsSnapshot) loadChannels(propertyId, channelsDays);
        if (activeTab === 'landing' && !landingSnapshot) loadLandingPages(propertyId, landingDays);
        if (activeTab === 'items' && !itemsSnapshot) loadItems(propertyId, itemsDays);
        if (activeTab === 'kpi' && !kpiTargets) loadKpiTargets(propertyId);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeTab, propertyId]);

    const handlePropertyChange = async (event) => {
        const next = event.target.value;
        setPropertyId(next);
        setDashboard(null);
        setRealtime(null);
        setChannelsSnapshot(null);
        setLandingSnapshot(null);
        setItemsSnapshot(null);
        setKpiTargets(null);
        setRefreshNotice('');
        await load(next);
    };

    const resetForm = () => {
        setForm({
            metric_key: 'conversions',
            sensitivity: 'medium',
            check_frequency: 'hourly',
            is_enabled: true,
            notify_line: true,
            notify_email: false,
            cooldown_hours: 6,
        });
        setEditingRuleId('');
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        if (!propertyId) return;
        setSaving(true);
        setError('');
        try {
            const payload = { ...form, property_id: propertyId, cooldown_hours: Number(form.cooldown_hours) || 6 };
            if (editingRuleId) {
                await ga4InsightsService.updateRule(editingRuleId, payload);
            } else {
                await ga4InsightsService.createRule(payload);
            }
            resetForm();
            await load(propertyId);
        } catch (err) {
            setError(err.message || t('Failed to save rule.', '儲存規則失敗。'));
        } finally {
            setSaving(false);
        }
    };

    const startEdit = (rule) => {
        setEditingRuleId(rule.id);
        setForm({
            metric_key: rule.metric_key,
            sensitivity: rule.sensitivity,
            check_frequency: rule.check_frequency,
            is_enabled: rule.is_enabled,
            notify_line: rule.notify_line,
            notify_email: rule.notify_email,
            cooldown_hours: rule.cooldown_hours,
        });
    };

    const handleDelete = async (ruleId) => {
        if (!window.confirm(t('Delete this anomaly rule?', '要刪除此告警規則嗎？'))) return;
        try {
            await ga4InsightsService.deleteRule(ruleId);
            if (editingRuleId === ruleId) resetForm();
            await load(propertyId);
        } catch (err) {
            setError(err.message || t('Failed to delete rule.', '刪除規則失敗。'));
        }
    };

    const handleAck = async (eventId) => {
        try {
            await ga4InsightsService.acknowledgeEvent(eventId);
            await load(propertyId);
        } catch (err) {
            setError(err.message || t('Failed to acknowledge event.', '標記已讀失敗。'));
        }
    };

    const unackedEvents = events.filter((e) => !e.acknowledged_at);

    const tabs = [
        { key: 'overview', en: 'Today', zh: '當日總覽' },
        { key: 'channels', en: 'Channels', zh: '渠道對照' },
        { key: 'landing', en: 'Landing Pages', zh: '到達頁' },
        { key: 'items', en: 'Items', zh: '商品' },
        { key: 'kpi', en: 'KPI', zh: 'KPI 目標' },
        { key: 'alerts', en: 'Alerts', zh: '告警設定' },
    ];

    const DaySelector = ({ value, onChange }) => (
        <div style={{ display: 'flex', gap: '6px' }}>
            {[7, 14, 30].map((d) => (
                <button key={d} type="button" style={dayButtonStyle(value === d)} onClick={() => onChange(d)}>
                    {d}{t('d', '天')}
                </button>
            ))}
        </div>
    );

    return (
        <div style={{ padding: isMobile ? '16px' : '24px', display: 'grid', gap: '16px' }}>
            <style>{VIZ_TOKENS}</style>
            <header style={{ display: 'grid', gap: '6px' }}>
                <div style={{ color: 'var(--accent-primary)', fontWeight: 700 }}>
                    {t('GA4 Conversion Insights', 'GA4 轉換洞察')}
                </div>
                <h1 style={{ margin: 0, color: 'var(--text-primary)' }}>
                    {t('Same-day dashboard, anomaly alerts, and channel/page/item breakdowns', '當日儀表板、異常告警與渠道／頁面／商品拆解')}
                </h1>
            </header>

            {error && (
                <div style={{ ...baseCardStyle, borderColor: 'rgba(239, 68, 68, 0.3)', color: '#fca5a5' }}>
                    {error}
                </div>
            )}

            <section style={baseCardStyle}>
                <div style={{ display: 'grid', gap: '10px', gridTemplateColumns: isMobile ? '1fr' : '2fr auto' }}>
                    <select value={propertyId} onChange={handlePropertyChange} style={inputStyle}>
                        <option value="">{t('Select GA4 property', '選擇 GA4 屬性')}</option>
                        {properties.map((property) => (
                            <option key={property.property_id} value={property.property_id}>
                                {property.display_name} · {property.property_id}
                            </option>
                        ))}
                    </select>
                    <div style={{ ...inputStyle, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        {lineStatus?.is_linked ? t('LINE linked', 'LINE 已綁定') : t('LINE not linked', 'LINE 尚未綁定')}
                    </div>
                </div>
            </section>

            {unackedEvents.length > 0 && (
                <section style={{ ...baseCardStyle, borderColor: 'rgba(239, 68, 68, 0.3)' }}>
                    <div style={{ color: '#fca5a5', fontWeight: 700, marginBottom: '6px' }}>
                        {t(`${unackedEvents.length} unacknowledged alert(s)`, `${unackedEvents.length} 則未讀告警`)}
                    </div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                        {unackedEvents[0]?.message}
                        {unackedEvents.length > 1 && ` …`}
                    </div>
                    <button type="button" style={{ ...secondaryButtonStyle, marginTop: '10px' }} onClick={() => setActiveTab('alerts')}>
                        {t('Go to alert settings', '前往告警設定')}
                    </button>
                </section>
            )}

            <nav style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '2px' }}>
                {tabs.map((tab) => (
                    <button
                        key={tab.key}
                        type="button"
                        style={tabButtonStyle(activeTab === tab.key)}
                        onClick={() => setActiveTab(tab.key)}
                    >
                        {t(tab.en, tab.zh)}
                    </button>
                ))}
            </nav>

            {!propertyId && !loading && (
                <section style={baseCardStyle}>{emptyState(t('Connect a GA4 property to see insights.', '請先連接 GA4 屬性以查看洞察。'))}</section>
            )}

            {propertyId && activeTab === 'overview' && (
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
            )}

            {propertyId && activeTab === 'channels' && (
                <>
                    <section style={baseCardStyle}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
                            <div>
                                <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{t('Assist vs. close channels', '渠道助攻/主攻對照')}</div>
                                <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                                    {t(
                                        'First-touch vs. last-touch conversions by channel. For deeper incremental contribution, see the Contribution Analysis page.',
                                        '首次接觸 vs 最後接觸轉換的渠道對照。想看更深入的增量貢獻，請至貢獻分析頁。'
                                    )}
                                </div>
                            </div>
                            <DaySelector value={channelsDays} onChange={(d) => { setChannelsDays(d); loadChannels(propertyId, d); }} />
                        </div>
                        {channelsError && <div style={{ color: '#fca5a5', fontSize: '0.85rem', marginBottom: '10px' }}>{channelsError}</div>}
                        {channelsLoading && !channelsSnapshot ? (
                            emptyState(t('Loading channels…', '載入渠道資料中…'))
                        ) : channelsSnapshot?.payload?.channels?.length ? (
                            <>
                                <div className="ga4-insights-chart-root">
                                    <ResponsiveContainer width="100%" height={Math.max(220, channelsSnapshot.payload.channels.length * 40)}>
                                        <BarChart data={channelsSnapshot.payload.channels} layout="vertical" margin={{ top: 4, right: 16, bottom: 4, left: 8 }}>
                                            <CartesianGrid stroke="var(--viz-grid)" horizontal={false} />
                                            <XAxis type="number" tick={{ fill: 'var(--viz-text)', fontSize: 11 }} axisLine={{ stroke: 'var(--viz-axis)' }} tickLine={false} />
                                            <YAxis type="category" dataKey="channel" width={140} tick={{ fill: 'var(--viz-text)', fontSize: 11 }} axisLine={false} tickLine={false} />
                                            <Tooltip contentStyle={{ background: 'var(--viz-tooltip-bg)', border: '1px solid var(--viz-tooltip-border)', borderRadius: 8, fontSize: '0.8rem' }} />
                                            <Legend wrapperStyle={{ fontSize: '0.78rem', color: 'var(--viz-text)' }} />
                                            <Bar dataKey="assisting_conversions" name={t('Assisting (first-touch)', '開發（首次接觸）')} fill="var(--viz-series-1)" radius={[0, 4, 4, 0]} />
                                            <Bar dataKey="closing_conversions" name={t('Closing (last-touch)', '收單（最後接觸）')} fill="var(--viz-series-2)" radius={[0, 4, 4, 0]} />
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                                <div style={{ overflowX: 'auto', marginTop: '12px' }}>
                                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                                        <thead>
                                            <tr style={{ color: 'var(--text-secondary)', textAlign: 'left' }}>
                                                <th style={{ padding: '6px' }}>{t('Channel', '渠道')}</th>
                                                <th style={{ padding: '6px' }}>{t('Assisting', '開發')}</th>
                                                <th style={{ padding: '6px' }}>{t('Closing', '收單')}</th>
                                                <th style={{ padding: '6px' }}>{t('Ratio', '比例')}</th>
                                                <th style={{ padding: '6px' }}>{t('Tag', '標籤')}</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {channelsSnapshot.payload.channels.map((row) => (
                                                <tr key={row.channel} style={{ borderTop: '1px solid var(--glass-border)' }}>
                                                    <td style={{ padding: '6px', color: 'var(--text-primary)' }}>{row.channel}</td>
                                                    <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtNumber(row.assisting_conversions)}</td>
                                                    <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtNumber(row.closing_conversions)}</td>
                                                    <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{row.ratio != null ? row.ratio.toFixed(2) : '--'}</td>
                                                    <td style={{ padding: '6px' }}>
                                                        <span style={badgeStyle(row.tag)}>
                                                            {tr(language, CHANNEL_TAG_LABELS[row.tag]?.en, CHANNEL_TAG_LABELS[row.tag]?.zh) || row.tag}
                                                        </span>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </>
                        ) : (
                            emptyState(t('No channel data.', '暫無渠道資料。'))
                        )}
                    </section>

                    <AIInsightNote
                        language={language}
                        snapshot={channelsSnapshot}
                        kind="daily_channel"
                        contextLabel={t(
                            `Property ${propertyId}; period ${channelsSnapshot?.payload?.start_date || ''} ~ ${channelsSnapshot?.payload?.end_date || ''}`,
                            `屬性 ${propertyId}；期間 ${channelsSnapshot?.payload?.start_date || ''} ~ ${channelsSnapshot?.payload?.end_date || ''}`
                        )}
                        buildPayload={() => ({ channels: channelsSnapshot?.payload?.channels || [] })}
                    />
                </>
            )}

            {propertyId && activeTab === 'landing' && (
                <>
                    <section style={baseCardStyle}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
                            <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{t('Landing pages', '到達頁分析')}</div>
                            <DaySelector value={landingDays} onChange={(d) => { setLandingDays(d); loadLandingPages(propertyId, d); }} />
                        </div>
                        {landingError && <div style={{ color: '#fca5a5', fontSize: '0.85rem', marginBottom: '10px' }}>{landingError}</div>}
                        {landingLoading && !landingSnapshot ? (
                            emptyState(t('Loading landing pages…', '載入到達頁資料中…'))
                        ) : landingSnapshot?.payload?.landing_pages?.length ? (
                            <div style={{ overflowX: 'auto' }}>
                                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                                    <thead>
                                        <tr style={{ color: 'var(--text-secondary)', textAlign: 'left' }}>
                                            <th style={{ padding: '6px' }}>{t('Page', '頁面')}</th>
                                            <th style={{ padding: '6px' }}>{t('Sessions', '工作階段')}</th>
                                            <th style={{ padding: '6px' }}>{t('Conversion rate', '轉換率')}</th>
                                            <th style={{ padding: '6px' }}>{t('Bounce rate', '跳出率')}</th>
                                            <th style={{ padding: '6px' }}>{t('Flag', '標記')}</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {[...landingSnapshot.payload.landing_pages]
                                            .sort((a, b) => (b.sessions || 0) - (a.sessions || 0))
                                            .map((row) => (
                                                <tr key={row.landingPage} style={{ borderTop: '1px solid var(--glass-border)' }}>
                                                    <td style={{ padding: '6px', color: 'var(--text-primary)', maxWidth: '280px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={row.landingPage}>
                                                        {row.landingPage}
                                                    </td>
                                                    <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtNumber(row.sessions)}</td>
                                                    <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtPct(row.conversion_rate)}</td>
                                                    <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtPct(row.bounceRate)}</td>
                                                    <td style={{ padding: '6px' }}>
                                                        {row.is_high_traffic_low_conversion && (
                                                            <span style={badgeStyle('flagged')}>{t('High traffic, low conversion', '高流量低轉換')}</span>
                                                        )}
                                                    </td>
                                                </tr>
                                            ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            emptyState(t('No landing page data.', '暫無到達頁資料。'))
                        )}
                    </section>

                    <AIInsightNote
                        language={language}
                        snapshot={landingSnapshot}
                        kind="landing_page"
                        contextLabel={t(
                            `Property ${propertyId}; period ${landingSnapshot?.payload?.start_date || ''} ~ ${landingSnapshot?.payload?.end_date || ''}`,
                            `屬性 ${propertyId}；期間 ${landingSnapshot?.payload?.start_date || ''} ~ ${landingSnapshot?.payload?.end_date || ''}`
                        )}
                        buildPayload={() => ({ landing_pages: landingSnapshot?.payload?.landing_pages || [] })}
                    />
                </>
            )}

            {propertyId && activeTab === 'items' && (
                <>
                    <section style={baseCardStyle}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
                            <div>
                                <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{t('Items', '商品分析')}</div>
                                <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                                    {t('View growth compares the last 7 days vs. the prior 7 days.', '瀏覽成長比較固定用近 7 天 vs 前 7 天。')}
                                </div>
                            </div>
                            <DaySelector value={itemsDays} onChange={(d) => { setItemsDays(d); loadItems(propertyId, d); }} />
                        </div>
                        {itemsError && <div style={{ color: '#fca5a5', fontSize: '0.85rem', marginBottom: '10px' }}>{itemsError}</div>}
                        {itemsLoading && !itemsSnapshot ? (
                            emptyState(t('Loading items…', '載入商品資料中…'))
                        ) : itemsSnapshot?.payload?.items?.length ? (
                            <div style={{ overflowX: 'auto' }}>
                                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                                    <thead>
                                        <tr style={{ color: 'var(--text-secondary)', textAlign: 'left' }}>
                                            <th style={{ padding: '6px' }}>{t('Item', '商品')}</th>
                                            <th style={{ padding: '6px' }}>{t('Views', '瀏覽')}</th>
                                            <th style={{ padding: '6px' }}>{t('Add-to-cart rate', '加購率')}</th>
                                            <th style={{ padding: '6px' }}>{t('View growth', '瀏覽成長')}</th>
                                            <th style={{ padding: '6px' }}>{t('Revenue', '營收')}</th>
                                            <th style={{ padding: '6px' }}>{t('Flag', '標記')}</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {[...itemsSnapshot.payload.items]
                                            .sort((a, b) => (b.is_potential ? 1 : 0) - (a.is_potential ? 1 : 0))
                                            .map((row) => (
                                                <tr key={row.itemName} style={{ borderTop: '1px solid var(--glass-border)' }}>
                                                    <td style={{ padding: '6px', color: 'var(--text-primary)' }}>{row.itemName}</td>
                                                    <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtNumber(row.itemsViewed)}</td>
                                                    <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtPct(row.add_to_cart_rate)}</td>
                                                    <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtPct(row.views_growth_rate)}</td>
                                                    <td style={{ padding: '6px', color: 'var(--text-secondary)' }}>{fmtNumber(row.itemRevenue)}</td>
                                                    <td style={{ padding: '6px' }}>
                                                        {row.is_potential && <span style={badgeStyle('potential')}>{t('Potential', '潛力商品')}</span>}
                                                    </td>
                                                </tr>
                                            ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            emptyState(t('No item data.', '暫無商品資料。'))
                        )}
                    </section>

                    <AIInsightNote
                        language={language}
                        snapshot={itemsSnapshot}
                        kind="item"
                        contextLabel={t(
                            `Property ${propertyId}; period ${itemsSnapshot?.payload?.start_date || ''} ~ ${itemsSnapshot?.payload?.end_date || ''}`,
                            `屬性 ${propertyId}；期間 ${itemsSnapshot?.payload?.start_date || ''} ~ ${itemsSnapshot?.payload?.end_date || ''}`
                        )}
                        buildPayload={() => ({ items: itemsSnapshot?.payload?.items || [] })}
                    />
                </>
            )}

            {propertyId && activeTab === 'kpi' && (
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
            )}

            {propertyId && activeTab === 'alerts' && (
                <>
                    <section style={{ ...baseCardStyle, display: 'grid', gap: '14px' }}>
                        <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>
                            {editingRuleId ? t('Edit alert rule', '編輯告警規則') : t('Create alert rule', '建立告警規則')}
                        </div>
                        <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '12px', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, minmax(0, 1fr))' }}>
                            <select value={form.metric_key} onChange={(event) => setForm((prev) => ({ ...prev, metric_key: event.target.value }))} style={inputStyle}>
                                <option value="conversions">{t('Conversions', '轉換')}</option>
                                <option value="sessions">{t('Sessions', '工作階段')}</option>
                                <option value="purchase_revenue">{t('Revenue', '營收')}</option>
                            </select>
                            <select value={form.sensitivity} onChange={(event) => setForm((prev) => ({ ...prev, sensitivity: event.target.value }))} style={inputStyle}>
                                <option value="high">{t('High sensitivity', '高敏感')}</option>
                                <option value="medium">{t('Medium sensitivity', '中敏感')}</option>
                                <option value="low">{t('Low sensitivity', '低敏感')}</option>
                            </select>
                            <select value={form.check_frequency} onChange={(event) => setForm((prev) => ({ ...prev, check_frequency: event.target.value }))} style={inputStyle}>
                                <option value="hourly">{t('Hourly cumulative', '每小時累計')}</option>
                                <option value="daily">{t('Daily total', '每日總量')}</option>
                            </select>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)' }}>
                                <input type="checkbox" checked={form.is_enabled} onChange={(event) => setForm((prev) => ({ ...prev, is_enabled: event.target.checked }))} />
                                {t('Enabled', '啟用')}
                            </label>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)' }}>
                                <input type="checkbox" checked={form.notify_line} onChange={(event) => setForm((prev) => ({ ...prev, notify_line: event.target.checked }))} />
                                {t('Notify via LINE', 'LINE 通知')}
                            </label>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)' }}>
                                <input type="checkbox" checked={form.notify_email} onChange={(event) => setForm((prev) => ({ ...prev, notify_email: event.target.checked }))} />
                                {t('Notify via email', 'Email 通知')}
                            </label>
                            <input
                                type="number"
                                min="1"
                                value={form.cooldown_hours}
                                onChange={(event) => setForm((prev) => ({ ...prev, cooldown_hours: event.target.value }))}
                                style={inputStyle}
                                placeholder={t('Cooldown hours', '冷卻小時')}
                            />
                            <div style={{ display: 'flex', gap: '8px', gridColumn: isMobile ? 'auto' : 'span 2' }}>
                                <button type="submit" style={buttonStyle} disabled={!propertyId || saving}>
                                    {saving ? t('Saving…', '儲存中…') : editingRuleId ? t('Update rule', '更新規則') : t('Create rule', '建立規則')}
                                </button>
                                {editingRuleId && (
                                    <button type="button" style={secondaryButtonStyle} onClick={resetForm}>
                                        {t('Cancel', '取消')}
                                    </button>
                                )}
                            </div>
                        </form>
                    </section>

                    <section style={baseCardStyle}>
                        <div style={{ marginBottom: '12px', color: 'var(--text-primary)', fontWeight: 700 }}>
                            {t('Alert rules', '告警規則')}
                        </div>
                        {loading ? emptyState(t('Loading rules…', '載入規則中…')) : rules.length === 0 ? emptyState(t('No rules yet.', '目前沒有規則。')) : (
                            <div style={{ display: 'grid', gap: '10px' }}>
                                {rules.map((rule) => (
                                    <div key={rule.id} style={{ border: '1px solid var(--glass-border)', borderRadius: '12px', padding: '14px' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
                                            <div>
                                                <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>
                                                    {rule.metric_key} · {rule.check_frequency}
                                                </div>
                                                <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                                                    {rule.sensitivity} · cooldown {rule.cooldown_hours}h · {rule.is_enabled ? t('enabled', '啟用中') : t('disabled', '已停用')}
                                                </div>
                                            </div>
                                            <div style={{ display: 'flex', gap: '8px' }}>
                                                <button type="button" style={secondaryButtonStyle} onClick={() => startEdit(rule)}>
                                                    {t('Edit', '編輯')}
                                                </button>
                                                <button type="button" style={secondaryButtonStyle} onClick={() => handleDelete(rule.id)}>
                                                    {t('Delete', '刪除')}
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </section>

                    <section style={baseCardStyle}>
                        <div style={{ marginBottom: '12px', color: 'var(--text-primary)', fontWeight: 700 }}>
                            {t('Alert history', '告警歷史')}
                        </div>
                        {loading ? emptyState(t('Loading events…', '載入事件中…')) : events.length === 0 ? emptyState(t('No events yet.', '目前沒有事件。')) : (
                            <div style={{ display: 'grid', gap: '10px' }}>
                                {events.map((eventRow) => (
                                    <div key={eventRow.id} style={{ border: '1px solid var(--glass-border)', borderRadius: '12px', padding: '14px' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
                                            <div style={{ display: 'grid', gap: '6px' }}>
                                                <div style={{ color: 'var(--text-primary)', fontWeight: 700 }}>
                                                    {eventRow.metric_key} · {eventRow.direction} · {eventRow.severity}
                                                </div>
                                                <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{eventRow.message}</div>
                                                <div style={{ color: 'var(--text-tertiary)', fontSize: '0.8rem' }}>
                                                    observed {eventRow.observed_value} / expected {eventRow.expected_low} - {eventRow.expected_high}
                                                </div>
                                            </div>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                {eventRow.acknowledged_at ? (
                                                    <span style={{ color: '#86efac', fontSize: '0.85rem' }}>{t('Acknowledged', '已讀')}</span>
                                                ) : (
                                                    <button type="button" style={buttonStyle} onClick={() => handleAck(eventRow.id)}>
                                                        {t('Acknowledge', '標記已讀')}
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </section>
                </>
            )}
        </div>
    );
};

export default GA4Insights;
