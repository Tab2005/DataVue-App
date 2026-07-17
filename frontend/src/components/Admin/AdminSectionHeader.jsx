import React from 'react';
import { FaSearch } from 'react-icons/fa';

const AdminSectionHeader = ({ icon, color, title, description, search, setSearch, styles, t }) => (
    <div style={styles.sectionHeader}>
        <div style={styles.headerLeft}>
            <div style={styles.iconBox(color)}>
                {icon}
            </div>
            <div>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 'bold', color: 'var(--text-primary)' }}>{title}</h2>
                <p style={{ fontSize: '0.875rem', marginTop: '4px', color: 'var(--text-secondary)' }}>
                    {description}
                </p>
            </div>
        </div>
        <div style={styles.searchContainer}>
            <FaSearch style={styles.searchIcon} />
            <input
                type="text"
                placeholder={t.search_placeholder}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                style={styles.searchInput}
            />
        </div>
    </div>
);

export default AdminSectionHeader;
