/**
 * @fileoverview Facebook 廣告帳號 Query Hook
 */

import { useQuery } from '@tanstack/react-query';
import apiClient from '../../services/apiClient';
import { queryKeys } from '../../constants/queryKeys';

/**
 * 取得使用者的廣告帳號列表
 * @param {string|undefined} userId - 使用者 ID（不存在時暫停請求）
 * @returns {import('@tanstack/react-query').UseQueryResult<import('../../types/api').AdAccount[]>}
 */
export function useFacebookAccounts(userId) {
  return useQuery({
    queryKey: queryKeys.facebook.accounts(userId),
    queryFn: () => apiClient.get('/api/facebook/accounts'),
    // 廣告帳號列表 5 分鐘快取
    staleTime: 5 * 60 * 1000,
    // userId 不存在時不請求
    enabled: Boolean(userId),
  });
}
