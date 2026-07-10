import apiClient from './apiClient';

export const ga4InsightsService = {
    listRules: async (propertyId) => {
        const query = propertyId ? `?property_id=${encodeURIComponent(propertyId)}` : '';
        return apiClient.get(`/api/ga4/insights/anomaly-rules${query}`);
    },

    createRule: async (payload) => apiClient.post('/api/ga4/insights/anomaly-rules', payload),

    updateRule: async (ruleId, payload) => apiClient.put(`/api/ga4/insights/anomaly-rules/${ruleId}`, payload),

    deleteRule: async (ruleId) => apiClient.delete(`/api/ga4/insights/anomaly-rules/${ruleId}`),

    listEvents: async (propertyId) => {
        const query = propertyId ? `?property_id=${encodeURIComponent(propertyId)}` : '';
        return apiClient.get(`/api/ga4/insights/anomaly-events${query}`);
    },

    acknowledgeEvent: async (eventId) => apiClient.patch(`/api/ga4/insights/anomaly-events/${eventId}/ack`, { acknowledged: true }),

    // ─── 第 2 波：當日儀表板 / Realtime / 渠道 / 到達頁 / 商品 ──────────
    getDashboard: async (propertyId) =>
        apiClient.get(`/api/ga4/insights/dashboard?property_id=${encodeURIComponent(propertyId)}`),

    refreshDashboard: async (propertyId) =>
        apiClient.post('/api/ga4/insights/dashboard/refresh', { property_id: propertyId }),

    getRealtime: async (propertyId) =>
        apiClient.get(`/api/ga4/insights/realtime?property_id=${encodeURIComponent(propertyId)}`),

    getChannels: async (propertyId, days = 7, dimension = 'default_channel_group') =>
        apiClient.get(
            `/api/ga4/insights/channels?property_id=${encodeURIComponent(propertyId)}&days=${days}&dimension=${encodeURIComponent(dimension)}`
        ),

    getLandingPages: async (propertyId, days = 7, keyEvent = null) =>
        apiClient.get(
            `/api/ga4/insights/landing-pages?property_id=${encodeURIComponent(propertyId)}&days=${days}`
            + (keyEvent ? `&key_event=${encodeURIComponent(keyEvent)}` : '')
        ),

    getItems: async (propertyId, days = 7) =>
        apiClient.get(`/api/ga4/insights/items?property_id=${encodeURIComponent(propertyId)}&days=${days}`),

    // ─── 第 2 波任務 2.4：AI 白話解讀持久化 ─────────────────────────
    saveAiSummary: async (snapshotId, aiSummary) =>
        apiClient.put(`/api/ga4/insights/snapshots/${snapshotId}/ai-summary`, { ai_summary: aiSummary }),

    // ─── 第 3 波：KPI 目標追蹤（選配） ───────────────────────────────
    listKpiTargets: async (propertyId) =>
        apiClient.get(`/api/ga4/insights/kpi-targets?property_id=${encodeURIComponent(propertyId)}`),

    upsertKpiTarget: async (payload) => apiClient.put('/api/ga4/insights/kpi-targets', payload),

    deleteKpiTarget: async (targetId) => apiClient.delete(`/api/ga4/insights/kpi-targets/${targetId}`),

    // ─── 第 5 波：到達頁分類規則（追加） ─────────────────────────────
    listLandingPageRules: async (propertyId) =>
        apiClient.get(`/api/ga4/insights/landing-page-rules?property_id=${encodeURIComponent(propertyId)}`),

    upsertLandingPageRule: async (payload) => apiClient.put('/api/ga4/insights/landing-page-rules', payload),

    deleteLandingPageRule: async (ruleId) => apiClient.delete(`/api/ga4/insights/landing-page-rules/${ruleId}`),

    // ─── 第 7 波：商品分類補充規則（追加） ───────────────────────────
    listItemCategoryRules: async (propertyId) =>
        apiClient.get(`/api/ga4/insights/item-category-rules?property_id=${encodeURIComponent(propertyId)}`),

    upsertItemCategoryRule: async (payload) => apiClient.put('/api/ga4/insights/item-category-rules', payload),

    deleteItemCategoryRule: async (ruleId) => apiClient.delete(`/api/ga4/insights/item-category-rules/${ruleId}`),
};
