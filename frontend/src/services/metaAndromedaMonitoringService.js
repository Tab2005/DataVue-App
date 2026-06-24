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

export const syncMetaAndromedaCalibrationDataset = async (payload) => {
    return apiClient.post('/api/meta-andromeda/calibration/sync', payload);
};

export const cleanupStaleScoreEvents = async (payload = {}) => {
    return apiClient.post('/api/meta-andromeda/maintenance/cleanup-stale-score-events', payload);
};

export const fetchScoringProfiles = async () => {
    return apiClient.get('/api/meta-andromeda/monitoring/scoring-profiles');
};

export const promoteScoringProfile = async (profileName) => {
    return apiClient.post(`/api/meta-andromeda/monitoring/scoring-profiles/${encodeURIComponent(profileName)}/promote`, {});
};

export const fetchDriftTrend = async (limit = 20, account_id = null) => {
    const params = { limit };
    if (account_id) params.account_id = account_id;
    return apiClient.get('/api/meta-andromeda/monitoring/drift-trend', { params });
};

export const fetchObservedAccounts = async () => {
    return apiClient.get('/api/meta-andromeda/monitoring/observed-accounts');
};

export default {
    fetchMetaAndromedaMonitoringSummary,
    fetchMetaAndromedaMonitoringTimeline,
    triggerMetaAndromedaDriftReport,
    syncMetaAndromedaCalibrationDataset,
    cleanupStaleScoreEvents,
    fetchDriftTrend,
    fetchObservedAccounts,
};
