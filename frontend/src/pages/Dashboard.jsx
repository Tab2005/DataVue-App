import React, { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import KPICard from '../components/KPICard';
import TrendsChart from '../components/TrendsChart';

function Dashboard() {
    const [language, setLanguage] = useState('zh');
    const [accounts, setAccounts] = useState([]);
    const [selectedAccountId, setSelectedAccountId] = useState('');
    const [days, setDays] = useState(7); // Default to 7 days
    const [data, setData] = useState({
        kpi: [], // Will be populated by API (Array of 8 items)
        chart_data: [],
        date_range: null
    });
    const [loading, setLoading] = useState(false);

    // 1. Fetch Ad Accounts on Mount with Retry Logic
    useEffect(() => {
        const fetchAccounts = async (retries = 3) => {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const token = localStorage.getItem('google_token');

            try {
                const response = await fetch(`${apiUrl}/api/ad-accounts`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const accList = await response.json();

                if (Array.isArray(accList)) {
                    setAccounts(accList);
                    if (accList.length > 0) {
                        setSelectedAccountId(accList[0].id);
                    }
                }
            } catch (err) {
                console.error(`Failed to fetch accounts (Retries left: ${retries})`, err);
                if (retries > 0) {
                    setTimeout(() => fetchAccounts(retries - 1), 1500); // Retry after 1.5s
                }
            }
        };

        fetchAccounts();
    }, []);

    // 2. Fetch Report Data Triggered by Account or specific interaction
    // We wrap it in a function to call when 'Generate Report' or 'Days Toggle' changes
    const fetchReport = (daysOverride = days) => {
        if (!selectedAccountId) return;

        setLoading(true);
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const token = localStorage.getItem('google_token');

        fetch(`${apiUrl}/api/dashboard-data?account_id=${selectedAccountId}&days=${daysOverride}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
            .then(res => res.json())
            .then(resData => {
                if (resData) {
                    setData({
                        kpi: resData.kpi || [],
                        chart_data: resData.chart_data || [],
                        date_range: resData.date_range || null
                    });
                }
            })
            .catch(err => {
                console.error("Failed to fetch report", err);
            })
            .finally(() => setLoading(false));
    };

    // Auto-fetch when selectedAccountId changes and we switch days
    useEffect(() => {
        if (selectedAccountId) {
            fetchReport(days);
        }
    }, [selectedAccountId, days]);

    const handleDaysChange = (newDays) => {
        setDays(newDays);
    };

    return (
        <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-primary)' }}>
            <Sidebar language={language} />

            <div style={{ flex: 1, marginLeft: '240px' }}>
                <Header
                    language={language}
                    setLanguage={setLanguage}
                    accounts={accounts}
                    selectedAccountId={selectedAccountId}
                    setSelectedAccountId={setSelectedAccountId}
                    onGenerateReport={() => fetchReport(days)}
                />

                <main style={{
                    marginTop: '70px',
                    padding: '32px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '24px'
                }}>
                    {/* Performance Overview Section */}
                    <section className="glass-panel" style={{
                        padding: '24px',
                        borderRadius: 'var(--radius-xl)',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '24px'
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>
                                {language === 'zh' ? '成效總覽' : 'Performance Overview'}
                            </h2>

                            <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                                {data.date_range && (
                                    <span style={{
                                        color: 'var(--text-secondary)',
                                        fontSize: '0.85rem',
                                        background: 'rgba(255,255,255,0.03)',
                                        padding: '4px 8px',
                                        borderRadius: '4px',
                                        border: '1px solid var(--glass-border)'
                                    }}>
                                        {data.date_range.start} ~ {data.date_range.stop}
                                    </span>
                                )}

                                <div style={{ display: 'flex', gap: '8px' }}>
                                    <button
                                        onClick={() => handleDaysChange(7)}
                                        style={{
                                            padding: '6px 16px',
                                            borderRadius: '6px',
                                            border: days === 7 ? '1px solid var(--accent-primary)' : '1px solid var(--glass-border)',
                                            background: days === 7 ? 'var(--accent-primary)' : 'transparent',
                                            color: days === 7 ? 'white' : 'var(--text-secondary)',
                                            cursor: 'pointer',
                                            fontSize: '0.9rem'
                                        }}
                                    >
                                        Last 7 Days
                                    </button>
                                    <button
                                        onClick={() => handleDaysChange(30)}
                                        style={{
                                            padding: '6px 16px',
                                            borderRadius: '6px',
                                            border: days === 30 ? '1px solid var(--accent-primary)' : '1px solid var(--glass-border)',
                                            background: days === 30 ? 'var(--accent-primary)' : 'transparent',
                                            color: days === 30 ? 'white' : 'var(--text-secondary)',
                                            cursor: 'pointer',
                                            fontSize: '0.9rem'
                                        }}
                                    >
                                        Last 30 Days
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* KPI Grid - 4 Columns x 2 Rows */}
                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(4, 1fr)',
                            gap: '16px',
                            opacity: loading ? 0.5 : 1, // Visual feedback for loading
                            transition: 'opacity 0.2s'
                        }}>
                            {data.kpi.length === 0 ? (
                                // Placeholders or Empty State
                                Array(8).fill(0).map((_, i) => (
                                    <div key={i} style={{ height: '120px', background: 'rgba(255,255,255,0.02)', borderRadius: 'var(--radius-lg)' }}></div>
                                ))
                            ) : (
                                data.kpi.map((kpi, idx) => (
                                    <KPICard
                                        key={idx}
                                        title={kpi.label}
                                        value={kpi.value}
                                        sub_value={kpi.sub_value}
                                        diff={kpi.diff}
                                        percent={kpi.percent}
                                        is_increase={kpi.is_increase}
                                        is_inverse={kpi.is_inverse}
                                    />
                                ))
                            )}
                        </div>
                    </section>

                    {/* Charts Area */}
                    <section>
                        <div style={{ marginBottom: '16px' }}>
                            <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>費用走勢 (Cost Trend)</h3>
                        </div>
                        <TrendsChart data={data.chart_data} language={language} title="Cost Trend" />
                    </section>

                </main>
            </div>
        </div>
    );
}

export default Dashboard;
