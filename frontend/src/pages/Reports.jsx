// frontend/src/pages/Reports.jsx
import React, { useState, useEffect } from 'react';
import { useOutletContext, Link } from 'react-router-dom';
import { FiPlus, FiFilter, FiSearch, FiFileText, FiChevronDown, FiAlertCircle } from 'react-icons/fi';
import { reportService } from '../services/reportService';
import { ReportCard } from '../components/Reports';
import PageLoading from '../components/PageLoading';

const Reports = () => {
    const { user, language, selectedTeamId } = useOutletContext();
    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filter, setFilter] = useState('all'); // all, draft, generated, archived
    const [searchQuery, setSearchQuery] = useState('');

    const t = (en, zh) => (language === 'zh' ? zh : en);

    const fetchReports = async () => {
        setLoading(true);
        try {
            const res = await reportService.list(selectedTeamId);
            setReports(res.data || []);
            setError(null);
        } catch (err) {
            console.error('Failed to fetch reports:', err);
            setError(t('Failed to load reports. Please check your connection.', '載入週報失敗，請檢查網路連線。'));
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchReports();
    }, [selectedTeamId]);

    const handleDelete = async (id) => {
        if (!window.confirm(t('Are you sure you want to delete this report?', '您確定要刪除這份週報嗎？'))) return;
        try {
            await reportService.delete(id);
            setReports(prev => prev.filter(r => r.id !== id));
        } catch (err) {
            console.error('Delete failed:', err);
            alert(t('Delete failed', '刪除失敗'));
        }
    };

    const filteredReports = reports.filter(r => {
        const matchesFilter = filter === 'all' || r.status === filter;
        const matchesSearch = r.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                             (r.ad_account_name || '').toLowerCase().includes(searchQuery.toLowerCase());
        return matchesFilter && matchesSearch;
    });

    if (loading) return <PageLoading />;

    return (
        <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
            {/* Header Area */}
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '32px',
                flexWrap: 'wrap',
                gap: '16px'
            }}>
                <div>
                    <h1 style={{ fontSize: '2.2rem', fontWeight: 'bold', color: 'var(--text-primary)', margin: '0 0 4px 0', display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <FiFileText size={36} color="var(--accent-primary)" />
                        {t('Weekly Reports', '週報管理')}
                    </h1>
                    <p style={{ color: 'var(--text-secondary)', margin: 0 }}>
                        {t('Create and manage your weekly multi-platform advertising reports.', '建立與管理您的每週廣告多平台成效報表。')}
                    </p>
                </div>
                <Link
                    to="/reports/new"
                    style={{
                        padding: '12px 24px',
                        backgroundColor: 'var(--accent-primary)',
                        color: 'white',
                        borderRadius: '12px',
                        textDecoration: 'none',
                        fontWeight: 'bold',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        transition: 'transform 0.2s, box-shadow 0.2s',
                        boxShadow: '0 4px 12px rgba(45, 136, 255, 0.3)'
                    }}
                    onMouseEnter={(e) => {
                        e.currentTarget.style.transform = 'translateY(-2px)';
                        e.currentTarget.style.boxShadow = '0 6px 16px rgba(45, 136, 255, 0.4)';
                    }}
                    onMouseLeave={(e) => {
                        e.currentTarget.style.transform = 'translateY(0)';
                        e.currentTarget.style.boxShadow = '0 4px 12px rgba(45, 136, 255, 0.3)';
                    }}
                >
                    <FiPlus size={20} />
                    {t('Create New Report', '建立新週報')}
                </Link>
            </div>

            {/* Filter Bar */}
            <div style={{
                display: 'flex',
                gap: '16px',
                marginBottom: '24px',
                flexWrap: 'wrap',
                alignItems: 'center'
            }}>
                <div style={{ position: 'relative', flex: 1, minWidth: '200px' }}>
                    <FiSearch style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-tertiary)' }} />
                    <input
                        type="text"
                        placeholder={t('Search reports...', '搜尋報表...')}
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        style={{
                            width: '100%',
                            padding: '12px 12px 12px 42px',
                            backgroundColor: 'var(--bg-secondary)',
                            border: '1px solid var(--glass-border)',
                            borderRadius: '10px',
                            color: 'var(--text-primary)',
                            fontSize: '0.95rem'
                        }}
                    />
                </div>

                <div style={{ display: 'flex', gap: '8px', padding: '4px', backgroundColor: 'var(--bg-secondary)', borderRadius: '10px' }}>
                    {['all', 'draft', 'generated', 'archived'].map(f => (
                        <button
                            key={f}
                            onClick={() => setFilter(f)}
                            style={{
                                padding: '8px 16px',
                                borderRadius: '8px',
                                border: 'none',
                                backgroundColor: filter === f ? 'var(--bg-hover)' : 'transparent',
                                color: filter === f ? 'var(--accent-primary)' : 'var(--text-tertiary)',
                                cursor: 'pointer',
                                fontWeight: filter === f ? 'bold' : 'normal',
                                transition: 'all 0.2s',
                                fontSize: '0.9rem'
                            }}
                        >
                            {f === 'all' && t('All', '全部')}
                            {f === 'draft' && t('Drafts', '草稿')}
                            {f === 'generated' && t('Generated', '已產生')}
                            {f === 'archived' && t('Archived', '已封存')}
                        </button>
                    ))}
                </div>
            </div>

            {/* Error Message */}
            {error && (
                <div style={{
                    padding: '20px',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    borderRadius: '12px',
                    color: '#ef4444',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    marginBottom: '24px'
                }}>
                    <FiAlertCircle size={24} />
                    {error}
                    <button
                        onClick={fetchReports}
                        style={{ marginLeft: 'auto', backgroundColor: '#ef4444', color: 'white', border: 'none', padding: '6px 16px', borderRadius: '6px', cursor: 'pointer' }}>
                        {t('Retry', '重試')}
                    </button>
                </div>
            )}

            {/* Reports Grid */}
            {!loading && filteredReports.length > 0 ? (
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
                    gap: '24px'
                }}>
                    {filteredReports.map(report => (
                        <ReportCard
                            key={report.id}
                            report={report}
                            onDelete={handleDelete}
                            language={language}
                        />
                    ))}
                </div>
            ) : (
                <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '80px 20px',
                    backgroundColor: 'var(--bg-secondary)',
                    borderRadius: '20px',
                    border: '2px dashed var(--glass-border)',
                    textAlign: 'center',
                    gap: '16px'
                }}>
                    <FiFileText size={64} color="var(--glass-border)" />
                    <div style={{ maxWidth: '400px' }}>
                        <h2 style={{ fontSize: '1.5rem', color: 'var(--text-primary)', marginBottom: '8px' }}>
                            {t('No reports found', '目前沒有週報')}
                        </h2>
                        <p style={{ color: 'var(--text-secondary)' }}>
                            {t('Start by creating your first weekly performance report to track your ad campaigns.', '開始建立您的第一份成效週報，輕鬆追蹤廣告活動表現。')}
                        </p>
                    </div>
                    <Link
                        to="/reports/new"
                        style={{
                            marginTop: '12px',
                            padding: '12px 32px',
                            backgroundColor: 'transparent',
                            color: 'var(--accent-primary)',
                            borderRadius: '10px',
                            border: '1px solid var(--accent-primary)',
                            textDecoration: 'none',
                            fontWeight: 'bold',
                            transition: 'all 0.2s'
                        }}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.backgroundColor = 'var(--accent-primary)';
                            e.currentTarget.style.color = 'white';
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.backgroundColor = 'transparent';
                            e.currentTarget.style.color = 'var(--accent-primary)';
                        }}
                    >
                        {t('Create New Report', '建立新週報')}
                    </Link>
                </div>
            )}
        </div>
    );
};

export default Reports;
