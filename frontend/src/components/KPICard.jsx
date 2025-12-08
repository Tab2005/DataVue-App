import React from 'react';

const KPICard = ({ title, value, change, isPositive }) => {
    return (
        <div className="glass-panel" style={{
            padding: '24px',
            borderRadius: 'var(--radius-xl)',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
            transition: 'transform 0.2s ease, box-shadow 0.2s ease',
            cursor: 'default'
        }}
            onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-4px)';
                e.currentTarget.style.boxShadow = 'var(--shadow-lg)';
                e.currentTarget.style.borderColor = 'rgba(45, 136, 255, 0.3)';
            }}
            onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'var(--shadow-sm)';
                e.currentTarget.style.borderColor = 'var(--glass-border)';
            }}
        >
            <h3 style={{
                fontSize: '0.9rem',
                color: 'var(--text-secondary)',
                fontWeight: 500
            }}>
                {title}
            </h3>

            <div style={{
                fontSize: '2rem',
                fontWeight: 700,
                letterSpacing: '-1px'
            }}>
                {value}
            </div>

            <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '0.85rem',
                fontWeight: 600,
                color: isPositive ? '#4ade80' : '#f87171'
            }}>
                <span style={{
                    backgroundColor: isPositive ? 'rgba(74, 222, 128, 0.1)' : 'rgba(248, 113, 113, 0.1)',
                    padding: '2px 6px',
                    borderRadius: '4px'
                }}>
                    {change}
                </span>
                <span style={{ color: 'var(--text-secondary)', fontWeight: 400 }}>vs last month</span>
            </div>
        </div>
    );
};

export default KPICard;
