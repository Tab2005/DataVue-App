import React, { useMemo, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { FaKey, FaUsers } from 'react-icons/fa';
import AdminStatsCards from '../components/Admin/AdminStatsCards';
import AdminTeamsSection from '../components/Admin/AdminTeamsSection';
import AdminUsersSection from '../components/Admin/AdminUsersSection';
import { createAdminStyles } from '../components/Admin/adminStyles';
import PermissionManager from '../components/PermissionManager';
import useAdminData from '../hooks/useAdminData';

const AdminDashboard = () => {
    const { language } = useOutletContext();
    const [activeTab, setActiveTab] = useState('overview');
    const adminData = useAdminData(language);
    const styles = useMemo(() => createAdminStyles(adminData.isMobile), [adminData.isMobile]);
    const { t } = adminData;

    if (adminData.loading) return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', color: 'var(--text-secondary)' }}>
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mb-4"></div>
            {t.loading}
        </div>
    );

    if (adminData.error) return (
        <div style={{ padding: '32px', textAlign: 'center' }}>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '8px', color: '#ef4444' }}>{t.access_error}</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>{adminData.error}</p>
            <button
                onClick={adminData.fetchData}
                style={{ padding: '8px 16px', backgroundColor: '#2563eb', color: 'white', borderRadius: '8px', border: 'none', cursor: 'pointer' }}
            >
                {t.retry}
            </button>
        </div>
    );

    return (
        <div style={styles.container}>
            <div style={styles.header}>
                <h1 style={{ fontSize: adminData.isMobile ? '1.5rem' : '1.875rem', fontWeight: 'bold', marginBottom: '8px', color: 'var(--text-primary)' }}>{t.title}</h1>
                <p style={{ fontSize: adminData.isMobile ? '1rem' : '1.125rem', color: 'var(--text-secondary)' }}>{t.subtitle}</p>
            </div>

            <AdminStatsCards stats={adminData.stats} styles={styles} t={t} />

            <div style={{ display: 'flex', gap: '12px', marginBottom: '24px', flexWrap: 'wrap' }}>
                <button
                    onClick={() => setActiveTab('overview')}
                    style={{
                        padding: '10px 20px',
                        borderRadius: '10px',
                        border: activeTab === 'overview' ? '1px solid #3b82f6' : '1px solid var(--glass-border)',
                        backgroundColor: activeTab === 'overview' ? 'rgba(59, 130, 246, 0.1)' : 'rgba(255,255,255,0.02)',
                        color: activeTab === 'overview' ? '#3b82f6' : 'var(--text-secondary)',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        fontWeight: activeTab === 'overview' ? '600' : '400',
                        transition: 'all 0.2s'
                    }}
                >
                    <FaUsers size={14} />
                    {language === 'en' ? 'Users & Teams' : '使用者與團隊'}
                </button>
                <button
                    onClick={() => setActiveTab('permissions')}
                    style={{
                        padding: '10px 20px',
                        borderRadius: '10px',
                        border: activeTab === 'permissions' ? '1px solid #f59e0b' : '1px solid var(--glass-border)',
                        backgroundColor: activeTab === 'permissions' ? 'rgba(245, 158, 11, 0.1)' : 'rgba(255,255,255,0.02)',
                        color: activeTab === 'permissions' ? '#f59e0b' : 'var(--text-secondary)',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        fontWeight: activeTab === 'permissions' ? '600' : '400',
                        transition: 'all 0.2s'
                    }}
                >
                    <FaKey size={14} />
                    {language === 'en' ? 'Permissions' : '權限管理'}
                </button>
            </div>

            <div style={styles.divider}></div>

            {activeTab === 'permissions' ? (
                <PermissionManager language={language} />
            ) : (
                <>
                    <AdminUsersSection
                        currentItems={adminData.userData.currentItems}
                        totalPages={adminData.userData.totalPages}
                        page={adminData.userPage}
                        setPage={adminData.setUserPage}
                        search={adminData.userSearch}
                        setSearch={adminData.setUserSearch}
                        loading={adminData.loading}
                        isMobile={adminData.isMobile}
                        onDeleteUser={adminData.handleDeleteUser}
                        styles={styles}
                        t={t}
                    />
                    <div style={styles.divider}></div>
                    <AdminTeamsSection
                        currentItems={adminData.teamData.currentItems}
                        totalPages={adminData.teamData.totalPages}
                        page={adminData.teamPage}
                        setPage={adminData.setTeamPage}
                        search={adminData.teamSearch}
                        setSearch={adminData.setTeamSearch}
                        loading={adminData.loading}
                        isMobile={adminData.isMobile}
                        styles={styles}
                        t={t}
                    />
                </>
            )}
        </div>
    );
};

export default AdminDashboard;
