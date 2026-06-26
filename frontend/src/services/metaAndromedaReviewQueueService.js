import apiClient from './apiClient';

export const fetchMetaAndromedaReviewQueue = async ({ status, has_observation, limit = 50, offset = 0 } = {}) => {
    const params = new URLSearchParams();
    if (status) params.set('status', status);
    if (has_observation !== undefined && has_observation !== null) params.set('has_observation', String(has_observation));
    params.set('limit', String(limit));
    params.set('offset', String(offset));

    const query = params.toString();
    return apiClient.get(`/api/meta-andromeda/review-queue${query ? `?${query}` : ''}`);
};

export const fetchMetaAndromedaReviewDetail = async (scoreEventId) => {
    return apiClient.get(`/api/meta-andromeda/review-queue/${scoreEventId}`);
};

export default {
    fetchMetaAndromedaReviewQueue,
    fetchMetaAndromedaReviewDetail,
};
