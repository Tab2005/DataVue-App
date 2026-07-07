import React, { useEffect, useMemo, useState, useCallback, useRef } from 'react';
import { useOutletContext } from 'react-router-dom';
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

import { useModuleAccess } from '../hooks/usePermission';
import {
    createAnalysis,
    getAnalysis,
    getGroups,
    listAnalyses,
    listCampaignSummaries,
    refreshContributionData,
    updateGroups,
} from '../services/contributionService';

const DEFAULT_PERIOD_DAYS = 180;
const POLL_INTERVAL_MS = 2000;

const t = (language, en, zh) => (language === 'en' ? en : zh);

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

const computePeriod = (days) => {
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

const Section = ({ title, subtitle, children, style }) => (
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

const ErrorPanel = ({ message }) => (
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

const InfoPanel = ({ message, tone = 'info' }) => {
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

const AccountAndPeriod = ({
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
}) => {
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
    return (
        <div style={{ width: '100%', height: isMobile ? 320 : 380 }}>
            <ResponsiveContainer>
                <BarChart
                    data={data}
                    layout="vertical"
                    margin={{ top: 8, right: 24, left: 16, bottom: 8 }}
                >
                    <CartesianGrid stroke="rgba(255,255,255,0.05)" strokeDasharray="3 3" />
                    <XAxis
                        type="number"
                        domain={[0, 'dataMax']}
                        tickFormatter={(v) => `${Math.round(v * 100)}%`}
                        tick={{ fill: 'var(--text-secondary)', fontSize: 11 }}
                    />
                    <YAxis
                        type="category"
                        dataKey="group"
                        width={120}
                        tick={{ fill: 'var(--text-secondary)', fontSize: 11 }}
                    />
                    <Tooltip
                        formatter={(v) => `${(v * 100).toFixed(1)}%`}
                        contentStyle={{
                            background: 'var(--bg-secondary)',
                            border: '1px solid var(--glass-border)',
                            borderRadius: '8px',
                            color: 'var(--text-primary)',
                            fontSize: '0.8rem',
                        }}
                    />
                    <Legend wrapperStyle={{ color: 'var(--text-secondary)', fontSize: '0.78rem' }} />
                    <Bar
                        dataKey="spend"
                        name={t(language, 'Spend Share', '花費占比')}
                        fill="#64748b"
                        radius={[2, 2, 2, 2]}
                    />
                    <Bar
                        dataKey="reported"
                        name={t(language, 'Platform-Reported', '自報占比')}
                        fill="#3b82f6"
                        radius={[2, 2, 2, 2]}
                    />
                    <Bar
                        dataKey="mmm"
                        name={t(language, 'MMM Contribution', 'MMM 貢獻 (中位)')}
                        fill="#10b981"
                        radius={[2, 2, 2, 2]}
                    >
                        {data.map((row, i) => (
                            <Cell key={`cell-${i}`} fill={row.doubtful ? '#6b7280' : '#10b981'} />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
            <div
                style={{
                    marginTop: '6px',
                    color: 'var(--text-secondary)',
                    fontSize: '0.74rem',
                    lineHeight: 1.5,
                }}
            >
                {t(
                    language,
                    'MMM contribution is shown as the median across restarts; range (min–max) is reported per row below.',
                    'MMM 貢獻以多次重啟的中位數呈現；每組的 min–max 範圍列於下方表格。'
                )}
            </div>
        </div>
    );
};

const ContributionTable = ({ language, rows, marginalStep, marginalCurrency }) => {
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
                            {t(language, `Marginal / +${marginalStep}${marginalCurrency}`, `邊際 / +${marginalStep}${marginalCurrency}`)}
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
                                {row.marginalPerStep?.median != null
                                    ? `+${fmtNumber(row.marginalPerStep.median, 2)}`
                                    : '--'}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

const MarginalChart = ({ language, rows, marginalStep, marginalCurrency, isMobile }) => {
    if (!rows.length) return null;
    const data = rows
        .filter((row) => row.marginalPerStep?.median != null)
        .map((row) => ({
            group: row.label,
            marginal: row.marginalPerStep.median,
            doubtful: row.doubtful,
        }));
    if (!data.length) {
        return <InfoPanel message={t(language, 'No marginal data.', '無邊際資料。')} />;
    }
    return (
        <div style={{ width: '100%', height: isMobile ? 240 : 280 }}>
            <ResponsiveContainer>
                <BarChart data={data} margin={{ top: 8, right: 16, left: 8, bottom: 24 }}>
                    <CartesianGrid stroke="rgba(255,255,255,0.05)" strokeDasharray="3 3" />
                    <XAxis
                        dataKey="group"
                        tick={{ fill: 'var(--text-secondary)', fontSize: 10 }}
                        angle={isMobile ? -25 : 0}
                        textAnchor={isMobile ? 'end' : 'middle'}
                        height={isMobile ? 60 : 30}
                    />
                    <YAxis
                        tick={{ fill: 'var(--text-secondary)', fontSize: 11 }}
                        tickFormatter={(v) => `+${v.toFixed(2)}`}
                    />
                    <Tooltip
                        formatter={(v) => `+${Number(v).toFixed(2)} ${t(language, 'conversions', '轉換')}`}
                        contentStyle={{
                            background: 'var(--bg-secondary)',
                            border: '1px solid var(--glass-border)',
                            borderRadius: '8px',
                            color: 'var(--text-primary)',
                            fontSize: '0.8rem',
                        }}
                    />
                    <Bar dataKey="marginal" radius={[4, 4, 0, 0]} fill="#22c55e">
                        {data.map((row, i) => (
                            <Cell key={`marg-cell-${i}`} fill={row.doubtful ? '#6b7280' : '#22c55e'} />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
            <div
                style={{
                    marginTop: '6px',
                    color: 'var(--text-secondary)',
                    fontSize: '0.74rem',
                    lineHeight: 1.5,
                }}
            >
                {t(
                    language,
                    'Local slope: estimated additional conversions from +N spend at the current spend level. Not valid for extrapolation outside the current range.',
                    '局部斜率：在目前花費水位附近，投入 +N 元的預估邊際轉換。不可線性外推到目前水位之外。'
                )}
            </div>
        </div>
    );
};

const DiagnosticsPanel = ({ language, diagnostics, r2, baseShare, dataSummary }) => {
    if (!diagnostics) return null;
    const warnings = diagnostics.collinearity_warnings || [];
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
            </div>

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

const GroupEditor = ({
    language,
    campaigns,
    groups,
    editing,
    onEdit,
    onCancel,
    onSave,
    saving,
    saveError,
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
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                            {group.campaign_ids.length === 0 && (
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

const HistoryList = ({ language, history, loading, onSelect, onRefresh, selectedId, isMobile }) => {
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

const AnalysisView = ({ language, isMobile, snapshot, groups, reportedByGroup, marginalStep, marginalCurrency }) => {
    const results = snapshot?.results || null;
    const diagnostics = snapshot?.diagnostics || null;

    const rows = useMemo(() => {
        if (!results || !groups.length) return [];
        const warnings = diagnostics?.collinearity_warnings || [];
        const correlatedPairs = new Set();
        warnings.forEach((w) => {
            correlatedPairs.add(w.group_a);
            correlatedPairs.add(w.group_b);
        });
        const groupsData = results.groups || {};
        return groups.map((g) => {
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
                doubtful,
            };
        });
    }, [results, groups, diagnostics, reportedByGroup]);

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
                    marginalStep={marginalStep}
                    marginalCurrency={marginalCurrency}
                />
            </Section>

            <Section
                title={t(language, 'Marginal ROI Ranking', '邊際報酬排序')}
                subtitle={t(
                    language,
                    'Higher = more incremental conversions per +N spend at the current spend level.',
                    '數值越高代表在目前花費水位附近，每 +N 元帶來的增量轉換越多。'
                )}
            >
                <MarginalChart
                    language={language}
                    rows={rows}
                    marginalStep={marginalStep}
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

const useAdAccountList = (teamId) => {
    const [accounts, setAccounts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    useEffect(() => {
        let cancelled = false;
        const load = async () => {
            setLoading(true);
            try {
                const mod = await import('../services/teamService');
                const res = await mod.TeamService.getAllAdAccounts(teamId);
                if (cancelled) return;
                setAccounts(res || []);
            } catch (err) {
                if (cancelled) return;
                setError(err.message || '載入帳戶失敗');
            } finally {
                if (!cancelled) setLoading(false);
            }
        };
        load();
        return () => {
            cancelled = true;
        };
    }, [teamId]);
    return { accounts, loading, error };
};

const ContributionAnalysis = () => {
    const { isMobile, language, selectedTeamId } = useOutletContext();
    const { hasAccess, loading: accessLoading } = useModuleAccess('contribution', selectedTeamId);
    const { accounts, loading: loadingAccounts } = useAdAccountList(selectedTeamId);

    const [accountId, setAccountId] = useState('');
    const [periodDays, setPeriodDays] = useState(DEFAULT_PERIOD_DAYS);
    const [campaigns, setCampaigns] = useState([]);
    const [groups, setGroups] = useState([]);
    const [editingGroups, setEditingGroups] = useState(null);
    const [savingGroups, setSavingGroups] = useState(false);
    const [groupSaveError, setGroupSaveError] = useState(null);
    const [refreshing, setRefreshing] = useState(false);
    const [refreshingError, setRefreshingError] = useState(null);
    const [submitting, setSubmitting] = useState(false);
    const [submitError, setSubmitError] = useState(null);
    const [activeSnapshot, setActiveSnapshot] = useState(null);
    const [polling, setPolling] = useState(false);
    const [history, setHistory] = useState([]);
    const [loadingHistory, setLoadingHistory] = useState(false);
    const [pageError, setPageError] = useState(null);
    const pollRef = useRef(null);

    // 預設選單一帳戶
    useEffect(() => {
        if (!accountId && accounts.length === 1) {
            setAccountId(accounts[0].id);
        }
    }, [accounts, accountId]);

    const loadCampaigns = useCallback(async (acct) => {
        if (!acct) {
            setCampaigns([]);
            return;
        }
        try {
            const res = await listCampaignSummaries({ accountId: acct });
            setCampaigns(res.campaigns || []);
        } catch (err) {
            console.error('listCampaignSummaries failed', err);
            setCampaigns([]);
        }
    }, []);

    const loadGroups = useCallback(async (acct) => {
        if (!acct) {
            setGroups([]);
            return;
        }
        try {
            const res = await getGroups({ accountId: acct });
            setGroups(res.groups || []);
        } catch (err) {
            console.error('getGroups failed', err);
            setGroups([]);
        }
    }, []);

    const loadHistory = useCallback(async (acct) => {
        if (!acct) {
            setHistory([]);
            return;
        }
        setLoadingHistory(true);
        try {
            const res = await listAnalyses({ accountId: acct, page: 1, pageSize: 20 });
            setHistory(res.analyses || []);
        } catch (err) {
            console.error('listAnalyses failed', err);
            setHistory([]);
        } finally {
            setLoadingHistory(false);
        }
    }, []);

    useEffect(() => {
        if (!accountId) {
            setActiveSnapshot(null);
            return;
        }
        loadCampaigns(accountId);
        loadGroups(accountId);
        loadHistory(accountId);
    }, [accountId, loadCampaigns, loadGroups, loadHistory]);

    // 輪詢 active snapshot
    useEffect(() => {
        if (!activeSnapshot || activeSnapshot.status === 'completed' || activeSnapshot.status === 'failed') {
            if (pollRef.current) {
                clearInterval(pollRef.current);
                pollRef.current = null;
            }
            setPolling(false);
            return;
        }
        setPolling(true);
        pollRef.current = setInterval(async () => {
            try {
                const next = await getAnalysis(activeSnapshot.snapshot_id);
                setActiveSnapshot(next);
                if (next.status === 'completed' || next.status === 'failed') {
                    clearInterval(pollRef.current);
                    pollRef.current = null;
                    setPolling(false);
                    if (next.status === 'completed') {
                        loadHistory(accountId);
                    }
                }
            } catch (err) {
                console.error('poll getAnalysis failed', err);
            }
        }, POLL_INTERVAL_MS);
        return () => {
            if (pollRef.current) {
                clearInterval(pollRef.current);
                pollRef.current = null;
            }
        };
    }, [activeSnapshot, accountId, loadHistory]);

    useEffect(() => () => {
        if (pollRef.current) clearInterval(pollRef.current);
    }, []);

    const handleRefreshData = async () => {
        if (!accountId) return;
        setRefreshing(true);
        setRefreshingError(null);
        try {
            await refreshContributionData({ accountId });
            // 等待 1.5s 後重抓快取（背景抓取已排入）
            setTimeout(async () => {
                await loadCampaigns(accountId);
                setRefreshing(false);
            }, 1500);
        } catch (err) {
            setRefreshingError(err.message);
            setRefreshing(false);
        }
    };

    const handleSubmitAnalysis = async () => {
        if (!accountId) return;
        setSubmitting(true);
        setSubmitError(null);
        setPageError(null);
        const { dateStart, dateEnd } = computePeriod(periodDays);
        try {
            const res = await createAnalysis({
                accountId,
                dateStart,
                dateEnd,
            });
            setActiveSnapshot({
                snapshot_id: res.snapshot_id,
                status: res.status,
                account_id: res.account_id,
                date_start: dateStart,
                date_end: dateEnd,
            });
            await loadHistory(accountId);
        } catch (err) {
            if (err.statusCode === 422) {
                setSubmitError(err.message);
            } else {
                setPageError(err.message || '分析啟動失敗');
            }
        } finally {
            setSubmitting(false);
        }
    };

    const handleSelectSnapshot = async (snapshotId) => {
        try {
            const next = await getAnalysis(snapshotId);
            setActiveSnapshot(next);
        } catch (err) {
            setPageError(err.message || '載入快照失敗');
        }
    };

    const handleEditGroups = (next) => {
        setGroupSaveError(null);
        setEditingGroups(next);
    };

    const handleCancelEdit = () => {
        setEditingGroups(null);
        setGroupSaveError(null);
    };

    const handleSaveGroups = async () => {
        if (!editingGroups || !accountId) return;
        setSavingGroups(true);
        setGroupSaveError(null);
        try {
            await updateGroups({ accountId, groups: editingGroups });
            await loadGroups(accountId);
            setEditingGroups(null);
        } catch (err) {
            setGroupSaveError(err.message);
        } finally {
            setSavingGroups(false);
        }
    };

    const reportedByGroup = useMemo(() => {
        if (!campaigns.length) return {};
        const cidToGroup = new Map();
        groups.forEach((g) => {
            (g.campaign_ids || []).forEach((cid) => cidToGroup.set(String(cid), g.group_key));
        });
        let totalConversions = 0;
        const groupConversions = {};
        campaigns.forEach((c) => {
            const conv = Number(c.conversions || 0);
            const gk = cidToGroup.get(String(c.campaign_id));
            if (!gk) return;
            totalConversions += conv;
            groupConversions[gk] = (groupConversions[gk] || 0) + conv;
        });
        const out = {};
        if (totalConversions > 0) {
            Object.entries(groupConversions).forEach(([gk, conv]) => {
                out[gk] = conv / totalConversions;
            });
        }
        return out;
    }, [campaigns, groups]);

    const marginalStep = activeSnapshot?.results?.groups?.[Object.keys(activeSnapshot.results.groups)[0]]?.marginal?.step;
    const marginalCurrency = ''; // 未來可由帳戶 metadata 取得

    if (accessLoading) {
        return (
            <div style={{ padding: isMobile ? '16px' : '24px' }}>
                <Section title={t(language, 'Contribution Analysis', '貢獻分析')}>
                    <InfoPanel message={t(language, 'Checking workspace access…', '正在確認工作區模組權限…')} />
                </Section>
            </div>
        );
    }

    if (!hasAccess) {
        return (
            <div style={{ padding: isMobile ? '16px' : '24px' }}>
                <Section title={t(language, 'Contribution Analysis', '貢獻分析')}>
                    <InfoPanel
                        message={t(
                            language,
                            'You do not have access to Contribution Analysis in this workspace.',
                            '此工作區無「貢獻分析」模組存取權限，請聯絡管理員開通。'
                        )}
                        tone="info"
                    />
                </Section>
            </div>
        );
    }

    const canSubmit = Boolean(accountId) && (groups.length > 0 || editingGroups);

    return (
        <div style={{ padding: isMobile ? '16px' : '24px' }}>
            <div
                style={{
                    marginBottom: '20px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: isMobile ? 'flex-start' : 'center',
                    flexDirection: isMobile ? 'column' : 'row',
                    gap: '12px',
                }}
            >
                <div>
                    <div style={{ color: 'var(--accent-primary)', fontWeight: 700, marginBottom: '8px' }}>
                        {t(language, 'Contribution Analysis', '貢獻分析')}
                    </div>
                    <h1 style={{ margin: 0, color: 'var(--text-primary)' }}>
                        {t(language, 'MMM Contribution Explorer', 'MMM 活動貢獻分析')}
                    </h1>
                </div>
            </div>

            {pageError && <ErrorPanel message={pageError} />}
            {submitError && <ErrorPanel message={submitError} />}

            <div style={{ display: 'grid', gap: '16px' }}>
                <AccountAndPeriod
                    language={language}
                    isMobile={isMobile}
                    accountId={accountId}
                    onAccountChange={(v) => {
                        setActiveSnapshot(null);
                        setAccountId(v);
                    }}
                    onRefreshCampaigns={handleRefreshData}
                    refreshing={refreshing}
                    campaignsCount={campaigns.length}
                    periodDays={periodDays}
                    onPeriodChange={setPeriodDays}
                    onSubmit={handleSubmitAnalysis}
                    submitting={submitting || polling}
                    canSubmit={canSubmit}
                    accountList={accounts}
                    loadingAccounts={loadingAccounts}
                />

                {refreshingError && <ErrorPanel message={refreshingError} />}

                {!accountId && (
                    <InfoPanel
                        message={t(
                            language,
                            'Select an ad account to start.',
                            '請選擇一個廣告帳戶開始使用。'
                        )}
                    />
                )}

                {accountId && campaigns.length === 0 && (
                    <InfoPanel
                        message={t(
                            language,
                            'No cached campaigns for this account. Click "Refresh Data" to fetch from Meta.',
                            '此帳戶快取中尚無活動資料，請按「抓取資料」從 Meta 拉取。'
                        )}
                    />
                )}

                {accountId && (
                    <GroupEditor
                        language={language}
                        campaigns={campaigns}
                        groups={groups}
                        editing={editingGroups}
                        onEdit={handleEditGroups}
                        onCancel={handleCancelEdit}
                        onSave={handleSaveGroups}
                        saving={savingGroups}
                        saveError={groupSaveError}
                    />
                )}

                {activeSnapshot && (
                    <Section
                        title={t(language, 'Latest Analysis', '最新分析')}
                        subtitle={
                            activeSnapshot.status === 'completed'
                                ? t(language, `Period: ${activeSnapshot.date_start} ~ ${activeSnapshot.date_end}`, `區間：${activeSnapshot.date_start} ~ ${activeSnapshot.date_end}`)
                                : t(language, `Snapshot ${activeSnapshot.snapshot_id} · ${activeSnapshot.status}`, `快照 ${activeSnapshot.snapshot_id} · ${activeSnapshot.status}`)
                        }
                    >
                        {activeSnapshot.status === 'failed' && (
                            <ErrorPanel message={activeSnapshot.error_message || '分析失敗'} />
                        )}
                        {(activeSnapshot.status === 'queued' || activeSnapshot.status === 'processing') && (
                            <InfoPanel message={t(language, 'Analysis is running, please wait…', '分析執行中，請稍候…')} />
                        )}
                        <AnalysisView
                            language={language}
                            isMobile={isMobile}
                            snapshot={activeSnapshot}
                            groups={groups}
                            reportedByGroup={reportedByGroup}
                            marginalStep={marginalStep}
                            marginalCurrency={marginalCurrency}
                        />
                    </Section>
                )}

                {accountId && (
                    <HistoryList
                        language={language}
                        history={history}
                        loading={loadingHistory}
                        onSelect={handleSelectSnapshot}
                        onRefresh={() => loadHistory(accountId)}
                        selectedId={activeSnapshot?.snapshot_id}
                        isMobile={isMobile}
                    />
                )}
            </div>
        </div>
    );
};

export default ContributionAnalysis;
