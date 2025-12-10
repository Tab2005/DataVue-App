import React from 'react';

const KPICard = ({ title, value, sub_value, change, isPositive }) => {
    return (
        <div className="glass-panel" style={{
            padding: '20px',
            borderRadius: 'var(--radius-lg)', // Slightly smaller radius for grid items
            display: 'flex',
            flexDirection: 'column',
            gap: '4px',
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
            <h3 style={{
                fontSize: '0.85rem',
                color: 'var(--text-secondary)',
                fontWeight: 600,
                marginBottom: '4px'
            }}>
                {title}
            </h3>

            <div style={{
                fontSize: '1.5rem',
                fontWeight: 700,
                letterSpacing: '-0.5px',
                color: 'var(--text-primary)'
            }}>
                {value}
            </div>

            <div style={{
                display: 'flex',
                alignItems: 'baseline',
                gap: '8px',
                fontSize: '0.75rem',
                marginTop: '4px'
            }}>
                <span style={{
                    color: 'var(--text-tertiary)',
                    fontWeight: 400
                }}>
                    {sub_value}
                </span>

                <span style={{
                    color: isPositive ? '#4ade80' : '#f87171',
                    fontWeight: 600
                }}>
                    {change}
                </span>
            </div>
        </div>
    );
};

export default KPICard;
