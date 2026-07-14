/* eslint-disable react-refresh/only-export-components */
import React from 'react';

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

export const fmtPct = (value, digits = 1) => {
    if (value == null || Number.isNaN(value)) return '--';
    return `${(value * 100).toFixed(digits)}%`;
};

export const fmtNumber = (value, digits = 2) => {
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

export const groupRowHasCampaigns = (group) => Array.isArray(group.campaign_ids) && group.campaign_ids.length > 0;

export const SelfDoubtfulBadge = ({ isDoubtful, language }) => {
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

export const selectStyle = {
    width: '100%',
    padding: '9px 12px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.05)',
    color: 'var(--text-primary)',
    fontSize: '0.85rem',
    boxSizing: 'border-box',
};

export const inputStyle = {
    padding: '8px 12px',
    borderRadius: '8px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.05)',
    color: 'var(--text-primary)',
    fontSize: '0.85rem',
    boxSizing: 'border-box',
};

export const thStyle = {
    padding: '10px 12px',
    fontWeight: 700,
    color: 'var(--text-secondary)',
    fontSize: '0.75rem',
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
};

export const tdStyle = {
    padding: '10px 12px',
    color: 'var(--text-primary)',
};

export const primaryButtonStyle = {
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

export const secondaryButtonStyle = {
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
