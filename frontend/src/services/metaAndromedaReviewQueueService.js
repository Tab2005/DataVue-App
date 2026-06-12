import apiClient from './apiClient';

export const fetchMetaAndromedaReviewQueue = async ({ status, reviewed, limit = 30 } = {}) => {
    const params = new URLSearchParams();
    if (status) params.set('status', status);
    if (reviewed !== undefined && reviewed !== null) params.set('reviewed', String(reviewed));
    params.set('limit', String(limit));

    const query = params.toString();
    return apiClient.get(`/api/meta-andromeda/review-queue${query ? `?${query}` : ''}`);
};

export const fetchMetaAndromedaReviewDetail = async (scoreEventId) => {
    return apiClient.get(`/api/meta-andromeda/review-queue/${scoreEventId}`);
};

export const fetchMetaAndromedaReviewFeedback = async (scoreEventId) => {
    return apiClient.get(`/api/meta-andromeda/scores/${scoreEventId}/feedback`);
};

export const submitMetaAndromedaReviewFeedback = async (scoreEventId, payload) => {
    return apiClient.post(`/api/meta-andromeda/scores/${scoreEventId}/feedback`, payload);
};

export default {
    fetchMetaAndromedaReviewQueue,
    fetchMetaAndromedaReviewDetail,
    fetchMetaAndromedaReviewFeedback,
    submitMetaAndromedaReviewFeedback,
};
