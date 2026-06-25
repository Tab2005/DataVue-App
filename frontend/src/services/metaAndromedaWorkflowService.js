import apiClient from './apiClient';
import { getAuthToken } from '../utils/auth';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const uploadMetaAndromedaAsset = async (file, assetType) => {
    const formData = new FormData();
    formData.append('asset_type', assetType);
    formData.append('source_filename', file.name);
    formData.append('file', file);
    const teamId = localStorage.getItem('selected_team_id');

    const response = await fetch(`${API_URL}/api/meta-andromeda/assets:upload`, {
        method: 'POST',
        headers: {
            Authorization: `Bearer ${getAuthToken()}`,
            ...(teamId ? { 'X-Team-ID': teamId } : {}),
        },
        body: formData,
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.error || `HTTP ${response.status}`);
    }

    return response.json();
};

export const submitMetaAndromedaScore = async (payload) => {
    return apiClient.post('/api/meta-andromeda/scores', payload);
};

export const fetchMetaAndromedaScore = async (scoreEventId) => {
    return apiClient.get(`/api/meta-andromeda/scores/${scoreEventId}`);
};

export const fetchMetaAndromedaFeedback = async (scoreEventId) => {
    return apiClient.get(`/api/meta-andromeda/scores/${scoreEventId}/feedback`);
};

export const submitMetaAndromedaFeedback = async (scoreEventId, payload) => {
    return apiClient.post(`/api/meta-andromeda/scores/${scoreEventId}/feedback`, payload);
};

export const importMetaAndromedaObservedFacebookAd = async (payload) => {
    return apiClient.post('/api/meta-andromeda/evaluations/import/facebook-ads', payload);
};

export const fetchMetaAndromedaObservedImportStatus = async (observedCreativeId) => {
    return apiClient.get(`/api/meta-andromeda/evaluations/import/facebook-ads/${observedCreativeId}/status`);
};

export const fetchMetaAndromedaAiReady = async () => {
    return apiClient.get('/api/meta-andromeda/runtime/ai-ready');
};

export default {
    uploadMetaAndromedaAsset,
    submitMetaAndromedaScore,
    fetchMetaAndromedaScore,
    fetchMetaAndromedaFeedback,
    submitMetaAndromedaFeedback,
    importMetaAndromedaObservedFacebookAd,
    fetchMetaAndromedaObservedImportStatus,
    fetchMetaAndromedaAiReady,
};
