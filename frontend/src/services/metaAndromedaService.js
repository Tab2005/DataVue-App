import apiClient from './apiClient';

export const fetchMetaAndromedaOverview = async () => {
    return apiClient.get('/api/meta-andromeda/overview');
};

export default {
    fetchMetaAndromedaOverview,
};
