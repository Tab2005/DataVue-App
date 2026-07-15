import React, { useEffect, useRef, useState } from 'react';
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
    ResponsiveContainer,
    ReferenceArea,
    ReferenceLine,
} from 'recharts';

import { ga4InsightsService } from '../../services/ga4InsightsService';
import { aiService } from '../../services/aiService';

// ── Chart token layer（沿用 ContributionAnalysis.jsx 已驗證通過 dataviz
//    六項檢查的同一組categorical色票，維持全站視覺一致；docs/22 第 2 波） ──
export const VIZ_TOKENS = `
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

export const baseCardStyle = {
    background: 'var(--bg-secondary)',
    border: '1px solid var(--glass-border)',
    borderRadius: '16px',
    padding: '20px',
};

export const inputStyle = {
    width: '100%',
    padding: '10px 12px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255, 255, 255, 0.04)',
    color: 'var(--text-primary)',
};

export const buttonStyle = {
    padding: '10px 14px',
    borderRadius: '10px',
    border: '1px solid rgba(59, 130, 246, 0.35)',
    background: 'rgba(59, 130, 246, 0.16)',
    color: '#bfdbfe',
    cursor: 'pointer',
};

export const secondaryButtonStyle = {
    ...buttonStyle,
    border: '1px solid var(--glass-border)',
    background: 'transparent',
    color: 'var(--text-secondary)',
};

export const tabButtonStyle = (active) => ({
    padding: '9px 16px',
    borderRadius: '999px',
    border: active ? '1px solid rgba(59, 130, 246, 0.5)' : '1px solid var(--glass-border)',
    background: active ? 'rgba(59, 130, 246, 0.18)' : 'transparent',
    color: active ? '#bfdbfe' : 'var(--text-secondary)',
    fontWeight: active ? 700 : 500,
    cursor: 'pointer',
    whiteSpace: 'nowrap',
});

export const dayButtonStyle = (active) => ({
    padding: '6px 12px',
    borderRadius: '8px',
    border: active ? '1px solid rgba(59, 130, 246, 0.5)' : '1px solid var(--glass-border)',
    background: active ? 'rgba(59, 130, 246, 0.16)' : 'transparent',
    color: active ? '#bfdbfe' : 'var(--text-secondary)',
    cursor: 'pointer',
    fontSize: '0.82rem',
});

export const badgeStyle = (kind) => {
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
        product: { bg: 'rgba(57, 135, 229, 0.16)', fg: '#93c5fd', border: 'rgba(57, 135, 229, 0.35)' },
        article: { bg: 'rgba(201, 133, 0, 0.18)', fg: '#fbbf24', border: 'rgba(201, 133, 0, 0.4)' },
        functional: { bg: 'rgba(25, 158, 112, 0.16)', fg: '#86efac', border: 'rgba(25, 158, 112, 0.35)' },
        new_entry: { bg: 'rgba(57, 135, 229, 0.16)', fg: '#93c5fd', border: 'rgba(57, 135, 229, 0.35)' },
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

export const emptyState = (text) => (
    <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{text}</div>
);

// 大量列表的純前端分頁器（資料已一次全部載入，不重打 API，只切片顯示）。
// 沿用 MetaAndromedaReviewQueue.jsx 的分頁 UI 樣式，維持全站視覺一致。
const pagerButtonStyle = {
    padding: '5px 10px',
    borderRadius: '8px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255, 255, 255, 0.04)',
    color: 'var(--text-primary)',
    cursor: 'pointer',
    fontSize: '0.85rem',
    minWidth: '32px',
};

export const TablePager = ({ page, totalPages, onPageChange, language }) => {
    if (totalPages <= 1) return null;

    const pages = [];
    const delta = 2;
    const left = Math.max(1, page - delta);
    const right = Math.min(totalPages, page + delta);
    if (left > 1) { pages.push(1); if (left > 2) pages.push('…'); }
    for (let i = left; i <= right; i++) pages.push(i);
    if (right < totalPages) { if (right < totalPages - 1) pages.push('…'); pages.push(totalPages); }

    return (
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center', justifyContent: 'center', flexWrap: 'wrap', marginTop: '14px' }}>
            <button
                type="button"
                onClick={() => onPageChange(page - 1)}
                disabled={page <= 1}
                style={{ ...pagerButtonStyle, opacity: page <= 1 ? 0.35 : 1 }}
            >‹</button>
            {pages.map((p, i) => (
                p === '…'
                    ? <span key={`ellipsis-${i}`} style={{ color: 'var(--text-secondary)', padding: '0 4px' }}>…</span>
                    : (
                        <button
                            key={p}
                            type="button"
                            onClick={() => onPageChange(p)}
                            style={{
                                ...pagerButtonStyle,
                                background: p === page ? 'var(--accent-primary)' : 'rgba(255, 255, 255, 0.04)',
                                color: p === page ? '#fff' : 'var(--text-primary)',
                                borderColor: p === page ? 'var(--accent-primary)' : 'var(--glass-border)',
                                fontWeight: p === page ? 700 : 400,
                            }}
                        >{p}</button>
                    )
            ))}
            <button
                type="button"
                onClick={() => onPageChange(page + 1)}
                disabled={page >= totalPages}
                style={{ ...pagerButtonStyle, opacity: page >= totalPages ? 0.35 : 1 }}
            >›</button>
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', marginLeft: '8px' }}>
                {tr(language, `Page ${page} / ${totalPages}`, `第 ${page} / ${totalPages} 頁`)}
            </span>
        </div>
    );
};

export const tr = (language, en, zh) => (language === 'en' ? en : zh);

export const fmtNumber = (value, digits = 0) => {
    if (value == null || Number.isNaN(value)) return '--';
    return Number(value).toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: 0 });
};

export const fmtPct = (value, digits = 1) => {
    if (value == null || Number.isNaN(value)) return '--';
    return `${(value * 100).toFixed(digits)}%`;
};

export const CHANNEL_TAG_LABELS = {
    assist: { en: 'Assist', zh: '助攻型' },
    close: { en: 'Close', zh: '主攻型' },
    balanced: { en: 'Balanced', zh: '均衡' },
    insufficient_data: { en: 'Insufficient data', zh: '資料不足' },
};

// docs/34 第一波：歸因模式揭露。「收單」欄位的實際意義依 GA4 property 的
// 報表歸因模式而定（資料驅動＝路徑加權功勞；最後點擊＝單純最後一次接觸）。
export const ATTRIBUTION_MODEL_LABELS = {
    data_driven: {
        en: 'Data-driven attribution',
        zh: '資料驅動歸因',
        tooltip: {
            en: 'This property\'s reporting attribution model is data-driven: "Closing" conversions already reflect credit distributed across the full path, not just the last touch.',
            zh: '此 GA4 屬性的報表歸因模式為「以數據為準」：「收單」已是路徑上多個接觸點加權後的功勞總和，不是單純最後一次點擊。',
        },
    },
    last_click: {
        en: 'Last-click attribution',
        zh: '最後點擊歸因',
        tooltip: {
            en: 'This property\'s reporting attribution model is last-click: "Closing" conversions are credited entirely to the last touchpoint.',
            zh: '此 GA4 屬性的報表歸因模式為「最後點擊」：「收單」的功勞全部算給最後一次接觸的管道。',
        },
    },
};

// docs/34 第二波：「收單」欄位文案依 attribution_model 動態切換（依賴第一波
// 的 payload.attribution_model）。"unknown" 時不臆測，用中性字樣。
const CHANNEL_CLOSING_LABEL_OVERRIDES = {
    data_driven: { en: 'Closing (path credit)', zh: '收單（路徑功勞）' },
    last_click: { en: 'Closing (last-touch)', zh: '收單（最後接觸）' },
};

export const channelClosingLabel = (attributionModel, language) => {
    const entry = CHANNEL_CLOSING_LABEL_OVERRIDES[attributionModel];
    return entry ? tr(language, entry.en, entry.zh) : tr(language, 'Closing', '收單');
};

// 第 4 波：渠道對照維度切換（5 選項，對映後端 CHANNEL_DIMENSION_MAP 白名單）
export const CHANNEL_DIMENSION_OPTIONS = [
    { value: 'default_channel_group', en: 'Session default channel group', zh: '工作階段主要管道群組' },
    { value: 'source_medium', en: 'Session source / medium', zh: '工作階段來源/媒介' },
    { value: 'source', en: 'Session source', zh: '工作階段來源' },
    { value: 'medium', en: 'Session medium', zh: '工作階段媒介' },
    { value: 'campaign', en: 'Session campaign', zh: '工作階段廣告活動' },
];

export const channelDimensionLabel = (dimension, language) => {
    const option = CHANNEL_DIMENSION_OPTIONS.find((o) => o.value === dimension) || CHANNEL_DIMENSION_OPTIONS[0];
    return tr(language, option.en, option.zh);
};

export const METRIC_LABELS = {
    sessions: { en: 'Sessions', zh: '工作階段' },
    conversions: { en: 'Conversions', zh: '轉換' },
    purchaseRevenue: { en: 'Revenue', zh: '營收' },
};

export const KPI_STATUS_LABELS = {
    ahead: { en: 'Ahead of pace', zh: '超前進度' },
    on_track: { en: 'On track', zh: '符合進度' },
    behind: { en: 'Behind pace', zh: '落後進度' },
    no_target: { en: 'No target set', zh: '未設定目標' },
    data_unavailable: { en: 'Data unavailable', zh: '資料暫缺' },
};

export const KPI_METRIC_OPTIONS = [
    { value: 'conversions', en: 'Conversions', zh: '轉換' },
    { value: 'sessions', en: 'Sessions', zh: '工作階段' },
    { value: 'purchase_revenue', en: 'Revenue', zh: '營收' },
];

export const currentMonthKey = () => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
};

export const currentQuarterKey = () => {
    const now = new Date();
    return `${now.getFullYear()}-Q${Math.floor(now.getMonth() / 3) + 1}`;
};

// 第 5 波：到達頁分類（4 類固定枚舉，對映後端 LANDING_PAGE_CATEGORIES）
export const LANDING_CATEGORY_ORDER = ['product', 'article', 'functional', 'other'];
export const LANDING_CATEGORY_LABELS = {
    product: { en: 'Product', zh: '商品' },
    article: { en: 'Article', zh: '文章' },
    functional: { en: 'Functional', zh: '功能' },
    other: { en: 'Other', zh: '其他' },
};
export const LANDING_MATCH_TYPE_OPTIONS = [
    { value: 'prefix', en: 'Prefix', zh: '前綴' },
    { value: 'contains', en: 'Contains', zh: '包含' },
];

// 第 7 波：商品分類來源標示（GA4 權威 vs 自訂規則補充 vs 未分類）
export const ITEM_CATEGORY_SOURCE_LABELS = {
    ga4: { en: 'from GA4', zh: '來自 GA4' },
    custom_rule: { en: 'from custom rule', zh: '來自自訂規則' },
    unset: { en: 'unset', zh: '未設定' },
};

export const DASHBOARD_METRICS = ['sessions', 'conversions', 'purchaseRevenue'];

// 商品分析表格可排序欄位（依使用者要求新增，2026-07-10）；預設方向：
// 數字欄位高到低（desc）比較常用，文字欄位 A→Z（asc）。
export const ITEMS_SORT_COLUMNS = {
    itemName: { type: 'string', defaultDir: 'asc' },
    item_category: { type: 'string', defaultDir: 'asc' },
    itemsViewed: { type: 'number', defaultDir: 'desc' },
    cart_to_view_rate: { type: 'number', defaultDir: 'desc' },
    purchase_to_view_rate: { type: 'number', defaultDir: 'desc' },
    views_growth_rate: { type: 'number', defaultDir: 'desc' },
    itemRevenue: { type: 'number', defaultDir: 'desc' },
};

// ── AI 白話解讀共用卡（同週報 / 貢獻分析頁的模式，docs/22 任務 2.4） ──
export const AIInsightNote = ({ language, snapshot, kind, buildPayload, contextLabel }) => {
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
export const IntradayMetricCard = ({ language, metricKey, hourlyTotals, baseline, cumulativeValue, isAnomaly }) => {
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
export const KpiPacingCard = ({ language, target, onDelete }) => {
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

