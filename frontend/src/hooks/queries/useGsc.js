/**
 * @fileoverview Google Search Console Query Hooks
 */

import { useQuery } from '@tanstack/react-query';
import apiClient from '../../services/apiClient';
import { queryKeys } from '../../constants/queryKeys';

/**
 * 取得 GSC 搜尋數據
 * @param {Object} params - 查詢參數
 * @param {boolean} [enabled=true] - 是否啟用查詢
 * @returns {import('@tanstack/react-query').UseQueryResult}
 */
export function useGscData(params, enabled = true) {
  return useQuery({
    queryKey: queryKeys.gsc.data(params),
    queryFn: () => apiClient.post('/api/gsc/data', params),
    staleTime: 5 * 60 * 1000,
    enabled: Boolean(enabled && params),
    placeholderData: (previousData) => previousData,
  });
}

/**
 * 取得 GSC 關鍵字分析
 * @param {Object} params - 查詢參數
 * @param {boolean} [enabled=true] - 是否啟用查詢
 * @returns {import('@tanstack/react-query').UseQueryResult}
 */
export function useGscKeywords(params, enabled = true) {
  return useQuery({
    queryKey: queryKeys.gsc.keywords(params),
    queryFn: () => apiClient.post('/api/gsc/keywords', params),
    staleTime: 5 * 60 * 1000,
    enabled: Boolean(enabled && params),
    placeholderData: (previousData) => previousData,
  });
}

/**
 * 取得 GSC 頁面分析
 * @param {Object} params - 查詢參數
 * @param {boolean} [enabled=true] - 是否啟用查詢
 * @returns {import('@tanstack/react-query').UseQueryResult}
 */
export function useGscPages(params, enabled = true) {
  return useQuery({
    queryKey: queryKeys.gsc.pages(params),
    queryFn: () => apiClient.post('/api/gsc/pages', params),
    staleTime: 5 * 60 * 1000,
    enabled: Boolean(enabled && params),
    placeholderData: (previousData) => previousData,
  });
}
