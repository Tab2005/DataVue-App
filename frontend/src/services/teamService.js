import { getAuthHeaders } from '../utils/auth';

const API_ROOT = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
const API_BASE_URL = `${API_ROOT}/api`;

export const TeamService = {
    /**
     * Get all teams current user belongs to
     */
    getMyTeams: async () => {
        const headers = getAuthHeaders();
        if (!headers) return [];

        const response = await fetch(`${API_BASE_URL}/teams/me`, {
            method: 'GET',
            headers: headers
        });

        if (!response.ok) {
            throw new Error('Failed to fetch teams');
        }

        return await response.json();
    },

    /**
     * Create a new team
     * @param {string} name Team Name
     */
    createTeam: async (name) => {
        const headers = getAuthHeaders();
        const response = await fetch(`${API_BASE_URL}/teams/`, {
            method: 'POST',
            headers: {
                ...headers,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Failed to create team');
        }

        return await response.json();
    },

    /**
     * Get Members of a Team
     */
    getTeamMembers: async (teamId) => {
        const headers = getAuthHeaders();
        const response = await fetch(`${API_BASE_URL}/teams/${teamId}/members`, {
            headers: headers
        });
        if (!response.ok) throw new Error("Failed to fetch members");
        return await response.json();
    },

    /**
     * Generate Invite Link
     */
    createInviteLink: async (teamId) => {
        const headers = getAuthHeaders();
        const response = await fetch(`${API_BASE_URL}/teams/${teamId}/invites`, {
            method: 'POST',
            headers: headers
        });
        if (!response.ok) throw new Error("Failed to generate invite");
        return await response.json(); // { invite_url, code, expires_at }
    },

    /**
     * Public Check Invite
     */
    checkInvite: async (code) => {
        const response = await fetch(`${API_BASE_URL}/invites/${code}`);
        if (!response.ok) {
            if (response.status === 404) throw new Error("Invite not found");
            throw new Error("Failed to check invite");
        }
        return await response.json();
    },

    /**
     * Accept Invite
     */
    acceptInvite: async (code) => {
        const headers = getAuthHeaders();
        if (!headers) throw new Error("Login required");

        const response = await fetch(`${API_BASE_URL}/invites/${code}/accept`, {
            method: 'POST',
            headers: headers
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Failed to join team");
        }
        return await response.json();
    },

    /**
     * Remove Member from Team
     */
    removeMember: async (teamId, userId) => {
        const headers = getAuthHeaders();
        const response = await fetch(`${API_BASE_URL}/teams/${teamId}/members/${userId}`, {
            method: 'DELETE',
            headers: headers
        });
        if (!response.ok) {
            const err = await response.json(); // Likely 400 or 403
            throw new Error(err.detail || "Failed to remove member");
        }
        return true;
    },

    /**
     * Update Member Role
     */
    updateMemberRole: async (teamId, userId, role) => {
        const headers = getAuthHeaders();
        const response = await fetch(`${API_BASE_URL}/teams/${teamId}/members/${userId}`, {
            method: 'PUT',
            headers: {
                ...headers,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ role })
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Failed to update role");
        }
        return await response.json();
    },

    /**
     * Update Team Settings (Name)
     */
    updateTeam: async (teamId, name) => {
        const headers = getAuthHeaders();
        const response = await fetch(`${API_BASE_URL}/teams/${teamId}`, {
            method: 'PUT',
            headers: {
                ...headers,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name })
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Failed to update team");
        }
        return await response.json();
    },

    /**
     * Delete Team (Disband)
     */
    deleteTeam: async (teamId) => {
        const headers = getAuthHeaders();
        const response = await fetch(`${API_BASE_URL}/teams/${teamId}`, {
            method: 'DELETE',
            headers: headers
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Failed to delete team");
        }
        return true;
    },

    /**
     * Update Team Ad Account Whitelist
     * @param {string} teamId 
     * @param {string[]} adAccountIds List of Account IDs
     */
    updateAdAccounts: async (teamId, adAccountIds) => {
        const headers = getAuthHeaders();
        const response = await fetch(`${API_BASE_URL}/teams/${teamId}/ad_accounts`, {
            method: 'PUT',
            headers: {
                ...headers,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ ad_account_ids: adAccountIds })
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Failed to update ad accounts");
        }
        return await response.json();
    },

    /**
     * Get All Ad Accounts (for Whitelist Selector)
     * Calls the standard /api/ad-accounts endpoint which returns ALL for Owner.
     * @param {string} teamId Optional. If provided, ensures context is correct.
     */
    getAllAdAccounts: async (teamId = null) => {
        const headers = getAuthHeaders();

        // Override X-Team-ID if explicitly provided to avoid localStorage race conditions
        if (teamId) {
            headers['X-Team-ID'] = teamId;
        }

        const response = await fetch(`${API_BASE_URL}/ad-accounts`, {
            headers: headers
        });
        if (!response.ok) {
            // If 404/400, return empty or throw
            return [];
        }
        return await response.json();
    }
};
