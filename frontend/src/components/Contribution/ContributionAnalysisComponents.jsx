import React, { useEffect, useMemo, useState, useRef } from 'react';
import { FiCpu, FiInfo, FiRefreshCcw } from 'react-icons/fi';
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
    Cell,
    Legend,
} from 'recharts';

import { aiService } from '../../services/aiService';
import { saveAiSummary } from '../../services/contributionService';

export const t = (language, en, zh) => (language === 'en' ? en : zh);

// ── Chart token layer (dark defaults + prefers-color-scheme: light) ──
// 3 categorical slots: Spend / Platform-Reported / MMM, in the reference order.
// Validated dark (ΔE 41.3 adjacent) and light (ΔE 47.2 adjacent) on
//  the surfaces below; chroma/lightness pass for categorical.
export const VIZ_TOKENS = `
.contribution-chart-root {
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
  .contribution-chart-root {
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
.contribution-chart-root text { font-variant-numeric: tabular-nums; }

/* AI 白話解讀卡片的 markdown 渲染樣式（搭配 remark-gfm） */
.report-ai-content {
  font-size: 0.9rem;
  line-height: 1.75;
  color: var(--text-primary);
}
.report-ai-content h2 {
  font-size: 1.05rem;
  font-weight: 700;
  color: #06b6d4;
  margin: 1.1rem 0 0.55rem;
  border-left: 3px solid #06b6d4;
  padding-left: 10px;
}
.report-ai-content h2:first-child { margin-top: 0; }
.report-ai-content h3 {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0.9rem 0 0.4rem;
}
.report-ai-content p {
  margin: 0.5rem 0;
  color: var(--text-secondary);
}
.report-ai-content ul {
  margin: 0.5rem 0 0.7rem;
  padding-left: 1.4rem;
  list-style: none;
}
.report-ai-content li {
  position: relative;
  margin: 0.35rem 0;
  line-height: 1.7;
  color: var(--text-primary);
}
.report-ai-content li::before {
  content: '▸';
  color: #06b6d4;
  position: absolute;
  left: -1rem;
  font-weight: bold;
}
.report-ai-content ol {
  margin: 0.5rem 0 0.7rem;
  padding-left: 1.6rem;
  color: var(--text-primary);
}
.report-ai-content ol li::before { content: ''; }
.report-ai-content table {
  width: 100%;
  border-collapse: collapse;
  margin: 0.6rem 0 0.8rem;
  font-size: 0.82rem;
}
.report-ai-content th {
  background: rgba(6, 182, 212, 0.1);
  color: #06b6d4;
  padding: 7px 10px;
  text-align: left;
  border-bottom: 2px solid #06b6d4;
  font-weight: 600;
}
.report-ai-content td {
  padding: 6px 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--text-primary);
}
.report-ai-content tr:last-child td { border-bottom: none; }
.report-ai-content strong {
  color: #06b6d4;
  font-weight: 600;
}
.report-ai-content code {
  background: rgba(6, 182, 212, 0.15);
  padding: 1px 5px;
  border-radius: 3px;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
  font-size: 0.85em;
}
.report-ai-content blockquote {
  margin: 0.6rem 0;
  padding: 0.4rem 0.8rem;
  border-left: 3px solid rgba(6, 182, 212, 0.5);
  background: rgba(6, 182, 212, 0.06);
  color: var(--text-secondary);
  border-radius: 0 4px 4px 0;
}
.report-ai-content hr {
  border: none;
  border-top: 1px dashed rgba(255, 255, 255, 0.1);
  margin: 0.9rem 0;
}
`;

const fmtPct = (value, digits = 1) => {
    if (value == null || Number.isNaN(value)) return '--';
    return `${(value * 100).toFixed(digits)}%`;
};

const fmtNumber = (value, digits = 2) => {
    if (value == null || Number.isNaN(value)) return '--';
    return value.toFixed(digits);
};

const isoDate = (offsetDays = 0) => {
    const d = new Date();
    d.setUTCHours(0, 0, 0, 0);
    d.setUTCDate(d.getUTCDate() + offsetDays);
    return d.toISOString().slice(0, 10);
};

export const computePeriod = (days) => {
    const end = isoDate(-1);
    const startDate = new Date(end);
    startDate.setUTCDate(startDate.getUTCDate() - (days - 1));
    return { dateStart: startDate.toISOString().slice(0, 10), dateEnd: end };
};

const groupRowHasCampaigns = (group) => Array.isArray(group.campaign_ids) && group.campaign_ids.length > 0;

const SelfDoubtfulBadge = ({ isDoubtful, language }) => {
    if (!isDoubtful) return null;
    return (
        <span
            style={{
                marginLeft: '8px',
                padding: '1px 8px',
                borderRadius: '999px',
                background: 'rgba(156, 163, 175, 0.18)',
                color: '#9ca3af',
                fontSize: '0.7rem',
                fontWeight: 700,
                letterSpacing: '0.04em',
            }}
            title={t(language, 'High collinearity with another group; estimate may be unreliable.', '與其他組別共線性高，估計可能不準確。')}
        >
            {t(language, 'DOUBTFUL', '存疑')}
        </span>
    );
};

export const Section = ({ title, subtitle, children, style }) => (
    <section
        style={{
            background: 'var(--bg-secondary)',
            border: '1px solid var(--glass-border)',
            borderRadius: '16px',
            padding: '20px 22px',
            ...style,
        }}
    >
        {(title || subtitle) && (
            <div style={{ marginBottom: '14px' }}>
                {title && (
                    <h2
                        style={{
                            margin: 0,
                            color: 'var(--text-primary)',
                            fontSize: '1rem',
                            fontWeight: 700,
                        }}
                    >
                        {title}
                    </h2>
                )}
                {subtitle && (
                    <div
                        style={{
                            marginTop: '4px',
                            color: 'var(--text-secondary)',
                            fontSize: '0.82rem',
                            lineHeight: 1.5,
                        }}
                    >
                        {subtitle}
                    </div>
                )}
            </div>
        )}
        {children}
    </section>
);

export const ErrorPanel = ({ message }) => (
    <div
        style={{
            marginBottom: '16px',
            padding: '12px 14px',
            borderRadius: '12px',
            background: 'rgba(239, 68, 68, 0.08)',
            border: '1px solid rgba(239, 68, 68, 0.25)',
            color: '#fca5a5',
            fontSize: '0.85rem',
            whiteSpace: 'pre-wrap',
        }}
    >
        {message}
    </div>
);

