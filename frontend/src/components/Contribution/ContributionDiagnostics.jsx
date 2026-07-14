import React from 'react';

import { fmtNumber, fmtPct, Section, t } from './ContributionShared';

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

export default DiagnosticsPanel;
