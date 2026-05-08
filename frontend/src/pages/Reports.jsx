// frontend/src/pages/Reports.jsx
import React, { useState, useEffect } from 'react';
import { useOutletContext, Link, useNavigate } from 'react-router-dom';
import { FiPlus, FiFilter, FiSearch, FiFileText, FiChevronDown, FiAlertCircle, FiCalendar, FiActivity, FiEdit, FiTrash2 } from 'react-icons/fi';
import { reportService } from '../services/reportService';
import { ReportCard } from '../components/Reports';
import PageLoading from '../components/PageLoading';

const Reports = () => {
    const navigate = useNavigate();
    const { user, language, selectedTeamId } = useOutletContext();
    const [reports, setReports] = useState([]);
    const [schedules, setSchedules] = useState([]);
    const [loading, setLoading] = useState(true);
    const [loadingSchedules, setLoadingSchedules] = useState(false);
    const [error, setError] = useState(null);
    const [filter, setFilter] = useState('all'); // all, draft, generated, archived
    const [searchQuery, setSearchQuery] = useState('');
    const [debouncedSearch, setDebouncedSearch] = useState('');
    const [viewMode, setViewMode] = useState('reports'); // reports, schedules
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [totalCount, setTotalCount] = useState(0);

    const t = (en, zh) => (language === 'zh' ? zh : en);

    // Search Debounce
    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedSearch(searchQuery);
            setPage(1);
        }, 500);
        return () => clearTimeout(timer);
    }, [searchQuery]);

    const fetchReports = async () => {
        if (viewMode !== 'reports') return;
        setLoading(true);
        try {
            const res = await reportService.list({
                team_id: selectedTeamId,
                status: filter,
                search: debouncedSearch,
                page,
                page_size: 12
            });
            setReports(res.items || []);
            setTotalPages(res.total_pages || 1);
            setTotalCount(res.total_count || 0);
            setError(null);
        } catch (err) {
            console.error('Failed to fetch reports:', err);
            setError(t('Failed to load reports.', '載入報表失敗。'));
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
    }, [selectedTeamId, filter, debouncedSearch, page, viewMode]);

    useEffect(() => {
        if (viewMode === 'schedules') fetchSchedules();
    }, [selectedTeamId, viewMode]);

    const handleDelete = async (id) => {
        if (!window.confirm(t('Are you sure you want to delete this report?', '您確定要刪除這份報表嗎？'))) return;
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

    const handleFilterChange = (newFilter) => {
        setFilter(newFilter);
        setPage(1); // Reset to first page
    };

    if (loading && viewMode === 'reports') return <PageLoading />;

    return (
        <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
            {/* Header Area */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                <div>
                    <h1 style={{ fontSize: '2.2rem', fontWeight: 'bold', color: 'var(--text-primary)', margin: '0', display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <FiFileText size={36} color="var(--accent-primary)" />
                        {viewMode === 'reports' ? t('Reports', '報表管理') : t('Automated Schedules', '自動排程管理')}
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
                            {t('Reports', '所有報表')}
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
                                <button key={f} onClick={() => handleFilterChange(f)}
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

                    {reports.length > 0 ? (
                        <>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '24px' }}>
                                {reports.map(report => (
                                    <ReportCard key={report.id} report={report} onDelete={handleDelete} language={language} />
                                ))}
                            </div>

                            {/* Pagination Controls */}
                            {totalPages > 1 && (
                                <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px', marginTop: '40px', paddingBottom: '20px' }}>
                                    <button 
                                        disabled={page === 1}
                                        onClick={() => { setPage(p => p - 1); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
                                        style={{ 
                                            padding: '8px 12px', borderRadius: '8px', border: '1px solid var(--glass-border)',
                                            backgroundColor: 'var(--bg-secondary)', color: page === 1 ? 'var(--text-tertiary)' : 'var(--text-primary)',
                                            cursor: page === 1 ? 'not-allowed' : 'pointer'
                                        }}
                                    >
                                        {t('Prev', '上一頁')}
                                    </button>
                                    
                                    <div style={{ display: 'flex', gap: '4px' }}>
                                        {[...Array(totalPages)].map((_, i) => {
                                            const p = i + 1;
                                            // 簡單的摘要邏輯：只顯示前後兩頁
                                            if (totalPages > 7 && Math.abs(p - page) > 2 && p !== 1 && p !== totalPages) {
                                                if (Math.abs(p - page) === 3) return <span key={p} style={{ color: 'var(--text-tertiary)', padding: '0 4px' }}>...</span>;
                                                return null;
                                            }
                                            return (
                                                <button 
                                                    key={p}
                                                    onClick={() => { setPage(p); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
                                                    style={{ 
                                                        width: '36px', height: '36px', borderRadius: '8px', border: 'none',
                                                        backgroundColor: page === p ? 'var(--accent-primary)' : 'var(--bg-secondary)',
                                                        color: page === p ? 'white' : 'var(--text-secondary)',
                                                        cursor: page === p ? 'not-allowed' : 'pointer', fontWeight: 'bold'
                                                    }}
                                                >
                                                    {p}
                                                </button>
                                            );
                                        })}
                                    </div>

                                    <button 
                                        disabled={page === totalPages}
                                        onClick={() => { setPage(p => p + 1); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
                                        style={{ 
                                            padding: '8px 12px', borderRadius: '8px', border: '1px solid var(--glass-border)',
                                            backgroundColor: 'var(--bg-secondary)', color: page === totalPages ? 'var(--text-tertiary)' : 'var(--text-primary)',
                                            cursor: page === totalPages ? 'not-allowed' : 'pointer'
                                        }}
                                    >
                                        {t('Next', '下一頁')}
                                    </button>
                                </div>
                            )}
                        </>
                    ) : (
                        <div style={{ textAlign: 'center', padding: '100px', backgroundColor: 'var(--bg-secondary)', borderRadius: '20px', border: '2px dashed var(--glass-border)' }}>
                            <FiFileText size={64} color="var(--glass-border)" style={{ marginBottom: '20px' }} />
                            <h3 style={{ color: 'white' }}>{t('No reports found', '目前沒有報表')}</h3>
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
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px', gap: '12px' }}>
                                        <div style={{ flex: 1, minWidth: 0 }}>
                                            <h3 style={{ color: 'var(--text-primary)', margin: '0 0 4px 0', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={s.name}>
                                                {s.name}
                                            </h3>
                                            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                                {s.ad_account_name || s.ad_account_id}
                                            </p>
                                        </div>
                                        <div style={{ display: 'flex', gap: '4px', alignItems: 'center', flexShrink: 0 }}>
                                            <button 
                                                onClick={() => handleToggleSchedule(s.id, s.is_active)}
                                                style={{ 
                                                    padding: '4px 10px', borderRadius: '6px', border: '1px solid var(--glass-border)',
                                                    backgroundColor: s.is_active ? 'rgba(16, 185, 129, 0.1)' : 'rgba(255,255,255,0.05)',
                                                    color: s.is_active ? '#10b981' : 'var(--text-tertiary)', cursor: 'pointer',
                                                    fontSize: '0.8rem', marginRight: '4px'
                                                }}
                                            >
                                                {s.is_active ? t('Active', '啟用中') : t('Paused', '已暫停')}
                                            </button>
                                            <button 
                                                onClick={() => navigate(`/reports/schedules/edit/${s.id}`)}
                                                style={{ 
                                                    width: '32px', height: '32px', borderRadius: '6px', display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                    color: 'var(--text-secondary)', backgroundColor: 'transparent', border: 'none', cursor: 'pointer',
                                                    transition: 'all 0.2s'
                                                }}
                                                onMouseEnter={(e) => e.target.style.backgroundColor = 'rgba(255,255,255,0.05)'}
                                                onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
                                                title={t('Edit', '編輯')}
                                            >
                                                <FiEdit size={18} />
                                            </button>
                                            <button 
                                                onClick={() => handleDeleteSchedule(s.id)}
                                                style={{ 
                                                    width: '32px', height: '32px', borderRadius: '6px', display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                    color: '#ef4444', backgroundColor: 'transparent', border: 'none', cursor: 'pointer',
                                                    transition: 'all 0.2s'
                                                }}
                                                onMouseEnter={(e) => e.target.style.backgroundColor = 'rgba(239, 68, 68, 0.1)'}
                                                onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
                                                title={t('Delete', '刪除')}
                                            >
                                                <FiTrash2 size={18} />
                                            </button>
                                        </div>
                                    </div>
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', fontSize: '0.9rem' }}>
                                        <div style={{ backgroundColor: 'rgba(255,255,255,0.03)', padding: '6px 12px', borderRadius: '6px', color: 'var(--text-secondary)' }}>
                                            <FiCalendar style={{ marginRight: '6px', verticalAlign: 'middle' }} />
                                            {s.frequency === 'daily' && t('Daily', '每日')}
                                            {s.frequency === 'weekly' && `${t('Weekly', '每週')} (${(() => {
                                                const days = {
                                                    '1': t('Mon', '週一'), '2': t('Tue', '週二'), '3': t('Wed', '週三'),
                                                    '4': t('Thu', '週四'), '5': t('Fri', '週五'), '6': t('Sat', '週六'), '0': t('Sun', '週日')
                                                };
                                                return days[s.day_of_week] || t('Mon', '週一');
                                            })()})`}
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

