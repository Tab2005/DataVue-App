import { getTabStyle, getToggleButtonStyle } from './GSCShared';

export const useGscStyles = (isMobile) => ({
    containerStyle: {
        display: 'flex',
        flexDirection: 'column',
        gap: isMobile ? '16px' : '24px',
        width: '100%',
        maxWidth: '100%',
        overflow: 'hidden',
        boxSizing: 'border-box'
    },
    selectStyle: {
        padding: isMobile ? '10px 12px' : '8px 12px',
        borderRadius: '8px',
        border: '1px solid var(--glass-border)',
        background: 'rgba(255, 255, 255, 0.05)',
        color: 'var(--text-primary)',
        outline: 'none',
        fontSize: isMobile ? '0.9rem' : '1rem',
        width: isMobile ? '100%' : 'auto'
    },
    cardStyle: {
        background: 'var(--bg-secondary)',
        padding: isMobile ? '12px' : '20px',
        borderRadius: isMobile ? '8px' : '12px',
        border: '1px solid var(--glass-border)',
        boxShadow: 'var(--shadow-sm)',
        minWidth: 0
    },
    cardLabelStyle: {
        fontSize: isMobile ? '12px' : '14px',
        color: 'var(--text-secondary)',
        marginBottom: '8px'
    },
    cardValueStyle: {
        fontSize: isMobile ? '16px' : '24px',
        fontWeight: 'bold',
        color: 'var(--text-primary)',
        wordBreak: 'break-word'
    },
    tableContainerStyle: {
        background: 'var(--bg-secondary)',
        borderRadius: '12px',
        border: '1px solid var(--glass-border)',
        overflow: 'hidden'
    },
    tableHeaderStyle: {
        padding: isMobile ? '12px 16px' : '16px',
        borderBottom: '1px solid var(--glass-border)',
        fontWeight: 'bold',
        color: 'var(--text-primary)',
        fontSize: isMobile ? '0.95rem' : '1rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '8px'
    },
    tableScrollStyle: {
        overflowX: 'auto',
        WebkitOverflowScrolling: 'touch',
        maxWidth: '100%'
    },
    tableStyle: {
        width: '100%',
        borderCollapse: 'collapse',
        textAlign: 'left',
        minWidth: '600px'
    },
    thStyle: {
        padding: isMobile ? '10px 12px' : '12px 24px',
        fontSize: isMobile ? '11px' : '12px',
        color: 'var(--text-secondary)',
        textTransform: 'uppercase',
        borderBottom: '1px solid var(--glass-border)',
        whiteSpace: 'nowrap',
        cursor: 'pointer',
        userSelect: 'none'
    },
    tdStyle: {
        padding: isMobile ? '12px' : '16px 24px',
        fontSize: isMobile ? '13px' : '14px',
        color: 'var(--text-primary)',
        borderBottom: '1px solid var(--glass-border)'
    },
    tabContainerStyle: {
        display: 'flex',
        gap: '4px',
        background: 'var(--bg-secondary)',
        padding: '4px',
        borderRadius: '12px',
        border: '1px solid var(--glass-border)',
        overflowX: 'auto',
        WebkitOverflowScrolling: 'touch'
    },
    tabStyle: getTabStyle(isMobile),
    searchInputStyle: {
        padding: '8px 12px',
        borderRadius: '8px',
        border: '1px solid var(--glass-border)',
        background: 'rgba(255, 255, 255, 0.05)',
        color: 'var(--text-primary)',
        outline: 'none',
        fontSize: '14px',
        width: isMobile ? '100%' : '200px'
    },
    toggleButtonStyle: getToggleButtonStyle,
    groupRowStyle: {
        background: 'var(--bg-hover)',
        cursor: 'pointer',
        fontWeight: '600'
    },
    childRowStyle: {
        background: 'var(--bg-primary)',
        paddingLeft: '40px'
    }
});
