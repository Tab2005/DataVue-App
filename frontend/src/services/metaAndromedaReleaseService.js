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

export default {
    fetchMetaAndromedaReleaseOverview,
    approveMetaAndromedaRelease,
    rejectMetaAndromedaRelease,
    rollbackMetaAndromedaRelease,
    createMetaAndromedaReleaseCandidate,
};
