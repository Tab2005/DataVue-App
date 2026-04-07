import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { getMetricConfig } from '../constants/analyticsConfig';

const TrendsChart = ({ data, language, title, metrics, dataKey = 'value', xAxisKey = 'name', height = 450 }) => {
    // Translations
    const t = {
        loading: language === 'zh' ? '正在載入圖表數據...' : 'Loading Chart Data...',
        defaultTitle: language === 'zh' ? '趨勢圖表' : 'Trend Chart',
    };

    if (!data || data.length === 0) {
        return (
            <div className="glass-panel" style={{
                padding: '32px',
                borderRadius: 'var(--radius-xl)',
                height: `${height}px`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--text-secondary)'
            }}>
                {t.loading}
            </div>
        );
    }

    // Color palette for multiple metrics
    const colors = [
        '#6366f1', // Indigo
        '#06b6d4', // Teal
        '#8b5cf6', // Violet
        '#fbbf24', // Amber
        '#fb7185', // Rose
    ];

    // Determine which keys to render
    const renderMetrics = metrics && metrics.length > 0 ? metrics : [dataKey];

    return (
        <div className="glass-panel" style={{
            padding: '24px',
            borderRadius: 'var(--radius-xl)',
            height: `${height}px`,
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
            background: 'transparent',
            border: 'none',
            boxShadow: 'none'
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <h3 style={{ color: 'var(--text-secondary)', fontWeight: 500, fontSize: '0.9rem' }}>{title || t.defaultTitle}</h3>
            </div>

            <div style={{ flex: 1, width: '100%', minHeight: 0 }}>
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                        <defs>
                            {renderMetrics.map((mKey, idx) => (
                                <linearGradient key={`grad-${mKey}`} id={`color-${mKey}`} x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor={colors[idx % colors.length]} stopOpacity={0.3} />
                                    <stop offset="95%" stopColor={colors[idx % colors.length]} stopOpacity={0} />
                                </linearGradient>
                            ))}
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                        <XAxis
                            dataKey={xAxisKey}
                            axisLine={false}
                            tickLine={false}
                            stroke="var(--text-secondary)"
                            fontSize={10}
                            dy={10}
                        />
                        <YAxis
                            axisLine={false}
                            tickLine={false}
                            stroke="var(--text-secondary)"
                            fontSize={10}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: 'var(--bg-secondary)',
                                borderColor: 'var(--glass-border)',
                                borderRadius: '8px',
                                color: 'var(--text-primary)',
                                fontSize: '0.8rem'
                            }}
                            itemStyle={{ color: 'var(--text-primary)' }}
                        />
                        {renderMetrics.length > 1 && <Legend wrapperStyle={{ fontSize: '0.75rem', paddingTop: '10px' }} />}
                        {renderMetrics.map((mKey, idx) => {
                            const config = getMetricConfig(mKey);
                            const label = language === 'zh' ? config?.label_zh : config?.label_en;
                            return (
                                <Area
                                    key={mKey}
                                    type="monotone"
                                    dataKey={mKey}
                                    name={label || mKey}
                                    stroke={colors[idx % colors.length]}
                                    strokeWidth={2}
                                    fillOpacity={1}
                                    fill={`url(#color-${mKey})`}
                                />
                            );
                        })}
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default TrendsChart;
