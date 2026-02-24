import apiClient from './apiClient';

export const UserService = {
  // Get all users (Admin only)
  getAllUsers: async () => {
    return apiClient.get('/users/');
  },

  // Get current user profile
  getMe: async () => {
    return apiClient.get('/users/me');
  },

  // Update user role or status (Admin only)
  updateUser: async (userId, data) => {
    return apiClient.put(`/users/${userId}`, data);
  },

  // Delete user (Admin only)
  deleteUser: async (userId) => {
    await apiClient.delete(`/users/${userId}`);
    return true;
  },
};
