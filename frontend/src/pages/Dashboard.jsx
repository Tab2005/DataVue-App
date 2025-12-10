import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import KPICard from '../components/KPICard';
import TrendsChart from '../components/TrendsChart';

function Dashboard() {
    // 1. Get Context from Layout
    const { selectedAccountId, user, language } = useOutletContext();

    const [days, setDays] = useState(7);
    const [dashboardData, setDashboardData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Translations
    const t = {
        zh: {
            title: "成效總覽 (Overview)",
            welcome: "歡迎回來，查看您的廣告帳戶成效",
            last7Days: "近 7 天",
            last30Days: "近 30 天",
            spendTrend: "花費趨勢 (Spend Trend)"
        },
        en: {
            title: "Performance Overview",
            welcome: "Welcome back, check your ad account performance.",
            last7Days: "Last 7 Days",
            last30Days: "Last 30 Days",
            spendTrend: "Spend Trend"
        }
    };

    const txt = t[language] || t.zh;

    // 2. Fetch Trigger
    useEffect(() => {
        if (!selectedAccountId) return;

        const fetchData = async () => {
            setLoading(true);
            setError(null); // Clear previous errors
            try {
                const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
                const token = localStorage.getItem('google_token');
                const res = await fetch(`${apiUrl}/api/dashboard-data?account_id=${selectedAccountId}&days=${days}`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (!res.ok) {
                    if (res.status === 401) {
                        // Redirect to login if unauthorized
                        window.location.href = '/login';
                        return;
                    }
                    throw new Error('Data fetch failed');
                }
                const json = await res.json();
                setDashboardData(json); // Response is not wrapped in 'data'
            } catch (err) {
                console.error("Failed to fetch report", err);
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [selectedAccountId, days]);

    // KPI Config with Translations
    const getKpiConfig = (lang) => [
        { key: 'impressions', title: lang === 'zh' ? '曝光 (Impressions)' : 'Impressions', format: 'number' },
        { key: 'link_clicks', title: lang === 'zh' ? '連結點擊 (Link Clicks)' : 'Link Clicks', format: 'number' },
        { key: 'ctr', title: 'CTR', format: 'percent' },
        { key: 'cpc', title: 'CPC', format: 'currency', isInverse: true },
        { key: 'spend', title: lang === 'zh' ? '費用 (Spend)' : 'Spend', format: 'currency', isInverse: true },
        { key: 'purchases', title: lang === 'zh' ? '購買 (Purchases)' : 'Purchases', format: 'number' },
        { key: 'add_to_cart', title: lang === 'zh' ? '購物車 (AddToCart)' : 'Add to Cart', format: 'number' },
        { key: 'roas', title: lang === 'zh' ? '回報率 (ROAS)' : 'ROAS', format: 'float' },
    ];

    const kpiList = getKpiConfig(language);

    return (
        <div style={{ padding: '24px', width: '100%' }}>
            {/* ... Header Omitted ... */}
            <div style={{ marginBottom: '32px', display: 'flex', justifyContent: 'space-between', alignItems: 'end' }}>
                <div>
                    <h1 style={{ fontSize: '1.8rem', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '8px' }}>
                        {txt.title}
                    </h1>
                    <p style={{ color: 'var(--text-secondary)' }}>
                        {txt.welcome}
                    </p>
                </div>
                {/* ... Controls Omitted ... */}
                <div className="glass-panel" style={{ display: 'flex', padding: '4px', borderRadius: '8px' }}>
                    {dashboardData && dashboardData.date_range && (
                        <span style={{
                            color: 'var(--text-secondary)',
                            fontSize: '0.85rem',
                            padding: '0 8px',
                            borderRight: '1px solid var(--glass-border)',
                            display: 'flex',
                            alignItems: 'center'
                        }}>
                            {dashboardData.date_range.start} ~ {dashboardData.date_range.stop}
                        </span>
                    )}
                    <button
                        onClick={() => setDays(7)}
                        style={{
                            background: days === 7 ? 'rgba(255,255,255,0.1)' : 'transparent',
                            color: days === 7 ? 'white' : 'var(--text-secondary)',
                            border: 'none',
                            padding: '6px 16px',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            transition: 'all 0.2s'
                        }}
                    >
                        {txt.last7Days}
                    </button>
                    <button
                        onClick={() => setDays(30)}
                        style={{
                            background: days === 30 ? 'rgba(255,255,255,0.1)' : 'transparent',
                            color: days === 30 ? 'white' : 'var(--text-secondary)',
                            border: 'none',
                            padding: '6px 16px',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            transition: 'all 0.2s'
                        }}
                    >
                        {txt.last30Days}
                    </button>
                </div>
            </div>

            {loading ? (
                <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>載入數據中...</div>
            ) : error ? (
                <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-error)' }}>Error: {error}</div>
            ) : (
                <>
                    {/* KPI Grid */}
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(4, 1fr)',
                        gap: '16px',
                        marginBottom: '24px'
                    }}>
                        {dashboardData && dashboardData.kpi ? (
                            kpiList.map((cfg) => {
                                const dataItem = dashboardData.kpi[cfg.key];
                                if (!dataItem) return null;
                                return (
                                    <KPICard
                                        key={cfg.key}
                                        title={cfg.title}
                                        value={dataItem.value}
                                        sub_value={dataItem.previous}
                                        diff={dataItem.diff}
                                        percent={dataItem.change}
                                        is_increase={dataItem.is_increase}
                                        is_inverse={cfg.isInverse}
                                    />
                                );
                            })
                        ) : (
                            <div style={{ gridColumn: '1 / -1', textAlign: 'center', color: 'gray' }}>No Data</div>
                        )}
                    </div>

                    {/* Charts Row */}
                    <div className="glass-panel" style={{ padding: '24px', borderRadius: '16px', minHeight: '300px' }}>
                        <h3 style={{ margin: '0 0 20px 0', fontSize: '1.1rem', color: 'var(--text-secondary)' }}>{txt.spendTrend}</h3>
                        {dashboardData && dashboardData.chart_data ? (
                            <TrendsChart data={dashboardData.chart_data} dataKey="spend" color="#ef4444" />
                        ) : (
                            <div style={{ textAlign: 'center', color: 'gray', padding: '40px' }}>No Chart Data</div>
                        )}
                    </div>
                </>
            )}
        </div>
    );
}

export default Dashboard;
