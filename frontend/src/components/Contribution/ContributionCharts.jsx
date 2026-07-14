import React from 'react';
import { FiInfo } from 'react-icons/fi';
import {
    Bar,
    BarChart,
    CartesianGrid,
    Cell,
    Legend,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from 'recharts';

import {
    fmtNumber,
    fmtPct,
    InfoPanel,
    SelfDoubtfulBadge,
    t,
    tdStyle,
    thStyle,
} from './ContributionShared';

const ChartMethodNote = ({ lead, detail }) => (
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

export const ContributionChart = ({ language, rows, isMobile }) => {
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

export const ContributionTable = ({ language, rows, marginalCurrency }) => {
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

export const MarginalChart = ({ language, rows, isMobile }) => {
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
