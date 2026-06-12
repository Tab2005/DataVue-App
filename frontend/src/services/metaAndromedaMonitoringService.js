import apiClient from './apiClient';

export const fetchMetaAndromedaMonitoringSummary = async () => {
    return apiClient.get('/api/meta-andromeda/monitoring/summary');
};

export const fetchMetaAndromedaMonitoringTimeline = async (scoreEventId) => {
    return apiClient.get(`/api/meta-andromeda/monitoring/score-events/${scoreEventId}/timeline`);
};

export const triggerMetaAndromedaDriftReport = async (payload) => {
    return apiClient.post('/api/meta-andromeda/drift:trigger', payload);
};

export default {
    fetchMetaAndromedaMonitoringSummary,
    fetchMetaAndromedaMonitoringTimeline,
    triggerMetaAndromedaDriftReport,
};
