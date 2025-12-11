import React from 'react';

const KPICard = ({ title, value, sub_value, diff, percent, is_increase, is_inverse }) => {
    // 1. Determine "Good" or "Bad" trend
    // Inverse metrics (Spend, CPC): Increase is BAD (Red), Decrease is GOOD (Green)
    // Normal metrics (ROAS, Purchase): Increase is GOOD (Green), Decrease is BAD (Red)
    const isGood = is_inverse ? !is_increase : is_increase;

    // 2. Select Color
    const color = isGood ? '#4ade80' : '#f87171';

    // 3. Arrow Symbol
    const arrow = is_increase ? '▲' : '▼';

    return (
        <div className="glass-panel" style={{
            padding: '20px',
            borderRadius: 'var(--radius-lg)',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
            transition: 'transform 0.2s ease, box-shadow 0.2s ease',
            cursor: 'default',
            minHeight: '120px',
            justifyContent: 'center'
        }}
            onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = 'var(--shadow-md)';
                e.currentTarget.style.borderColor = 'rgba(45, 136, 255, 0.3)';
            }}
            onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'var(--shadow-sm)';
                e.currentTarget.style.borderColor = 'var(--glass-border)';
            }}
        >
            {/* Title */}
            <h3 style={{
                fontSize: '0.85rem',
                color: 'var(--text-secondary)',
                fontWeight: 600,
                marginBottom: '4px'
            }}>
                {title}
            </h3>

            {/* Value Row: Current + (Previous) */}
            <div style={{
                display: 'flex',
                alignItems: 'baseline',
                gap: '8px'
            }}>
                <div style={{
                    fontSize: '1.6rem',
                    fontWeight: 700,
                    letterSpacing: '-0.5px',
                    color: 'var(--text-primary)'
                }}>
                    {value}
                </div>
                <div style={{
                    fontSize: '0.9rem',
                    color: 'var(--text-tertiary)',
                    fontWeight: 400
                }}>
                    {sub_value}
                </div>
            </div>

            {/* Change Row: Arrow Diff (Percent) */}
            {diff && (
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    color: color
                }}>
                    <span>{arrow} {diff} ({percent})</span>
                </div>
            )}
        </div>
    );
};

export default KPICard;
