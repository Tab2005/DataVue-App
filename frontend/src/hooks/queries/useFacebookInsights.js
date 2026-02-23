/**
 * @fileoverview Facebook 廣告洞察數據 Query Hook
 */

import { useQuery } from '@tanstack/react-query';
import apiClient from '../../services/apiClient';
import { queryKeys } from '../../constants/queryKeys';

/**
 * 取得廣告洞察數據
 * @param {Object} params - 查詢參數
 * @param {string} params.accountId - 廣告帳號 ID
 * @param {string} params.startDate - 開始日期（YYYY-MM-DD）
 * @param {string} params.endDate - 結束日期（YYYY-MM-DD）
 * @param {string[]} params.metrics - 指標列表
 * @returns {import('@tanstack/react-query').UseQueryResult<import('../../types/api').InsightMetric[]>}
 */
export function useFacebookInsights({ accountId, startDate, endDate, metrics }) {
  return useQuery({
    queryKey: queryKeys.facebook.insights(accountId, { startDate, endDate, metrics }),
    queryFn: () => apiClient.post('/api/facebook/insights', {
      account_id: accountId,
      start_date: startDate,
      end_date: endDate,
      metrics,
    }),
    // 廣告數據 2 分鐘快取（相對即時）
    staleTime: 2 * 60 * 1000,
    enabled: Boolean(accountId && startDate && endDate),
    // 保留之前的資料在新請求進行時（避免 loading 閃爍）
    placeholderData: (previousData) => previousData,
  });
}

/**
 * 取得廣告趨勢數據
 * @param {Object} params - 查詢參數
 * @param {string} params.accountId - 廣告帳號 ID
 * @param {Object} params.queryParams - 其他查詢參數
 * @returns {import('@tanstack/react-query').UseQueryResult}
 */
export function useFacebookTrends({ accountId, ...queryParams }) {
  return useQuery({
    queryKey: queryKeys.facebook.trends(accountId, queryParams),
    queryFn: () => apiClient.post('/api/facebook/trends', {
      account_id: accountId,
      ...queryParams,
    }),
    staleTime: 2 * 60 * 1000,
    enabled: Boolean(accountId),
    placeholderData: (previousData) => previousData,
  });
}
