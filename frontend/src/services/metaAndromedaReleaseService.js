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

export default {
    fetchMetaAndromedaReleaseOverview,
    approveMetaAndromedaRelease,
    rejectMetaAndromedaRelease,
    rollbackMetaAndromedaRelease,
};
