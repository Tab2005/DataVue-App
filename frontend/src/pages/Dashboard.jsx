import React, { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import KPICard from '../components/KPICard';
import TrendsChart from '../components/TrendsChart';

function Dashboard() {
    const [language, setLanguage] = useState('zh');
    const [accounts, setAccounts] = useState([]);
    const [selectedAccountId, setSelectedAccountId] = useState('');
    const [data, setData] = useState({
        kpi: [
            { label: "Total Followers", value: "---", change: "---", isPositive: true },
            { label: "Engagement Rate", value: "---", change: "---", isPositive: true },
            { label: "Impressions", value: "---", change: "---", isPositive: false },
            { label: "Reach", value: "---", change: "---", isPositive: true },
        ],
        chart_data: []
    });

    // 1. Fetch Ad Accounts on Mount
    useEffect(() => {
        // 取得 API 網址：優先使用環境變數 VITE_API_URL，如果未設定則預設為 localhost (本地開發用)
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const token = localStorage.getItem('google_token');

        fetch(`${apiUrl}/api/ad-accounts`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
            .then(res => res.json())
            .then(accList => {
                if (Array.isArray(accList) && accList.length > 0) {
                    setAccounts(accList);
                    // Optional: Default select first one
                    setSelectedAccountId(accList[0].id);
                }
            })
            .catch(err => console.error("Failed to fetch accounts", err));
    }, []);

    // 2. Fetch Report Data ONLY when triggered
    const handleGenerateReport = () => {
        if (!selectedAccountId) return;

        // Show loading state implicitly or explicit (optional)
        setData(prev => ({ ...prev, kpi: prev.kpi.map(k => ({ ...k, value: "Loading..." })) }));

        // 取得 API 網址
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const token = localStorage.getItem('google_token');

        fetch(`${apiUrl}/api/dashboard-data?account_id=${selectedAccountId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
            .then(res => res.json())
            .then(resData => {
                if (resData) {
                    setData({
                        kpi: resData.kpi ? resData.kpi.map(item => ({
                            ...item,
                            isPositive: item.change.startsWith('+')
                        })) : [],
                        chart_data: resData.chart_data || []
                    });
                }
            })
            .catch(err => {
                console.error("Failed to fetch report", err);
                // Reset or show error
            });
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
                    onGenerateReport={handleGenerateReport}
                />

                <main style={{
                    marginTop: '70px',
                    padding: '32px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '32px'
                }}>

                    {/* KPI Grid */}
                    <section style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                        gap: '24px'
                    }}>
                        {data.kpi.map((kpi, idx) => (
                            <KPICard
                                key={idx}
                                title={kpi.label}
                                value={kpi.value}
                                change={kpi.change}
                                isPositive={kpi.isPositive} // Derived from change string
                            />
                        ))}
                    </section>

                    {/* Charts Area */}
                    <section>
                        <TrendsChart data={data.chart_data} language={language} />
                    </section>

                </main>
            </div>
        </div>
    );
}

export default Dashboard;
