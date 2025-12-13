import { getAuthHeaders } from '../utils/auth';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const UserService = {
  // Get all users (Admin only)
  getAllUsers: async () => {
    try {
      const response = await fetch(`${API_URL}/users/`, {
        method: 'GET',
        headers: getAuthHeaders(),
      });
      if (!response.ok) throw new Error('Failed to fetch users');
      return await response.json();
    } catch (error) {
      console.error('Error fetching users:', error);
      throw error;
    }
  },

  // Get current user profile
  getMe: async () => {
    try {
      const response = await fetch(`${API_URL}/users/me`, {
        method: 'GET',
        headers: getAuthHeaders(),
      });
      if (!response.ok) throw new Error('Failed to fetch user profile');
      return await response.json();
    } catch (error) {
      console.error('Error fetching profile:', error);
      throw error;
    }
  },

  // Update user role or status (Admin only)
  updateUser: async (userId, data) => {
    try {
      const response = await fetch(`${API_URL}/users/${userId}`, {
        method: 'PUT',
        headers: {
          ...getAuthHeaders(),
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('Failed to update user');
      return await response.json();
    } catch (error) {
      console.error('Error updating user:', error);
      throw error;
    }
  },

  // Delete user (Admin only)
  deleteUser: async (userId) => {
    try {
      const response = await fetch(`${API_URL}/users/${userId}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });
      if (!response.ok) throw new Error('Failed to delete user');
      return true;
    } catch (error) {
      console.error('Error deleting user:', error);
      throw error;
    }
  }
};
