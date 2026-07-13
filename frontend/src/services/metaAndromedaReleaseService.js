import apiClient from './apiClient';

export const fetchMetaAndromedaReleaseOverview = async () => {
    return apiClient.get('/api/meta-andromeda/release/overview');
};

export const approveMetaAndromedaRelease = async (payload) => {
    return apiClient.post('/api/meta-andromeda/release/approve', payload);
};

export const rejectMetaAndromedaRelease = async (payload) => {
    return apiClient.post('/api/meta-andromeda/release/reject', payload);
};

export const rollbackMetaAndromedaRelease = async (payload) => {
    return apiClient.post('/api/meta-andromeda/release/rollback', payload);
};

// 新增候選版本（讓正式評分模型也能像回測模型一樣自由指定要試哪個 model_version，
// 而不是只能在種子資料建立的舊候選之間 approve/rollback）。approve/rollback 的
// 稽核流程完全不變。
export const createMetaAndromedaReleaseCandidate = async (payload) => {
    return apiClient.post('/api/meta-andromeda/release/candidates', payload);
};

// 配對明細（docs/32 任務 1.1）：release 指標背後的逐筆「觀測素材 × AI 評分」對照。
// 注意 apiClient 不支援 axios 式 { params }，query string 必須拼在路徑上。
export const fetchMetaAndromedaReleaseMetricPairs = async (modelVersion, { sort = 'mismatch', limit = 200 } = {}) => {
    const qs = `sort=${encodeURIComponent(sort)}&limit=${encodeURIComponent(limit)}`;
    return apiClient.get(`/api/meta-andromeda/release/${encodeURIComponent(modelVersion)}/metric-pairs?${qs}`);
};

export const fetchMetaAndromedaBacktestRuns = async ({ limit = 20 } = {}) => {
    return apiClient.get(`/api/meta-andromeda/backtest/runs?limit=${encodeURIComponent(limit)}`);
};

export const createMetaAndromedaBacktestRun = async (payload) => {
    return apiClient.post('/api/meta-andromeda/backtest/runs', payload);
};

export default {
    fetchMetaAndromedaReleaseOverview,
    approveMetaAndromedaRelease,
    rejectMetaAndromedaRelease,
    rollbackMetaAndromedaRelease,
    createMetaAndromedaReleaseCandidate,
    fetchMetaAndromedaReleaseMetricPairs,
    fetchMetaAndromedaBacktestRuns,
    createMetaAndromedaBacktestRun,
};
