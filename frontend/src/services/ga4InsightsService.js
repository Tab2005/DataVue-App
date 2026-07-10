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
};
