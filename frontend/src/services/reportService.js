// frontend/src/services/reportService.js
import apiClient from './apiClient';

export const reportService = {
  /** 取得報表列表 */
  list: (teamId) =>
    apiClient.get('/api/reports', { params: teamId ? { team_id: teamId } : {} }),

  /** 取得單筆報表 */
  get: (id) => apiClient.get(`/api/reports/${id}`),

  /** 建立新報表（草稿） */
  create: (payload) => apiClient.post('/api/reports', payload),

  /** 更新報表（名稱/章節/AI摘要） */
  update: (id, payload) => apiClient.put(`/api/reports/${id}`, payload),

  /** 刪除報表 */
  delete: (id) => apiClient.delete(`/api/reports/${id}`),

  /** 觸發資料產生 */
  generate: (id) => apiClient.post(`/api/reports/${id}/generate`),

  /** 取得公開分享報表 */
  getSharedReport: (token) =>
    apiClient.get(`/api/reports/share/${token}`, { skipAuth: true }),
};
