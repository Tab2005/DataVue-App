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

// Unified Metric Groups Config
// Used for BOTH the Metric Selector (Checkbox) and the KPI Cards/Table Columns
const METRIC_GROUPS = [
    {
        id: 'general',
        label_zh: '通用指標',
        label_en: 'General Metrics',
        color: '#3b82f6', // Blue for KPI Card border
        metrics: [
            { key: 'spend', label_zh: '花費金額', label_en: 'Spend', format: 'currency' },
            { key: 'impressions', label_zh: '曝光次數', label_en: 'Impressions', format: 'number' },
            { key: 'reach', label_zh: '觸及人數', label_en: 'Reach', format: 'number' },
            { key: 'link_clicks', label_zh: '連結點擊次數', label_en: 'Link Clicks', format: 'number' },
            { key: 'ctr', label_zh: '連結點擊率 (CTR)', label_en: 'CTR', format: 'percent' },
            { key: 'cpc', label_zh: 'CPC (單次連結點擊成本)', label_en: 'CPC', format: 'currency' },
            { key: 'cpm', label_zh: 'CPM (每千次廣告曝光成本)', label_en: 'CPM', format: 'currency' },
        ]
    },
    {
        id: 'ecommerce',
        label_zh: '電商指標',
        label_en: 'E-commerce Metrics',
        color: '#10b981', // Emerald
        metrics: [
            { key: 'view_content', label_zh: '內容查看次數', label_en: 'Content Views', format: 'number' },
            { key: 'cost_per_atc', label_zh: '每次加入購物車成本', label_en: 'Cost per Add to Cart', format: 'currency' },
            { key: 'add_to_cart', label_zh: '加到購物車次數', label_en: 'Add to Cart', format: 'number' },
            { key: 'atc_value', label_zh: '加到購物車的轉換值', label_en: 'ATC Value', format: 'currency' },
            { key: 'initiate_checkout', label_zh: '開始結帳次數', label_en: 'Initiate Checkout', format: 'number' },
            { key: 'add_payment_info', label_zh: '新增付款資訊次數', label_en: 'Payment Info Added', format: 'number' },
            { key: 'purchases', label_zh: '購買次數', label_en: 'Purchases', format: 'number' },
            { key: 'purchase_value', label_zh: '購買轉換價值', label_en: 'Purchase Convert Value', format: 'currency' },
            { key: 'cpa', label_zh: 'CPA (單次購買成本)', label_en: 'CPA', format: 'currency' },
            { key: 'roas', label_zh: 'ROAS', label_en: 'ROAS', format: 'decimal' },
        ]
    },
    {
        id: 'funnel',
        label_zh: '漏斗指標',
        label_en: 'Funnel Metrics',
        color: '#f59e0b', // Amber
        metrics: [
            { key: 'cvr', label_zh: '購買轉換率', label_en: 'Purchase Conversion Rate', format: 'percent' },
            { key: 'view_to_cart', label_zh: '查看後購物車加入率', label_en: 'View-to-Cart Rate', format: 'percent' },
            { key: 'cart_conversion', label_zh: '購物車購買率', label_en: 'Cart Purchase Rate', format: 'percent' },
            { key: 'cart_dropoff', label_zh: '廣告購物車流失率', label_en: 'Cart Drop-off Rate', format: 'percent' },
            { key: 'cart_value_realization', label_zh: '購物車價值實現率', label_en: 'Cart Value Realization', format: 'percent' },
        ]
    }
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
            keyMetrics: "關鍵指標總覽",
            customMetrics: "自訂表格指標欄位",
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
            keyMetrics: "Key Metrics Overview",
            customMetrics: "Custom Report Metrics",
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

    // Metric Selector State (Default: Select all keys from all groups)
    const [selectedMetrics, setSelectedMetrics] = useState(new Set(
        METRIC_GROUPS.flatMap(g => g.metrics).map(m => m.key)
    ));

    // UI: Toggle Metric Panel
    const [showMetricPanel, setShowMetricPanel] = useState(false);

    // 2.1 Handle Preset Change
    const handlePresetChange = (e) => {
        const preset = e.target.value;
        setDatePreset(preset);

        const today = new Date();
        let newRange = { since: '', until: '' };

        switch (preset) {
            case 'today': newRange.since = format(today, 'yyyy-MM-dd'); newRange.until = format(today, 'yyyy-MM-dd'); break;
            case 'yesterday': { const yest = subDays(today, 1); newRange.since = format(yest, 'yyyy-MM-dd'); newRange.until = format(yest, 'yyyy-MM-dd'); break; }
            case 'this_week': newRange.since = format(startOfWeek(today, { weekStartsOn: 1 }), 'yyyy-MM-dd'); newRange.until = format(today, 'yyyy-MM-dd'); break;
            case 'last_week': { const start = startOfWeek(subDays(today, 7), { weekStartsOn: 1 }); const end = endOfWeek(subDays(today, 7), { weekStartsOn: 1 }); newRange.since = format(start, 'yyyy-MM-dd'); newRange.until = format(end, 'yyyy-MM-dd'); break; }
            case 'this_month': newRange.since = format(startOfMonth(today), 'yyyy-MM-dd'); newRange.until = format(today, 'yyyy-MM-dd'); break;
            case 'last_month': { const lm = subMonths(today, 1); newRange.since = format(startOfMonth(lm), 'yyyy-MM-dd'); newRange.until = format(endOfMonth(lm), 'yyyy-MM-dd'); break; }
            case 'last_7d': newRange.since = format(subDays(today, 6), 'yyyy-MM-dd'); newRange.until = format(today, 'yyyy-MM-dd'); break;
            case 'last_14d': newRange.since = format(subDays(today, 13), 'yyyy-MM-dd'); newRange.until = format(today, 'yyyy-MM-dd'); break;
            case 'last_30d': newRange.since = format(subDays(today, 29), 'yyyy-MM-dd'); newRange.until = format(today, 'yyyy-MM-dd'); break;
            case 'custom': return;
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

    useEffect(() => {
        if (selectedAccountId) {
            fetchAnalytics();
        }
    }, [selectedAccountId]);

    // Metric Toggle Handler
    const toggleMetric = (key) => {
        const newSet = new Set(selectedMetrics);
        if (newSet.has(key)) {
            newSet.delete(key);
        } else {
            newSet.add(key);
        }
        setSelectedMetrics(newSet);
    };

    // Helper to get active columns based on order defined in METRIC_GROUPS
    const getActiveColumns = () => {
        const cols = [];
        // Flatten groups to preserve order
        METRIC_GROUPS.forEach(group => {
            group.metrics.forEach(m => {
                if (selectedMetrics.has(m.key)) {
                    cols.push(m);
                }
            });
        });
        return cols;
    };

    const activeCols = getActiveColumns();

    // 7. Calculate Summary for KPI Cards
    const calculateSummary = () => {
        if (!reportData || reportData.length === 0) return null;

        // Sum basic additive metrics
        const sum = (key) => reportData.reduce((acc, row) => acc + (row[key] || 0), 0);

        const total = {
            spend: sum('spend'),
            impressions: sum('impressions'),
            reach: sum('reach'), // Approximation
            link_clicks: sum('link_clicks'),
            view_content: sum('view_content'),
            add_to_cart: sum('add_to_cart'),
            initiate_checkout: sum('initiate_checkout'),
            add_payment_info: sum('add_payment_info'),
            purchases: sum('purchases'),
            purchase_value: sum('purchase_value'),
            atc_value: sum('atc_value'),
        };

        // Recalculate derived rates
        total.cpc = total.link_clicks > 0 ? total.spend / total.link_clicks : 0;
        total.cpm = total.impressions > 0 ? (total.spend / total.impressions) * 1000 : 0;
        total.ctr = total.impressions > 0 ? (total.link_clicks / total.impressions) * 100 : 0;
        total.cpa = total.purchases > 0 ? total.spend / total.purchases : 0;
        total.cost_per_atc = total.add_to_cart > 0 ? total.spend / total.add_to_cart : 0;
        total.roas = total.spend > 0 ? total.purchase_value / total.spend : 0;

        // Funnel Rates
        total.cvr = total.link_clicks > 0 ? (total.purchases / total.link_clicks) * 100 : 0;
        total.view_to_cart = total.view_content > 0 ? (total.add_to_cart / total.view_content) * 100 : 0;
        total.cart_conversion = total.add_to_cart > 0 ? (total.purchases / total.add_to_cart) * 100 : 0;
        total.cart_dropoff = total.add_to_cart > 0 ? (1 - (total.purchases / total.add_to_cart)) * 100 : 0;
        total.cart_value_realization = total.atc_value > 0 ? (total.purchase_value / total.atc_value) * 100 : 0;

        return total;
    };

    const summaryData = calculateSummary();

    const renderMetricValue = (val, format) => {
        if (val === undefined || val === null || isNaN(val)) return '-';
        if (format === 'currency') return `$${val.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`; // Round currency on cards
        if (format === 'percent') return `${val.toFixed(2)}%`;
        if (format === 'decimal') return val.toFixed(2);
        return val.toLocaleString();
    };


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

            {/* Split Layout Control Panel (Top) */}
            <div style={{ display: 'grid', gridTemplateColumns: '3fr 1fr', gap: '24px', marginBottom: '24px' }}>

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

                    {/* Metric Selector Toggle (Now includes ALL groups) */}
                    <div style={{ borderTop: '1px solid var(--glass-border)', paddingTop: '16px' }}>
                        <div
                            style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
                            onClick={() => setShowMetricPanel(!showMetricPanel)}
                        >
                            <label style={{ fontSize: '0.9rem', color: 'var(--text-primary)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <span style={{ fontSize: '1.2rem' }}>📊</span>
                                {txt.customMetrics}
                            </label>
                            <span>{showMetricPanel ? '▲' : '▼'}</span>
                        </div>

                        {showMetricPanel && (
                            <div style={{ marginTop: '16px', animation: 'fadeIn 0.3s' }}>
                                {METRIC_GROUPS.map(group => (
                                    <div key={group.id} style={{ marginBottom: '16px' }}>
                                        <div style={{ fontSize: '0.85rem', color: group.color || 'var(--accent-primary)', fontWeight: 'bold', marginBottom: '8px' }}>
                                            {language === 'zh' ? group.label_zh : group.label_en}
                                        </div>
                                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
                                            {group.metrics.map(metric => (
                                                <label key={metric.key} style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                                                    <input
                                                        type="checkbox"
                                                        checked={selectedMetrics.has(metric.key)}
                                                        onChange={() => toggleMetric(metric.key)}
                                                        style={{ accentColor: 'var(--accent-primary)' }}
                                                    />
                                                    {language === 'zh' ? metric.label_zh : metric.label_en}
                                                </label>
                                            ))}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Right Panel: Actions */}
                <div className="glass-panel" style={{ padding: '24px', borderRadius: '16px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                    {/* (Same advanced options) */}
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

            {/* KPI Cards Section (Middle) - Now Dynamic! */}
            {summaryData && (
                <div style={{ marginBottom: '32px' }}>
                    <h2 style={{ fontSize: '1.2rem', color: '#fbbf24', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        ⭐ {txt.keyMetrics} <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', fontWeight: 'normal' }}>({dateRange.since} ~ {dateRange.until})</span>
                    </h2>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                        {METRIC_GROUPS.map((group, gIdx) => {
                            // Filter metrics for this group that are currently selected
                            const activeGroupMetrics = group.metrics.filter(m => selectedMetrics.has(m.key));

                            // If no metrics in this group are selected, don't render the group title or container
                            if (activeGroupMetrics.length === 0) return null;

                            return (
                                <div key={gIdx}>
                                    <h3 style={{ fontSize: '1rem', color: group.color || '#3b82f6', marginBottom: '12px', borderLeft: `3px solid ${group.color || '#3b82f6'}`, paddingLeft: '8px' }}>
                                        {language === 'zh' ? group.label_zh : group.label_en}
                                    </h3>
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '12px' }}>
                                        {activeGroupMetrics.map(m => (
                                            <div key={m.key} className="glass-panel" style={{ padding: '16px', borderRadius: '12px', borderLeft: '3px solid var(--accent-primary)', background: 'rgba(255,255,255,0.03)' }}>
                                                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '8px', minHeight: '32px' }}>
                                                    {language === 'zh' ? m.label_zh : m.label_en}
                                                </div>
                                                <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'white' }}>
                                                    {renderMetricValue(summaryData[m.key], m.format)}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

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
                                {/* Dynamic Headers */}
                                {activeCols.map(col => (
                                    <th key={col.key} style={{ padding: '12px', minWidth: '100px' }}>
                                        {language === 'zh' ? col.label_zh : col.label_en}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {reportData && reportData.map((row, idx) => (
                                <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                    <td style={{ padding: '12px', fontWeight: 600 }}>{row.name}</td>
                                    {/* Dynamic Cells */}
                                    {activeCols.map(col => {
                                        let val = row[col.key];
                                        // Simple formatting
                                        if (col.format === 'currency') val = `$${val?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                                        else if (col.format === 'percent') val = `${val?.toFixed(2)}%`;
                                        else if (col.format === 'number') val = val?.toLocaleString();

                                        return (
                                            <td key={col.key} style={{ padding: '12px' }}>{val}</td>
                                        );
                                    })}
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
