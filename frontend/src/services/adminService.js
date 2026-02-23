import apiClient from './apiClient';

const getStats = async () => {
    return apiClient.get('/api/admin/stats');
};

const getAllUsers = async () => {
    return apiClient.get('/api/admin/users');
};

const getAllTeams = async () => {
    return apiClient.get('/api/admin/teams');
};

const deleteUser = async (userId) => {
    await apiClient.delete(`/api/admin/users/${userId}`);
    return true;
};

export const AdminService = {
    getStats,
    getAllUsers,
    getAllTeams,
    deleteUser
};
