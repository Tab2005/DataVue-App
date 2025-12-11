
import React, { useState, useEffect, useMemo } from 'react';
import { ResponsiveContainer, ComposedChart, Line, Bar, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { useOutletContext } from 'react-router-dom';
import { format, parseISO } from 'date-fns';

// Metric Definitions moved inside to combine with props


const TrendSection = ({ accountId, dateRange, prevDateRange, isCompareMode, selectedMetrics, metricGroups }) => {
    const { language, user } = useOutletContext();
    const t = {
        expand: language === 'zh' ? '📈 展開趨勢圖表' : '📈 Show Trend Chart',
        collapse: language === 'zh' ? '收起圖表' : 'Hide Chart',
        loading: language === 'zh' ? '載入中...' : 'Loading...',
        noData: language === 'zh' ? '無數據' : 'No Data',
        leftAxis: language === 'zh' ? '左軸指標' : 'Left Axis',
        rightAxis: language === 'zh' ? '右軸指標' : 'Right Axis',
        vs: language === 'zh' ? 'vs 上期' : 'vs Prev',
    };

    // Core Metrics that are always available
    const CORE_METRICS = [
        { key: 'spend', label_zh: '花費金額 (Spend)', label_en: 'Spend', format: 'currency' },
        { key: 'roas', label_zh: 'ROAS (投資報酬率)', label_en: 'ROAS', format: 'decimal' },
        { key: 'purchases', label_zh: '購買次數 (Purchases)', label_en: 'Purchases', format: 'number' },
        { key: 'cpa', label_zh: 'CPA (單次購買成本)', label_en: 'CPA', format: 'currency' },
        { key: 'impressions', label_zh: '曝光次數 (Impressions)', label_en: 'Impressions', format: 'number' },
        { key: 'cpm', label_zh: 'CPM (千次曝光成本)', label_en: 'CPM', format: 'currency' },
        { key: 'link_clicks', label_zh: '連結點擊 (Link Clicks)', label_en: 'Link Clicks', format: 'number' },
        { key: 'cpc', label_zh: 'CPC (單次連結點擊成本)', label_en: 'CPC', format: 'currency' },
        { key: 'ctr', label_zh: 'CTR (點擊率)', label_en: 'CTR', format: 'percent' },
    ];

    // Compute Available Metrics (Core + Selected)
    const availableMetrics = useMemo(() => {
        // Start with Core
        const combined = [...CORE_METRICS];
        const existingKeys = new Set(combined.map(m => m.key));

        // Add Selected Metrics if not present
        if (metricGroups && selectedMetrics) {
            metricGroups.forEach(group => {
                group.metrics.forEach(m => {
                    const compositeKey = `${group.id}:${m.key}`;
                    if (selectedMetrics.has(compositeKey)) {
                        // If user selected this metric, add it to dropdown if not exists
                        if (!existingKeys.has(m.key)) {
                            combined.push(m);
                            existingKeys.add(m.key);
                        }
                    }
                });
            });
        }
        return combined;
    }, [metricGroups, selectedMetrics]);

    // UI State
    const [expanded, setExpanded] = useState(false);
    const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);

    useEffect(() => {
        const handleResize = () => setIsMobile(window.innerWidth <= 768);
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    // Data State
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(false);

    // Metric Selection State (Independent from Table)
    const [leftKey, setLeftKey] = useState('spend');
    const [rightKey, setRightKey] = useState('roas');

    // Fetch Logic
    useEffect(() => {
        if (expanded && accountId) {
            fetchTrendData();
        }
    }, [expanded, accountId, dateRange, prevDateRange, isCompareMode]);

    const fetchTrendData = async () => {
        setLoading(true);
        try {
            const idToken = localStorage.getItem('google_token');
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

            const params = new URLSearchParams({
                account_id: accountId,
                since: dateRange.since,
                until: dateRange.until,
            });

            if (isCompareMode && prevDateRange.since) {
                params.append('prev_since', prevDateRange.since);
                params.append('prev_until', prevDateRange.until);
            }

            const res = await fetch(`${apiUrl}/api/analytics-trend?${params}`, {
                headers: { 'Authorization': `Bearer ${idToken}` }
            });
            const json = await res.json();
            setData(json || []);
        } catch (err) {
            console.error("Trend fetch error", err);
        } finally {
            setLoading(false);
        }
    };

    // Helper: Find Metric Config
    // Helper: Find Metric Config
    const getMetric = (key) => availableMetrics.find(m => m.key === key) || CORE_METRICS[0];

    // Format Value Helper
    const fmt = (val, key) => {
        const m = getMetric(key);
        if (val === undefined || val === null) return '-';
        if (m.format === 'currency') return `$${val.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
        if (m.format === 'percent') return `${val.toFixed(2)}%`;
        if (m.format === 'decimal') return val.toFixed(2);
        return val.toLocaleString();
    };

    // Calculate Domains for Y-Axis
    const { leftDomain, rightDomain } = useMemo(() => {
        if (!data || data.length === 0) return { leftDomain: ['auto', 'auto'], rightDomain: ['auto', 'auto'] };

        const mLeft = getMetric(leftKey);
        const mRight = getMetric(rightKey);

        // Calculate Max Values
        const maxLeft = Math.max(...data.map(d => d[leftKey] || 0));
        const maxRight = Math.max(...data.map(d => d[rightKey] || 0));

        // Sync Logic:
        // If formats are the same AND they are 'number' or 'percent', sync them.
        // We generally avoid syncing Currency because Spend ($1000) vs CPA ($10) renders CPA invisible.
        // But for Counts (Purchases vs ATC), syncing is desired for comparison.
        const shouldSync = mLeft.format === mRight.format && (mLeft.format === 'number' || mLeft.format === 'percent');

        if (shouldSync) {
            const globalMax = Math.max(maxLeft, maxRight);
            // Add 10% padding
            const domainMax = Math.ceil(globalMax * 1.1);
            return { leftDomain: [0, domainMax], rightDomain: [0, domainMax] };
        }

        // Default: Independent Axes (with some padding for aesthetics)
        return {
            leftDomain: [0, 'auto'],
            rightDomain: [0, 'auto']
        };

    }, [data, leftKey, rightKey, availableMetrics]);

    if (!expanded) {
        return (
            <div style={{ marginBottom: '16px' }}>
                <button
                    onClick={() => setExpanded(true)}
                    className="glass-panel"
                    style={{
                        width: '100%',
                        padding: '12px',
                        textAlign: 'center',
                        color: 'var(--accent-primary)',
                        fontWeight: 600,
                        cursor: 'pointer',
                        border: '1px dashed var(--glass-border)',
                        borderRadius: '12px',
                        background: 'rgba(255,255,255,0.02)',
                        transition: 'all 0.2s'
                    }}
                >
                    {t.expand}
                </button>
            </div>
        );
    }

    return (
        <div className="glass-panel" style={{
            padding: isMobile ? '16px' : '24px', // Reduced padding
            borderRadius: '16px',
            marginBottom: '24px',
            animation: 'fadeIn 0.3s'
        }}>
            {/* Header / Controls */}
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: isMobile ? 'flex-start' : 'center',
                flexDirection: isMobile ? 'column-reverse' : 'row',
                marginBottom: '24px',
                flexWrap: 'wrap',
                gap: '16px'
            }}>

                {/* Dropdowns */}
                <div style={{
                    display: 'flex',
                    gap: isMobile ? '12px' : '16px',
                    alignItems: 'center',
                    flexDirection: isMobile ? 'column' : 'row',
                    width: isMobile ? '100%' : 'auto'
                }}>
                    {/* Left Axis */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', width: isMobile ? '100%' : 'auto' }}>
                        <label style={{ fontSize: '0.75rem', color: 'var(--accent-primary)', fontWeight: 600 }}>{t.leftAxis} (Bar/Area)</label>
                        <select
                            value={leftKey}
                            onChange={(e) => setLeftKey(e.target.value)}
                            style={{
                                padding: '8px',
                                borderRadius: '8px',
                                background: 'rgba(255,255,255,0.05)',
                                border: '1px solid var(--glass-border)',
                                color: 'white',
                                minWidth: isMobile ? '100%' : '160px',
                                width: isMobile ? '100%' : 'auto'
                            }}
                        >
                            {availableMetrics.map(m => (
                                <option key={m.key} value={m.key} style={{ color: 'black' }}>
                                    {language === 'zh' ? m.label_zh : m.label_en}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Right Axis */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', width: isMobile ? '100%' : 'auto' }}>
                        <label style={{ fontSize: '0.75rem', color: '#fb7185', fontWeight: 600 }}>{t.rightAxis} (Line)</label>
                        <select
                            value={rightKey}
                            onChange={(e) => setRightKey(e.target.value)}
                            style={{
                                padding: '8px',
                                borderRadius: '8px',
                                background: 'rgba(255,255,255,0.05)',
                                border: '1px solid var(--glass-border)',
                                color: 'white',
                                minWidth: isMobile ? '100%' : '160px',
                                width: isMobile ? '100%' : 'auto'
                            }}
                        >
                            {availableMetrics.map(m => (
                                <option key={m.key} value={m.key} style={{ color: 'black' }}>
                                    {language === 'zh' ? m.label_zh : m.label_en}
                                </option>
                            ))}
                        </select>
                    </div>
                </div>

                {/* Close Button */}
                <button
                    onClick={() => setExpanded(false)}
                    style={{
                        padding: '8px 16px',
                        background: 'transparent',
                        border: '1px solid var(--text-secondary)',
                        color: 'var(--text-secondary)',
                        borderRadius: '20px',
                        cursor: 'pointer',
                        fontSize: '0.85rem',
                        alignSelf: isMobile ? 'flex-end' : 'auto',
                        marginTop: isMobile ? '-10px' : '0'
                    }}
                >
                    {t.collapse}
                </button>
            </div>

            {/* Chart Area */}
            <div style={{ height: isMobile ? '300px' : '400px', width: '100%', marginLeft: isMobile ? '-10px' : '0' }}>
                {loading ? (
                    <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
                        {t.loading}
                    </div>
                ) : data.length === 0 ? (
                    <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
                        {t.noData}
                    </div>
                ) : (
                    <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={data} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                            <defs>
                                <linearGradient id="colorLeft" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="var(--accent-primary)" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="var(--accent-primary)" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />

                            {/* X Axis: Date */}
                            <XAxis
                                dataKey="date"
                                axisLine={false}
                                tickLine={false}
                                tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
                                dy={10}
                            />

                            {/* Y Axis Left */}
                            <YAxis
                                yAxisId="left"
                                orientation="left"
                                axisLine={false}
                                tickLine={false}
                                tick={{ fill: 'var(--accent-primary)', fontSize: 12 }}
                                tickFormatter={(val) => fmt(val, leftKey)}
                                domain={leftDomain}
                            />

                            {/* Y Axis Right */}
                            <YAxis
                                yAxisId="right"
                                orientation="right"
                                axisLine={false}
                                tickLine={false}
                                tick={{ fill: '#fb7185', fontSize: 12 }}
                                tickFormatter={(val) => fmt(val, rightKey)}
                                domain={rightDomain}
                            />

                            <Tooltip
                                contentStyle={{ backgroundColor: '#18191a', borderColor: '#3a3b3c', color: 'white' }}
                                labelStyle={{ color: 'var(--text-secondary)', marginBottom: '8px' }}
                                formatter={(value, name, props) => {
                                    // Custom tooltip formatting
                                    // name maps to dataKey, we need to show proper labels
                                    // We'll trust the default for now but could enhance
                                    return [fmt(value, name.includes(leftKey) ? leftKey : rightKey), name];
                                }}
                            />
                            <Legend />

                            {/* Left Metric: Current (Area/Bar) */}
                            <Area
                                yAxisId="left"
                                type="monotone"
                                dataKey={leftKey}
                                name={`${getMetric(leftKey).label_en}`}
                                stroke="var(--accent-primary)"
                                fill="url(#colorLeft)"
                                strokeWidth={2}
                            />

                            {/* Left Metric: Previous (Dashed Line) */}
                            {isCompareMode && (
                                <Line
                                    yAxisId="left"
                                    type="monotone"
                                    dataKey={`${leftKey}_prev`}
                                    name={`${getMetric(leftKey).label_en} (Prev)`}
                                    stroke="var(--accent-primary)"
                                    strokeDasharray="5 5"
                                    strokeWidth={2}
                                    dot={false}
                                    activeDot={false}
                                    opacity={0.6}
                                />
                            )}

                            {/* Right Metric: Current (Solid Line) */}
                            <Line
                                yAxisId="right"
                                type="monotone"
                                dataKey={rightKey}
                                name={`${getMetric(rightKey).label_en}`}
                                stroke="#fb7185"
                                strokeWidth={2}
                                dot={{ fill: '#fb7185', r: 3 }}
                            />

                            {/* Right Metric: Previous (Dashed Line) */}
                            {isCompareMode && (
                                <Line
                                    yAxisId="right"
                                    type="monotone"
                                    dataKey={`${rightKey}_prev`}
                                    name={`${getMetric(rightKey).label_en} (Prev)`}
                                    stroke="#fb7185"
                                    strokeDasharray="5 5"
                                    strokeWidth={2}
                                    dot={false}
                                    activeDot={false}
                                    opacity={0.6}
                                />
                            )}

                        </ComposedChart>
                    </ResponsiveContainer>
                )}
            </div>
        </div>
    );
};

export default TrendSection;
