/**
 * 成效分析頁「AI 廣告分析」快照 + 分享連結（docs/58）。
 */
import apiClient from './apiClient';

export const analyticsAiService = {
    createSnapshot: async ({ accountId, teamId, level, dateSince, dateUntil, payload }) =>
        apiClient.post('/api/analytics-ai/snapshots', {
            account_id: accountId,
            team_id: teamId || null,
            level,
            date_since: dateSince,
            date_until: dateUntil,
            payload,
        }),

    saveAiSummary: async (snapshotId, aiSummary) =>
        apiClient.put(`/api/analytics-ai/snapshots/${snapshotId}/ai-summary`, { ai_summary: aiSummary }),

    createShareLink: async (snapshotId) =>
        apiClient.post(`/api/analytics-ai/snapshots/${snapshotId}/share`, {}),

    getSharedSnapshot: async (token) =>
        apiClient.get(`/api/analytics-ai/share/${token}`, { skipAuth: true }),
};

export default analyticsAiService;