export const InfoPanel = ({ message, tone = 'info' }) => {
    const palette = {
        info: { bg: 'rgba(59, 130, 246, 0.08)', border: 'rgba(59, 130, 246, 0.3)', color: '#93c5fd' },
        success: { bg: 'rgba(34, 197, 94, 0.08)', border: 'rgba(34, 197, 94, 0.3)', color: '#86efac' },
    };
    const c = palette[tone] || palette.info;
    return (
        <div
            style={{
                padding: '10px 14px',
                borderRadius: '12px',
                background: c.bg,
                border: `1px solid ${c.border}`,
                color: c.color,
                fontSize: '0.85rem',
                lineHeight: 1.6,
            }}
        >
            {message}
        </div>
    );
};

const ChartMethodNote = ({ lead, detail, language }) => (
    <div
        className="contribution-chart-root"
        style={{
            marginTop: '16px',
            padding: '10px 12px 10px 14px',
            borderRadius: '8px',
            background: 'rgba(255, 255, 255, 0.025)',
            border: '1px solid var(--viz-grid)',
            display: 'flex',
            gap: '10px',
            alignItems: 'flex-start',
        }}
    >
        <FiInfo
            size={14}
            color="var(--viz-axis)"
            style={{ flexShrink: 0, marginTop: '3px' }}
            aria-hidden="true"
        />
        <div
            style={{
                fontSize: '0.78rem',
                lineHeight: 1.6,
                color: 'var(--viz-text)',
            }}
        >
            <span
                style={{
                    color: 'var(--viz-text-strong)',
                    fontWeight: 600,
                }}
            >
                {lead}
            </span>
            {detail && (
                <>
                    <span aria-hidden="true" style={{ margin: '0 6px', color: 'var(--viz-axis)' }}>
                        ·
                    </span>
                    {detail}
                </>
            )}
        </div>
    </div>
);

export const AccountAndPeriod = ({
    language,
    isMobile,
    accountId,
    onAccountChange,
    onRefreshCampaigns,
    refreshing,
    campaignsCount,
    periodDays,
    onPeriodChange,
    onSubmit,
    submitting,
    canSubmit,
    accountList,
    loadingAccounts,
    dataCoverage,
}) => {
    // docs/27 任務 6.1：分析請求區間若超出實際快取涵蓋範圍，後端會自動
    // clamp 到快取實際涵蓋範圍（並在結果附加說明），不會把缺口日子當假的
    // 零花費資料餵進模型。這裡只是先讓使用者知道「選了 N 天但可能沒那麼
    // 多可用資料」，不是唯一把關點，也不因此停用送出按鈕。
    const requestedStart = accountId ? computePeriod(periodDays).dateStart : null;
    const coverageInsufficient = Boolean(
        dataCoverage?.first_date && requestedStart && requestedStart < dataCoverage.first_date
    );
    return (
        <Section
            title={t(language, 'Ad Account & Period', '廣告帳戶與分析期間')}
            subtitle={t(
                language,
                'Pick an ad account and analysis period, then run MMM. Defaults to the most recent 180 days.',
                '選擇廣告帳戶與分析期間後開始 MMM 分析。預設為最近 180 天。'
            )}
        >
            <div
                style={{
                    display: 'grid',
                    gridTemplateColumns: isMobile ? '1fr' : '1.4fr 1fr auto',
                    gap: '12px',
                    alignItems: 'flex-end',
                }}
            >
                <label style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                        {t(language, 'Ad Account', '廣告帳戶')}
                    </span>
                    <select
                        value={accountId}
                        onChange={(e) => onAccountChange(e.target.value)}
                        style={selectStyle}
                        disabled={loadingAccounts}
                    >
                        <option value="">
                            {loadingAccounts
                                ? t(language, 'Loading...', '載入中…')
                                : t(language, 'Select an account', '請選擇帳戶')}
                        </option>
                        {accountList.map((acc) => (
                            <option key={acc.id} value={acc.id}>
                                {acc.name} · {acc.id}
                            </option>
                        ))}
                    </select>
                </label>

                <label style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                        {t(language, 'Period (days)', '分析區間（天）')}
                    </span>
                    <select
                        value={periodDays}
                        onChange={(e) => onPeriodChange(Number(e.target.value))}
                        style={selectStyle}
                    >
                        <option value={90}>90</option>
                        <option value={180}>180</option>
                        <option value={365}>365</option>
                    </select>
                </label>

                <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                        type="button"
                        onClick={onRefreshCampaigns}
                        disabled={!accountId || refreshing}
                        style={{
                            ...secondaryButtonStyle,
                            opacity: !accountId || refreshing ? 0.5 : 1,
                        }}
                    >
                        {refreshing
                            ? t(language, 'Refreshing…', '抓取中…')
                            : t(language, 'Refresh Data', '抓取資料')}
                    </button>
                    <button
                        type="button"
                        onClick={onSubmit}
                        disabled={!canSubmit || submitting}
                        style={{
                            ...primaryButtonStyle,
                            opacity: !canSubmit || submitting ? 0.5 : 1,
                        }}
                    >
                        {submitting
                            ? t(language, 'Submitting…', '送出中…')
                            : t(language, 'Run Analysis', '開始分析')}
                    </button>
                </div>
            </div>

            {accountId && (
                <div
                    style={{
                        marginTop: '10px',
                        color: 'var(--text-secondary)',
                        fontSize: '0.78rem',
                    }}
                >
                    {t(
                        language,
                        `Cached campaigns: ${campaignsCount}. If 0, click Refresh Data to fetch from Meta.`,
                        `快取中活動數：${campaignsCount}。若為 0 請先按「抓取資料」從 Meta 拉取。`
                    )}
                    {dataCoverage?.first_date && (
                        <span>
                            {' · '}
                            {t(
                                language,
                                `Cached data covers ${dataCoverage.first_date} ~ ${dataCoverage.last_date} (${dataCoverage.days_covered} days).`,
                                `快取資料涵蓋 ${dataCoverage.first_date} ~ ${dataCoverage.last_date}（共 ${dataCoverage.days_covered} 天）。`
                            )}
                        </span>
                    )}
                </div>
            )}

            {coverageInsufficient && (
                <div style={{ marginTop: '10px' }}>
                    <InfoPanel
                        message={t(
                            language,
                            `Requested period starts before cached data (${dataCoverage.first_date}). Analysis will automatically use the actually cached range instead of padding missing days with zero.`,
                            `選擇的區間早於實際快取起點（${dataCoverage.first_date}），分析會自動改用實際可用的快取區間，不會把缺口日子當成 0 花費餵進模型。`
                        )}
                    />
                </div>
            )}
        </Section>
    );
};

