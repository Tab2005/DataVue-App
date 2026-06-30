import apiClient from './apiClient';

export const fetchMetaAndromedaReviewQueue = async ({ status, has_observation, roas_band, search, source, scoring_engine, page = 1, page_size = 25 } = {}) => {
    const params = new URLSearchParams();
    if (status) params.set('status', status);
    if (has_observation !== undefined && has_observation !== null) params.set('has_observation', String(has_observation));
    if (roas_band) params.set('roas_band', roas_band);
    if (search) params.set('search', search);
    if (source) params.set('source', source);
    if (scoring_engine) params.set('scoring_engine', scoring_engine);
    params.set('page', String(page));
    params.set('page_size', String(page_size));

    const query = params.toString();
    return apiClient.get(`/api/meta-andromeda/review-queue${query ? `?${query}` : ''}`);
};

export const fetchMetaAndromedaReviewDetail = async (scoreEventId) => {
    return apiClient.get(`/api/meta-andromeda/review-queue/${scoreEventId}`);
};

export const deleteMetaAndromedaReviewItem = async (scoreEventId) => {
    return apiClient.delete(`/api/meta-andromeda/review-queue/${scoreEventId}`);
};

export const batchDeleteMetaAndromedaReviewItems = async (scoreEventIds) => {
    return apiClient.post('/api/meta-andromeda/review-queue/batch-delete', { score_event_ids: scoreEventIds });
};

export default {
    fetchMetaAndromedaReviewQueue,
    fetchMetaAndromedaReviewDetail,
    deleteMetaAndromedaReviewItem,
    batchDeleteMetaAndromedaReviewItems,
};
