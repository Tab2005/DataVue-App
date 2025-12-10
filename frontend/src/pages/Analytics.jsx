import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { format, subDays, startOfWeek, endOfWeek, startOfMonth, endOfMonth, subMonths } from 'date-fns';

const DATE_PRESETS = [
    { label: '今日 (Today)', value: 'today' },
    { label: '昨天 (Yesterday)', value: 'yesterday' },
    { label: '本週 (This Week)', value: 'this_week' },
    { label: '上週 (Last Week)', value: 'last_week' },
    { label: '本月 (This Month)', value: 'this_month' },
    { label: '上月 (Last Month)', value: 'last_month' },
    { label: '最近 7 天 (Last 7 Days)', value: 'last_7d' },
    { label: '最近 14 天 (Last 14 Days)', value: 'last_14d' },
    { label: '最近 30 天 (Last 30 Days)', value: 'last_30d' },
    { label: '自訂 (Custom)', value: 'custom' },
];

const COMPARE_PRESETS = [
    { label: '前一期 (Previous Period)', value: 'previous_period' },
    { label: '去年同期 (Same Period Last Year)', value: 'year_over_year' },
    { label: '自訂 (Custom)', value: 'custom' },
];

const Analytics = () => {
    // 1. Get shared context
    const { selectedAccountId, user, language } = useOutletContext();

    // 2. Translations
    const t = {
        zh: {
            title: "深度成效分析",
            subtitle: "自訂報表與漏斗分析",
            mainSettings: "主要設定",
            level: "分析層級",
            dateRange: "日期範圍",
            customStart: "開始",
            customEnd: "結束",
            advanced: "進階選項",
            compareMode: "V.S 比較模式",
            comparePeriod: "比較期間",
            updateReport: "更新報表",
            levels: {
                campaign: "按活動名稱",
                adset: "按廣告組合名稱",
                ad: "按廣告名稱",
                account: "整體總覽",
            },
            presets: {
                today: "今日",
                yesterday: "昨天",
                this_week: "本週",
                last_week: "上週",
                this_month: "本月",
                last_month: "上月",
                last_7d: "最近 7 天",
                last_14d: "最近 14 天",
                last_30d: "最近 30 天",
                custom: "自訂",
            },
            comparePresets: {
                previous_period: "前一期",
                year_over_year: "去年同期",
                custom: "自訂",
            },
            table: {
                name: "名稱",
                spend: "花費",
                roas: "回報率 (ROAS)",
                purchases: "購買數",
                cpa: "CPA",
                clicks: "點擊數",
                cvr: "轉換率",
                atc: "購物車",
                dropoff: "流失率",
            }
        },
        en: {
            title: "Deep Analytics",
            subtitle: "Custom Reports & Funnel Analysis",
            mainSettings: "Main Settings",
            level: "Analysis Level",
            dateRange: "Date Range",
            customStart: "Start",
            customEnd: "End",
            advanced: "Advanced",
            compareMode: "Comparison Mode",
            comparePeriod: "Compare Period",
            updateReport: "Run Report",
            levels: {
                campaign: "By Campaign",
                adset: "By Ad Set",
                ad: "By Ad",
                account: "Account Overview",
            },
            presets: {
                today: "Today",
                yesterday: "Yesterday",
                this_week: "This Week",
                last_week: "Last Week",
                this_month: "This Month",
                last_month: "Last Month",
                last_7d: "Last 7 Days",
                last_14d: "Last 14 Days",
                last_30d: "Last 30 Days",
                custom: "Custom",
            },
            comparePresets: {
                previous_period: "Previous Period",
                year_over_year: "Year Over Year",
                custom: "Custom",
            },
            table: {
                name: "Name",
                spend: "Spend",
                roas: "ROAS",
                purchases: "Purchases",
                cpa: "CPA",
                clicks: "Link Clicks",
                cvr: "CVR",
                atc: "Add to Cart",
                dropoff: "Drop-off",
            }
        }
    };

    const txt = t[language] || t.zh;

    // 2. Local State for Controls
    const [level, setLevel] = useState('account');
    const [datePreset, setDatePreset] = useState('last_7d');
    const [dateRange, setDateRange] = useState({
        since: format(subDays(new Date(), 6), 'yyyy-MM-dd'),
        until: format(new Date(), 'yyyy-MM-dd')
    });

    // Comparison State
    const [isCompareMode, setIsCompareMode] = useState(false);
    const [comparePreset, setComparePreset] = useState('previous_period');
    const [compareRange, setCompareRange] = useState({ since: '', until: '' });

    // 2.1 Handle Preset Change
    const handlePresetChange = (e) => {
        const preset = e.target.value;
        setDatePreset(preset);

        const today = new Date();
        let newRange = { since: '', until: '' };

        switch (preset) {
            case 'today':
                newRange.since = format(today, 'yyyy-MM-dd');
                newRange.until = format(today, 'yyyy-MM-dd');
                break;
            case 'yesterday':
                const yest = subDays(today, 1);
                newRange.since = format(yest, 'yyyy-MM-dd');
                newRange.until = format(yest, 'yyyy-MM-dd');
                break;
            case 'this_week':
                newRange.since = format(startOfWeek(today, { weekStartsOn: 1 }), 'yyyy-MM-dd');
                newRange.until = format(today, 'yyyy-MM-dd');
                break;
            case 'last_week':
                const lastWeekStart = startOfWeek(subDays(today, 7), { weekStartsOn: 1 });
                const lastWeekEnd = endOfWeek(subDays(today, 7), { weekStartsOn: 1 });
                newRange.since = format(lastWeekStart, 'yyyy-MM-dd');
                newRange.until = format(lastWeekEnd, 'yyyy-MM-dd');
                break;
            case 'this_month':
                newRange.since = format(startOfMonth(today), 'yyyy-MM-dd');
                newRange.until = format(today, 'yyyy-MM-dd');
                break;
            case 'last_month':
                const lastMonth = subMonths(today, 1);
                newRange.since = format(startOfMonth(lastMonth), 'yyyy-MM-dd');
                newRange.until = format(endOfMonth(lastMonth), 'yyyy-MM-dd');
                break;
            case 'last_7d':
                newRange.since = format(subDays(today, 6), 'yyyy-MM-dd');
                newRange.until = format(today, 'yyyy-MM-dd');
                break;
            case 'last_14d':
                newRange.since = format(subDays(today, 13), 'yyyy-MM-dd');
                newRange.until = format(today, 'yyyy-MM-dd');
                break;
            case 'last_30d':
                newRange.since = format(subDays(today, 29), 'yyyy-MM-dd');
                newRange.until = format(today, 'yyyy-MM-dd');
                break;
            case 'custom':
                return;
            default:
                return;
        }

        setDateRange(newRange);
    };

    // 3. Data State
    const [reportData, setReportData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // 4. Fetch Function
    const fetchAnalytics = async () => {
        if (!selectedAccountId || !user) return;

        setLoading(true);
        setError(null);
        try {
            const idToken = localStorage.getItem('google_token');
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

            const query = new URLSearchParams({
                account_id: selectedAccountId,
                since: dateRange.since,
                until: dateRange.until,
                level: level,
                // compare: isCompareMode ? 'true' : 'false' 
            });

            const res = await fetch(`${apiUrl}/api/analytics-data?${query}`, {
                headers: {
                    'Authorization': `Bearer ${idToken}`
                }
            });

            if (!res.ok) throw new Error("Failed to fetch data");

            const json = await res.json();
            setReportData(json.data);

        } catch (err) {
            console.error(err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    // 5. Effect: Fetch when controls form is submitted (Actually user wanted manual update, so effect on loading only initially or keep manual)
    // Actually, Phase 3.1 spec says "Update Report Button triggers fetch".
    // So distinct from Dashboard which auto-fetches.
    // However, we want to pre-load reasonable data?
    // Let's keep manual fetch for now, or fetch on mount.

    // We can keep the effect watching selectedAccountId to reset/clear data, but mostly rely on button.
    useEffect(() => {
        if (selectedAccountId) {
            fetchAnalytics(); // Auto fetch on account switch
        }
    }, [selectedAccountId]); // Don't auto-fetch on date change, wait for button? Or auto fetch?
    // User clicked "Update Report" in screenshot. So probably manual.
    // But if I change preset, maybe I expect auto update?
    // Let's stick to "Click Button to Update" for flexibility, or maybe auto update ensures easier use.
    // Given the "Update Report" button exists, I will NOT auto-fetch on control change, only on Account change.

    // 6. Basic UI Components
    return (
        <div style={{ padding: '24px', width: '100%' }}>
            {/* Header Section */}
            <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h1 style={{ fontSize: '1.8rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                        {txt.title}
                    </h1>
                    <p style={{ color: 'var(--text-secondary)' }}>
                        {txt.subtitle}
                    </p>
                </div>
            </div>

            {/* Split Layout Control Panel */}
            <div style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: '24px', marginBottom: '24px' }}>

                {/* Left Panel: Primary Settings */}
                <div className="glass-panel" style={{ padding: '24px', borderRadius: '16px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
                    <h3 style={{ margin: 0, fontSize: '1rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>{txt.mainSettings}</h3>

                    <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
                        {/* Level Selector */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1, minWidth: '180px' }}>
                            <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>{txt.level}</label>
                            <select
                                value={level}
                                onChange={(e) => setLevel(e.target.value)}
                                style={{
                                    padding: '10px',
                                    borderRadius: '8px',
                                    background: 'rgba(255,255,255,0.05)',
                                    border: '1px solid var(--glass-border)',
                                    color: 'white',
                                    width: '100%'
                                }}
                            >
                                <option value="campaign" style={{ color: 'black' }}>{txt.levels.campaign}</option>
                                <option value="adset" style={{ color: 'black' }}>{txt.levels.adset}</option>
                                <option value="ad" style={{ color: 'black' }}>{txt.levels.ad}</option>
                                <option value="account" style={{ color: 'black' }}>{txt.levels.account}</option>
                            </select>
                        </div>

                        {/* Date Preset Selector */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1, minWidth: '180px' }}>
                            <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>{txt.dateRange}</label>
                            <select
                                value={datePreset}
                                onChange={handlePresetChange}
                                style={{
                                    padding: '10px',
                                    borderRadius: '8px',
                                    background: 'rgba(255,255,255,0.05)',
                                    border: '1px solid var(--glass-border)',
                                    color: 'white',
                                    width: '100%'
                                }}
                            >
                                {DATE_PRESETS.map(p => (
                                    <option key={p.value} value={p.value} style={{ color: 'black' }}>
                                        {txt.presets[p.value] || p.label}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {/* Custom Date Inputs (Conditional) */}
                    {datePreset === 'custom' && (
                        <div style={{ display: 'flex', gap: '16px' }}>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
                                <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>{txt.customStart}</label>
                                <input type="date" value={dateRange.since} onChange={(e) => setDateRange({ ...dateRange, since: e.target.value })}
                                    style={{ padding: '10px', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)', color: 'var(--text-primary)', colorScheme: 'dark', width: '100%' }} />
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
                                <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>{txt.customEnd}</label>
                                <input type="date" value={dateRange.until} onChange={(e) => setDateRange({ ...dateRange, until: e.target.value })}
                                    style={{ padding: '10px', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)', color: 'var(--text-primary)', colorScheme: 'dark', width: '100%' }} />
                            </div>
                        </div>
                    )}
                </div>

                {/* Right Panel: Comparison & Actions */}
                <div className="glass-panel" style={{ padding: '24px', borderRadius: '16px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <h3 style={{ margin: 0, fontSize: '1rem', color: 'var(--text-secondary)' }}>{txt.advanced}</h3>
                        </div>

                        {/* Comparison Toggle */}
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px' }}>
                            <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>{txt.compareMode}</span>
                            <label className="switch" style={{ position: 'relative', display: 'inline-block', width: '40px', height: '24px' }}>
                                <input type="checkbox" checked={isCompareMode} onChange={(e) => setIsCompareMode(e.target.checked)} style={{ opacity: 0, width: 0, height: 0 }} />
                                <span style={{
                                    position: 'absolute', cursor: 'pointer', top: 0, left: 0, right: 0, bottom: 0,
                                    backgroundColor: isCompareMode ? 'var(--accent-primary)' : '#ccc', borderRadius: '24px', transition: '.4s'
                                }}>
                                    <span style={{
                                        position: 'absolute', content: "", height: '16px', width: '16px', left: '4px', bottom: '4px',
                                        backgroundColor: 'white', transition: '.4s', borderRadius: '50%',
                                        transform: isCompareMode ? 'translateX(16px)' : 'translateX(0)'
                                    }}></span>
                                </span>
                            </label>
                        </div>

                        {/* Comparison Date Selector (Visible only if enabled) */}
                        {isCompareMode && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', transition: 'all 0.3s' }}>
                                <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>{txt.comparePeriod}</label>
                                <select
                                    value={comparePreset}
                                    onChange={(e) => setComparePreset(e.target.value)}
                                    style={{
                                        padding: '10px',
                                        borderRadius: '8px',
                                        background: 'rgba(255,255,255,0.05)',
                                        border: '1px solid var(--glass-border)',
                                        color: 'white',
                                        width: '100%'
                                    }}
                                >
                                    {COMPARE_PRESETS.map(p => (
                                        <option key={p.value} value={p.value} style={{ color: 'black' }}>
                                            {txt.comparePresets[p.value] || p.label}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        )}
                    </div>

                    <button
                        onClick={fetchAnalytics}
                        style={{
                            marginTop: '20px',
                            padding: '12px 24px',
                            background: 'var(--accent-primary)',
                            border: 'none',
                            borderRadius: '8px',
                            color: 'white',
                            fontWeight: 600,
                            cursor: 'pointer',
                            fontSize: '1rem',
                            display: 'flex',
                            justifyContent: 'center',
                            alignItems: 'center',
                            gap: '8px'
                        }}
                    >
                        {txt.updateReport}
                    </button>

                </div>
            </div>

            {/* Data Table */}
            {loading ? (
                <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>載入數據中...</div>
            ) : error ? (
                <div style={{ textAlign: 'center', padding: '40px', color: '#f87171' }}>{error}</div>
            ) : (
                <div className="glass-panel" style={{ padding: '20px', borderRadius: '16px', overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', color: 'var(--text-primary)', fontSize: '0.9rem' }}>
                        <thead>
                            <tr style={{ borderBottom: '1px solid var(--glass-border)', textAlign: 'left' }}>
                                <th style={{ padding: '12px', minWidth: '200px' }}>{txt.table.name}</th>
                                <th style={{ padding: '12px' }}>{txt.table.spend}</th>
                                <th style={{ padding: '12px' }}>{txt.table.roas}</th>
                                <th style={{ padding: '12px' }}>{txt.table.purchases}</th>
                                <th style={{ padding: '12px' }}>{txt.table.cpa}</th>
                                <th style={{ padding: '12px' }}>{txt.table.clicks}</th>
                                <th style={{ padding: '12px' }}>{txt.table.cvr}</th>
                                <th style={{ padding: '12px' }}>{txt.table.atc}</th>
                                <th style={{ padding: '12px' }}>{txt.table.dropoff}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {reportData && reportData.map((row, idx) => (
                                <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                    <td style={{ padding: '12px', fontWeight: 600 }}>{row.name}</td>
                                    <td style={{ padding: '12px' }}>${row.spend.toLocaleString()}</td>
                                    <td style={{ padding: '12px', color: row.roas > 2 ? '#4ade80' : 'inherit' }}>{row.roas.toFixed(2)}</td>
                                    <td style={{ padding: '12px' }}>{row.purchases}</td>
                                    <td style={{ padding: '12px' }}>${row.cpa.toFixed(1)}</td>
                                    <td style={{ padding: '12px' }}>{row.link_clicks}</td>
                                    <td style={{ padding: '12px' }}>{row.cvr.toFixed(2)}%</td>
                                    <td style={{ padding: '12px' }}>{row.add_to_cart}</td>
                                    <td style={{ padding: '12px', color: row.cart_dropoff > 80 ? '#f87171' : 'inherit' }}>
                                        {row.cart_dropoff.toFixed(1)}%
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    {!reportData || reportData.length === 0 && (
                        <div style={{ textAlign: 'center', padding: '20px', color: 'var(--text-tertiary)' }}>無數據 (No Data)</div>
                    )}
                </div>
            )}
        </div>
    );
};

export default Analytics;
