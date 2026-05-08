/**
 * GA4 服務模組
 */
import apiClient from './apiClient';

export const ga4Service = {
  /**
   * 取得使用者的 GA4 屬性列表
   */
  getProperties: async () => {
    const res = await apiClient.get('/api/ga4/properties');
    return res?.properties || res || [];
  },

  /**
   * 取得 GA4 分析報告數據
   */
  getReport: async (params) => {
    const query = new URLSearchParams(params).toString();
    return apiClient.get(`/api/ga4/report?${query}`);
  },

  /**
   * 檢查 GA4 連線狀態
   */
  checkConnection: async () => {
    try {
      await apiClient.get('/api/ga4/properties');
      return { is_connected: true };
    } catch (err) {
      if (err.statusCode === 400 && err.message.includes('No GA4 credentials')) {
        return { is_connected: false };
      }
      throw err;
    }
  }
};
