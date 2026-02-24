import apiClient from './apiClient';

const API_BASE = '/api';

export const TeamService = {
    /**
     * Get all teams current user belongs to
     */
    getMyTeams: async () => {
        return apiClient.get(`${API_BASE}/teams/me`);
    },

    /**
     * Create a new team
     * @param {string} name Team Name
     */
    createTeam: async (name) => {
        return apiClient.post(`${API_BASE}/teams/`, { name });
    },

    /**
     * Get Members of a Team
     */
    getTeamMembers: async (teamId) => {
        return apiClient.get(`${API_BASE}/teams/${teamId}/members`);
    },

    /**
     * Generate Invite Link
     */
    createInviteLink: async (teamId) => {
        return apiClient.post(`${API_BASE}/teams/${teamId}/invites`);
    },

    /**
     * Public Check Invite（不需認證）
     */
    checkInvite: async (code) => {
        return apiClient.get(`${API_BASE}/invites/${code}`, { skipAuth: true });
    },

    /**
     * Accept Invite
     */
    acceptInvite: async (code) => {
        return apiClient.post(`${API_BASE}/invites/${code}/accept`);
    },

    /**
     * Remove Member from Team
     */
    removeMember: async (teamId, userId) => {
        await apiClient.delete(`${API_BASE}/teams/${teamId}/members/${userId}`);
        return true;
    },

    /**
     * Update Member Role
     */
    updateMemberRole: async (teamId, userId, role) => {
        return apiClient.put(`${API_BASE}/teams/${teamId}/members/${userId}`, { role });
    },

    /**
     * Update Team Settings (Name)
     */
    updateTeam: async (teamId, name) => {
        return apiClient.put(`${API_BASE}/teams/${teamId}`, { name });
    },

    /**
     * Delete Team (Disband)
     */
    deleteTeam: async (teamId) => {
        await apiClient.delete(`${API_BASE}/teams/${teamId}`);
        return true;
    },

    /**
     * Update Team Ad Account Whitelist
     * @param {string} teamId
     * @param {string[]} adAccountIds List of Account IDs
     */
    updateAdAccounts: async (teamId, adAccountIds) => {
        return apiClient.put(`${API_BASE}/teams/${teamId}/ad_accounts`, { ad_account_ids: adAccountIds });
    },

    /**
     * Get All Ad Accounts (for Whitelist Selector)
     * Calls the standard /api/ad-accounts endpoint which returns ALL for Owner.
     * @param {string} teamId Optional. If provided, ensures context is correct.
     */
    getAllAdAccounts: async (teamId = null) => {
        try {
            // 若明確傳入 teamId，透過額外 header 覆蓋 localStorage 的值
            const extraHeaders = teamId ? { 'X-Team-ID': teamId } : {};
            return await apiClient.get(`${API_BASE}/ad-accounts`, { headers: extraHeaders });
        } catch {
            return [];
        }
    },
};

