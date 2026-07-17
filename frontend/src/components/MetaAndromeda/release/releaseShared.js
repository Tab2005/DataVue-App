const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// 縮圖來源:優先走本地 asset preview(檔案已集中在 worker,穩定),沒有 asset 才退回
// Facebook CDN media_url(可能過期)
export const resolvePairPreviewUrl = (item) => {
    if (item?.asset_uri) {
        const base = API_URL.endsWith('/') ? API_URL.slice(0, -1) : API_URL;
        return `${base}/api/meta-andromeda/assets/preview?uri=${encodeURIComponent(item.asset_uri)}`;
    }
    return item?.media_url || null;
};

export const createReleaseTranslator = (t) => (key) => {
    if (!key) return '--';
    const keyLower = String(key).toLowerCase();
    switch (keyLower) {
        case 'model_version':
            return t('Model Version', '模型版本');
        case 'status':
            return t('Status', '狀態');
        case 'approved_by':
            return t('Approved By', '核准人員');
        case 'pairwise_ranking_accuracy':
            return t('Pairwise Ranking Accuracy', '成對排序準確率');
        case 'mean_band_error':
            return t('Mean Band Error', '平均級距誤差');
        case 'release_status':
            return t('Release Status', '釋出狀態');
        case 'approved':
            return t('Approved', '已核准上線');
        case 'rejected':
            return t('Rejected', '已退回');
        case 'rollback':
            return t('Rollback', '回滾');
        case 'rollbacked':
            return t('Rolled Back', '已回滾');
        case 'pending_review':
            return t('Pending Review', '審核中');
        case 'candidate':
            return t('Candidate', '候選版本');
        case 'current_production':
            return t('Current Production', '目前線上版本');
        case 'approve':
            return t('Approve', '核准上線');
        case 'reject':
            return t('Reject', '退回');
        case 'drifted':
            return t('Drifted', '嚴重預估偏差');
        case 'warning':
            return t('Warning', '警告');
        case 'stable':
            return t('Stable', '穩定');
        case 'last_24h':
            return t('Last 24 Hours', '最近 24 小時');
        case 'last_7d':
            return t('Last 7 Days', '最近 7 天');
        case 'last_30d':
            return t('Last 30 Days', '最近 30 天');
        case 'lifetime':
            return t('Lifetime', '累積歷史成效');
        case 'custom':
            return t('Custom Range', '自訂時間區間');
        case 'accuracy_gate':
            return t('Accuracy Gate', '準確率安全門檻');
        case 'mae_gate':
            return t('MAE Gate', '平均偏差安全門檻');
        case 'bias_gate':
            return t('Bias Gate', '模型偏向性門檻');
        case 'model_loaded_check':
            return t('Model Loaded Check', '模型載入測試');
        case 'active_drift_alert_check':
            return t('Active Drift Alert Check', '線上無嚴重預估偏差安全閘');
        case 'release actions now persist to datavue db.':
            return t('Release actions now persist to DataVue DB.', '版本發佈操作已成功持久化至 DataVue 資料庫。');
        case 'release metadata is now aligned with the meta andromeda registry source of truth.':
            return t('Release metadata is now aligned with the Meta Andromeda registry source of truth.', '版本中繼資料已與 Meta Andromeda 註冊表單一事實來源同步。');
        default:
            return key;
    }
};

export const formatDateTime = (isoString) => {
    if (!isoString) return '--';
    try {
        let dateStr = isoString;
        if (!dateStr.endsWith('Z') && !dateStr.includes('+')) {
            dateStr = dateStr.includes('T') ? `${dateStr}Z` : dateStr;
        }
        const date = new Date(dateStr);
        if (Number.isNaN(date.getTime())) return isoString;

        const y = date.getFullYear();
        const m = String(date.getMonth() + 1).padStart(2, '0');
        const d = String(date.getDate()).padStart(2, '0');
        const hh = String(date.getHours()).padStart(2, '0');
        const mm = String(date.getMinutes()).padStart(2, '0');
        const ss = String(date.getSeconds()).padStart(2, '0');

        return `${y}-${m}-${d} ${hh}:${mm}:${ss}`;
    } catch {
        return isoString;
    }
};

