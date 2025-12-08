import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const TrendsChart = ({ data, language }) => {
    // Translations
    const t = {
        loading: language === 'zh' ? '正在載入圖表數據...' : 'Loading Chart Data...',
        title: language === 'zh' ? '受眾成長趨勢' : 'Audience Growth',
        options: {
            sixMonths: language === 'zh' ? '過去 6 個月' : 'Last 6 Months',
            lastYear: language === 'zh' ? '過去一年' : 'Last Year',
        }
    };

    if (!data || data.length === 0) {
        return (
            <div className="glass-panel" style={{
                padding: '32px',
                borderRadius: 'var(--radius-xl)',
                height: '400px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--text-secondary)'
            }}>
                {t.loading}
            </div>
        );
    }

    return (
        <div className="glass-panel" style={{
            padding: '24px',
            borderRadius: 'var(--radius-xl)',
            height: '450px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px'
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <h3 style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>{t.title}</h3>
                <select style={{
                    background: 'rgba(255,255,255,0.05)',
                    border: '1px solid var(--glass-border)',
                    color: 'var(--text-secondary)',
                    padding: '4px 8px',
                    borderRadius: '6px',
                    outline: 'none'
                }}>
                    <option>{t.options.sixMonths}</option>
                    <option>{t.options.lastYear}</option>
                </select>
            </div>

            <div style={{ flex: 1, width: '100%', minHeight: 0 }}>
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                        <defs>
                            <linearGradient id="colorFollowers" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="var(--accent-primary)" stopOpacity={0.4} />
                                <stop offset="95%" stopColor="var(--accent-primary)" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                        <XAxis
                            dataKey="name"
                            axisLine={false}
                            tickLine={false}
                            stroke="var(--text-secondary)"
                            fontSize={12}
                            dy={10}
                        />
                        <YAxis
                            axisLine={false}
                            tickLine={false}
                            stroke="var(--text-secondary)"
                            fontSize={12}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: 'var(--bg-secondary)',
                                borderColor: 'var(--glass-border)',
                                borderRadius: '8px',
                                color: 'var(--text-primary)'
                            }}
                            itemStyle={{ color: 'var(--text-primary)' }}
                        />
                        <Area
                            type="monotone"
                            dataKey="followers"
                            stroke="var(--accent-primary)"
                            strokeWidth={3}
                            fillOpacity={1}
                            fill="url(#colorFollowers)"
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default TrendsChart;