const ContributionChart = ({ language, rows, isMobile }) => {
    if (!rows.length) {
        return <InfoPanel message={t(language, 'No analysis result yet.', '尚無分析結果。')} />;
    }
    const data = rows.map((row) => ({
        group: row.label,
        spend: row.spendShare,
        reported: row.reportedShare,
        mmm: row.contributionShare?.median ?? 0,
        mmmMin: row.contributionShare?.min ?? 0,
        mmmMax: row.contributionShare?.max ?? 0,
        doubtful: row.doubtful,
    }));
    const chartHeight = isMobile ? 320 : Math.max(360, data.length * 64);

    return (
        <div className="contribution-chart-root" style={{ width: '100%' }}>
            <div style={{ width: '100%', height: chartHeight }}>
                <ResponsiveContainer>
                    <BarChart
                        data={data}
                        layout="vertical"
                        margin={{ top: 8, right: 28, left: 8, bottom: 8 }}
                        barCategoryGap="32%"
                        barGap={2}
                    >
                    <CartesianGrid
                        stroke="var(--viz-grid)"
                        horizontal={false}
                        vertical
                    />
                    <XAxis
                        type="number"
                        domain={[0, (dMax) => Math.max(0.05, Math.ceil(dMax * 10) / 10)]}
                        tickFormatter={(v) => `${Math.round(v * 100)}%`}
                        tick={{ fill: 'var(--viz-text)', fontSize: 11 }}
                        stroke="var(--viz-axis)"
                        tickLine={false}
                    />
                    <YAxis
                        type="category"
                        dataKey="group"
                        width={140}
                        tick={{ fill: 'var(--viz-text)', fontSize: 11 }}
                        stroke="var(--viz-axis)"
                        tickLine={false}
                    />
                    <Tooltip
                        cursor={{ fill: 'var(--viz-grid)' }}
                        formatter={(v) => `${(v * 100).toFixed(1)}%`}
                        contentStyle={{
                            background: 'var(--viz-tooltip-bg)',
                            border: '1px solid var(--viz-tooltip-border)',
                            borderRadius: '8px',
                            color: 'var(--viz-text-strong)',
                            fontSize: '0.8rem',
                            padding: '8px 10px',
                        }}
                        itemStyle={{ color: 'var(--viz-text-strong)' }}
                        labelStyle={{
                            color: 'var(--viz-text)',
                            marginBottom: '4px',
                            fontSize: '0.72rem',
                        }}
                    />
                    <Legend
                        wrapperStyle={{
                            color: 'var(--viz-text)',
                            fontSize: '0.78rem',
                            paddingTop: '4px',
                        }}
                        iconType="rect"
                        iconSize={10}
                    />
                    <Bar
                        dataKey="spend"
                        name={t(language, 'Spend Share', '花費占比')}
                        fill="var(--viz-series-1)"
                        radius={[0, 2, 2, 0]}
                        maxBarSize={14}
                    >
                        {data.map((row, i) => (
                            <Cell
                                key={`spend-${i}`}
                                fill={row.doubtful ? 'var(--viz-series-muted)' : 'var(--viz-series-1)'}
                            />
                        ))}
                    </Bar>
                    <Bar
                        dataKey="reported"
                        name={t(language, 'Platform-Reported', '自報占比')}
                        fill="var(--viz-series-2)"
                        radius={[0, 2, 2, 0]}
                        maxBarSize={14}
                    >
                        {data.map((row, i) => (
                            <Cell
                                key={`reported-${i}`}
                                fill={row.doubtful ? 'var(--viz-series-muted)' : 'var(--viz-series-2)'}
                            />
                        ))}
                    </Bar>
                    <Bar
                        dataKey="mmm"
                        name={t(language, 'MMM Contribution (median)', 'MMM 貢獻 (中位)')}
                        fill="var(--viz-series-3)"
                        radius={[0, 2, 2, 0]}
                        maxBarSize={14}
                    >
                        {data.map((row, i) => (
                            <Cell
                                key={`mmm-${i}`}
                                fill={row.doubtful ? 'var(--viz-series-muted)' : 'var(--viz-series-3)'}
                            />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
            </div>
            <ChartMethodNote
                language={language}
                lead={t(
                    language,
                    'MMM contribution is the median across restarts.',
                    'MMM 貢獻 = 多次重啟的中位數。'
                )}
                detail={t(
                    language,
                    'Per-group min–max range is reported in the table below; gray bars mark groups flagged as doubtful due to high collinearity.',
                    '每組 min–max 範圍列於下方表格；標「存疑」的組別以灰階呈現並附共線性說明。'
                )}
            />
        </div>
    );
};

const ContributionTable = ({ language, rows, marginalCurrency }) => {
    if (!rows.length) return null;
    return (
        <div
            style={{
                marginTop: '12px',
                border: '1px solid var(--glass-border)',
                borderRadius: '10px',
                overflow: 'hidden',
            }}
        >
            <table
                style={{
                    width: '100%',
                    borderCollapse: 'collapse',
                    fontSize: '0.82rem',
                    color: 'var(--text-primary)',
                }}
            >
                <thead>
                    <tr style={{ background: 'rgba(255,255,255,0.04)', textAlign: 'left' }}>
                        <th style={thStyle}>{t(language, 'Group', '組別')}</th>
                        <th style={thStyle}>{t(language, 'Spend', '花費占比')}</th>
                        <th style={thStyle}>{t(language, 'Reported', '自報占比')}</th>
                        <th style={thStyle}>{t(language, 'MMM (median / min / max)', 'MMM (中位 / 最小 / 最大)')}</th>
                        <th style={thStyle}>
                            {/* docs/27 任務 4.3：每組步長各自不同（依日均花費計算），
                                表頭不再宣稱單一步長，實際步長改列在每列內。 */}
                            {t(language, 'Marginal (step per row)', '邊際轉換（每組步長見列內）')}
                        </th>
                    </tr>
                </thead>
                <tbody>
                    {rows.map((row) => (
                        <tr key={row.groupKey} style={{ borderTop: '1px solid var(--glass-border)' }}>
                            <td style={tdStyle}>
                                <span style={{ color: row.doubtful ? '#9ca3af' : 'var(--text-primary)' }}>
                                    {row.label}
                                </span>
                                <SelfDoubtfulBadge isDoubtful={row.doubtful} language={language} />
                            </td>
                            <td style={tdStyle}>{fmtPct(row.spendShare)}</td>
                            <td style={tdStyle}>{fmtPct(row.reportedShare)}</td>
                            <td style={tdStyle}>
                                {fmtPct(row.contributionShare?.median)} / {fmtPct(row.contributionShare?.min)} / {fmtPct(row.contributionShare?.max)}
                            </td>
                            <td style={tdStyle}>
                                {row.marginalPerStep?.median != null && row.marginalStepValue != null
                                    ? `+${fmtNumber(row.marginalPerStep.median, 2)}（/ +${fmtNumber(row.marginalStepValue, 0)}${marginalCurrency}）`
                                    : '--'}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

const MarginalTooltipContent = ({ active, payload, language }) => {
    if (!active || !payload?.length) return null;
    const row = payload[0]?.payload;
    if (!row) return null;
    return (
        <div
            style={{
                background: 'var(--viz-tooltip-bg)',
                border: '1px solid var(--viz-tooltip-border)',
                borderRadius: '8px',
                color: 'var(--viz-text-strong)',
                fontSize: '0.8rem',
                padding: '8px 10px',
            }}
        >
            <div style={{ color: 'var(--viz-text)', marginBottom: '4px', fontSize: '0.72rem' }}>
                {row.group}
            </div>
            <div>
                +{row.marginal.toFixed(2)} {t(language, 'per +100', '每 +100 元')}
            </div>
            <div style={{ color: 'var(--viz-text)', fontSize: '0.72rem', marginTop: '2px' }}>
                {t(
                    language,
                    `raw: +${row.rawMarginal.toFixed(2)} per +${row.step}`,
                    `原始：+${row.rawMarginal.toFixed(2)} / +${row.step} 元`
                )}
            </div>
        </div>
    );
};

const MarginalChart = ({ language, rows, marginalCurrency, isMobile }) => {
    if (!rows.length) return null;
    // docs/27 任務 4.3：各組步長不同（依日均花費各自計算），原始邊際值不能
    // 直接跨組比大小——正規化為「每 +100 元」的邊際轉換後才可公平排序/比較，
    // 原始 step 與原始邊際值改在 tooltip 顯示。
    const data = rows
        .filter((row) => row.marginalPerStep?.median != null && row.marginalStepValue)
        .map((row) => {
            const step = row.marginalStepValue;
            const rawMarginal = row.marginalPerStep.median;
            return {
                group: row.label,
                marginal: (rawMarginal / step) * 100,
                rawMarginal,
                step,
                groupKey: row.groupKey,
                doubtful: row.doubtful,
            };
        });
    if (!data.length) {
        return <InfoPanel message={t(language, 'No marginal data.', '無邊際資料。')} />;
    }
    data.sort((a, b) => b.marginal - a.marginal);
    const chartHeight = isMobile ? 280 : Math.max(320, data.length * 52);
    return (
        <div className="contribution-chart-root" style={{ width: '100%' }}>
            <div style={{ width: '100%', height: chartHeight }}>
                <ResponsiveContainer>
                    <BarChart
                        data={data}
                        layout="vertical"
                        margin={{ top: 8, right: 56, left: 8, bottom: 8 }}
                        barCategoryGap="36%"
                        barGap={2}
                    >
                    <CartesianGrid
                        stroke="var(--viz-grid)"
                        horizontal={false}
                        vertical
                    />
                    <XAxis
                        type="number"
                        tickFormatter={(v) => `+${v.toFixed(2)}`}
                        tick={{ fill: 'var(--viz-text)', fontSize: 11 }}
                        stroke="var(--viz-axis)"
                        tickLine={false}
                    />
                    <YAxis
                        type="category"
                        dataKey="group"
                        width={140}
                        tick={{ fill: 'var(--viz-text)', fontSize: 11 }}
                        stroke="var(--viz-axis)"
                        tickLine={false}
                    />
                    <Tooltip
                        cursor={{ fill: 'var(--viz-grid)' }}
                        content={<MarginalTooltipContent language={language} />}
                    />
                    <Bar
                        dataKey="marginal"
                        fill="var(--viz-series-3)"
                        radius={[0, 2, 2, 0]}
                        maxBarSize={18}
                    >
                        {data.map((row, i) => (
                            <Cell
                                key={`marg-cell-${i}`}
                                fill={row.doubtful ? 'var(--viz-series-muted)' : 'var(--viz-series-3)'}
                            />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
            </div>
            <ChartMethodNote
                language={language}
                lead={t(
                    language,
                    'Local slope, normalized to "+100" spend per group so groups are directly comparable.',
                    '局部斜率：每組已依各自步長正規化為「每 +100 元」，可跨組直接比較。'
                )}
                detail={t(
                    language,
                    'Not valid for extrapolation outside the current range; hover a bar for the raw per-group step and value.',
                    '不可線性外推到目前水位之外；每組原始步長與邊際值可從 tooltip 查看。'
                )}
            />
        </div>
    );
};

const DiagnosticsPanel = ({ language, diagnostics, r2, baseShare, dataSummary }) => {
    if (!diagnostics) return null;
    const warnings = diagnostics.collinearity_warnings || [];
    // docs/27 任務 5.3：未分組活動的花費會被丟棄、轉換仍計入 y（維持 y 總和），
    // 分組後新上線的活動會把基線墊高卻無提示——data_summary.ungrouped_spend_share
    // 與 data_quality_warnings 由後端 service._merge_ungrouped_spend_diagnostics 附加。
    const ungroupedSpendShare = dataSummary?.ungrouped_spend_share;
    const dataQualityWarnings = diagnostics.data_quality_warnings || [];
    return (
        <Section
            title={t(language, 'Diagnostics', '診斷')}
            subtitle={t(
                language,
                'Fit quality, collinearity warnings and noise ceiling.',
                '擬合品質、共線性警告與雜訊天花板。'
            )}
        >
            <div
                style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
                    gap: '10px',
                    marginBottom: '14px',
                }}
            >
                <MetricTile
                    label={t(language, 'Holdout R² (median)', 'Holdout R² (中位)')}
                    value={r2?.holdout?.median != null ? fmtNumber(r2.holdout.median, 3) : '--'}
                />
                <MetricTile
                    label={t(language, 'Poisson Ceiling (holdout)', 'Poisson 天花板 (holdout)')}
                    value={diagnostics.poisson_ceiling_r2?.holdout != null
                        ? fmtNumber(diagnostics.poisson_ceiling_r2.holdout, 3)
                        : '--'}
                />
                <MetricTile
                    label={t(language, 'Days of data', '資料天數')}
                    value={dataSummary?.days ?? '--'}
                />
                <MetricTile
                    label={t(language, 'Mean daily conversions', '日均轉換')}
                    value={dataSummary?.mean_daily_conversions != null
                        ? fmtNumber(dataSummary.mean_daily_conversions, 2)
                        : '--'}
                />
                <MetricTile
                    label={t(language, 'Base share (median)', '基線占比 (中位)')}
                    value={baseShare?.median != null ? fmtPct(baseShare.median) : '--'}
                />
                <MetricTile
                    label={t(language, 'Ungrouped spend share', '未分組花費占比')}
                    value={ungroupedSpendShare != null ? fmtPct(ungroupedSpendShare) : '--'}
                />
            </div>

            {dataQualityWarnings.length > 0 && (
                <div
                    style={{
                        padding: '12px 14px',
                        borderRadius: '12px',
                        background: 'rgba(245, 158, 11, 0.07)',
                        border: '1px solid rgba(245, 158, 11, 0.3)',
                        marginBottom: '12px',
                    }}
                >
                    <div style={{ fontWeight: 700, color: '#fbbf24', marginBottom: '6px' }}>
                        {t(language, 'Data Quality Warnings', '資料品質警告')}
                    </div>
                    <ul style={{ margin: 0, paddingLeft: '18px', color: 'var(--text-secondary)', lineHeight: 1.7, fontSize: '0.85rem' }}>
                        {dataQualityWarnings.map((w, idx) => (
                            <li key={`dqw-${idx}`}>{w.message}</li>
                        ))}
                    </ul>
                </div>
            )}

            {warnings.length > 0 && (
                <div
                    style={{
                        padding: '12px 14px',
                        borderRadius: '12px',
                        background: 'rgba(245, 158, 11, 0.07)',
                        border: '1px solid rgba(245, 158, 11, 0.3)',
                        marginBottom: '12px',
                    }}
                >
                    <div style={{ fontWeight: 700, color: '#fbbf24', marginBottom: '6px' }}>
                        {t(language, 'Collinearity Warnings', '共線性警告')}
                    </div>
                    <ul style={{ margin: 0, paddingLeft: '18px', color: 'var(--text-secondary)', lineHeight: 1.7, fontSize: '0.85rem' }}>
                        {warnings.map((w, idx) => (
                            <li key={`cw-${idx}`}>
                                {w.group_a} ↔ {w.group_b} · r = {w.correlation}
                            </li>
                        ))}
                    </ul>
                    <div style={{ marginTop: '6px', color: 'var(--text-secondary)', fontSize: '0.78rem' }}>
                        {t(
                            language,
                            'When two groups move together, attribution is ambiguous. Stagger their budget changes to disentangle effects.',
                            '兩組同時變動時，歸因會不明確。請錯開兩組的預算調整以分辨效果。'
                        )}
                    </div>
                </div>
            )}
        </Section>
    );
};

const MetricTile = ({ label, value }) => (
    <div
        style={{
            padding: '10px 12px',
            borderRadius: '10px',
            border: '1px solid var(--glass-border)',
            background: 'rgba(255,255,255,0.03)',
        }}
    >
        <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>{label}</div>
        <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>{value}</div>
    </div>
);

const buildAiPayload = ({ snapshot, groups, reportedByGroup }) => {
    const results = snapshot?.results || {};
    const diagnostics = snapshot?.diagnostics || {};
    const config = snapshot?.config || {};
    const warnings = diagnostics.collinearity_warnings || [];
    const correlatedPairs = new Set();
    warnings.forEach((w) => {
        correlatedPairs.add(w.group_a);
        correlatedPairs.add(w.group_b);
    });
    const groupsData = results.groups || {};
    const groupRows = (groups || []).map((g) => {
        const data = groupsData[g.group_key] || {};
        const median = data.contribution_share?.median ?? 0;
        return {
            group_key: g.group_key,
            group_name: g.group_name,
            spend_share: data.spend_share ?? 0,
            reported_share: reportedByGroup?.[g.group_key] ?? 0,
            contribution_share_median: median,
            contribution_share_min: data.contribution_share?.min ?? 0,
            contribution_share_max: data.contribution_share?.max ?? 0,
            marginal_per_step_median: data.marginal?.per_step?.median ?? null,
            marginal_step: data.marginal?.step ?? null,
            doubtful: median <= 0.005 && correlatedPairs.has(g.group_key),
        };
    });
    return {
        groups: groupRows,
        diagnostics: {
            collinearity_warnings: warnings,
            // docs/27 任務 5.3：data_summary 內已含 ungrouped_spend_share，
            // 另把 data_quality_warnings（未分組花費等資料品質警告）一併帶上，
            // 讓 AI 白話解讀也能引用（prompt 既有「只引用 payload 內數字」規則已涵蓋）。
            data_quality_warnings: diagnostics.data_quality_warnings || [],
            holdout_r2_median: results.r2?.holdout?.median ?? null,
            poisson_ceiling_r2_holdout: diagnostics.poisson_ceiling_r2?.holdout ?? null,
            data_summary: diagnostics.data_summary || null,
        },
        config: {
            metric_key: config.metric_key || 'omni_purchase',
            n_restarts: config.n_restarts || null,
            holdout_days: config.holdout_days || null,
        },
    };
};

const AiInsightsCard = ({
    language,
    snapshot,
    groups,
    reportedByGroup,
    accountName,
    onAiSummarySaved,
}) => {
    const existing = snapshot?.ai_summary || '';
    const [aiContent, setAiContent] = useState(existing);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [aiError, setAiError] = useState(null);
    // 儲存時需讀取最新串流內容：與 setAiContent 同步雙寫，避免 setState 閉包舊值
    const aiContentRef = useRef(existing);

    // 切換快照時重置內容
    useEffect(() => {
        setAiContent(existing);
        aiContentRef.current = existing;
        setAiError(null);
    }, [snapshot?.snapshot_id, existing]);

    if (!snapshot || snapshot.status !== 'completed' || !snapshot.results) {
        return null;
    }

    const handleGenerate = async () => {
        if (isAnalyzing) return;
        setIsAnalyzing(true);
        setAiError(null);
        setAiContent('');
        aiContentRef.current = '';
        const payload = buildAiPayload({ snapshot, groups, reportedByGroup });
        const accountLabel = accountName || snapshot.account_id;
        const context = t(
            language,
            `Account: ${accountLabel} (${snapshot.account_id}); Period: ${snapshot.date_start} ~ ${snapshot.date_end}; Groups: ${groups.length}.`,
            `帳戶：${accountLabel}（${snapshot.account_id}）· 期間：${snapshot.date_start} ~ ${snapshot.date_end} · 群組數：${groups.length}`
        );
        try {
            await aiService.analyzeDataStream(
                payload,
                context,
                'contribution_analysis',
                null,
                (chunk) => {
                    aiContentRef.current = aiContentRef.current + chunk;
                    setAiContent((prev) => prev + chunk);
                },
                null,
                null,
                'weekly',
                'fb_ads'
            );
        } catch (err) {
            setAiError(
                err?.message ||
                t(language, 'AI analysis failed. Check AI key in settings.', 'AI 解讀失敗，請至設定頁確認 AI 金鑰。')
            );
            setIsAnalyzing(false);
            return;
        }
        setIsAnalyzing(false);

        // 串流完成 → 持久化（讀 ref 確保拿到最新內容，不靠閉包舊值）
        setIsSaving(true);
        try {
            const saved = await saveAiSummary({
                snapshotId: snapshot.snapshot_id,
                aiSummary: aiContentRef.current,
            });
            if (onAiSummarySaved) onAiSummarySaved(saved);
        } catch (err) {
            setAiError(
                err?.message ||
                t(language, 'AI summary generated but failed to save. Retry to persist.', 'AI 解讀已生成但儲存失敗，請重試以持久化。')
            );
        } finally {
            setIsSaving(false);
        }
    };

    const hasContent = aiContent && aiContent.length > 0;
    const buttonLabel = hasContent
        ? t(language, 'Regenerate', '重新解讀')
        : t(language, 'Generate Insights', '開始 AI 解讀');

    return (
        <Section
            title={t(language, 'AI Plain-Language Insights', 'AI 白話解讀')}
            subtitle={t(
                language,
                'Translates the numbers above into a quick read for non-statisticians. Generated by AI; the charts above remain the source of truth.',
                '把上方數字翻成白話文，給不懂統計的主管快速掌握重點。AI 生成，上方圖表仍是事實來源。'
            )}
        >
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '10px' }}>
                <button
                    type="button"
                    onClick={handleGenerate}
                    disabled={isAnalyzing || isSaving}
                    style={{
                        ...secondaryButtonStyle,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        opacity: isAnalyzing || isSaving ? 0.5 : 1,
                    }}
                >
                    {isAnalyzing || isSaving ? <FiRefreshCcw className="spin" /> : <FiCpu />}
                    {isAnalyzing
                        ? t(language, 'Analyzing…', '解讀中…')
                        : isSaving
                            ? t(language, 'Saving…', '儲存中…')
                            : buttonLabel}
                </button>
            </div>

            {aiError && <ErrorPanel message={aiError} />}

            <div
                style={{
                    background: 'rgba(59, 130, 246, 0.05)',
                    border: '1px solid rgba(59, 130, 246, 0.2)',
                    borderRadius: '12px',
                    padding: '20px 22px',
                    minHeight: '100px',
                    color: 'var(--text-primary)',
                    lineHeight: 1.7,
                }}
            >
                {hasContent ? (
                    <div className="report-ai-content">
                        <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            rehypePlugins={[rehypeRaw]}
                        >
                            {aiContent}
                        </ReactMarkdown>
                    </div>
                ) : (
                    <div
                        style={{
                            color: 'var(--text-tertiary)',
                            textAlign: 'center',
                            padding: '20px',
                            fontSize: '0.85rem',
                        }}
                    >
                        {isAnalyzing
                            ? t(language, 'AI is analyzing your data…', 'AI 正在分析您的數據…')
                            : t(
                                language,
                                'No AI summary yet. Click "Generate Insights" to ask AI to translate the results.',
                                '尚無 AI 解讀。點選「開始 AI 解讀」讓 AI 翻譯結果。'
                            )}
                    </div>
                )}
            </div>

            <div
                style={{
                    marginTop: '10px',
                    fontSize: '0.74rem',
                    color: 'var(--text-tertiary)',
                    lineHeight: 1.5,
                }}
            >
                {t(
                    language,
                    'Disclaimer: AI insights are for reference only. The charts and numbers above are the source of truth.',
                    '免責聲明：AI 解讀僅供參考，數字仍以上方圖表為準。'
                )}
            </div>
        </Section>
    );
};

export const GroupEditor = ({
    language,
    campaigns,
    groups,
    editing,
    onEdit,
    onCancel,
    onSave,
    saving,
    saveError,
    onReset,
    resetting,
    resetError,
}) => {
    const campaignsById = useMemo(() => {
        const map = new Map();
        campaigns.forEach((c) => map.set(String(c.campaign_id), c));
        return map;
    }, [campaigns]);

    const draft = editing || groups;

    const allCampaignIds = useMemo(
        () => campaigns.map((c) => String(c.campaign_id)),
        [campaigns]
    );

    const handleMove = (campaignId, targetGroupKey) => {
        const next = (editing || groups).map((g) => ({ ...g, campaign_ids: [...g.campaign_ids] }));
        next.forEach((g) => {
            g.campaign_ids = g.campaign_ids.filter((cid) => cid !== campaignId);
        });
        const target = next.find((g) => g.group_key === targetGroupKey);
        if (target) target.campaign_ids.push(campaignId);
        onEdit(next);
    };

    const handleRename = (groupKey, newName) => {
        const next = (editing || groups).map((g) =>
            g.group_key === groupKey ? { ...g, group_name: newName } : g
        );
        onEdit(next);
    };

    return (
        <Section
            title={t(language, 'Group Editor', '活動分組編輯')}
            subtitle={t(
                language,
                'Move campaigns between groups or rename them, then save. Saved groups become the active set for the next analysis.',
                '拖拉活動到不同組別或重新命名後儲存。儲存後的分組將作為下次分析的主分組。'
            )}
        >
            {saveError && <ErrorPanel message={saveError} />}
            {resetError && <ErrorPanel message={resetError} />}

            {draft.length === 0 && (
                <InfoPanel message={t(language, 'No groups to edit.', '沒有可編輯的分組。')} />
            )}

            <div style={{ display: 'grid', gap: '10px' }}>
                {draft.map((group) => (
                    <div
                        key={group.group_key}
                        style={{
                            padding: '12px 14px',
                            borderRadius: '10px',
                            border: '1px solid var(--glass-border)',
                            background: 'rgba(255,255,255,0.03)',
                        }}
                    >
                        <div
                            style={{
                                display: 'flex',
                                gap: '8px',
                                alignItems: 'center',
                                marginBottom: '8px',
                                flexWrap: 'wrap',
                            }}
                        >
                            <span
                                style={{
                                    fontSize: '0.78rem',
                                    color: 'var(--text-secondary)',
                                    fontWeight: 600,
                                }}
                            >
                                {group.group_key}
                            </span>
                            <input
                                value={group.group_name}
                                onChange={(e) => handleRename(group.group_key, e.target.value)}
                                style={{ ...inputStyle, flex: '1 1 200px' }}
                            />
                            <span
                                style={{
                                    fontSize: '0.72rem',
                                    color: 'var(--text-secondary)',
                                }}
                            >
                                {group.campaign_ids.length} {t(language, 'campaigns', '個活動')}
                            </span>
                        </div>
                        {/* docs/27 任務 4.4：把某組活動全搬走後，明確告知使用者這個
                            空組會在儲存時被移除（handleSaveGroups 送出前已過濾），
                            避免使用者以為卡住、無從得知空組的下場。只在「有未儲存
                            編輯」時顯示——已儲存的分組理論上不會有空組。 */}
                        {editing && group.campaign_ids.length === 0 && (
                            <div
                                style={{
                                    marginBottom: '8px',
                                    padding: '6px 10px',
                                    borderRadius: '8px',
                                    background: 'rgba(245, 158, 11, 0.08)',
                                    border: '1px dashed rgba(245, 158, 11, 0.35)',
                                    color: '#fbbf24',
                                    fontSize: '0.74rem',
                                }}
                            >
                                {t(
                                    language,
                                    'This group has no campaigns left and will be removed when you save.',
                                    '此組已無任何活動，將於儲存時移除。'
                                )}
                            </div>
                        )}
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                            {group.campaign_ids.length === 0 && !editing && (
                                <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                                    {t(language, 'No campaigns.', '無活動。')}
                                </span>
                            )}
                            {group.campaign_ids.map((cid) => {
                                const campaign = campaignsById.get(String(cid));
                                return (
                                    <div
                                        key={`${group.group_key}-${cid}`}
                                        style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '4px',
                                            padding: '4px 8px',
                                            borderRadius: '999px',
                                            background: 'rgba(59, 130, 246, 0.12)',
                                            color: '#93c5fd',
                                            fontSize: '0.78rem',
                                        }}
                                    >
                                        <span title={campaign?.campaign_name || cid}>
                                            {campaign?.campaign_name || cid}
                                        </span>
                                        <select
                                            value={group.group_key}
                                            onChange={(e) => handleMove(cid, e.target.value)}
                                            style={{
                                                background: 'transparent',
                                                border: 'none',
                                                color: '#bfdbfe',
                                                fontSize: '0.72rem',
                                                cursor: 'pointer',
                                            }}
                                        >
                                            {draft.map((g) => (
                                                <option key={g.group_key} value={g.group_key}>
                                                    → {g.group_key}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                ))}
            </div>

            {allCampaignIds.length > 0 && (
                <div
                    style={{
                        marginTop: '12px',
                        fontSize: '0.78rem',
                        color: 'var(--text-secondary)',
                    }}
                >
                    {t(
                        language,
                        'Hint: use the small selector on each campaign chip to move it to another group. Rerun analysis afterwards.',
                        '提示：點選活動徽章上的小選擇器即可移到其他組別，之後再重跑分析。'
                    )}
                </div>
            )}

            <div style={{ marginTop: '14px', display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                <button
                    type="button"
                    onClick={onReset}
                    disabled={resetting || saving}
                    title={t(
                        language,
                        'Clear current groups (including manual edits) and regenerate with the latest auto-grouping rules.',
                        '清除目前分組（含手動編輯）並以最新的自動分組規則重新產生。'
                    )}
                    style={{
                        ...secondaryButtonStyle,
                        marginRight: 'auto',
                        opacity: resetting || saving ? 0.5 : 1,
                    }}
                >
                    {resetting
                        ? t(language, 'Resetting…', '重設中…')
                        : t(language, 'Reset to Auto', '重設為自動分組')}
                </button>
                {editing && (
                    <button type="button" onClick={onCancel} style={secondaryButtonStyle}>
                        {t(language, 'Cancel', '取消')}
                    </button>
                )}
                <button
                    type="button"
                    onClick={onSave}
                    disabled={!editing || saving}
                    style={{
                        ...primaryButtonStyle,
                        opacity: !editing || saving ? 0.5 : 1,
                    }}
                >
                    {saving
                        ? t(language, 'Saving…', '儲存中…')
                        : t(language, 'Save Groups', '儲存分組')}
                </button>
            </div>
        </Section>
    );
};

export const HistoryList = ({ language, history, loading, onSelect, onRefresh, selectedId, isMobile }) => {
    return (
        <Section
            title={t(language, 'Analysis History', '歷史分析快照')}
            subtitle={t(
                language,
                'Past analyses for this account. Click to load a snapshot.',
                '此帳戶的歷次分析。點選以載入快照。'
            )}
        >
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '8px' }}>
                <button type="button" onClick={onRefresh} style={secondaryButtonStyle}>
                    {t(language, 'Refresh', '重新整理')}
                </button>
            </div>
            {loading ? (
                <InfoPanel message={t(language, 'Loading history…', '載入歷史中…')} />
            ) : history.length === 0 ? (
                <InfoPanel message={t(language, 'No analysis yet.', '尚無分析紀錄。')} />
            ) : (
                <div style={{ display: 'grid', gap: '8px' }}>
                    {history.map((row) => {
                        const isSelected = row.snapshot_id === selectedId;
                        const statusColor = {
                            completed: '#10b981',
                            processing: '#f59e0b',
                            queued: '#3b82f6',
                            failed: '#ef4444',
                        }[row.status] || '#9ca3af';
                        return (
                            <button
                                key={row.snapshot_id}
                                type="button"
                                onClick={() => onSelect(row.snapshot_id)}
                                style={{
                                    textAlign: 'left',
                                    padding: '10px 12px',
                                    borderRadius: '10px',
                                    border: `1px solid ${isSelected ? 'var(--accent-primary)' : 'var(--glass-border)'}`,
                                    background: isSelected ? 'rgba(45, 136, 255, 0.08)' : 'rgba(255,255,255,0.02)',
                                    color: 'var(--text-primary)',
                                    cursor: 'pointer',
                                    fontSize: '0.82rem',
                                }}
                            >
                                <div
                                    style={{
                                        display: 'flex',
                                        justifyContent: 'space-between',
                                        gap: '8px',
                                        alignItems: 'center',
                                        flexWrap: isMobile ? 'wrap' : 'nowrap',
                                    }}
                                >
                                    <div>
                                        <div style={{ fontWeight: 600 }}>
                                            {row.date_start} ~ {row.date_end}
                                        </div>
                                        <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                                            {row.snapshot_id}
                                        </div>
                                    </div>
                                    <div
                                        style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '6px',
                                            color: statusColor,
                                            fontWeight: 600,
                                            fontSize: '0.78rem',
                                        }}
                                    >
                                        <span
                                            style={{
                                                width: '8px',
                                                height: '8px',
                                                borderRadius: '50%',
                                                background: statusColor,
                                            }}
                                        />
                                        {row.status}
                                    </div>
                                </div>
                                {row.error_message && (
                                    <div
                                        style={{
                                            marginTop: '4px',
                                            color: '#fca5a5',
                                            fontSize: '0.72rem',
                                            whiteSpace: 'pre-wrap',
                                        }}
                                    >
                                        {row.error_message}
                                    </div>
                                )}
                            </button>
                        );
                    })}
                </div>
            )}
        </Section>
    );
};

export const AnalysisView = ({ language, isMobile, snapshot, groups, reportedByGroup, marginalCurrency, accountName, onAiSummarySaved }) => {
    const results = snapshot?.results || null;
    const diagnostics = snapshot?.diagnostics || null;

    // docs/27 任務 4.1：歷史快照應以「分析當時的分組」渲染，不是頁面目前的
    // groups state——使用者改組後點開舊快照，用當前 groups 對不上會顯示 0
    // 或缺組。snapshot.config.group_snapshot 是 create_analysis 當下寫入的
    // 分組快照（service._group_to_dict，形狀與 groups state 相同：
    // group_key/group_name/campaign_ids/source）；理論上自任務 1.4 起每筆
    // snapshot 都會有此欄位，缺欄位時仍安全退回目前 groups。
    const effectiveGroups = snapshot?.config?.group_snapshot ?? groups;

    const rows = useMemo(() => {
        if (!results || !effectiveGroups.length) return [];
        const warnings = diagnostics?.collinearity_warnings || [];
        const correlatedPairs = new Set();
        warnings.forEach((w) => {
            correlatedPairs.add(w.group_a);
            correlatedPairs.add(w.group_b);
        });
        const groupsData = results.groups || {};
        return effectiveGroups.map((g) => {
            const data = groupsData[g.group_key] || {};
            const median = data.contribution_share?.median ?? 0;
            const doubtful = median <= 0.005 && correlatedPairs.has(g.group_key);
            return {
                groupKey: g.group_key,
                label: `${g.group_key} · ${g.group_name}`,
                spendShare: data.spend_share,
                reportedShare: reportedByGroup[g.group_key] || 0,
                contributionShare: data.contribution_share,
                marginalPerStep: data.marginal?.per_step,
                // docs/27 任務 4.3：邊際步長是各組依自己日均花費各自計算的
                // （engine.resolve_marginal_step），不是全帳戶統一的單一值。
                // 每列需帶自己的 step 才能正確標示「+N 元」。
                marginalStepValue: data.marginal?.step ?? null,
                doubtful,
            };
        });
    }, [results, effectiveGroups, diagnostics, reportedByGroup]);

    if (snapshot?.status !== 'completed' || !results) {
        return null;
    }

    return (
        <div style={{ display: 'grid', gap: '16px' }}>
            <Section
                title={t(language, 'Contribution Comparison', '貢獻對比')}
                subtitle={t(
                    language,
                    'Spend share vs. platform-reported share vs. MMM contribution. Doubtful groups are grayed out.',
                    '花費占比 vs 自報占比 vs MMM 貢獻。標「存疑」的組別以灰階呈現。'
                )}
            >
                <ContributionChart language={language} rows={rows} isMobile={isMobile} />
                <ContributionTable
                    language={language}
                    rows={rows}
                    marginalCurrency={marginalCurrency}
                />
            </Section>

            <Section
                title={t(language, 'Marginal ROI Ranking', '邊際報酬排序')}
                subtitle={t(
                    language,
                    'Higher = more incremental conversions per +100 spend at the current spend level (normalized across groups).',
                    '數值越高代表在目前花費水位附近，每 +100 元帶來的增量轉換越多（已跨組正規化）。'
                )}
            >
                <MarginalChart
                    language={language}
                    rows={rows}
                    marginalCurrency={marginalCurrency}
                    isMobile={isMobile}
                />
            </Section>

            <DiagnosticsPanel
                language={language}
                diagnostics={diagnostics}
                r2={results.r2}
                baseShare={results.base_share}
                dataSummary={diagnostics?.data_summary}
            />

            <AiInsightsCard
                language={language}
                snapshot={snapshot}
                groups={effectiveGroups}
                reportedByGroup={reportedByGroup}
                accountName={accountName}
                onAiSummarySaved={onAiSummarySaved}
            />
        </div>
    );
};

const selectStyle = {
    width: '100%',
    padding: '9px 12px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.05)',
    color: 'var(--text-primary)',
    fontSize: '0.85rem',
    boxSizing: 'border-box',
};

const inputStyle = {
    padding: '8px 12px',
    borderRadius: '8px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.05)',
    color: 'var(--text-primary)',
    fontSize: '0.85rem',
    boxSizing: 'border-box',
};

const thStyle = {
    padding: '10px 12px',
    fontWeight: 700,
    color: 'var(--text-secondary)',
    fontSize: '0.75rem',
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
};

const tdStyle = {
    padding: '10px 12px',
    color: 'var(--text-primary)',
};

const primaryButtonStyle = {
    padding: '10px 18px',
    borderRadius: '10px',
    border: 'none',
    background: 'var(--accent-primary)',
    color: 'white',
    fontWeight: 600,
    fontSize: '0.85rem',
    cursor: 'pointer',
    transition: 'all 0.2s',
};

const secondaryButtonStyle = {
    padding: '10px 18px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.05)',
    color: 'var(--text-primary)',
    fontWeight: 600,
    fontSize: '0.85rem',
    cursor: 'pointer',
    transition: 'all 0.2s',
};

