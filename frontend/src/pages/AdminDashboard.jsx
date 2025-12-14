import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { FaUsers, FaBuilding, FaTrash, FaShieldAlt, FaSearch, FaChevronLeft, FaChevronRight } from 'react-icons/fa';
import { AdminService } from '../services/adminService';

const AdminDashboard = () => {
    // 1. Get language from context
    const { language } = useOutletContext();

    // Data State
    const [stats, setStats] = useState({ user_count: 0, team_count: 0 });
    const [users, setUsers] = useState([]);
    const [teams, setTeams] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // Pagination & Search State
    const [userSearch, setUserSearch] = useState('');
    const [userPage, setUserPage] = useState(1);
    const [teamSearch, setTeamSearch] = useState('');
    const [teamPage, setTeamPage] = useState(1);
    const itemsPerPage = 10;

    // 2. Define Translations
    const translations = {
        en: {
            title: "Super Admin Dashboard",
            subtitle: "Platform-wide management and statistics",
            loading: "Loading Admin Dashboard...",
            retry: "Retry",
            access_error: "Access Error",

            // Stats
            total_users: "Total Users",
            total_teams: "Total Teams",

            // Shared
            search_placeholder: "Search by name or ID...",
            prev: "Previous",
            next: "Next",
            page: "Page",

            // Section: Users
            section_users: "All Users",
            desc_users: "Manage all registered users on the platform",
            th_name: "Name",
            th_email: "Email",
            th_role: "Role",
            th_joined: "Joined",
            th_actions: "Actions",
            no_users: "No users found matching your search.",

            // Section: Teams
            section_teams: "All Teams",
            desc_teams: "Overview of all active teams and their owners",
            th_team_name: "Team Name",
            th_owner_id: "Owner ID",
            th_created_at: "Created At",
            th_members: "Members",
            no_teams: "No teams found matching your search.",

            // Actions
            confirm_delete: "Are you sure? This action is irreversible.",
            role_super: "SUPER ADMIN",
            role_user: "USER",
            delete_title: "Force Delete User"
        },
        zh: {
            title: "超級管理員後台",
            subtitle: "平台全域管理與數據統計",
            loading: "載入管理後台...",
            retry: "重試",
            access_error: "存取錯誤",

            // Stats
            total_users: "總使用者數",
            total_teams: "總團隊數",

            // Shared
            search_placeholder: "搜尋名稱或 ID...",
            prev: "上一頁",
            next: "下一頁",
            page: "頁次",

            // Section: Users
            section_users: "所有使用者",
            desc_users: "管理平台所有註冊用戶",
            th_name: "姓名",
            th_email: "Email",
            th_role: "角色",
            th_joined: "加入時間",
            th_actions: "操作",
            no_users: "找不到符合搜尋條件的使用者。",

            // Section: Teams
            section_teams: "所有團隊",
            desc_teams: "瀏覽所有活躍團隊與擁有者",
            th_team_name: "團隊名稱",
            th_owner_id: "擁有者 ID",
            th_created_at: "建立時間",
            th_members: "成員數",
            no_teams: "找不到符合搜尋條件的團隊。",

            // Actions
            confirm_delete: "您確定嗎？此操作無法復原。",
            role_super: "超級管理員",
            role_user: "一般用戶",
            delete_title: "強制刪除用戶"
        }
    };

    const t = translations[language] || translations.zh;

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [statsData, usersData, teamsData] = await Promise.all([
                AdminService.getStats(),
                AdminService.getAllUsers(),
                AdminService.getAllTeams()
            ]);
            setStats(statsData || { user_count: 0, team_count: 0 });
            setUsers(Array.isArray(usersData) ? usersData : []);
            setTeams(Array.isArray(teamsData) ? teamsData : []);
        } catch (err) {
            console.error("Dashboard Load Error:", err);
            setError(err instanceof Error ? err.message : String(err));
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteUser = async (userId) => {
        if (!window.confirm(t.confirm_delete)) return;
        try {
            await AdminService.deleteUser(userId);
            setUsers(users.filter(u => u.id !== userId));
            setStats(prev => ({ ...prev, user_count: prev.user_count - 1 }));
        } catch (err) {
            alert(err instanceof Error ? err.message : String(err));
        }
    };

    // --- Filter & Pagination Logic ---

    // Users
    const filteredUsers = users.filter(u =>
        (u.name && u.name.toLowerCase().includes(userSearch.toLowerCase())) ||
        (u.email && u.email.toLowerCase().includes(userSearch.toLowerCase()))
    );
    const totalUserPages = Math.ceil(filteredUsers.length / itemsPerPage);
    const currentUserItems = filteredUsers.slice((userPage - 1) * itemsPerPage, userPage * itemsPerPage);

    // Teams
    const filteredTeams = teams.filter(tm =>
        (tm.name && tm.name.toLowerCase().includes(teamSearch.toLowerCase())) ||
        (tm.owner_id && tm.owner_id.toLowerCase().includes(teamSearch.toLowerCase()))
    );
    const totalTeamPages = Math.ceil(filteredTeams.length / itemsPerPage);
    const currentTeamItems = filteredTeams.slice((teamPage - 1) * itemsPerPage, teamPage * itemsPerPage);

    useEffect(() => { setUserPage(1); }, [userSearch]); // Reset page on search
    useEffect(() => { setTeamPage(1); }, [teamSearch]); // Reset page on search


    // --- Responsive Check ---
    const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

    useEffect(() => {
        const handleResize = () => setIsMobile(window.innerWidth < 768);
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    // --- STYLES ---
    const styles = {
        container: {
            maxWidth: '1280px',
            margin: '0 auto',
            padding: isMobile ? '24px 16px' : '48px 32px',
            display: 'flex',
            flexDirection: 'column',
            gap: isMobile ? '24px' : '32px'
        },
        header: { marginBottom: '8px' },
        sectionHeader: {
            display: 'flex',
            flexDirection: isMobile ? 'column' : 'row',
            alignItems: isMobile ? 'flex-start' : 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '16px',
            marginBottom: '24px'
        },
        headerLeft: {
            display: 'flex',
            alignItems: 'center',
            gap: '16px',
            width: isMobile ? '100%' : 'auto'
        },
        iconBox: (color) => ({
            padding: '12px',
            borderRadius: '12px',
            backgroundColor: color === 'blue' ? 'rgba(59, 130, 246, 0.1)' : color === 'purple' ? 'rgba(168, 85, 247, 0.1)' : 'rgba(234, 179, 8, 0.1)',
            color: color === 'blue' ? '#3b82f6' : color === 'purple' ? '#a855f7' : '#eab308',
            border: `1px solid ${color === 'blue' ? 'rgba(59, 130, 246, 0.2)' : color === 'purple' ? 'rgba(168, 85, 247, 0.2)' : 'rgba(234, 179, 8, 0.2)'}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            minWidth: '44px' // Prevent shrinking
        }),
        statsGrid: {
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '24px',
            marginBottom: isMobile ? '32px' : '48px'
        },
        statCard: {
            padding: '24px',
            borderRadius: '16px',
            backgroundColor: 'rgba(255,255,255,0.03)',
            border: '1px solid var(--glass-border)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
        },
        // Table Styles (Desktop)
        tableContainer: {
            borderRadius: '16px',
            overflow: 'hidden',
            border: '1px solid var(--glass-border)',
            padding: 0,
            background: 'var(--glass-bg)',
            marginBottom: '16px'
        },
        table: {
            width: '100%',
            textAlign: 'left',
            borderCollapse: 'collapse'
        },
        th: {
            padding: '16px',
            fontSize: '0.875rem',
            fontWeight: '600',
            color: 'var(--text-secondary)',
            background: '#242526',
            borderBottom: '1px solid var(--glass-border)',
            whiteSpace: 'nowrap'
        },
        td: {
            padding: '16px',
            borderBottom: '1px solid rgba(255,255,255,0.05)',
            color: 'var(--text-primary)'
        },
        // Mobile Card Styles
        mobileCard: {
            padding: '16px',
            borderRadius: '12px',
            backgroundColor: 'rgba(255,255,255,0.02)',
            border: '1px solid var(--glass-border)',
            marginBottom: '12px',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px'
        },
        mobileCardRow: {
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '0.875rem'
        },
        mobileCardLabel: {
            color: 'var(--text-secondary)',
            fontSize: '0.75rem'
        },
        divider: {
            position: 'relative',
            height: '1px',
            width: '100%',
            backgroundColor: 'var(--glass-border)'
        },
        badge: (role) => {
            const isSuper = role === 'SUPER ADMIN';
            return {
                padding: '4px 8px',
                borderRadius: '9999px',
                fontSize: '0.75rem',
                fontWeight: '600',
                backgroundColor: isSuper ? 'rgba(234, 179, 8, 0.1)' : 'rgba(107, 114, 128, 0.1)',
                color: isSuper ? '#eab308' : '#9ca3af',
                display: 'inline-block'
            };
        },
        // Search Input Style
        searchContainer: {
            position: 'relative',
            width: isMobile ? '100%' : 'auto',
            minWidth: isMobile ? '100%' : '250px'
        },
        searchInput: {
            width: '100%',
            padding: '10px 16px 10px 40px',
            borderRadius: '12px',
            backgroundColor: 'rgba(255,255,255,0.05)',
            border: '1px solid var(--glass-border)',
            color: 'var(--text-primary)',
            outline: 'none',
            fontSize: '0.875rem'
        },
        searchIcon: {
            position: 'absolute',
            left: '12px',
            top: '50%',
            transform: 'translateY(-50%)',
            color: 'var(--text-secondary)'
        },
        // Pagination
        pagination: {
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            gap: '16px',
            color: 'var(--text-secondary)',
            fontSize: '0.875rem'
        },
        pageBtn: {
            padding: '8px 16px',
            borderRadius: '8px',
            backgroundColor: 'rgba(255,255,255,0.05)',
            border: '1px solid var(--glass-border)',
            color: 'var(--text-primary)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
        }
    };

    if (loading) return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', color: 'var(--text-secondary)' }}>
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mb-4"></div>
            {t.loading}
        </div>
    );

    if (error) return (
        <div style={{ padding: '32px', textAlign: 'center' }}>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '8px', color: '#ef4444' }}>{t.access_error}</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>{error}</p>
            <button
                onClick={fetchData}
                style={{ padding: '8px 16px', backgroundColor: '#2563eb', color: 'white', borderRadius: '8px', border: 'none', cursor: 'pointer' }}
            >
                {t.retry}
            </button>
        </div>
    );

    return (
        <div style={styles.container}>
            {/* Page Header */}
            <div style={styles.header}>
                <h1 style={{ fontSize: isMobile ? '1.5rem' : '1.875rem', fontWeight: 'bold', marginBottom: '8px', color: 'var(--text-primary)' }}>{t.title}</h1>
                <p style={{ fontSize: isMobile ? '1rem' : '1.125rem', color: 'var(--text-secondary)' }}>{t.subtitle}</p>
            </div>

            {/* Stats Cards */}
            <div style={styles.statsGrid}>
                <div style={styles.statCard}>
                    <div>
                        <p style={{ fontSize: '0.875rem', fontWeight: '500', color: 'var(--text-secondary)', marginBottom: '4px' }}>{t.total_users}</p>
                        <p style={{ fontSize: '2.25rem', fontWeight: 'bold', color: 'var(--text-primary)' }}>{stats.user_count}</p>
                    </div>
                    <div style={styles.iconBox('blue')}>
                        <FaUsers size={24} />
                    </div>
                </div>

                <div style={styles.statCard}>
                    <div>
                        <p style={{ fontSize: '0.875rem', fontWeight: '500', color: 'var(--text-secondary)', marginBottom: '4px' }}>{t.total_teams}</p>
                        <p style={{ fontSize: '2.25rem', fontWeight: 'bold', color: 'var(--text-primary)' }}>{stats.team_count}</p>
                    </div>
                    <div style={styles.iconBox('purple')}>
                        <FaBuilding size={24} />
                    </div>
                </div>
            </div>

            {/* Divider */}
            <div style={styles.divider}></div>

            {/* SECTION 1: USERS */}
            <section className="animate-fade-in">
                {/* Section Header with Search */}
                <div style={styles.sectionHeader}>
                    <div style={styles.headerLeft}>
                        <div style={styles.iconBox('blue')}>
                            <FaUsers size={20} />
                        </div>
                        <div>
                            <h2 style={{ fontSize: isMobile ? '1.1rem' : '1.25rem', fontWeight: 'bold', color: 'var(--text-primary)' }}>{t.section_users}</h2>
                            <p style={{ fontSize: isMobile ? '0.8rem' : '0.875rem', marginTop: '4px', color: 'var(--text-secondary)' }}>
                                {t.desc_users}
                            </p>
                        </div>
                    </div>
                    {/* Search Bar */}
                    <div style={styles.searchContainer}>
                        <FaSearch style={styles.searchIcon} />
                        <input
                            type="text"
                            placeholder={t.search_placeholder}
                            value={userSearch}
                            onChange={(e) => setUserSearch(e.target.value)}
                            style={styles.searchInput}
                        />
                    </div>
                </div>

                {/* Users List (Mobile Card / Desktop Table) */}
                {isMobile ? (
                    <div>
                        {currentUserItems.length > 0 ? currentUserItems.map(user => (
                            <div key={user.id} style={styles.mobileCard}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                    <div style={{
                                        width: '40px', height: '40px', borderRadius: '50%',
                                        backgroundColor: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6',
                                        display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold'
                                    }}>
                                        {user.name ? user.name.charAt(0).toUpperCase() : '?'}
                                    </div>
                                    <div>
                                        <div style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{user.name}</div>
                                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{user.email}</div>
                                    </div>
                                    {user.is_super_admin && <FaShieldAlt style={{ color: '#eab308', marginLeft: 'auto' }} />}
                                </div>

                                <div style={styles.divider}></div>

                                <div style={styles.mobileCardRow}>
                                    <span style={styles.mobileCardLabel}>{t.th_role}</span>
                                    <span style={styles.badge(user.is_super_admin ? 'SUPER ADMIN' : 'USER')}>
                                        {user.is_super_admin ? t.role_super : t.role_user}
                                    </span>
                                </div>
                                <div style={styles.mobileCardRow}>
                                    <span style={styles.mobileCardLabel}>{t.th_joined}</span>
                                    <span style={{ color: 'var(--text-primary)' }}>
                                        {user.created_at ? new Date(user.created_at).toLocaleDateString() : '-'}
                                    </span>
                                </div>
                                {!user.is_super_admin && (
                                    <button
                                        onClick={() => handleDeleteUser(user.id)}
                                        style={{
                                            width: '100%',
                                            marginTop: '8px',
                                            padding: '8px',
                                            borderRadius: '8px',
                                            backgroundColor: 'rgba(239, 68, 68, 0.1)',
                                            color: '#ef4444',
                                            border: 'none',
                                            cursor: 'pointer',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            gap: '8px'
                                        }}
                                    >
                                        <FaTrash size={14} /> {t.delete_title}
                                    </button>
                                )}
                            </div>
                        )) : (
                            <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-secondary)' }}>{t.no_users}</div>
                        )}
                    </div>
                ) : (
                    <div className="glass-panel" style={styles.tableContainer}>
                        <div style={{ overflowX: 'auto' }}>
                            <table style={styles.table}>
                                <thead>
                                    <tr>
                                        <th style={styles.th}>{t.th_name}</th>
                                        <th style={styles.th}>{t.th_email}</th>
                                        <th style={styles.th}>{t.th_role}</th>
                                        <th style={styles.th}>{t.th_joined}</th>
                                        <th style={{ ...styles.th, textAlign: 'right' }}>{t.th_actions}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {currentUserItems.length > 0 ? currentUserItems.map((user, idx) => (
                                        <tr key={user.id} style={{
                                            ...styles.td,
                                            backgroundColor: idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)'
                                        }}>
                                            <td style={styles.td}>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                    {user.is_super_admin && <FaShieldAlt style={{ color: '#eab308' }} title={t.role_super} />}
                                                    <span style={{ fontWeight: '500' }}>{user.name}</span>
                                                </div>
                                            </td>
                                            <td style={{ ...styles.td, color: 'var(--text-secondary)' }}>{user.email}</td>
                                            <td style={styles.td}>
                                                <span style={styles.badge(user.is_super_admin ? 'SUPER ADMIN' : 'USER')}>
                                                    {user.is_super_admin ? t.role_super : t.role_user}
                                                </span>
                                            </td>
                                            <td style={{ ...styles.td, fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                                                {user.created_at ? new Date(user.created_at).toLocaleDateString() : '-'}
                                            </td>
                                            <td style={{ ...styles.td, textAlign: 'right' }}>
                                                {!user.is_super_admin && (
                                                    <button
                                                        onClick={() => handleDeleteUser(user.id)}
                                                        style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', padding: '8px' }}
                                                        onMouseOver={(e) => { e.currentTarget.style.color = '#ef4444' }}
                                                        onMouseOut={(e) => { e.currentTarget.style.color = 'var(--text-secondary)' }}
                                                        title={t.delete_title}
                                                    >
                                                        <FaTrash />
                                                    </button>
                                                )}
                                            </td>
                                        </tr>
                                    )) : (
                                        <tr>
                                            <td colSpan="5" style={{ padding: '32px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                                                {loading ? t.loading : t.no_users}
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* Pagination Controls */}
                {totalUserPages > 1 && (
                    <div style={styles.pagination}>
                        <button
                            onClick={() => setUserPage(p => Math.max(1, p - 1))}
                            disabled={userPage === 1}
                            style={{ ...styles.pageBtn, opacity: userPage === 1 ? 0.5 : 1 }}
                        >
                            <FaChevronLeft /> {t.prev}
                        </button>
                        <span>{t.page} {userPage} / {totalUserPages}</span>
                        <button
                            onClick={() => setUserPage(p => Math.min(totalUserPages, p + 1))}
                            disabled={userPage === totalUserPages}
                            style={{ ...styles.pageBtn, opacity: userPage === totalUserPages ? 0.5 : 1 }}
                        >
                            {t.next} <FaChevronRight />
                        </button>
                    </div>
                )}
            </section>

            {/* Divider */}
            <div style={styles.divider}></div>

            {/* SECTION 2: TEAMS */}
            <section className="animate-fade-in">
                {/* Section Header with Search */}
                <div style={styles.sectionHeader}>
                    <div style={styles.headerLeft}>
                        <div style={styles.iconBox('purple')}>
                            <FaBuilding size={20} />
                        </div>
                        <div>
                            <h2 style={{ fontSize: isMobile ? '1.1rem' : '1.25rem', fontWeight: 'bold', color: 'var(--text-primary)' }}>{t.section_teams}</h2>
                            <p style={{ fontSize: isMobile ? '0.8rem' : '0.875rem', marginTop: '4px', color: 'var(--text-secondary)' }}>
                                {t.desc_teams}
                            </p>
                        </div>
                    </div>
                    {/* Search Bar */}
                    <div style={styles.searchContainer}>
                        <FaSearch style={styles.searchIcon} />
                        <input
                            type="text"
                            placeholder={t.search_placeholder}
                            value={teamSearch}
                            onChange={(e) => setTeamSearch(e.target.value)}
                            style={styles.searchInput}
                        />
                    </div>
                </div>

                {/* Teams List (Mobile Card / Desktop Table) */}
                {isMobile ? (
                    <div>
                        {currentTeamItems.length > 0 ? currentTeamItems.map(team => (
                            <div key={team.id} style={styles.mobileCard}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                    <div style={{
                                        width: '40px', height: '40px', borderRadius: '8px',
                                        backgroundColor: 'rgba(168, 85, 247, 0.1)', color: '#a855f7',
                                        display: 'flex', alignItems: 'center', justifyContent: 'center'
                                    }}>
                                        <FaBuilding size={18} />
                                    </div>
                                    <div>
                                        <div style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{team.name}</div>
                                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontFamily: 'monospace' }}>
                                            ID: {team.id.substring(0, 8)}...
                                        </div>
                                    </div>
                                </div>

                                <div style={styles.divider}></div>

                                <div style={styles.mobileCardRow}>
                                    <span style={styles.mobileCardLabel}>{t.th_owner_id}</span>
                                    <span style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>
                                        {team.owner_id}
                                    </span>
                                </div>
                                <div style={styles.mobileCardRow}>
                                    <span style={styles.mobileCardLabel}>{t.th_created_at}</span>
                                    <span style={{ color: 'var(--text-primary)' }}>
                                        {team.created_at ? new Date(team.created_at).toLocaleDateString() : '-'}
                                    </span>
                                </div>
                            </div>
                        )) : (
                            <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-secondary)' }}>{t.no_teams}</div>
                        )}
                    </div>
                ) : (
                    <div className="glass-panel" style={styles.tableContainer}>
                        <div style={{ overflowX: 'auto' }}>
                            <table style={styles.table}>
                                <thead>
                                    <tr>
                                        <th style={styles.th}>{t.th_team_name}</th>
                                        <th style={styles.th}>{t.th_owner_id}</th>
                                        <th style={styles.th}>{t.th_created_at}</th>
                                        <th style={{ ...styles.th, textAlign: 'right' }}>{t.th_members}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {currentTeamItems.length > 0 ? currentTeamItems.map((team, idx) => (
                                        <tr key={team.id} style={{
                                            ...styles.td,
                                            backgroundColor: idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)'
                                        }}>
                                            <td style={{ ...styles.td, fontWeight: 'bold' }}>{team.name}</td>
                                            <td style={{ ...styles.td, fontFamily: 'monospace', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{team.owner_id}</td>
                                            <td style={{ ...styles.td, fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                                                {team.created_at ? new Date(team.created_at).toLocaleString() : '-'}
                                            </td>
                                            <td style={{ ...styles.td, textAlign: 'right', color: 'var(--text-secondary)' }}>
                                                -
                                            </td>
                                        </tr>
                                    )) : (
                                        <tr>
                                            <td colSpan="4" style={{ padding: '32px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                                                {loading ? t.loading : t.no_teams}
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* Pagination Controls */}
                {totalTeamPages > 1 && (
                    <div style={styles.pagination}>
                        <button
                            onClick={() => setTeamPage(p => Math.max(1, p - 1))}
                            disabled={teamPage === 1}
                            style={{ ...styles.pageBtn, opacity: teamPage === 1 ? 0.5 : 1 }}
                        >
                            <FaChevronLeft /> {t.prev}
                        </button>
                        <span>{t.page} {teamPage} / {totalTeamPages}</span>
                        <button
                            onClick={() => setTeamPage(p => Math.min(totalTeamPages, p + 1))}
                            disabled={teamPage === totalTeamPages}
                            style={{ ...styles.pageBtn, opacity: teamPage === totalTeamPages ? 0.5 : 1 }}
                        >
                            {t.next} <FaChevronRight />
                        </button>
                    </div>
                )}
            </section>
        </div>
    );
};

export default AdminDashboard;