export const getCandidateReleaseGate = (candidate, t) => {
    if (!candidate) return { passed: false, reason: t('No candidate data', '沒有候選版本資料') };
    if (candidate.is_demo_data) {
        return {
            passed: false,
            reason: t('Metrics have not been computed yet.', '尚未使用真實資料計算指標。'),
        };
    }
    const accuracy = Number(candidate.pairwise_ranking_accuracy);
    if (Number.isNaN(accuracy) || accuracy < 0.55) {
        return {
            passed: false,
            reason: t('Pairwise accuracy is below 0.55.', '成對排序準確率低於 0.55。'),
        };
    }
    return { passed: true, reason: t('Accuracy gate passed.', '準確率門檻已通過。') };
};

export const getBacktestVerdict = (run, overview, t) => {
    const baseline = Number(overview?.current_production?.pairwise_ranking_accuracy);
    const accuracy = Number(run?.pairwise_ranking_accuracy);
    if (run?.status !== 'completed' || Number.isNaN(accuracy)) return { label: t('Pending', '待完成'), color: '#94a3b8' };
    if (accuracy >= 0.55 && (Number.isNaN(baseline) || accuracy >= baseline)) {
        return { label: t('Better than baseline', '優於線上基準'), color: '#10b981' };
    }
    return { label: t('Not ready', '不建議上線'), color: '#ef4444' };
};
export const demoBadgeStyle = {
    display: 'inline-flex',
    alignItems: 'center',
    padding: '3px 8px',
    borderRadius: '999px',
    border: '1px solid rgba(245, 158, 11, 0.35)',
    background: 'rgba(245, 158, 11, 0.1)',
    color: '#fbbf24',
    fontSize: '0.72rem',
    fontWeight: 700,
};

export const panelStyle = {
    background: 'var(--bg-secondary)',
    border: '1px solid var(--glass-border)',
    borderRadius: '16px',
    padding: '24px',
};

export const sectionTitleStyle = {
    margin: '0 0 16px 0',
    color: 'var(--text-primary)',
    fontSize: '1rem',
};

export const metricGridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: '12px',
};

export const detailCardStyle = {
    padding: '14px',
    borderRadius: '12px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.02)',
};

export const gateRowStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
};

export const buttonPrimaryStyle = {
    padding: '12px 16px',
    borderRadius: '10px',
    border: 'none',
    background: 'var(--accent-primary)',
    color: 'white',
    cursor: 'pointer',
};

export const buttonSecondaryStyle = {
    padding: '12px 16px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.02)',
    color: 'var(--text-primary)',
    cursor: 'pointer',
};

export const fieldLabelStyle = {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
    fontSize: '0.8rem',
    color: 'var(--text-secondary)',
};

export const fieldInputStyle = {
    padding: '10px 12px',
    borderRadius: '8px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255,255,255,0.03)',
    color: 'var(--text-primary)',
    fontSize: '0.85rem',
};

export const errorPanelStyle = {
    marginBottom: '16px',
    padding: '16px',
    borderRadius: '12px',
    background: 'rgba(239, 68, 68, 0.08)',
    border: '1px solid rgba(239, 68, 68, 0.18)',
    color: 'var(--text-primary)',
};

export const successPanelStyle = {
    marginBottom: '16px',
    padding: '16px',
    borderRadius: '12px',
    background: 'rgba(16, 185, 129, 0.12)',
    border: '1px solid rgba(16, 185, 129, 0.25)',
    color: 'var(--text-primary)',
};

export const warningPanelStyle = {
    marginBottom: '16px',
    padding: '16px',
    borderRadius: '12px',
    background: 'rgba(245, 158, 11, 0.1)',
    border: '1px solid rgba(245, 158, 11, 0.3)',
    color: 'var(--text-primary)',
    fontSize: '0.88rem',
};

export const infoPanelStyle = {
    marginTop: '16px',
    padding: '12px 14px',
    borderRadius: '12px',
    background: 'rgba(59, 130, 246, 0.08)',
    border: '1px solid rgba(59, 130, 246, 0.18)',
    color: 'var(--text-secondary)',
    lineHeight: 1.7,
};

export const emptyStateStyle = {
    padding: '14px',
    borderRadius: '12px',
    border: '1px dashed var(--glass-border)',
    color: 'var(--text-secondary)',
    textAlign: 'center',
};

export const pairTableHeaderStyle = {
    position: 'sticky',
    top: 0,
    background: 'var(--bg-secondary)',
    color: 'var(--text-secondary)',
    textAlign: 'left',
    padding: '10px 12px',
    fontWeight: 600,
    whiteSpace: 'nowrap',
};

export const pairTableCellStyle = {
    padding: '8px 12px',
    color: 'var(--text-secondary)',
    verticalAlign: 'middle',
};


