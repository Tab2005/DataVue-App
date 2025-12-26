
import React, { useEffect, useState } from 'react';

const GSCStats = ({ language, isMobile = false }) => {
    const t = (zh, en) => language === 'zh' ? zh : en;
    const [sites, setSites] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedSite, setSelectedSite] = useState('');
    const [analytics, setAnalytics] = useState([]);
    const [analyticsLoading, setAnalyticsLoading] = useState(false);

    useEffect(() => {
        fetchSites();
    }, []);

    const fetchSites = async () => {
        try {
            const resp = await fetch('/api/gsc/sites', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('google_token')}` }
            });
            // Check for HTML response again to be safe
            const contentType = resp.headers.get("content-type");
            if (contentType && contentType.indexOf("application/json") !== -1) {
                const data = await resp.json();
                if (!resp.ok) throw new Error(data.detail || 'Failed to fetch sites');
                setSites(data);
                if (data.length > 0) setSelectedSite(data[0].siteUrl);
            } else {
                throw new Error("Server returned non-JSON response");
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (selectedSite) {
            fetchAnalytics(selectedSite);
        }
    }, [selectedSite]);

    const fetchAnalytics = async (siteUrl) => {
        setAnalyticsLoading(true);
        try {
            // Default last 30 days
            const end = new Date();
            const start = new Date();
            start.setDate(end.getDate() - 30);

            const startStr = start.toISOString().split('T')[0];
            const endStr = end.toISOString().split('T')[0];

            const resp = await fetch(`/api/gsc/analytics?site_url=${encodeURIComponent(siteUrl)}&start_date=${startStr}&end_date=${endStr}&dimensions=date`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('google_token')}` }
            });
            const data = await resp.json();
            if (!resp.ok) throw new Error(data.detail);
            setAnalytics(data);
        } catch (err) {
            console.error(err);
        } finally {
            setAnalyticsLoading(false);
        }
    };

    // Responsive Styles
    const containerStyle = {
        display: 'flex',
        flexDirection: 'column',
        gap: isMobile ? '16px' : '24px',
        width: '100%',
        maxWidth: '100%',
        overflow: 'hidden',
        boxSizing: 'border-box'
    };

    const headerStyle = {
        display: 'flex',
        flexDirection: isMobile ? 'column' : 'row',
        alignItems: isMobile ? 'stretch' : 'center',
        gap: isMobile ? '8px' : '16px'
    };

    const labelStyle = {
        color: 'var(--text-primary)',
        fontWeight: '500',
        fontSize: isMobile ? '0.9rem' : '1rem'
    };

    const selectStyle = {
        padding: isMobile ? '10px 12px' : '8px 12px',
        borderRadius: '8px',
        border: '1px solid var(--glass-border)',
        background: 'var(--bg-secondary)',
        color: 'var(--text-primary)',
        outline: 'none',
        fontSize: isMobile ? '0.9rem' : '1rem',
        width: isMobile ? '100%' : 'auto'
    };

    const gridStyle = {
        display: 'grid',
        gridTemplateColumns: isMobile ? 'calc(50% - 4px) calc(50% - 4px)' : 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: isMobile ? '8px' : '16px',
        width: '100%',
        boxSizing: 'border-box'
    };

    const cardStyle = {
        background: 'var(--bg-secondary)',
        padding: isMobile ? '12px' : '20px',
        borderRadius: isMobile ? '8px' : '12px',
        border: '1px solid var(--glass-border)',
        boxShadow: 'var(--shadow-sm)',
        minWidth: 0  // Prevent flex/grid overflow
    };

    const cardLabelStyle = {
        fontSize: isMobile ? '12px' : '14px',
        color: 'var(--text-secondary)',
        marginBottom: '8px'
    };

    const cardValueStyle = {
        fontSize: isMobile ? '16px' : '24px',
        fontWeight: 'bold',
        color: 'var(--text-primary)',
        wordBreak: 'break-word'
    };

    const tableContainerStyle = {
        background: 'var(--bg-secondary)',
        borderRadius: '12px',
        border: '1px solid var(--glass-border)',
        overflow: 'hidden'
    };

    const tableHeaderStyle = {
        padding: isMobile ? '12px 16px' : '16px',
        borderBottom: '1px solid var(--glass-border)',
        fontWeight: 'bold',
        color: 'var(--text-primary)',
        fontSize: isMobile ? '0.95rem' : '1rem'
    };

    const tableScrollStyle = {
        overflowX: 'auto',
        WebkitOverflowScrolling: 'touch',  // Smooth scrolling on iOS
        maxWidth: '100%'
    };

    const tableStyle = {
        width: '100%',
        borderCollapse: 'collapse',
        textAlign: 'left',
        minWidth: '600px' // Always force minimum width to enable scroll
    };

    const thStyle = {
        padding: isMobile ? '10px 12px' : '12px 24px',
        fontSize: isMobile ? '11px' : '12px',
        color: 'var(--text-secondary)',
        textTransform: 'uppercase',
        borderBottom: '1px solid var(--glass-border)',
        whiteSpace: 'nowrap'
    };

    const tdStyle = {
        padding: isMobile ? '12px' : '16px 24px',
        fontSize: isMobile ? '13px' : '14px',
        color: 'var(--text-primary)',
        borderBottom: '1px solid var(--glass-border)'
    };

    if (loading) return (
        <div style={{ padding: '20px', color: 'var(--text-secondary)' }}>
            {t('載入網站列表...', 'Loading sites...')}
        </div>
    );

    if (error) return (
        <div style={{ padding: '20px', color: '#ea4335' }}>
            {t('錯誤:', 'Error:')} {error}
        </div>
    );

    return (
        <div style={containerStyle}>
            <div style={headerStyle}>
                <label style={labelStyle}>{t('選擇資源:', 'Select Property:')}</label>
                <select
                    value={selectedSite}
                    onChange={(e) => setSelectedSite(e.target.value)}
                    style={selectStyle}
                >
                    {sites.map(site => (
                        <option key={site.siteUrl} value={site.siteUrl}>
                            {site.siteUrl} ({site.permissionLevel})
                        </option>
                    ))}
                </select>
            </div>

            {analyticsLoading ? (
                <div style={{ color: 'var(--text-secondary)' }}>
                    {t('載入數據中...', 'Loading analytics...')}
                </div>
            ) : (
                <div style={gridStyle}>
                    {/* Summary Cards */}
                    <div style={cardStyle}>
                        <div style={cardLabelStyle}>{t('總點擊數 (30天)', 'Total Clicks (30d)')}</div>
                        <div style={cardValueStyle}>
                            {analytics.reduce((acc, row) => acc + row.clicks, 0).toLocaleString()}
                        </div>
                    </div>
                    <div style={cardStyle}>
                        <div style={cardLabelStyle}>{t('總曝光數 (30天)', 'Total Impressions (30d)')}</div>
                        <div style={cardValueStyle}>
                            {analytics.reduce((acc, row) => acc + row.impressions, 0).toLocaleString()}
                        </div>
                    </div>
                    <div style={cardStyle}>
                        <div style={cardLabelStyle}>{t('平均點閱率', 'Avg CTR')}</div>
                        <div style={cardValueStyle}>
                            {(analytics.reduce((acc, row) => acc + row.ctr, 0) / (analytics.length || 1) * 100).toFixed(2)}%
                        </div>
                    </div>
                    <div style={cardStyle}>
                        <div style={cardLabelStyle}>{t('平均排名', 'Avg Position')}</div>
                        <div style={cardValueStyle}>
                            {(analytics.reduce((acc, row) => acc + row.position, 0) / (analytics.length || 1)).toFixed(1)}
                        </div>
                    </div>
                </div>
            )}

            {/* Table Section */}
            <div style={tableContainerStyle}>
                <div style={tableHeaderStyle}>{t('每日成效', 'Daily Performance')}</div>
                <div style={tableScrollStyle}>
                    <table style={tableStyle}>
                        <thead>
                            <tr style={{ background: 'var(--bg-hover)' }}>
                                <th style={thStyle}>{t('日期', 'Date')}</th>
                                <th style={thStyle}>{t('點擊', 'Clicks')}</th>
                                <th style={thStyle}>{t('曝光', 'Impressions')}</th>
                                <th style={thStyle}>{t('點閱率', 'CTR')}</th>
                                <th style={thStyle}>{t('排名', 'Position')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {analytics.map((row, idx) => (
                                <tr
                                    key={idx}
                                    style={{ transition: 'background 0.2s' }}
                                    onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-hover)'}
                                    onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                                >
                                    <td style={tdStyle}>{row.keys && row.keys[0]}</td>
                                    <td style={tdStyle}>{row.clicks}</td>
                                    <td style={tdStyle}>{row.impressions}</td>
                                    <td style={tdStyle}>{(row.ctr * 100).toFixed(2)}%</td>
                                    <td style={tdStyle}>{row.position.toFixed(1)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default GSCStats;

