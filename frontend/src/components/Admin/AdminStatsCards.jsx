import React from 'react';
import { FaBuilding, FaUsers } from 'react-icons/fa';

const AdminStatsCards = ({ stats, styles, t }) => (
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
);

export default AdminStatsCards;
