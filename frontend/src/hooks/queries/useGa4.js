/**
 * @fileoverview GA4 Analytics Query Hooks
 */

import { useQuery } from '@tanstack/react-query';
import apiClient from '../../services/apiClient';
import { queryKeys } from '../../constants/queryKeys';

/**
 * 取得 GA4 總覽數據
 * @param {Object} params - 查詢參數
 * @param {boolean} [enabled=true] - 是否啟用查詢
 * @returns {import('@tanstack/react-query').UseQueryResult}
 */
export function useGa4Overview(params, enabled = true) {
  return useQuery({
    queryKey: queryKeys.ga4.overview(params),
    queryFn: () => apiClient.post('/api/ga4/report', params),
    staleTime: 5 * 60 * 1000,
    enabled: Boolean(enabled && params),
    placeholderData: (previousData) => previousData,
  });
}

/**
 * 取得 GA4 事件數據
 * @param {Object} params - 查詢參數
 * @param {boolean} [enabled=true] - 是否啟用查詢
 * @returns {import('@tanstack/react-query').UseQueryResult}
 */
export function useGa4Events(params, enabled = true) {
  return useQuery({
    queryKey: queryKeys.ga4.events(params),
    queryFn: () => apiClient.post('/api/ga4/events', params),
    staleTime: 5 * 60 * 1000,
    enabled: Boolean(enabled && params),
    placeholderData: (previousData) => previousData,
  });
}

/**
 * 取得 GA4 頻道分組數據
 * @param {Object} params - 查詢參數
 * @param {boolean} [enabled=true] - 是否啟用查詢
 * @returns {import('@tanstack/react-query').UseQueryResult}
 */
export function useGa4Channels(params, enabled = true) {
  return useQuery({
    queryKey: queryKeys.ga4.channels(params),
    queryFn: () => apiClient.post('/api/ga4/channels', params),
    staleTime: 5 * 60 * 1000,
    enabled: Boolean(enabled && params),
    placeholderData: (previousData) => previousData,
  });
}
