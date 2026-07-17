import React from 'react';
import { FaBuilding } from 'react-icons/fa';
import AdminPagination from './AdminPagination';
import AdminSectionHeader from './AdminSectionHeader';

const AdminTeamsMobile = ({ teams, styles, t }) => {
    if (teams.length === 0) {
        return <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-secondary)' }}>{t.no_teams}</div>;
    }

    return (
        <div>
            {teams.map(team => (
                <div key={team.id} style={styles.mobileCard}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <div style={{
                            width: '40px',
                            height: '40px',
                            borderRadius: '8px',
                            backgroundColor: 'rgba(168, 85, 247, 0.1)',
                            color: '#a855f7',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
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
            ))}
        </div>
    );
};

const AdminTeamsTable = ({ teams, loading, styles, t }) => (
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
                    {teams.length > 0 ? teams.map((team, idx) => (
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
);

const AdminTeamsSection = ({
    currentItems,
    totalPages,
    page,
    setPage,
    search,
    setSearch,
    loading,
    isMobile,
    styles,
    t
}) => (
    <section className="animate-fade-in">
        <AdminSectionHeader
            icon={<FaBuilding size={20} />}
            color="purple"
            title={t.section_teams}
            description={t.desc_teams}
            search={search}
            setSearch={setSearch}
            styles={styles}
            t={t}
        />

        {isMobile ? (
            <AdminTeamsMobile teams={currentItems} styles={styles} t={t} />
        ) : (
            <AdminTeamsTable teams={currentItems} loading={loading} styles={styles} t={t} />
        )}

        <AdminPagination page={page} totalPages={totalPages} setPage={setPage} styles={styles} t={t} />
    </section>
);

export default AdminTeamsSection;
