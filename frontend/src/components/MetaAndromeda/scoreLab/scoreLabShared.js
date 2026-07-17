export const OBJECTIVES = [
    { value: 'purchase', label: { zh: '購買轉換 (purchase)', en: 'Purchase Conversion' } },
    { value: 'lead', label: { zh: '潛在客戶 (lead)', en: 'Lead Generation' } },
    { value: 'traffic', label: { zh: '流量 (traffic)', en: 'Traffic' } },
    { value: 'engagement', label: { zh: '互動 (engagement)', en: 'Engagement' } },
    { value: 'awareness', label: { zh: '品牌知名度 (awareness)', en: 'Brand Awareness' } },
    { value: 'reach', label: { zh: '觸及人數 (reach)', en: 'Reach' } },
    { value: 'video_views', label: { zh: '影片觀看 (video_views)', en: 'Video Views' } },
];

export const PLACEMENTS = [
    { value: 'all', label: { zh: '全版位 (all)', en: 'All Placements' } },
    { value: 'feed', label: { zh: 'Feed 貼文', en: 'Feed' } },
    { value: 'reels', label: { zh: 'Reels / 短影音', en: 'Reels' } },
    { value: 'stories', label: { zh: 'Stories', en: 'Stories' } },
    { value: 'search', label: { zh: '搜尋結果', en: 'Search' } },
    { value: 'instream', label: { zh: 'In-stream 影音廣告', en: 'In-stream' } },
];

export const MARKETS = [
    { value: 'TW', label: 'TW - 台灣' },
    { value: 'US', label: 'US - 美國' },
    { value: 'JP', label: 'JP - 日本' },
    { value: 'HK', label: 'HK - 香港' },
    { value: 'SG', label: 'SG - 新加坡' },
    { value: 'MY', label: 'MY - 馬來西亞' },
    { value: 'TH', label: 'TH - 泰國' },
    { value: 'ID', label: 'ID - 印尼' },
    { value: 'VN', label: 'VN - 越南' },
    { value: 'PH', label: 'PH - 菲律賓' },
];

export const REQUEST_MODES = [
    { value: 'auto', label: { zh: '自動 (auto)', en: 'Auto' } },
    { value: 'diagnostic_plus_roas', label: { zh: '診斷 + ROAS 預測', en: 'Diagnostic + ROAS' } },
    { value: 'diagnostic_only', label: { zh: '僅診斷 (不含 ROAS)', en: 'Diagnostic Only' } },
];

export const ROAS_COLOR = { high: '#10b981', mid: '#f59e0b', low: '#ef4444' };
export const TERMINAL = new Set(['completed', 'failed']);

export const inferAssetType = (file) => {
    if (!file) return null;
    if (file.type.startsWith('image/')) return 'image';
    if (file.type.startsWith('video/')) return 'video';
    const low = file.name.toLowerCase();
    if (['.png', '.jpg', '.jpeg', '.webp'].some(e => low.endsWith(e))) return 'image';
    if (['.mp4', '.mov'].some(e => low.endsWith(e))) return 'video';
    return null;
};

export const scoreColor = (score) => {
    if (score == null) return 'var(--text-secondary)';
    if (score >= 75) return '#10b981';
    if (score >= 50) return '#f59e0b';
    return '#ef4444';
};

export const statusLabel = (status, t) => {
    switch (String(status).toLowerCase()) {
        case 'completed': return t('Completed', '評分完成');
        case 'failed': return t('Failed', '評分失敗');
        case 'queued': return t('Queued', '已排隊');
        case 'processing': return t('Processing', '處理中');
        default: return status;
    }
};

export const scoreLabScrollCss = `
    .sl-scroll::-webkit-scrollbar { width: 5px; }
    .sl-scroll::-webkit-scrollbar-thumb { background: var(--glass-border); border-radius: 99px; }
    .sl-scroll::-webkit-scrollbar-thumb:hover { background: var(--accent-primary); }
    select option { background: #1a1a2e; color: #e2e8f0; }
`;

export const panelStyle = {
    background: 'var(--bg-secondary)',
    border: '1px solid var(--glass-border)',
    borderRadius: '16px',
    padding: '24px',
};

export const cardStyle = {
    padding: '12px 14px',
    borderRadius: '12px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.02)',
};

export const titleSt = { margin: '0 0 16px', color: 'var(--text-primary)', fontSize: '1rem' };
export const labelSt = { color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '4px', fontWeight: 600 };

const dropBase = {
    border: '2px dashed var(--glass-border)',
    borderRadius: '12px',
    padding: '20px 16px',
    textAlign: 'center',
    cursor: 'pointer',
    transition: 'all 0.18s',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    minHeight: '130px',
};

export const dropStyle = { ...dropBase, background: 'rgba(255,255,255,0.01)' };
export const dropActiveStyle = { ...dropBase, borderColor: 'var(--accent-primary)', background: 'rgba(59,130,246,0.07)' };

export const selStyle = {
    padding: '8px 10px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.05)',
    color: 'var(--text-primary)',
    fontSize: '0.85rem',
    appearance: 'auto',
};

export const inpStyle = {
    padding: '8px 11px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.05)',
    color: 'var(--text-primary)',
    fontSize: '0.85rem',
    resize: 'vertical',
};

export const btnPriStyle = {
    padding: '11px 16px',
    borderRadius: '10px',
    border: 'none',
    background: 'var(--accent-primary)',
    color: '#fff',
    fontWeight: 700,
    fontSize: '0.9rem',
    cursor: 'pointer',
    transition: 'opacity 0.15s',
};

export const btnSecStyle = {
    padding: '9px 14px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.03)',
    color: 'var(--text-primary)',
    cursor: 'pointer',
    fontSize: '0.85rem',
};

export const errorPanelStyle = {
    marginBottom: '16px',
    padding: '14px 16px',
    borderRadius: '12px',
    background: 'rgba(239,68,68,0.08)',
    border: '1px solid rgba(239,68,68,0.2)',
    color: 'var(--text-primary)',
};

export const histItemStyle = {
    textAlign: 'left',
    padding: '9px 12px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    cursor: 'pointer',
    transition: 'all 0.15s',
    width: '100%',
};
