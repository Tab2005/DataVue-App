const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const PAGE_SIZE = 25;

export const statusToneMap = {
    completed: 'rgba(16, 185, 129, 0.15)',
    queued: 'rgba(59, 130, 246, 0.15)',
    failed: 'rgba(239, 68, 68, 0.15)',
    processing: 'rgba(245, 158, 11, 0.15)',
};

export const roasBandColor = {
    high: '#10b981',
    mid: '#f59e0b',
    low: '#ef4444',
};

export const sourceMeta = {
    analytics: {
        bg: 'rgba(59,130,246,0.15)',
        color: '#60a5fa',
    },
    score_lab: {
        bg: 'rgba(139,92,246,0.15)',
        color: '#a78bfa',
    },
};

export const resolvePreviewUrl = (item) => {
    if (!item) return null;
    const url = item.preview_url;
    if (url && (url.startsWith('http') || url.startsWith('/'))) return url;
    if (item.asset_uri) {
        const base = API_URL.endsWith('/') ? API_URL.slice(0, -1) : API_URL;
        return `${base}/api/meta-andromeda/assets/preview?uri=${encodeURIComponent(item.asset_uri)}`;
    }
    return null;
};

export const getStatusLabel = (key, t) => {
    switch (String(key).toLowerCase()) {
        case 'completed': return t('Completed', '已完成');
        case 'failed': return t('Failed', '失敗');
        case 'pending': return t('Pending', '待處理');
        case 'processing': return t('Processing', '處理中');
        case 'queued': return t('Queued', '排隊中');
        default: return key;
    }
};

export const queueScrollCss = `
    .queue-scroll-box::-webkit-scrollbar { width: 6px; }
    .queue-scroll-box::-webkit-scrollbar-track { background: rgba(255,255,255,0.01); border-radius: 999px; }
    .queue-scroll-box::-webkit-scrollbar-thumb { background: var(--glass-border); border-radius: 999px; }
    .queue-scroll-box::-webkit-scrollbar-thumb:hover { background: var(--accent-primary); }
    .queue-item-wrap .queue-delete-btn { opacity: 0; transition: opacity 0.15s; }
    .queue-item-wrap:hover .queue-delete-btn { opacity: 1; }
`;

export const panelStyle = {
    background: 'var(--bg-secondary)',
    border: '1px solid var(--glass-border)',
    borderRadius: '16px',
    padding: '24px',
};

export const queueItemStyle = {
    textAlign: 'left',
    padding: '10px 12px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    cursor: 'pointer',
    transition: 'all 0.15s ease-in-out',
    width: '100%',
};

export const detailCardStyle = {
    padding: '14px',
    borderRadius: '12px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.02)',
};

export const innerCardStyle = {
    padding: '8px 10px',
    borderRadius: '8px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.02)',
};

export const sectionTitleStyle = {
    margin: '0 0 14px 0',
    color: 'var(--text-primary)',
    fontSize: '1rem',
};

export const labelStyle = {
    color: 'var(--text-secondary)',
    fontSize: '0.8rem',
    marginBottom: '5px',
};

export const selectStyle = {
    padding: '8px 12px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.05)',
    color: 'var(--text-primary)',
    fontSize: '0.85rem',
};

export const searchInputStyle = {
    width: '100%',
    padding: '9px 12px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.05)',
    color: 'var(--text-primary)',
    marginBottom: '12px',
    fontSize: '0.85rem',
    boxSizing: 'border-box',
};

export const errorPanelStyle = {
    marginBottom: '16px',
    padding: '16px',
    borderRadius: '12px',
    background: 'rgba(239,68,68,0.08)',
    border: '1px solid rgba(239,68,68,0.18)',
    color: 'var(--text-primary)',
};

export const listStyle = {
    margin: 0,
    paddingLeft: '18px',
    color: 'var(--text-secondary)',
    lineHeight: 1.7,
};

export const pagebtnStyle = {
    padding: '5px 10px',
    borderRadius: '8px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.04)',
    color: 'var(--text-primary)',
    cursor: 'pointer',
    fontSize: '0.85rem',
    minWidth: '32px',
    transition: 'all 0.15s',
};
