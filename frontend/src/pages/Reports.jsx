// frontend/src/pages/Reports.jsx
import React, { useState, useEffect } from 'react';
import { useOutletContext, Link } from 'react-router-dom';
import { FiPlus, FiFilter, FiSearch, FiFileText, FiChevronDown, FiAlertCircle, FiCalendar, FiActivity } from 'react-icons/fi';
import { reportService } from '../services/reportService';
import { ReportCard } from '../components/Reports';
import PageLoading from '../components/PageLoading';

const Reports = () => {
    const { user, language, selectedTeamId } = useOutletContext();
    const [reports, setReports] = useState([]);
    const [schedules, setSchedules] = useState([]);
    const [loading, setLoading] = useState(true);
    const [loadingSchedules, setLoadingSchedules] = useState(false);
    const [error, setError] = useState(null);
    const [filter, setFilter] = useState('all'); // all, draft, generated, archived
    const [searchQuery, setSearchQuery] = useState('');
    const [viewMode, setViewMode] = useState('reports'); // reports, schedules

    const t = (en, zh) => (language === 'zh' ? zh : en);

    const fetchReports = async () => {
        setLoading(true);
        try {
            const res = await reportService.list(selectedTeamId);
            setReports(res || []);
            setError(null);
        } catch (err) {
            console.error('Failed to fetch reports:', err);
            setError(t('Failed to load reports.', '載入週報失敗。'));
        } finally {
            setLoading(false);
        }
    };

    const fetchSchedules = async () => {
        setLoadingSchedules(true);
        try {
            const res = await reportService.listSchedules(selectedTeamId);
            setSchedules(res || []);
        } catch (err) {
            console.error('Failed to fetch schedules:', err);
        } finally {
            setLoadingSchedules(false);
        }
    };

    useEffect(() => {
        fetchReports();
        if (viewMode === 'schedules') fetchSchedules();
    }, [selectedTeamId, viewMode]);

    const handleDelete = async (id) => {
        if (!window.confirm(t('Are you sure you want to delete this report?', '您確定要刪除這份週報嗎？'))) return;
        try {
            await reportService.delete(id);
            setReports(prev => prev.filter(r => r.id !== id));
        } catch (err) {
            console.error('Delete failed:', err);
        }
    };

    const handleDeleteSchedule = async (id) => {
        if (!window.confirm(t('Are you sure you want to delete this schedule?', '您確定要刪除此排程嗎？'))) return;
        try {
            await reportService.deleteSchedule(id);
            setSchedules(prev => prev.filter(s => s.id !== id));
        } catch (err) {
            console.error('Delete schedule failed:', err);
        }
    };

    const handleToggleSchedule = async (id, isActive) => {
        try {
            await reportService.updateSchedule(id, { is_active: !isActive });
            setSchedules(prev => prev.map(s => s.id === id ? { ...s, is_active: !isActive } : s));
        } catch (err) {
            console.error('Toggle schedule failed:', err);
        }
    };

    const filteredReports = reports.filter(r => {
        const matchesFilter = filter === 'all' || r.status === filter;
        const matchesSearch = r.name.toLowerCase().includes(searchQuery.toLowerCase());
        return matchesFilter && matchesSearch;
    });

    if (loading && viewMode === 'reports') return <PageLoading />;

    return (
        <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
            {/* Header Area */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                <div>
                    <h1 style={{ fontSize: '2.2rem', fontWeight: 'bold', color: 'var(--text-primary)', margin: '0', display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <FiFileText size={36} color="var(--accent-primary)" />
                        {viewMode === 'reports' ? t('Weekly Reports', '週報管理') : t('Automated Schedules', '自動排程管理')}
                    </h1>
                </div>
                <div style={{ display: 'flex', gap: '12px' }}>
                     {/* Tab Switcher */}
                    <div style={{ display: 'flex', backgroundColor: 'var(--bg-secondary)', padding: '4px', borderRadius: '10px', border: '1px solid var(--glass-border)' }}>
                        <button 
                            onClick={() => setViewMode('reports')}
                            style={{ 
                                padding: '8px 16px', borderRadius: '8px', border: 'none', 
                                backgroundColor: viewMode === 'reports' ? 'var(--bg-hover)' : 'transparent',
                                color: viewMode === 'reports' ? 'var(--accent-primary)' : 'var(--text-tertiary)',
                                cursor: 'pointer', fontWeight: '600', transition: 'all 0.2s'
                            }}
                        >
                            {t('Reports', '所有週報')}
                        </button>
                        <button 
                            onClick={() => setViewMode('schedules')}
                            style={{ 
                                padding: '8px 16px', borderRadius: '8px', border: 'none', 
                                backgroundColor: viewMode === 'schedules' ? 'var(--bg-hover)' : 'transparent',
                                color: viewMode === 'schedules' ? 'var(--accent-primary)' : 'var(--text-tertiary)',
                                cursor: 'pointer', fontWeight: '600', transition: 'all 0.2s'
                            }}
                        >
                            {t('Schedules', '自動排程')}
                        </button>
                    </div>

                    <Link
                        to="/reports/new"
                        style={{
                            padding: '10px 20px', backgroundColor: 'var(--accent-primary)', color: 'white', borderRadius: '10px',
                            textDecoration: 'none', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px'
                        }}
                    >
                        <FiPlus size={20} />
                        {t('Create New', '建立新項目')}
                    </Link>
                </div>
            </div>

            {viewMode === 'reports' ? (
                <>
                    {/* Filter Bar for Reports */}
                    <div style={{ display: 'flex', gap: '16px', marginBottom: '24px' }}>
                        <div style={{ position: 'relative', flex: 1 }}>
                            <FiSearch style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-tertiary)' }} />
                            <input
                                type="text"
                                placeholder={t('Search reports...', '搜尋報表...')}
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                style={{
                                    width: '100%', padding: '12px 12px 12px 42px', backgroundColor: 'var(--bg-secondary)',
                                    border: '1px solid var(--glass-border)', borderRadius: '10px', color: 'var(--text-primary)'
                                }}
                            />
                        </div>
                        <div style={{ display: 'flex', gap: '8px', padding: '4px', backgroundColor: 'var(--bg-secondary)', borderRadius: '10px' }}>
                            {['all', 'draft', 'generated', 'archived'].map(f => (
                                <button key={f} onClick={() => setFilter(f)}
                                    style={{
                                        padding: '8px 16px', borderRadius: '8px', border: 'none',
                                        backgroundColor: filter === f ? 'var(--bg-hover)' : 'transparent',
                                        color: filter === f ? 'var(--accent-primary)' : 'var(--text-tertiary)',
                                        cursor: 'pointer', fontSize: '0.9rem'
                                    }}>
                                    {f === 'all' && t('All', '全部')}
                                    {f === 'draft' && t('Drafts', '草稿')}
                                    {f === 'generated' && t('Generated', '已產生')}
                                    {f === 'archived' && t('Archived', '已封存')}
                                </button>
                            ))}
                        </div>
                    </div>

                    {filteredReports.length > 0 ? (
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '24px' }}>
                            {filteredReports.map(report => (
                                <ReportCard key={report.id} report={report} onDelete={handleDelete} language={language} />
                            ))}
                        </div>
                    ) : (
                        <div style={{ textAlign: 'center', padding: '100px', backgroundColor: 'var(--bg-secondary)', borderRadius: '20px', border: '2px dashed var(--glass-border)' }}>
                            <FiFileText size={64} color="var(--glass-border)" style={{ marginBottom: '20px' }} />
                            <h3 style={{ color: 'white' }}>{t('No reports found', '目前沒有週報')}</h3>
                        </div>
                    )}
                </>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    {loadingSchedules ? <PageLoading /> : schedules.length > 0 ? (
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))', gap: '24px' }}>
                            {schedules.map(s => (
                                <div key={s.id} style={{
                                    backgroundColor: 'var(--bg-secondary)', padding: '24px', borderRadius: '16px',
                                    border: '1px solid var(--glass-border)', position: 'relative',
                                    transition: 'transform 0.2s',
                                    opacity: s.is_active ? 1 : 0.6
                                }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
                                        <div>
                                            <h3 style={{ color: 'var(--text-primary)', margin: '0 0 4px 0' }}>{s.name}</h3>
                                            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0 }}>
                                                {s.ad_account_name || s.ad_account_id}
                                            </p>
                                        </div>
                                        <div style={{ display: 'flex', gap: '8px' }}>
                                            <button 
                                                onClick={() => handleToggleSchedule(s.id, s.is_active)}
                                                style={{ 
                                                    padding: '6px 12px', borderRadius: '6px', border: '1px solid var(--glass-border)',
                                                    backgroundColor: s.is_active ? 'rgba(16, 185, 129, 0.1)' : 'rgba(255,255,255,0.05)',
                                                    color: s.is_active ? '#10b981' : 'var(--text-tertiary)', cursor: 'pointer'
                                                }}
                                            >
                                                {s.is_active ? t('Active', '啟用中') : t('Paused', '已暫停')}
                                            </button>
                                            <button 
                                                onClick={() => handleDeleteSchedule(s.id)}
                                                style={{ padding: '6px', color: '#ef4444', backgroundColor: 'transparent', border: 'none', cursor: 'pointer' }}
                                            >
                                                {t('Delete', '刪除')}
                                            </button>
                                        </div>
                                    </div>
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', fontSize: '0.9rem' }}>
                                        <div style={{ backgroundColor: 'rgba(255,255,255,0.03)', padding: '6px 12px', borderRadius: '6px', color: 'var(--text-secondary)' }}>
                                            <FiCalendar style={{ marginRight: '6px', verticalAlign: 'middle' }} />
                                            {s.frequency === 'daily' && t('Daily', '每日')}
                                            {s.frequency === 'weekly' && `${t('Weekly', '每週')} (${t('Mon', '週一')})`}
                                            {s.frequency === 'monthly' && `${t('Monthly', '每月')} (${s.day_of_month})`}
                                            {` @ ${s.time_of_day}`}
                                        </div>
                                        <div style={{ backgroundColor: 'rgba(255,255,255,0.03)', padding: '6px 12px', borderRadius: '6px', color: 'var(--text-secondary)' }}>
                                            {t('Breakdown', '分析層級')}: {s.breakdown}
                                        </div>
                                    </div>
                                    <div style={{ marginTop: '16px', fontSize: '0.8rem', color: 'var(--text-tertiary)', borderTop: '1px solid var(--glass-border)', paddingTop: '12px' }}>
                                        {t('Last Run', '上次執行')}: {s.last_run ? new Date(s.last_run).toLocaleString() : t('Never', '尚未執行')}
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div style={{ textAlign: 'center', padding: '100px', backgroundColor: 'var(--bg-secondary)', borderRadius: '20px', border: '2px dashed var(--glass-border)' }}>
                            <FiActivity size={64} color="var(--glass-border)" style={{ marginBottom: '20px' }} />
                            <h3 style={{ color: 'white' }}>{t('No automated schedules found', '目前沒有自動化排程')}</h3>
                            <p style={{ color: 'var(--text-secondary)' }}>{t('Create one to automate your weekly updates.', '建立一個排程來自動化您的每週數據更新。')}</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default Reports;

