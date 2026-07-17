import React from 'react';
import { FaShieldAlt, FaTrash, FaUsers } from 'react-icons/fa';
import AdminPagination from './AdminPagination';
import AdminSectionHeader from './AdminSectionHeader';

const AdminUsersMobile = ({ users, onDeleteUser, styles, t }) => {
    if (users.length === 0) {
        return <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-secondary)' }}>{t.no_users}</div>;
    }

    return (
        <div>
            {users.map(user => (
                <div key={user.id} style={styles.mobileCard}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <div style={{
                            width: '40px',
                            height: '40px',
                            borderRadius: '50%',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            color: '#3b82f6',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontWeight: 'bold'
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
                            onClick={() => onDeleteUser(user.id)}
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
            ))}
        </div>
    );
};

const AdminUsersTable = ({ users, loading, onDeleteUser, styles, t }) => (
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
                    {users.length > 0 ? users.map((user, idx) => (
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
                                        onClick={() => onDeleteUser(user.id)}
                                        style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', padding: '8px' }}
                                        onMouseOver={(e) => { e.currentTarget.style.color = '#ef4444'; }}
                                        onMouseOut={(e) => { e.currentTarget.style.color = 'var(--text-secondary)'; }}
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
);

const AdminUsersSection = ({
    currentItems,
    totalPages,
    page,
    setPage,
    search,
    setSearch,
    loading,
    isMobile,
    onDeleteUser,
    styles,
    t
}) => (
    <section className="animate-fade-in">
        <AdminSectionHeader
            icon={<FaUsers size={20} />}
            color="blue"
            title={t.section_users}
            description={t.desc_users}
            search={search}
            setSearch={setSearch}
            styles={styles}
            t={t}
        />

        {isMobile ? (
            <AdminUsersMobile users={currentItems} onDeleteUser={onDeleteUser} styles={styles} t={t} />
        ) : (
            <AdminUsersTable users={currentItems} loading={loading} onDeleteUser={onDeleteUser} styles={styles} t={t} />
        )}

        <AdminPagination page={page} totalPages={totalPages} setPage={setPage} styles={styles} t={t} />
    </section>
);

export default AdminUsersSection;
