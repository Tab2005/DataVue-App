export const createAdminStyles = (isMobile) => ({
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
        minWidth: '44px'
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
});
