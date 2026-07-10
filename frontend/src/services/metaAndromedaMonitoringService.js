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

export const promoteScoringProfile = async (profileName, force = false) => {
    const query = force ? '?force=true' : '';
    return apiClient.post(`/api/meta-andromeda/monitoring/scoring-profiles/${encodeURIComponent(profileName)}/promote${query}`, {});
};

export const runScoringProfileBacktest = async (profileName) => {
    return apiClient.post(`/api/meta-andromeda/monitoring/scoring-profiles/${encodeURIComponent(profileName)}/backtest`, {});
};

export const fetchDriftTrend = async (limit = 20, account_id = null) => {
    const params = { limit };
    if (account_id) params.account_id = account_id;
    return apiClient.get('/api/meta-andromeda/monitoring/drift-trend', { params });
};

export const fetchObservedAccounts = async () => {
    return apiClient.get('/api/meta-andromeda/monitoring/observed-accounts');
};

export const fetchModelRegistry = async () => {
    return apiClient.get('/api/meta-andromeda/monitoring/model-registry');
};

export const updateBacktestModel = async (provider, providerModel) => {
    return apiClient.put('/api/meta-andromeda/monitoring/model-registry/backtest-model', {
        provider,
        provider_model: providerModel,
    });
};

// 目前實際生效的互動評分設定 vs. 資料庫 registry 標記的 production 列——
// env override（META_ANDROMEDA_SCORING_PROVIDER/_MODEL/_MODEL_VERSION）完全
// 不寫資料庫，只在記憶體即時生效，畫面若只讀 registry 表會誤以為沒生效。
export const fetchEffectiveScoringStatus = async () => {
    return apiClient.get('/api/meta-andromeda/monitoring/model-registry/effective');
};

// 換模型前先查：這個 model id 在 OpenRouter 是否真的存在、支不支援評分需要的圖片
// 輸入、實際 context/輸出上限多大（2026-07-10 事故後新增，見 docs）。
export const validateCandidateModel = async (modelId) => {
    return apiClient.get('/api/meta-andromeda/monitoring/model-registry/validate-candidate', {
        params: { model_id: modelId },
    });
};

export default {
    fetchMetaAndromedaMonitoringSummary,
    fetchMetaAndromedaMonitoringTimeline,
    triggerMetaAndromedaDriftReport,
    syncMetaAndromedaCalibrationDataset,
    cleanupStaleScoreEvents,
    fetchScoringProfiles,
    promoteScoringProfile,
    runScoringProfileBacktest,
    fetchDriftTrend,
    fetchObservedAccounts,
    fetchModelRegistry,
    updateBacktestModel,
    fetchEffectiveScoringStatus,
    validateCandidateModel,
};
