import apiClient from './apiClient';

export const ga4InsightsService = {
    listRules: async (propertyId) => {
        const query = propertyId ? `?property_id=${encodeURIComponent(propertyId)}` : '';
        return apiClient.get(`/api/ga4/insights/anomaly-rules${query}`);
    },

    createRule: async (payload) => apiClient.post('/api/ga4/insights/anomaly-rules', payload),

    updateRule: async (ruleId, payload) => apiClient.put(`/api/ga4/insights/anomaly-rules/${ruleId}`, payload),

    deleteRule: async (ruleId) => apiClient.delete(`/api/ga4/insights/anomaly-rules/${ruleId}`),

    listEvents: async (propertyId, page = 1, pageSize = 20) => {
        const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
        if (propertyId) params.set('property_id', propertyId);
        return apiClient.get(`/api/ga4/insights/anomaly-events?${params.toString()}`);
    },

    acknowledgeEvent: async (eventId) => apiClient.patch(`/api/ga4/insights/anomaly-events/${eventId}/ack`, { acknowledged: true }),

    // docs/52：告警規則「轉換」的關鍵事件下拉選單來源（近 7 天，使用者開表單時查一次）
    getRuleAvailableKeyEvents: async (propertyId) =>
        apiClient.get(`/api/ga4/insights/anomaly-rules/available-key-events?property_id=${encodeURIComponent(propertyId)}`),

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

    // docs/54：compare=true 時多回傳一組「跟上一期比較」欄位，預設 false
    // 維持現況行為不變。
    getLandingPages: async (propertyId, days = 7, keyEvent = null, channelDimension = null, channelValue = null, channelGroup = null, compare = false) =>
        apiClient.get(
            `/api/ga4/insights/landing-pages?property_id=${encodeURIComponent(propertyId)}&days=${days}`
            + (keyEvent ? `&key_event=${encodeURIComponent(keyEvent)}` : '')
            + (channelDimension && channelValue
                ? `&channel_dimension=${encodeURIComponent(channelDimension)}&channel_value=${encodeURIComponent(channelValue)}`
                : '')
            + (channelDimension && channelGroup
                ? `&channel_dimension=${encodeURIComponent(channelDimension)}&channel_group=${encodeURIComponent(channelGroup)}`
                : '')
            + (compare ? '&compare=true' : '')
        ),

    getItems: async (propertyId, days = 7, channelDimension = null, channelValue = null, channelGroup = null, compare = false) =>
        apiClient.get(
            `/api/ga4/insights/items?property_id=${encodeURIComponent(propertyId)}&days=${days}`
            + (channelDimension && channelValue
                ? `&channel_dimension=${encodeURIComponent(channelDimension)}&channel_value=${encodeURIComponent(channelValue)}`
                : '')
            + (channelDimension && channelGroup
                ? `&channel_dimension=${encodeURIComponent(channelDimension)}&channel_group=${encodeURIComponent(channelGroup)}`
                : '')
            + (compare ? '&compare=true' : '')
        ),

    // ─── docs/47：商品頁面與商品轉換率交叉對照（追加） ───────────────
    getItemLandingCross: async (propertyId, days = 7) =>
        apiClient.get(`/api/ga4/insights/item-landing-cross?property_id=${encodeURIComponent(propertyId)}&days=${days}`),

    // ─── 第 2 波任務 2.4：AI 白話解讀持久化 ─────────────────────────
    saveAiSummary: async (snapshotId, aiSummary) =>
        apiClient.put(`/api/ga4/insights/snapshots/${snapshotId}/ai-summary`, { ai_summary: aiSummary }),

    // ─── docs/39：快照分享連結 ───────────────────────────────────────
    createShareLink: async (snapshotId) =>
        apiClient.post(`/api/ga4/insights/snapshots/${snapshotId}/share`, {}),

    getSharedSnapshot: async (token) =>
        apiClient.get(`/api/ga4/insights/share/${token}`, { skipAuth: true }),

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

    // ─── docs/44：渠道值自訂分組規則（追加） ─────────────────────────
    listChannelGroupRules: async (propertyId, channelDimension = null) =>
        apiClient.get(
            `/api/ga4/insights/channel-group-rules?property_id=${encodeURIComponent(propertyId)}`
            + (channelDimension ? `&channel_dimension=${encodeURIComponent(channelDimension)}` : '')
        ),

    upsertChannelGroupRule: async (payload) => apiClient.put('/api/ga4/insights/channel-group-rules', payload),

    deleteChannelGroupRule: async (ruleId) => apiClient.delete(`/api/ga4/insights/channel-group-rules/${ruleId}`),

    listChannelGroups: async (propertyId, channelDimension) =>
        apiClient.get(
            `/api/ga4/insights/channel-groups?property_id=${encodeURIComponent(propertyId)}&channel_dimension=${encodeURIComponent(channelDimension)}`
        ),
};
