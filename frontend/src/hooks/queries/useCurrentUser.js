/**
 * @fileoverview 當前使用者 Query Hook
 */

import { useQuery } from '@tanstack/react-query';
import apiClient from '../../services/apiClient';
import { queryKeys } from '../../constants/queryKeys';

/**
 * 取得當前登入使用者資料
 * @returns {import('@tanstack/react-query').UseQueryResult<import('../../types/api').User>}
 */
export function useCurrentUser() {
  return useQuery({
    queryKey: queryKeys.users.me(),
    queryFn: () => apiClient.get('/users/me'),
    // 使用者資料不常變更，快取較長時間
    staleTime: 10 * 60 * 1000,
  });
}
