// frontend/src/services/lineService.js
import apiClient from './apiClient';

export const lineService = {
    // 取得綁定代碼
    getBindingCode: async () => {
        const response = await apiClient.get('/api/line/binding-code');
        return response.data;
    },

    // 取得綁定狀態
    getStatus: async () => {
        const response = await apiClient.get('/api/line/status');
        return response.data;
    }
};
