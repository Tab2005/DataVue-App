import { getAuthHeaders } from '../utils/auth';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const getStats = async () => {
    try {
        const response = await fetch(`${API_URL}/api/admin/stats`, {
            headers: getAuthHeaders()
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw errorData.detail || 'Failed to fetch stats';
        }
        return await response.json();
    } catch (error) {
        throw error;
    }
};

const getAllUsers = async () => {
    try {
        const response = await fetch(`${API_URL}/api/admin/users`, {
            headers: getAuthHeaders()
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw errorData.detail || 'Failed to fetch users';
        }
        return await response.json();
    } catch (error) {
        throw error;
    }
};

const getAllTeams = async () => {
    try {
        const response = await fetch(`${API_URL}/api/admin/teams`, {
            headers: getAuthHeaders()
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw errorData.detail || 'Failed to fetch teams';
        }
        return await response.json();
    } catch (error) {
        throw error;
    }
};

const deleteUser = async (userId) => {
    try {
        const response = await fetch(`${API_URL}/api/admin/users/${userId}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw errorData.detail || 'Failed to delete user';
        }
        return true;
    } catch (error) {
        throw error;
    }
};

export const AdminService = {
    getStats,
    getAllUsers,
    getAllTeams,
    deleteUser
};
